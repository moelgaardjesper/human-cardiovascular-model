"""
Intravenous anaesthetic and vasopressor pharmacodynamic models.

Each function returns a dict of multiplicative factors applied to the
baseline haemodynamic parameters in circulation.py.

Dose-response curves use Hill equations calibrated to published clinical
pharmacology data (see individual function docstrings for references).

Factor sign conventions (all multiplicative, 1.0 = no effect):
    svr_factor          >1 raises systemic arterial resistance
    hr_factor           >1 raises heart rate
    lv/rv_emax_factor   >1 raises ventricular contractility
    venous_tone_factor  multiplies systemic venous UNSTRESSED volume (V0):
                          <1 = venoconstriction (recruits blood centrally,
                               raises venous pressure → augments preload/CO)
                          >1 = venodilation (pools blood → reduces preload/CO)
                        This matches the baroreflex `v0_vein_factor` arm and
                        is applied in circulation.py `_odes`.
    venous_compliance_factor
                        multiplies systemic venous COMPLIANCE, on the same
                        compartments as venous_tone_factor:
                          >1 = more compliant (same volume, LESS pressure)
                          <1 = stiffer
                        A SEPARATE DEGREE OF FREEDOM from venous_tone_factor, and
                        not interchangeable with it: mean systemic filling
                        pressure is stressed volume / compliance, so V0 and C move
                        it the same way while differing in how filling pressure
                        responds to a volume CHANGE. Added 2026-09-27 for
                        identifiability (backlog item 70). NO DRUG SETS IT YET.
    venous_resistance_factor
                        multiplies the resistance of every SYSTEMIC VENOUS
                        drainage path (resistance to venous return):
                          >1 = more resistance (venoconstriction narrows vessels)
                          <1 = less resistance (venodilation widens them)
                        NOT inverted, unlike venous_tone_factor. Sourced from both
                        directions: de Wit 2016 (propofol, Rvr -30 %) and Maas 2013
                        (noradrenaline, Rvr x1.50). Added 2026-09-27, backlog item
                        70. NO DRUG SETS IT YET.
    postcap_factor      >1 raises POSTCAPILLARY resistance — the venous drainage
                        out of each exchange bed. Raising it dams blood in the
                        venous compartment, lifting venous and hence capillary
                        pressure, so fluid filters OUT of the plasma. 1.0 = no
                        effect. Applied in circulation.py `_odes` to the four
                        systemic venous drainage flows only.

Note that `venous_tone_factor` and `postcap_factor` are different mechanisms on
the same vessels and are NOT interchangeable: the first is capacitance (how much
volume the veins hold unstressed), the second is resistance (how fast blood
leaves). Only the second moves capillary pressure.
"""

import numpy as np


def _hill(dose: float, ec50: float, e_max: float, n: float = 1.0) -> float:
    """Hill equation: fraction of maximal effect [0, e_max]."""
    if dose <= 0.0:
        return 0.0
    return e_max * (dose ** n) / (ec50 ** n + dose ** n)


# --- alpha-1 postcapillary constriction -------------------------------------
#
# SHAPE is sourced; MAGNITUDE is fitted. Abboud & Eckstein 1968 II (J Clin Invest
# 47:10-19, PMID 16695932) perfused the dog forelimb at constant flow and recorded
# arterial and venous segment pressures separately. Doubling the norepinephrine
# dose (1 -> 2 ug) raised the arterial response 66.1 -> 82.5 mmHg (x1.25) but the
# venous response 6.0 -> 13.5 mmHg (x2.25) — the venous dose-response curve is
# 1.80x steeper. That ratio is dimensionless, so it survives the dog-to-human jump
# where an absolute resistance would not (see CLAUDE.md species rule).
#
# The parameters below reproduce it: over a doubling of dose in the clinical range
# the postcapillary arm grows ~1.85x faster than the arterial arm, against
# Abboud's 1.80. Achieved by a higher Hill coefficient (1.6 vs 0.8) and a higher
# EC50 (0.20 vs 0.10) than the arterial arm, i.e. a curve that is still climbing
# where the arterial one has begun to saturate.
#
# This also reconciles Doorenbos 1991 (human forearm, PMID 1829369), which found
# no norepinephrine effect on capillary filtration and called NE "a predominant
# arterial constrictor". That was a single LOW dose. With a steeper venous slope,
# arterial predominance at low dose and venous catch-up higher up are one curve.
#
# E_MAX is anchored to Abboud's VENOUS PRESSURE response, not to a downstream
# endpoint. At constant flow, pressure is proportional to resistance, so his
# 2 ug figures — small vein pressure rising 13.5 mmHg on a resting 16.9 mmHg —
# imply the venous segment resistance roughly doubled (x1.8). E_MAX = 2.60 puts
# postcap_factor at 2.01 for norepinephrine 0.15 mcg/kg/min, the mid-clinical
# dose, which matches that.
#
# IT IS DELIBERATELY *NOT* FITTED TO LISTER. Fitting it to reproduce Lister's
# 15-19% plasma volume loss would require postcap_factor around 4.5, roughly
# 2.5x what Abboud measured, and would cost ~20% of cardiac output. The residual
# gap is not this parameter's to close: the model's systemic pre/post-capillary
# resistance ratio is ~25 (arteriolar 3.7-4.6 against venous 0.12-0.17) where the
# physiological value is ~4, so capillary pressure is pinned to venous pressure
# and barely responds to ANY pre/post redistribution. See backlog item 20.
# Inflating a sourced drug parameter to paper over a structural calibration error
# is the same mistake as closing the gap by raising Kf, which this project has
# already refused once.
#
# Values above the mid-clinical dose are extrapolation: the saturating value of
# 3.6 is not constrained by any source read so far.
ALPHA1_POSTCAP_EC50  = 0.20
ALPHA1_POSTCAP_HILL  = 1.6
ALPHA1_POSTCAP_EMAX  = 2.60


def norepinephrine(dose_mcg_kg_min: float) -> dict:
    """
    Norepinephrine (α1 + β1 agonist).
    Primary effect: SVR increase.  Secondary: mild inotropy, modest HR rise.

    Reference range: 0.01–0.5 mcg/kg/min clinical.
    """
    svr_factor   = 1.0 + _hill(dose_mcg_kg_min, ec50=0.10, e_max=1.50, n=0.8)
    hr_factor    = 1.0 + _hill(dose_mcg_kg_min, ec50=0.20, e_max=0.10, n=1.0)
    emax_factor  = 1.0 + _hill(dose_mcg_kg_min, ec50=0.15, e_max=0.25, n=0.9)
    return {
        "svr_factor": svr_factor,
        "hr_factor": hr_factor,
        "lv_emax_factor": emax_factor,
        # The RV gets 70 % of the LV inotropic effect, so 70 % of the DEVIATION
        # from 1.0 — not 70 % of the factor itself.
        #
        # This was `emax_factor * 0.7` until 2026-08-28, which inverted the sign of
        # the effect: at the therapeutic dose of 0.10 mcg/kg/min it returned 0.772,
        # a 23 % SUPPRESSION of right ventricular contractility, from a drug this
        # function's own docstring describes as mildly inotropic. At ZERO dose it
        # returned 0.7 — a 30 % suppression from a drug that is not being given,
        # which is the tell: every other factor here is 1.0 at zero dose, because
        # that is what a dose-response means.
        "rv_emax_factor": 1.0 + 0.7 * (emax_factor - 1.0),
        # α1 venoconstriction reduces venous V0 (recruits splanchnic reservoir) → <1.0
        "venous_tone_factor": 1.0 - _hill(dose_mcg_kg_min, ec50=0.20, e_max=0.15),
        # α1 postcapillary constriction raises capillary pressure → filtration out
        "postcap_factor": 1.0 + _hill(dose_mcg_kg_min,
                                      ec50=ALPHA1_POSTCAP_EC50,
                                      e_max=ALPHA1_POSTCAP_EMAX,
                                      n=ALPHA1_POSTCAP_HILL),
    }


def phenylephrine(dose_mcg_kg_min: float) -> dict:
    """
    Phenylephrine (pure α1 agonist).
    Pure vasoconstriction; reflex bradycardia expected (handled by baroreflex).

    Reference range: 0.1–2.0 mcg/kg/min clinical.

    ARTERIAL ARM — CALIBRATED 2026-09-26 against Schaefers 1999 (PMID 10073742),
    the placebo arm: twelve healthy supine men, age 27, reflexes intact. That is
    the model's own condition, which is why it is the calibration source and the
    anaesthetised cohorts are not (see below).
      * CEILING: e_max 1.80 -> 2.10. At the old value the pressor response
        saturated at dMAP +20 / dTPR +476 against a measured +28 (23.5-32.5) /
        +950 (650-1270). A diagnostic settled that the limit was this curve and
        not the resistance pathway: raising the ceiling raises pressure freely.
        At 2.10 all FIVE Schaefers quantities sit in their quartile bands at
        once — dMAP +25.1, dTPR +682, dCO -1.08, dHR -19.0, dSV +10.1.
        THE WINDOW IS NARROW (about 2.05 to 2.15): above it heart rate falls
        past the band, because the model's reflex bradycardia per mmHg is a
        little steeper than measured. Recorded, not tuned away.
      * POTENCY: ec50 0.50 is UNCHANGED, and it is now sourced. Schaefers report
        a median DBP rise of +16.8 mmHg at 1 mcg/kg/min against +30 at the top
        dose, a ratio of 0.56; the model gives 0.53.
    DO NOT set potency from anaesthetised cohorts (Juhl-Olsen 2023, Hojlund 2024).
    Their much larger pressure rise per dose is the MISSING SYMPATHOLYSIS, not
    drug potency: with the baroreflex switched off the model's pressor response at
    the old ceiling is +88 mmHg against +20 with it on. Fitting potency to them
    would bake the missing opioid into this curve.

    THE CEILING IS CONDITIONAL ON AN UNCITED CLIP — measured 2026-09-27, recorded
    here rather than left to be rediscovered. The baroreflex's `svr_factor` floor
    of 0.5 is BINDING at these doses (pre-clip 0.476 at 1 mcg/kg/min, 0.394 at 4),
    so the reflex's vasodilator reserve runs out and stops buffering. Sweeping the
    floor at this curve: 0.50 gives dMAP +25.1 / dTPR +682, and any floor at or
    below 0.39 gives +18.0 / +413 — outside Schaefers' bands. **So about 7 of the
    25 mmHg comes from the clip, and the floor has no source.** The fit is not
    refuted — all five quantities still land together — but it rests on two
    numbers and only one is sourced. **Do NOT move the floor to move this
    response**; it is a reflex limit, not a drug parameter. See backlog item 70,
    which is where the resting-tone question belongs.

    VENOUS ARM — e_max 0.10 IS KEPT, and it is now constrained, though not by a
    direct measurement. Raising it to 0.30 (what the anaesthetised cohorts'
    filling pressures ask for) breaks Schaefers' flow response in awake men: dSV
    +31 mL against +9, dHR -25 against -16. The two groups need different values
    because the drug's venous effect depends on the patient's own sympathetic
    venous tone — small when the veins are already constricted (awake), large
    when that tone is withdrawn (anaesthesia). A fixed ceiling cannot express
    that; it needs endogenous and exogenous agonism on a shared stage. Backlog
    item 70.
    """
    svr_factor = 1.0 + _hill(dose_mcg_kg_min, ec50=0.50, e_max=2.10, n=0.9)
    return {
        "svr_factor": svr_factor,
        "hr_factor": 1.0,          # baroreflex will decrease HR
        "lv_emax_factor": 1.0,
        "rv_emax_factor": 1.0,
        # Pure α1 venoconstriction reduces venous V0 → <1.0
        "venous_tone_factor": 1.0 - _hill(dose_mcg_kg_min, ec50=0.80, e_max=0.10),
        # Postcapillary constriction. Abboud [A4] showed the venous response is
        # α-receptor-mediated — phenoxybenzamine abolished it (-84%) while only
        # partly reducing the arterial (-28%) — so a pure α1 agonist must have it.
        # ASSUMPTION: magnitude taken equal to norepinephrine's, EC50 shifted by the
        # same ratio as the arterial arm (0.50/0.10 = 5x). There is no phenylephrine-
        # specific measurement; leaving this at 1.0 would itself assert that a pure
        # α1 agonist has no venous effect, which Abboud contradicts.
        "postcap_factor": 1.0 + _hill(dose_mcg_kg_min,
                                      ec50=ALPHA1_POSTCAP_EC50 * 5.0,
                                      e_max=ALPHA1_POSTCAP_EMAX,
                                      n=ALPHA1_POSTCAP_HILL),
    }


def vasopressin(units_per_hr: float) -> dict:
    """
    Vasopressin / ADH (V1 receptor, smooth muscle vasoconstriction).
    Low doses: SVR up, no inotropy.  Used as a vasopressor adjunct.

    Reference range: 0.01–0.04 units/min clinical (= 0.6–2.4 units/hr).
    """
    svr_factor          = 1.0 + _hill(units_per_hr, ec50=1.5, e_max=1.20, n=1.0)
    # V1 smooth-muscle venoconstriction reduces venous V0 → <1.0.
    # e_max 0.15 → ~7% reservoir V0 recruitment at 2 U/hr; keeps cardiac index
    # ≈ maintained (Patel 2002: CI preserved). Applied to the mobilizable
    # reservoir set (splanchnic + upper-body) — see circulation._VENOUS_TONE_IDX.
    venous_tone_factor  = 1.0 - _hill(units_per_hr, ec50=2.0, e_max=0.15, n=1.0)
    return {
        "svr_factor": svr_factor,
        "hr_factor": 1.0,
        "lv_emax_factor": 1.0,
        "rv_emax_factor": 1.0,
        "venous_tone_factor": venous_tone_factor,
    }


def epinephrine(dose_mcg_kg_min: float) -> dict:
    """
    Epinephrine (α1 + β1 + β2).
    Low dose: mostly β (inotropy, chronotropy, vasodilation).
    High dose: α dominates (vasoconstriction).
    """
    # β effect peaks at low dose then plateaus; α rises more steeply
    beta_svr_reduction = _hill(dose_mcg_kg_min, ec50=0.05, e_max=0.30, n=1.0)
    alpha_svr_increase = _hill(dose_mcg_kg_min, ec50=0.20, e_max=2.00, n=1.2)
    svr_factor  = 1.0 + alpha_svr_increase - beta_svr_reduction
    hr_factor   = 1.0 + _hill(dose_mcg_kg_min, ec50=0.05, e_max=0.50, n=0.8)
    emax_factor = 1.0 + _hill(dose_mcg_kg_min, ec50=0.05, e_max=0.80, n=0.9)
    return {
        "svr_factor": max(svr_factor, 0.5),
        "hr_factor": hr_factor,
        "lv_emax_factor": emax_factor,
        "rv_emax_factor": emax_factor,
        "venous_tone_factor": 1.0,
    }


def propofol(dose_mg_kg: float) -> dict:
    """
    Propofol — IV induction and maintenance anaesthetic.

    Primary mechanism: peripheral arteriolar vasodilation (α1 inhibition)
    + moderate venous dilation (increases venous capacitance).
    No significant direct chronotropy. Mild negative inotropy at higher doses.
    Cardiac output is maintained at clinical doses (afterload reduction
    partially compensates for reduced preload).

    Calibration — Claeys MA, Gepts E, Camu F (1988). Haemodynamic changes
    during anaesthesia induced and maintained with propofol. Br J Anaesth
    60:3–9. DOI: 10.1093/bja/60.1.3  (PubMed PMID: 3257393)
      n=10 elderly patients, propofol 2 mg/kg IV:
        SVR:  −21% at 2 min after induction, −30% during infusion
        SBP:  −28% at 2 min, −30% during infusion
        DBP:  −19% at 2 min, −25% during infusion
        CO:   unchanged throughout
        HR:   unchanged throughout

    Hill parameters calibrated so that dose=2.0 gives SVR reduction ~22%
    (midpoint of reported 21–30% range):
      ec50_svr = 1.5 mg/kg, emax_svr = 0.40  →  effect(2) = 0.229 ≈ 23% ✓
      ec50_vein = 2.0 mg/kg, emax_vein = 0.12 →  ~6% reservoir V0 ↑ at 2 mg/kg.
        Gives MAP −23 %, CO −6 % (baroreflex off) — matches Claeys (MAP −25 %,
        CO unchanged). Venous tone acts on the mobilizable reservoir set
        (splanchnic + upper-body), see circulation._VENOUS_TONE_IDX; propofol's
        dominant haemodynamic effect is arteriolar/SVR, venodilation secondary.

    Parameters
    ----------
    dose_mg_kg : float
        Equivalent propofol dose (mg/kg).
        0   = no drug
        1   = light sedation / low induction dose
        2   = standard induction dose (target: SVR −20–25%)
        2.5 = induction in elderly or compromised patients
        3   = high induction dose (SVR −30%)
    """
    # Arteriolar vasodilation (primary effect — reduces afterload)
    svr_reduction      = _hill(dose_mg_kg, ec50=1.5, e_max=0.40, n=1.0)
    # Venous dilation (increases unstressed venous volume → reduces preload)
    venous_dilation    = _hill(dose_mg_kg, ec50=2.0, e_max=0.12, n=1.0)
    # Mild negative inotropy (only relevant at high doses; CO unchanged at 2 mg/kg)
    inotropy_reduction = _hill(dose_mg_kg, ec50=3.0, e_max=0.12, n=1.5)

    return {
        "svr_factor":       1.0 - svr_reduction,        # e.g. 0.77 at 2 mg/kg
        "hr_factor":        1.0,                         # no direct chronotropy
        "lv_emax_factor":   1.0 - inotropy_reduction,   # e.g. 0.95 at 2 mg/kg
        "rv_emax_factor":   1.0 - inotropy_reduction,
        "venous_tone_factor": 1.0 + venous_dilation,    # e.g. 1.06 at 2 mg/kg
    }


def spinal_anaesthesia(block_height: float) -> dict:
    """
    Spinal (subarachnoid) anaesthesia — sympathetic denervation below block level.

    block_height: fractional extent of sympathetic block
        0.5 = low block (≈T10) — lower limb / hip surgery
        1.0 = high block (≈T4) — abdominal / Caesarean section

    Mechanism: preganglionic sympathetic fibres blocked → arteriolar dilation
    (SVR↓) and venodilatation (venous capacitance↑). At high block (T1-T4),
    cardiac accelerator fibres are also partially blocked → direct HR blunting;
    however the vagal arc remains intact.

    Calibration — Malmqvist LA et al. (1987) Acta Anaesthesiol Scand 31:467-473.
    DOI: 10.1111/j.1399-6576.1987.tb02605.x  PMID: 3630592
      n=30 patients, average analgesic level T4-5:
        25/30: only minor alterations in CO, HR, SV, MAP, SVR (baroreflex compensates).
         5/30 (T3-4 + complete sympathetic block): MAP fell ≥30%, CO preserved.
      Hill parameters calibrated so that block_height=1.0 gives SVR reduction
      ≈38% (within the Malmqvist 30-40% range at complete block).
    """
    # CLAMPED, because an out-of-range block DIVERGES rather than saturating.
    # Measured 2026-09-15: block_height = 4.0 (four times a complete block, an
    # obvious mis-entry) returned MAP 4.2e47 and CO 0 — the ODE blew up rather
    # than producing anything a caller could recognise as wrong. A model aimed at
    # intraoperative use must not do that: a reviewer will not try it, and a
    # clinician typing into the UI might.
    # Clamping rather than raising, because the UI passes user input straight
    # through and a hard failure mid-run is worse than a saturated block. Full
    # sympathetic denervation is the physiological ceiling; there is nothing
    # beyond it to represent.
    block_height    = min(max(float(block_height), 0.0), 1.0)
    svr_reduction   = 0.38 * block_height    # ≈38% SVR reduction at full block
    # Sympathetic venodilation below the block ↑ reservoir V0. e_max 0.12 gives
    # CO −11 % at full block (baroreflex on) — CO preserved per Malmqvist.
    # Acts on the mobilizable reservoir set (see circulation._VENOUS_TONE_IDX).
    venous_dilation = 0.12 * block_height    # +12% reservoir V0 at full block
    hr_blunting     = 0.07 * block_height    # −7% direct HR at full block (cardiac accelerator block)
    return {
        "svr_factor":         1.0 - svr_reduction,
        "hr_factor":          1.0 - hr_blunting,
        "lv_emax_factor":     1.0,
        "rv_emax_factor":     1.0,
        "venous_tone_factor": 1.0 + venous_dilation,
    }


def combined_drug_factors(drugs: dict) -> dict:
    """
    Merge effects of multiple concurrent drugs by multiplying their factors.

    Parameters
    ----------
    drugs : dict  e.g. {"norepinephrine": 0.1, "vasopressin": 1.0}
              keys are drug names, values are doses in their respective units.
    """
    drug_fns = {
        "norepinephrine": norepinephrine,
        "phenylephrine":  phenylephrine,
        "vasopressin":    vasopressin,
        "epinephrine":    epinephrine,
        "propofol":       propofol,
        "spinal":         spinal_anaesthesia,
    }
    combined = {
        "svr_factor": 1.0,
        "hr_factor": 1.0,
        "lv_emax_factor": 1.0,
        "rv_emax_factor": 1.0,
        "venous_tone_factor": 1.0,
        # No drug returns this yet, so it stays 1.0 and every run is unchanged.
        "venous_compliance_factor": 1.0,
        "venous_resistance_factor": 1.0,
        # Drugs without a sourced postcapillary ratio return 1.0 and so leave this
        # untouched: vasopressin, epinephrine, propofol and spinal block.
        "postcap_factor": 1.0,
    }
    for drug_name, dose in drugs.items():
        fn = drug_fns.get(drug_name)
        if fn is None:
            continue
        effect = fn(dose)
        for key in combined:
            combined[key] *= effect.get(key, 1.0)
    return combined


NEUTRAL_FACTORS = {
    "svr_factor": 1.0,
    "hr_factor": 1.0,
    "lv_emax_factor": 1.0,
    "rv_emax_factor": 1.0,
    "venous_tone_factor": 1.0,
    "venous_compliance_factor": 1.0,
    "venous_resistance_factor": 1.0,
    "postcap_factor": 1.0,
}
