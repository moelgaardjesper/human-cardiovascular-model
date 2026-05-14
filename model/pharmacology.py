"""
Vasopressor pharmacodynamic models.

Each function returns a dict of multiplicative factors applied to the
baseline haemodynamic parameters in circulation.py.

Dose-response curves use Hill equations calibrated to standard clinical
pharmacology references (not in the three primary papers; standard PD).
"""

import numpy as np


def _hill(dose: float, ec50: float, e_max: float, n: float = 1.0) -> float:
    """Hill equation: fraction of maximal effect [0, e_max]."""
    if dose <= 0.0:
        return 0.0
    return e_max * (dose ** n) / (ec50 ** n + dose ** n)


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
        "rv_emax_factor": emax_factor * 0.7,
        "venous_tone_factor": 1.0 + _hill(dose_mcg_kg_min, ec50=0.20, e_max=0.15),
    }


def phenylephrine(dose_mcg_kg_min: float) -> dict:
    """
    Phenylephrine (pure α1 agonist).
    Pure vasoconstriction; reflex bradycardia expected (handled by baroreflex).

    Reference range: 0.1–2.0 mcg/kg/min clinical.
    """
    svr_factor = 1.0 + _hill(dose_mcg_kg_min, ec50=0.50, e_max=1.80, n=0.9)
    return {
        "svr_factor": svr_factor,
        "hr_factor": 1.0,          # baroreflex will decrease HR
        "lv_emax_factor": 1.0,
        "rv_emax_factor": 1.0,
        "venous_tone_factor": 1.0 + _hill(dose_mcg_kg_min, ec50=0.80, e_max=0.10),
    }


def vasopressin(units_per_hr: float) -> dict:
    """
    Vasopressin / ADH (V1 receptor, smooth muscle vasoconstriction).
    Low doses: SVR up, no inotropy.  Used as a vasopressor adjunct.

    Reference range: 0.01–0.04 units/min clinical (= 0.6–2.4 units/hr).
    """
    svr_factor          = 1.0 + _hill(units_per_hr, ec50=1.5, e_max=1.20, n=1.0)
    venous_tone_factor  = 1.0 + _hill(units_per_hr, ec50=2.0, e_max=0.20, n=1.0)
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
    }
    combined = {
        "svr_factor": 1.0,
        "hr_factor": 1.0,
        "lv_emax_factor": 1.0,
        "rv_emax_factor": 1.0,
        "venous_tone_factor": 1.0,
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
}
