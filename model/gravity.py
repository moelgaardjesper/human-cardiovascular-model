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

import math

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


# POSITIONAL INTRATHORACIC PRESSURE IN HEAD-DOWN TILT — SET TO ZERO 2026-10-04.
#
# Until then k = 8.5 added +2.2 mmHg of pleural pressure at -15 deg. That value
# was FITTED, not measured: it was chosen to put the reported Trendelenburg CVP
# rise inside Likhvantsev 2025's CI, at a time when a hydrostatic conservation
# error (backlog item 65) was pushing blood toward the heart in head-down tilt.
# The two errors cancelled. When item 65 was fixed, this term alone held back
# venous return and head-down cardiac output went negative.
#
# THE MEASUREMENT. Drummond & Martin 1978 (PMID 147698, Br J Anaesth 50:261),
# 9 anaesthetised, paralysed women, oesophageal balloon, static end-expiratory
# pressure at FRC, supine -> 15 deg head-down WITHOUT pneumoperitoneum: change
# -22 Pa, 95 % CI -75 to +30 Pa = **-0.17 mmHg (-0.56 to +0.23)**. Their own
# words: changing position "did not cause a significant change". GRADE A for the
# quantity, one small cohort.
#
# WHAT THIS COSTS. The reported CVP rise at -15 deg falls to about +0.5 mmHg
# against Likhvantsev's pooled +4.1. That is carried as a strict xfail until the
# meta-analysis's included studies are read: some may have had pneumoperitoneum,
# which DOES raise abdominal pressure (Drummond: gastric 3.4 -> 6.4 mmHg), and
# transducer levelling during tilt is unreported.
#
# The function is kept so that callers and the reporting path are unchanged and a
# sourced value can replace this one. Pneumoperitoneum is a DIFFERENT mechanism
# (intra-abdominal pressure) and must not be smuggled in through this constant.
POSITIONAL_ITP_K_MMHG = 0.0


# ---------------------------------------------------------------------------
# ARTICULATED LEGS — backlog item 53, leg rebuild stage 3 (2026-10-05)
# ---------------------------------------------------------------------------
# Until now ONE angle tilted the whole body, so a passive leg raise could only be
# modelled as whole-body head-down tilt — a different manoeuvre (Sejersen 2022,
# PMID 35854636: in the same men, 20 deg HDT left SV unchanged while a leg raise
# from semi-recumbent raised it 9 mL).
#
# GEOMETRY. Each compartment's `height_m` is its position along the body axis
# from the heart (negative = footward). The trunk rotates by `trunk_deg` (the
# existing tilt). The legs pivot at the hip, flexed by `hip_flexion_deg`
# relative to the trunk (positive = legs raised off a flat table). A leg point
# at axial position h, with the hip at h_hip, sits vertically at
#     h_hip * sin(trunk) + (h - h_hip) * sin(trunk - flexion)
# With zero flexion this is h * sin(trunk), the old formula — and the code
# takes the old path exactly in that case, so every existing tilt result is
# bit-for-bit unchanged.
#   semi-recumbent (trunk 45, flexion 45)  -> legs horizontal at hip height
#   leg raise from it (trunk 0, flexion 45) -> legs 45 deg up from a flat trunk
def articulated_hydrostatic_delta_mmhg(
    height_m: float,
    trunk_deg: float,
    hip_flexion_deg: float,
    hip_height_m: float,
    g: float = GravityEnvironment.EARTH,
) -> float:
    """Hydrostatic delta (mmHg) for a LEG compartment, legs pivoting at the hip.

    Identical to `hydrostatic_delta_mmhg(height_m, trunk_deg, g)` when
    `hip_flexion_deg` is zero (that branch is taken explicitly)."""
    if hip_flexion_deg == 0.0:
        return hydrostatic_delta_mmhg(height_m, trunk_deg, g)
    vertical = (hip_height_m * np.sin(np.radians(trunk_deg))
                + (height_m - hip_height_m) * np.sin(np.radians(trunk_deg - hip_flexion_deg)))
    return BLOOD_DENSITY * g * vertical * MMHG_PER_PA


def positional_itp_mmhg(tilt_deg: float, k_mmhg: float = POSITIONAL_ITP_K_MMHG) -> float:
    """
    ITP rise (mmHg) from body positioning — the DC (non-oscillatory) component.

    Zero by default since 2026-10-04: a human measurement found no pleural
    pressure change on 15 deg head-down tilt. See POSITIONAL_ITP_K_MMHG.

    Parameters
    ----------
    tilt_deg : current tilt angle (degrees from horizontal; negative = HDT)
    k_mmhg   : slope constant (mmHg per unit sin(tilt))
    """
    if tilt_deg >= 0.0:
        return 0.0
    return k_mmhg * math.sin(math.radians(-tilt_deg))


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
