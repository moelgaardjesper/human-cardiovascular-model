"""
Patient-specific parameter scaling.

Scales the default (healthy 70-kg male) compartment parameters to match
individual patient inputs using allometric relationships.

Tiers
-----
1 (minimal)    MAP + BMI/height  → blood volume scaling, resistance from estimated CO
2 (intermediate) + cardiac output + ABI → direct arterial resistance fit
3 (advanced)   + CVP + PCWP + PAP → full intracardiac calibration

BSA formula: Mosteller (1987): BSA = sqrt(height_cm * weight_kg / 3600)
"""

import numpy as np
from .compartments import default_compartments, Compartment


BSA_REF = 1.87   # m² — reference BSA for the default parameter set (70 kg, 175 cm male)
BV_REF  = 5000.0 # mL — reference total blood volume


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
    """
    bv_scale = bsa / BSA_REF
    scaled = []

    for c in compartments:
        # Unstressed volumes scale with blood volume
        new_v0     = c.unstressed_volume * bv_scale
        new_c      = c.compliance * bv_scale       # compliance scales with volume
        new_r      = c.resistance                  # resistance starts unchanged
        new_vinit  = c.init_volume * bv_scale
        scaled.append(Compartment(
            name=c.name,
            compliance=new_c,
            resistance=new_r,
            unstressed_volume=new_v0,
            height_m=c.height_m,
            init_volume=new_vinit,
        ))

    cardiac = {
        "hr_bpm": hr_bpm if hr_bpm is not None else 70.0,
        "lv_emax_factor": 1.0,
        "rv_emax_factor": 1.0,
    }

    # Tier 1: scale SVR from MAP if cardiac output not available
    if map_mmhg is not None:
        co_est = cardiac_output_lpm if cardiac_output_lpm is not None else _estimate_co(bsa)
        svr_measured = _svr(map_mmhg, cvp_mmhg or 5.0, co_est)
        svr_ref      = _svr(93.0, 5.0, 5.0)
        svr_scale    = svr_measured / svr_ref
        for c in scaled:
            if "art" in c.name or c.name in ("aorta", "brachiocephalic", "abdominal_aorta"):
                c.resistance *= svr_scale

    # Tier 2: ABI — peripheral arterial disease increases lower-body resistance
    if abi is not None and abi < 1.0:
        pad_factor = 1.0 + 2.0 * (1.0 - abi)  # up to 3x at ABI=0
        for c in scaled:
            if "lower_body_art" in c.name:
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
) -> tuple[list[Compartment], dict]:
    """Convenience wrapper: compute BSA then scale compartments."""
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
