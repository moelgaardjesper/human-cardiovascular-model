"""
Slow-timescale cardiovascular dynamics (minutes to hours).

Motivation
----------
Before this module the model's slowest mechanism was the sympathetic-slow
baroreflex arm at tau = 20 s. A timescale audit (2026-08-06) showed the model
reaches equilibrium within ~40 s of a step perturbation and is then stationary:
drift from t=20-40 s out to 5 min was <= 2.5 % on MAP and <= 4.2 % on CO for
every tilt scenario tested.

That is a problem for validation, because much of the literature the model is
checked against reports at minutes, not seconds:

    Wieling 1998 (HUT)          1 min
    Claeys 1988 (propofol)      2 min
    Sejersen 2022 (HDT)        10 min
    Sarafian 2017 (graded HUT) 16 min per stage

Since the model was already stationary by 40 s, that mismatch could NOT be
closed by simulating longer — there was nothing left to happen. In the same
window a real subject undergoes transcapillary fluid exchange, venous stress
relaxation, and neurohumoral activation. This module supplies that missing
1-minute-to-2-hour band.

Mechanisms (added in dependency order; see docs/ideas_backlog.md)
----------------------------------------------------------------
1. Venous stress relaxation   tau ~ 300-600 s   viscoelastic creep of vein wall
2. Transcapillary refill      tau ~ 300-3600 s  Starling filtration/absorption
3. RAAS / ADH                 tau ~ 600-1200 s  Ang II + ADH vasoconstriction
4. Baroreflex resetting       tau ~ 900-1800 s  setpoint adaptation

Design
------
These states have time constants of 1e2-1e4 s, so integrating them on the 1 ms
fast clock is wasted work. They advance on their own coarse clock (SLOW_DT),
which is still ~3 orders of magnitude finer than the fastest of them. The fast
ODE in circulation._odes is untouched.

Everything here is gated by `SimParams.slow_dynamics_enabled`. With the flag
off, `SlowState` is inert and the model is bit-for-bit identical to the
pre-existing behaviour — the fast regression suite is the ratchet and must not
move because this module exists.
"""

from dataclasses import dataclass, field

import numpy as np


# Slow-state integration step (s of simulated time). The fastest slow mechanism
# has tau ~ 300 s, so 0.1 s is ~3000x finer than needed — chosen to be cheap
# (1 update per 100 fast steps at dt=1 ms) while leaving headroom if a future
# mechanism turns out to be faster than expected.
SLOW_DT = 0.1

# Settling delay (s) before the slow mechanisms engage, and before the resting
# reference state is captured.
#
# WHY THIS EXISTS. Every slow mechanism is driven by a DEVIATION from rest, so
# it needs a resting reference. The obvious choice — each compartment's
# `init_volume` — turns out NOT to be the model's true equilibrium: the volumes
# redistribute by ~174 mL over the first minute, leaving settled venous
# pressures 0.9-4.6 mmHg above their init-derived values (IVC worst, 195 ->
# 263 mL, 5.0 -> 9.6 mmHg). Referencing init_volume therefore left stress
# relaxation seeing a permanent positive deviation and creeping continuously,
# dropping resting MAP by ~1.4 mmHg — the mechanism was not neutral at rest.
#
# Capturing the reference from the model's OWN settled state instead makes the
# module exactly neutral at rest by construction, and is the physiologically
# sensible reading: viscoelastic creep responds to a change in distension from
# the recent quiescent state, not to an absolute pressure.
#
# CONSEQUENCE FOR SCENARIO DESIGN: slow-dynamics scenarios must let the model
# settle supine before applying a perturbation. A scenario that is already
# tilted at t=0 would capture the tilted state as its reference and the
# mechanisms would not respond to the tilt itself.
#
# (The stale init_volume values are a real and separate finding — see
# docs/ideas_backlog.md — but re-deriving them changes the fast model, so it is
# deliberately not bundled into this phase.)
SETTLE_S = 60.0


# ---------------------------------------------------------------------------
# Phase 1 — venous stress relaxation (viscoelastic creep)
# ---------------------------------------------------------------------------
#
# Under sustained distension the vein wall creeps: tension falls and volume is
# accommodated at lower pressure. Classic demonstration (Guyton, in anaesthetised
# reflex-blocked dogs): rapidly infusing 35 % of blood volume drove mean systemic
# filling pressure to ~24 mmHg, which then decayed asymptotically back toward
# somewhat above the pre-infusion level, with a HALF-TIME OF 2-4 MINUTES.
#
# tau from that half-time: tau = t_half / ln 2 = 120/0.693 .. 240/0.693
#                              = 173 .. 346 s. 250 s sits mid-range.
TAU_STRESS_RELAX = 250.0   # s

# Magnitude. Modelled as a slowly-growing addition to unstressed volume:
#
#     dV0_relax/dt = (k*(P_tm - P_ref) - V0_relax) / tau
#
# At steady state V0_relax = k*(P_tm - P_ref), so for a compartment of
# compliance C the fraction of an acute pressure rise that is dissipated is
#
#     f = (k/C) / (1 + k/C)      i.e.   k = C * f/(1-f)
#
# expressing k as a multiple of that compartment's own compliance.
#
# CALIBRATION NOTE — deliberately conservative. In the Guyton experiment MSFP
# decayed most of the way back to baseline, but the source attributes part of
# that to fluid moving into the interstitium, which is transcapillary filtration
# (Phase 2) and NOT viscoelastic creep. Attributing the whole decay to stress
# relaxation here would double-count once Phase 2 lands. f = 0.30 takes roughly
# the fast third; the remainder is expected to come from filtration, and the
# combined behaviour is what gets validated against the full decay curve.
RELAX_FRACTION = 0.30
K_RELAX = RELAX_FRACTION / (1.0 - RELAX_FRACTION)   # multiplier on compliance

# Applied to the systemic venous capacitance vessels only. Arteries undergo
# comparatively little viscoelastic creep relative to their (small) volume
# changes, and the cardiac chambers are governed by time-varying elastance.
STRESS_RELAX_COMPARTMENTS = (
    "upper_body_vein", "svc", "renal_vein", "splanchnic_vein",
    "thigh_vein", "calf_vein", "foot_vein", "ivc",
)


@dataclass
class SlowState:
    """
    Mutable slow-timescale state carried alongside the fast volume vector.

    All fields are absolute quantities, not deltas, so the state can be
    inspected directly and reported without reconstruction.

    Phase 0 defines the container and the clock only; the mechanism fields are
    populated by later phases. A field that its phase has not yet implemented
    holds its neutral value and has no effect.
    """

    # --- Phase 1: venous stress relaxation ---------------------------------
    # Additive offset (mL) to each compartment's unstressed volume. Positive =
    # the vessel has crept, accommodating volume at lower pressure.
    v0_relax_ml: np.ndarray | None = None

    # --- Phase 2: transcapillary refill ------------------------------------
    # Plasma and interstitial fluid + protein. Protein mass matters because
    # plasma oncotic pressure is what BRAKES refill: as plasma is diluted,
    # pi_p falls, net filtration returns toward zero, and the mechanism
    # self-limits. Without a dynamic pi_p, refill runs away over hours.
    plasma_volume_ml: float = 0.0
    plasma_protein_g: float = 0.0
    interstitial_volume_ml: float = 0.0
    interstitial_protein_g: float = 0.0

    # --- Phase 3: RAAS / ADH -----------------------------------------------
    # Normalised activation, 0 = none, 1 = maximal. Effects are applied as
    # multipliers on SVR (and, for ADH V2, on renal water handling).
    angiotensin: float = 0.0
    adh: float = 0.0

    # --- Phase 4: baroreflex resetting -------------------------------------
    # Offset (mmHg) applied to the baroreflex MAP setpoint. Without this the
    # reflex defends 93 mmHg indefinitely; in vivo it adapts over minutes to
    # hours, which is why a sustained deviation stops being fought.
    map_setpoint_offset: float = 0.0

    # --- Bookkeeping --------------------------------------------------------
    # Simulated time (s) at which the slow state was last advanced.
    last_update_s: float = -1e9

    # Resting transmural pressure per compartment (mmHg). NOT taken from
    # init_volume (which is not the model's true equilibrium — see SETTLE_S);
    # captured from the model's own settled state at t = SETTLE_S, and None
    # until then. Every slow mechanism is driven by a DEVIATION from this, so
    # the module is exactly neutral at rest by construction.
    p_ref: np.ndarray | None = None

    # Indices the stress-relaxation mechanism acts on (resolved once at init).
    relax_idx: tuple = ()

    def as_dict(self) -> dict:
        """Flat snapshot for reporting / logging."""
        return {
            "plasma_volume_ml": self.plasma_volume_ml,
            "plasma_protein_g": self.plasma_protein_g,
            "interstitial_volume_ml": self.interstitial_volume_ml,
            "interstitial_protein_g": self.interstitial_protein_g,
            "angiotensin": self.angiotensin,
            "adh": self.adh,
            "map_setpoint_offset": self.map_setpoint_offset,
        }


def init_slow_state(compartments) -> SlowState:
    """Build a neutral SlowState sized to the compartment list.

    Resting transmural pressures are captured here so that every slow mechanism
    is driven by a DEVIATION from rest. That makes the whole module exactly
    neutral at baseline: at rest every driving term is zero, so enabling slow
    dynamics cannot shift resting haemodynamics.
    """
    n = len(compartments)
    names = [c.name for c in compartments]
    relax_idx = tuple(
        names.index(nm) for nm in STRESS_RELAX_COMPARTMENTS if nm in names
    )
    # p_ref is left None deliberately: it is captured from the model's own
    # settled state at t = SETTLE_S, not from init_volume. See SETTLE_S.
    return SlowState(
        v0_relax_ml=np.zeros(n, dtype=float),
        p_ref=None,
        relax_idx=relax_idx,
    )


def _update_stress_relaxation(state: SlowState, dt_slow: float,
                              P: np.ndarray, compartments) -> None:
    """Viscoelastic creep of the venous wall.

    Sustained distension (P above its resting value) slowly raises unstressed
    volume, accommodating the extra volume at a lower pressure. Relaxes back
    when the distension is removed — the same first-order law runs both ways.
    """
    for idx in state.relax_idx:
        c = compartments[idx]
        target = K_RELAX * c.compliance * (P[idx] - state.p_ref[idx])
        state.v0_relax_ml[idx] += (
            (target - state.v0_relax_ml[idx]) * dt_slow / TAU_STRESS_RELAX
        )


def update_slow_state(
    state: SlowState,
    t: float,
    V: np.ndarray,
    P: np.ndarray,
    params,
    baro=None,
) -> None:
    """
    Advance the slow state to simulated time `t`, in place.

    Called from the fast integration loop, but only does work when at least
    SLOW_DT of simulated time has elapsed since the last advance. Safe to call
    every fast step.

    Parameters
    ----------
    state : SlowState        state to advance (mutated in place)
    t     : float            current simulated time (s)
    V     : np.ndarray       compartment volumes (mL)
    P     : np.ndarray       compartment transmural pressures (mmHg)
    params: SimParams        simulation parameters
    baro  : BaroreflexController | None

    Notes
    -----
    Phase 0 implements the clock only. Each mechanism is added in its own phase
    and validated before the next is started; see the module docstring.
    """
    if not getattr(params, "slow_dynamics_enabled", False):
        return

    # Hold everything inert until the model has settled, then capture the
    # resting reference from its own state (see SETTLE_S).
    if t < SETTLE_S:
        return
    if state.p_ref is None:
        state.p_ref = np.array(P, dtype=float, copy=True)
        state.last_update_s = t
        return

    dt_slow = t - state.last_update_s
    if dt_slow < SLOW_DT:
        return
    state.last_update_s = t

    _update_stress_relaxation(state, dt_slow, P, params.compartments)

    # Phase 2: transcapillary refill      -> _update_fluid_exchange(...)
    # Phase 3: RAAS / ADH                 -> _update_neurohumoral(...)
    # Phase 4: baroreflex resetting       -> _update_setpoint(...)
    return
