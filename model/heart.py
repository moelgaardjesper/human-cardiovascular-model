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
    """
    T = 60.0 / hr_bpm          # cardiac period (s)
    t_n = (t % T) / T          # normalised phase [0, 1)
    e_n = _normalised_activation(t_n)
    return (e_max - e_min) * e_n + e_min


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
LV_EMAX = 2.50   # mmHg/mL  left ventricle peak systolic elastance
LV_EMIN = 0.08   # mmHg/mL  left ventricle diastolic elastance
RV_EMAX = 1.15   # mmHg/mL  right ventricle peak systolic elastance
# RV_EMIN reduced 0.05→0.02: the RV is highly compliant at diastole (thin wall).
# With RV_EMIN=0.05 and EDV≈180 mL: P_rv_dia=5 mmHg, forcing RA (CVP) to stay ≥5 mmHg.
# With RV_EMIN=0.02 and EDV≈163 mL: P_rv_dia=1.7 mmHg → CVP end-diastolic ≈2 mmHg ✓
# ESV is unchanged (determined by P_pa/RV_EMAX = 15/1.15 ≈ 93 mL), so SV improves.
RV_EMIN = 0.02   # mmHg/mL  right ventricle diastolic elastance (was 0.05)
RA_EMAX = 0.25   # mmHg/mL  right atrium
# RA_EMIN reduced 0.07→0.04: with P_rv_dia≈1.4 mmHg (from RV_EMIN=0.02),
# equilibrium RA pressure ≈ 3.8 mmHg, giving end-diastolic CVP ≈ 3 mmHg.
# Analytical: at equilibrium 2×(P_svc−P_ra)/R = (P_ra−P_rv)/R → P_ra≈3.8 mmHg ✓
RA_EMIN = 0.04   # mmHg/mL  right atrium diastolic elastance (was 0.07)
LA_EMAX = 0.35   # mmHg/mL  left atrium
LA_EMIN = 0.09   # mmHg/mL

# Atrial activation is offset by ~60% of the cardiac cycle from ventricular
ATRIAL_PHASE_OFFSET = 0.60  # fraction of T
