"""
Hydrostatic pressure corrections for posture and gravitational environment.

Core equation (PMC9363491, Heldt 2002):
    ΔP_hydrostatic = ρ · g · h · sin(α)

where
    ρ  = 1060 kg/m³  (blood density)
    g  = gravitational acceleration (m/s²)
    h  = compartment height above heart (m), negative = below heart
    α  = tilt angle from horizontal (degrees)
        0°  = supine (horizontal)
       90°  = upright standing
      -30°  = head-down (Trendelenburg)
"""

import numpy as np

BLOOD_DENSITY = 1060.0   # kg/m³
MMHG_PER_PA   = 1.0 / 133.322  # 1 Pa = 0.0075 mmHg


class GravityEnvironment:
    """Gravitational environment constants."""
    EARTH      = 9.81   # m/s²
    MARS       = 3.721  # m/s²
    MOON       = 1.625  # m/s²
    MICROGRAVITY = 0.0  # m/s²


def hydrostatic_delta_mmhg(
    height_m: float,
    tilt_deg: float,
    g: float = GravityEnvironment.EARTH,
) -> float:
    """
    Hydrostatic pressure contribution of a compartment (mmHg).

    Positive result means the compartment sits above heart level and
    gravity reduces its filling pressure; negative means below-heart
    compartment has extra gravitational filling.

    Parameters
    ----------
    height_m : compartment height above heart centroid (m). Negative = below.
    tilt_deg : body tilt from horizontal (deg). 0 = supine, 90 = standing.
    g        : gravitational acceleration (m/s²)
    """
    alpha_rad = np.radians(tilt_deg)
    delta_pa = BLOOD_DENSITY * g * height_m * np.sin(alpha_rad)
    return delta_pa * MMHG_PER_PA


def smooth_tilt_profile(
    t: float,
    tilt_start: float,
    tilt_end: float,
    t0: float,
    duration: float = 5.0,
) -> float:
    """
    Return instantaneous tilt angle during a sinusoidal tilt transition.
    Matches the smooth 5-second ramp used in PMC9363491.

    Parameters
    ----------
    t          : current time (s)
    tilt_start : initial tilt angle (degrees)
    tilt_end   : target tilt angle (degrees)
    t0         : time when tilt begins (s)
    duration   : transition duration (s), default 5 s
    """
    if t < t0:
        return tilt_start
    if t >= t0 + duration:
        return tilt_end
    phase = (t - t0) / duration   # 0 → 1
    fraction = 0.5 * (1 - np.cos(np.pi * phase))
    return tilt_start + fraction * (tilt_end - tilt_start)
