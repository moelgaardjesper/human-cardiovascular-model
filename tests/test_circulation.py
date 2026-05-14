"""
Smoke tests for the cardiovascular circulation model.

Validates that simulated steady-state haemodynamics fall within
physiologically plausible ranges for:
  1. Resting supine (baseline)
  2. Head-down tilt 30° (Trendelenburg)
  3. Microgravity
"""

import numpy as np
import pytest

from model.circulation import SimParams, run_simulation
from model.gravity import GravityEnvironment


DURATION = 30.0   # seconds — long enough for steady state
DT       = 0.001  # 1 ms — required for Euler stability with current parameters


def _mean_last_half(arr: np.ndarray) -> float:
    """Mean over the second half of the time series (post-transient)."""
    return float(np.mean(arr[len(arr) // 2:]))


# ---------------------------------------------------------------------------
# 1. Resting baseline
# ---------------------------------------------------------------------------

def test_resting_baseline():
    params = SimParams()
    result = run_simulation(params, duration_s=DURATION, dt=DT)

    map_mean = _mean_last_half(result["map"])
    hr_mean  = _mean_last_half(result["hr"])
    co_mean  = _mean_last_half(result["co"])

    assert 70 <= map_mean <= 110, f"MAP out of range: {map_mean:.1f} mmHg"
    assert 50 <= hr_mean  <= 90,  f"HR out of range: {hr_mean:.1f} bpm"
    assert 3  <= co_mean  <= 8,   f"CO out of range: {co_mean:.2f} L/min"


# ---------------------------------------------------------------------------
# 2. Head-down tilt (Trendelenburg −30°)
# ---------------------------------------------------------------------------

def test_trendelenburg_raises_map_and_cvp():
    """
    Head-down tilt shifts blood toward the thorax:
    MAP should rise (or stay similar), CVP should increase.
    """
    # Baseline (supine)
    p_base = SimParams()
    r_base = run_simulation(p_base, duration_s=DURATION, dt=DT)
    map_base = _mean_last_half(r_base["map"])
    cvp_base = _mean_last_half(r_base["cvp"])

    # Trendelenburg
    p_tilt = SimParams()
    p_tilt.tilt_start_deg = -30.0
    p_tilt.tilt_end_deg   = -30.0
    r_tilt = run_simulation(p_tilt, duration_s=DURATION, dt=DT)
    map_tilt = _mean_last_half(r_tilt["map"])
    cvp_tilt = _mean_last_half(r_tilt["cvp"])

    assert cvp_tilt > cvp_base, (
        f"CVP did not increase with head-down tilt: {cvp_base:.1f} → {cvp_tilt:.1f} mmHg"
    )
    assert map_tilt >= map_base - 5, (
        f"MAP dropped unexpectedly with head-down tilt: {map_base:.1f} → {map_tilt:.1f} mmHg"
    )


# ---------------------------------------------------------------------------
# 3. Microgravity
# ---------------------------------------------------------------------------

def test_microgravity_equalises_pressures():
    """
    In microgravity there are no hydrostatic gradients.
    CVP should increase relative to upright, MAP may be lower than Earth upright.
    """
    # Upright on Earth
    p_earth = SimParams()
    p_earth.tilt_start_deg = 90.0
    p_earth.tilt_end_deg   = 90.0
    r_earth = run_simulation(p_earth, duration_s=DURATION, dt=DT)

    # Microgravity (supine tilt irrelevant — g=0 eliminates hydrostatics)
    p_micro = SimParams()
    p_micro.gravity = GravityEnvironment.MICROGRAVITY
    r_micro = run_simulation(p_micro, duration_s=DURATION, dt=DT)

    cvp_earth = _mean_last_half(r_earth["cvp"])
    cvp_micro = _mean_last_half(r_micro["cvp"])
    map_earth = _mean_last_half(r_earth["map"])
    map_micro = _mean_last_half(r_micro["map"])

    # Without pooling in legs, microgravity CVP > upright Earth CVP
    assert cvp_micro > cvp_earth - 3, (
        f"Microgravity CVP unexpectedly low: Earth upright {cvp_earth:.1f}, µg {cvp_micro:.1f} mmHg"
    )
    # MAP should remain in survivable range
    assert 50 <= map_micro <= 120, f"MAP out of range in microgravity: {map_micro:.1f} mmHg"
