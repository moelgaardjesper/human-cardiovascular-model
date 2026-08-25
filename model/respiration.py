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
Jardin F et al. (1981) N Engl J Med 304:387-392 (PMID 7005679) — PEEP hemodynamics
Hirsch JA & Bishop B (1981) Am J Physiol 241:H620-629 — RSA physiology
"""

import math

# 1 cmH₂O = 0.735 mmHg
_CMHG_TO_MMHG = 0.735

# Fraction of airway pressure that reaches the pleural space during
# positive-pressure ventilation. Physically this is the chest-wall share of
# total respiratory-system elastance, Est,w / Est,rs.
#
# Pelosi 1995 (PMID 7633703, DOI 10.1164/ajrccm.152.2.7633703) measured both
# halves with an esophageal balloon in a NORMAL anaesthetised-paralysed control
# group (n=8) — the model's own target population — at PEEP 0:
#     Est,L 9.3 ± 1.7,  Est,w 5.6 ± 2.3 cmH2O/L
#     Est,w / (Est,L + Est,w) = 5.6 / 14.9 = 0.376
# Their two injury arms give 0.418 (moderate ALI) and 0.358 (ARDS), so the ratio
# is close to 0.4 regardless of lung pathology even though both elastances rise
# steeply with severity. Full table in docs/reference_values.md.
#
# This replaces an unsourced 0.5 that was attributed to Suter 1978 and Talmor
# 2008. Neither paper reports a transmission fraction — Suter (1975, not 1978)
# is a PEEP-titration study and Talmor 2008 is an outcome RCT. See RETRACTIONS
# R3. The old value was ~33% above the measured human ratio and, because every
# ITP-driven venous-return effect scales with it, that error propagated into
# the model's PEEP sensitivity and its pulse-pressure variation.
PLEURAL_TRANSMISSION = 0.376


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
        # Model constraint: the SVC→RA and IVC→RA connections are low-resistance,
        # as large veins should be (VENOATRIAL_R = 0.02 since the valve rebuild;
        # this comment said VALVE_R = 0.08 until 2026-08-25, which those junctions
        # have not used since they stopped being modelled as valves). With a
        # normal driving pressure of ~2 mmHg, even a −5 mmHg ITP would flood the
        # RA every inspiratory cycle. The physiological limiter is not modelled,
        # so ITP has to be kept small enough that the RA self-limits via its own
        # compliance before the cascade destabilises.
        #
        # The limiter is NOT the Guyton waterfall, contrary to what this comment
        # used to claim — see validation_log.md "PPV diagnosed" (2026-08-25) for
        # the algebra: with the SVC inside the thoracic set, ITP cancels out of
        # the waterfall form. What is actually missing is the respiratory swing
        # in ABDOMINAL pressure (backlog item 27), which in a real subject moves
        # with pleural pressure and partly cancels it on the IVC path.
        #
        # Calibration: baseline −2 cmH₂O, swing −1 cmH₂O (peak −3 cmH₂O =
        # −2.2 mmHg), chosen so the RA restores equilibrium within the same
        # breath. RSA (modelled separately) remains the main respiratory
        # signature in HR.
        baseline  = -2.0   # cmH₂O, resting end-expiratory
        swing     = -1.0   # additional cmH₂O at mid-inspiration (total: −3 cmH₂O)
        if phase < ie_ratio:
            itp_cmh2o = baseline + swing * math.sin(math.pi * phase / ie_ratio)
        else:
            itp_cmh2o = baseline

    elif mode == 'mechanical':
        # Airway pressure (PEEP→PIP) is attenuated by the chest wall before it
        # reaches the pleural space. See PLEURAL_TRANSMISSION above.
        _TRANSMISSION = PLEURAL_TRANSMISSION
        if phase < ie_ratio:
            airway    = peep_cmh2o + (pip_cmh2o - peep_cmh2o) * math.sin(
                math.pi * phase / ie_ratio
            )
        else:
            airway    = peep_cmh2o
        itp_cmh2o = airway * _TRANSMISSION

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
