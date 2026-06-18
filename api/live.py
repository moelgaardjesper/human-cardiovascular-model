"""
Live mode — continuous cardiovascular simulation with real-time parameter updates.

Architecture
------------
- GET  /api/live/stream  → Server-Sent Events (SSE); pushes haemodynamic state at 10 Hz
- POST /api/live/start   → (re)initialise the session and start the simulation thread
- PATCH /api/live/params → update tilt, drugs, pump, gravity mid-run (thread-safe)
- POST /api/live/stop    → gracefully stop the simulation thread

The LiveSimulator runs the 23-compartment ODE in a background thread at DT=0.002 s
(Euler, stable for all compartments at this step size).  Each 50-step batch (0.1 s
simulated) takes ~0.03 s of wall time, leaving margin to sleep the remaining ~0.07 s
so the simulation paces at approximately 1:1 real-time.

State is extracted after each batch and stored in self._state.  The SSE generator
reads that dict and pushes it to all connected clients.
"""

import csv
import json
import math
import os
import threading
import time
from datetime import datetime
import numpy as np
from collections import deque
from flask import Blueprint, Response, jsonify, request

from model.circulation import _odes, SimParams, IDX, region_volumes, _vascular_pressure
from model.compartments import default_compartments
from model.baroreflex import BaroreflexController
from model.gravity import smooth_tilt_profile, GravityEnvironment, hydrostatic_delta_mmhg
from model.pharmacology import combined_drug_factors, NEUTRAL_FACTORS
from model.perfusion import (
    cerebral_perfusion_pressure, coronary_perfusion_pressure, buckberg_index
)
from model.heart import RA_EMIN, LV_EMIN
from model.respiration import respiratory_sinus_arrhythmia

live_bp = Blueprint("live", __name__)

# ---------------------------------------------------------------------------
# Simulation constants
# ---------------------------------------------------------------------------
# DT=0.001 s: stability criterion for forward Euler is DT < τ_min/2 where
# τ_min = VALVE_R × C_RV = 0.08 × 0.05 = 0.004 s → need DT < 0.002 s.
# DT=0.002 sat right at the boundary; small numerical drift caused the model
# to diverge at ~150 s into a long live run. DT=0.001 gives 4× safety margin.
DT          = 0.001   # s — integration step
PUSH_STEPS  = 100     # steps per push → 100 × 0.001 = 0.1 s simulated per push
TARGET_RATE = 0.1     # target wall-clock seconds per push (≈ real-time)
HISTORY_LEN = 600     # max points kept (60 s at 10 Hz)

# Every live session's full state history (one row per push, ~10 Hz) is
# written here on stop/restart so runs can be examined afterwards.
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")


# ---------------------------------------------------------------------------
# LiveSimulator — runs ODE in a background thread
# ---------------------------------------------------------------------------

class LiveSimulator:
    """Stateful, threaded cardiovascular simulator for live mode."""

    def __init__(self):
        self.params  = SimParams()
        self.comps   = self.params.compartments
        self.V       = np.array([c.init_volume for c in self.comps], dtype=float)
        self.baro    = BaroreflexController(dt=DT)
        self.t       = 0.0
        self._cardiac_phase = 0.0

        # Body-region baseline volumes (mL) for the fluid-distribution
        # avatar — region volumes are reported as % change from these.
        self._region_baseline = region_volumes(self.V)

        self._lock        = threading.Lock()
        self._stop_event  = threading.Event()
        self._thread: threading.Thread | None = None

        # Latest extracted state (dict); None until first push
        self._state: dict | None = None

        # Rolling windows (same logic as run_simulation)
        win = max(100, int(2 * 60.0 / 70.0 / DT))
        self._cvp_win = deque([10.0] * win, maxlen=win)
        self._dbp_win = deque([80.0]  * win, maxlen=win)
        self._sbp_win = deque([120.0] * win, maxlen=win)
        self._map_win = deque([90.0]  * win, maxlen=win)

        # SV / CO tracking — 5-beat rolling average eliminates step-function artifact
        self._prev_V_lv   = self.V[IDX["left_ventricle"]]
        self._beat_ejected = 0.0
        self._last_t_beat  = 0.0
        self._sv_history   = deque([70.0] * 5, maxlen=5)  # 5-beat SV average
        self._sv_current   = 70.0
        self._hr_monitor   = 70.0

        # Within-beat min/max for clean SBP/DBP per beat (aortic + brachial)
        self._beat_p_max        = 90.0
        self._beat_p_min        = 70.0
        self._sbp_last          = 120.0
        self._dbp_last          = 75.0
        self._brachial_beat_max = 90.0
        self._brachial_beat_min = 70.0
        self._brachial_sbp_last = 120.0
        self._brachial_dbp_last = 75.0

        # Latest instantaneous aortic pressure (for cardiac waveform display)
        self._p_ao_last    = 90.0

        # Current tilt (tracked for smooth transitions when user changes it)
        self._current_tilt = 0.0

        # Full per-push state history for this session, written to LOG_DIR
        # on stop()/reset() so runs can be examined afterwards.
        self._history: list[dict] = []
        self.last_log_path: str | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start (or restart) the background simulation thread."""
        self.stop()
        self._stop_event.clear()
        self._history = []
        self._thread = threading.Thread(target=self._run, daemon=True, name="live-sim")
        self._thread.start()

    def stop(self) -> None:
        """Signal the simulation thread to stop and wait for it."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
        self._save_history()

    def _save_history(self) -> None:
        """Write the accumulated per-push state history to LOG_DIR as CSV."""
        if not self._history:
            return
        os.makedirs(LOG_DIR, exist_ok=True)
        fname = datetime.now().strftime("live_%Y%m%d_%H%M%S.csv")
        path = os.path.join(LOG_DIR, fname)
        fieldnames = list(self._history[0].keys())
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self._history)
        self.last_log_path = path
        self._history = []

    def reset(self, scenario: dict | None = None, patient: dict | None = None) -> None:
        """Reinitialise state to default and optionally apply scenario/patient."""
        was_running = self._thread and self._thread.is_alive()
        self.stop()

        self.params  = SimParams()
        self.comps   = self.params.compartments
        self.V       = np.array([c.init_volume for c in self.comps], dtype=float)
        self.baro    = BaroreflexController(dt=DT)
        self.t       = 0.0
        self._cardiac_phase = 0.0
        self._state  = None

        win = max(100, int(2 * 60.0 / 70.0 / DT))
        self._cvp_win = deque([10.0] * win, maxlen=win)
        self._dbp_win = deque([80.0]  * win, maxlen=win)
        self._sbp_win = deque([120.0] * win, maxlen=win)
        self._map_win = deque([90.0]  * win, maxlen=win)
        self._prev_V_lv   = self.V[IDX["left_ventricle"]]
        self._beat_ejected = 0.0
        self._last_t_beat  = 0.0
        self._sv_current   = 70.0
        self._hr_monitor   = 70.0
        self._current_tilt = 0.0

        if patient:
            self._apply_patient(patient)
        if scenario:
            self._apply_scenario(scenario, smooth_transition=False)

        self._region_baseline = region_volumes(self.V)

        if was_running:
            self.start()

    def update_params(self, scenario: dict) -> None:
        """Thread-safe parameter update (called from the PATCH endpoint)."""
        with self._lock:
            self._apply_scenario(scenario, smooth_transition=True)

    @property
    def latest(self) -> dict | None:
        return self._state

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_patient(self, patient: dict) -> None:
        """Scale compartments from patient inputs (runs before thread start)."""
        from model.patient import build_patient_params
        from model.heart import LV_EMAX, RV_EMAX
        height_cm = float(patient.get("height_cm", 175))
        weight_kg = float(patient.get("weight_kg", 75))
        map_in    = _opt_float(patient.get("map_mmhg"))
        hr_in     = float(patient.get("hr_bpm", 70))
        comps, cardiac = build_patient_params(height_cm, weight_kg,
                                              map_mmhg=map_in, hr_bpm=hr_in)
        self.params.compartments = comps
        self.comps = comps
        self.params.hr_bpm  = hr_in
        self.params.lv_emax = LV_EMAX * cardiac.get("lv_emax_factor", 1.0)
        self.params.rv_emax = RV_EMAX * cardiac.get("rv_emax_factor", 1.0)
        self.V = np.array([c.init_volume for c in comps], dtype=float)
        self._prev_V_lv = self.V[IDX["left_ventricle"]]

    def _apply_scenario(self, scenario: dict, smooth_transition: bool = True) -> None:
        """Apply scenario dict to params (must be called under self._lock or before thread start)."""
        gravity_map = {
            "earth": GravityEnvironment.EARTH, "mars": GravityEnvironment.MARS,
            "moon": GravityEnvironment.MOON,   "microgravity": GravityEnvironment.MICROGRAVITY,
        }
        if "gravity" in scenario:
            self.params.gravity = gravity_map.get(scenario["gravity"], GravityEnvironment.EARTH)

        if "tilt_deg" in scenario or "tilt_end_deg" in scenario:
            new_tilt = float(scenario.get("tilt_deg", scenario.get("tilt_end_deg", 0)))
            if smooth_transition:
                self.params.tilt_start_deg  = self._current_tilt
                self.params.tilt_end_deg    = new_tilt
                self.params.tilt_onset_s    = self.t
                self.params.tilt_duration_s = float(scenario.get("tilt_duration_s", 5.0))
            else:
                self.params.tilt_start_deg = new_tilt
                self.params.tilt_end_deg   = new_tilt
                self.params.tilt_onset_s   = 0.0

        if "drugs" in scenario:
            self.params.drug_factors = combined_drug_factors(scenario["drugs"])
        elif "drugs_reset" in scenario:
            self.params.drug_factors = dict(NEUTRAL_FACTORS)

        if "muscle_pump_pressure" in scenario:
            self.params.muscle_pump_pressure = float(scenario["muscle_pump_pressure"])
        if "muscle_pump_freq_hz" in scenario:
            self.params.muscle_pump_freq_hz = float(scenario["muscle_pump_freq_hz"])

        if "ventilation_mode" in scenario:
            self.params.ventilation_mode = str(scenario["ventilation_mode"])
        if "resp_rate_bpm" in scenario:
            self.params.resp_rate_bpm = float(scenario["resp_rate_bpm"])
        if "peep_cmh2o" in scenario:
            self.params.peep_cmh2o = float(scenario["peep_cmh2o"])
        if "pip_cmh2o" in scenario:
            self.params.pip_cmh2o = float(scenario["pip_cmh2o"])
        if "ie_ratio" in scenario:
            self.params.ie_ratio = float(scenario["ie_ratio"])

    def _run(self) -> None:
        """Main simulation loop — runs in the background thread."""
        import traceback
        try:
            self._run_inner()
        except Exception:
            traceback.print_exc()
            print("[live] Simulation thread crashed — check traceback above.")

    def _run_inner(self) -> None:
        i     = IDX
        lv_v0 = self.comps[i["left_ventricle"]].unstressed_volume
        ra_v0 = self.comps[i["right_atrium"]].unstressed_volume
        ao_c  = self.comps[i["aorta"]].compliance
        ao_v0 = self.comps[i["aorta"]].unstressed_volume
        bc_c  = self.comps[i["brachiocephalic"]].compliance
        bc_v0 = self.comps[i["brachiocephalic"]].unstressed_volume
        p_ao     = self._p_ao_last      # initialise before first step
        p_bc_raw = self._brachial_sbp_last

        while not self._stop_event.is_set():
            t0 = time.monotonic()

            # Snapshot params atomically
            with self._lock:
                params = self.params   # reference; read-only for this batch

            drugs = params.drug_factors

            # ---- Run PUSH_STEPS ODE steps ----
            for _ in range(PUSH_STEPS):
                # hr_delta in effect for THIS step's _odes call (set by the
                # previous iteration's baroreflex update, below).
                hr_delta_now = self.baro.hr_delta

                dV = _odes(self.t, self.V, params, self.baro, self._cardiac_phase)
                self.V = np.maximum(self.V + dV * DT, 0.0)
                self.t += DT

                # Pressure monitoring (mirrors run_simulation monitoring loop)
                p_ao  = (self.V[i["aorta"]] - ao_v0) / ao_c
                p_ra  = max(0.0, RA_EMIN * (self.V[i["right_atrium"]] - ra_v0))
                p_lvedp = max(0.0, LV_EMIN * (self.V[i["left_ventricle"]] - lv_v0))

                self._cvp_win.append(p_ra)
                self._map_win.append(p_ao)
                self._p_ao_last = p_ao

                # Track per-beat SBP/DBP (aortic + brachial transmural)
                if p_ao > self._beat_p_max:
                    self._beat_p_max = p_ao
                if p_ao < self._beat_p_min:
                    self._beat_p_min = p_ao
                p_bc_raw = _vascular_pressure(self.V[i["brachiocephalic"]], bc_v0, bc_c)
                if p_bc_raw > self._brachial_beat_max:
                    self._brachial_beat_max = p_bc_raw
                if p_bc_raw < self._brachial_beat_min:
                    self._brachial_beat_min = p_bc_raw

                # CO from LV volume decrease
                curr_V_lv = self.V[i["left_ventricle"]]
                dv_ej = max(0.0, self._prev_V_lv - curr_V_lv)
                self._beat_ejected += dv_ej
                self._prev_V_lv = curr_V_lv

                T_beat = 60.0 / self._hr_monitor
                if self.t - self._last_t_beat >= T_beat:
                    self._sv_history.append(self._beat_ejected)
                    self._sv_current        = float(np.mean(self._sv_history))
                    self._sbp_last          = self._beat_p_max
                    self._dbp_last          = self._beat_p_min
                    self._brachial_sbp_last = self._brachial_beat_max
                    self._brachial_dbp_last = self._brachial_beat_min
                    self._beat_ejected      = 0.0
                    self._beat_p_max        = p_ao
                    self._beat_p_min        = p_ao
                    self._brachial_beat_max = p_bc_raw
                    self._brachial_beat_min = p_bc_raw
                    self._last_t_beat       = self.t

                # Baroreflex update (uses end-diastolic CVP, same as run_simulation)
                p_cvp_edi = min(self._cvp_win)
                self.baro.update(p_ao, 40.0, p_cvp_edi)
                self._hr_monitor = max(30.0, min(180.0,
                                                 params.hr_bpm + self.baro.hr_delta))

                # Advance the continuously-integrated cardiac phase using the
                # HR _odes actually used this step (hr_bpm * drug hr_factor,
                # then baroreflex, then RSA) — see model/circulation.py for
                # why this replaces (t % T)/T.
                hr_now = params.hr_bpm * drugs.get("hr_factor", 1.0)
                hr_now = max(30.0, min(180.0, hr_now + hr_delta_now))
                if params.ventilation_mode != 'none':
                    hr_now = max(30.0, min(180.0, hr_now + respiratory_sinus_arrhythmia(
                        self.t, params.ventilation_mode, params.resp_rate_bpm, params.ie_ratio)))
                self._cardiac_phase = (self._cardiac_phase + hr_now / 60.0 * DT) % 1.0

            # ---- Extract state for this push ----
            tilt = smooth_tilt_profile(
                self.t,
                params.tilt_start_deg, params.tilt_end_deg,
                params.tilt_onset_s,   params.tilt_duration_s,
            )
            self._current_tilt = tilt

            map_val  = float(np.mean(self._map_win))   # 3-beat smoothed MAP
            sbp_val  = self._sbp_last                  # per-beat systolic
            dbp_val  = self._dbp_last                  # per-beat diastolic
            cvp_val  = float(min(self._cvp_win))
            sv       = self._sv_current                # 5-beat smoothed SV
            hr       = self._hr_monitor
            co       = sv * hr / 1000.0

            # Ankle / brachial pressures — same convention as run_simulation
            # (model/circulation.py): P_site = P_transmural - hdp(site).
            c_lba = self.comps[IDX["lower_body_art"]]
            c_bc  = self.comps[IDX["brachiocephalic"]]
            p_lba = _vascular_pressure(self.V[IDX["lower_body_art"]], c_lba.unstressed_volume, c_lba.compliance)
            p_bc  = _vascular_pressure(self.V[IDX["brachiocephalic"]], c_bc.unstressed_volume, c_bc.compliance)
            ankle_p    = p_lba - hydrostatic_delta_mmhg(c_lba.height_m, tilt, params.gravity)
            brachial_p = p_bc  - hydrostatic_delta_mmhg(c_bc.height_m,  tilt, params.gravity)
            hdp_bc     = hydrostatic_delta_mmhg(c_bc.height_m, tilt, params.gravity)
            brachial_sbp_val = self._brachial_sbp_last - hdp_bc
            brachial_dbp_val = self._brachial_dbp_last - hdp_bc

            # Body-region fluid distribution — % change from baseline volume
            regions_now = region_volumes(self.V)
            regions_pct = {
                name: round(100.0 * (vol / self._region_baseline[name] - 1.0), 1)
                for name, vol in regions_now.items()
            }

            self._state = {
                "t":        round(self.t, 2),
                "aortic_p": round(self._p_ao_last, 1),   # instantaneous — shows cardiac cycle
                "map":      round(map_val, 1),             # 3-beat smoothed
                "cvp":      round(cvp_val, 2),
                "co":       round(co, 2),
                "hr":       round(hr, 1),
                "sv":       round(sv, 1),
                "dbp":      round(dbp_val, 1),             # per-beat diastolic
                "sbp":      round(sbp_val, 1),             # per-beat systolic
                "tilt":     round(tilt, 1),
                "cpp":      round(cerebral_perfusion_pressure(map_val, tilt, params.gravity), 1),
                "cop":      round(coronary_perfusion_pressure(dbp_val, float(p_lvedp)), 1),
                "buckberg": round(buckberg_index(dbp_val, float(p_lvedp), hr, sbp_val), 3),
                "ankle_p":      round(float(ankle_p), 1),
                "brachial_p":   round(float(brachial_p), 1),
                "brachial_sbp": round(float(brachial_sbp_val), 1),
                "brachial_dbp": round(float(brachial_dbp_val), 1),
                "regions":  regions_pct,
            }
            hist_row = {k: v for k, v in self._state.items() if k != "regions"}
            hist_row.update({f"region_{name}_pct": pct for name, pct in regions_pct.items()})
            self._history.append(hist_row)

            # ---- Pace to real-time ----
            elapsed   = time.monotonic() - t0
            sleep_for = max(0.0, TARGET_RATE - elapsed)
            if sleep_for > 0:
                time.sleep(sleep_for)


# ---------------------------------------------------------------------------
# Singleton session
# ---------------------------------------------------------------------------
_session = LiveSimulator()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@live_bp.route("/api/live/start", methods=["POST"])
def live_start():
    body    = request.get_json(force=True) or {}
    patient  = body.get("patient", {})
    scenario = body.get("scenario", {})
    _session.reset(scenario=scenario or None, patient=patient or None)
    _session.start()
    return jsonify({"ok": True, "message": "Live simulation started"})


@live_bp.route("/api/live/stop", methods=["POST"])
def live_stop():
    _session.stop()
    return jsonify({"ok": True, "log_path": _session.last_log_path})


@live_bp.route("/api/live/params", methods=["PATCH"])
def live_params():
    body = request.get_json(force=True) or {}
    _session.update_params(body.get("scenario", {}))
    return jsonify({"ok": True})


@live_bp.route("/api/live/state")
def live_state():
    """
    Polling endpoint — returns the latest haemodynamic state as JSON.

    The client polls this at 10 Hz with a simple fetch().
    This replaces SSE which was unreliable with werkzeug's dev server
    due to response buffering (data sent in ~30-second batches instead
    of immediately, causing the browser to see a 30-second freeze).
    """
    state = _session.latest
    if state is None:
        return jsonify({"ready": False})
    return jsonify({**state, "ready": True})


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
