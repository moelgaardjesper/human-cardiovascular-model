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
# Phase 1 — venous stress relaxation
#
# Under sustained distension the vein wall creeps: tension falls and volume is
# accommodated at lower pressure.
#
# [S1] Guyton AC et al., via "Venous Return — Control of Cardiac Output",
#      NCBI Bookshelf NBK54476.
#      In anaesthetised, reflex-blocked dogs, rapidly infusing 35% of blood
#      volume drove mean systemic filling pressure to ~24 mmHg, which then
#      decayed asymptotically back toward somewhat above the pre-infusion
#      level, with a HALF-TIME OF 2-4 MINUTES. Attributed to stress relaxation
#      of the large capacitance vessels, with fluid movement into the
#      interstitium contributing gradually.
#
# [S2] Rothe CF (1983). Venous system: physiology of the capacitance vessels.
#      Physiol Rev 63:1281-1342. DOI: 10.1152/physrev.1983.63.4.1281
#      Viscoelastic properties of the capacitance vessels; venous unstressed
#      volume as the variable that accommodates sustained distension.
#
# NOTE ON CALIBRATION: RELAX_FRACTION is deliberately set to take only the fast
# ~third of the observed decay. [S1] explicitly attributes part of it to
# interstitial fluid movement, which is transcapillary filtration (Phase 2) and
# not viscoelastic creep; taking the whole decay here would double-count once
# Phase 2 lands. The COMBINED behaviour is what should be validated against the
# full decay curve.
# ===========================================================================

def test_stress_relaxation_time_constant_matches_guyton():
    """[S1] Creep half-time must sit in the literature's 2-4 min band.

    Unit-level: drives one compartment's transmural pressure above its resting
    reference and integrates the mechanism directly, so this asserts the
    calibration rather than any emergent circulatory behaviour.
    """
    from model.slow_dynamics import (
        _update_stress_relaxation, TAU_STRESS_RELAX, K_RELAX,
    )
    from model.compartments import default_compartments, IDX

    comps = default_compartments()
    state = init_slow_state(comps)
    idx = IDX["splanchnic_vein"]
    c = comps[idx]

    # Establish a resting reference, then step pressure 5 mmHg above it.
    state.p_ref = np.array([cc.pressure(cc.init_volume) for cc in comps], dtype=float)
    P = state.p_ref.copy()
    P[idx] += 5.0

    target = K_RELAX * c.compliance * 5.0
    half_t = None
    for step in range(3600):
        _update_stress_relaxation(state, 1.0, P, comps)
        if half_t is None and state.v0_relax_ml[idx] >= 0.5 * target:
            half_t = step + 1

    assert half_t is not None, "creep never reached half of its steady-state target"
    assert 120 <= half_t <= 240, (
        f"creep half-time {half_t} s is outside the 2-4 min band reported by [S1]"
    )
    assert abs(state.v0_relax_ml[idx] - target) < 0.01 * target, (
        "creep did not converge to its steady-state target within 1 h"
    )
    # Sanity: the half-time should be tau*ln2 for a first-order law.
    assert abs(half_t - TAU_STRESS_RELAX * np.log(2)) < 2.0


def test_stress_relaxation_is_reversible():
    """Creep must relax back when the distension is removed.

    A one-way mechanism would act as a ratchet, permanently inflating venous
    capacity after any transient load — which would silently corrupt every
    subsequent measurement in a long run.
    """
    from model.slow_dynamics import _update_stress_relaxation
    from model.compartments import default_compartments, IDX

    comps = default_compartments()
    state = init_slow_state(comps)
    idx = IDX["splanchnic_vein"]

    state.p_ref = np.array([cc.pressure(cc.init_volume) for cc in comps], dtype=float)
    P = state.p_ref.copy()

    P[idx] += 5.0
    for _ in range(3600):
        _update_stress_relaxation(state, 1.0, P, comps)
    assert state.v0_relax_ml[idx] > 1.0, "creep did not develop"

    P[idx] -= 5.0
    for _ in range(3600):
        _update_stress_relaxation(state, 1.0, P, comps)
    assert abs(state.v0_relax_ml[idx]) < 0.01, (
        f"creep did not reverse: {state.v0_relax_ml[idx]:.4f} mL residual"
    )


def test_stress_relaxation_neutral_at_rest():
    """Enabling slow dynamics must not move resting haemodynamics.

    The mechanism is driven by a deviation from a resting reference captured
    from the model's OWN settled state (see SETTLE_S). Referencing `init_volume`
    instead — which is not the true equilibrium — made the mechanism creep
    permanently and dropped resting MAP by ~1.4 mmHg. This guards that.
    """
    def run(enabled):
        p = SimParams()
        p.slow_dynamics_enabled = enabled
        p.baroreflex_enabled = False
        p.ventilation_mode = "none"
        r = run_simulation(p, duration_s=300.0, dt=DT)
        h = len(r["map"]) // 2
        return {k: float(np.mean(r[k][h:])) for k in ("map", "co", "cvp")}

    off, on = run(False), run(True)
    assert abs(on["map"] - off["map"]) < 0.20, (
        f"resting MAP moved with slow dynamics enabled: "
        f"{off['map']:.3f} -> {on['map']:.3f}"
    )
    assert abs(on["cvp"] - off["cvp"]) < 0.05, (
        f"resting CVP moved: {off['cvp']:.3f} -> {on['cvp']:.3f}"
    )
    assert abs(on["co"] - off["co"]) < 0.05, (
        f"resting CO moved: {off['co']:.3f} -> {on['co']:.3f}"
    )


@pytest.mark.slow
def test_stress_relaxation_decays_cvp_after_volume_load():
    """[S1] After a volume load, CVP must fall at constant blood volume.

    This is the whole point of the mechanism, and it is the behaviour the model
    could not previously produce: without stress relaxation CVP steps up on
    infusion and then sits flat forever, because nothing in the model operates
    on the minutes timescale.

    Baroreflex is disabled so this isolates the viscoelastic effect from reflex
    compensation. The bolus starts after SETTLE_S so the resting reference is
    captured from a genuinely quiescent state.

    ~15 min of simulated time (about 5 min wall) — hence `slow`.
    """
    def run(enabled):
        p = SimParams()
        p.slow_dynamics_enabled = enabled
        p.baroreflex_enabled = False
        p.ventilation_mode = "none"
        p.fluid_bolus_ml = 1000.0
        p.fluid_bolus_start_s = 120.0
        p.fluid_bolus_duration_s = 30.0
        return run_simulation(p, duration_s=900.0, dt=DT)

    def cvp_at(r, t, total=900.0, w=5.0):
        n = len(r["cvp"])
        return float(np.mean(r["cvp"][int(n * (t - w / 2) / total):
                                      int(n * (t + w / 2) / total)]))

    off, on = run(False), run(True)

    base = cvp_at(on, 100)
    peak = cvp_at(on, 160)
    late = cvp_at(on, 880)
    rise = peak - base
    assert rise > 0.5, f"bolus did not raise CVP meaningfully: +{rise:.2f} mmHg"

    # Without the mechanism, CVP must NOT decay — this is the control, and it
    # confirms the decay below is the mechanism rather than some other drift.
    off_peak, off_late = cvp_at(off, 160), cvp_at(off, 880)
    assert abs(off_late - off_peak) < 0.15, (
        f"CVP drifted without stress relaxation ({off_peak:.3f} -> {off_late:.3f}); "
        f"the decay below cannot be attributed to the mechanism"
    )

    # With it, CVP decays toward the calibrated fraction of the rise.
    dissipated = (peak - late) / rise
    assert dissipated > 0.15, (
        f"stress relaxation dissipated only {dissipated * 100:.1f}% of the CVP rise"
    )
    assert dissipated < 0.50, (
        f"stress relaxation dissipated {dissipated * 100:.1f}% — more than the "
        f"calibration allows for. RELAX_FRACTION deliberately takes only the fast "
        f"portion; the rest of the decay observed in [S1] is interstitial fluid "
        f"movement, which is Phase 2 (transcapillary refill), not creep."
    )


# ===========================================================================
# Phase 2-4 validation tests land below, each marked @pytest.mark.slow.
# ===========================================================================
