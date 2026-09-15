"""
Patient-specific parameter scaling.

Scales the default (healthy 70-kg male) compartment parameters to match
individual patient inputs using allometric relationships.

Tiers
-----
1 (minimal)    MAP + height + weight → blood volume scaling, resistance from estimated CO
2 (intermediate) + cardiac output + ABI → direct arterial resistance fit
3 (advanced)   + CVP + PCWP + PAP → full intracardiac calibration

BSA formula: Mosteller (1987): BSA = sqrt(height_cm * weight_kg / 3600)

Body habitus enters through BSA and nothing else. Height and weight are collapsed
to BSA immediately, and every compartment scales by bsa / BSA_REF. Two patients with
the same BSA get the same model whatever their BMI. BMI is derivable from the inputs
but is not used — see backlog item 34, which carries the measured slope (Sindi 2014:
oesophageal pressure +0.27 cmH2O per BMI unit) for when the term goes in.
"""

from dataclasses import replace

from .aging import (REFERENCE_AGE_YEARS, arterial_compliance_factor,
                    chamber_age_factors)

import numpy as np
from .compartments import default_compartments, Compartment, ARTERIOLAR_SEGMENTS
from model.baroreflex import (REFERENCE_MAP_MMHG, REFERENCE_CVP_MMHG,
                              REFERENCE_CO_LPM)


# The body the default compartment set represents.
REF_HEIGHT_CM = 175.0
REF_WEIGHT_KG = 70.0

# BSA_REF IS COMPUTED, NOT ASSIGNED, and that is the fix. It was 1.87, from the
# initial commit, commented "(70 kg, 175 cm male)" — but no BSA formula gives
# 1.87 for that body: Mosteller 1.8447, DuBois 1.8481, Haycock 1.8468,
# Gehan-George 1.8539. The model uses Mosteller everywhere else, so the constant
# disagreed with the function beside it.
#
# The consequence was quiet and systematic: every compartment scales by
# bsa / BSA_REF, so `build_patient_params(175, 70)` — the reference patient
# entered by their own height and weight — scaled everything by 0.9865 instead
# of 1.0. A 1.4 % shrink applied to the exact case that should have been the
# identity. Deriving it from the same function that measures every patient makes
# the two incapable of disagreeing.
BSA_REF = np.sqrt(REF_HEIGHT_CM * REF_WEIGHT_KG / 3600.0)   # = 1.8447 m²
BV_REF  = 5000.0 # mL — reference total blood volume


# ---------------------------------------------------------------------------
# PATIENT SEX — backlog item 32.
#
# The reference parameter set is MALE. That was not a choice made explicitly: the
# 2026-08-24 chamber rebuild derived every chamber from the MALE columns of Luu
# 2022 and Gao 2022, so the model has been a male reference patient without ever
# saying so. A female patient entered by height and weight got male chamber
# proportions scaled by BSA, and the residual error was systematic, not random.
#
# THE SEX DIFFERENCE SURVIVES BSA INDEXING — that is the whole point. These are
# female/male ratios of values ALREADY indexed to body surface area, so they are
# what remains after body size is accounted for:
#
#   Luu 2022 (PMID 34980185, n=3206), ventricles, indexed mL/m2:
#       LVEDV 74 -> 65 (0.878)   LVESV 28 -> 23 (0.821)   LVEF 62 -> 64 (1.032)
#       RVEDV 86 -> 72 (0.837)   RVESV 41 -> 31 (0.756)   RVEF 53 -> 58 (1.094)
#   Gao 2022 (PMID 35124105, n=408), atria, indexed mL/m2:
#       LAVmax 35.7 -> 38.4 (1.076)   LAEF total 60.0 -> 62.5 (1.042)
#       RAVmax 34.9 -> 32.7 (0.937)   RAEF total 47.2 -> 52.6 (1.114)
#
# NOTE THE LEFT ATRIUM RUNS THE OTHER WAY. Indexed to BSA the female LA is
# LARGER (1.076) while every other chamber is smaller. A single "female chambers
# are smaller" factor would be wrong, and would be wrong in a direction that
# matters — the LA is the wedge-pressure surrogate.
#
# HOW THE FACTORS ARE APPLIED. For a chamber, EDV = V0 + P/E_min. To scale the
# volume at an UNCHANGED filling pressure, V0 and 1/E_min must scale together —
# scaling V0 alone would drop the filling pressure with it, which is not what the
# data says (a woman's filling pressures are not 12 % lower than a man's). So
# `volume` scales unstressed volume and init_volume, and E_min is divided by the
# same factor. `emax` then carries the ejection-fraction difference, since
# ESV = V0 + P_sys/E_max.
#
# MALE IS THE IDENTITY. Every male factor is exactly 1.0, so a male patient is
# bit-for-bit what the model did before this existed — which is what keeps the
# entire validation suite untouched. There is a regression test asserting it.


SEX_CHAMBER_FACTORS = {
    "male": {
        "left_ventricle":  {"volume": 1.0, "emax": 1.0},
        "right_ventricle": {"volume": 1.0, "emax": 1.0},
        "left_atrium":     {"volume": 1.0, "emax": 1.0},
        "right_atrium":    {"volume": 1.0, "emax": 1.0},
    },
    "female": {
        # These are NOT the raw female/male ratios. In a closed loop a chamber
        # does not keep the volume it is assigned — the circulation pushes back,
        # so an assigned factor is only partly transmitted. Measured
        # transmission, at fixed body size: LV 0.62, RV 0.71, RA 0.87. The
        # factors below are the raw ratios divided through by that, and were
        # then verified by re-measuring against Luu's and Gao's female columns.
        # Same lesson as RA_EMIN in heart.py: elastance and V0 set VOLUME, and
        # how much volume they actually get is the circulation's decision.
        "left_ventricle":  {"volume": 0.804, "emax": 1.032},
        "right_ventricle": {"volume": 0.769, "emax": 1.094},
        # LEFT ATRIUM DELIBERATELY 1.0 — it cannot be scaled this way. Measured
        # transmission is NEGATIVE (-0.11): assigning a LARGER LA volume made the
        # chamber SMALLER. That is the pooled-volume problem confirmed from a
        # second direction — with the mitral valve at 0.01 and the pulmonary-vein
        # junction at 0.02, the pulmonary veins, LA and LV are nearly continuous,
        # so LA volume is a compliance-weighted share of one pool rather than an
        # independently set quantity (see backlog items 23 and 25a). The female
        # LA is the one chamber that is LARGER indexed to BSA (1.076), so this is
        # a real gap, not a rounding decision. It needs 25a's structural fix.
        "left_atrium":     {"volume": 1.0,   "emax": 1.042},
        "right_atrium":    {"volume": 0.928, "emax": 1.114},
    },
}

# ---------------------------------------------------------------------------
# PATIENT AGE — backlog item 25b. Which vessels stiffen.
# ---------------------------------------------------------------------------
# Age scales the compliance of the LARGE ELASTIC ARTERIES and nothing else.
# Like THORACIC_COMPARTMENTS and ABDOMINAL_COMPARTMENTS this is ANATOMY, not a
# knob: it is the set of vessels whose wall is elastin-dominated and whose
# stiffening with age is what widens pulse pressure.
#
#   aorta, abdominal_aorta   the elastic conduit itself, and where most of
#                            total arterial compliance lives
#   brachiocephalic          a great vessel of the same wall type
#
# DELIBERATELY EXCLUDED: upper_body_art, lower_body_art, renal_art,
# splanchnic_art. These stand for the muscular distributing and resistance
# vessels, whose compliance contributes little to the pulse-pressure buffer and
# which do not stiffen with age the way the aorta does. That difference is not
# incidental — the age-related REVERSAL of the aortic-to-brachial stiffness
# gradient exists precisely because the aorta stiffens and the periphery does
# not. Including them would model the wrong physiology and would also make the
# effect too large.
#
# Together these three carry 0.87 of the model's 1.64 mL/mmHg total arterial
# compliance, which is the right share for a pulse-pressure buffer.
ELASTIC_ARTERIES = ("aorta", "abdominal_aorta", "brachiocephalic")


_CHAMBER_TO_PARAM = {
    "left_ventricle": "lv", "right_ventricle": "rv",
    "left_atrium": "la", "right_atrium": "ra",
}


def apply_cardiac(params, cardiac: dict) -> None:
    """Apply a `cardiac` dict from scale_compartments() onto a SimParams.

    Callers used to do this by hand and set only `lv_emax`/`rv_emax`. That is the
    same failure mode that silently dropped `p_stiffen` from the compartment copy
    for months — a hand-written field list that stops matching what produces it.
    Anything added to the cardiac dict is applied here and nowhere else.
    """
    from .heart import LV_EMAX, RV_EMAX, LA_EMAX, RA_EMAX
    from .heart import LV_EMIN, RV_EMIN, LA_EMIN, RA_EMIN
    base_max = {"lv": LV_EMAX, "rv": RV_EMAX, "la": LA_EMAX, "ra": RA_EMAX}
    base_min = {"lv": LV_EMIN, "rv": RV_EMIN, "la": LA_EMIN, "ra": RA_EMIN}
    if "hr_bpm" in cardiac:
        params.hr_bpm = cardiac["hr_bpm"]
    for tag in ("lv", "rv", "la", "ra"):
        setattr(params, f"{tag}_emax",
                base_max[tag] * cardiac.get(f"{tag}_emax_factor", 1.0))
        setattr(params, f"{tag}_emin",
                base_min[tag] * cardiac.get(f"{tag}_emin_factor", 1.0))


def bsa_mosteller(height_cm: float, weight_kg: float) -> float:
    """Body surface area (m²) using Mosteller formula."""
    return np.sqrt(height_cm * weight_kg / 3600.0)


def estimated_blood_volume(bsa: float) -> float:
    """
    Nadler formula approximation: BV ∝ BSA.
    Returns total blood volume (mL).
    """
    return BV_REF * (bsa / BSA_REF)


def scale_compartments(
    compartments: list[Compartment],
    bsa: float,
    map_mmhg: float | None = None,
    hr_bpm: float | None = None,
    cardiac_output_lpm: float | None = None,
    abi: float | None = None,
    cvp_mmhg: float | None = None,
    pcwp_mmhg: float | None = None,
    pap_mean_mmhg: float | None = None,
    sex: str = "male",
    age_years: float = REFERENCE_AGE_YEARS,
) -> tuple[list[Compartment], dict]:
    """
    Return scaled compartment list and a dict of cardiac parameters.

    Parameters
    ----------
    compartments    : default compartment list from default_compartments()
    bsa             : patient BSA (m²)
    map_mmhg        : measured mean arterial pressure (mmHg)
    hr_bpm          : heart rate (bpm)
    cardiac_output_lpm : cardiac output (L/min) — tier 2
    abi             : ankle-brachial index — tier 2 (1.0 = normal)
    cvp_mmhg        : central venous pressure — tier 3
    pcwp_mmhg       : pulmonary capillary wedge pressure — tier 3
    pap_mean_mmhg   : mean pulmonary artery pressure — tier 3
    sex             : "male" (default, the reference set) or "female".
                      See SEX_CHAMBER_FACTORS — male is the identity, so a male
                      patient is unchanged by this parameter existing.
    """
    if sex not in SEX_CHAMBER_FACTORS:
        raise ValueError(
            f"sex must be one of {sorted(SEX_CHAMBER_FACTORS)}, got {sex!r}. "
            "The reference data (Luu 2022, Gao 2022) reports biological sex, "
            "which is what carries the chamber physiology."
        )
    sex_factors = SEX_CHAMBER_FACTORS[sex]
    age_factor = arterial_compliance_factor(age_years)
    age_chamber = chamber_age_factors(age_years)
    bv_scale = bsa / BSA_REF
    scaled = []

    for c in compartments:
        # Unstressed volumes scale with blood volume
        # dataclasses.replace copies EVERY field and overrides only the scaled
        # ones. Listing fields by hand here silently dropped `p_stiffen` — so
        # every patient-scaled scenario, which is all of the literature tests,
        # ran with LINEAR limb veins instead of the collapsible-tube law — and
        # would have dropped `drain_resistance` the same way. Do not go back to
        # naming fields individually.
        # Sex applies ONLY to the four cardiac chambers, and only after BSA:
        # these are ratios of BSA-indexed values, so body size is already out.
        sex_vol = (sex_factors.get(c.name, {}).get("volume", 1.0)
                   * age_chamber.get(c.name, {}).get("volume", 1.0))
        # Age stiffens the large elastic arteries and nothing else here.
        # ELASTIC_ARTERIES is anatomy, not a knob — see its note below.
        age_c = age_factor if c.name in ELASTIC_ARTERIES else 1.0
        scaled.append(replace(
            c,
            compliance=c.compliance * bv_scale * age_c,
            unstressed_volume=c.unstressed_volume * bv_scale * sex_vol,
            init_volume=c.init_volume * bv_scale * sex_vol,
            # resistance deliberately unscaled here; tiers 1-3 below adjust it
        ))

    cardiac = {
        "hr_bpm": hr_bpm if hr_bpm is not None else 70.0,
        "sex": sex,
    }
    # E_min is divided by the volume factor so the chamber holds its scaled
    # volume at an UNCHANGED filling pressure (EDV = V0 + P/E_min); E_max carries
    # the ejection-fraction difference. See SEX_CHAMBER_FACTORS.
    # Sex and age both act on these two fields and are INDEPENDENT axes: sex
    # factors are ratios of BSA-indexed values within an age band, age factors
    # are ratios within the male columns. They therefore MULTIPLY. Age touches
    # only the two ventricles — see chamber_age_factors for why the atria are
    # excluded.
    for chamber, tag in _CHAMBER_TO_PARAM.items():
        f = sex_factors.get(chamber, {})
        a = age_chamber.get(chamber, {})
        vol  = f.get("volume", 1.0) * a.get("volume", 1.0)
        emax = f.get("emax", 1.0) * a.get("emax", 1.0)
        cardiac[f"{tag}_emax_factor"] = emax
        cardiac[f"{tag}_emin_factor"] = 1.0 / vol

    # Tier 1: scale SVR from MAP if cardiac output not available
    if map_mmhg is not None:
        co_est = cardiac_output_lpm if cardiac_output_lpm is not None else _estimate_co(bsa)
        svr_measured = _svr(map_mmhg, cvp_mmhg or 5.0, co_est)
        # Imported, not re-typed — see the REFERENCE_* note in baroreflex.py.
        # These were two independent copies of one operating point until
        # 2026-09-15 (backlog item 50).
        svr_ref      = _svr(REFERENCE_MAP_MMHG, REFERENCE_CVP_MMHG,
                            REFERENCE_CO_LPM)
        svr_scale    = svr_measured / svr_ref
        # Scale the ARTERIOLES, which since 2026-08-21 live on the venous side
        # of each exchange bed (see ARTERIOLAR_SEGMENTS). Matching on "art" in the
        # name would now hit only the small conduit resistances and scale SVR by
        # almost nothing.
        for c in scaled:
            if c.name in ARTERIOLAR_SEGMENTS:
                c.resistance *= svr_scale

    # Tier 2: ABI — peripheral arterial disease increases lower-body resistance
    if abi is not None and abi < 1.0:
        pad_factor = 1.0 + 2.0 * (1.0 - abi)  # up to 3x at ABI=0
        # The lower-body arteriolar resistance is carried by the three leg
        # exchange segments, not by lower_body_art (a conduit).
        for c in scaled:
            if c.name in ("thigh_vein", "calf_vein", "foot_vein"):
                c.resistance *= pad_factor

    # Tier 3: pulmonary calibration from PCWP / PAP
    if pcwp_mmhg is not None and pap_mean_mmhg is not None and cardiac_output_lpm is not None:
        pvr_measured = _pvr(pap_mean_mmhg, pcwp_mmhg, cardiac_output_lpm)
        pvr_ref      = _pvr(15.0, 9.0, 5.0)
        pvr_scale    = pvr_measured / pvr_ref
        for c in scaled:
            if "pulmonary" in c.name:
                c.resistance *= pvr_scale

    if pcwp_mmhg is not None:
        # PCWP ≈ LA pressure → adjust LV E_min / compliance to match filling pressure
        pcwp_ref = 9.0  # mmHg
        if pcwp_mmhg > pcwp_ref:
            # Elevated PCWP suggests reduced LV compliance or raised filling
            cardiac["lv_emax_factor"] = max(0.5, 1.0 - 0.02 * (pcwp_mmhg - pcwp_ref))

    return scaled, cardiac


def build_patient_params(
    height_cm: float,
    weight_kg: float,
    map_mmhg: float | None = None,
    hr_bpm: float | None = None,
    cardiac_output_lpm: float | None = None,
    abi: float | None = None,
    cvp_mmhg: float | None = None,
    pcwp_mmhg: float | None = None,
    pap_mean_mmhg: float | None = None,
    sex: str = "male",
    age_years: float = REFERENCE_AGE_YEARS,
) -> tuple[list[Compartment], dict]:
    """Convenience wrapper: compute BSA then scale compartments.

    `sex` defaults to "male" because the reference parameter set IS male — the
    chambers were derived from the male columns of Luu 2022 and Gao 2022. All
    validation and calibration is done against male patients (see the note in
    tests/test_circulation.py), so the default keeps every comparison
    like-for-like.
    """
    bsa = bsa_mosteller(height_cm, weight_kg)
    compartments = default_compartments()
    return scale_compartments(
        compartments, bsa,
        map_mmhg=map_mmhg,
        hr_bpm=hr_bpm,
        cardiac_output_lpm=cardiac_output_lpm,
        abi=abi,
        cvp_mmhg=cvp_mmhg,
        pcwp_mmhg=pcwp_mmhg,
        pap_mean_mmhg=pap_mean_mmhg,
        sex=sex,
        age_years=age_years,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _estimate_co(bsa: float) -> float:
    """Cardiac index ~3.0 L/min/m² → CO (L/min)."""
    return 3.0 * bsa


def _svr(map_mmhg: float, cvp_mmhg: float, co_lpm: float) -> float:
    """Systemic vascular resistance (mmHg·min/L = Wood units)."""
    return (map_mmhg - cvp_mmhg) / co_lpm


def _pvr(pap_mmhg: float, pcwp_mmhg: float, co_lpm: float) -> float:
    """Pulmonary vascular resistance (Wood units)."""
    return (pap_mmhg - pcwp_mmhg) / co_lpm
