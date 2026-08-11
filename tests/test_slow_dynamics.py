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

    # Both mechanisms active here deliberately: neutrality must hold for the
    # module as a whole, not just one mechanism at a time.
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
        # ISOLATE stress relaxation. With filtration also active the decay is
        # ~81% rather than ~27%, and this test would silently be measuring the
        # sum of both mechanisms rather than the one it is named after. The
        # combined behaviour has its own test below.
        p.slow_fluid_exchange_enabled = False
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
# Phase 2 — transcapillary refill
#
# [S3] Drucker WR, Chadwick CD, Gann DS (1981). Transcapillary refill in
#      hemorrhage and shock. Arch Surg 116(10):1344-53.
#      DOI: 10.1001/archsurg.1981.01380220088014   PMID: 7283706
#      Refill is "mediated entirely by changes in the Starling forces,
#      dominated in the first phase by a fall in capillary hydrostatic
#      pressure, which promotes a rapid shift of protein-free fluid from the
#      interstitium into the capillaries. The second phase, temporally
#      overlapping the initial phase, involves the return of protein to support
#      plasma oncotic pressure."
#
# [S4] Lister J, McNeill IF, Marshall VC, Plzak LF, Dagher FJ, Moore FD (1963).
#      Transcapillary refilling after hemorrhage in normal man: basal rates and
#      volumes; effect of norepinephrine. Ann Surg 158(4):698-712.
#      DOI: 10.1097/00000658-196310000-00016   PMID: 14067514
#      HUMAN. 16 healthy men, 490-968 mL bled over 15-20 min (10-20% of blood
#      volume), essentially non-hypotensive. Cr-51 red cell volume + T-1824
#      plasma volume, followed 72 h.
#        refill 0-24 h : 18.8-36.7 mL/h, mean 27.9
#        refill 24-48 h: 3.8-15.0 mL/h,  mean 11.1
#        replaced      : 50-80% at 24 h; complete only at 36-48 h
#        early phase   : ~100 mL/h in the first 1-2 h (Figs 3, 7)
#        NE, no bleed  : plasma volume -15% and -19%, reversible (Fig 5)
#        NE after bleed: plasma volume -220 to -480 mL (-9 to -14%)
#      NOTE: the paper contains no filtration coefficient. Do not cite it for Kf.
#
# Retrieved via PubMed; full text obtained and read 2026-08-10.
# ===========================================================================

@pytest.mark.slow
def test_transcapillary_refill_after_haemorrhage():
    """[S3][S4] Blood volume must partially self-restore after haemorrhage.

    Without this mechanism the model leaves a bled patient in fixed profound
    shock indefinitely — blood volume is flat forever and MAP never recovers,
    which is not what happens to a real patient.

    The relaxation-OFF run is carried as an explicit control: blood volume must
    be *exactly* flat there, so the recovery below cannot be attributed to
    anything but transcapillary absorption.

    ~20 min simulated per arm (about 13 min wall) — hence `slow`.
    """
    D = 1200.0

    def run(enabled):
        p = SimParams()
        p.slow_dynamics_enabled = enabled
        p.baroreflex_enabled = True
        p.ventilation_mode = "none"
        p.hemorrhage_rate_mlmin = 1000.0        # 1000 mL over 60 s
        p.hemorrhage_start_s = 120.0            # after SETTLE_S
        p.hemorrhage_duration_s = 60.0
        return run_simulation(p, duration_s=D, dt=DT)

    def bv(r, t, w=10.0):
        n = len(r["volumes"])
        seg = r["volumes"][int(n * (t - w / 2) / D):int(n * (t + w / 2) / D)]
        return float(seg.sum(axis=1).mean())

    def mean_at(r, key, t, w=10.0):
        n = len(r[key])
        return float(np.mean(r[key][int(n * (t - w / 2) / D):
                                    int(n * (t + w / 2) / D)]))

    off, on = run(False), run(True)

    # Control: no mechanism, no volume recovery. Guards the attribution.
    assert abs(bv(off, 1180) - bv(off, 200)) < 1.0, (
        "blood volume changed without slow dynamics; the recovery below cannot "
        "be attributed to transcapillary refill"
    )

    deficit = bv(on, 110) - bv(on, 200)
    assert deficit > 800.0, f"haemorrhage did not remove the expected volume: {deficit:.0f} mL"

    recovered = bv(on, 1180) - bv(on, 200)
    frac = recovered / deficit
    assert frac > 0.10, (
        f"transcapillary refill recovered only {frac * 100:.1f}% of the deficit "
        f"in 18 min; [S3] has the majority of refill inside 30-60 min"
    )
    # Upper bound guards the oncotic brake. Absorbed fluid is nearly
    # protein-free, so it dilutes plasma protein, pi_p falls and absorption
    # self-limits. Without a working brake this runs away and over-fills.
    assert frac < 0.70, (
        f"refill recovered {frac * 100:.1f}% of the deficit — the oncotic brake "
        f"is not limiting absorption"
    )

    # The clinically meaningful consequence: pressure recovers.
    map_off = mean_at(off, "map", 1180)
    map_on = mean_at(on, "map", 1180)
    assert map_on > map_off + 10.0, (
        f"MAP did not recover with refill: {map_off:.1f} -> {map_on:.1f} mmHg"
    )


# ===========================================================================
# Phases 1 + 2 combined
# ===========================================================================

@pytest.mark.slow
def test_combined_slow_dynamics_reproduce_guyton_decay():
    """[S1] Creep AND filtration together must reproduce the full decay curve.

    This is the test the two-phase split was designed around, and the one that
    justifies Phase 1 being calibrated to only part of the observed decay.

    [S1]: a 35% blood-volume infusion drove mean systemic filling pressure to
    ~24 mmHg, which then "began immediately to decline asymptotically toward a
    steady-state value somewhat above the initial level". With a pre-infusion
    MSFP of ~7 mmHg, settling to ~10 mmHg is about 82% of the rise dissipated.
    The source attributes the decay to stress relaxation of the capacitance
    vessels WITH fluid movement into the interstitium contributing gradually —
    i.e. to exactly these two mechanisms together.

    Neither mechanism reproduces this alone: stress relaxation on its own
    dissipates ~27% (see the isolated test above), and that is deliberate.
    Tuning Phase 1 to hit the full curve by itself would have double-counted
    filtration and left Phase 2 nothing to contribute.
    """
    D = 900.0

    def run(**flags):
        p = SimParams()
        p.baroreflex_enabled = False
        p.ventilation_mode = "none"
        p.fluid_bolus_ml = 1000.0
        p.fluid_bolus_start_s = 120.0
        p.fluid_bolus_duration_s = 30.0
        for k, v in flags.items():
            setattr(p, k, v)
        return run_simulation(p, duration_s=D, dt=DT)

    def cvp_at(r, t, w=5.0):
        n = len(r["cvp"])
        return float(np.mean(r["cvp"][int(n * (t - w / 2) / D):
                                      int(n * (t + w / 2) / D)]))

    both = run(slow_dynamics_enabled=True)

    base, peak, late = cvp_at(both, 100), cvp_at(both, 160), cvp_at(both, 880)
    rise = peak - base
    assert rise > 0.5, f"bolus did not raise CVP meaningfully: +{rise:.2f} mmHg"

    dissipated = (peak - late) / rise
    assert dissipated > 0.60, (
        f"combined mechanisms dissipated only {dissipated * 100:.1f}% of the CVP "
        f"rise; [S1] has MSFP returning to near baseline (~82%)"
    )
    assert dissipated < 1.05, (
        f"combined mechanisms dissipated {dissipated * 100:.1f}% — CVP has "
        f"overshot below its pre-infusion level, which [S1] does not show "
        f"(it settles 'somewhat above the initial level')"
    )


# ===========================================================================
# Infrastructure added for the Lister 1963 comparison (fast).
#
# Two capabilities the human validation needs, guarded so they cannot rot:
#   - a drug INFUSION WINDOW, because slow dynamics run in deviation form from
#     the state at SETTLE_S. A drug present from t=0 is baked into that
#     reference, so the Starling balance is zeroed at the drugged state and a
#     vasopressor appears to have no fluid effect whatsoever. Lister's
#     norepinephrine experiment is unreproducible without starting the drug
#     after settling.
#   - plasma volume / haematocrit outputs, because that is what Lister
#     measures. Blood volume alone cannot supply them once red cells are
#     leaving with the bleed.
# ===========================================================================

def test_drug_window_defaults_are_inert():
    """The default window (0 -> inf) must leave drug behaviour unchanged."""
    from model.circulation import _drug_factors_at
    from model.pharmacology import combined_drug_factors, NEUTRAL_FACTORS

    p = SimParams()
    p.drug_factors = combined_drug_factors({"norepinephrine": 0.1})
    for t in (0.0, 1.0, 1e6):
        assert _drug_factors_at(p, t) is p.drug_factors, (
            f"default drug window altered the factors at t={t}"
        )

    p.drug_start_s, p.drug_stop_s = 100.0, 200.0
    assert _drug_factors_at(p, 99.9) is NEUTRAL_FACTORS
    assert _drug_factors_at(p, 100.0) is p.drug_factors
    assert _drug_factors_at(p, 199.9) is p.drug_factors
    assert _drug_factors_at(p, 200.0) is NEUTRAL_FACTORS, (
        "drug still acting after drug_stop_s"
    )


def test_drug_window_moves_pressure_at_onset_and_offset():
    """A windowed pressor must actually step the pressure on and off.

    Guards against the window silently doing nothing — which is exactly how a
    drug baked into the slow-dynamics reference would look.
    """
    from model.pharmacology import combined_drug_factors

    D = 200.0
    p = SimParams()
    p.ventilation_mode = "none"
    p.drug_factors = combined_drug_factors({"norepinephrine": 0.15})
    p.drug_start_s, p.drug_stop_s = 80.0, 140.0
    r = run_simulation(p, duration_s=D, dt=DT)

    def mean_at(t, w=10.0):
        n = len(r["map"])
        return float(np.mean(r["map"][int(n * (t - w / 2) / D):
                                      int(n * (t + w / 2) / D)]))

    before, during, after = mean_at(70), mean_at(110), mean_at(190)
    assert during - before > 5.0, (
        f"pressor raised MAP only {during - before:.1f} mmHg inside its window"
    )
    assert during - after > 5.0, (
        f"MAP stayed elevated {after:.1f} mmHg after drug_stop_s — the window "
        f"is not switching the drug off"
    )


def test_slow_diagnostics_are_consistent_and_absent_when_off():
    """Plasma volume + red cells must equal blood volume, and NaN before init."""
    p_off = SimParams()
    p_off.ventilation_mode = "none"
    r_off = run_simulation(p_off, duration_s=5.0, dt=DT)
    for key in ("plasma_volume", "haematocrit", "interstitial_volume",
                "oncotic_pressure"):
        assert key not in r_off, (
            f"{key} emitted with slow dynamics off — an ordinary run must not "
            f"pay for slow-dynamics diagnostics"
        )

    p = SimParams()
    p.ventilation_mode = "none"
    p.slow_dynamics_enabled = True
    D = 80.0
    r = run_simulation(p, duration_s=D, dt=DT)

    # Before SETTLE_S the reference has not been captured; the diagnostics must
    # say so rather than report a plausible-looking wrong number.
    early = int(30.0 / DT)
    assert np.isnan(r["plasma_volume"][early]), (
        "plasma volume reported before the slow reference was captured"
    )

    late = int(75.0 / DT)
    assert not np.isnan(r["plasma_volume"][late])
    bv = float(r["volumes"][late].sum())
    pv = float(r["plasma_volume"][late])
    hct = float(r["haematocrit"][late])
    assert abs((pv + hct * bv) - bv) < 1e-6 * bv, (
        "plasma volume and red cell volume do not sum to blood volume"
    )
    assert 0.40 < hct < 0.50, f"resting haematocrit {hct:.3f} is not physiological"
    assert 20.0 < float(r["oncotic_pressure"][late]) < 30.0, (
        "resting plasma oncotic pressure outside the physiological range"
    )


def test_norepinephrine_lowers_plasma_volume_and_reverses():
    """[S4] A pressor must move fluid OUT of the plasma, reversibly.

    Lister's cleanest experiment: norepinephrine infused into an unbled healthy
    man reduced plasma volume by 15% and 19%, recovering within about an hour of
    stopping (Fig 5). The magnitude is badly under-predicted here — see the
    slow test below — but the SIGN and the REVERSIBILITY are physiology this
    model does get right, and they are worth guarding cheaply.

    The sign is not obvious and is easy to break. venous_tone_factor runs
    INVERTED relative to every other drug factor, and svr_factor (precapillary
    constriction, which LOWERS capillary pressure) pulls against it. Flip either
    and a pressor would start auto-transfusing the patient.

    Short window on purpose: the mechanism plateaus within ~25 min, so a few
    minutes is enough to establish direction.
    """
    from model.pharmacology import combined_drug_factors

    D = 450.0
    p = SimParams()
    p.ventilation_mode = "none"
    p.slow_dynamics_enabled = True
    p.drug_factors = combined_drug_factors({"norepinephrine": 0.15})
    p.drug_start_s, p.drug_stop_s = 90.0, 300.0
    r = run_simulation(p, duration_s=D, dt=DT)

    def pv_at(t, w=6.0):
        n = len(r["plasma_volume"])
        seg = r["plasma_volume"][int(n * (t - w / 2) / D):int(n * (t + w / 2) / D)]
        return float(np.nanmean(seg))

    before, during, after = pv_at(85), pv_at(297), pv_at(440)

    assert during < before - 0.5, (
        f"norepinephrine did not move fluid out of the plasma "
        f"({during - before:+.2f} mL). [S4] Fig 5 has plasma volume falling "
        f"15-19% under NE; the sign here is wrong or the pathway is dead"
    )
    recovered = (after - during) / (before - during)
    assert recovered > 0.5, (
        f"plasma volume recovered only {recovered * 100:.0f}% after the "
        f"infusion stopped; [S4] has it returning within about an hour"
    )


# ===========================================================================
# Phase 2 vs Lister 1963 — the human anchor. Both marked slow.
# ===========================================================================

@pytest.mark.slow
def test_refill_trajectory_matches_lister_human_haemorrhage():
    """[S4] Refill after a human-protocol bleed must run at a human rate.

    Lister's protocol, reproduced: 550 mL (about 10% of blood volume) drawn
    over 15 min, which in his subjects was essentially non-hypotensive. He
    reports (Table 1, n=6) a mean refill rate of 27.9 mL/h over 0-24 h
    (range 18.8-36.7), 50-80% of the loss replaced at 24 h, and completion only
    at 36-48 h.

    Refill is front-loaded — reading his Figs 3 and 7, roughly 150 mL is back
    inside the first 2 h, so the early rate is around 2-3x the 24 h mean, of
    order 60-100 mL/h. The band below spans that with room either side; it is
    deliberately wide because the 2 h figure is read off a 1963 scan, while the
    tabulated 24 h rates are the firm numbers.

    What the band is really guarding is the two failure modes that matter:
      - no meaningful refill at all (the pre-Phase-2 model, which left a bled
        patient in fixed shock forever), and
      - DOG-like refill. Lister states the contrast directly: the dog refills
        "to a maximum level in some instances in an hour or less", man "more
        gradual, occupying 36 to 48 hours". A model that completes inside 2 h
        is reproducing the wrong species.

    ~2 h simulated (about 40 min wall) — hence `slow`.
    """
    D = 7200.0
    BLEED_ML, BLEED_S = 550.0, 900.0
    t_end_bleed = 120.0 + BLEED_S

    p = SimParams()
    p.ventilation_mode = "none"
    p.baroreflex_enabled = True
    p.slow_dynamics_enabled = True
    p.hemorrhage_rate_mlmin = BLEED_ML / (BLEED_S / 60.0)
    p.hemorrhage_start_s = 120.0
    p.hemorrhage_duration_s = BLEED_S
    r = run_simulation(p, duration_s=D, dt=DT)

    def bv(t, w=20.0):
        n = len(r["volumes"])
        return float(r["volumes"][int(n * (t - w / 2) / D):
                                  int(n * (t + w / 2) / D)].sum(axis=1).mean())

    def hct(t, w=20.0):
        n = len(r["haematocrit"])
        return float(np.nanmean(r["haematocrit"][int(n * (t - w / 2) / D):
                                                 int(n * (t + w / 2) / D)]))

    pre, post, end = bv(110), bv(t_end_bleed), bv(7180)
    deficit = pre - post
    assert deficit > 350.0, f"bleed did not remove enough volume: {deficit:.0f} mL"

    # Rate over the ~1.7 h following the bleed.
    hours = (7180 - t_end_bleed) / 3600.0
    rate = (end - post) / hours
    assert 30.0 < rate < 200.0, (
        f"refill ran at {rate:.0f} mL/h over the {hours:.1f} h after the bleed. "
        f"[S4] Table 1 gives a 0-24 h mean of 27.9 mL/h (18.8-36.7) in man, and "
        f"his Figs 3/7 put the early rate at roughly 60-100 mL/h"
    )

    # Must NOT be finished. This is the species discriminator.
    frac = (end - post) / deficit
    assert frac < 0.60, (
        f"refill replaced {frac * 100:.0f}% of the loss within 2 h. [S4] has "
        f"50-80% at TWENTY-FOUR hours and completion at 36-48 h; refilling this "
        f"fast is the canine pattern he explicitly contrasts with man"
    )
    assert frac > 0.05, (
        f"refill replaced only {frac * 100:.1f}% of the loss in 2 h"
    )

    # Haematocrit is what Lister actually measured. His Fig 2 has LVH still at
    # ~98-99% of pre-bleed at 2 h, reaching 75-87% only by 72 h.
    hct_drop = (hct(110) - hct(7180)) / hct(110)
    assert 0.0 < hct_drop < 0.08, (
        f"haematocrit fell {hct_drop * 100:.1f}% within 2 h; [S4] Fig 2 has a "
        f"few per cent at 2 h and only 13-25% by 72 h"
    )


@pytest.mark.xfail(strict=True, reason=(
    "KNOWN GAP, not a flaky test. Modelled capillary pressure is nearly "
    "insensitive to vasoactive drugs, so a pressor barely shifts fluid: "
    "measured -0.13% against Lister's -15%/-19%, a shortfall of about 100x. "
    "Cause is structural — the *_art compartments sit at 8-22 mmHg, just above "
    "their paired veins, because the arteriolar resistance is UPSTREAM of them, "
    "so Pc = P_v + 0.20*(P_a - P_v) is essentially venous pressure and the fixed "
    "0.20 weighting cannot express the disproportionate VENULAR constriction "
    "Lister invokes. Precapillary constriction (svr_factor, lowers Pc) and "
    "venoconstriction (venous_tone_factor, raises Pc) then very nearly cancel: "
    "net dPc = +0.15 mmHg for a 20 mmHg rise in systolic pressure. Fixing this "
    "needs a drug-sensitive pre/post-capillary resistance ratio (backlog). "
    "strict=True so this flips to a FAILURE the day it starts passing."
))
@pytest.mark.slow
def test_norepinephrine_plasma_volume_magnitude_matches_lister():
    """[S4] NE in an unbled human should remove 15-19% of the plasma volume.

    Lister Fig 5: two control subjects, no haemorrhage, NE titrated to raise
    systolic pressure 40-50 mmHg, each with a paired 5% glucose infusion run at
    matched infusion and sampling rates so the difference is attributable to the
    drug alone. Plasma volume fell 15% (C.M.) and 19% (J.B.). Direct plasma
    volume measurement at the height of the effect confirmed it was a real loss
    of dye-dilution volume, not red-cell release or plasma trapping.

    In bled subjects the same infusion removed 220-480 mL, 9-14% of the
    pre-infusion plasma volume, reversing refill at its peak rate — which is why
    this matters clinically and not just numerically.

    ~50 min simulated (about 16 min wall) — hence `slow`. The mechanism plateaus
    inside 25 min, so this is long enough to settle the magnitude.
    """
    from model.pharmacology import combined_drug_factors

    D = 3000.0
    p = SimParams()
    p.ventilation_mode = "none"
    p.slow_dynamics_enabled = True
    p.drug_factors = combined_drug_factors({"norepinephrine": 0.15})
    p.drug_start_s, p.drug_stop_s = 300.0, D
    r = run_simulation(p, duration_s=D, dt=DT)

    def pv_at(t, w=20.0):
        n = len(r["plasma_volume"])
        return float(np.nanmean(r["plasma_volume"][int(n * (t - w / 2) / D):
                                                   int(n * (t + w / 2) / D)]))

    before, after = pv_at(290), pv_at(2980)
    drop = (before - after) / before
    assert drop > 0.10, (
        f"norepinephrine removed {drop * 100:.2f}% of the plasma volume; [S4] "
        f"Fig 5 measured 15% and 19% in normal man"
    )


# ===========================================================================
# Phase 3-4 validation tests land below, each marked @pytest.mark.slow.
# ===========================================================================
