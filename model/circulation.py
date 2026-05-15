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
    elastance, frank_starling_emax,
    LV_EMAX, LV_EMIN, RV_EMAX, RV_EMIN,
    RA_EMAX, RA_EMIN, LA_EMAX, LA_EMIN,
    ATRIAL_PHASE_OFFSET,
)
from .gravity import hydrostatic_delta_mmhg, GravityEnvironment, smooth_tilt_profile
from .baroreflex import BaroreflexController
from .pharmacology import combined_drug_factors, NEUTRAL_FACTORS


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


# ---------------------------------------------------------------------------
# Pressure helpers
# ---------------------------------------------------------------------------

def _vascular_pressure(vol: float, v0: float, compliance: float) -> float:
    return (vol - v0) / compliance


def _cardiac_pressure(vol: float, v0: float, e: float) -> float:
    return max(0.0, e * (vol - v0))


# ---------------------------------------------------------------------------
# Main ODE function
# ---------------------------------------------------------------------------

def _odes(t: float, V: np.ndarray, params: SimParams, baro: BaroreflexController | None):
    """
    Compute dV/dt for the 23-compartment system.

    Parameters
    ----------
    t      : time (s)
    V      : state vector, volumes (mL)
    params : SimParams
    baro   : BaroreflexController (or None)
    """
    comp  = params.compartments
    drugs = params.drug_factors

    # -----------------------------------------------------------------------
    # Effective heart rate (baroreflex delta + drug factor)
    # -----------------------------------------------------------------------
    hr = params.hr_bpm * drugs.get("hr_factor", 1.0)
    if baro is not None:
        hr = max(30.0, min(180.0, hr + baro.hr_delta))

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
    # Instantaneous elastances
    # -----------------------------------------------------------------------
    T = 60.0 / hr
    E_lv = elastance(t, hr, lv_emax_eff, params.lv_emin)
    E_rv = elastance(t, hr, rv_emax_eff, params.rv_emin)

    # Atria fire ~60% of cycle before ventricles (offset in phase)
    t_atrial = t + ATRIAL_PHASE_OFFSET * T
    E_la = elastance(t_atrial, hr, params.la_emax, params.la_emin)
    E_ra = elastance(t_atrial, hr, params.ra_emax, params.ra_emin)

    # -----------------------------------------------------------------------
    # Compute pressures for every compartment
    # -----------------------------------------------------------------------
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
        P[idx] = _vascular_pressure(V[idx], c.unstressed_volume, c.compliance)

    # Cardiac chambers (time-varying elastance)
    P[i["left_ventricle"]]  = _cardiac_pressure(V[i["left_ventricle"]],  comp[i["left_ventricle"]].unstressed_volume,  E_lv)
    P[i["right_ventricle"]] = _cardiac_pressure(V[i["right_ventricle"]], comp[i["right_ventricle"]].unstressed_volume, E_rv)
    P[i["left_atrium"]]     = _cardiac_pressure(V[i["left_atrium"]],     comp[i["left_atrium"]].unstressed_volume,     E_la)
    P[i["right_atrium"]]    = _cardiac_pressure(V[i["right_atrium"]],    comp[i["right_atrium"]].unstressed_volume,    E_ra)

    # -----------------------------------------------------------------------
    # Tilt angle at current time
    # -----------------------------------------------------------------------
    tilt = smooth_tilt_profile(
        t,
        params.tilt_start_deg, params.tilt_end_deg,
        params.tilt_onset_s, params.tilt_duration_s,
    )
    g = params.gravity

    def hdp(idx_name: str) -> float:
        """Hydrostatic delta (mmHg) for this compartment at current tilt."""
        return hydrostatic_delta_mmhg(comp[IDX[idx_name]].height_m, tilt, g)

    # -----------------------------------------------------------------------
    # SVR scaling (baroreflex + drug)
    # -----------------------------------------------------------------------
    svr_factor = params.svr_scale * drugs.get("svr_factor", 1.0)
    if baro is not None:
        svr_factor *= baro.svr_factor

    def R(idx_name: str, systemic_arterial: bool = False) -> float:
        r = comp[IDX[idx_name]].resistance
        return r * svr_factor if systemic_arterial else r

    # Venous tone (unstressed volume modulation via compliance proxy)
    vt = drugs.get("venous_tone_factor", 1.0)
    if baro is not None:
        vt *= baro.v0_vein_factor

    # -----------------------------------------------------------------------
    # Flows (mL/s) — Q > 0 means forward flow
    # One-way valve: max(Q, 0) for cardiac valve positions
    # -----------------------------------------------------------------------

    # Systemic arterial tree
    # Hydrostatic correction: Q = (P_up - P_down + hdp(upstream) - hdp(downstream)) / R
    # Positive hdp(up) - hdp(down) when going downhill (increases flow); negative when uphill.
    Q_ao_brachio  = (P[i["aorta"]] - P[i["brachiocephalic"]] + hdp("aorta") - hdp("brachiocephalic")) / R("brachiocephalic", True)
    Q_brachio_ub  = (P[i["brachiocephalic"]] - P[i["upper_body_art"]] + hdp("brachiocephalic") - hdp("upper_body_art")) / R("upper_body_art", True)
    Q_ub_art_vein = (P[i["upper_body_art"]] - P[i["upper_body_vein"]]) / R("upper_body_vein")
    Q_ub_vein_svc = (P[i["upper_body_vein"]] - P[i["svc"]] + hdp("upper_body_vein") - hdp("svc")) / R("svc")

    Q_ao_abd      = (P[i["aorta"]] - P[i["abdominal_aorta"]] + hdp("aorta") - hdp("abdominal_aorta")) / R("abdominal_aorta", True)
    Q_abd_renal   = (P[i["abdominal_aorta"]] - P[i["renal_art"]]) / R("renal_art", True)
    Q_renal_vein  = (P[i["renal_art"]] - P[i["renal_vein"]]) / R("renal_vein")
    Q_abd_splanch = (P[i["abdominal_aorta"]] - P[i["splanchnic_art"]]) / R("splanchnic_art", True)
    Q_splanch_vein= (P[i["splanchnic_art"]] - P[i["splanchnic_vein"]]) / R("splanchnic_vein")
    Q_abd_lb      = (P[i["abdominal_aorta"]] - P[i["lower_body_art"]] + hdp("abdominal_aorta") - hdp("lower_body_art")) / R("lower_body_art", True)

    # Capillary inflow from lower body arteries to each venous segment (30/40/30% split).
    # The old single lower_body_vein used R=0.30 (outflow resistance) for the art→vein flow,
    # giving total arteriocapillary R_total=0.30. Split across three parallel branches:
    #   R_to_thigh = 0.30/0.30 = 1.00,  R_to_calf = 0.30/0.40 = 0.75,  R_to_foot = 0.30/0.30 = 1.00
    # Equivalent parallel resistance = 1/(0.30+0.40+0.30) * 0.30 = 0.30 ✓
    R_lb_cap_total = 0.30   # mmHg·s/mL — original arteriocapillary resistance
    R_lb_to_thigh  = R_lb_cap_total / 0.30
    R_lb_to_calf   = R_lb_cap_total / 0.40
    R_lb_to_foot   = R_lb_cap_total / 0.30
    Q_lb_art_thigh = (P[i["lower_body_art"]] - P[i["thigh_vein"]]) / R_lb_to_thigh
    Q_lb_art_calf  = (P[i["lower_body_art"]] - P[i["calf_vein"]])  / R_lb_to_calf
    Q_lb_art_foot  = (P[i["lower_body_art"]] - P[i["foot_vein"]])  / R_lb_to_foot

    # Venous drainage: foot→calf→thigh→ivc with hydrostatic corrections.
    # Each segment's outflow resistance is stored on that compartment.
    Q_foot_calf  = (P[i["foot_vein"]]  - P[i["calf_vein"]]  + hdp("foot_vein")  - hdp("calf_vein"))  / R("foot_vein")
    Q_calf_thigh = (P[i["calf_vein"]]  - P[i["thigh_vein"]] + hdp("calf_vein")  - hdp("thigh_vein")) / R("calf_vein")
    Q_thigh_ivc  = (P[i["thigh_vein"]] - P[i["ivc"]]        + hdp("thigh_vein") - hdp("ivc"))        / R("thigh_vein")

    Q_renal_ivc   = (P[i["renal_vein"]]     - P[i["ivc"]]) / R("renal_vein")
    Q_splanch_ivc = (P[i["splanchnic_vein"]] - P[i["ivc"]]) / R("splanchnic_vein")

    # Right heart inflows
    Q_svc_ra = (P[i["svc"]] - P[i["right_atrium"]] + hdp("svc") - hdp("right_atrium")) / R("right_atrium")
    Q_ivc_ra = (P[i["ivc"]] - P[i["right_atrium"]] + hdp("ivc") - hdp("right_atrium")) / R("right_atrium")

    # Tricuspid valve (RA → RV)
    Q_tricuspid = max(0.0, (P[i["right_atrium"]] - P[i["right_ventricle"]]) / comp[i["right_ventricle"]].resistance)
    # Pulmonic valve (RV → PA)
    Q_pulmonic  = max(0.0, (P[i["right_ventricle"]] - P[i["pulmonary_art"]]) / comp[i["pulmonary_art"]].resistance)

    # Pulmonary circulation
    Q_pa_cap    = (P[i["pulmonary_art"]] - P[i["pulmonary_cap"]]) / R("pulmonary_cap")
    Q_cap_pv    = (P[i["pulmonary_cap"]] - P[i["pulmonary_vein"]]) / R("pulmonary_vein")

    # Mitral valve (PV → LA → LV)
    Q_pv_la     = max(0.0, (P[i["pulmonary_vein"]] - P[i["left_atrium"]]) / comp[i["left_atrium"]].resistance)
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

    return dV


# ---------------------------------------------------------------------------
# Public simulation runner
# ---------------------------------------------------------------------------

def run_simulation(
    params: SimParams,
    duration_s: float = 60.0,
    dt: float = 0.001,
    use_baroreflex: bool = True,
) -> dict:
    """
    Integrate the ODE system and return time-series haemodynamic outputs.

    Returns
    -------
    dict with keys:
        t           : np.ndarray (s)
        aortic_p    : np.ndarray (mmHg) — instantaneous aortic pressure
        map         : np.ndarray (mmHg) — running 3-beat MAP approximation
        cvp         : np.ndarray (mmHg) — right atrial pressure
        la_pressure : np.ndarray (mmHg) — left atrial / PCWP proxy
        co          : np.ndarray (L/min) — aortic flow (cardiac output)
        hr          : np.ndarray (bpm)
        sv          : np.ndarray (mL)   — stroke volume
        volumes     : np.ndarray (mL, shape [n_steps, n_compartments])
    """
    comp = params.compartments
    V0   = np.array([c.init_volume for c in comp], dtype=float)

    baro: BaroreflexController | None = None
    if use_baroreflex and params.baroreflex_enabled:
        baro = BaroreflexController(dt=dt)

    t_eval = np.arange(0.0, duration_s, dt)
    n = len(t_eval)

    # Storage
    aortic_p    = np.zeros(n)
    cvp_ts      = np.zeros(n)
    la_p_ts     = np.zeros(n)
    co_ts       = np.zeros(n)
    hr_ts       = np.zeros(n)
    volumes_ts  = np.zeros((n, len(comp)))

    # We step manually so baroreflex can update each step
    V = V0.copy()
    i = IDX

    # Stroke volume tracking (from aortic flow integration per beat)
    _beat_flow   = 0.0
    _last_t_beat = 0.0
    sv_ts        = np.zeros(n)
    _sv_current  = 70.0   # initial guess

    for step, t in enumerate(t_eval):
        # Record
        c_ao = comp[i["aorta"]]
        c_ra = comp[i["right_atrium"]]
        c_la = comp[i["left_atrium"]]
        c_lv = comp[i["left_ventricle"]]

        E_lv_now = elastance(t, params.hr_bpm, params.lv_emax, params.lv_emin)
        E_la_now = elastance(t + ATRIAL_PHASE_OFFSET * 60.0 / params.hr_bpm,
                             params.hr_bpm, params.la_emax, params.la_emin)
        E_ra_now = elastance(t + ATRIAL_PHASE_OFFSET * 60.0 / params.hr_bpm,
                             params.hr_bpm, params.ra_emax, params.ra_emin)

        p_ao = _vascular_pressure(V[i["aorta"]], c_ao.unstressed_volume, c_ao.compliance)
        p_ra = _cardiac_pressure(V[i["right_atrium"]], c_ra.unstressed_volume, E_ra_now)
        p_la = _cardiac_pressure(V[i["left_atrium"]], c_la.unstressed_volume, E_la_now)
        p_lv = _cardiac_pressure(V[i["left_ventricle"]], c_lv.unstressed_volume, E_lv_now)

        # Aortic valve flow (uses LV valve resistance, same as _odes)
        q_av = max(0.0, (p_lv - p_ao) / c_lv.resistance)
        _beat_flow += q_av * dt
        # Report instantaneous CO as 3-beat rolling average (smoothed below)
        co_ts[step] = q_av * 60.0 / 1000.0   # mL/s → L/min (instantaneous)

        # Stroke volume: integrate over one nominal cardiac cycle
        T_beat = 60.0 / params.hr_bpm
        if t - _last_t_beat >= T_beat:
            _sv_current  = _beat_flow
            _beat_flow   = 0.0
            _last_t_beat = t
        sv_ts[step] = _sv_current

        hr_eff = params.hr_bpm
        if baro is not None:
            # Pass beat-averaged MAP (aortic pressure) and RA pressure as CVP.
            # PP not yet wired; baroreflex buffers handle averaging internally.
            pp_approx = 40.0   # placeholder — set to setpoint so PP error = 0
            baro.update(p_ao, pp_approx, p_ra)
            hr_eff = max(30.0, min(180.0, params.hr_bpm + baro.hr_delta))

        aortic_p[step]   = p_ao
        cvp_ts[step]     = p_ra
        la_p_ts[step]    = p_la
        hr_ts[step]      = hr_eff
        volumes_ts[step] = V.copy()

        # Euler step
        dV = _odes(t, V, params, baro)
        V  = V + dV * dt

        # Guard: volumes can't go negative; replace NaN/inf from overflow
        V = np.maximum(V, 0.0)
        if not np.all(np.isfinite(V)):
            V = np.where(np.isfinite(V), V, np.array([c.init_volume for c in comp]))

    # Smooth MAP and CO over ~3 beats to remove pulsatility
    beat_win = max(1, int(3.0 / dt))
    kernel   = np.ones(beat_win) / beat_win
    map_ts = np.convolve(aortic_p, kernel, mode="same")
    co_ts  = np.convolve(co_ts,    kernel, mode="same")

    return {
        "t":           t_eval,
        "aortic_p":    aortic_p,
        "map":         map_ts,
        "cvp":         cvp_ts,
        "la_pressure": la_p_ts,
        "co":          co_ts,
        "hr":          hr_ts,
        "sv":          sv_ts,
        "volumes":     volumes_ts,
    }
