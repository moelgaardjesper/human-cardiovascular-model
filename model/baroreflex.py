"""
Arterial baroreflex and cardiopulmonary reflex model.

Implements the 4-step control architecture from PMC9363491 §Methods,
which itself follows Heldt 2002:

  Step 1: Integrate aortic and right-atrial pressures (running averages).
  Step 2: Compute error signals vs. setpoints.
  Step 3: Convolve with impulse response functions (sympathetic/parasympathetic).
  Step 4: Scale convolution outputs to effector adjustments (HR, SVR, E_max, V0_vein).

Setpoints (healthy male at rest):
    MAP_set  = 93 mmHg   (mean aortic pressure)
    PP_set   = 40 mmHg   (pulse pressure)
    CVP_set  =  3 mmHg   (central venous / right atrial pressure)
"""

import numpy as np
from collections import deque


MAP_SETPOINT = 93.0   # mmHg
PP_SETPOINT  = 40.0   # mmHg
CVP_SETPOINT =  3.0   # mmHg

# Impulse response time constants (s) — sympathetic fast/slow, parasympathetic
_TAU_SYMP_FAST  =  2.0
_TAU_SYMP_SLOW  = 10.0
_TAU_PARA       =  1.5


def _exp_impulse(tau: float, dt: float, n: int) -> np.ndarray:
    """Discrete exponential impulse response of length n."""
    t = np.arange(n) * dt
    h = (1 / tau) * np.exp(-t / tau)
    h /= h.sum()
    return h


class BaroreflexController:
    """
    Stateful baroreflex controller.

    Call `update(map_mmhg, pp_mmhg, cvp_mmhg, dt)` every simulation step.
    Read `hr_delta`, `svr_factor`, `emax_factor`, `v0_vein_factor` for
    the current effector adjustments.

    All factors are multiplicative (1.0 = no change).
    `hr_delta` is additive in bpm.
    """

    def __init__(
        self,
        map_set: float = MAP_SETPOINT,
        pp_set: float  = PP_SETPOINT,
        cvp_set: float = CVP_SETPOINT,
        dt: float = 0.01,
        history_len: int = 300,
    ):
        self.map_set  = map_set
        self.pp_set   = pp_set
        self.cvp_set  = cvp_set
        self.dt       = dt

        # Rolling pressure buffers (250-sample average, ~2.5 s at dt=0.01)
        n = history_len
        self._map_buf  = deque([map_set]  * n, maxlen=n)
        self._pp_buf   = deque([pp_set]   * n, maxlen=n)
        self._cvp_buf  = deque([cvp_set]  * n, maxlen=n)

        # Impulse response filters (100 taps each)
        taps = 100
        self._h_fast = _exp_impulse(_TAU_SYMP_FAST, dt, taps)
        self._h_slow = _exp_impulse(_TAU_SYMP_SLOW, dt, taps)
        self._h_para = _exp_impulse(_TAU_PARA,       dt, taps)

        # Error signal histories for convolution
        self._err_map  = deque([0.0] * taps, maxlen=taps)
        self._err_pp   = deque([0.0] * taps, maxlen=taps)
        self._err_cvp  = deque([0.0] * taps, maxlen=taps)

        # Effector outputs (updated each step)
        self.hr_delta       = 0.0   # bpm added to baseline HR
        self.svr_factor     = 1.0
        self.emax_factor    = 1.0
        self.v0_vein_factor = 1.0

        # Effector gains (tuned to reproduce Heldt 2002 tilt response)
        self._gain_hr_para  = -25.0   # bpm per normalised error
        self._gain_hr_symp  =  15.0
        self._gain_svr      =   0.40
        self._gain_emax     =   0.25
        self._gain_v0_vein  =   0.10

    def update(
        self,
        map_mmhg: float,
        pp_mmhg: float,
        cvp_mmhg: float,
    ) -> None:
        """Advance the controller by one time step."""
        # Step 1 — running average (already implicit in deque mean)
        self._map_buf.append(map_mmhg)
        self._pp_buf.append(pp_mmhg)
        self._cvp_buf.append(cvp_mmhg)

        avg_map = np.mean(self._map_buf)
        avg_pp  = np.mean(self._pp_buf)
        avg_cvp = np.mean(self._cvp_buf)

        # Step 2 — error signals (positive = pressure above setpoint)
        err_map = avg_map - self.map_set
        err_pp  = avg_pp  - self.pp_set
        err_cvp = avg_cvp - self.cvp_set

        self._err_map.append(err_map)
        self._err_pp.append(err_pp)
        self._err_cvp.append(err_cvp)

        arr_map = np.array(self._err_map)
        arr_pp  = np.array(self._err_pp)
        arr_cvp = np.array(self._err_cvp)

        # Step 3 — convolve each error with sympathetic/parasympathetic filters
        # np.dot gives the current output of the convolution (scalar)
        symp_fast_map = float(np.dot(self._h_fast, arr_map))
        symp_slow_map = float(np.dot(self._h_slow, arr_map))
        para_map      = float(np.dot(self._h_para, arr_map))
        symp_cvp      = float(np.dot(self._h_fast, arr_cvp))

        # Step 4 — effector adjustments
        # HR: parasympathetic reduces HR when MAP high; sympathetic raises it when low
        self.hr_delta = (
            self._gain_hr_para * _sigmoid(para_map, scale=10.0)
            + self._gain_hr_symp * _sigmoid(-symp_fast_map, scale=10.0)
        )
        # SVR: sympathetic increases resistance when MAP low
        svr_err = -(symp_slow_map + symp_cvp * 0.3)
        self.svr_factor     = 1.0 + self._gain_svr  * _sigmoid(svr_err, scale=15.0)
        self.emax_factor    = 1.0 + self._gain_emax * _sigmoid(svr_err, scale=15.0)
        self.v0_vein_factor = 1.0 - self._gain_v0_vein * _sigmoid(svr_err, scale=20.0)

        # Clamp to physiological limits
        self.hr_delta       = np.clip(self.hr_delta, -30.0, 50.0)
        self.svr_factor     = np.clip(self.svr_factor, 0.3, 3.0)
        self.emax_factor    = np.clip(self.emax_factor, 0.4, 2.5)
        self.v0_vein_factor = np.clip(self.v0_vein_factor, 0.7, 1.3)


def _sigmoid(x: float, scale: float = 10.0) -> float:
    """Soft-saturation: maps (-∞,+∞) to (-1, 1)."""
    return np.tanh(x / scale)
