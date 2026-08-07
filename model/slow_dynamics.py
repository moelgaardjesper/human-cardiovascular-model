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
    """Build a neutral SlowState sized to the compartment list."""
    return SlowState(v0_relax_ml=np.zeros(len(compartments), dtype=float))


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

    dt_slow = t - state.last_update_s
    if dt_slow < SLOW_DT:
        return
    state.last_update_s = t

    # Phase 1: venous stress relaxation   -> _update_stress_relaxation(...)
    # Phase 2: transcapillary refill      -> _update_fluid_exchange(...)
    # Phase 3: RAAS / ADH                 -> _update_neurohumoral(...)
    # Phase 4: baroreflex resetting       -> _update_setpoint(...)
    return
