"""
Time-varying elastance heart model (Suga & Sagawa 1974).

Implementation follows PMC9363491 and Heldt 2002:
  E(t) = (E_max - E_min) * e_n(t_n) + E_min

where e_n(t_n) is a normalised activation function that rises and falls
over the cardiac cycle, scaled to the current RR interval.
"""

import numpy as np


def _normalised_activation(t_n: float) -> float:
    """
    Normalised time-varying elastance curve over one cardiac cycle.
    t_n in [0, 1] (fraction of cardiac period).
    Returns e_n in [0, 1].

    Uses a double-Hill function approximation that matches the canonical
    Suga-Sagawa activation curve shape (systolic rise, diastolic fall).
    """
    # Systolic rise: peaks at t_n ≈ 0.3
    if t_n < 0.0 or t_n > 1.0:
        t_n = t_n % 1.0

    if t_n <= 0.30:
        # sinusoidal rise
        return 0.5 * (1 - np.cos(np.pi * t_n / 0.30))
    elif t_n <= 0.45:
        # sinusoidal fall from peak back to baseline
        return 0.5 * (1 + np.cos(np.pi * (t_n - 0.30) / 0.15))
    else:
        return 0.0


def elastance_from_phase(
    t_n: float,
    e_max: float,
    e_min: float,
) -> float:
    """
    Instantaneous ventricular elastance (mmHg/mL) from a cardiac-cycle phase.

    Parameters
    ----------
    t_n    : cardiac-cycle phase (fraction of RR interval, any real value —
             wrapped to [0, 1) internally)
    e_max  : peak systolic elastance (mmHg/mL)
    e_min  : diastolic elastance (mmHg/mL)
    """
    e_n = _normalised_activation(t_n)
    return (e_max - e_min) * e_n + e_min


def elastance(
    t: float,
    hr_bpm: float,
    e_max: float,
    e_min: float,
) -> float:
    """
    Instantaneous ventricular elastance (mmHg/mL).

    Parameters
    ----------
    t      : absolute time (s)
    hr_bpm : heart rate (beats per minute)
    e_max  : peak systolic elastance (mmHg/mL)
    e_min  : diastolic elastance (mmHg/mL)

    Note: with a continuously time-varying hr_bpm (e.g. baroreflex
    feedback), (t % T)/T is discontinuous every step and should not be
    used to drive the ODE — use a continuously-integrated phase with
    elastance_from_phase() instead. This wrapper remains for callers with
    a fixed hr_bpm.
    """
    T = 60.0 / hr_bpm          # cardiac period (s)
    t_n = (t % T) / T          # normalised phase [0, 1)
    return elastance_from_phase(t_n, e_max, e_min)


def frank_starling_emax(
    e_max_baseline: float,
    edv: float,
    edv_ref: float = 130.0,
    slope: float = 0.003,
) -> float:
    """
    Scale E_max with end-diastolic volume (Frank-Starling).

    Implements the two-region Starling curve:
    - Ascending limb (EDV < edv_ref): reduced E_max when underloaded (hypovolemia).
    - Plateau (EDV >= edv_ref): E_max capped at baseline — normovolemic supine subjects
      operate here, consistent with the finding that 20° HDT does not increase SV/CO
      in healthy supine volunteers (DOI: 10.14814/phy2.15216).

    Parameters
    ----------
    e_max_baseline : baseline E_max (mmHg/mL)
    edv            : current end-diastolic volume (mL)
    edv_ref        : EDV at which plateau begins (mL); default 130 mL
    slope          : ascending-limb sensitivity (mmHg/mL per mL deficit)
    """
    if edv >= edv_ref:
        return e_max_baseline                       # plateau: no further increase
    return e_max_baseline + slope * (edv - edv_ref)  # ascending limb: E_max reduced


# ---------------------------------------------------------------------------
# Default cardiac elastance parameters (healthy male, Heldt 2002)
# ---------------------------------------------------------------------------
LV_EMAX = 3.00   # mmHg/mL  left ventricle peak systolic elastance
LV_EMIN = 0.055   # mmHg/mL  left ventricle diastolic elastance
# RV_EMAX was 1.15 (Heldt 2002) until 2026-09-09. Replaced with a HUMAN
# MEASUREMENT: Richter MJ et al. 2021 (PMID 33655769,
# DOI 10.1152/ajplung.00583.2020) measured right-ventricular end-systolic
# elastance by conductance catheter with preload reduction, fitting a tangent
# across the end-systolic points of multibeat pressure-volume loops. In 15
# patients WITHOUT pulmonary hypertension:
#     Ees 0.7 [0.6-0.9] mmHg/mL     Ea 0.4 [0.3-0.5]     Ees/Ea 1.7 [1.1-2.3]
#
# The model was measured by the SAME method (graded preload reduction, reflex
# off) rather than by reading this constant: Ees came out 1.114 mmHg/mL with the
# elastance line intercepting the volume axis at 42.8 mL against the chamber's
# unstressed volume of 38, r2 0.9996. That measurement recovers this constant to
# within 3 %, which is what validates identifying end-systole at maximum P/V —
# so the constant is scaled by 0.7/1.114 to put the MEASURED Ees on Richter's
# median. Full record in docs/validation_log.md, 2026-09-09.
#
# CAVEAT KEPT DELIBERATELY: Richter's controls are dyspnoeic referrals with a
# mean PA pressure of 19 mmHg, which is upper-normal, not healthy volunteers. A
# mildly pressure-loaded right ventricle would if anything have a HIGHER Ees, so
# the direction of this change is safe even though the cohort is not ideal. A
# healthy-volunteer RV Ees is on the WANTED list in docs/reference_values.md.
RV_EMAX = 0.72   # mmHg/mL  right ventricle peak systolic elastance
# The RV is highly compliant in diastole (thin wall). Measured: P_rv_dia = 1.68 mmHg
# at RV Vmin 80 mL, which is what lets the RA sit low enough to be a plausible CVP.
RV_EMIN = 0.04   # mmHg/mL  right ventricle diastolic elastance
# RA_EMAX 0.30 -> 0.45 (2026-08-26), derived from Gao 2022's RA emptying fraction.
# E_max/E_min is the RATIO that sets emptying fraction, which is why it is derivable even
# though the atrium's absolute stiffness is not (see RA_EMIN below, and the note on
# Ferguson 1989 in docs/reference_values.md — that paper's volumes are in RELATIVE units).
# Sweep with E_min held at 0.20:
#   E_max   RAEF      RA Vmin        (Gao n=408: RAEF 49.7 +/- 9.2 %, RAVmin 17.1 +/- 5.6 mL/m2)
#    0.30   39.0 %    34.7 mL / 18.8 mL/m2
#    0.45   49.5 %    28.7 mL / 15.5 mL/m2
#    0.50   51.6 %    27.5 mL / 14.9 mL/m2
# 0.45 hits the emptying fraction almost exactly and leaves Vmin inside 1 SD of Gao. RA
# Vmax is unmoved at 56.8 mL, so this costs nothing on the volume side.
# It also drops reported CVP as a CONSEQUENCE — a harder atrial contraction empties the
# chamber further during the x descent, and CVP is reported as a rolling minimum:
# 5.20 -> 4.89 on the default patient with reflexes off, and 6.0 -> 5.7 on the 175/75
# fixture that test_cvp_baseline_calibration uses. That is not why the value was chosen
# and it does not close the CVP gap; see backlog item 28.
RA_EMAX = 0.45   # mmHg/mL  right atrium peak systolic elastance
# RA_EMIN IS SET BY VOLUME, NOT BY PRESSURE — do not lower it to chase CVP.
#
# The comments here used to derive RA_EMIN from an "equilibrium RA pressure ≈ 3.8 mmHg",
# and they described values (0.04, and RV_EMIN 0.02) that the 2026-08-24 chamber rebuild
# had already replaced. Both the values and the reasoning were stale. Measured on
# 2026-08-25 by sweeping RA_EMIN over 3x with everything else held:
#
#   RA_EMIN   mean RA P    RA Vmax     (Gao 2022 CMR target: RA Vmax 62.5 mL @ BSA 1.845)
#     0.200      6.37       56.8
#     0.097      6.19       92.0
#     0.064      5.99      121.5
#
# A threefold change in atrial stiffness moves mean RA pressure by 0.4 mmHg and more than
# doubles the volume. That is the expected behaviour of a low-pressure chamber in a closed
# loop: the circulation IMPOSES the pressure, and the chamber's elastance sets how much
# volume it takes up at that pressure. CVP is a venous-filling quantity — it belongs to
# mean systemic filling pressure and total vascular compliance (backlog item 28), not here.
# 0.200 is the best volume match of the sweep; test_atrial_volumes_are_physiological
# (RAVmax band 20-48 mL/m2) fails at 0.097 and below.
RA_EMIN = 0.20   # mmHg/mL  right atrium diastolic elastance
LA_EMAX = 0.45   # mmHg/mL  left atrium

# LEFT ATRIAL DIASTOLIC ELASTANCE — DERIVED FROM GAO, NOT FITTED (2026-08-31).
#
# Was 0.28, unsourced. Gao 2022 (PMID 35124105) gives the compliance directly:
# the left atrium accepts LAVmax - LAVmin = 68 - 26.5 = 41.5 mL while its
# pressure rises from roughly 5 to 13 mmHg (v-wave), which is 5.19 mL/mmHg —
# an elastance of 8/41.5 = 0.19 mmHg/mL. The model's atrium was ~1.5x too
# stiff.
#
# WHY IT MATTERED, and it was not a small effect. At 0.28 the LA reached
# 21.6 mmHg at peak volume against a real v-wave of 10-15. That over-pressure
# filled the left ventricle completely during PASSIVE diastole: the LV hit
# 10.1 mmHg — its full end-diastolic pressure — BEFORE the atrium contracted,
# so the atrial kick added 1.7 mL. Measured consequences at 0.28 were LAEF
# passive 56.6 % against Gao's 35.6, atrial contribution to LV filling 6.7 %
# against Alhogbani's 22-38.5 (PMID 23097384), and E/A 21.5 against NORRE's
# 1.22 (PMID 25896355). In a real heart pre-A pressure is 5-7 and the kick
# raises it to 10-12.
#
# WHAT WAS RULED OUT FIRST, all recorded in the validation log: mitral
# resistance (reaching the ACC band produces mitral stenosis — mean PA 30.8,
# PCWP 23.0), LA_EMAX alone (moves the booster but LAEF passive is invariant),
# LA unstressed volume (15 -> 45 mL leaves peak pressure and ACC completely
# unchanged, because the closed loop imposes the pressure), and lv_emin
# (hits LAEF passive exactly but drives LVEDP to 20.4 mmHg, which is failure).
#
# A MORE COMPLIANT 0.10 FITS MORE ENDPOINTS AND IS DELIBERATELY NOT USED. It
# would give LAEF passive 37.8, ACC 36.1 and E/A 2.09, and would close both
# currently-xfailed pulmonary assertions — but it is twice as compliant as
# Gao's own volume-and-pressure data support, and it drives LAVmax to
# 62.9 mL/m2 against Gao's 36.9 +/- 7.7. Fitting five numbers by adopting a
# compliance the source contradicts is the failure mode this project keeps
# catching.
#
# WHAT 0.19 DOES NOT FIX. LAEF passive stays near 49 % and total near 74 %.
# The residual is a VOLUME DISTRIBUTION problem, not an atrial one: LA peak
# pressure is imposed by the circulation, so a compliant atrium is necessarily
# a bigger one at that pressure, and the pulmonary vessels hold 365.8 mL
# (7.1 % of blood volume) where the literature has 450-500 mL and 9-11 %. The
# vessels are under-filled while the atrium is over-filled. See backlog 25a.
LA_EMIN = 0.19   # mmHg/mL

# ---------------------------------------------------------------------------
# ATRIOVENTRICULAR DELAY — the PR interval, as a TIME rather than a fraction
# ---------------------------------------------------------------------------
# Atrial contraction precedes ventricular contraction by the PR interval. In
# this model, cardiac phase 0 is the onset of VENTRICULAR activation and the
# atrial activation curve starts at its own phase 0, so the offset between them
# IS the PR interval expressed as a fraction of the cardiac period.
#
# WHAT WAS HERE BEFORE, AND WHY IT WAS WRONG. `ATRIAL_PHASE_OFFSET = 0.60`,
# from the initial commit, unsourced, with no test constraining it. A fixed
# 0.60 of the cycle at the reference 70 bpm is a PR interval of 514 ms — more
# than double the upper limit of normal, and into complete-heart-block
# territory. Measured against the volume traces it put the atrial kick in
# MID-DIASTOLE, so the atrium was contracting while the mitral valve was shut
# and it was still filling from the pulmonary veins. LA volume ROSE from 40 to
# 88 mL while atrial activation climbed from 0 to 0.93.
#
# Normal PR interval is 120-200 ms in adults; 160 ms is the mid-normal value
# and is what is used here.
ATRIAL_PR_INTERVAL_S = 0.16

# PR is a fixed TIME, not a fixed fraction of the cycle. That distinction
# matters here because heart rate moves substantially in the scenarios this
# model is validated on — baroreflex, tilt, haemorrhage, vasopressors — and a
# fixed fraction would slide the atrial kick out of end-diastole exactly when
# the reflex is doing the most work. At 70 bpm the offset is 0.187; at 150 bpm
# a fixed 0.187 would imply a PR of only 75 ms.
#
# Real PR does shorten a little as rate rises, but far less than cycle length
# does, so holding it constant is much closer than holding the fraction
# constant. The clamp keeps the atrial kick from colliding with ventricular
# systole at extreme tachycardia, which is itself physiological — at high
# enough rates atrial and ventricular events do merge.
def atrial_phase_offset(hr_bpm: float) -> float:
    """Atrial activation offset (fraction of the cardiac cycle) at this rate."""
    period_s = 60.0 / max(1e-6, hr_bpm)
    return min(0.45, ATRIAL_PR_INTERVAL_S / period_s)
