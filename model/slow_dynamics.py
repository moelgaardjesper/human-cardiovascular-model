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


# ---------------------------------------------------------------------------
# Phase 2 — transcapillary refill (Starling filtration)
# ---------------------------------------------------------------------------
#
# Net fluid flux across the capillary wall:
#
#     J_v = Kf * [ (P_c - P_i) - sigma*(pi_p - pi_i) ]     (+ve = out of plasma)
#
# In haemorrhage capillary pressure falls, fluid is absorbed from the
# interstitium, and plasma volume is partly restored. Upright, capillary
# pressure in dependent limbs rises and fluid filters OUT. The mechanism is
# bidirectional and is what makes a 10-minute measurement differ from a
# 40-second one.
#
# Implemented in DEVIATION form — driven by the departure of each term from its
# resting value (captured at SETTLE_S) — so the resting Starling balance is
# exactly zero by construction and enabling the mechanism cannot shift baseline
# haemodynamics. (In vivo there is a small net resting filtration balanced by
# lymph flow, ~2 mL/min; modelling that absolutely would require the lymphatic
# balance to be calibrated to cancel it exactly, which buys nothing here.)
#
# Kf: whole-body filtration coefficient. Guyton's figure is a net filtration of
# ~2 mL/min at a net force imbalance of ~0.3 mmHg, i.e. ~6.7 mL/min/mmHg for the
# whole body. Lister 1963 (below) derived 5.6 +/- 1.4 mL/(min*mmHg*50 kg lean
# body mass) from haemorrhage in normal man — consistent.
KF_TOTAL_ML_PER_MIN_MMHG = 6.7
KF_TOTAL = KF_TOTAL_ML_PER_MIN_MMHG / 60.0        # mL/s/mmHg

# Reflection coefficient — the fraction of protein the wall holds back. ~0.9
# means filtered fluid is nearly protein-free, which is why the FIRST phase of
# refill dilutes plasma protein and thereby brakes itself.
SIGMA_PROTEIN = 0.9

# Capillary pressure sits between the arteriolar and venular ends, closer to the
# venous side because post-capillary resistance is the smaller of the two
# (R_pre/R_post ~ 4):  P_c = P_v + FRACTION*(P_a - P_v).
CAPILLARY_PRESSURE_FRACTION = 0.20

# Capillary beds: (arterial compartment, venous compartment, share of total Kf).
# Shares follow roughly the resting distribution of cardiac output / exchange
# surface across the systemic beds represented in the model.
CAPILLARY_BEDS = (
    ("upper_body_art",  "upper_body_vein",  0.30),
    ("renal_art",       "renal_vein",       0.15),
    ("splanchnic_art",  "splanchnic_vein",  0.35),
    ("lower_body_art",  "thigh_vein",       0.20),
)

# Plasma protein and oncotic pressure. Normal plasma protein ~70 g/L over a
# ~3 L plasma volume. Oncotic pressure from the Landis-Pappenheimer relation,
#     pi = 2.1c + 0.16c^2 + 0.009c^3      (c in g/dL, pi in mmHg)
# which gives 25.6 mmHg at 7 g/dL — the textbook value, and importantly it is
# NONLINEAR, so dilution costs less oncotic pressure than a linear law implies.
PLASMA_PROTEIN_G_PER_L = 70.0

# Red cell volume is treated as constant (no haemorrhage-independent red cell
# loss on this timescale), so plasma volume follows total blood volume. Resting
# haematocrit 0.45.
HAEMATOCRIT = 0.45

# Lymphatic protein return. The second phase of refill: protein returns to the
# plasma, sustaining oncotic pressure and permitting further absorption. Slow
# relative to the fluid shift.
TAU_LYMPH = 3600.0   # s


def oncotic_pressure_mmhg(protein_g: float, plasma_volume_ml: float) -> float:
    """Landis-Pappenheimer plasma colloid osmotic pressure."""
    if plasma_volume_ml <= 1.0:
        return 0.0
    c = protein_g / (plasma_volume_ml / 100.0)   # g/dL
    return 2.1 * c + 0.16 * c * c + 0.009 * c * c * c


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
    # Plasma oncotic pressure is what BRAKES refill: absorbed fluid is nearly
    # protein-free (sigma ~ 0.9), so it dilutes plasma protein, pi_p falls, net
    # absorption returns toward zero and the mechanism self-limits. Without a
    # dynamic pi_p refill runs away over hours.
    #
    # Plasma volume is NOT a separate state — it is derived from the compartment
    # volumes (total blood volume minus a constant red cell volume), so it
    # cannot drift out of step with the circulation the ODE is integrating.
    plasma_protein_g: float = 0.0

    # Red cell volume (mL). NOT a constant: whole-blood haemorrhage removes red
    # cells along with plasma, so holding this fixed would make plasma volume
    # read far too low after a bleed and manufacture a large spurious oncotic
    # gradient. Tracked so that whole-blood loss leaves haematocrit unchanged
    # (correct physiology) while protein-free refill dilutes it.
    red_cell_volume_ml: float = 0.0

    # Total blood volume at the previous slow step, used to attribute
    # blood-volume changes the slow module did not itself cause.
    prev_blood_volume_ml: float = 0.0

    # Interstitial reservoir, as a DEVIATION from rest (mL). Negative = the
    # interstitium has given up fluid to the plasma, as in haemorrhage.
    interstitial_volume_ml: float = 0.0

    # Cumulative fluid moved plasma->interstitium (mL, signed). Diagnostic:
    # lets a test read the refill volume directly rather than inferring it.
    cumulative_filtration_ml: float = 0.0

    # Resting references, captured at SETTLE_S alongside p_ref.
    pc_ref: np.ndarray | None = None      # capillary pressure per bed
    pi_p_ref: float = 0.0                 # plasma oncotic pressure
    plasma_volume_ref_ml: float = 0.0

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


def _capillary_pressures(P: np.ndarray, idx_map: dict) -> np.ndarray:
    """Capillary pressure for each bed, between its arteriolar and venular ends."""
    out = np.zeros(len(CAPILLARY_BEDS))
    for k, (art, ven, _share) in enumerate(CAPILLARY_BEDS):
        p_a, p_v = P[idx_map[art]], P[idx_map[ven]]
        out[k] = p_v + CAPILLARY_PRESSURE_FRACTION * (p_a - p_v)
    return out


def _update_fluid_exchange(state: SlowState, dt_slow: float, V: np.ndarray,
                           P: np.ndarray, idx_map: dict) -> np.ndarray:
    """Starling filtration across each capillary bed.

    Returns the per-compartment volume change (mL) to apply to the circulation:
    negative where fluid has left the plasma, positive where it was absorbed.

    Driven by deviations from the resting state, so the resting balance is
    exactly zero and enabling the mechanism cannot move baseline haemodynamics.
    """
    dV = np.zeros(len(V))
    blood_volume = float(V.sum())

    # --- Attribute blood-volume change since the last slow step -------------
    # Whatever the slow module did not itself move must have come from the fast
    # ODE: whole-blood haemorrhage, or a crystalloid bolus. They affect red cell
    # mass differently, and getting this wrong corrupts plasma volume and hence
    # every oncotic term.
    delta_other = (blood_volume - state.prev_blood_volume_ml)
    if state.prev_blood_volume_ml > 0.0 and delta_other < 0.0:
        # Blood lost: red cells leave at the prevailing haematocrit, so
        # haematocrit is unchanged by the bleed itself — as in vivo.
        rcv_before = state.red_cell_volume_ml
        hct = rcv_before / max(state.prev_blood_volume_ml, 1.0)
        state.red_cell_volume_ml = max(0.0, rcv_before + delta_other * hct)
        # Protein leaves with the lost plasma, at the prevailing concentration.
        # prev_plasma must use the PRE-loss red cell volume, or the
        # concentration is under-stated and protein is under-removed.
        prev_plasma = max(state.prev_blood_volume_ml - rcv_before, 1.0)
        state.plasma_protein_g = max(
            0.0, state.plasma_protein_g + delta_other * (1.0 - hct)
            * (state.plasma_protein_g / prev_plasma)
        )
    # A positive delta_other is crystalloid: volume without red cells or protein,
    # so both are left alone and haematocrit falls, which is correct.

    # Plasma volume follows the circulation the ODE is actually integrating.
    plasma_volume = blood_volume - state.red_cell_volume_ml
    pi_p = oncotic_pressure_mmhg(state.plasma_protein_g, plasma_volume)

    pc = _capillary_pressures(P, idx_map)

    for k, (_art, ven, share) in enumerate(CAPILLARY_BEDS):
        # Net Starling imbalance relative to rest. The oncotic term is the
        # brake: absorbing fluid dilutes plasma protein, pi_p falls below its
        # reference, and the (-sigma * negative) term pushes the imbalance back
        # toward zero.
        d_pc = pc[k] - state.pc_ref[k]
        d_pi = pi_p - state.pi_p_ref
        jv = KF_TOTAL * share * (d_pc - SIGMA_PROTEIN * d_pi)   # mL/s, +ve = out

        moved = jv * dt_slow
        dV[idx_map[ven]] -= moved
        state.interstitial_volume_ml += moved
        state.cumulative_filtration_ml += moved

    # Lymphatic protein return — the second phase of refill. Protein returns to
    # the plasma, sustaining oncotic pressure and permitting further absorption.
    # Modelled as first-order relaxation of plasma protein back toward the mass
    # that would restore the resting concentration.
    target_protein = PLASMA_PROTEIN_G_PER_L * (state.plasma_volume_ref_ml / 1000.0)
    state.plasma_protein_g += (
        (target_protein - state.plasma_protein_g) * dt_slow / TAU_LYMPH
    )

    # Carry forward the blood volume INCLUDING this step's own flux, so the next
    # step's attribution sees only what the fast ODE did.
    state.prev_blood_volume_ml = blood_volume + float(dV.sum())

    return dV


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
):
    """
    Advance the slow state to simulated time `t`, in place.

    Returns a per-compartment volume change (mL) to apply to the circulation —
    transcapillary fluid moved into or out of the plasma this step — or None if
    nothing was advanced.

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

    idx_map = {c.name: k for k, c in enumerate(params.compartments)}

    # Hold everything inert until the model has settled, then capture the
    # resting reference from its own state (see SETTLE_S).
    if t < SETTLE_S:
        return
    if state.p_ref is None:
        state.p_ref = np.array(P, dtype=float, copy=True)
        blood_volume = float(V.sum())
        state.red_cell_volume_ml = blood_volume * HAEMATOCRIT
        state.plasma_volume_ref_ml = blood_volume - state.red_cell_volume_ml
        state.plasma_protein_g = (
            PLASMA_PROTEIN_G_PER_L * state.plasma_volume_ref_ml / 1000.0
        )
        state.pc_ref = _capillary_pressures(P, idx_map)
        state.pi_p_ref = oncotic_pressure_mmhg(
            state.plasma_protein_g, state.plasma_volume_ref_ml
        )
        state.prev_blood_volume_ml = blood_volume
        state.last_update_s = t
        return

    dt_slow = t - state.last_update_s
    if dt_slow < SLOW_DT:
        return
    state.last_update_s = t

    if getattr(params, "slow_stress_relaxation_enabled", True):
        _update_stress_relaxation(state, dt_slow, P, params.compartments)

    if getattr(params, "slow_fluid_exchange_enabled", True):
        return _update_fluid_exchange(state, dt_slow, V, P, idx_map)
    return None

    # Phase 2: transcapillary refill      -> _update_fluid_exchange(...)
    # Phase 3: RAAS / ADH                 -> _update_neurohumoral(...)
    # Phase 4: baroreflex resetting       -> _update_setpoint(...)
    return
