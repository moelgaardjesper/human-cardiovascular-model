"""
Arterial baroreflex and cardiopulmonary reflex model.

Implements the 4-step control architecture from PMC9363491 §Methods / Heldt 2002:

  Step 1: Input smoothing — running average of aortic and RA pressures (~2.5 s window)
            to remove beat-to-beat pulsatility before error computation.
  Step 2: Error signals vs setpoints (MAP_set=93, CVP_set=3 mmHg).
  Step 3: IIR first-order exponential filters for each autonomic time constant.
            Parasympathetic (τ=1.5 s) → fast HR adjustment (1-2 cardiac cycles).
            Sympathetic fast (τ=2 s)  → acute HR modulation.
            Sympathetic slow (τ=10 s) → sustained SVR and venous tone.
            Source: Borst & Karemaker 1983; Olufsen et al. 2005/2006.
            (identifiers and two caveats at the constants below)
  Step 4: Scale filtered errors to effector adjustments (HR, SVR, E_max, V0_vein).

NOTE on implementation: the original FIR convolution approach (100 taps at dt=0.001 s)
only spanned 0.1 s of history — far too short for the 2–10 s physiological time constants,
making all components effectively instantaneous and identical. Replaced with IIR first-order
filters (y[k] = (1-α)·y[k-1] + α·x[k], α = dt/τ) which correctly implement each
time constant with O(1) memory.

Setpoints (healthy male at rest):
    MAP_set  = 93 mmHg
    CVP_set  =  3 mmHg

Gain calibration:
    HR gain calibrated against Fritsch 1989 (PMID 2916705) — 0.85 bpm/mmHg,
      from a matched pair of sustained pressure changes in one cohort.
      See HR_REFLEX_GAIN_BPM below for the derivation.
    SVR gain (0.65) increased to maintain MAP during moderate HUT without
      over-relying on HR; validated against Wieling 1998 (PMID 9640339).
"""

import numpy as np
from collections import deque


# ---------------------------------------------------------------------------
# THE REFERENCE OPERATING POINT — defined here ONCE and imported elsewhere.
#
# Backlog item 50. Until 2026-09-15 `patient.py` hard-coded the same operating
# point a SECOND time, as `_svr(93.0, 5.0, 5.0)`, with nothing tying the two
# together: change one and the other silently disagrees, and the symptom would
# be a patient-scaling error that looks like a reflex error. Same shape as
# `pulmonary_art.resistance` serving double duty and the `VALVE_R` coupling.
#
# ON THE MAP VALUE. 93 had no citation when it was chosen. It is now supportable
# rather than merely inherited: McEniery CM et al. 2005 (PMID 16256881), the
# Anglo-Cardiff Collaborative Trial, 4001 healthy normotensive subjects, males
# 50-59 (n=429) measure **MAP 95 +/- 7 mmHg**. 93 sits 0.3 SD below that, so the
# number is fine; it was the absence of a source that was the defect.
#
# ON THE SETPOINT vs WHERE THE MODEL SETTLES. The model settles ABOVE this
# setpoint, and that is correct, not a defect. The reflex is purely
# PROPORTIONAL — first-order lags, no integral term — so a standing error is
# structural. An integrating baroreflex would drive every steady-state error to
# zero, which would make sustained hypertension impossible. **Do not add an
# integrator to close the gap.**
# ---------------------------------------------------------------------------
MAP_SETPOINT = 93.0   # mmHg — McEniery 2005 males 50-59 measure 95 +/- 7
PP_SETPOINT  = 40.0   # mmHg
CVP_SETPOINT =  3.0   # mmHg

# The reference patient's OPERATING POINT, used by `patient.py` to compute the
# SVR a patient's measured numbers should be scaled against. This is NOT the
# same thing as the setpoints above — a proportional reflex settles above its
# setpoint, so the operating point is legitimately higher.
#
# **KNOWN DEFECT, MEASURED 2026-09-15 AND NOT SILENTLY CHANGED.** These values
# describe a model that no longer exists. The reference patient actually settles
# at MAP 95.37, CO 5.99, CVP 4.36, so feeding the model its OWN operating point
# back in yields `svr_scale = 0.863` where it must be 1.000 — the reference
# patient rescales itself by -14 %. The CO term is the worst of the three: 5.0
# against a settled 5.99.
# Correcting them is NOT a one-line change: raising svr_ref raises svr_scale for
# every patient, which moves every patient-scaled test, and the direction makes
# the known MAP overshoot on a requested-MAP input WORSE before it makes it
# better. Carried as a strict xfail
# (`test_reference_operating_point_is_self_consistent`) rather than adjusted.
REFERENCE_MAP_MMHG = 93.0
REFERENCE_CVP_MMHG =  5.0
REFERENCE_CO_LPM   =  5.0

# Autonomic time constants (s) — Borst & Karemaker 1983, Olufsen 2005/2006.
#
# IDENTIFIERS ADDED 2026-09-15, and the lookup corrected TWO things. Both are
# recorded rather than quietly fixed, because each changes what these constants
# can claim to rest on.
#
#   Borst C, Karemaker JM. "Time delays in the human baroreceptor reflex."
#   J Auton Nerv Syst 9(2-3):399-409. PMID 6663021,
#   DOI 10.1016/0165-1838(83)90004-8.
#
# (1) IT IS 1983, not the "1982/1984" this file carried. Same shape as the
#     Suter 1975-vs-1978 error already recorded in respiration.py: a year
#     attribution that nobody could check because no identifier sat beside it.
#
# (2) IT MEASURES DELAYS, NOT TIME CONSTANTS, and that is a match-the-quantity
#     issue of the kind that has cost this project real time. Borst reports
#     LATENCIES from carotid-sinus-nerve stimulation in 11 subjects: PP interval
#     0.5-0.6 s, AV interval ~1 s, arterial pressure 2-3 s. A latency is a dead
#     time before a response starts; a tau is the rate at which it then
#     proceeds. They are different quantities and this file uses the paper for
#     the second while the paper measures the first. The 2-3 s arterial figure
#     is at least consistent with _TAU_SYMP_FAST = 2.0, but "consistent with" is
#     not "measured as".
#
#   Olufsen MS et al. J Appl Physiol 99(4):1523-37, 2005. PMID 15860687,
#   DOI 10.1152/japplphysiol.00177.2005.
#   Olufsen MS et al. Am J Physiol Regul Integr Comp Physiol 291(5):R1355-68,
#   2006. PMID 16793939, DOI 10.1152/ajpregu.00205.2006.
#
# (3) OLUFSEN IS A MODEL, NOT A MEASUREMENT. Both papers are parameter-estimation
#     studies that FIT a lumped model to postural-change data. Under this
#     project's own rule — do not treat another model's parameter table as
#     ground truth, the rule that demoted Heldt — these are a starting point and
#     a cross-check, not validation. The taus below therefore rest on one
#     delay study and two fitted models, and NO test asserts them directly.
#     That is a weaker footing than most constants in this repository have, and
#     it is worth a sourced human measurement of autonomic response dynamics.
_TAU_PARA       =  1.5   # parasympathetic (fast HR, 1-2 cardiac cycles)
_TAU_SYMP_FAST  =  2.0   # sympathetic fast (acute HR modulation)
# τ_slow increased 10→20 s: adds damping to the SVR feedback loop.
# At τ=10 s the baroreflex-SVR loop was underdamped, producing large-amplitude
# Mayer-wave-like oscillations (~90 mmHg pulse pressure) at extreme tilt angles.
# τ=20 s matches the slower physiological sympathetic vascular response
# (Olufsen 2005 reports 10–30 s for peripheral resistance changes).
_TAU_SYMP_SLOW  = 20.0   # sympathetic slow (sustained SVR, venous tone)
# Sympathetic control of HEART RATE is slower than its control of the SA node's
# vagal counterpart and slower than the 2 s fast arm used for SVR. Kept separate
# from _TAU_SYMP_FAST so the SVR pathway is untouched by HR recalibration.
_TAU_SYMP_HR    =  5.0   # sympathetic, heart rate


# --- Heart-rate arm of the arterial baroreflex ------------------------------
# CALIBRATED AGAINST Fritsch JM, Rea RF, Eckberg DL 1989 (PMID 2916705),
# n=10 healthy volunteers, ages 23-43. That study changed MAP in BOTH directions
# in ONE cohort and held each change for 25 min, which makes it a matched pair:
#
#   nitroprusside   ΔMAP −11 mmHg   R-R 932 → 820 ms    ΔHR  +8.8 bpm   0.80 bpm/mmHg
#   phenylephrine   ΔMAP +19 mmHg   R-R 932 → 1251 ms   ΔHR −16.4 bpm   0.86 bpm/mmHg
#
# Least-squares gain through the origin: 0.85 bpm/mmHg. Neither drug has a
# meaningful direct chronotropic action, so both responses are reflex.
#
# BOTH POINTS ARE FLOORS. They were measured after 25 min, by which time the
# reflex has partly reset toward the new pressure, so the acute gain is higher
# than 0.85. The model is calibrated to the floor and not above it.
#
# The two points are consistent with a LINEAR response over the range tested:
# their gains differ by 8 %, which is well inside the study's own standard
# errors (R-R ±37 to ±61 ms). The saturating reserve below is therefore NOT
# fitted to them — it is placed at physiological heart-rate limits instead.
HR_REFLEX_GAIN_BPM   = 30.0   # saturating reserve each way: HR 40–100 from 70
HR_REFLEX_SCALE_MMHG = 35.0   # gain at the setpoint = 30/35 = 0.857 bpm/mmHg
# --- Cardiopulmonary (filling-pressure) arm of the heart-rate reflex --------
# In humans the tachycardia of hypovolaemia is driven by FALLING CARDIAC FILLING
# and not by falling arterial pressure. The clearest demonstration is the graded
# LBNP dataset (n=20 healthy volunteers, supine) in `reference_values.md`:
#
#   LBNP  0    MAP 77.3   CVP 6.9   HR 65.8
#   LBNP 40    MAP 74.0   CVP 2.5   HR 74.1
#   LBNP 80    MAP 79.9   CVP 0.2   HR 91.1     (>1 L blood-volume equivalent)
#
# MAP IS FLAT across the whole range while CVP falls 6.7 mmHg and heart rate
# rises 25.3 bpm. There is no arterial error for the arm above to act on, so it
# explains none of this: 25.3 / 6.7 = 3.8 bpm per mmHg of filling pressure.
#
# That gain is much larger than the arterial arm's 0.86 bpm/mmHg because filling
# pressure has a much smaller dynamic range — 0-8 mmHg against 60-120. That is
# the physiology, not a fudge: cardiopulmonary receptors answer to small changes
# in cardiac distension.
#
# As in the arterial arm the GAIN is fitted and the SATURATION is not, because
# LBNP never approaches the asymptote. The reserve is placed at the largest
# tachycardia measured in humans with arterial pressure still defended —
# Vettorello 2016 (PMID 26756378), HR 69 -> 107 across LBNP 0 to -80, i.e.
# +38 bpm at the edge of presyncope.
#
# The arm is BIDIRECTIONAL. Rising filling pressure slows the heart, which is
# what Herrera 2017 measured for a 500 mL crystalloid bolus: HR 87 -> 83.
CP_HR_GAIN_BPM_PER_MMHG = 3.8    # at the reference filling pressure
CP_HR_RESERVE_BPM       = 40.0   # saturating reserve each way

# THE REFERENCE THIS ARM MEASURES DEVIATION FROM IS NOT `CVP_SETPOINT`.
# A cardiopulmonary receptor sits at its operating point when filling is normal
# FOR THAT PERSON. People differ in resting CVP and none of them are permanently
# tachycardic, so the reference is the patient's own resting filling pressure —
# not a population constant.
#
# `CVP_SETPOINT` is 3.0 mmHg, is uncited, and is 1.7 mmHg below the pressure the
# model actually rests at. Driving this arm from it produced a standing
# bradycardia of 6.0 bpm at rest (66.2 -> 60.2), which is an artefact of the
# mismatch and not physiology. The SVR arm still uses `CVP_SETPOINT`; there the
# same mismatch moves `svr_factor` by about 2 % and has always been absorbed
# into that arm's calibration.
#
# 4.7 mmHg is the default patient's settled CVP, and it sits inside the model's
# own validated CVP band of 4-10 (Hoff, n=20). It is a MODELLING CHOICE, not a
# measurement, and it should become patient-specific once `build_patient_params`
# can supply a resting filling pressure — logged as backlog item 39. Whether
# `CVP_SETPOINT` itself is right belongs with item 37.
CP_HR_REFERENCE_CVP_MMHG = 4.7


# Split between the two efferent limbs. Both see the same error, so they set
# the DYNAMICS, not the steady-state curve: the vagal limb is fast enough to
# track the respiratory cycle, the sympathetic limb is not.
_HR_VAGAL_FRACTION   = 0.45


class BaroreflexController:
    """
    Stateful baroreflex controller using IIR exponential filters.

    Call `update(map_mmhg, pp_mmhg, cvp_mmhg)` every simulation step.
    Read `hr_delta`, `svr_factor`, `emax_factor`, `v0_vein_factor`.

    `hr_delta` is additive (bpm). All other factors are multiplicative.
    """

    def __init__(
        self,
        map_set: float = MAP_SETPOINT,
        pp_set: float  = PP_SETPOINT,
        cvp_set: float = CVP_SETPOINT,
        dt: float = 0.001,
        history_len: int = 2500,
        cp_hr_enabled: bool = True,
        cp_hr_ref_cvp: float = CP_HR_REFERENCE_CVP_MMHG,
    ):
        self.map_set  = map_set
        self.pp_set   = pp_set
        self.cvp_set  = cvp_set
        self.dt       = dt

        # Input smoothing: ~2.5 s running average removes beat-to-beat pulsatility
        n = history_len   # 2500 steps × 0.001 s = 2.5 s at dt=0.001
        self._map_buf = deque([map_set]  * n, maxlen=n)
        self._cvp_buf = deque([cvp_set]  * n, maxlen=n)

        # IIR filter states — one per time constant per signal
        # Each state y is updated: y ← (1-α)·y + α·error, α = dt/τ
        self._para_map      = 0.0   # parasympathetic, MAP error (τ=1.5 s)
        self._symp_fast_map = 0.0   # sympathetic fast, MAP error (τ=2 s)
        self._symp_hr_map   = 0.0   # sympathetic, MAP error, HR arm (τ=5 s)
        self._symp_hr_cvp   = 0.0   # sympathetic, CVP error, HR arm (τ=5 s)
        self._symp_slow_map = 0.0   # sympathetic slow, MAP error (τ=10 s) — SVR
        self._symp_fast_cvp = 0.0   # sympathetic fast, CVP error (τ=2 s)

        # IIR decay coefficients α = dt/τ (clamped to [0,1])
        self._a_para    = min(1.0, dt / _TAU_PARA)
        self._a_fast    = min(1.0, dt / _TAU_SYMP_FAST)
        self._a_symp_hr = min(1.0, dt / _TAU_SYMP_HR)
        self._a_slow    = min(1.0, dt / _TAU_SYMP_SLOW)

        # Effector outputs (read by run_simulation after each update)
        self.hr_delta       = 0.0
        self.svr_factor     = 1.0
        self.emax_factor    = 1.0
        self.v0_vein_factor = 1.0

        # Effector gains
        # HR: one sourced curve (Fritsch 1989 — see the module constants), split
        # between the vagal and sympathetic limbs. The split changes only how fast
        # each limb follows the error; at steady state the two sum to the single
        # curve −HR_REFLEX_GAIN_BPM · tanh(err / HR_REFLEX_SCALE_MMHG).
        #
        # This REPLACES a pair of gains (−3 vagal, +2 sympathetic) that both read
        # the same error through the same scale of 10 mmHg. Being odd functions of
        # one signal they collapsed algebraically to −5·tanh(err/10): a reflex whose
        # whole heart-rate authority was ±5 bpm, and which was already 97 % saturated
        # after a 1000 mL bleed. That is narrower than the range of the CAROTID limb
        # measured alone (13.5 bpm, Fritsch), which a whole reflex cannot be.
        self._gain_hr       = HR_REFLEX_GAIN_BPM
        self._scale_hr      = HR_REFLEX_SCALE_MMHG
        self._frac_hr_vagal = _HR_VAGAL_FRACTION
        # Cardiopulmonary arm — its own switch, so it can be validated in
        # isolation and in combination. Without it the model cannot produce the
        # human hypovolaemic tachycardia AT ALL, by any choice of arterial gain,
        # because in that data there is no arterial error to respond to.
        self.cp_hr_enabled  = bool(cp_hr_enabled)
        self.cp_hr_ref_cvp  = float(cp_hr_ref_cvp)
        self._gain_hr_cp    = CP_HR_RESERVE_BPM
        self._scale_hr_cp   = CP_HR_RESERVE_BPM / CP_HR_GAIN_BPM_PER_MMHG
        # SVR gain 0.65. It had been reduced to 0.45 on the pre-rebuild model,
        # where the compressed venous compliance left the baroreflex-SVR loop
        # underdamped — a strong gain produced ~90 mmHg pulse-pressure oscillation
        # at steep tilt. The venous-system rebuild (physiological venous
        # compliance ~130 mL/mmHg) damps that loop, so the gain can be restored
        # to a physiological orthostatic level (max SVR ~1.65×) — needed to
        # defend MAP/cerebral perfusion at 45° upright — while MAP stays stable
        # (pulse-pressure oscillation < 8 mmHg at −26°). A nice consequence of
        # fixing the volume scale: stronger, more physiological reflex control.
        self._gain_svr      =   0.65
        self._gain_emax     =   0.20
        # Baroreflex venous-tone (venoconstriction) arm — wired through to venous
        # unstressed volume in circulation.py `_odes` (via `vt *= v0_vein_factor`).
        # Re-enabled at physiological gain after the venous-system rebuild
        # (compartments.py) gave the model physiological venous compliance and a
        # ~1.6 L stressed pool. Previously this arm had to be held at 0: with the
        # old compressed 0.7 L pool it over-recruited during hypovolaemia
        # (flattening PPV below the Michard threshold, blunting PLR) and
        # over-venodilated at high MAP (inverting the epinephrine dose-CO curve).
        # With leverage now ~±13 % (was ±48 %) the arm defends venous return in
        # the correct direction without those artefacts.
        self._gain_v0_vein  =   0.10

    def update(
        self,
        map_mmhg: float,
        pp_mmhg: float,
        cvp_mmhg: float,
    ) -> None:
        """Advance the controller by one simulation time step."""
        # Step 1 — input smoothing (removes pulsatility)
        self._map_buf.append(map_mmhg)
        self._cvp_buf.append(cvp_mmhg)
        avg_map = np.mean(self._map_buf)
        avg_cvp = np.mean(self._cvp_buf)

        # Step 2 — error signals (positive = pressure above setpoint)
        err_map = avg_map - self.map_set
        err_cvp = avg_cvp - self.cvp_set

        # Step 3 — IIR exponential filtering (y ← (1-α)y + αx)
        # Each filter has a distinct physiological time constant.
        self._para_map      = (1-self._a_para)*self._para_map      + self._a_para*err_map
        self._symp_fast_map = (1-self._a_fast)*self._symp_fast_map + self._a_fast*err_map
        self._symp_hr_map   = (1-self._a_symp_hr)*self._symp_hr_map + self._a_symp_hr*err_map
        err_cvp_cp          = avg_cvp - self.cp_hr_ref_cvp
        self._symp_hr_cvp   = (1-self._a_symp_hr)*self._symp_hr_cvp + self._a_symp_hr*err_cvp_cp
        self._symp_slow_map = (1-self._a_slow)*self._symp_slow_map + self._a_slow*err_map
        self._symp_fast_cvp = (1-self._a_fast)*self._symp_fast_cvp + self._a_fast*err_cvp

        # Step 4 — effector adjustments
        # HR: the vagal limb activates when MAP rises (slowing the heart) and
        # withdraws when it falls; the sympathetic limb does the reverse, more
        # slowly. Both read the same error, so they sum to one sourced curve.
        fv = self._frac_hr_vagal
        self.hr_delta = -self._gain_hr * (
            fv * _sigmoid(self._para_map,    scale=self._scale_hr)
            + (1.0 - fv) * _sigmoid(self._symp_hr_map, scale=self._scale_hr)
        )
        # Cardiopulmonary arm: falling filling pressure speeds the heart.
        if self.cp_hr_enabled:
            self.hr_delta += -self._gain_hr_cp * _sigmoid(
                self._symp_hr_cvp, scale=self._scale_hr_cp)

        # SVR: slow sympathetic sustains vasoconstriction when MAP is chronically low
        svr_err = -(self._symp_slow_map + self._symp_fast_cvp * 0.3)
        self.svr_factor     = 1.0 + self._gain_svr       * _sigmoid(svr_err, scale=15.0)
        self.emax_factor    = 1.0 + self._gain_emax      * _sigmoid(svr_err, scale=15.0)
        self.v0_vein_factor = 1.0 - self._gain_v0_vein   * _sigmoid(svr_err, scale=20.0)

        # Clamp to physiological limits.
        # SVR range tightened 0.3–3.0 → 0.5–1.8: prevents extreme vasoconstriction/
        # vasodilation that amplified oscillations at steep tilt angles.
        # HR: a GUARD, not the operative limit. The tanh saturates at
        # ±HR_REFLEX_GAIN_BPM (30) first and that is the sourced limit; these
        # bounds only stop a pathological error from producing a nonsense rate.
        # Before 2026-09-04 this clip was the reverse — it read as ±25/+40 while
        # the curve behind it saturated at ±5 bpm, so it could never be reached
        # and the real ceiling was invisible.
        self.hr_delta       = np.clip(self.hr_delta,       -35.0, 45.0)
        self.svr_factor     = np.clip(self.svr_factor,       0.5,  1.8)
        self.emax_factor    = np.clip(self.emax_factor,      0.5,  2.0)
        # Asymmetric: the baroreflex venous effector is active venoCONSTRICTION
        # reserve (v0_vein_factor < 1, recruits the reservoir to defend venous
        # return in hypotension/orthostatic stress). At high MAP the reflex only
        # WITHDRAWS this tone — passive venodilation is limited — so the factor is
        # capped at 1.0 rather than allowed to actively venodilate. Without this
        # cap, high-MAP venodilation drops preload enough to invert the
        # epinephrine dose–CO curve (a non-physiological artefact).
        self.v0_vein_factor = np.clip(self.v0_vein_factor,   0.75, 1.0)


def _sigmoid(x: float, scale: float = 10.0) -> float:
    """Soft-saturation: maps (−∞, +∞) → (−1, 1)."""
    return np.tanh(x / scale)
