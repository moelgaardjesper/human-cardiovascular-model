"""
REST API routes for the vascular model simulator.

Endpoints
---------
GET  /                    → serve frontend/index.html
GET  /api/defaults        → default parameter set
POST /api/simulate        → run simulation, return time-series JSON
POST /api/estimate        → fit parameters to clinical observations
"""

import numpy as np
from flask import Blueprint, jsonify, request, send_from_directory, current_app

from model.circulation import SimParams, run_simulation, BODY_REGIONS
from model.compartments import default_compartments, IDX
from model.gravity import GravityEnvironment
from model.pharmacology import combined_drug_factors, NEUTRAL_FACTORS
from model.patient import build_patient_params

bp = Blueprint("api", __name__)


# ---------------------------------------------------------------------------
# Serve frontend
# ---------------------------------------------------------------------------

@bp.route("/")
def index():
    return send_from_directory(current_app.static_folder, "index.html")


# ---------------------------------------------------------------------------
# GET /api/defaults
# ---------------------------------------------------------------------------

@bp.route("/api/defaults", methods=["GET"])
def get_defaults():
    return jsonify({
        "patient": {
            "height_cm": 175,
            "weight_kg": 75,
            "map_mmhg": None,
            "hr_bpm": 70,
            "cardiac_output_lpm": None,
            "abi": None,
            "cvp_mmhg": None,
            "pcwp_mmhg": None,
            "pap_mean_mmhg": None,
        },
        "scenario": {
            "tilt_start_deg": 0,
            "tilt_end_deg": 0,
            "tilt_onset_s": 5,
            "tilt_duration_s": 5,
            "gravity": "earth",
            "drugs": {},
        },
        "simulation": {
            "duration_s": 60,
            "baroreflex_enabled": True,
        },
    })


# ---------------------------------------------------------------------------
# POST /api/simulate
# ---------------------------------------------------------------------------

@bp.route("/api/simulate", methods=["POST"])
def simulate():
    body = request.get_json(force=True)

    patient  = body.get("patient", {})
    scenario = body.get("scenario", {})
    sim_cfg  = body.get("simulation", {})

    # --- Patient parameters ---
    height_cm = float(patient.get("height_cm", 175))
    weight_kg = float(patient.get("weight_kg", 75))
    map_in    = _opt_float(patient.get("map_mmhg"))
    hr_in     = float(patient.get("hr_bpm", 70))
    co_in     = _opt_float(patient.get("cardiac_output_lpm"))
    abi_in    = _opt_float(patient.get("abi"))
    cvp_in    = _opt_float(patient.get("cvp_mmhg"))
    pcwp_in   = _opt_float(patient.get("pcwp_mmhg"))
    pap_in    = _opt_float(patient.get("pap_mean_mmhg"))

    compartments, cardiac = build_patient_params(
        height_cm, weight_kg,
        map_mmhg=map_in,
        hr_bpm=hr_in,
        cardiac_output_lpm=co_in,
        abi=abi_in,
        cvp_mmhg=cvp_in,
        pcwp_mmhg=pcwp_in,
        pap_mean_mmhg=pap_in,
    )

    # --- Simulation parameters ---
    params = SimParams(compartments=compartments)
    params.hr_bpm = hr_in

    # Apply cardiac scaling from patient.py
    from model.heart import LV_EMAX, RV_EMAX
    params.lv_emax = LV_EMAX * cardiac.get("lv_emax_factor", 1.0)
    params.rv_emax = RV_EMAX * cardiac.get("rv_emax_factor", 1.0)

    # --- Scenario ---
    gravity_map = {
        "earth":       GravityEnvironment.EARTH,
        "mars":        GravityEnvironment.MARS,
        "moon":        GravityEnvironment.MOON,
        "microgravity": GravityEnvironment.MICROGRAVITY,
    }
    params.gravity         = gravity_map.get(scenario.get("gravity", "earth"), GravityEnvironment.EARTH)
    params.tilt_start_deg       = float(scenario.get("tilt_start_deg", 0))
    params.tilt_end_deg         = float(scenario.get("tilt_end_deg", 0))
    params.tilt_onset_s         = float(scenario.get("tilt_onset_s", 5))
    params.tilt_duration_s      = float(scenario.get("tilt_duration_s", 5))
    params.muscle_pump_pressure = float(scenario.get("muscle_pump_pressure", 0))
    params.muscle_pump_freq_hz  = float(scenario.get("muscle_pump_freq_hz", 0.5))
    params.ventilation_mode     = str(scenario.get("ventilation_mode", "none"))
    params.resp_rate_bpm        = float(scenario.get("resp_rate_bpm", 14.0))
    params.peep_cmh2o           = float(scenario.get("peep_cmh2o", 5.0))
    params.pip_cmh2o            = float(scenario.get("pip_cmh2o", 20.0))
    params.ie_ratio             = float(scenario.get("ie_ratio", 0.33))

    drugs = scenario.get("drugs", {})
    if drugs:
        params.drug_factors = combined_drug_factors(drugs)

    # --- Run ---
    duration_s = min(float(sim_cfg.get("duration_s", 60)), 300)
    baro       = bool(sim_cfg.get("baroreflex_enabled", True))
    dt         = 0.001   # 1 ms fixed step (required for stability)

    result = run_simulation(params, duration_s=duration_s, dt=dt, use_baroreflex=baro)

    # --- Downsample to ~20 Hz for transfer ---
    step = max(1, int(0.05 / dt))
    idx  = slice(None, None, step)
    h    = len(result["map"]) // 2   # second half for summary stats

    def _round(arr: np.ndarray, decimals: int = 2) -> list:
        return [round(float(v), decimals) for v in arr[idx]]

    def _mean(key: str) -> float:
        return round(float(np.mean(result[key][h:])), 2)

    # --- Body-region fluid distribution (% change from sim-start volume) ---
    volumes = result["volumes"]
    region_cols = {region: [IDX[name] for name in names] for region, names in BODY_REGIONS.items()}
    baseline_regions = {region: float(volumes[0, cols].sum()) for region, cols in region_cols.items()}
    region_means = {region: float(volumes[h:, cols].sum(axis=1).mean()) for region, cols in region_cols.items()}
    regions_pct = {
        region: round(100.0 * (region_means[region] / baseline_regions[region] - 1.0), 1)
        for region in BODY_REGIONS
    }

    return jsonify({
        "t":           _round(result["t"], 3),
        "aortic_p":    _round(result["aortic_p"]),
        "map":         _round(result["map"]),
        "cvp":         _round(result["cvp"]),
        "la_pressure": _round(result["la_pressure"]),
        "co":          _round(result["co"]),
        "hr":          _round(result["hr"]),
        "sv":          _round(result["sv"]),
        "dbp":         _round(result["dbp"]),
        "sbp":         _round(result["sbp"]),
        "cpp":         _round(result["cpp"]),
        "cop":         _round(result["cop"]),
        "buckberg":    _round(result["buckberg"], 3),
        "summary": {
            "map_mean":      _mean("map"),
            "hr_mean":       _mean("hr"),
            "co_mean":       _mean("co"),
            "cvp_mean":      _mean("cvp"),
            "sv_mean":       _mean("sv"),
            "dbp_mean":      _mean("dbp"),
            "sbp_mean":      _mean("sbp"),
            "cpp_mean":      _mean("cpp"),
            "cop_mean":      _mean("cop"),
            "buckberg_mean": _mean("buckberg"),
            "regions":       regions_pct,
        },
    })


# ---------------------------------------------------------------------------
# POST /api/estimate
# ---------------------------------------------------------------------------

@bp.route("/api/estimate", methods=["POST"])
def estimate():
    """
    Given observed haemodynamic values, return a fitted parameter set
    that can be passed straight back to /api/simulate.
    """
    body    = request.get_json(force=True)
    patient = body.get("patient", {})

    height_cm = float(patient.get("height_cm", 175))
    weight_kg = float(patient.get("weight_kg", 75))
    map_in    = _opt_float(patient.get("map_mmhg"))
    hr_in     = float(patient.get("hr_bpm", 70))
    co_in     = _opt_float(patient.get("cardiac_output_lpm"))
    abi_in    = _opt_float(patient.get("abi"))
    cvp_in    = _opt_float(patient.get("cvp_mmhg"))
    pcwp_in   = _opt_float(patient.get("pcwp_mmhg"))
    pap_in    = _opt_float(patient.get("pap_mean_mmhg"))

    _compartments, cardiac = build_patient_params(
        height_cm, weight_kg,
        map_mmhg=map_in, hr_bpm=hr_in,
        cardiac_output_lpm=co_in, abi=abi_in,
        cvp_mmhg=cvp_in, pcwp_mmhg=pcwp_in,
        pap_mean_mmhg=pap_in,
    )

    return jsonify({
        "patient": {
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "map_mmhg":  map_in,
            "hr_bpm":    hr_in,
            "cardiac_output_lpm": co_in,
            "abi":       abi_in,
            "cvp_mmhg":  cvp_in,
            "pcwp_mmhg": pcwp_in,
            "pap_mean_mmhg": pap_in,
        },
        "derived": {
            "lv_emax_factor": cardiac.get("lv_emax_factor", 1.0),
            "rv_emax_factor": cardiac.get("rv_emax_factor", 1.0),
        },
    })


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _opt_float(v) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None
