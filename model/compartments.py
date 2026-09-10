"""
Vascular compartment definitions for the lumped-parameter cardiovascular model.

Based on the 23-compartment structure extended from:
  Heldt T et al. (2002) J Appl Physiol 92:1239-1254
  PMC9363491 — cardiovascular model for orthostatic stress / spaceflight

The original single lower_body_vein compartment has been split into three
anatomically-placed segments (thigh_vein, calf_vein, foot_vein) to correctly
simulate the ~640 mL venous pooling observed on standing (Sjöstrand 1953).
"""

from dataclasses import dataclass, field


@dataclass
class Compartment:
    """
    One lumped vascular compartment.

    Parameters
    ----------
    name : str
    compliance : float
        mL/mmHg — relates stressed volume to pressure
    resistance : float
        mmHg·s/mL — outflow resistance to the next compartment
    unstressed_volume : float
        mL — volume at zero transmural pressure
    height_m : float
        metres above heart level (negative = below heart).
        Used to compute the hydrostatic pressure column when tilted.
    init_volume : float
        mL — initial volume for ODE state vector (defaults to unstressed_volume)
    """

    name: str
    compliance: float       # mL/mmHg — low-pressure compliance C0
    resistance: float       # mmHg·s/mL  (outflow to next compartment)
    unstressed_volume: float  # mL
    height_m: float = 0.0   # metres from heart level
    init_volume: float = field(default=None)
    # Nonlinear (collapsible-vein) pressure–volume behaviour. When set, the
    # compartment stiffens above transmural pressure `p_stiffen` (mmHg) via an
    # exponential tube law: P = k·(exp(Vs/(C0·k)) − 1), Vs = stressed volume.
    # dP/dVs → 1/C0 at Vs→0 (compliant, e.g. supine/leg-raised) and rises with
    # volume (low incremental compliance when dependent → self-limiting pooling).
    # None → linear P = Vs/C0. Used for the limb veins so they hold recruitable
    # volume supine yet do not pool catastrophically upright.
    p_stiffen: float | None = None
    # Drainage resistance out of an exchange bed toward the great veins
    # (mmHg·s/mL). Only meaningful for the systemic venous compartments.
    #
    # WHY THIS EXISTS. `renal_vein` and `splanchnic_vein` previously used a single
    # `resistance` value for BOTH the artery→vein flow through the exchange bed and
    # the vein→IVC drainage — one number doing two physiologically distinct jobs,
    # so neither could be changed without silently changing the other. Backlog
    # item 20 needs exactly that separation: the exchange segment carries the
    # arteriolar resistance and sets capillary pressure, while drainage sets
    # venous return. They are not the same quantity and must not share a field.
    #
    # None → falls back to `resistance`, which reproduces the old shared behaviour.
    drain_resistance: float | None = None

    def __post_init__(self):
        if self.init_volume is None:
            self.init_volume = self.unstressed_volume
        if self.drain_resistance is None:
            self.drain_resistance = self.resistance

    def pressure(self, volume: float) -> float:
        """Transmural pressure from stressed volume (mmHg)."""
        vs = volume - self.unstressed_volume
        if self.p_stiffen is None or vs <= 0.0:
            return vs / self.compliance
        import numpy as _np
        return self.p_stiffen * (_np.exp(vs / (self.compliance * self.p_stiffen)) - 1.0)


# ---------------------------------------------------------------------------
# Cardiac valve resistance (mmHg·s/mL).
# Must satisfy: VALVE_R * C_min > dt for Euler stability.
# With C_min = 0.05 and dt = 0.001 s → VALVE_R > 0.02.
# ---------------------------------------------------------------------------
# VALVE_R must satisfy: VALVE_R * C_aorta > dt for Euler stability at dt=0.001 s.
# With C_aorta=0.50 → need VALVE_R > 0.002 s. Using 0.08 limits peak valve flow
# to ~500 mL/s (physiological) and keeps LV-aortic ΔP ≈ 40 mmHg during ejection.
VALVE_R = 0.01

# ---------------------------------------------------------------------------
# THE FOUR VALVES, EACH WITH ITS OWN PARAMETER (2026-08-31, for backlog 25a)
# ---------------------------------------------------------------------------
# Every other flow in this model follows one convention: a compartment's
# `resistance` is its INFLOW resistance, so flow from A to B divides by
# B.resistance (see Q_ao_brachio -> R("brachiocephalic")). The valves followed
# it too, and that is self-consistent — but it left three problems for anyone
# working on the left-heart coupling:
#
#   1. MITRAL AND AORTIC SHARED ONE NUMBER. Both divided by
#      left_ventricle.resistance, so mitral resistance could not be changed
#      without also changing aortic. That blocks item 25a outright.
#   2. left_atrium.resistance AND right_atrium.resistance WERE NEVER READ.
#      Under the inflow convention an atrium's inflow is the upstream vein's
#      drain_resistance, so the atrial `resistance` field did nothing. Setting
#      it looked reasonable and was silently ignored — it swallowed a whole
#      parameter sweep on 2026-08-31 before the flat results gave it away.
#   3. THE PULMONIC VALVE WAS 0.03 WHILE THE OTHER THREE WERE 0.01, because
#      pulmonary_art.resistance served double duty as both the pulmonic valve
#      and the PA inflow resistance. Whether 3x is intended is an open
#      question — it is preserved here, not silently normalised.
#
# The aortic valve already deviated from the convention deliberately, with a
# comment, because aorta.resistance is the systemic arterial resistance rather
# than a valve. Naming all four removes the ambiguity instead of having one
# documented exception to a rule the reader has to infer.
#
# VALUES ARE UNCHANGED FROM WHAT THE FLOW EQUATIONS ACTUALLY USED, so this is
# a pure refactor — see test_valve_resistances_are_a_pure_refactor.
TRICUSPID_R = VALVE_R      # was right_ventricle.resistance
# PULMONIC_R was 0.03 until 2026-09-10, three times the other three valves.
# The naming commit preserved that rather than normalising it and left the
# question open in writing: "whether 3x is intended". MEASURED, AND IT IS NOT.
#   peak pulmonic gradient  15.93 mmHg   (aortic 8.55)
#   mean over ejection       9.44 mmHg   (aortic 4.17)
# A peak gradient under 10 mmHg is normal and 10-40 is mild stenosis, so the
# model had a mild functional pulmonic stenosis. It is why RV peak pressure read
# 40.99 while pulmonary artery systolic was only 29.82 — eleven mmHg of the
# right ventricle's work never reached the artery.
# The 0.03 was inherited because `pulmonary_art.resistance` served double duty
# as the pulmonic valve AND the PA inflow resistance. The refactor separated
# them; only the value carried over. `pulmonary_art.resistance` is now read by
# nothing in `_odes` — the PA-to-capillary flow uses `pulmonary_cap.resistance`.
# ANATOMY, NOT TIDINESS: the pulmonic and aortic valves are comparable semilunar
# orifices and the pulmonic annulus is if anything the larger of the two, so
# there is no basis for the pulmonic being the more resistive.
PULMONIC_R  = VALVE_R      # was 0.03; see above and validation_log 2026-09-10
MITRAL_R    = VALVE_R      # was left_ventricle.resistance
AORTIC_R    = VALVE_R      # was left_ventricle.resistance

# ---------------------------------------------------------------------------
# ORIFICE (BERNOULLI) VALVE FLOW — optional, off by default
# ---------------------------------------------------------------------------
# A heart valve is an ORIFICE, not a pipe. Poiseuille flow through a tube gives
# Q proportional to dP; flow through an orifice is inertial and gives
# dP proportional to Q^2, i.e. Q proportional to sqrt(dP). This is why the
# clinical gradient equation is the simplified Bernoulli dP = 4v^2, and why
# Gorlin's formula solves for valve AREA rather than resistance:
#
#     A (cm2) = Q (mL/s) / (44.3 * C * sqrt(dP))     ->    Q = 44.3 * C * A * sqrt(dP)
#
# so the orifice coefficient is K = 44.3 * C * A, in mL/s per sqrt(mmHg).
#
# WHY IT MATTERS HERE. Under a linear law the ratio of two flows equals the
# ratio of their driving pressures; under an orifice law it equals the SQUARE
# ROOT of that ratio. The model's mitral E/A is 21.5 against NORRE's 1.22
# precisely because early filling has a large gradient and the atrial kick a
# small one. Square-rooting compresses that ratio toward sqrt(21.5) ~ 4.6 —
# it blunts the E wave and spares the A wave, which is the direction the
# left-atrial phasic function needs, and it comes from correct physiology
# rather than from a fitted parameter.
#
# AREAS ARE TEXTBOOK CLINICAL RANGES AND ARE NOT PROPERLY SOURCED YET. Normal
# mitral 4-6 cm2, aortic 3-4, tricuspid 7-9, pulmonic ~3-4. Midpoints are used.
# Discharge coefficients are Gorlin's: 0.85 for the atrioventricular valves,
# 1.0 for the semilunar ones. IF THIS MECHANISM IS ADOPTED, these four numbers
# need a primary source before they can be load-bearing.
GORLIN_CONST = 44.3        # hydraulic constant, mL/s per cm2 per sqrt(mmHg)

VALVE_AREA_CM2 = {"mitral": 5.0, "aortic": 3.5, "tricuspid": 8.0, "pulmonic": 3.5}
VALVE_CD       = {"mitral": 0.85, "aortic": 1.0, "tricuspid": 0.85, "pulmonic": 1.0}

def orifice_k(valve: str) -> float:
    """Orifice coefficient K = 44.3 * Cd * A, so that Q = K * sqrt(dP)."""
    return GORLIN_CONST * VALVE_CD[valve] * VALVE_AREA_CM2[valve]

# Regularisation. Q = K*sqrt(dP) has infinite slope at dP = 0, which with
# forward Euler at dt = 1 ms would chatter every time a valve opens or closes.
# The form actually used is
#
#     Q = K * dP / sqrt(dP + dP_c)
#
# which tends to K*sqrt(dP) for dP >> dP_c, becomes LINEAR with slope
# K/sqrt(dP_c) for dP << dP_c, and is smooth with finite slope at the origin.
# One expression, no branch, no discontinuity in value or derivative.
# At dP_c = 0.1 mmHg the near-zero slope is ~3.2*K, giving an effective
# resistance of ~0.0017 mmHg*s/mL for the mitral valve; against the smallest
# diastolic chamber compliance (~5 mL/mmHg) that is R*C ~ 9 ms, comfortably
# above the 1 ms timestep.
VALVE_DP_REG = 0.1         # mmHg

# Great-vein -> atrium resistance. NOT A VALVE. See backlog item 23.
# Kept for the PULMONARY venoatrial junction (pulmonary_vein -> LA), which is a
# different circulation and was not part of the 2026-08-26 systemic rework.
VENOATRIAL_R = 0.02

# Cava -> right atrium (SVC and IVC). Split out from VENOATRIAL_R and raised
# 0.02 -> 0.04 on 2026-08-26 as part of the resistance-to-venous-return work,
# backlog item 28. See VENOUS_DRAINAGE_SCALE below for the whole change.
CAVOATRIAL_R = 0.04


# ---------------------------------------------------------------------------
# Compartments whose `resistance` field carries the systemic ARTERIOLAR
# resistance, i.e. the artery→vein exchange segment of each bed.
#
# Since 2026-08-21 the arteriole sits on the flow OUT of each `*_art` compartment
# rather than into it (backlog item 20), so the arteriolar resistance is stored on
# the downstream venous compartment. Anything scaling systemic vascular resistance
# — the patient calibration in patient.py, drug `svr_factor`, the baroreflex —
# must act on THESE, not on the `*_art` compartments, which now hold only small
# conduit resistances. Their `drain_resistance` is a separate, postcapillary
# quantity and must NOT be scaled by an arteriolar factor.
# ---------------------------------------------------------------------------
ARTERIOLAR_SEGMENTS = (
    "upper_body_vein", "renal_vein", "splanchnic_vein",
    "thigh_vein", "calf_vein", "foot_vein",
)


# ---------------------------------------------------------------------------
# VENOUS COMPLIANCE AND DRAINAGE — reworked 2026-08-26, backlog item 28.
#
# Two changes applied together, because each alone makes the model worse and
# they were cancelling each other:
#   venous compliance    x0.80   (upper_body_vein, svc, renal_vein,
#                                 splanchnic_vein, thigh/calf/foot, ivc)
#   venous drainage      x2      (each vein's drain_resistance, and the cava ->
#                                 RA resistance CAVOATRIAL_R 0.02 -> 0.06)
# The x3 is taken OUT of each bed's exchange segment so every bed's TOTAL
# artery-to-cava resistance is unchanged: 3.850, 4.700, 3.740, 9.633, 7.050,
# 9.403 before and after. Total systemic resistance, and therefore MAP at a
# given cardiac output, is preserved by construction.
#
# WHY. Maas 2009 (PMID 19237896) measured the venous return curve directly in
# humans — slope -0.465 +/- 0.151 L/min/mmHg, i.e. resistance to venous return
# Rvr = 0.129 mmHg.s/mL, with Rvr/Rsys = 15 %. The model had Rvr = 0.054 and
# Rvr/Rsys = 5.6 %: total systemic resistance was right but only ~5 % of it sat
# downstream of the mean-filling-pressure point where humans have ~15 %.
#
# WHY BOTH AT ONCE. CO = (MSFP - CVP)/Rvr and MSFP = stressed volume /
# compliance, and MSFP is a ZERO-FLOW quantity so no rearrangement of
# resistances can change it. Raising Rvr alone therefore just throttles venous
# return — measured: MAP fell to 59.5 and CO to 3.15. Lowering compliance alone
# raises filling pressure with nothing to absorb it — measured: CO 10.5, SV 161.
# For a normal operating point the two are tied:
#     MSFP = CVP + CO x Rvr = 3 + 100 x 0.129 = 15.9 mmHg
#
# THE SCALES ARE SET BY THE MEASURED SLOPE, NOT BY THAT ARITHMETIC. A first pass
# used x0.66 / x3, derived from Rvr computed against the ZERO-FLOW MSFP. Measured
# with Maas's own hold protocol that overshot — slope -0.346 against his -0.465,
# i.e. venous resistance 1.33x too HIGH. The zero-flow MSFP and the extrapolated
# intercept are different quantities and only the latter is what Maas reports.
# Retuned against the measured slope:
#     x0.66 / x3   slope -0.346  (0.74x)   pmsf 21.12
#     x0.80 / x2   slope -0.456  (0.98x)   pmsf 17.38   <- chosen
#     x0.90 / x1.6 slope -0.530  (1.14x)   pmsf 15.43
# Resulting systemic compliance ~1.41 mL/mmHg/kg: at the bottom of the 30-second
# animal range (1.4-2.6) and above Maas's 20-minute reflex-intact 0.98, which is
# where a passive compliance belongs relative to those two methods.
#
# THIS IS A DERIVATION, NOT A FIT. The compliance falls out of the model's own
# identities plus one directly measured quantity; it does not use Maas's own
# compliance figure, which is not comparable (he measures >20 min after loading
# in reflex-intact patients, where the model's C is passive). Two independent
# checks it was not fitted to: the resulting 1.17 mL/mmHg/kg lands BETWEEN
# Maas's 0.98 and the 30-second animal range of 1.4-2.6, which is where a
# passive compliance belongs relative to those two methods; and the model's
# Maas-style extrapolated MSFP comes out ~19.4 against his measured 18.76.
#
# Full record in docs/validation_log.md under "Item 28".
VENOUS_COMPLIANCE_SCALE = 0.80   # documentation only; values are inlined below
VENOUS_DRAINAGE_SCALE = 2.0      # documentation only; values are inlined below


# ---------------------------------------------------------------------------
# Baseline 23-compartment parameter set
# Compartment order (indices 0-22) matches circulation.py state vector.
#
# Parameter values from Heldt 2002 Table 1 and PMC9363491 Supplementary.
# Heights measured from heart centroid in supine (horizontal) reference:
#   positive = head-ward, negative = foot-ward.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# PULMONARY COMPLIANCE — raised 9.5x on 2026-09-03
# ---------------------------------------------------------------------------
# The pulmonary bed was the stiffest part of this model by a wide margin: a
# whole-bed compliance of 1.70 mL/mmHg (0.40 + 0.50 + 0.80), against systemic
# veins carrying 60+. A pulmonary circulation that stiff cannot act as a
# reservoir, and it showed: the bed held 23.7 mL of STRESSED volume, i.e. it was
# almost entirely unstressed volume with nothing to give.
#
# THREE INDEPENDENT MEASUREMENTS SAID THE SAME THING.
#   Claessen 2015 (PMID 25801760, n=14 HEALTHY controls, CMR with simultaneous
#     invasive pressure): pulmonary ARTERIAL compliance 9.7 +/- 3.1 mL/mmHg —
#     the arterial segment ALONE measured nearly 6x the model's entire bed.
#   Ugander 2021 (PMID 34706735, n=21 healthy controls, CMR): pulmonary blood
#     volume 526 +/- 87 mL against the model's 364.
#   Heldt 2002 Table 3: pulmonary arteries 4.3, pulmonary veins 8.4. NOT a
#     target — CLAUDE.md forbids treating the ancestor model as ground truth —
#     but it is independent corroboration of the same order.
#
# THE FACTOR IS 5.0, CHOSEN AS THE INTERSECTION OF FIVE MEASURED BANDS — and
# the first attempt at 9.5 was wrong for an instructive reason. 9.5 landed
# pulmonary blood volume exactly on Ugander's MEAN (527 vs 526) and broke two
# atrial tests: LA emptying fraction fell to 40.6 % against Gao's 61.1 +/- 6.2,
# and female RAVmax to 25.4 against a 27-38 band.
#
# The mistake was optimising ONE endpoint when several constrain the same
# parameter, and the volume target is the LOOSEST of them: Ugander's +/- 87 mL
# is +/- 17 %, while the atrial emptying fraction is +/- 10 %. Sweeping 1x to
# 9.5x and reading every bound gives:
#     PBV 439-613 (Ugander 526 +/- 87)             -> x >= 4.7
#     transit time 4.3-7.1 s (Ugander 5.7 +/- 1.4) -> x >= 4.4
#     LAEF total 45-72 % (Gao 61.1 +/- 6.2)        -> x <= 5.7
#     LAVmax index 37-48 (Gao 36.9 at 44, Ugander 48.4 at 61) -> x <= 5.5
#     RAVmax index >= 27 (Gao 33.9 +/- 8.9)        -> x <= 7.5
# The feasible interval is [4.7, 5.5] and 5.0 sits in it with margin on both
# sides. Every bound above is a measured human range, so this is not a
# compromise between a target and a test — it is the region where the model is
# simultaneously consistent with all of them.
#
# WHAT THE RESULTING NUMBER IS, STATED HONESTLY. Whole-bed compliance becomes
# 8.50 mL/mmHg, which is BELOW Claessen's 9.7 for the arterial segment alone.
# Those are not directly comparable — Claessen's PAC is the SV/PP estimate,
# which lumps in downstream capacitance during ejection and is known to run
# high — but it means Claessen is NOT the source for this value. Claessen
# establishes the ORDER, and that the old 1.70 was indefensible. The value
# itself is set by the joint volume-and-atrial constraint above.
#
# THE EXISTING ARTERY:VEIN SPLIT WAS ALREADY RIGHT — only the scale was wrong.
# After scaling, vein/artery compliance is 7.60/3.80 = 2.00, against Heldt's
# 8.4/4.3 = 1.95. That the ratio survives untouched is a sign this was a single
# scale error rather than a distribution error.
#
# WHAT IT FIXES, all measured: pulmonary blood volume 364 -> 527 (Ugander 526),
# pulmonary transit time 3.60 -> ~5.5 s (Ugander 5.7 +/- 1.4), mean PA
# 19.6 -> ~16.6, wedge 11.4 -> ~9.1, and — not anticipated — indexed LAVmax
# 56.3 -> ~33, because blood that had nowhere compliant to sit was pooling in
# the left atrium. That last effect reaches backlog item 25a's gap A, which
# five atrial parameters had failed to move.
#
# WHAT IT DOES NOT FIX: mean PA stays well above Claessen's measured 10 +/- 3.
# Compliance is not the lever for that — sweeping it 25x moved mPAP only
# 19.6 -> 14.3 while total pulmonary vascular resistance sat at ~235
# dyn.s.cm-5 throughout, against Claessen's measured 134 +/- 49. PRESSURE IS
# SET BY RESISTANCE AND FLOW, VOLUME BY COMPLIANCE, and they are separable.
# The resistance half is logged as its own finding and is NOT changed here.


def default_compartments() -> list[Compartment]:
    """
    Return the 23 baseline compartments in canonical index order.

    Parameters calibrated to reproduce resting haemodynamics:
      MAP ≈ 90 mmHg, CO ≈ 5 L/min, CVP ≈ 5 mmHg, HR = 70 bpm
      SVR_target = (MAP-CVP)/CO = 1.02 mmHg·s/mL
      Total arterial C ≈ 1.5 mL/mmHg → Windkessel τ = C·SVR ≈ 1.5 s
        → DBP ≈ SBP·exp(-T_dia/τ) ≈ 120·exp(-0.57/1.5) = 82 mmHg ✓

    init_volume gives physiological resting pressure in each compartment:
      Arterial: P₀ ≈ 90 mmHg  → V_init = V0 + P₀·C
      Venous:   P₀ ≈ 8 mmHg   → V_init = V0 + P₀·C
      Cardiac (elastance model): V_init = V0 + P₀/E_min

    The lower body venous return is modelled as three serial segments:
      foot_vein → calf_vein → thigh_vein → ivc
    Anatomical heights reproduce correct hydrostatic column at 90° upright
    (IVC reference h=−0.15 m), giving substantially more pooling than the
    old single-compartment approximation (Sjöstrand 1953).
    Hydrostatic columns at 90° upright:
      thigh (h=−0.20): ΔP= 3.9 mmHg
      calf  (h=−0.55): ΔP=31.2 mmHg
      foot  (h=−0.85): ΔP=54.6 mmHg
    Pooling ΔV ∝ C × ΔP_hydrostatic per segment.
    """
    return [
        # idx  name                    C(mL/mmHg)  R(mmHg·s/mL)   V0(mL)  h(m)   init_vol(mL)
        # ---- Systemic arterial (large compliant vessels + arterioles) ----
        #
        # ARTERIOLAR RESISTANCE PLACEMENT (fixed 2026-08-21, backlog item 20).
        # `resistance` is the resistance on the flow INTO this compartment. The
        # arteriolar resistance used to sit here, on the inflow to each `*_art`
        # compartment, which put the whole arteriolar pressure drop UPSTREAM of it:
        # `upper_body_art` settled at 8.6 mmHg while its own init_volume
        # (72 = V0 50 + C 0.25 x 88) and the comment below both say 88 mmHg.
        # Capillary pressure, computed between `*_art` and `*_vein`, was therefore
        # pinned to venous pressure at ~6.8 mmHg against a physiological ~20.
        # The arteriole now sits on the artery→vein segment where the exchange
        # vessels actually are; each `*_art` keeps only a small conduit resistance.
        # Artery→vein TOTALS are unchanged per bed, so systemic resistance, MAP and
        # cardiac output are preserved (measured: CO 4.131 -> 4.140).
        # See docs/validation_log.md "Backlog 20 diagnosed".
        Compartment("aorta",               0.50, 0.05,  100,  0.05,  145),  # 0  P0=90
        Compartment("brachiocephalic",     0.12, 0.05,   30,  0.15,   41),  # 1  P0=91
        Compartment("upper_body_art",      0.25, 0.10,   50,  0.25,   72),  # 2  P0=88 (conduit; arteriole moved to upper_body_vein)
        # Heights reference the volume-weighted thoracic venous centroid (~heart
        # level), not the neck: with physiological compliance the hydrostatic term
        # C·ΔP dominates tilt redistribution, so a mid-neck height (0.15-0.20) would
        # pool ~200 mL into the upper body in head-down tilt and steal preload.
        Compartment("upper_body_vein",    12.00, 3.75,  350,  0.05,  440,
                    drain_resistance=0.100),  # 3  P0≈6 (R = arteriole + exchange segment)
        Compartment("svc",                 8.00, 0.05,   70,  0.05,  110, drain_resistance=CAVOATRIAL_R),  # 4  P0≈4
        Compartment("abdominal_aorta",     0.25, 0.05,   60, -0.10,   82),  # 5  P0=88
        Compartment("renal_art",           0.05, 0.10,   20, -0.10,   24),  # 6  P0=80 (conduit; arteriole moved to renal_vein)
        # renal_vein / splanchnic_vein: `resistance` is the artery→vein exchange
        # segment; `drain_resistance` is the vein→IVC drainage. These were a single
        # shared number until 2026-08-21 — see Compartment.drain_resistance.
        Compartment("renal_vein",          7.20, 4.50,   60, -0.10,  132,
                    drain_resistance=0.200),                                # 7  P0≈8
        Compartment("splanchnic_art",      0.12, 0.10,   50, -0.15,   60),  # 8  P0=83 (conduit; arteriole moved to splanchnic_vein)
        Compartment("splanchnic_vein",    52.00, 3.60, 1200, -0.08, 1920,
                    drain_resistance=0.140),  # 9  P0≈11 (dominant mobilizable reservoir)
        Compartment("lower_body_art",      0.35, 0.30,   80, -0.50,  111),  # 10 P0=89 (conduit; arteriole moved to the leg exchange branches)
        # ---- Lower body venous: foot→calf→thigh→ivc (outflow resistance on each segment) ----
        # Compliances reproduce the ~640 mL venous pooling on standing documented by
        # Sjöstrand (1953, DOI: 10.1152/physrev.1953.33.2.202).
        #
        # Hydrostatic pooling at 90° upright, relative to supine equilibrium (~13 mmHg):
        #   thigh (h=−0.20m): ΔV = 5 × (8.9−13) = −20 mL  (above IVC → decompresses)
        #   calf  (h=−0.55m): ΔV = 9 × (36.2−14) = +200 mL
        #   foot  (h=−0.85m): ΔV = 7 × (59.6−14) = +319 mL
        #   Net ≈ +500–600 mL (vs Sjöstrand target 640 mL) ✓
        #
        # Supine equilibrium pressures (from analytical flow balance):
        #   P_lb_art_eq ≈ 15.7 mmHg, P_thigh_eq ≈ 12.7, P_calf_eq ≈ 13.6, P_foot_eq ≈ 14.2 mmHg
        # Vinit = V0 + C × P_eq (gives correct starting point, avoids large initial transient).
        # Total lower body venous volume at supine: ~1186 mL (physiologically normal).
        #
        # Euler stability at dt=0.001 s: τ_min = C / Σconductances > 0.2 s for all segments ✓
        # Compliances calibrated to give maximum orthostatic pooling while keeping 45° upright
        # MAP ≥ 60 mmHg and supine hemodynamics within physiological range.
        # Vinit set at analytical steady-state supine pressures (≈12.5 / 13.0 / 13.5 mmHg),
        # not at P=8 mmHg, to avoid a large initial transient that drains central circulation.
        #
        # At 45° upright: ΔV ≈ +130 mL pooling.
        # At 90° upright: ΔV ≈ +220 mL (vs old single-vein 73 mL).
        # Full Sjöstrand 640 mL requires the active muscle pump (absent in sedated patients).
        # Limb veins use the nonlinear tube law (p_stiffen): compliant when
        # filling (supine/leg-raised → hold recruitable volume, restore PLR
        # response) but self-limiting when dependent (upright → pooling capped,
        # no MAP collapse). C0 is the low-pressure compliance.
        # Leg veins follow the same convention as the other exchange beds:
        # `resistance` is the arteriole + exchange segment feeding the compartment,
        # `drain_resistance` is its outflow (foot→calf→thigh→IVC). The exchange
        # resistances were hard-coded inside `_odes` until 2026-08-21, which put
        # them out of reach of both the patient SVR calibration and the PAD factor.
        # They carry the 2.80 arteriolar resistance that used to sit on
        # lower_body_art's inflow, split 30/40/30 across the three segments:
        #   2.80/0.30 = 9.33,  2.80/0.40 = 7.00,  2.80/0.30 = 9.33
        #   equivalent parallel R = 2.80 ✓, plus the 0.30 conduit = 3.10 as before.
        Compartment("thigh_vein",          3.20, 9.033, 300, -0.20,  332, p_stiffen=12.0,
                    drain_resistance=0.600),  # 11
        Compartment("calf_vein",           4.80, 6.950, 400, -0.55,  448, p_stiffen=11.0,
                    drain_resistance=0.100),  # 12
        Compartment("foot_vein",           4.00, 9.263, 200, -0.85,  241, p_stiffen= 8.0,
                    drain_resistance=0.140),  # 13
        Compartment("ivc",                12.00, 0.04,  120, -0.15,  195, drain_resistance=CAVOATRIAL_R),  # 14 P0≈5
        # ---- Cardiac chambers (elastance model; R = valve resistance) ----
        # RA Vinit=155: at RA_EMIN=0.04 and P_ra_eq≈3.8 mmHg → V=60+3.8/0.04=155 mL.
        # End-diastolic (rolling-minimum) CVP ≈ 3 mmHg once RA partially empties ✓
        Compartment("right_atrium",        0.35, VALVE_R,  16,  0.0,   47),  # 15
        # RV Vinit=163: at RV_EMIN=0.02, P_rv_dia=0.02×(163-80)=1.7 mmHg → CVP can be 2-3 mmHg.
        # ESV=V0+P_pa/E_max=80+15/1.15=93 mL; SV=163-93=70 mL (improved from 56 mL). ✓
        Compartment("right_ventricle",     0.10, VALVE_R,  38,  0.0,  159),  # 16 EDV≈163 mL
        # ---- Pulmonary (PVR ≈ 0.08 mmHg·s/mL) ----
        # PULMONARY COMPLIANCES RAISED x5.0 ON 2026-09-03 (was 0.40/0.50/0.80,
        # whole bed 1.70 mL/mmHg). See PULMONARY_COMPLIANCE note above.
        # resistance 0.03 -> PULMONIC_R: this field is now read by NOTHING in
        # `_odes` (the pulmonic valve uses params.pulmonic_r and PA->capillary
        # uses pulmonary_cap.resistance). Kept equal to the valve so the two
        # cannot silently diverge again — see test_valve_resistances.
        Compartment("pulmonary_art",       2.00, PULMONIC_R, 100, 0.0, 106),  # 17
        Compartment("pulmonary_cap",       2.50, 0.06,   80,  0.0,   85),  # 18
        Compartment("pulmonary_vein",      4.00, 0.02,  160,  0.0,  168, drain_resistance=VENOATRIAL_R),  # 19
        # ---- Left heart ----
        Compartment("left_atrium",         0.20, VALVE_R,  15,  0.0,   47),  # 20 EDP≈9
        Compartment("left_ventricle",      0.08, VALVE_R,  10,  0.0,  137),  # 21 EDV≈160
        # ---- Coronary ----
        Compartment("coronary",            0.10, 15.0,   20,  0.05,   21),  # 22 flow≈0.3 L/min
    ]


# Compartment index constants for readable cross-references
IDX = {c.name: i for i, c in enumerate(default_compartments())}
