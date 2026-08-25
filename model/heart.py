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
RV_EMAX = 1.15   # mmHg/mL  right ventricle peak systolic elastance
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
LA_EMIN = 0.28   # mmHg/mL

# Atrial activation is offset by ~60% of the cardiac cycle from ventricular
ATRIAL_PHASE_OFFSET = 0.60  # fraction of T
