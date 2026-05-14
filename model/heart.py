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
    edv_ref: float = 120.0,
    slope: float = 0.005,
) -> float:
    """
    Scale E_max with end-diastolic volume (Frank-Starling).
    Linear approximation: E_max increases when EDV > reference.

    Parameters
    ----------
    e_max_baseline : baseline E_max (mmHg/mL)
    edv            : current end-diastolic volume (mL)
    edv_ref        : reference EDV for baseline E_max (mL)
    slope          : sensitivity (mmHg/mL per mL of extra filling)
    """
    return e_max_baseline + slope * (edv - edv_ref)


# ---------------------------------------------------------------------------
# Default cardiac elastance parameters (healthy male, Heldt 2002)
# ---------------------------------------------------------------------------
LV_EMAX = 2.50   # mmHg/mL  left ventricle peak systolic elastance
LV_EMIN = 0.08   # mmHg/mL  left ventricle diastolic elastance
RV_EMAX = 1.15   # mmHg/mL  right ventricle peak systolic elastance
RV_EMIN = 0.05   # mmHg/mL  right ventricle diastolic elastance
RA_EMAX = 0.25   # mmHg/mL  right atrium
RA_EMIN = 0.07   # mmHg/mL
LA_EMAX = 0.35   # mmHg/mL  left atrium
LA_EMIN = 0.09   # mmHg/mL

# Atrial activation is offset by ~60% of the cardiac cycle from ventricular
ATRIAL_PHASE_OFFSET = 0.60  # fraction of T
