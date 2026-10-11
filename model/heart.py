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


# ---------------------------------------------------------------------------
# VENTRICULAR ACTIVATION — MEASURED HUMAN SHAPE AND TIMING (2026-10-10)
# ---------------------------------------------------------------------------
# `_normalised_activation` above is UNSOURCED and lays systole out as FRACTIONS
# OF THE BEAT (rise to 0.30, relaxed by 0.45). Two defects in one: at rest the LV
# ejected for 193 ms where man ejects ~294 (Weissler); and systole shrank in
# proportion to the beat at high rates (106 ms at 110 bpm) — the error class of
# the old fixed-fraction PR offset. It is kept only as the "legacy" option.
#
# SHAPE — Senzaki, Chen, Kass 1996 (PMID 8921794; conductance catheter, 72 loops,
# 52 patients): normalised elastance E_N(t_N), t_N = t / t_max, "remarkably
# consistent despite variations in ... heart rate" (atrial pacing 76-130 bpm
# virtually identical). Their Table 4 12-term Fourier fit is used verbatim.
# GRADE A for the shape. The model has a SEPARATE passive curve (Klotz), so only
# the ACTIVE part is used: e = (E_N - E_N(0)) / (1 - E_N(0)), floored at 0.
# Subtracting E_N(0) (not the diastolic plateau) removes a step at beat start
# that otherwise produced a 4,800 mmHg/s dP/dt spike (prototype, 2026-10-10).
#
# TIMING — t_max (R wave -> peak elastance) = total electromechanical systole
# QS2 (Weissler 1968, PMID 5640345; 121 men, 90 women): QS2 = -0.0021 HR + 0.546 s
# (men). Two labs, two methods agree: Weissler's PEP/QS2 at 70 bpm = 103/399 =
# 0.258; Senzaki's aortic opening at t_N 0.258 ± 0.035. GRADE B.
# The model's beat starts at MECHANICAL onset, so the electromechanical delay is
# subtracted: QRS onset -> LV pressure rise 21 ± 5 ms (Manolas 1975, Br Heart J
# 37:1263; tip manometers, n 10, normal LV). GRADE A-minus. The atrial PR offset is
# left relative to ventricular mechanical onset, i.e. atrial EMD ASSUMED equal.
# The same curve and timing drive the RV — an ASSUMPTION (grade D): Senzaki
# measured left ventricles; RV ejection is known to outlast LV ejection.
# Validated (prototype, 2026-10-10): peak dP/dt 1,703 vs Manolas 1,700 ± 370;
# (dP/dt)/DP 28 vs Mason 1971 ~30; LVET 312 ms at 70 bpm (Weissler 294, +1.8 SD),
# 219 at 110 (226); LV Ees by Chen 1998's method 2.8 vs 2.3 ± 1.0.
_SZ_A = np.array([28.38975, 37.58583, 21.02345, 7.665592, 4.809436, 4.181973, 1.940692,
                  0.5870049, 1.181256, 0.84039, 0.02259011, 0.3071458, 0.3226207]) / 100.0
_SZ_PHI = np.array([0.0, 0.08367674, -1.486758, 2.865675, 0.1677238, 4.630239, 3.088379,
                    -0.3053668, 4.410703, 3.181538, 1.242886, 4.156753, 2.946186])
_SZ_N = np.arange(13)
_SZ_PERIOD_TN = 3.46            # one Fourier period (2 pi) in t_N, Senzaki Table 4
_SZ_EN0 = float(_SZ_A[0] + np.sum(_SZ_A[1:] * np.sin(_SZ_PHI[1:])))   # E_N(0) = 0.0789
_SZ_TN_END = 1.75               # active part < 0.01 beyond this (relaxed)

QS2_INTERCEPT_S = 0.546         # Weissler 1968, men
QS2_SLOPE_S_PER_BPM = 0.0021    # Weissler 1968, men
ELECTROMECHANICAL_DELAY_S = 0.021   # Manolas 1975
# t_max SCALE — GRADE E, PINNED 2026-10-10. Senzaki's t_max is timed to peak
# elastance; mapping it onto Weissler's QS2 (which ends at A2, aortic CLOSURE)
# was an inference (the 0.258 agreement). In THIS model the aortic valve closes
# only when LV pressure falls below root pressure — there is no blood inertia to
# decelerate and reverse flow — so ejection overruns peak elastance, and with the
# characteristic impedance LVET came out 332 ms against Weissler's measured 294
# (+3.8 SD). LVET is the MEASURED quantity (grade A), so t_max is pinned jointly
# with AORTIC_ZC from two endpoints: LVET at rest (Weissler) and invasive-
# equivalent central PP (McEniery + Cheng). Out-of-sample check that agreed:
# peak aortic flow / SV 5.4 vs ~5-6 (Carlsson 2004 Fig 3). Sweep in
# validation_log 2026-10-10.
VENTRICULAR_T_MAX_SCALE = 0.875


def senzaki_active(t_n: float) -> float:
    """Active part (0..1) of Senzaki 1996's normalised human LV elastance at
    t_N = t / t_max (time from mechanical onset over time to peak)."""
    if t_n < 0.0 or t_n >= _SZ_TN_END:
        return 0.0
    x = 2.0 * np.pi * t_n / _SZ_PERIOD_TN
    en = _SZ_A[0] + float(np.sum(_SZ_A[1:] * np.sin(_SZ_N[1:] * x + _SZ_PHI[1:])))
    return max(0.0, (en - _SZ_EN0) / (1.0 - _SZ_EN0))


def ventricular_t_max(hr_bpm: float, scale: float = 1.0) -> float:
    """Mechanical time to peak elastance (s): Weissler's QS2 minus Manolas'
    electromechanical delay, times `scale`, bounded so relaxation completes
    within the beat."""
    rr = 60.0 / max(hr_bpm, 1e-6)
    t_max = scale * (QS2_INTERCEPT_S - QS2_SLOPE_S_PER_BPM * hr_bpm - ELECTROMECHANICAL_DELAY_S)
    return min(t_max, 0.95 * rr / _SZ_TN_END)


def ventricular_activation(cardiac_phase: float, hr_bpm: float, legacy: bool = False,
                           t_max_scale: float = 1.0) -> float:
    """Ventricular activation e(t) in 0..1 for the current beat phase."""
    t_n = cardiac_phase % 1.0
    if legacy:
        return _normalised_activation(t_n)
    return senzaki_active((t_n * 60.0 / max(hr_bpm, 1e-6)) / ventricular_t_max(hr_bpm, t_max_scale))


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
# VENTRICULAR DIASTOLE — THE KLOTZ CURVE (2026-10-06)
# ---------------------------------------------------------------------------
# Until 2026-10-06 both ventricles filled along a STRAIGHT line, P = E_min·(V - V0)
# (LV E_min 0.055, RV 0.04 mmHg/mL), equally stiff at every volume. A straight
# line cannot make a Starling plateau: every extra mmHg of filling pressure buys
# the same extra volume, and the elastance heart ejects it. Sejersen 2022
# (PMID 35854636) measured the plateau in healthy men — 20 deg head-down left SV
# unchanged — and the model gained 22-29 mL (validation log 2026-10-05).
#
# THE SOURCE. Klotz et al. 2006 (PMID 16428349): end-diastolic P-V relations of
# 80 human hearts (normal, ischaemic, dilated, post-LVAD) collapse onto ONE curve
# once volume is normalised, EDP = An·EDVn^Bn, EDVn = (V - V0)/(V30 - V0), with
# V0 the volume at ~0 mmHg and V30 at 30 mmHg. Validated in 36 living patients
# (RMSE ~3 mmHg). GRADE A for the SHAPE. An = 28.2, Bn = 2.79 are the values
# their single-beat placement equations (Eq 5, Eq 8) were derived with; the
# all-80 fit is 27.8 +/- 0.3 and 2.76 +/- 0.05.
#
# PLACEMENT, from ONE sourced end-diastolic point per ventricle (Klotz Eq 8, 5):
#     V0  = EDV·(0.6 - 0.006·EDP)          V30 = V0 + (EDV - V0)/(EDP/An)^(1/Bn)
# Klotz's hearts were outside the body, so EDP here is TRANSMURAL. The catheter
# sources are intraluminal at end-expiration; the model's spontaneous-breathing
# pleural pressure at end-expiration is -1.47 mmHg, added back.
#   LV  EDV Luu male 74 mL/m2 x BSA 1.909 (175 cm / 75 kg) = 141.3 mL
#       EDP Chemla 2004 PAOP 11 mmHg (wedge as the LVEDP surrogate, GRADE C)
#           + 1.47 = 12.47 transmural
#   RV  EDV Luu male 86 mL/m2 x 1.909 = 164.2 mL
#       EDP Richter 2021 RVEDP 4 [3-5] mmHg + 1.47 = 5.47 transmural
# LEFT VENTRICLE ONLY. The RV was tried on the same curve (Jesper's assumption,
# 2026-10-06) and it FAILED: below its V0 (~95 mL) the curve gives no wall
# pressure, the RV ejects down to ~77 mL, so early in every diastole the right
# atrium drained into an unresisting chamber and RA pressure fell to 0.9 mmHg
# (Richter 2-6). Five tests broke on it and recovered when the RV went back to
# its straight line (venoconstriction, a 500 mL bleed, sympathetic block, RA
# pressure, tilt tachycardia; validation log 2026-10-06). Klotz measured left
# ventricles; the shape does not transfer to the thin-walled RV. A human RV
# EDPVR source is WANTED.
#
# NOT MODELLED: the pericardium (Klotz's hearts had none; it limits filling of
# both ventricles together at high volumes) — the leading candidate for the
# head-down over-response that remains.
#
# A SEPARATE DIASTOLIC REFERENCE VOLUME. Klotz's V0 is ~55 % of EDV (~74 mL);
# the chamber's `unstressed_volume` (LV 10 mL) is the SYSTOLIC (ESPVR) intercept
# and stays the reference for contraction. Ventricular pressure is
#     P = e(t)·Emax·(V - V0_systolic) + (1 - e(t))·P_klotz(V)
# with e(t) the same activation curve as before.
KLOTZ_AN = 28.2
KLOTZ_BN = 2.79
_BSA_REF = (175.0 * 75.0 / 3600.0) ** 0.5           # Mosteller, REF patient
_PLEURAL_END_EXPIRATION = -1.47                       # mmHg, model, spontaneous


def klotz_placement(edv: float, edp: float) -> tuple[float, float]:
    """(V0, V30) of the Klotz EDPVR through one end-diastolic point (Eq 8, 5).
    `edp` must be transmural."""
    v0 = edv * (0.6 - 0.006 * edp)
    v30 = v0 + (edv - v0) / (edp / KLOTZ_AN) ** (1.0 / KLOTZ_BN)
    return v0, v30


def klotz_diastolic_pressure(vol: float, v0: float, v30: float) -> float:
    """Passive (transmural) ventricular pressure on the Klotz curve."""
    x = (vol - v0) / (v30 - v0)
    return KLOTZ_AN * x ** KLOTZ_BN if x > 0.0 else 0.0


LV_V0_DIA, LV_V30 = klotz_placement(74.0 * _BSA_REF, 11.0 - _PLEURAL_END_EXPIRATION)


# ---------------------------------------------------------------------------
# THE PERICARDIUM (2026-10-08) — a shared external pressure, not a compartment
# ---------------------------------------------------------------------------
# The heart sits in a sac. The sac holds no blood, so it is not a compartment:
# it is a PRESSURE, set by how full the whole heart is, pressing on all four
# chambers at once — the same kind of term as intrathoracic pressure, one layer
# further in. Chamber pressure as a catheter reads it is then
#     P_cavity = P_wall(V_chamber) + P_peri(V_heart) [+ ITP]
# with V_heart = RA + RV + LA + LV.
#
# THE EVIDENCE (ledger, all read in full):
#   - Pericardial pressure ~ right atrial pressure in man: slope 1.16 +/- 0.20,
#     intercept 0.71 +/- 2.48 (Tyberg 1986, PMID 3948353, n 9, open chest).
#   - Human RA wall (transmural) pressure 1.0 +/- 1.5 over CVP 3-16; the
#     pericardium carries 89 % of RA and 77 % of RV cavity pressure at CVP 10
#     (Hamilton 1994, PMID 7955207).
#   - Healthy 55-year-olds: PCWP 11.4, RAP 8.0, LV wall pressure only 3.4 —
#     70 % of the wedge reading is external (Fujimoto 2011, PMID 21398598).
#   - Opening the sac cuts the PCWP rise on volume loading by 67 % in man
#     (Borlaug 2018 via Borlaug & Reddy 2019, PMID 31248569).
#   - Mechanics: little pressure at small heart volume, steep once the heart
#     fills the sac (Borlaug & Reddy; Kroeker 2003, dog).
#
# THE SAC IS ITS OWN STRUCTURE (rebuilt 2026-10-09, Jesper: "we need both if we
# want to model cardiac tamponade"). It has an anatomical CAPACITY, it holds the
# heart AND any excess fluid, and it presses only once its contents exceed that
# capacity:
#     contents = RA + RV + LA + LV + pericardial_fluid_ml
#     P_peri   = 0                                       contents <= capacity
#              = k * (exp((contents - capacity) / vk) - 1)  above it
# Slack below the knee, an "elastic band" above it (Kroeker 2003, dog; Holt 1967
# review: "accommodates large volume increases with little or no increase in
# pressure; after a certain large volume is reached, small increases produce
# large increases"). P_peri is relative to PLEURAL pressure; ITP is added on top
# as for every thoracic structure, so a drained sac can read below atmospheric
# (Reddy 1978, PMID 668074; Boltwood 1987, PMID 3568311).
#
# pericardial_fluid_ml is EXCESS fluid. The normal film is part of the capacity,
# which keeps an unsourced "normal fluid volume" out of the model. Tamponade is
# fluid > 0; pericardiocentesis is lowering it.
#
# THE THREE NUMBERS AND THEIR GRADES (ledger 2026-10-09, all read in full):
#   capacity  GRADE C — at the resting heart volume. Dog: 10 mL into a normal sac
#             raised pressure ~1.8 mmHg, so the heart fills it to within ~10 mL
#             (Banchero via Holt 1967, PMID 4866091). Human: ~200 mL of acute
#             effusion can cause hypotensive tamponade (Beck 1935 via Boltwood);
#             ~70 % of resting wedge is external (Fujimoto 2011). CONTRADICTED by
#             Applegate 1992 (dog, no constraint at rest) — recorded, unresolved.
#             The default is the reference heart's measured mean four-chamber
#             volume, 305 mL; it scales with heart size in apply_cardiac.
#   k, vk     GRADE D/E — slope at the knee k/vk = 0.18 mmHg/mL from the same dog
#             experiment. Human drainage slopes (0.03-0.2 mmHg/mL, Reddy, Boltwood)
#             are from CHRONICALLY STRETCHED sacs and are not a normal sac's
#             stiffness. vk is unmeasured. Both to be PINNED from a human endpoint
#             (Borlaug 2018's 67 %, or Bhella 2014's RA rise on saline) and tested
#             on the others.
# A stretched (subacute) sac is a larger capacity with the same stiffness
# (Freeman & LeWinter 1984, dog) — model it by raising capacity, not softening k.
#
# KNOWN BLOCKER FOR SWITCHING IT ON: the model's four-chamber volume swings
# ~158 mL per beat against ~64 mL in man (Carlsson 2004, PMID 15016625), because
# the atria do not fill during ventricular ejection (no AV-plane coupling). A
# sac converts that swing into a large pressure oscillation every beat.
#
# WHAT EACH CONSUMER GETS. The ODE uses cavity pressure — venous return into the
# RA is opposed by the sac as well as the wall. The baroreflex keeps the WALL
# pressure: cardiopulmonary receptors sense stretch, which is transmural.
# Reported CVP / LA / chamber traces are cavity pressures, as a catheter reads.
# Off by default (SimParams.pericardium_enabled) until measured.
#
# KNOWN DOUBLE-COUNT IF SWITCHED ON AS-IS: the LV Klotz curve above was placed
# at Chemla's wedge (11 mmHg) treated as a wall pressure. A wedge is a CAVITY
# pressure, so part of it is already pericardial. Adding the sac on top counts
# that part twice on the left. The walls must be re-placed at WALL pressures
# (Hamilton 1994, Bhella 2014) before the sac goes on (validation log 2026-10-08).
PERI_CAPACITY = 305.0  # mL — GRADE C: knee at the reference heart's mean four-chamber volume
PERI_VK = 30.0         # mL — GRADE E, to be pinned
PERI_K = 0.18 * PERI_VK  # mmHg — GRADE D: slope at the knee 0.18 mmHg/mL (dog, Banchero via Holt)
# NUMERICAL GUARD, NOT PHYSIOLOGY. Above this sac pressure the curve continues as
# a straight line at its own slope there (continuous value and slope). Without
# it, an effusion the heart cannot make room for (300 mL into a 305 mL sac)
# drives the exponential to ~1e5 mmHg and the 1 ms explicit integrator
# overflows (measured 2026-10-09). 60 mmHg is ~3x the highest sac pressures in
# human tamponade (Reddy 1978: 14-20; Boltwood 1987: 10-18), so no
# physiological case reaches it.
PERI_P_LINEAR = 60.0     # mmHg


def pericardial_pressure(contents: float, capacity: float, k: float, vk: float) -> float:
    """Pressure of the pericardial sac on all four chambers, relative to pleural
    pressure (mmHg). Zero while the contents fit; exponential above capacity."""
    if contents <= capacity:
        return 0.0
    x = (contents - capacity) / vk
    x_lin = np.log(PERI_P_LINEAR / k + 1.0)
    if x <= x_lin:
        return k * (np.exp(x) - 1.0)
    return PERI_P_LINEAR + (PERI_P_LINEAR + k) * (x - x_lin)


# ---------------------------------------------------------------------------
# Default cardiac elastance parameters (healthy male, Heldt 2002)
# ---------------------------------------------------------------------------
LV_EMAX = 3.00   # mmHg/mL  left ventricle peak systolic elastance
# LV_EMIN (0.055) — the straight-line LV diastolic stiffness — was REMOVED on
# 2026-10-06, replaced by the Klotz curve above. Removed rather than left
# unused, so nothing can keep reading a stiffness the ODE ignores.
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
# The RV is highly compliant in diastole (thin wall). STILL A STRAIGHT LINE: the
# Klotz curve was tried here on 2026-10-06 and failed (see VENTRICULAR DIASTOLE).
# 0.04 sits between the values implied by Richter's RVEDP 4 and Hoff's RAP with
# Petersen's CMR RVEDV (0.031-0.053; reference_values.md) — a BOUND, GRADE C.
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
# WHAT 0.19 DOES NOT FIX. The residual is a VOLUME DISTRIBUTION problem, not an
# atrial one: LA peak pressure is IMPOSED BY THE CIRCULATION. Raising the
# atrium's unstressed volume from 15 to 45 mL left peak pressure completely
# unchanged, which is the direct evidence for that — the atrium finds a
# different VOLUME at the pressure the loop dictates.
#
# THE DIAGNOSIS THAT USED TO BE HERE HAS BEEN OVERTAKEN, 2026-09-10. It read:
# "the pulmonary vessels hold 365.8 mL where the literature has 450-500, so the
# vessels are under-filled while the atrium is over-filled." Both halves have
# since flipped. The pulmonary bed now holds 505 mL against Ugander's
# 526 +/- 87 — corrected by the compliance work of 2026-09-03 and 2026-09-10 —
# and the LEFT ATRIUM IS NOW UNDER-FILLED, at a volume index of 34.1 against
# Gao's 37-48, with a peak pressure of 9.64 against Chemla's PAOP of 11 +/- 2.
#
# THAT RULES SOMETHING OUT. Fixing the pulmonary bed did NOT bring the atrium
# up with it, so "the lungs are holding the atrium's volume" is not the
# explanation. The missing ~10 mL is somewhere else.
# AND IT RULES OUT A TEMPTING FIX: making the atrial law exponential or
# collapsible-tube would change the VOLUME at which the imposed pressure is
# reached, not the pressure — and since the volume is already low, a stiffening
# law moves it further from target. See validation_log.md, 2026-09-10.
# See backlog 25a.
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
