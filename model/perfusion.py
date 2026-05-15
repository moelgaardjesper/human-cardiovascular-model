"""
Cerebral and coronary perfusion sub-models.

These are pure output calculations — no coupling back into the ODE.
They take haemodynamic outputs from run_simulation() and derive
clinically critical perfusion metrics.

Cerebral perfusion pressure (CPP)
----------------------------------
CPP = MAP_brain − ICP

MAP_brain is adjusted for the hydrostatic column between the heart and
the brain (positive correction when head is below heart in HDT;
negative correction in upright / beach-chair).

ICP model: baseline 10 mmHg supine; increases ~0.7 mmHg per cm of
head-below-heart in head-down tilt (venous congestion); decreases
slightly in upright (venous drainage).

Clinical thresholds:
  CPP > 60 mmHg  — adequate (green)
  50–60 mmHg     — marginal (amber)
  < 50 mmHg      — ischaemia risk (red)

Coronary perfusion pressure (CoPP)
------------------------------------
CoPP = DBP − LVEDP

Subendocardial coronary flow is almost entirely diastolic (systolic
compression limits flow in the subendocardium). The driving pressure
is therefore diastolic aortic pressure minus LV end-diastolic pressure.

Buckberg index (subendocardial viability ratio, SEVR)
------------------------------------------------------
Buckberg = DPTI / SPTI
  DPTI = (DBP − LVEDP) × diastolic time   [supply proxy]
  SPTI = SBP × systolic time              [demand proxy]

Clinical thresholds:
  > 0.8  — adequate (green)
  0.5–0.8 — marginal (amber)
  < 0.5  — ischaemia risk (red)

References
----------
- Pohl A, Cullen DJ (2005). Beach-chair position: cerebral perfusion
  considerations during general anaesthesia. Anesth & Analg / JCA / APSF.
- Buckberg GD et al. (1972). Some sources of error in measuring regional
  blood flow with radioactive microspheres. J Appl Physiol 31:598–604.
- Hoffman JI, Buckberg GD (1978). The myocardial supply:demand ratio —
  a critical review. Am J Cardiol 41:327–332.
"""

import numpy as np
from math import sin, radians

from .gravity import BLOOD_DENSITY, MMHG_PER_PA

# ---------------------------------------------------------------------------
# Anatomical constants
# ---------------------------------------------------------------------------
H_BRAIN_M   = 0.25    # m — brain centre above heart (supine reference)
ICP_BASE    = 10.0    # mmHg — normal supine ICP (Marmarou 2005)
ICP_SLOPE   = 0.07    # mmHg/mm of head-below-heart in HDT


# ---------------------------------------------------------------------------
# Cerebral perfusion
# ---------------------------------------------------------------------------

def map_at_brain(map_aorta_mmhg: float, tilt_deg: float,
                 g: float = 9.81) -> float:
    """
    Arterial pressure at brain level (mmHg), corrected for hydrostatics.

    In upright tilt (brain above heart): MAP_brain < MAP_aorta.
    In head-down tilt (brain below heart): MAP_brain > MAP_aorta.
    """
    delta_pa = BLOOD_DENSITY * g * H_BRAIN_M * sin(radians(tilt_deg))
    delta_mmhg = delta_pa * MMHG_PER_PA
    return map_aorta_mmhg - delta_mmhg


def intracranial_pressure(tilt_deg: float) -> float:
    """
    Estimated ICP (mmHg) from tilt angle.

    Head-down tilt → venous congestion → ICP rises.
    Head-up tilt   → venous drainage  → ICP falls slightly.
    Clamped to physiologically plausible range [5, 30] mmHg.
    """
    # Positive when head is below heart (head-down tilt)
    h_below_mm = H_BRAIN_M * 1000.0 * sin(radians(-tilt_deg))
    delta_icp  = max(-5.0, min(20.0, h_below_mm * ICP_SLOPE))
    return ICP_BASE + delta_icp


def cerebral_perfusion_pressure(map_mmhg: float, tilt_deg: float,
                                g: float = 9.81) -> float:
    """
    Cerebral perfusion pressure = MAP_brain − ICP  (mmHg).
    Returns 0 if ICP exceeds brain arterial pressure (theoretical).
    """
    return max(0.0,
               map_at_brain(map_mmhg, tilt_deg, g)
               - intracranial_pressure(tilt_deg))


# ---------------------------------------------------------------------------
# Coronary perfusion
# ---------------------------------------------------------------------------

def coronary_perfusion_pressure(dbp_mmhg: float, lvedp_mmhg: float) -> float:
    """
    Diastolic coronary perfusion pressure = DBP − LVEDP  (mmHg).
    Clinical concern: CoPP < 40 mmHg → subendocardial ischaemia risk.
    """
    return max(0.0, dbp_mmhg - lvedp_mmhg)


def buckberg_index(dbp: float, lvedp: float, hr: float, sbp: float) -> float:
    """
    Subendocardial viability ratio (Buckberg index) = DPTI / SPTI.

    DPTI = (DBP − LVEDP) × diastolic time  [O2 supply proxy]
    SPTI = SBP × systolic time             [O2 demand proxy]

    Diastolic fraction estimated from HR using the relation:
      f_dia ≈ 1 − 0.004 × HR  (clamped 0.40–0.70)
    This captures the known decrease in diastolic time with tachycardia.
    """
    if hr <= 0 or sbp <= 0:
        return 0.0
    t_beat = 60.0 / hr
    f_dia  = max(0.40, min(0.70, 1.0 - 0.004 * hr))
    t_dia  = t_beat * f_dia
    t_sys  = t_beat * (1.0 - f_dia)
    dpti   = (dbp - lvedp) * t_dia
    spti   = sbp * t_sys
    return dpti / spti if spti > 0 else 0.0


# ---------------------------------------------------------------------------
# Convenience: compute all perfusion metrics from a run_simulation() result
# ---------------------------------------------------------------------------

def compute_perfusion(result: dict, tilt_deg: float,
                      g: float = 9.81) -> dict:
    """
    Derive all perfusion metrics from run_simulation() output.

    Parameters
    ----------
    result    : dict returned by run_simulation()
    tilt_deg  : steady-state tilt angle (degrees) for this scenario
    g         : gravitational acceleration (m/s²)

    Returns
    -------
    dict with keys:
        cpp       — cerebral perfusion pressure (mmHg)
        cop       — coronary perfusion pressure (mmHg)
        buckberg  — Buckberg index (dimensionless)
        dbp       — diastolic aortic pressure (mmHg)
        sbp       — systolic aortic pressure (mmHg)
        lvedp     — LV end-diastolic pressure (mmHg)
    """
    n    = len(result["map"])
    h    = n // 2   # use second half (post-transient)
    beat = max(1, int(3.0 / (result["t"][1] - result["t"][0]))) if n > 1 else 1

    aortic = result["aortic_p"]
    # DBP / SBP from rolling min / max over 3-beat window
    kernel = np.ones(beat) / beat
    dbp_arr = np.convolve(np.array([np.min(aortic[max(0, k-beat):k+1]) for k in range(n)]),
                          np.ones(1), mode="same")
    sbp_arr = np.convolve(np.array([np.max(aortic[max(0, k-beat):k+1]) for k in range(n)]),
                          np.ones(1), mode="same")

    dbp_mean  = float(np.mean(result["aortic_p"][h:]) * 0.70)   # fast approximation: DBP ≈ 0.70 × aortic mean
    sbp_mean  = float(np.mean(result["aortic_p"][h:]) * 1.25)   # SBP ≈ 1.25 × mean (rough pulse pressure)
    lvedp_mean = float(np.mean(result.get("lvedp", np.zeros(n))[h:]))
    hr_mean   = float(np.mean(result["hr"][h:]))
    map_mean  = float(np.mean(result["map"][h:]))

    cpp_val      = cerebral_perfusion_pressure(map_mean, tilt_deg, g)
    cop_val      = coronary_perfusion_pressure(dbp_mean, lvedp_mean)
    buckberg_val = buckberg_index(dbp_mean, lvedp_mean, hr_mean, sbp_mean)

    return {
        "cpp":      cpp_val,
        "cop":      cop_val,
        "buckberg": buckberg_val,
        "dbp":      dbp_mean,
        "sbp":      sbp_mean,
        "lvedp":    lvedp_mean,
    }
