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

import json
import math
import threading
import time
import numpy as np
from collections import deque
from flask import Blueprint, Response, jsonify, request

from model.circulation import _odes, SimParams, IDX
from model.compartments import default_compartments
from model.baroreflex import BaroreflexController
from model.gravity import smooth_tilt_profile, GravityEnvironment
from model.pharmacology import combined_drug_factors, NEUTRAL_FACTORS
from model.perfusion import (
    cerebral_perfusion_pressure, coronary_perfusion_pressure, buckberg_index
)
from model.heart import RA_EMIN, LV_EMIN

live_bp = Blueprint("live", __name__)

# ---------------------------------------------------------------------------
# Simulation constants
# ---------------------------------------------------------------------------
DT          = 0.002   # s — integration step (Euler stable for all compartments)
PUSH_STEPS  = 50      # steps per push → 50 × 0.002 = 0.1 s simulated per push
TARGET_RATE = 0.1     # target wall-clock seconds per push (≈ real-time)
HISTORY_LEN = 600     # max points kept (60 s at 10 Hz)


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

        # Within-beat min/max for clean SBP/DBP per beat
        self._beat_p_max   = 90.0
        self._beat_p_min   = 70.0
        self._sbp_last     = 120.0
        self._dbp_last     = 75.0

        # Latest instantaneous aortic pressure (for cardiac waveform display)
        self._p_ao_last    = 90.0

        # Current tilt (tracked for smooth transitions when user changes it)
        self._current_tilt = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start (or restart) the background simulation thread."""
        self.stop()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="live-sim")
        self._thread.start()

    def stop(self) -> None:
        """Signal the simulation thread to stop and wait for it."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None

    def reset(self, scenario: dict | None = None, patient: dict | None = None) -> None:
        """Reinitialise state to default and optionally apply scenario/patient."""
        was_running = self._thread and self._thread.is_alive()
        self.stop()

        self.params  = SimParams()
        self.comps   = self.params.compartments
        self.V       = np.array([c.init_volume for c in self.comps], dtype=float)
        self.baro    = BaroreflexController(dt=DT)
        self.t       = 0.0
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
        p_ao  = self._p_ao_last   # initialise before first step

        while not self._stop_event.is_set():
            t0 = time.monotonic()

            # Snapshot params atomically
            with self._lock:
                params = self.params   # reference; read-only for this batch

            # ---- Run PUSH_STEPS ODE steps ----
            for _ in range(PUSH_STEPS):
                dV = _odes(self.t, self.V, params, self.baro)
                self.V = np.maximum(self.V + dV * DT, 0.0)
                self.t += DT

                # Pressure monitoring (mirrors run_simulation monitoring loop)
                p_ao  = (self.V[i["aorta"]] - ao_v0) / ao_c
                p_ra  = max(0.0, RA_EMIN * (self.V[i["right_atrium"]] - ra_v0))
                p_lvedp = max(0.0, LV_EMIN * (self.V[i["left_ventricle"]] - lv_v0))

                self._cvp_win.append(p_ra)
                self._map_win.append(p_ao)
                self._p_ao_last = p_ao

                # Track per-beat SBP/DBP
                if p_ao > self._beat_p_max:
                    self._beat_p_max = p_ao
                if p_ao < self._beat_p_min:
                    self._beat_p_min = p_ao

                # CO from LV volume decrease
                curr_V_lv = self.V[i["left_ventricle"]]
                dv_ej = max(0.0, self._prev_V_lv - curr_V_lv)
                self._beat_ejected += dv_ej
                self._prev_V_lv = curr_V_lv

                T_beat = 60.0 / self._hr_monitor
                if self.t - self._last_t_beat >= T_beat:
                    self._sv_history.append(self._beat_ejected)
                    self._sv_current   = float(np.mean(self._sv_history))
                    self._sbp_last     = self._beat_p_max
                    self._dbp_last     = self._beat_p_min
                    self._beat_ejected = 0.0
                    self._beat_p_max   = p_ao
                    self._beat_p_min   = p_ao
                    self._last_t_beat  = self.t

                # Baroreflex update (uses end-diastolic CVP, same as run_simulation)
                p_cvp_edi = min(self._cvp_win)
                self.baro.update(p_ao, 40.0, p_cvp_edi)
                self._hr_monitor = max(30.0, min(180.0,
                                                 params.hr_bpm + self.baro.hr_delta))

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
            }

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
    return jsonify({"ok": True})


@live_bp.route("/api/live/params", methods=["PATCH"])
def live_params():
    body = request.get_json(force=True) or {}
    _session.update_params(body.get("scenario", {}))
    return jsonify({"ok": True})


@live_bp.route("/api/live/stream")
def live_stream():
    """SSE endpoint — push latest haemodynamic state at ~10 Hz."""
    def generate():
        tick = 0
        try:
            while True:
                state = _session.latest
                if state is not None:
                    yield f"data: {json.dumps(state)}\n\n"
                else:
                    # Send keepalive comment while no state available yet
                    yield ": waiting\n\n"

                tick += 1
                # Send keepalive comment every 5s to prevent proxy timeouts
                if tick % 50 == 0:
                    yield ": keepalive\n\n"

                time.sleep(TARGET_RATE)
        except GeneratorExit:
            pass  # client disconnected — clean exit

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering
            "Connection":        "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )


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
