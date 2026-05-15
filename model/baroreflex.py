"""
Arterial baroreflex and cardiopulmonary reflex model.

Implements the 4-step control architecture from PMC9363491 §Methods / Heldt 2002:

  Step 1: Input smoothing — running average of aortic and RA pressures (~2.5 s window)
            to remove beat-to-beat pulsatility before error computation.
  Step 2: Error signals vs setpoints (MAP_set=93, CVP_set=3 mmHg).
  Step 3: IIR first-order exponential filters for each autonomic time constant.
            Parasympathetic (τ=1.5 s) → fast HR adjustment (1-2 cardiac cycles).
            Sympathetic fast (τ=2 s)  → acute HR modulation.
            Sympathetic slow (τ=10 s) → sustained SVR and venous tone.
            Source: Borst et al. 1982/1984; Olufsen et al. 2005/2006.
  Step 4: Scale filtered errors to effector adjustments (HR, SVR, E_max, V0_vein).

NOTE on implementation: the original FIR convolution approach (100 taps at dt=0.001 s)
only spanned 0.1 s of history — far too short for the 2–10 s physiological time constants,
making all components effectively instantaneous and identical. Replaced with IIR first-order
filters (y[k] = (1-α)·y[k-1] + α·x[k], α = dt/τ) which correctly implement each
time constant with O(1) memory.

Setpoints (healthy male at rest):
    MAP_set  = 93 mmHg
    CVP_set  =  3 mmHg

Gain calibration:
    HR gains (-3, +2) calibrated against Likhvantsev 2025 (PMID 39500675):
      Trendelenburg ΔHR = −1.65 bpm for ΔMAP ≈ +4 mmHg
      → effective gain ≈ 5 × tanh(4/10) ≈ 1.8 bpm ✓
    SVR gain (0.65) increased to maintain MAP during moderate HUT without
      over-relying on HR; validated against Wieling 1998 (PMID 9640339).
"""

import numpy as np
from collections import deque


MAP_SETPOINT = 93.0   # mmHg
PP_SETPOINT  = 40.0   # mmHg
CVP_SETPOINT =  3.0   # mmHg

# Autonomic time constants (s) — Borst 1982, Olufsen 2005
_TAU_PARA       =  1.5   # parasympathetic (fast HR, 1-2 cardiac cycles)
_TAU_SYMP_FAST  =  2.0   # sympathetic fast (acute HR modulation)
_TAU_SYMP_SLOW  = 10.0   # sympathetic slow (sustained SVR, venous tone)


class BaroreflexController:
    """
    Stateful baroreflex controller using IIR exponential filters.

    Call `update(map_mmhg, pp_mmhg, cvp_mmhg)` every simulation step.
    Read `hr_delta`, `svr_factor`, `emax_factor`, `v0_vein_factor`.

    `hr_delta` is additive (bpm). All other factors are multiplicative.
    """

    def __init__(
        self,
        map_set: float = MAP_SETPOINT,
        pp_set: float  = PP_SETPOINT,
        cvp_set: float = CVP_SETPOINT,
        dt: float = 0.001,
        history_len: int = 2500,
    ):
        self.map_set  = map_set
        self.pp_set   = pp_set
        self.cvp_set  = cvp_set
        self.dt       = dt

        # Input smoothing: ~2.5 s running average removes beat-to-beat pulsatility
        n = history_len   # 2500 steps × 0.001 s = 2.5 s at dt=0.001
        self._map_buf = deque([map_set]  * n, maxlen=n)
        self._cvp_buf = deque([cvp_set]  * n, maxlen=n)

        # IIR filter states — one per time constant per signal
        # Each state y is updated: y ← (1-α)·y + α·error, α = dt/τ
        self._para_map      = 0.0   # parasympathetic, MAP error (τ=1.5 s)
        self._symp_fast_map = 0.0   # sympathetic fast, MAP error (τ=2 s)
        self._symp_slow_map = 0.0   # sympathetic slow, MAP error (τ=10 s) — SVR
        self._symp_fast_cvp = 0.0   # sympathetic fast, CVP error (τ=2 s)

        # IIR decay coefficients α = dt/τ (clamped to [0,1])
        self._a_para = min(1.0, dt / _TAU_PARA)
        self._a_fast = min(1.0, dt / _TAU_SYMP_FAST)
        self._a_slow = min(1.0, dt / _TAU_SYMP_SLOW)

        # Effector outputs (read by run_simulation after each update)
        self.hr_delta       = 0.0
        self.svr_factor     = 1.0
        self.emax_factor    = 1.0
        self.v0_vein_factor = 1.0

        # Effector gains
        self._gain_hr_para  =  -3.0   # bpm/sigmoid (was −25; reduced 8× per Likhvantsev 2025)
        self._gain_hr_symp  =   2.0   # bpm/sigmoid (was +15)
        self._gain_svr      =   0.65  # SVR scale factor (was 0.40; increased for MAP maintenance)
        self._gain_emax     =   0.25
        self._gain_v0_vein  =   0.10

    def update(
        self,
        map_mmhg: float,
        pp_mmhg: float,
        cvp_mmhg: float,
    ) -> None:
        """Advance the controller by one simulation time step."""
        # Step 1 — input smoothing (removes pulsatility)
        self._map_buf.append(map_mmhg)
        self._cvp_buf.append(cvp_mmhg)
        avg_map = np.mean(self._map_buf)
        avg_cvp = np.mean(self._cvp_buf)

        # Step 2 — error signals (positive = pressure above setpoint)
        err_map = avg_map - self.map_set
        err_cvp = avg_cvp - self.cvp_set

        # Step 3 — IIR exponential filtering (y ← (1-α)y + αx)
        # Each filter has a distinct physiological time constant.
        self._para_map      = (1-self._a_para)*self._para_map      + self._a_para*err_map
        self._symp_fast_map = (1-self._a_fast)*self._symp_fast_map + self._a_fast*err_map
        self._symp_slow_map = (1-self._a_slow)*self._symp_slow_map + self._a_slow*err_map
        self._symp_fast_cvp = (1-self._a_fast)*self._symp_fast_cvp + self._a_fast*err_cvp

        # Step 4 — effector adjustments
        # HR: parasympathetic (fast) withdraws when MAP ↑; sympathetic raises when MAP ↓
        self.hr_delta = (
            self._gain_hr_para * _sigmoid(self._para_map,      scale=10.0)
            + self._gain_hr_symp * _sigmoid(-self._symp_fast_map, scale=10.0)
        )

        # SVR: slow sympathetic sustains vasoconstriction when MAP is chronically low
        svr_err = -(self._symp_slow_map + self._symp_fast_cvp * 0.3)
        self.svr_factor     = 1.0 + self._gain_svr       * _sigmoid(svr_err, scale=15.0)
        self.emax_factor    = 1.0 + self._gain_emax      * _sigmoid(svr_err, scale=15.0)
        self.v0_vein_factor = 1.0 - self._gain_v0_vein   * _sigmoid(svr_err, scale=20.0)

        # Clamp to physiological limits
        self.hr_delta       = np.clip(self.hr_delta,       -30.0, 50.0)
        self.svr_factor     = np.clip(self.svr_factor,       0.3,  3.0)
        self.emax_factor    = np.clip(self.emax_factor,      0.4,  2.5)
        self.v0_vein_factor = np.clip(self.v0_vein_factor,   0.7,  1.3)


def _sigmoid(x: float, scale: float = 10.0) -> float:
    """Soft-saturation: maps (−∞, +∞) → (−1, 1)."""
    return np.tanh(x / scale)
