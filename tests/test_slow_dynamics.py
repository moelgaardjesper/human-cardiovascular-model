"""
Slow-timescale dynamics validation (minutes to hours).

WHY THIS FILE IS SEPARATE
-------------------------
These tests simulate up to 2 h of physiology. At ~3x real time that is roughly
38 min of wall clock per 2 h scenario, so running them alongside the fast
regression suite would make the ratchet unusable. Everything here is marked
`slow` and is DESELECTED BY DEFAULT (see pytest.ini):

    pytest                  fast suite only (what CI runs)
    pytest -m slow          this file
    pytest -m ""            everything

BACKGROUND
----------
A timescale audit (2026-08-06) established that before this work the model's
slowest mechanism was the sympathetic-slow baroreflex arm at tau = 20 s, and
that the model was effectively stationary within ~40 s of a step perturbation.
Much of the validation literature reports at 1-16 min, so the model was being
compared against measurements that include slow compensation it did not model.
See model/slow_dynamics.py for the mechanisms being added to close that gap.

PHASES
------
0. Infrastructure — slow-state container + clock (this file starts here)
1. Venous stress relaxation
2. Transcapillary refill
3. RAAS / ADH
4. Baroreflex resetting

Each phase lands with its own literature-cited test and a docs/validation_log.md
entry, and must leave the fast suite green WITHOUT loosening any assertion in it.
"""

import numpy as np
import pytest

from model.circulation import SimParams, run_simulation
from model.slow_dynamics import SLOW_DT, SlowState, init_slow_state


DT = 0.001


# ===========================================================================
# Phase 0 — infrastructure
#
# These are fast (~8 s) and are deliberately NOT marked `slow`, so they run as
# part of the default suite and guard the ratchet on every run. They live in
# this file rather than the fast suite only because they concern the
# slow-dynamics machinery.
# ===========================================================================

def test_slow_dynamics_disabled_is_bit_identical():
    """With the flag off the model must be UNCHANGED, bit for bit.

    The fast regression suite is the project's ratchet. Introducing the
    slow-dynamics scaffolding must not perturb it — not by a rounding step,
    not by an extra RNG draw, not at all. This asserts exact equality rather
    than approximate, because any difference at all means the scaffolding is
    not inert and every existing validation number is silently in question.
    """
    a = run_simulation(SimParams(), duration_s=10.0, dt=DT)

    p = SimParams()
    p.slow_dynamics_enabled = False
    b = run_simulation(p, duration_s=10.0, dt=DT)

    for key in ("map", "co", "cvp", "sv", "hr", "aortic_p", "volumes"):
        assert np.array_equal(a[key], b[key]), (
            f"'{key}' differs with slow dynamics explicitly disabled — "
            f"the scaffolding is not inert"
        )


def test_slow_state_container_starts_neutral():
    """A fresh SlowState carries no effect: every mechanism at its null value."""
    comps = SimParams().compartments
    s = init_slow_state(comps)

    assert isinstance(s, SlowState)
    assert s.v0_relax_ml is not None and len(s.v0_relax_ml) == len(comps)
    assert not np.any(s.v0_relax_ml), "stress-relaxation offsets must start at zero"
    assert s.angiotensin == 0.0
    assert s.adh == 0.0
    assert s.map_setpoint_offset == 0.0, (
        "a non-zero initial setpoint offset would silently move the baroreflex "
        "target before Phase 4 is even implemented"
    )


def test_slow_clock_is_coarser_than_fast_step():
    """The slow clock must be far coarser than dt, and far finer than the
    fastest slow mechanism (tau ~ 300 s for venous stress relaxation)."""
    assert SLOW_DT > DT * 10, "slow clock is not meaningfully coarser than the ODE step"
    assert SLOW_DT < 300.0 / 100, "slow clock too coarse to resolve tau ~ 300 s"


def test_odes_pressure_passthrough_matches_recompute():
    """`_odes(..., p_out=...)` must hand back the pressures it actually used.

    The slow mechanisms are driven by compartment pressures. Rather than
    recomputing them on the slow clock (duplicating work and risking a
    divergent second implementation), _odes writes the array it already built.
    This guards that contract.
    """
    from model.circulation import _odes

    params = SimParams()
    comps = params.compartments
    V = np.array([c.init_volume for c in comps], dtype=float)

    p_out = np.zeros(len(comps))
    _odes(0.0, V, params, None, 0.0, p_out)

    assert np.any(p_out), "p_out was never written"
    assert np.all(np.isfinite(p_out)), "p_out contains non-finite pressures"

    # Aortic pressure should match the direct compliance calculation.
    from model.compartments import IDX
    c_ao = comps[IDX["aorta"]]
    expected = (V[IDX["aorta"]] - c_ao.unstressed_volume) / c_ao.compliance
    assert abs(p_out[IDX["aorta"]] - expected) < 1e-9


# ===========================================================================
# Phase 1-4 validation tests land below, each marked @pytest.mark.slow.
# ===========================================================================
