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
# is a PEEP-titration study and Talmor 2008 is an outcome RCT. Both verified
# against PubMed 2026-09-15 and both readings hold:
#   Suter  PMID 234174,   DOI 10.1056/NEJM197502062920604 — N Engl J Med
#          292(6):284-9, 1975. "Optimum end-expiratory airway pressure in
#          patients with acute pulmonary failure", n=15. PEEP titration.
#   Talmor PMID 19001507, DOI 10.1056/NEJMoa0708638 — N Engl J Med
#          359(20):2095-104, 2008. Oesophageal-pressure-guided PEEP RCT, n=61,
#          primary endpoint OXYGENATION.
# The identifiers are recorded so a reader can check the retraction rather than
# take it on trust. See RETRACTIONS
# R3. The old value was ~33% above the measured human ratio and, because every
# ITP-driven venous-return effect scales with it, that error propagated into
# the model's PEEP sensitivity and its pulse-pressure variation.
PLEURAL_TRANSMISSION = 0.376

# Fraction of the PLEURAL pressure swing that reaches the abdominal compartment
# during POSITIVE-PRESSURE ventilation. The ventilator pushes the diaphragm
# down, which pressurises the abdomen, so pleural and abdominal pressure rise
# TOGETHER.
#
# Heijnen 2016 (PMID 26732769, DOI 10.1177/0885066615625180), n=18 ventilated
# patients, intravesical pressure at 5-second inspiratory and expiratory holds:
#     transmission index 8.9 ± 5.0 % (post-cardiac-surgery, n=9)
#                        7.1 ± 7.9 % (acute respiratory failure, n=9)
# THE DENOMINATOR IN THAT PAPER IS AIRWAY DRIVING PRESSURE, not pleural: their
# Methods define it as ΔIAP / (Pplat − PEEP). Since this model's ITP is already
# a pleural pressure, the 8 % must be divided by PLEURAL_TRANSMISSION:
#     0.08 / 0.376 = 0.21
# Per group: 24.4 % (group 1) and 18.1 % (group 2). Feeding the model the raw
# 8 % would understate the coupling by 2.6x.
#
# Cross-check on the MECHANISM rather than the coefficient — van den Berg,
# Jansen & Pinsky 2002 (PMID 11842062, n=42, sedated AND PARALYSED): raising
# airway pressure to 19 cmH2O took right atrial pressure from 8.1 to 15.4 mmHg
# and cardiac output did NOT change, because 70 % or more of the atrial rise was
# matched by an abdominal rise (ΔPabd/ΔPra 0.73 ± 0.36). Their ΔPabd/ΔPaw is
# 0.20 ± 0.1, ~0.27 once the mixed mmHg/cmH2O units are corrected — about 3x
# Heijnen's. The difference is the preparation: van den Berg used 25-second
# holds at 1750 mL in patients the authors themselves call "probably
# hypervolemic", chosen to MAXIMISE the effect. Heijnen used tidal holds at
# unchanged settings, which is the condition this model simulates, so Heijnen
# sets the coefficient and van den Berg confirms the mechanism is real.
# Both tables are in docs/reference_values.md.
ABDOMINAL_TRANSMISSION = 0.21

# ---------------------------------------------------------------------------
# WHY THIS IS APPLIED ONLY UNDER MECHANICAL VENTILATION
# ---------------------------------------------------------------------------
# The sign of the pleural-to-abdominal coupling is NOT the same in the two
# ventilation modes, and using one coefficient for both would invert the
# mechanism in one of them:
#
#   MECHANICAL  the ventilator pushes the diaphragm down. Pleural pressure RISES
#               and abdominal pressure RISES. Same sign. ABDOMINAL_TRANSMISSION
#               is positive and is what Heijnen and van den Berg measured.
#
#   SPONTANEOUS the diaphragm CONTRACTS and descends under its own power.
#               Pleural pressure FALLS while abdominal pressure RISES. Opposite
#               signs — this is exactly the transdiaphragmatic pressure,
#               Pdi = Pabd − Ppl, and it is generated by muscle, not
#               transmitted through tissue.
#
# There is therefore no single coefficient, and no sourced value for the
# spontaneous case: Akoumianaki 2024 [PMID 38753985, DOI
# 10.1097/ALN.0000000000005071, Anesthesiology 141(3):541-553] has the right
# instrumentation (76 patients,
# simultaneous oesophageal and gastric pressure) but every patient had
# spontaneous effort, so its ΔPgas is expiratory MUSCLE contraction rather than
# transmitted pressure.
#
# So the mechanism is applied under mechanical ventilation only. That covers the
# case it is needed for — pulse-pressure variation is a positive-pressure
# quantity and Michard's < 13 % threshold is defined in ventilated patients.
# The spontaneous case is a KNOWN GAP with a known sign, recorded as backlog
# item 27b. Do not extend this constant to spontaneous breathing by flipping a
# sign; the magnitude is a different quantity and needs its own source.


# ---------------------------------------------------------------------------
# SPONTANEOUS BREATHING — pleural pressure baseline and swing
# ---------------------------------------------------------------------------
# At module level so they can be swept and asserted, rather than buried as
# locals in a function body.
#
# BASELINE is the resting end-expiratory pleural pressure. Unchanged at
# -2 cmH2O and still not independently sourced; it sets the MEAN intrathoracic
# pressure and therefore the mean intraluminal right atrial pressure, which is
# a separate gap — the model's mean is 3.2 mmHg against Hoff's measured 6.94.
# That is a mean problem, not an amplitude problem, and is left alone here.
#
# SWING was -1.0 cmH2O and is now -3.5. THE OLD VALUE WAS AN ADMITTED WORKAROUND,
# not a measurement: the comment it replaced said ITP "has to be kept small
# enough that the RA self-limits via its own compliance before the cascade
# destabilises", because "even a -5 mmHg ITP would flood the RA every
# inspiratory cycle".
#
# THAT STABILITY CLAIM WAS RE-MEASURED ON 2026-09-01 AND IS FALSE. Sweeping the
# swing from -1 to -12 cmH2O produced no instability at any value: at -5 the
# model gives CO 6.88 and MAP 98.0; at -12, CO 7.20 and MAP 99.1, both entirely
# stable. Whatever made the cap necessary was fixed by later work — most likely
# the chamber rebuild, the venous rework, or the left-atrial compliance
# correction, none of which existed when the cap was written.
#
# THE NEW VALUE IS CALIBRATED AGAINST A MEASURED ENDPOINT, not against a
# pleural-pressure target. Hoff 2019 (PMID 31560715) gives the respiratory swing
# in intraluminal CVP in 10 healthy awake supine volunteers: 3.05 mmHg
# peak-to-peak. Measured against `ra_intraluminal`:
#     swing -1.0 -> 0.86 mmHg     swing -3.5 -> 3.07 mmHg
#     swing -3.0 -> 2.64          swing -5.0 -> 4.34
# -3.5 cmH2O lands on 3.07 against the measured 3.05.
#
# Calibrating a parameter to an endpoint is normally the failure mode this
# project guards against. It is legitimate HERE because the old value was not
# sourced — it was a self-described workaround — and the new one is anchored to
# a direct human measurement through the quantity it governs. The resulting
# pleural swing of 2.57 mmHg peak-to-peak also sits inside the 2.2-4.4 mmHg that
# textbooks give for quiet breathing, which is a cross-check rather than the
# target, since that range is not sourced in this project's ledger.
#
# STILL WANTED: a measured dPes during quiet unloaded tidal breathing, to
# constrain the DRIVER independently of the endpoint.
SPONTANEOUS_ITP_BASELINE_CMH2O = -2.0
SPONTANEOUS_ITP_SWING_CMH2O    = -3.5


def intrathoracic_pressure(
    t: float,
    mode: str,
    resp_rate_bpm: float,
    peep_cmh2o: float = 5.0,
    pip_cmh2o: float = 20.0,
    ie_ratio: float = 0.33,
    hold_start_s: float | None = None,
    hold_duration_s: float = 0.0,
    hold_mode: str = 'inspiratory',
    hold_pressure_cmh2o: float | None = None,
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
    hold_start_s  : when a ventilatory hold begins (s), or None for no hold
    hold_duration_s : how long the hold lasts (s)
    hold_mode     : 'inspiratory' (airway held at the plateau) or 'expiratory'
                    (airway held at PEEP)
    hold_pressure_cmh2o : plateau pressure for an inspiratory hold; defaults to
                    `pip_cmh2o`. Ignored for an expiratory hold.

    Returns
    -------
    ITP in mmHg (negative = below atmospheric, as in spontaneous breathing)

    Notes
    -----
    **On the hold.** Cyclic inspiration here is a HALF-SINE, so airway pressure
    ramps up and straight back down and there is no plateau to read against.
    That is correct for tidal ventilation and wrong for the manoeuvre used to
    measure the venous return curve, which needs a SQUARE step held long enough
    to read.

    Berger 2016 (Am J Physiol Heart Circ Physiol 311:H794-806,
    DOI 10.1152/ajpheart.00931.2015) holds at a fixed airway plateau for 30 s
    and reads "the first three cardiac cycles occurring **9 s into the
    manoeuvre**". The 9 s matters: he measured mean systemic filling pressure
    over 9-12 s of right atrial occlusion **"before the onset of sympathetic
    reflex vasoconstriction"**, and notes that sympathetic activation shows up
    as a further rise in all intravascular pressures about 10 s later.
    **Read later than that and the reflex, not the vasculature, is what is being
    measured.** A sustained-pressure protocol read at 45-60 s gave a venous
    return slope of -0.280 against -0.456 for the same model measured properly.

    Berger's study is in PIGS, so the PROTOCOL transfers but none of its
    absolute values may be used as a human target.
    """
    if mode == 'none':
        return 0.0

    # ---- ventilatory hold: a square plateau, overriding the cyclic waveform --
    if hold_start_s is not None and hold_duration_s > 0.0 \
            and hold_start_s <= t < hold_start_s + hold_duration_s:
        if mode == 'mechanical':
            if hold_mode == 'expiratory':
                airway = peep_cmh2o
            else:
                airway = pip_cmh2o if hold_pressure_cmh2o is None \
                    else hold_pressure_cmh2o
            return airway * PLEURAL_TRANSMISSION * _CMHG_TO_MMHG
        # A spontaneous breath-hold parks ITP at its end-expiratory baseline.
        return SPONTANEOUS_ITP_BASELINE_CMH2O * _CMHG_TO_MMHG

    T     = 60.0 / resp_rate_bpm          # breath period (s)
    phase = (t % T) / T                    # 0–1 within one breath cycle

    if mode == 'spontaneous':
        # See SPONTANEOUS_ITP_BASELINE_CMH2O / _SWING_CMH2O above.
        if phase < ie_ratio:
            itp_cmh2o = (SPONTANEOUS_ITP_BASELINE_CMH2O
                         + SPONTANEOUS_ITP_SWING_CMH2O
                         * math.sin(math.pi * phase / ie_ratio))
        else:
            itp_cmh2o = SPONTANEOUS_ITP_BASELINE_CMH2O

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


def valsalva_itp_mmhg(
    t: float,
    start_s: float | None,
    duration_s: float,
    mouth_pressure_mmhg: float = 40.0,
    transmission: float = 0.9,
) -> float:
    """Intrathoracic pressure offset (mmHg) during a Valsalva strain.

    **WHY THIS IS NOT THE VENTILATORY HOLD WITH A DIFFERENT NUMBER.**
    `PLEURAL_TRANSMISSION = 0.376` describes POSITIVE-PRESSURE VENTILATION: the
    ventilator inflates the lung, the chest wall and diaphragm resist, and only
    about a third of airway pressure reaches the pleural space.
    **A Valsalva is the opposite manoeuvre.** The glottis is closed and the
    subject actively contracts the expiratory muscles, so the thorax is squeezed
    from OUTSIDE and pleural pressure rises almost as much as mouth pressure —
    oesophageal pressure tracks a 40 mmHg strain closely. Routing a Valsalva
    through the ventilation path would therefore under-deliver it by roughly a
    factor of two and make the manoeuvre look far milder than it is.
    The default of 0.9 rather than 1.0 leaves a little for abdominal recruitment
    and rib-cage compliance. **It is an assumption, not a measurement** — no
    sourced pleural-to-mouth ratio for a strained Valsalva is in the ledger.

    The standard bedside manoeuvre is 40 mmHg held for 15 s, which is the
    default here.

    Parameters
    ----------
    t                   : simulation time (s)
    start_s             : when the strain begins, or None for no Valsalva
    duration_s          : strain duration (s)
    mouth_pressure_mmhg : expiratory pressure held against the closed glottis
    transmission        : fraction reaching the pleural space (see above)
    """
    if start_s is None or duration_s <= 0.0:
        return 0.0
    if not (start_s <= t < start_s + duration_s):
        return 0.0
    return mouth_pressure_mmhg * transmission


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
