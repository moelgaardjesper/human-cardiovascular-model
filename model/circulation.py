"""
23-compartment lumped-parameter cardiovascular ODE system.

Primary reference:
  PMC9363491 — Heldt-based cardiovascular model for orthostatic stress
  Heldt T et al. (2002) J Appl Physiol 92:1239-1254

State vector V[0..22]: volume (mL) in each compartment.
Compartment order defined in compartments.py / default_compartments().

The original single lower_body_vein has been split into three serial
segments (foot_vein → calf_vein → thigh_vein → ivc) to correctly
simulate the ~640 mL venous pooling observed on standing (Sjöstrand 1953).

Flow between compartments:
    Q = (P_upstream - P_downstream + ΔP_hydrostatic) / R_outflow

Cardiac chamber pressure (time-varying elastance):
    P = E(t) * (V - V0)

Vascular compartment pressure:
    P = (V - V0) / C

Hydrostatic correction (gravity.py):
    ΔP = ρ g h sin(α)   [mmHg]

One-way valves (mitral, aortic, tricuspid, pulmonic) enforced by
setting Q = 0 if flow would be retrograde.
"""

import numpy as np
from scipy.integrate import solve_ivp

from .compartments import default_compartments, IDX
from .heart import (
    elastance_from_phase, frank_starling_emax,
    LV_EMAX, LV_EMIN, RV_EMAX, RV_EMIN,
    RA_EMAX, RA_EMIN, LA_EMAX, LA_EMIN,
    ATRIAL_PHASE_OFFSET,
)
from .gravity import hydrostatic_delta_mmhg, GravityEnvironment, smooth_tilt_profile, positional_itp_mmhg
from .baroreflex import BaroreflexController
from .pharmacology import combined_drug_factors, NEUTRAL_FACTORS
from .respiration import intrathoracic_pressure, respiratory_sinus_arrhythmia
from .slow_dynamics import (init_slow_state, update_slow_state,
                            oncotic_pressure_mmhg, neurohumoral_svr_factor)


# Systemic venous reservoir — holds the bulk of circulating blood volume.
# Hemorrhage removes volume from these compartments proportionally to their
# current stressed volume; this avoids creating an artificial localised
# pressure sink at any single site.
VENOUS_RESERVOIR = (
    "upper_body_vein", "svc", "renal_vein", "splanchnic_vein",
    "thigh_vein", "calf_vein", "foot_vein", "ivc",
)


# Body regions for the fluid-distribution avatar — groups compartments into
# anatomical zones. Each zone's total volume, tracked relative to its value
# at simulation start, indicates net fluid shift (e.g. leg pooling on tilt,
# abdominal/leg depletion on hemorrhage, thoracic engorgement on fluid bolus
# or Trendelenburg).
BODY_REGIONS = {
    "thorax": (
        "aorta", "brachiocephalic", "upper_body_art", "upper_body_vein", "svc",
        "right_atrium", "right_ventricle", "pulmonary_art", "pulmonary_cap",
        "pulmonary_vein", "left_atrium", "left_ventricle", "coronary",
    ),
    "abdomen": (
        "abdominal_aorta", "renal_art", "renal_vein", "splanchnic_art", "splanchnic_vein",
    ),
    "legs": (
        "lower_body_art", "thigh_vein", "calf_vein", "foot_vein", "ivc",
    ),
}


def region_volumes(V: np.ndarray) -> dict[str, float]:
    """Sum compartment volumes (mL) into the BODY_REGIONS zones."""
    return {region: float(sum(V[IDX[name]] for name in names))
            for region, names in BODY_REGIONS.items()}


# Compartments whose unstressed volume (V0) is modulated by venous tone
# (drug venous_tone_factor × baroreflex v0_vein_factor): venoconstriction
# (factor < 1) lowers V0, recruiting blood centrally; venodilation (> 1) raises
# V0, pooling blood.
#
# Applied to the MOBILIZABLE VENOUS RESERVOIR (splanchnic + upper-body/cutaneous
# beds). This is the physiology: sympathetic venoconstriction recruits chiefly
# the splanchnic capacitance bed (Rothe 1983; Gelman 2008), while the caval
# conduits, renal, and muscle/limb veins contribute little actively mobilizable
# volume. With physiological venous compliance (compartments.py) the recruited
# slug lands in a ~1.6 L stressed pool, so a ±15 % tone change moves CO ~±13 %.
MOBILIZABLE_VENOUS_RESERVOIR = ("splanchnic_vein", "upper_body_vein")
_VENOUS_TONE_IDX = frozenset(IDX[name] for name in MOBILIZABLE_VENOUS_RESERVOIR)


# Compartments that lie inside the chest and are therefore surrounded by pleural
# pressure. ITP is added to their intraluminal pressure in _odes().
#
# The governing principle is that intrathoracic pressure is a *uniform external
# pressure*. A uniform pressure applied around a closed elastic system produces
# no internal flow — it can only drive flow where a vessel crosses the chest
# wall, because that is the only place a pressure step exists. So the membership
# of this set is not a tuning knob: it fixes *where the boundaries are*, and any
# compartment wrongly left out creates a spurious ITP-driven gradient at an
# internal junction that has no business carrying one.
#
# Anatomy, and the boundaries that follow:
#   arterial out : aorta and brachiocephalic (innominate) are mediastinal →
#                  boundaries at aorta→abdominal_aorta (aortic hiatus) and
#                  brachiocephalic→upper_body_art (thoracic outlet)
#   venous in    : the SVC is entirely intrathoracic → boundary at
#                  upper_body_vein→svc, at the thoracic outlet
#   the IVC is NOT included: only its last 2–3 cm are intrathoracic, so the
#                  boundary belongs at ivc→right_atrium, where it already is
#   coronary     : epicardial, inside the pericardium
#
# Until 2026-08-25 the aorta, brachiocephalic, SVC and coronary were all
# omitted, which put the entire ITP swing across the *aortic valve* — an
# internal junction, where it acted as a spurious respiratory modulation of
# ejection. Its magnitude scaled with 1/VALVE_R, so it was largely hidden at
# VALVE_R = 0.08 and grew eightfold when the valve rebuild dropped VALVE_R to
# 0.01, taking normovolaemic PPV to 43 %. Removing it drops PPV to 32.6 % at an
# unchanged transmission fraction. Note it inflated STROKE-VOLUME variation, not
# the pressure-to-volume ratio: PPV tracks the model's own `sv` 1:1 both before
# and after (1.02 and 0.98). See docs/validation_log.md, "PPV diagnosed".
THORACIC_COMPARTMENTS = (
    "aorta", "brachiocephalic", "svc", "coronary",
    "right_atrium", "right_ventricle",
    "pulmonary_art", "pulmonary_cap", "pulmonary_vein",
    "left_atrium", "left_ventricle",
)
_THORACIC_IDX = tuple(IDX[name] for name in THORACIC_COMPARTMENTS)


# ---------------------------------------------------------------------------
# Simulation parameters dataclass
# ---------------------------------------------------------------------------

class SimParams:
    """
    All parameters needed for one simulation run.

    Attributes are intentionally public so the API layer can patch
    individual values before passing to run_simulation().
    """

    def __init__(self, compartments=None):
        self.compartments = compartments or default_compartments()

        # Heart rate baseline (bpm) — baroreflex adjusts around this
        self.hr_bpm = 70.0

        # Cardiac elastance parameters (multiplicative factors applied after patient scaling)
        self.lv_emax = LV_EMAX
        self.lv_emin = LV_EMIN
        self.rv_emax = RV_EMAX
        self.rv_emin = RV_EMIN
        self.la_emax = LA_EMAX
        self.la_emin = LA_EMIN
        self.ra_emax = RA_EMAX
        self.ra_emin = RA_EMIN

        # Posture / gravity
        self.tilt_start_deg  = 0.0                     # degrees from horizontal
        self.tilt_end_deg    = 0.0
        self.tilt_onset_s    = 0.0
        self.tilt_duration_s = 5.0
        self.gravity         = GravityEnvironment.EARTH  # m/s²

        # Drug effects (merged multiplicative factors)
        self.drug_factors = dict(NEUTRAL_FACTORS)

        # Baroreflex on/off
        self.baroreflex_enabled = True

        # Frank-Starling on/off
        self.frank_starling_enabled = True

        # SVR scaling factor from patient.py (applied to arterial resistances)
        self.svr_scale = 1.0

        # Muscle pump — calf squeeze driving venous return.
        # Default 0 = inactive (sedated/anaesthetised patients).
        # Walking: pressure ≈ 35–50 mmHg, freq ≈ 0.5–1.0 Hz.
        self.muscle_pump_pressure = 0.0   # mmHg peak calf compression
        self.muscle_pump_freq_hz  = 0.5   # Hz contraction frequency

        # Ventilation — respiratory-cardiovascular coupling.
        # mode 'none'        : ITP = 0, no RSA (default, sedated/apnoeic)
        # mode 'spontaneous' : negative-pressure breathing; ITP swings −5 to −13 cmH₂O
        # mode 'mechanical'  : positive-pressure PPV; ITP swings PEEP → PIP
        self.ventilation_mode = 'spontaneous'  # 'none' | 'spontaneous' | 'mechanical'
        self.resp_rate_bpm    = 14.0     # breaths/min (8–25 typical)
        self.peep_cmh2o       = 5.0      # cmH₂O — PEEP for mechanical ventilation
        self.pip_cmh2o        = 20.0     # cmH₂O — peak inspiratory pressure
        self.ie_ratio         = 0.33     # inspiratory fraction (0.33 = 1:2 I:E)

        # Hemorrhage — constant-rate blood volume loss over [start, start+duration].
        # Removed proportionally from the systemic venous reservoir (see
        # VENOUS_RESERVOIR), the compartments holding most circulating volume.
        # duration_s = 0 disables hemorrhage (default).
        self.hemorrhage_rate_mlmin  = 0.0
        self.hemorrhage_start_s     = 0.0
        self.hemorrhage_duration_s  = 0.0

        # Fluid bolus — constant-rate crystalloid infusion into the upper-body
        # venous compartment (peripheral/central IV access) over
        # [start, start+duration]. duration_s = 0 disables the bolus (default).
        self.fluid_bolus_ml         = 0.0
        self.fluid_bolus_start_s    = 0.0
        self.fluid_bolus_duration_s = 0.0

        # Slow-timescale dynamics (minutes to hours): transcapillary refill,
        # venous stress relaxation, RAAS/ADH, baroreflex resetting. See
        # model/slow_dynamics.py.
        #
        # Default ON as of 2026-08-11 (phases 1 and 2 validated; 3 and 4 still
        # to land). Deliberate decision, not a side effect of adding a phase.
        #
        # The reasoning: with this off, a simulated patient has NO mechanism
        # slower than the 20 s sympathetic baroreflex arm, so a bled patient
        # sits in fixed shock forever and any run longer than ~40 s is
        # stationary by construction. That is wrong in the direction that
        # matters clinically, and the API serves runs up to 300 s while live
        # mode runs indefinitely — precisely the horizon where the missing
        # physiology shows.
        #
        # Safe to default on because every mechanism is in DEVIATION form from
        # a reference captured at SETTLE_S, so it is exactly neutral at rest by
        # construction. `test_default_config_is_stable_at_rest` guards that at
        # the API's 300 s ceiling in the configuration users actually get.
        #
        # Set False to recover the pre-2026-08 behaviour exactly.
        self.slow_dynamics_enabled = True

        # Per-mechanism switches, gated by the master flag above. These exist so
        # each phase can be validated IN ISOLATION as well as in combination —
        # without them a test named after one mechanism silently measures the
        # sum of all of them. (Exactly that happened when Phase 2 landed: the
        # Phase 1 volume-load test jumped from 27 % to 81 % dissipation because
        # filtration had joined in.)
        self.slow_stress_relaxation_enabled = True
        self.slow_fluid_exchange_enabled    = True
        self.slow_raas_enabled              = True
        self.slow_adh_enabled               = True

        # Drug infusion window. Defaults reproduce the historical behaviour
        # exactly — drug_factors applied for the whole run — so nothing changes
        # unless a caller sets drug_stop_s.
        #
        # This exists because slow dynamics are in DEVIATION form from the state
        # captured at SETTLE_S. A drug present from t=0 is baked into that
        # reference, so the Starling balance is zeroed at the drugged state and
        # the mechanism reports no effect at all. Validating a vasopressor
        # against slow dynamics therefore *requires* starting it after settling.
        self.drug_start_s = 0.0
        self.drug_stop_s  = float("inf")


def _drug_factors_at(params, t):
    """Drug factors in force at time `t`.

    Outside [drug_start_s, drug_stop_s) the patient is undrugged. With the
    default window (0 -> inf) this returns params.drug_factors itself, so the
    common path is unchanged and costs one comparison.
    """
    start = getattr(params, "drug_start_s", 0.0)
    stop  = getattr(params, "drug_stop_s", float("inf"))
    if start <= t < stop:
        return params.drug_factors
    return NEUTRAL_FACTORS


# ---------------------------------------------------------------------------
# Pressure helpers
# ---------------------------------------------------------------------------

def _smooth_edges(x: np.ndarray, win: int) -> np.ndarray:
    """
    Moving average that does not corrupt the ends of the series.

    `np.convolve(x, kernel, mode="same")` implicitly zero-pads, so the first
    and last ~win/2 samples are pulled toward zero — the final sample of a
    pressure trace reads about half its true value. Any mean taken over the
    tail of the run (which is what the test helpers do) is then biased low.

    Partial-window mean instead: at every sample, average over however much of
    the window actually overlaps the data. Near the ends the window is shorter,
    so the result is the true mean of the available samples, and the interior
    is unchanged.

    Assuming nothing about what lies beyond the boundary matters here. Edge-value
    replication would work for a smooth trace like aortic_p but is wrong for
    co_ts, which is a spike train (nonzero only during ejection): replicating a
    boundary sample pads with either a mid-ejection spike or a diastolic zero
    depending on where the run stops in the cardiac cycle, injecting a
    phase-dependent error larger than the effects being measured.
    """
    x = np.asarray(x, dtype=float)
    if win <= 1 or x.size == 0:
        return x
    k   = np.ones(win)
    num = np.convolve(x, k, mode="same")
    den = np.convolve(np.ones_like(x), k, mode="same")
    return num / den


def _vascular_pressure(vol: float, v0: float, compliance: float,
                       p_stiffen: float | None = None) -> float:
    vs = vol - v0
    if p_stiffen is None or vs <= 0.0:
        return vs / compliance
    # Collapsible-vein tube law: stiffens above p_stiffen (see Compartment).
    return p_stiffen * (np.exp(vs / (compliance * p_stiffen)) - 1.0)


def _cardiac_pressure(vol: float, v0: float, e: float) -> float:
    return max(0.0, e * (vol - v0))


# ---------------------------------------------------------------------------
# Main ODE function
# ---------------------------------------------------------------------------

def _odes(t: float, V: np.ndarray, params: SimParams, baro: BaroreflexController | None,
          cardiac_phase: float, p_out: np.ndarray | None = None, slow=None):
    """
    Compute dV/dt for the 23-compartment system.

    Parameters
    ----------
    t             : time (s)
    V             : state vector, volumes (mL)
    params        : SimParams
    baro          : BaroreflexController (or None)
    cardiac_phase : continuously-integrated ventricular cycle phase
                    (fraction of RR interval, wrapped to [0, 1) by the
                    caller). Driving elastance from this rather than
                    (t % T)/T avoids phase discontinuities when HR varies
                    every step (baroreflex/RSA).
    """
    comp  = params.compartments
    drugs = _drug_factors_at(params, t)

    # -----------------------------------------------------------------------
    # Elastance parameters (baroreflex + drug modulation)
    # -----------------------------------------------------------------------
    emax_factor = drugs.get("lv_emax_factor", 1.0)
    if baro is not None:
        emax_factor *= baro.emax_factor

    lv_emax_eff = params.lv_emax * emax_factor
    rv_emax_eff = params.rv_emax * drugs.get("rv_emax_factor", 1.0)
    if baro is not None:
        rv_emax_eff *= baro.emax_factor

    # Frank-Starling: scale E_max with EDV
    if params.frank_starling_enabled:
        edv_lv = V[IDX["left_ventricle"]]
        edv_rv = V[IDX["right_ventricle"]]
        lv_emax_eff = frank_starling_emax(lv_emax_eff, edv_lv)
        rv_emax_eff = frank_starling_emax(rv_emax_eff, edv_rv, edv_ref=100.0)

    # -----------------------------------------------------------------------
    # Instantaneous elastances, driven by the continuously-integrated
    # cardiac phase (see docstring above for why not (t % T)/T).
    # -----------------------------------------------------------------------
    t_n_v = cardiac_phase % 1.0
    E_lv = elastance_from_phase(t_n_v, lv_emax_eff, params.lv_emin)
    E_rv = elastance_from_phase(t_n_v, rv_emax_eff, params.rv_emin)

    # Atria fire ~60% of cycle before ventricles (offset in phase)
    t_n_a = (cardiac_phase + ATRIAL_PHASE_OFFSET) % 1.0
    E_la = elastance_from_phase(t_n_a, params.la_emax, params.la_emin)
    E_ra = elastance_from_phase(t_n_a, params.ra_emax, params.ra_emin)

    # -----------------------------------------------------------------------
    # Compute pressures for every compartment
    # -----------------------------------------------------------------------
    # Venous tone: drug venoconstriction × baroreflex venous arm, applied as a
    # multiplier on systemic venous unstressed volume (V0). See _VENOUS_TONE_IDX.
    #   < 1  venoconstriction → lower V0 → higher venous P → ↑ preload/CO
    #   > 1  venodilation     → higher V0 → venous pooling → ↓ preload/CO
    vt = drugs.get("venous_tone_factor", 1.0)
    if baro is not None:
        vt *= baro.v0_vein_factor

    i = IDX
    P = np.zeros(len(comp))

    # Vascular compartments
    for idx in [i["aorta"], i["brachiocephalic"], i["upper_body_art"],
                i["upper_body_vein"], i["svc"],
                i["abdominal_aorta"], i["renal_art"], i["renal_vein"],
                i["splanchnic_art"], i["splanchnic_vein"],
                i["lower_body_art"],
                i["thigh_vein"], i["calf_vein"], i["foot_vein"], i["ivc"],
                i["pulmonary_art"], i["pulmonary_cap"], i["pulmonary_vein"],
                i["coronary"]]:
        c = comp[idx]
        v0 = c.unstressed_volume * vt if idx in _VENOUS_TONE_IDX else c.unstressed_volume
        # Venous stress relaxation (slow_dynamics.py) adds a slowly-varying
        # offset to unstressed volume: sustained distension lets the wall creep,
        # accommodating volume at lower pressure. Zero at rest and when slow
        # dynamics are disabled.
        if slow is not None:
            v0 += slow.v0_relax_ml[idx]
        P[idx] = _vascular_pressure(V[idx], v0, c.compliance, c.p_stiffen)

    # Cardiac chambers (time-varying elastance)
    P[i["left_ventricle"]]  = _cardiac_pressure(V[i["left_ventricle"]],  comp[i["left_ventricle"]].unstressed_volume,  E_lv)
    P[i["right_ventricle"]] = _cardiac_pressure(V[i["right_ventricle"]], comp[i["right_ventricle"]].unstressed_volume, E_rv)
    P[i["left_atrium"]]     = _cardiac_pressure(V[i["left_atrium"]],     comp[i["left_atrium"]].unstressed_volume,     E_la)
    P[i["right_atrium"]]    = _cardiac_pressure(V[i["right_atrium"]],    comp[i["right_atrium"]].unstressed_volume,    E_ra)

    # -----------------------------------------------------------------------
    # Tilt angle at current time  (computed first — needed for positional ITP)
    # -----------------------------------------------------------------------
    tilt = smooth_tilt_profile(
        t,
        params.tilt_start_deg, params.tilt_end_deg,
        params.tilt_onset_s, params.tilt_duration_s,
    )
    g = params.gravity

    # -----------------------------------------------------------------------
    # Intrathoracic pressure (ITP) — two additive components:
    #
    # 1. Respiratory ITP (oscillatory): cyclic pleural pressure from breathing.
    #    Applied only when ventilation_mode != 'none'.
    #
    # 2. Positional ITP (DC): abdominal viscera shift cranially in head-down
    #    tilt and compress the diaphragm, raising the pleural pressure baseline.
    #    This is the mechanism behind the ~+4 mmHg clinical CVP rise in
    #    Trendelenburg (Likhvantsev 2025) that transmural CVP alone cannot
    #    reproduce. Implemented via positional_itp_mmhg() in gravity.py.
    #
    # Combined effect on cross-boundary flows:
    #   Venous return:  Q_SVC/IVC → RA = (P_SVC/IVC − (P_RA_tm + ITP)) / R
    #     → ITP_resp negative (spontaneous insp.) → venous return ↑ ✓
    #     → ITP_resp positive (PPV insp.)          → venous return ↓ ✓
    #     → ITP_pos positive (Trendelenburg)       → slightly offsets
    #       hydrostatic venous-return benefit, matching clinical observation
    #       that Trendelenburg ΔCO/ΔSV is modest (+0.33 L/min, +8 mL) ✓
    #   Intra-thoracic flows: ITP cancels between both thoracic sides ✓
    #
    # Aorta is deliberately excluded from the ITP set — see note in the
    # spontaneous-breathing code path: including aorta causes unphysical
    # retrograde peripheral arterial flow when ITP is negative. Without
    # aorta, LV→aorta retains the ITP offset (LV thoracic, aorta not),
    # giving correct pulsus inspiratorius / PPV/SVV mechanics ✓
    # -----------------------------------------------------------------------
    itp_resp = (
        intrathoracic_pressure(
            t, params.ventilation_mode, params.resp_rate_bpm,
            params.peep_cmh2o, params.pip_cmh2o, params.ie_ratio,
        )
        if params.ventilation_mode != 'none' else 0.0
    )
    itp_pos   = positional_itp_mmhg(tilt)
    itp_total = itp_resp + itp_pos

    if itp_total != 0.0:
        for _ti in _THORACIC_IDX:
            P[_ti] += itp_total

    def hdp(idx_name: str) -> float:
        """Hydrostatic delta (mmHg) for this compartment at current tilt."""
        return hydrostatic_delta_mmhg(comp[IDX[idx_name]].height_m, tilt, g)

    # -----------------------------------------------------------------------
    # SVR scaling (baroreflex + drug)
    # -----------------------------------------------------------------------
    svr_factor = params.svr_scale * drugs.get("svr_factor", 1.0)
    if baro is not None:
        svr_factor *= baro.svr_factor
    if slow is not None:
        # Angiotensin II + AVP. Exactly 1.0 at rest, so this cannot shift
        # baseline haemodynamics; it engages only as arterial pressure falls
        # below the resting reference.
        svr_factor *= neurohumoral_svr_factor(slow)

    def R(idx_name: str, systemic_arterial: bool = False) -> float:
        r = comp[IDX[idx_name]].resistance
        return r * svr_factor if systemic_arterial else r

    # -----------------------------------------------------------------------
    # Postcapillary resistance — backlog item 18
    # -----------------------------------------------------------------------
    # The alpha-1 postcapillary effect does NOT act here. It shifts the pre/post
    # split WITHIN the exchange segment, which moves capillary pressure without
    # moving flow, and is applied in slow_dynamics.capillary_pressure_fraction().
    # It was briefly applied to the venous drainage resistance instead; that is the
    # wrong site (drainage is downstream of the venous compartment, so raising it
    # chokes venous return) and it is not applied to any resistance here now.
    #
    # The division of labour: `svr_factor` above scales the whole exchange segment
    # — the common arteriolar + venular rise — while `postcap_factor` carries only
    # the differential, that the venular response is steeper than the arterial one.
    def R_drain(idx_name: str) -> float:
        """Venous drainage resistance for an exchange bed.

        Reads `drain_resistance`, which is a separate field from `resistance` so
        that the exchange segment and the drainage path can be set independently
        (see the note on Compartment.drain_resistance).
        """
        return comp[IDX[idx_name]].drain_resistance

    # -----------------------------------------------------------------------
    # Flows (mL/s) — Q > 0 means forward flow
    # One-way valve: max(Q, 0) for cardiac valve positions
    # -----------------------------------------------------------------------

    # Systemic arterial tree
    # Hydrostatic correction: Q = (P_up - P_down + hdp(upstream) - hdp(downstream)) / R
    # Positive hdp(up) - hdp(down) when going downhill (increases flow); negative when uphill.
    # Conduit arteries carry no arteriolar resistance and are NOT drug-scaled; the
    # arteriolar resistance (and with it `svr_factor`) now lives on the artery→vein
    # exchange segment, which is where the arterioles physically are. See the
    # placement note in compartments.py.
    Q_ao_brachio  = (P[i["aorta"]] - P[i["brachiocephalic"]] + hdp("aorta") - hdp("brachiocephalic")) / R("brachiocephalic")
    Q_brachio_ub  = (P[i["brachiocephalic"]] - P[i["upper_body_art"]] + hdp("brachiocephalic") - hdp("upper_body_art")) / R("upper_body_art")
    Q_ub_art_vein = (P[i["upper_body_art"]] - P[i["upper_body_vein"]]) / R("upper_body_vein", True)
    # Every exchange bed now owns both its own numbers: `resistance` is its
    # arteriole + exchange segment, `drain_resistance` its outflow. (This one used
    # to read svc.resistance, leaving upper_body_vein.drain_resistance defaulting
    # to the 3.80 arteriolar value and looking like a drainage figure.)
    Q_ub_vein_svc = (P[i["upper_body_vein"]] - P[i["svc"]] + hdp("upper_body_vein") - hdp("svc")) / R_drain("upper_body_vein")

    Q_ao_abd      = (P[i["aorta"]] - P[i["abdominal_aorta"]] + hdp("aorta") - hdp("abdominal_aorta")) / R("abdominal_aorta")
    Q_abd_renal   = (P[i["abdominal_aorta"]] - P[i["renal_art"]]) / R("renal_art")
    Q_renal_vein  = (P[i["renal_art"]] - P[i["renal_vein"]]) / R("renal_vein", True)
    Q_abd_splanch = (P[i["abdominal_aorta"]] - P[i["splanchnic_art"]]) / R("splanchnic_art")
    Q_splanch_vein= (P[i["splanchnic_art"]] - P[i["splanchnic_vein"]]) / R("splanchnic_vein", True)
    Q_abd_lb      = (P[i["abdominal_aorta"]] - P[i["lower_body_art"]] + hdp("abdominal_aorta") - hdp("lower_body_art")) / R("lower_body_art")

    # Capillary inflow from lower body arteries to each venous segment (30/40/30% split).
    # The old single lower_body_vein used R=0.30 (outflow resistance) for the art→vein flow,
    # giving total arteriocapillary R_total=0.30. Split across three parallel branches:
    #   R_to_thigh = 0.30/0.30 = 1.00,  R_to_calf = 0.30/0.40 = 0.75,  R_to_foot = 0.30/0.30 = 1.00
    # Equivalent parallel resistance = 1/(0.30+0.40+0.30) * 0.30 = 0.30 ✓
    # Leg arteriolar + exchange resistances now live in the compartment table
    # (see the leg-vein block in compartments.py), so the patient SVR calibration
    # and the PAD factor can reach them. Drug-scaled like every other arteriolar
    # segment.
    Q_lb_art_thigh = (P[i["lower_body_art"]] - P[i["thigh_vein"]]) / R("thigh_vein", True)
    Q_lb_art_calf  = (P[i["lower_body_art"]] - P[i["calf_vein"]])  / R("calf_vein", True)
    Q_lb_art_foot  = (P[i["lower_body_art"]] - P[i["foot_vein"]])  / R("foot_vein", True)

    # Muscle pump: rhythmic calf compression drives venous return.
    # sin²(2πft) profile: always ≥ 0 (no suction phase), smooth, periodic.
    # pump_p = 0 when muscle_pump_pressure = 0 → identical to current model.
    pump_p = 0.0
    if params.muscle_pump_pressure > 0:
        pump_p = params.muscle_pump_pressure * np.sin(2 * np.pi * params.muscle_pump_freq_hz * t) ** 2

    # Venous drainage: foot→calf→thigh→ivc.
    # max(0,...) implements anatomical one-way venous valves — prevents retrograde flow
    # that would otherwise occur when hydrostatic gradient exceeds driving pressure.
    # Pump boost applied to foot→calf and calf→thigh (calf contraction zone).
    Q_foot_calf  = max(0.0, (P[i["foot_vein"]]  - P[i["calf_vein"]]  + hdp("foot_vein")  - hdp("calf_vein")  + pump_p) / R_drain("foot_vein"))
    Q_calf_thigh = max(0.0, (P[i["calf_vein"]]  - P[i["thigh_vein"]] + hdp("calf_vein")  - hdp("thigh_vein") + pump_p) / R_drain("calf_vein"))
    Q_thigh_ivc  = max(0.0, (P[i["thigh_vein"]] - P[i["ivc"]]        + hdp("thigh_vein") - hdp("ivc"))                  / R_drain("thigh_vein"))

    Q_renal_ivc   = (P[i["renal_vein"]]     - P[i["ivc"]]) / R_drain("renal_vein")
    Q_splanch_ivc = (P[i["splanchnic_vein"]] - P[i["ivc"]]) / R_drain("splanchnic_vein")

    # Right heart inflows — one-way valves prevent retrograde venous flow.
    # Without the max(0,...) guard, positive ITP (mechanical PPV) can raise
    # P_RA above P_SVC/IVC and drive blood backward through the great veins.
    # These junctions are NOT valves — see VENOATRIAL_R in compartments.py. The
    # max(0, ...) guard is retained deliberately: it substitutes for venous collapse,
    # which the great veins do not model (backlog item 11), and without it positive
    # ITP under PPV drives blood backward up the great veins without limit.
    Q_svc_ra = max(0.0, (P[i["svc"]] - P[i["right_atrium"]] + hdp("svc") - hdp("right_atrium")) / R_drain("svc"))
    Q_ivc_ra = max(0.0, (P[i["ivc"]] - P[i["right_atrium"]] + hdp("ivc") - hdp("right_atrium")) / R_drain("ivc"))

    # Tricuspid valve (RA → RV)
    Q_tricuspid = max(0.0, (P[i["right_atrium"]] - P[i["right_ventricle"]]) / comp[i["right_ventricle"]].resistance)
    # Pulmonic valve (RV → PA)
    Q_pulmonic  = max(0.0, (P[i["right_ventricle"]] - P[i["pulmonary_art"]]) / comp[i["pulmonary_art"]].resistance)

    # Pulmonary circulation
    Q_pa_cap    = (P[i["pulmonary_art"]] - P[i["pulmonary_cap"]]) / R("pulmonary_cap")
    Q_cap_pv    = (P[i["pulmonary_cap"]] - P[i["pulmonary_vein"]]) / R("pulmonary_vein")

    # Mitral valve (PV → LA → LV)
    # Pulmonary veins → LA: continuous, no valve. A wedge catheter reads LA pressure
    # precisely because of this.
    Q_pv_la     = max(0.0, (P[i["pulmonary_vein"]] - P[i["left_atrium"]]) / R_drain("pulmonary_vein"))
    Q_mitral    = max(0.0, (P[i["left_atrium"]] - P[i["left_ventricle"]]) / comp[i["left_ventricle"]].resistance)
    # Aortic valve (LV → aorta) — use valve resistance, not aortic outflow resistance
    Q_aortic    = max(0.0, (P[i["left_ventricle"]] - P[i["aorta"]]) / comp[i["left_ventricle"]].resistance)

    # Coronary (aorta → coronary → right atrium)
    Q_ao_cor    = (P[i["aorta"]] - P[i["coronary"]]) / R("coronary", True)
    Q_cor_ra    = (P[i["coronary"]] - P[i["right_atrium"]]) / R("right_atrium") * 0.1

    # -----------------------------------------------------------------------
    # dV/dt for each compartment
    # -----------------------------------------------------------------------
    dV = np.zeros(len(comp))

    dV[i["aorta"]]           = Q_aortic - Q_ao_brachio - Q_ao_abd - Q_ao_cor
    dV[i["brachiocephalic"]] = Q_ao_brachio - Q_brachio_ub
    dV[i["upper_body_art"]]  = Q_brachio_ub - Q_ub_art_vein
    dV[i["upper_body_vein"]] = Q_ub_art_vein - Q_ub_vein_svc
    dV[i["svc"]]             = Q_ub_vein_svc - Q_svc_ra
    dV[i["abdominal_aorta"]] = Q_ao_abd - Q_abd_renal - Q_abd_splanch - Q_abd_lb
    dV[i["renal_art"]]       = Q_abd_renal - Q_renal_vein
    dV[i["renal_vein"]]      = Q_renal_vein - Q_renal_ivc
    dV[i["splanchnic_art"]]  = Q_abd_splanch - Q_splanch_vein
    dV[i["splanchnic_vein"]] = Q_splanch_vein - Q_splanch_ivc
    dV[i["lower_body_art"]]  = Q_abd_lb - Q_lb_art_thigh - Q_lb_art_calf - Q_lb_art_foot
    dV[i["thigh_vein"]]      = Q_lb_art_thigh + Q_calf_thigh - Q_thigh_ivc
    dV[i["calf_vein"]]       = Q_lb_art_calf  + Q_foot_calf  - Q_calf_thigh
    dV[i["foot_vein"]]       = Q_lb_art_foot                 - Q_foot_calf
    dV[i["ivc"]]             = Q_thigh_ivc + Q_renal_ivc + Q_splanch_ivc - Q_ivc_ra
    dV[i["right_atrium"]]    = Q_svc_ra + Q_ivc_ra + Q_cor_ra - Q_tricuspid
    dV[i["right_ventricle"]] = Q_tricuspid - Q_pulmonic
    dV[i["pulmonary_art"]]   = Q_pulmonic - Q_pa_cap
    dV[i["pulmonary_cap"]]   = Q_pa_cap - Q_cap_pv
    dV[i["pulmonary_vein"]]  = Q_cap_pv - Q_pv_la
    dV[i["left_atrium"]]     = Q_pv_la - Q_mitral
    dV[i["left_ventricle"]]  = Q_mitral - Q_aortic
    dV[i["coronary"]]        = Q_ao_cor - Q_cor_ra

    # -----------------------------------------------------------------------
    # Hemorrhage / fluid bolus — net volume change to the circulation
    # -----------------------------------------------------------------------
    if params.hemorrhage_duration_s > 0:
        t_end = params.hemorrhage_start_s + params.hemorrhage_duration_s
        if params.hemorrhage_start_s <= t < t_end:
            hem_rate = params.hemorrhage_rate_mlmin / 60.0  # mL/s
            stressed = np.array([
                max(0.0, V[i[name]] - comp[i[name]].unstressed_volume)
                for name in VENOUS_RESERVOIR
            ])
            total_stressed = stressed.sum()
            if total_stressed > 1e-6:
                for name, s in zip(VENOUS_RESERVOIR, stressed):
                    dV[i[name]] -= hem_rate * (s / total_stressed)

    if params.fluid_bolus_duration_s > 0:
        t_end = params.fluid_bolus_start_s + params.fluid_bolus_duration_s
        if params.fluid_bolus_start_s <= t < t_end:
            dV[i["upper_body_vein"]] += params.fluid_bolus_ml / params.fluid_bolus_duration_s

    # Expose the pressures already computed above to the caller, without
    # recomputing them. Used by the slow-dynamics clock (slow_dynamics.py),
    # whose mechanisms need compartment pressures but run on a much coarser
    # step than this ODE. No cost when p_out is None.
    if p_out is not None:
        p_out[:] = P

    return dV


# ---------------------------------------------------------------------------
# PPV helper
# ---------------------------------------------------------------------------

def _compute_ppv(aortic_p: np.ndarray, dt: float, hr_bpm: float,
                 resp_rate_bpm: float) -> np.ndarray:
    """
    Compute pulse pressure variation (PPV, %) time series from the aortic
    pressure waveform.

        PPV = (PP_max − PP_min) / PP_mean × 100

    where PP_max and PP_min are the largest and smallest per-beat pulse
    pressures (SBP_i − DBP_i) within one respiratory cycle.

    Only meaningful under mechanical ventilation, but the function returns
    an array of the same length as aortic_p regardless of mode. Values near
    simulation start are unreliable (< 1 full resp cycle of data).
    """
    from scipy.signal import find_peaks as _fp

    n      = len(aortic_p)
    n_card = max(1, int(60.0 / hr_bpm / dt))
    n_resp = max(1, int(60.0 / resp_rate_bpm / dt))

    if n < 2 * n_resp:
        return np.zeros(n)

    # Detect systolic peaks: above median, separated by ≥ half cardiac cycle.
    peaks, _   = _fp(aortic_p, distance=n_card // 2,
                     height=float(np.median(aortic_p)))
    # Detect diastolic troughs (local minima in the waveform).
    troughs, _ = _fp(-aortic_p, distance=n_card // 2)

    if len(peaks) < 3 or len(troughs) < 3:
        return np.zeros(n)

    # Per-beat PP = SBP_i − DBP_i (the diastolic trough immediately preceding
    # each systolic peak).
    pp_idx, pp_vals = [], []
    for p in peaks:
        pre = troughs[troughs < p]
        if len(pre) == 0:
            continue
        pp_idx.append(int(p))
        pp_vals.append(float(aortic_p[p] - aortic_p[pre[-1]]))

    if len(pp_idx) < 3:
        return np.zeros(n)

    pp_idx  = np.asarray(pp_idx,  dtype=np.intp)
    pp_vals = np.asarray(pp_vals, dtype=float)

    # For each beat, scan the surrounding ±half-respiratory-cycle beats and
    # compute PPV = (PP_max − PP_min) / PP_mean.
    half = n_resp // 2
    ppv_beats = np.zeros(len(pp_idx))
    for j, pidx in enumerate(pp_idx):
        mask   = (pp_idx >= pidx - half) & (pp_idx <= pidx + half)
        pp_win = pp_vals[mask]
        if len(pp_win) < 2:
            continue
        pp_mean = float(pp_win.mean())
        if pp_mean <= 0:
            continue
        ppv_beats[j] = (pp_win.max() - pp_win.min()) / pp_mean * 100.0

    # Interpolate per-beat PPV to every time step; clamp to [0, 100].
    ppv_ts = np.interp(np.arange(n, dtype=float), pp_idx.astype(float), ppv_beats)
    return np.clip(ppv_ts, 0.0, 100.0)


# ---------------------------------------------------------------------------
# Public simulation runner
# ---------------------------------------------------------------------------

def run_simulation(
    params: SimParams,
    duration_s: float = 60.0,
    dt: float = 0.001,
    use_baroreflex: bool = True,
    output_every: int = 1,
    hires_windows: list[tuple[float, float]] | None = None,
) -> dict:
    """
    Integrate the ODE system and return time-series haemodynamic outputs.

    Returns
    -------
    dict with keys:
        t           : np.ndarray (s)
        aortic_p    : np.ndarray (mmHg) — instantaneous aortic pressure
        map         : np.ndarray (mmHg) — running 3-beat MAP approximation
        cvp         : np.ndarray (mmHg) — right atrial end-diastolic pressure
        la_pressure : np.ndarray (mmHg) — left atrial / PCWP proxy
        co          : np.ndarray (L/min) — cardiac output (LV volume decrease)
        hr          : np.ndarray (bpm)
        sv          : np.ndarray (mL)   — stroke volume
        dbp         : np.ndarray (mmHg) — diastolic aortic pressure (rolling min)
        sbp         : np.ndarray (mmHg) — systolic aortic pressure (rolling max)
        lvedp       : np.ndarray (mmHg) — LV end-diastolic pressure
        cpp         : np.ndarray (mmHg) — cerebral perfusion pressure
        cop         : np.ndarray (mmHg) — coronary perfusion pressure (DBP − LVEDP)
        buckberg    : np.ndarray        — Buckberg subendocardial viability ratio
        ppv         : np.ndarray (%)   — pulse pressure variation (mechanical vent only; zeros otherwise)
        volumes     : np.ndarray (mL, shape [n_steps, n_compartments])
    """
    from .perfusion import (cerebral_perfusion_pressure,
                            coronary_perfusion_pressure, buckberg_index)
    from .heart import LV_EMIN as _LV_EMIN

    comp = params.compartments
    V0   = np.array([c.init_volume for c in comp], dtype=float)

    baro: BaroreflexController | None = None
    if use_baroreflex and params.baroreflex_enabled:
        baro = BaroreflexController(dt=dt)

    # Slow-timescale dynamics (minutes to hours). Inert unless explicitly
    # enabled: when off, `slow_state` stays None, `_p_scratch` is never
    # allocated, and the integration loop below costs one boolean test per
    # step — behaviour is bit-for-bit identical to having no slow dynamics.
    slow_enabled = bool(getattr(params, "slow_dynamics_enabled", False))
    slow_state = init_slow_state(comp) if slow_enabled else None
    _p_scratch = np.zeros(len(comp)) if slow_enabled else None

    t_eval = np.arange(0.0, duration_s, dt)
    n = len(t_eval)

    # ---- OUTPUT DOWNSAMPLING (backlog item 33) --------------------------------
    # Storing every 1 ms sample costs 26 GB for a 24 h run, which does not fit in
    # memory. `output_every` stores one sample per block of that many steps.
    #
    # Each stored sample is the block MEAN, not every Nth value. That distinction
    # is load-bearing: heart rate is about 1.17 Hz, so decimating to 1 Hz would
    # ALIAS the cardiac cycle and put a beat-frequency artefact into every trend.
    # Averaging is decimation with the anti-aliasing filter built in, and it is
    # also what a trend over hours should show.
    #
    # output_every=1 is the identity and every stored value is bit-for-bit what it
    # was before this existed.
    if output_every < 1:
        raise ValueError(f"output_every must be >= 1, got {output_every}")
    n_out = (n + output_every - 1) // output_every
    _blk = np.zeros(n_out)                       # samples accumulated per block
    for _i in range(n):
        _blk[_i // output_every] += 1.0

    # ---- HIGH-RESOLUTION SLICES ----------------------------------------------
    # Downsampling destroys exactly the information this project has repeatedly
    # needed: numerical drift shows as a change in waveform MORPHOLOGY, and
    # "is this sampled mid-systole or end-systole" is invisible in a trend. Keep
    # full-dt windows alongside the trend. 30 s holds ~5 breaths and ~35 beats.
    _hires_ranges = []
    if hires_windows:
        for (a, b) in hires_windows:
            i0, i1 = max(0, int(a / dt)), min(n, int(b / dt))
            if i1 > i0:
                _hires_ranges.append((i0, i1))
    _hires_n = sum(i1 - i0 for i0, i1 in _hires_ranges)
    _hires_t = np.zeros(_hires_n)
    _hires_ao = np.zeros(_hires_n)
    _hires_cvp = np.zeros(_hires_n)
    _hires_vol = np.zeros((_hires_n, len(comp)))
    _hires_map = {}                              # step -> row in the hires arrays
    _row = 0
    for i0, i1 in _hires_ranges:
        for _i in range(i0, i1):
            _hires_map[_i] = _row
            _row += 1

    # Storage
    aortic_p    = np.zeros(n_out)
    cvp_ts      = np.zeros(n_out)
    la_p_ts     = np.zeros(n_out)
    co_ts       = np.zeros(n_out)
    hr_ts       = np.zeros(n_out)
    dbp_ts          = np.zeros(n_out)
    sbp_ts          = np.zeros(n_out)
    brachial_sbp_ts = np.zeros(n_out)
    brachial_dbp_ts = np.zeros(n_out)
    lvedp_ts    = np.zeros(n_out)
    cpp_ts      = np.zeros(n_out)
    cop_ts      = np.zeros(n_out)
    buckberg_ts = np.zeros(n_out)
    ankle_p_ts    = np.zeros(n_out)
    brachial_p_ts = np.zeros(n_out)
    volumes_ts  = np.zeros((n_out, len(comp)))

    # Slow-dynamics diagnostics. Allocated only when the mechanism is active, so
    # an ordinary run pays nothing for them and its result dict is unchanged.
    # Validation against the human haemorrhage literature is expressed in plasma
    # volume and haematocrit (Lister 1963 measures both), which blood volume
    # alone cannot supply once red cells are leaving with the bleed.
    if slow_enabled:
        plasma_vol_ts   = np.zeros(n_out)
        haematocrit_ts  = np.zeros(n_out)
        interstitial_ts = np.zeros(n_out)
        oncotic_ts      = np.zeros(n_out)

    # We step manually so baroreflex can update each step
    V = V0.copy()
    i = IDX

    # CVP: rolling minimum of RA pressure over 2 beats (end-diastolic trough).
    from collections import deque as _deque
    _cvp_win_len = max(100, int(2 * 60.0 / params.hr_bpm / dt))
    _cvp_win     = _deque([10.0] * _cvp_win_len, maxlen=_cvp_win_len)

    # DBP / SBP: rolling min / max of aortic and brachial pressure over 2 beats.
    _bp_win_len      = _cvp_win_len
    _dbp_win         = _deque([80.0]  * _bp_win_len, maxlen=_bp_win_len)
    _sbp_win         = _deque([120.0] * _bp_win_len, maxlen=_bp_win_len)
    _brachial_dbp_win = _deque([80.0]  * _bp_win_len, maxlen=_bp_win_len)
    _brachial_sbp_win = _deque([120.0] * _bp_win_len, maxlen=_bp_win_len)

    # CO / SV: LV volume decrease per step (avoids HR phase-mismatch bug).
    _prev_V_lv   = V[i["left_ventricle"]]
    _beat_ejected = 0.0
    _last_t_beat  = 0.0
    sv_ts         = np.zeros(n_out)
    _sv_current   = 70.0

    # HR / E_max from previous step (1-step lag) for consistent monitoring.
    _hr_monitor   = params.hr_bpm
    _emax_monitor = params.lv_emax
    # Continuously-integrated cardiac-cycle phase (cycles, wrapped to [0,1)).
    # _cardiac_phase drives the ODE's elastances (advanced using the HR seen
    # by _odes this step); _monitor_phase drives the 1-step-lagged E_ra/E_la
    # used for CVP/PCWP monitoring (advanced using _hr_monitor). Both replace
    # (t % T)/T, which is discontinuous whenever HR varies step-to-step.
    _cardiac_phase = 0.0
    _monitor_phase = 0.0

    for step, t in enumerate(t_eval):
        _oi = step // output_every       # output block index (see output_every above)
        c_ao = comp[i["aorta"]]
        c_ra = comp[i["right_atrium"]]
        c_la = comp[i["left_atrium"]]

        # Use E_ra/E_la from PREVIOUS step's monitor phase for consistent
        # pressure monitoring. (ODE will use the CURRENT baro state computed below.)
        t_n_a_monitor = (_monitor_phase + ATRIAL_PHASE_OFFSET) % 1.0
        E_ra_now = elastance_from_phase(t_n_a_monitor, params.ra_emax, params.ra_emin)
        E_la_now = elastance_from_phase(t_n_a_monitor, params.la_emax, params.la_emin)

        p_ao = _vascular_pressure(V[i["aorta"]], c_ao.unstressed_volume, c_ao.compliance)
        p_ra = _cardiac_pressure(V[i["right_atrium"]], c_ra.unstressed_volume, E_ra_now)
        p_la = _cardiac_pressure(V[i["left_atrium"]], c_la.unstressed_volume, E_la_now)

        # CO: measure from LV volume decrease (no elastance-timing dependency).
        curr_V_lv = V[i["left_ventricle"]]
        dV_ejected = max(0.0, _prev_V_lv - curr_V_lv)  # positive during ejection
        _beat_ejected += dV_ejected
        _prev_V_lv = curr_V_lv

        # CO (instantaneous rate): ejection rate * 60/1000 for L/min
        co_ts[_oi] += dV_ejected / dt * 60.0 / 1000.0

        # SV: sum ejected volume over one actual HR-based beat
        T_beat = 60.0 / _hr_monitor
        if t - _last_t_beat >= T_beat:
            _sv_current   = _beat_ejected
            _beat_ejected = 0.0
            _last_t_beat  = t
        sv_ts[_oi] += _sv_current

        # CVP: end-diastolic RA trough (pass to baroreflex too, not instantaneous p_ra)
        _cvp_win.append(p_ra)
        p_cvp_edi = min(_cvp_win)

        # Update baroreflex — updates hr_delta, svr_factor etc. for NEXT ODE step
        hr_eff = params.hr_bpm
        rsa_now = 0.0
        if baro is not None:
            baro.update(p_ao, 40.0, p_cvp_edi)
            hr_eff = max(30.0, min(180.0, params.hr_bpm + baro.hr_delta))
        if params.ventilation_mode != 'none':
            rsa_now = respiratory_sinus_arrhythmia(
                t, params.ventilation_mode, params.resp_rate_bpm, params.ie_ratio)
            hr_eff = max(30.0, min(180.0, hr_eff + rsa_now))

        # Carry forward updated HR for next step's monitoring
        _hr_monitor   = hr_eff
        _emax_monitor = params.lv_emax * (baro.emax_factor if baro is not None else 1.0)

        # HR driving _odes's elastance this step (hr_bpm * drug hr_factor,
        # then baroreflex, then RSA — same formula _odes used internally
        # before this refactor moved phase-integration out to the caller).
        hr_now = params.hr_bpm * _drug_factors_at(params, t).get("hr_factor", 1.0)
        if baro is not None:
            hr_now = max(30.0, min(180.0, hr_now + baro.hr_delta))
        if params.ventilation_mode != 'none':
            hr_now = max(30.0, min(180.0, hr_now + rsa_now))

        # DBP / SBP tracking (rolling min / max)
        _dbp_win.append(p_ao); _sbp_win.append(p_ao)
        p_dbp = min(_dbp_win)
        p_sbp = max(_sbp_win)

        # LVEDP: LV diastolic elastance × stressed volume (same method as CVP)
        lv_v0  = comp[i["left_ventricle"]].unstressed_volume
        p_lvedp = max(0.0, params.lv_emin * (V[i["left_ventricle"]] - lv_v0))

        # Current tilt for perfusion calculations
        tilt_now = smooth_tilt_profile(
            t, params.tilt_start_deg, params.tilt_end_deg,
            params.tilt_onset_s, params.tilt_duration_s,
        )

        # Ankle / brachial pressures: compartment transmural pressure,
        # hydrostatically referenced to heart level (same convention as
        # map_at_brain in perfusion.py — P_site = P_transmural − hdp(site)).
        # lower_body_art (height_m=-0.50) is the model's only lower-limb
        # arterial compartment; brachiocephalic (height_m=0.12) is the
        # proximal-arm conduit artery used as the brachial-cuff proxy.
        # See docs/avatar caveats doc for limitations of this mapping.
        c_lba = comp[i["lower_body_art"]]
        c_bc  = comp[i["brachiocephalic"]]
        p_lba = _vascular_pressure(V[i["lower_body_art"]], c_lba.unstressed_volume, c_lba.compliance)
        p_bc  = _vascular_pressure(V[i["brachiocephalic"]], c_bc.unstressed_volume, c_bc.compliance)
        _p_ankle = p_lba - hydrostatic_delta_mmhg(c_lba.height_m, tilt_now, params.gravity)
        _p_brach = p_bc  - hydrostatic_delta_mmhg(c_bc.height_m,  tilt_now, params.gravity)
        ankle_p_ts[_oi]    += _p_ankle
        brachial_p_ts[_oi] += _p_brach
        _brachial_dbp_win.append(_p_brach)
        _brachial_sbp_win.append(_p_brach)
        brachial_sbp_ts[_oi] += max(_brachial_sbp_win)
        brachial_dbp_ts[_oi] += min(_brachial_dbp_win)

        # Positional ITP offset for CVP and LA-pressure reporting.
        # The baroreflex uses transmural CVP (p_cvp_edi) — wall-stretch drives
        # the reflex, not the absolute lumen pressure. Reported CVP is absolute
        # (transmural + positional ITP), matching what a CVC catheter reads.
        # Respiratory ITP is NOT added here: clinical CVP is read at end-
        # expiration when respiratory ITP ≈ 0 (spontaneous) or PEEP baseline
        # (mechanical); the current transmural CVP already approximates this.
        itp_pos_now = positional_itp_mmhg(tilt_now)

        aortic_p[_oi]    += p_ao
        cvp_ts[_oi]      += p_cvp_edi + itp_pos_now
        la_p_ts[_oi]     += p_la + itp_pos_now
        hr_ts[_oi]       += hr_eff
        dbp_ts[_oi]      += p_dbp
        sbp_ts[_oi]      += p_sbp
        lvedp_ts[_oi]    += p_lvedp
        cpp_ts[_oi]      += cerebral_perfusion_pressure(p_ao, tilt_now, params.gravity)
        cop_ts[_oi]      += coronary_perfusion_pressure(p_dbp, p_lvedp)
        buckberg_ts[_oi] += buckberg_index(p_dbp, p_lvedp, hr_eff, p_sbp)
        volumes_ts[_oi]  += V

        # Full-dt capture inside the requested windows (backlog item 33).
        _hr_row = _hires_map.get(step)
        if _hr_row is not None:
            _hires_t[_hr_row] = t
            _hires_ao[_hr_row] = p_ao
            _hires_cvp[_hr_row] = p_cvp_edi + itp_pos_now
            _hires_vol[_hr_row] = V

        if slow_enabled:
            _rcv = slow_state.red_cell_volume_ml
            if _rcv <= 0.0:
                # Before SETTLE_S the slow reference has not been captured and
                # red cell volume is still zero. Emit NaN rather than a number
                # that looks plausible (plasma volume would read as whole blood
                # volume, haematocrit as 0).
                plasma_vol_ts[_oi]   += np.nan
                haematocrit_ts[_oi]  += np.nan
                interstitial_ts[_oi] += np.nan
                oncotic_ts[_oi]      += np.nan
            else:
                _bv = V.sum()
                _pv = max(_bv - _rcv, 1.0)
                plasma_vol_ts[_oi]   += _pv
                haematocrit_ts[_oi]  += _rcv / max(_bv, 1.0)
                interstitial_ts[_oi] += slow_state.interstitial_volume_ml
                oncotic_ts[_oi]      += oncotic_pressure_mmhg(
                    slow_state.plasma_protein_g, _pv)

        # Euler step. When slow dynamics are active, ask _odes to hand back the
        # compartment pressures it already computed (no recomputation), then
        # advance the slow state on its own coarse clock — update_slow_state()
        # returns immediately unless SLOW_DT of simulated time has elapsed.
        dV = _odes(t, V, params, baro, _cardiac_phase, _p_scratch, slow_state)
        V  = V + dV * dt

        if slow_enabled:
            # Transcapillary flux is returned as a volume change rather than
            # folded into _odes: it is a slow-clock quantity (mL moved over
            # SLOW_DT), not a rate the 1 ms integrator should see.
            dV_slow = update_slow_state(
                slow_state, t, V, _p_scratch, params, baro,
                postcap_factor=_drug_factors_at(params, t).get("postcap_factor", 1.0))
            if dV_slow is not None:
                V = V + dV_slow

        # Advance integrated cardiac phases for the next step.
        _cardiac_phase = (_cardiac_phase + hr_now / 60.0 * dt) % 1.0
        _monitor_phase = (_monitor_phase + _hr_monitor / 60.0 * dt) % 1.0

        # Guard: volumes can't go negative; replace NaN/inf from overflow
        V = np.maximum(V, 0.0)
        if not np.all(np.isfinite(V)):
            V = np.where(np.isfinite(V), V, np.array([c.init_volume for c in comp]))

    # Smooth MAP and CO over ~3 beats to remove pulsatility.
    #
    # Edge handling matters. np.convolve(..., mode="same") ZERO-pads beyond the
    # array ends, so the first and last ~beat_win/2 samples are dragged toward
    # zero — the final sample is roughly halved (e.g. MAP reading 46 mmHg where
    # aortic_p is 84). Every downstream mean that includes the tail is then
    # biased low: `last_half()` over a 40 s run averages through ~1.5 s of
    # corrupted signal and under-reports MAP/CO by roughly 2 %.
    #
    # Replicating the edge values instead keeps the smoothed series unbiased at
    # both ends, which is also the physically sensible assumption (the signal
    # continues at its boundary value rather than dropping to zero).
    # ---- normalise the block accumulators to means -----------------------------
    # Every series above was accumulated with += over its block; divide to get the
    # mean. With output_every=1 every block holds one sample and this is a no-op,
    # which is what makes that case bit-for-bit identical to the old behaviour.
    for _arr in (aortic_p, cvp_ts, la_p_ts, co_ts, hr_ts, sv_ts, dbp_ts, sbp_ts,
                 brachial_sbp_ts, brachial_dbp_ts, lvedp_ts, cpp_ts, cop_ts,
                 buckberg_ts, ankle_p_ts, brachial_p_ts):
        _arr /= _blk
    volumes_ts /= _blk[:, None]
    if slow_enabled:
        for _arr in (plasma_vol_ts, haematocrit_ts, interstitial_ts, oncotic_ts):
            _arr /= _blk

    # Output timebase: the CENTRE of each block, not its leading edge.
    t_out = (np.arange(n_out) + 0.5 * (_blk - 1.0)) * dt * 1.0
    t_out = np.array([(i * output_every + 0.5 * (_blk[i] - 1.0)) * dt
                      for i in range(n_out)])

    # The 3-second smoothing window is in OUTPUT samples, not raw steps.
    beat_win = max(1, int(3.0 / (dt * output_every)))
    map_ts = _smooth_edges(aortic_p, beat_win)
    co_ts  = _smooth_edges(co_ts,    beat_win)

    # PPV: only computed for mechanical ventilation (requires positive-pressure
    # ITP cycles to modulate venous return). Returns a time-series in percent.
    ppv_ts = (
        _compute_ppv(aortic_p, dt, params.hr_bpm, params.resp_rate_bpm)
        if params.ventilation_mode == 'mechanical'
        else np.zeros(n)
    )

    slow_out = {} if not slow_enabled else {
        "plasma_volume":       plasma_vol_ts,
        "haematocrit":         haematocrit_ts,
        "interstitial_volume": interstitial_ts,
        "oncotic_pressure":    oncotic_ts,
    }

    return {
        **slow_out,
        "t":           t_out,
        "aortic_p":    aortic_p,
        "map":         map_ts,
        "cvp":         cvp_ts,
        "la_pressure": la_p_ts,
        "co":          co_ts,
        "hr":          hr_ts,
        "sv":          sv_ts,
        "dbp":         dbp_ts,
        "sbp":         sbp_ts,
        "lvedp":       lvedp_ts,
        "cpp":         _smooth_edges(cpp_ts,      beat_win),
        "cop":         _smooth_edges(cop_ts,      beat_win),
        "buckberg":    _smooth_edges(buckberg_ts, beat_win),
        "ankle_p":      ankle_p_ts,
        "brachial_p":   brachial_p_ts,
        "brachial_sbp": brachial_sbp_ts,
        "brachial_dbp": brachial_dbp_ts,
        "ppv":         ppv_ts,
        "volumes":     volumes_ts,
        # Full-dt slices, empty unless hires_windows was given. See item 33: a
        # trend cannot show waveform morphology, and morphology is how numerical
        # drift and mid-systole/end-systole sampling errors become visible.
        "hires": {
            "t":        _hires_t,
            "aortic_p": _hires_ao,
            "cvp":      _hires_cvp,
            "volumes":  _hires_vol,
            "windows":  [(i0 * dt, i1 * dt) for i0, i1 in _hires_ranges],
        },
    }
