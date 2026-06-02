"""
Respiratory-cardiovascular coupling.

Two mechanisms are implemented:

1. Intrathoracic pressure (ITP)
   Cyclic variation of pleural pressure with the respiratory cycle.
   Applied as an additive offset to all thoracic compartment pressures
   in _odes(), so that:
     P_intraluminal = P_transmural + ITP
   This modulates venous return (IVC/SVC → RA) and pulmonary vascular
   flow exactly as in Heldt 2002 §2.3 and Magosso 2001.

   Spontaneous breathing (negative-pressure): ITP drops during inspiration
   → RA intraluminal pressure falls → venous return augments → SV rises.

   Mechanical PPV (positive-pressure): ITP rises during machine breath
   → RA intraluminal pressure rises → venous return impeded → SV falls.
   Sustained PEEP shifts the entire ITP baseline upward, producing a
   chronic reduction in venous return and CO proportional to PEEP level.

2. Respiratory sinus arrhythmia (RSA)
   Vagally-mediated HR modulation at the respiratory frequency.
   HR increases during inspiration, decreases during expiration.
   Calibration: amplitude ≈ 4 bpm peak-to-peak for resting spontaneous
   breathing (Hirsch & Bishop 1981, Saul et al. 1989).
   Blunted (~40 %) under mechanical PPV (reduced vagal tone).

References
----------
Heldt T et al. (2002) J Appl Physiol 92:1239-1254  — ITP model §2.3
Magosso E & Ursino M (2001) Med Biol Eng Comput 39:155-166 — ITP coupling
Jardin F et al. (1981) Crit Care Med 9:19-22 — PEEP hemodynamics
Hirsch JA & Bishop B (1981) Am J Physiol 241:H620-629 — RSA physiology
"""

import math

# 1 cmH₂O = 0.735 mmHg
_CMHG_TO_MMHG = 0.735


def intrathoracic_pressure(
    t: float,
    mode: str,
    resp_rate_bpm: float,
    peep_cmh2o: float = 5.0,
    pip_cmh2o: float = 20.0,
    ie_ratio: float = 0.33,
) -> float:
    """
    Instantaneous intrathoracic pressure (mmHg) as a function of time.

    Parameters
    ----------
    t             : simulation time (s)
    mode          : 'none' | 'spontaneous' | 'mechanical'
    resp_rate_bpm : respiratory rate (breaths/min)
    peep_cmh2o    : PEEP for mechanical ventilation (cmH₂O)
    pip_cmh2o     : peak inspiratory pressure for mechanical ventilation (cmH₂O)
    ie_ratio      : inspiratory fraction of cycle (0.33 → 1:2 I:E ratio)

    Returns
    -------
    ITP in mmHg (negative = below atmospheric, as in spontaneous breathing)
    """
    if mode == 'none':
        return 0.0

    T     = 60.0 / resp_rate_bpm          # breath period (s)
    phase = (t % T) / T                    # 0–1 within one breath cycle

    if mode == 'spontaneous':
        # Resting end-expiratory ITP: −5 cmH₂O (Heldt 2002).
        # Drops to ~−13 cmH₂O at mid-inspiration with normal tidal volume.
        # Smooth half-sine during inspiration; flat (passive) during expiration.
        baseline  = -5.0   # cmH₂O
        swing     = -8.0   # additional cmH₂O depression at mid-inspiration
        if phase < ie_ratio:
            itp_cmh2o = baseline + swing * math.sin(math.pi * phase / ie_ratio)
        else:
            itp_cmh2o = baseline

    elif mode == 'mechanical':
        # Pressure swings from PEEP (expiration) to PIP (peak inspiration).
        # Half-sine rise during the inspiratory fraction; falls back to PEEP.
        if phase < ie_ratio:
            itp_cmh2o = peep_cmh2o + (pip_cmh2o - peep_cmh2o) * math.sin(
                math.pi * phase / ie_ratio
            )
        else:
            itp_cmh2o = peep_cmh2o

    else:
        return 0.0

    return itp_cmh2o * _CMHG_TO_MMHG


def respiratory_sinus_arrhythmia(
    t: float,
    mode: str,
    resp_rate_bpm: float,
    ie_ratio: float = 0.33,
) -> float:
    """
    RSA heart-rate modulation (additive delta-bpm) at the respiratory frequency.

    Positive = HR increase (mid-inspiration peak).
    Peak-to-peak amplitude: ~4 bpm spontaneous, ~1.6 bpm mechanical PPV.

    Parameters
    ----------
    t             : simulation time (s)
    mode          : 'none' | 'spontaneous' | 'mechanical'
    resp_rate_bpm : respiratory rate (breaths/min)
    ie_ratio      : inspiratory fraction of cycle
    """
    if mode == 'none':
        return 0.0

    T     = 60.0 / resp_rate_bpm
    phase = (t % T) / T

    # Amplitude: half peak-to-peak (so full swing = 2 × amplitude)
    amp = 2.0 if mode == 'spontaneous' else 0.8   # bpm

    if phase < ie_ratio:
        # Rise to peak at mid-inspiration
        return amp * math.sin(math.pi * phase / ie_ratio)
    else:
        # Gradual return during expiration (slower than inspiration)
        exp_phase = (phase - ie_ratio) / (1.0 - ie_ratio)
        return -amp * 0.5 * math.sin(math.pi * exp_phase)
