"""
23-compartment lumped-parameter cardiovascular ODE system.

Primary reference:
  PMC9363491 — Heldt-based cardiovascular model for orthostatic stress
  Heldt T et al. (2002) J Appl Physiol 92:1239-1254

State vector V[0..22]: volume (mL) in each compartment.
Compartment order defined in compartments.py / default_compartments().

The original single lower_body_vein has been split into three serial
segments (foot_vein → calf_vein → thigh_vein → ivc) to correctly
simulate the ~640 mL venous pooling observed on standing (Sjöstrand 1953).

Flow between compartments:
    Q = (P_upstream - P_downstream + ΔP_hydrostatic) / R_outflow

Cardiac chamber pressure (time-varying elastance):
    P = E(t) * (V - V0)

Vascular compartment pressure:
    P = (V - V0) / C

Hydrostatic correction (gravity.py):
    ΔP = ρ g h sin(α)   [mmHg]

One-way valves (mitral, aortic, tricuspid, pulmonic) enforced by
setting Q = 0 if flow would be retrograde.
"""

import math
import numpy as np
from scipy.integrate import solve_ivp

from .compartments import (
    HIP_HEIGHT_M, default_compartments, IDX,
    TRICUSPID_R, PULMONIC_R, MITRAL_R, AORTIC_R, AORTIC_ZC,
    orifice_k, VALVE_DP_REG,
)
from .heart import (
    elastance_from_phase, frank_starling_emax,
    LV_EMAX, RV_EMAX, RV_EMIN, LV_V0_DIA, LV_V30,
    klotz_diastolic_pressure, _normalised_activation, ventricular_activation,
    VENTRICULAR_T_MAX_SCALE,
    RA_EMAX, RA_EMIN, LA_EMAX, LA_EMIN,
    atrial_phase_offset,
    pericardial_pressure, PERI_CAPACITY, PERI_K, PERI_VK,
)
from .gravity import (hydrostatic_delta_mmhg, GravityEnvironment, smooth_tilt_profile,
                      positional_itp_mmhg, articulated_hydrostatic_delta_mmhg)
from .baroreflex import (BaroreflexController,
                         VENOUS_RESTING_TONE as B_VENOUS_RESTING_TONE)
from .pharmacology import (combined_drug_factors, NEUTRAL_FACTORS,
                           ALPHA1_VENOUS_EMAX, alpha1_tone_drive)
from .respiration import (
    intrathoracic_pressure, respiratory_sinus_arrhythmia, valsalva_itp_mmhg,
    ABDOMINAL_TRANSMISSION,
)
from .slow_dynamics import (init_slow_state, update_slow_state,
                            oncotic_pressure_mmhg, neurohumoral_svr_factor)


# Systemic venous reservoir — holds the bulk of circulating blood volume.
# Hemorrhage removes volume from these compartments proportionally to their
# current stressed volume; this avoids creating an artificial localised
# pressure sink at any single site.
VENOUS_RESERVOIR = (
    "upper_body_vein", "svc", "renal_vein", "splanchnic_vein",
    "thigh_vein", "calf_vein", "foot_vein", "ivc",
    "ivc_renal", "ivc_infrarenal",     # the IVC split, items 65 and 72
)

# The venous compartments that are pure CONDUITS — they receive venous inflow
# rather than arterial, so they are NOT exchange beds and carry no Starling
# filtration. Named once here so that tests and tools DERIVE the exchange-bed set
# instead of writing their own list of conduits, which is exactly how splitting
# the IVC would otherwise have silently made two new "missing filtration beds".
VENOUS_CONDUITS = ("svc", "ivc", "ivc_renal", "ivc_infrarenal")


# Body regions for the fluid-distribution avatar — groups compartments into
# anatomical zones. Each zone's total volume, tracked relative to its value
# at simulation start, indicates net fluid shift (e.g. leg pooling on tilt,
# abdominal/leg depletion on hemorrhage, thoracic engorgement on fluid bolus
# or Trendelenburg).
BODY_REGIONS = {
    "thorax": (
        "aorta", "brachiocephalic", "upper_body_art", "upper_body_vein", "svc",
        "right_atrium", "right_ventricle", "pulmonary_art", "pulmonary_cap",
        "pulmonary_vein", "left_atrium", "left_ventricle", "coronary",
    ),
    "abdomen": (
        "abdominal_aorta", "renal_art", "renal_vein", "splanchnic_art", "splanchnic_vein",
    ),
    "legs": (
        "lower_body_art", "thigh_vein", "calf_vein", "foot_vein", "ivc",
        # The IVC split keeps all three segments where the lumped IVC already was.
        # NOTE THIS IS ANATOMICALLY QUESTIONABLE — the IVC is abdominal, not a leg
        # vessel — but moving it would shift the regional blood-volume figures the
        # leg rebuild's stage 2 is aimed at, so it is left for that stage to decide
        # deliberately rather than changed here as a side effect.
        "ivc_renal", "ivc_infrarenal",
    ),
}


def region_volumes(V: np.ndarray) -> dict[str, float]:
    """Sum compartment volumes (mL) into the BODY_REGIONS zones."""
    return {region: float(sum(V[IDX[name]] for name in names))
            for region, names in BODY_REGIONS.items()}


# Compartments whose unstressed volume (V0) is modulated by venous tone
# (drug venous_tone_factor × baroreflex v0_vein_factor): venoconstriction
# (factor < 1) lowers V0, recruiting blood centrally; venodilation (> 1) raises
# V0, pooling blood.
#
# Applied to the MOBILIZABLE VENOUS RESERVOIR (splanchnic + upper-body/cutaneous
# beds). This is the physiology: sympathetic venoconstriction recruits chiefly
# the splanchnic capacitance bed (Rothe 1983; Gelman 2008 — PMID 18362606,
# DOI 10.1097/ALN.0b013e3181672607, Anesthesiology 108(4):735-48, the review
# that sets out the compliant/noncompliant two-compartment split this tuple
# implements), while the caval
# conduits, renal, and muscle/limb veins contribute little actively mobilizable
# volume. With physiological venous compliance (compartments.py) the recruited
# slug lands in a ~1.6 L stressed pool, so a ±15 % tone change moves CO ~±13 %.
MOBILIZABLE_VENOUS_RESERVOIR = ("splanchnic_vein", "upper_body_vein")
_VENOUS_TONE_IDX = frozenset(IDX[name] for name in MOBILIZABLE_VENOUS_RESERVOIR)

# Which drainage paths `venous_resistance_factor` acts on — backlog item 70.
#
# THE WHOLE SYSTEMIC VENOUS PATH, and that is DELIBERATELY WIDER than
# _VENOUS_TONE_IDX above. Resistance to venous return is measured as a
# whole-path quantity: Maas and de Wit both obtain it from the slope of a venous
# return curve built by inspiratory holds, which sees every vessel between the
# filling-pressure point and the right atrium. Restricting the factor to the two
# mobilizable compartments would make the model's Rvr respond to a fraction of
# the bed the sources measured.
#
# THE ASYMMETRY WITH _VENOUS_TONE_IDX IS A KNOWN DEFECT, NOT A DESIGN. Venous
# smooth muscle tone changes unstressed volume AND cross-sectional area together
# — Maas 2013 says so explicitly — so one drug should act on one anatomy through
# both arms. That the tone arm reaches only splanchnic and upper-body veins is
# backlog items 9 and 64, and when that set widens these two should become one.
# Recorded here so the inconsistency is visible rather than inherited.
#
# The PULMONARY vein also drains through R_drain and is deliberately excluded:
# it is not part of systemic venous return.
_VENOUS_DRAIN_IDX = frozenset(IDX[name] for name in VENOUS_RESERVOIR)

# Beds carrying the TRANSIENT limb venous arm — Samueloff 1966 (PMID 5903943),
# HUMAN. These are deliberately DISJOINT from MOBILIZABLE_VENOUS_RESERVOIR, and
# the disjointness is the physiology rather than a convenience.
#
# **TWO BEDS, TWO TIME COURSES, ONE DRIVE.** Samueloff measured limb capacity
# vessels at constant volume through 4 min of 70 deg head-up tilt: they constrict,
# peak at 27 s, and are back at baseline by 133 s while the RESISTANCE vessels of
# the same limb stay constricted throughout. The splanchnic bed is not measured
# there and sustains its response in this model, which is what orthostatic venous
# return depends on. So the mobilizable reservoir gets `v0_vein_factor` (sustained)
# and these get `v0_vein_limb_factor` (transient).
#
# **DRUGS DO NOT REACH THESE BEDS, and that is unchanged.** `venous_tone_factor`
# and the shared alpha1 stage still act only on _VENOUS_TONE_IDX. Samueloff's
# finding is about the REFLEX; Pang and Bell both have limb veins largely passive
# to circulating drug. So registration 007's result — that the model cannot
# recruit pooled leg blood with a pressor — still stands, and backlog items 9 and
# 64 are untouched by this.
#
# WHY A TRANSIENT ARM CHANGES NOTHING AT THE ENDPOINT, which is itself a measured
# constraint. Brown, Wood & Lampert 1949 (cited by Samueloff): under ganglionic
# blockade the volume ultimately displaced to the legs on tilting was NOT
# increased, only the RATE of filling rose. Because this factor returns to 1.0
# while the tilt continues, the settled leg volume is unchanged by construction —
# the arm can only alter how fast the legs fill. That is asserted, not assumed.
TRANSIENT_VENOUS_BEDS = ("thigh_vein", "calf_vein", "foot_vein")
_VENOUS_LIMB_IDX = frozenset(IDX[name] for name in TRANSIENT_VENOUS_BEDS)

# Every compartment whose pressure comes from the vascular (compliance) law —
# i.e. everything except the four elastance-driven cardiac chambers.
#
# DERIVED, NOT LISTED, and that is the point. Until 2026-10-04 `_odes` iterated a
# HAND-WRITTEN list of 19 indices. A compartment missing from it keeps a pressure
# of exactly zero for the whole run while flows still pour into it — the
# "mechanism silently inert" class this project has hit eleven times. The IVC
# split added two compartments and both had to be remembered by hand; deriving
# the set means the next one cannot be forgotten.
_CARDIAC_CHAMBERS = ("right_atrium", "right_ventricle", "left_atrium", "left_ventricle")
_VASCULAR_IDX = tuple(idx for name, idx in IDX.items() if name not in _CARDIAC_CHAMBERS)


# Compartments that lie inside the chest and are therefore surrounded by pleural
# pressure. ITP is added to their intraluminal pressure in _odes().
#
# The governing principle is that intrathoracic pressure is a *uniform external
# pressure*. A uniform pressure applied around a closed elastic system produces
# no internal flow — it can only drive flow where a vessel crosses the chest
# wall, because that is the only place a pressure step exists. So the membership
# of this set is not a tuning knob: it fixes *where the boundaries are*, and any
# compartment wrongly left out creates a spurious ITP-driven gradient at an
# internal junction that has no business carrying one.
#
# Anatomy, and the boundaries that follow:
#   arterial out : aorta and brachiocephalic (innominate) are mediastinal →
#                  boundaries at aorta→abdominal_aorta (aortic hiatus) and
#                  brachiocephalic→upper_body_art (thoracic outlet)
#   venous in    : the SVC is entirely intrathoracic → boundary at
#                  upper_body_vein→svc, at the thoracic outlet
#   the IVC is NOT included: only its last 2–3 cm are intrathoracic, so the
#                  boundary belongs at ivc→right_atrium, where it already is
#   coronary     : epicardial, inside the pericardium
#
# Until 2026-08-25 the aorta, brachiocephalic, SVC and coronary were all
# omitted, which put the entire ITP swing across the *aortic valve* — an
# internal junction, where it acted as a spurious respiratory modulation of
# ejection. Its magnitude scaled with 1/VALVE_R, so it was largely hidden at
# VALVE_R = 0.08 and grew eightfold when the valve rebuild dropped VALVE_R to
# 0.01, taking normovolaemic PPV to 43 %. Removing it drops PPV to 32.6 % at an
# unchanged transmission fraction. Note it inflated STROKE-VOLUME variation, not
# the pressure-to-volume ratio: PPV tracks the model's own `sv` 1:1 both before
# and after (1.02 and 0.98). See docs/validation_log.md, "PPV diagnosed".
THORACIC_COMPARTMENTS = (
    "aorta", "brachiocephalic", "svc", "coronary",
    "right_atrium", "right_ventricle",
    "pulmonary_art", "pulmonary_cap", "pulmonary_vein",
    "left_atrium", "left_ventricle",
)
_THORACIC_IDX = tuple(IDX[name] for name in THORACIC_COMPARTMENTS)

# Ventricular phase held during a circulatory arrest. `_normalised_activation`
# returns EXACTLY 0.0 for any phase >= 0.45, so this is true diastole and both
# ventricles sit at E_min. 0.90 is chosen well clear of that boundary.
_ARREST_PHASE = 0.90

_ORIFICE_K = {v: orifice_k(v) for v in ("mitral", "aortic", "tricuspid", "pulmonic")}
_NO_ORIFICE = {v: None for v in _ORIFICE_K}

# Compartments that lie inside the ABDOMINAL cavity. Like
# THORACIC_COMPARTMENTS this is ANATOMY, NOT A KNOB, and the same argument
# applies: abdominal pressure is a uniform external pressure, so around a closed
# elastic system it produces no internal flow. Membership fixes WHERE THE
# BOUNDARIES ARE, and the boundaries are the diaphragm (the IVC crossing into
# the chest) and the pelvic brim (the iliac vessels leaving for the legs).
# A compartment wrongly included or left out invents a pressure step at an
# internal junction.
#
#   abdominal_aorta   retroperitoneal, diaphragm to the iliac bifurcation
#   renal_art/vein    retroperitoneal
#   splanchnic_art    mesenteric
#   splanchnic_vein   portal, mesenteric AND HEPATIC — the mobilizable reservoir,
#                     and the compartment through which this mechanism does its
#                     work. **THE LIVER IS INSIDE IT.** Declared explicitly on
#                     2026-09-10 (Jesper) because the model had never decided:
#                     this line used to read "portal and mesenteric", which
#                     EXCLUDES the liver, while no other compartment contained
#                     any hepatic blood. A healthy adult carries ~618 mL there
#                     (11.3 % of total blood volume, Kiszka-Kanowitz 2001,
#                     PMID 11690706), so the ambiguity was worth 600 mL and made
#                     the model's abdominal excess unquotable — +703 or +1322 mL
#                     depending on the reading. It is now the former.
#                     CONSEQUENCE FOR ANY FUTURE SPLIT: a separate liver
#                     compartment goes in SERIES (gut -> liver -> IVC), not in
#                     parallel, so it would insert resistance into the venous
#                     return path. See backlog item 46.
#   ivc               runs from the iliac confluence to the diaphragm at T8. The
#                     intrathoracic segment above the diaphragm is ~1 cm and is
#                     not separately represented, so the compartment is abdominal
#
# The leg veins (thigh, calf, foot) and lower_body_art are BELOW the pelvic
# brim and are excluded — they are the reason the abdominal pressure produces
# net flow at all, because they sit outside the pressurised cavity.
# upper_body_* and svc are above the diaphragm.
ABDOMINAL_COMPARTMENTS = (
    "abdominal_aorta", "renal_art", "renal_vein",
    "splanchnic_art", "splanchnic_vein", "ivc",
    # All three IVC segments are infra-diaphragmatic and intra-abdominal, from the
    # iliac confluence to the diaphragm. Membership is anatomy, not a knob.
    "ivc_renal", "ivc_infrarenal",
)
_ABDOMINAL_IDX = tuple(IDX[name] for name in ABDOMINAL_COMPARTMENTS)

# ---------------------------------------------------------------------------
# THE LEGS, which pivot at the hip — backlog item 53 (2026-10-05)
# ---------------------------------------------------------------------------
# Membership is anatomy: the leg arteries and the three leg vein segments. The
# infrarenal IVC is abdominal and moves with the trunk.
LEG_COMPARTMENTS = ("lower_body_art", "thigh_vein", "calf_vein", "foot_vein")
_LEG_NAMES = frozenset(LEG_COMPARTMENTS)

# WHERE THE HIP IS: `SimParams.hip_height_m`, default HIP_HEIGHT_M from
# compartments.py (Winter Fig 4.1, greater trochanter at 0.530H). Scaled with
# stature by build_patient_params, like every compartment height.


# ---------------------------------------------------------------------------
# Simulation parameters dataclass
# ---------------------------------------------------------------------------

class SimParams:
    """
    All parameters needed for one simulation run.

    Attributes are intentionally public so the API layer can patch
    individual values before passing to run_simulation().
    """

    def __init__(self, compartments=None):
        self.compartments = compartments or default_compartments()

        # Heart rate baseline (bpm) — baroreflex adjusts around this
        self.hr_bpm = 70.0

        # Cardiac elastance parameters (multiplicative factors applied after patient scaling)
        self.lv_emax = LV_EMAX
        # Ventricular diastole: the Klotz curve (heart.py). Volumes in mL;
        # scaled with chamber size by apply_cardiac.
        self.lv_v0_dia = LV_V0_DIA
        self.lv_v30    = LV_V30
        # The pericardium (heart.py THE PERICARDIUM): its own structure, with a
        # capacity, a stiffness and a fluid content. Off until measured; capacity
        # scales with heart size in apply_cardiac. pericardial_fluid_ml is EXCESS
        # fluid (the normal film is inside the capacity): > 0 is an effusion, and
        # with the sac on, a tamponade.
        self.pericardium_enabled = False
        self.pericardial_capacity_ml = PERI_CAPACITY
        self.pericardial_k_mmhg = PERI_K
        self.pericardial_vk_ml = PERI_VK
        self.pericardial_fluid_ml = 0.0
        # Re-zeroes the reflex's CVP input to its resting value when the sac is on.
        self.reflex_cvp_offset = 0.0
        # Ventricular activation (heart.py VENTRICULAR ACTIVATION): Senzaki's measured
        # human shape timed in SECONDS (Weissler QS2 - Manolas EMD). True = the
        # unsourced fraction-of-beat curve, kept only for comparison runs.
        self.legacy_ventricular_activation = False
        self.ventricular_t_max_scale = VENTRICULAR_T_MAX_SCALE   # heart.py, grade E pinned
        # AORTIC CHARACTERISTIC IMPEDANCE (mmHg s/mL) — 2026-10-10. In series between
        # the aortic valve and the aortic compliance: the LV ejects against ROOT
        # pressure (node + Zc x flow). Without it the model's pulse pressure was made
        # by an unphysiological ejection (peak aortic flow 924 mL/s vs ~560 in man,
        # Carlsson 2004 Fig 3). GRADE C, PINNED: Framingham men measure 0.14 (Nayor
        # 2023, PMID 37850464) as a WAVE quantity; a lumped resistor is not a wave
        # impedance, so the value is pinned from invasive-equivalent central PP
        # (McEniery 2005 + Cheng 2013) and peak aortic flow together. See the sweep
        # in validation_log 2026-10-10. Central SBP/DBP are reported at the ROOT; MAP
        # and the baroreflex stay at the elastic NODE, because a lumped series Zc puts
        # a mean pressure drop (Zc x mean flow) that real large arteries do not have.
        self.aortic_zc = AORTIC_ZC
        self.rv_emax = RV_EMAX
        self.rv_emin = RV_EMIN
        self.la_emax = LA_EMAX
        self.la_emin = LA_EMIN
        self.ra_emax = RA_EMAX
        self.ra_emin = RA_EMIN

        # Posture / gravity
        self.tilt_start_deg  = 0.0                     # degrees from horizontal
        self.tilt_end_deg    = 0.0
        self.tilt_onset_s    = 0.0
        self.tilt_duration_s = 5.0
        # Hip flexion: legs relative to the trunk, degrees, positive = legs
        # raised off a flat table. Shares the tilt's onset and ramp. Zero leaves
        # every result bit-for-bit as before (backlog item 53).
        #   leg raise from flat:        trunk 0,      flexion 0 -> 45
        #   semi-recumbent:             trunk 0 -> 45, flexion 0 -> 45 (legs stay flat)
        #   leg raise from semi-recumb: trunk 45 -> 0, flexion 45 (constant)
        self.hip_flexion_start_deg = 0.0
        self.hip_flexion_end_deg   = 0.0
        # Hip pivot, metres from the heart along the body axis (negative =
        # footward). Scaled with stature via apply_cardiac.
        self.hip_height_m          = HIP_HEIGHT_M
        self.gravity         = GravityEnvironment.EARTH  # m/s²

        # Drug effects (merged multiplicative factors)
        self.drug_factors = dict(NEUTRAL_FACTORS)

        # Baroreflex on/off
        self.baroreflex_enabled = True
        # Cardiopulmonary (filling-pressure) arm of the heart-rate reflex.
        # Its own switch so it can be validated alone and in combination.
        self.cardiopulmonary_hr_enabled = True

        # DEMAND PACING, beats/min, or None for no pacemaker. A LOWER RATE LIMIT:
        # the heart beats at max(native rate, paced rate), which is how AAI and
        # DDD pacing behave — the pacemaker fires only when the native rhythm
        # falls below its set rate.
        #
        # WHY IT EXISTS. Switching the baroreflex off is the only other way to
        # hold heart rate still, and it also removes the reflex's VASCULAR arms.
        # Pacing removes the rate response and leaves the vessels alone, which is
        # what a paced patient has. Most patients are paced after cardiac surgery,
        # and Juhl-Olsen 2023 (PMID 37186094) — the cleanest phenylephrine study
        # in the ledger — paced 25 of 30 at 80-90 /min.
        #
        # None is the identity: no code path changes, so every existing run is
        # bit-for-bit unchanged.
        self.paced_hr_bpm = None

        # Reflex OUTFLOW and end-organ RESPONSIVENESS — backlog item 70. See
        # the note in baroreflex.py. All exactly 1.0 by default, which is the
        # identity: every run is bit-for-bit what it was before these existed.
        # Outflow scales act before the end-organ saturation (a drug that cuts
        # nerve traffic); responsiveness acts after it (an end organ that
        # answers less, as with age).
        self.sympathetic_outflow_scale = 1.0
        self.vagal_outflow_scale       = 1.0
        self.reflex_responsiveness     = None   # dict, keys as DEFAULT_REFLEX_RESPONSIVENESS
        # RESTING SYMPATHETIC VENOUS TONE — item 70 pass 2. The fraction of
        # DENERVATED mobilizable venous unstressed volume that resting tone holds
        # back. `sympathetic_outflow_scale` withdraws it, so a sympatholytic
        # venodilates at rest, which nothing could do before. Calibrated against a
        # three-source convergence on the fall in mean circulatory filling pressure
        # when tone is removed (Hahn -13.8 %, de Wit -23.3 %, Appleton -26 %).
        # See VENOUS_RESTING_TONE in baroreflex.py. 0.0 is the exact identity.
        self.venous_resting_tone       = B_VENOUS_RESTING_TONE

        # Frank-Starling on/off
        self.frank_starling_enabled = True

        # SVR scaling factor from patient.py (applied to arterial resistances)
        self.svr_scale = 1.0

        # Muscle pump — calf squeeze driving venous return.
        # Default 0 = inactive (sedated/anaesthetised patients).
        # Walking: pressure ≈ 35–50 mmHg, freq ≈ 0.5–1.0 Hz.
        self.muscle_pump_pressure = 0.0   # mmHg peak calf compression
        self.muscle_pump_freq_hz  = 0.5   # Hz contraction frequency

        # Ventilation — respiratory-cardiovascular coupling.
        # mode 'none'        : ITP = 0, no RSA (default, sedated/apnoeic)
        # mode 'spontaneous' : negative-pressure breathing; ITP swings −5 to −13 cmH₂O
        # mode 'mechanical'  : positive-pressure PPV; ITP swings PEEP → PIP
        self.ventilation_mode = 'spontaneous'  # 'none' | 'spontaneous' | 'mechanical'
        self.resp_rate_bpm    = 14.0     # breaths/min (8–25 typical)
        self.peep_cmh2o       = 5.0      # cmH₂O — PEEP for mechanical ventilation
        self.pip_cmh2o        = 20.0     # cmH₂O — peak inspiratory pressure
        self.ie_ratio         = 0.33     # inspiratory fraction (0.33 = 1:2 I:E)

        # ---- Ventilatory hold (Berger 2016's venous-return manoeuvre) -------
        # Cyclic inspiration is a half-sine, so there is no plateau to read a
        # venous return curve against. A hold steps airway pressure to a square
        # plateau and keeps it there. Read the result at ~9 s: Berger places his
        # window at 9-12 s explicitly BEFORE sympathetic vasoconstriction, which
        # shows up about 10 s later. Reading at 45-60 s measures the reflex, not
        # the vasculature -- it flattened the model's venous return slope from
        # -0.456 to -0.280. See backlog item 47.
        self.hold_start_s        = None     # s, or None for no hold
        self.hold_duration_s     = 0.0      # s
        self.hold_mode           = 'inspiratory'   # 'inspiratory' | 'expiratory'
        self.hold_pressure_cmh2o = None     # plateau; None -> pip_cmh2o

        # ---- Circulatory arrest (Schipke 2003's fibrillation sequences) -----
        # Stops cardiac ejection so arterial and venous pressures converge
        # towards the static filling pressure. Implemented by PINNING the
        # ventricular phase in diastole, where `_normalised_activation` is
        # exactly zero (it returns 0 for phase >= 0.45), so both ventricles
        # become passive chambers at E_min and no ejection occurs.
        #
        # WHY IT IS WORTH HAVING. Schipke JD et al. 2003, Am J Physiol Heart
        # Circ Physiol 285:H2510-H2515, measured 82 anaesthetised supine
        # patients (age 59 +/- 10) through 323 fibrillation/defibrillation
        # sequences of 13 +/- 2 s. That is the only direct human measurement of
        # the approach to static filling pressure, and it yields TIME CONSTANTS
        # rather than a single number -- which is what actually constrains the
        # arterial and venous compliances. See backlog item 47.
        #
        # CAVEAT ON VF vs ASYSTOLE. Schipke's patients are in VENTRICULAR
        # FIBRILLATION, where the myocardium keeps some disorganised tone; this
        # implementation is a FLACCID diastolic arrest. `arrest_activation`
        # exposes that assumption -- 0.0 is flaccid, and a small positive value
        # stiffens the chambers as fibrillating muscle would. Do not tune it to
        # fit an endpoint.
        self.arrest_start_s    = None   # s, or None for no arrest
        self.arrest_duration_s = 0.0    # s
        self.arrest_activation = 0.0    # 0 = flaccid diastole

        # ---- Valsalva strain (backlog item 29) ------------------------------
        # A forced expiration against a closed glottis. NOT routed through the
        # ventilation path: see `valsalva_itp_mmhg` for why the pleural
        # transmission differs from positive-pressure ventilation's 0.376.
        # Standard bedside manoeuvre is 40 mmHg for 15 s.
        self.valsalva_start_s     = None   # s, or None for no strain
        # LOWER BODY NEGATIVE PRESSURE — a sealed tank at the iliac crests. A
        # negative external pressure on LEG_COMPARTMENTS, applied exactly like
        # intrathoracic pressure on the thorax (intraluminal = transmural +
        # external). Until 2026-10-08 LBNP was imitated by a bleed (500 mL ~
        # -30 mmHg, PMID 27702883) — an equivalence fitted on the sac-free model,
        # so circular once the heart changes. lbnp_mmhg < 0; ramped over
        # lbnp_ramp_s; held until lbnp_end_s (None = to the end).
        self.lbnp_mmhg   = 0.0
        self.lbnp_start_s = 0.0
        self.lbnp_end_s   = None
        self.lbnp_ramp_s  = 5.0
        self.valsalva_duration_s  = 15.0   # s
        self.valsalva_mmhg        = 40.0   # mouth pressure held

        # Abdominal pressure driven by the same diaphragm descent that raises
        # pleural pressure (backlog item 27). Mechanical ventilation only — see
        # ABDOMINAL_TRANSMISSION in respiration.py for why the spontaneous case
        # has the opposite sign and is deliberately not modelled. Its own switch
        # so the mechanism can be validated in isolation.
        self.abdominal_coupling_enabled = True

        # The four valves, each independently settable. Before 2026-08-31
        # mitral and aortic shared left_ventricle.resistance and could not be
        # varied apart, which blocked the left-heart coupling work in item 25a.
        # See the note above the constants in compartments.py.
        # A heart valve is an orifice, not a pipe: dP goes as Q^2, not Q. OFF by
        # default so it changes nothing until deliberately switched on — see the
        # ORIFICE VALVE FLOW note in compartments.py.
        self.valve_orifice_enabled = False

        self.tricuspid_r = TRICUSPID_R
        self.pulmonic_r  = PULMONIC_R
        self.mitral_r    = MITRAL_R
        self.aortic_r    = AORTIC_R

        # Hemorrhage — constant-rate blood volume loss over [start, start+duration].
        # Removed proportionally from the systemic venous reservoir (see
        # VENOUS_RESERVOIR), the compartments holding most circulating volume.
        # duration_s = 0 disables hemorrhage (default).
        self.hemorrhage_rate_mlmin  = 0.0
        self.hemorrhage_start_s     = 0.0
        self.hemorrhage_duration_s  = 0.0

        # Fluid bolus — constant-rate crystalloid infusion into the upper-body
        # venous compartment (peripheral/central IV access) over
        # [start, start+duration]. duration_s = 0 disables the bolus (default).
        self.fluid_bolus_ml         = 0.0
        self.fluid_bolus_start_s    = 0.0
        self.fluid_bolus_duration_s = 0.0

        # Slow-timescale dynamics (minutes to hours): transcapillary refill,
        # venous stress relaxation, RAAS/ADH, baroreflex resetting. See
        # model/slow_dynamics.py.
        #
        # Default ON as of 2026-08-11 (phases 1 and 2 validated; 3 and 4 still
        # to land). Deliberate decision, not a side effect of adding a phase.
        #
        # The reasoning: with this off, a simulated patient has NO mechanism
        # slower than the 20 s sympathetic baroreflex arm, so a bled patient
        # sits in fixed shock forever and any run longer than ~40 s is
        # stationary by construction. That is wrong in the direction that
        # matters clinically, and the API serves runs up to 300 s while live
        # mode runs indefinitely — precisely the horizon where the missing
        # physiology shows.
        #
        # Safe to default on because every mechanism is in DEVIATION form from
        # a reference captured at SETTLE_S, so it is exactly neutral at rest by
        # construction. `test_default_config_is_stable_at_rest` guards that at
        # the API's 300 s ceiling in the configuration users actually get.
        #
        # Set False to recover the pre-2026-08 behaviour exactly.
        self.slow_dynamics_enabled = True

        # Per-mechanism switches, gated by the master flag above. These exist so
        # each phase can be validated IN ISOLATION as well as in combination —
        # without them a test named after one mechanism silently measures the
        # sum of all of them. (Exactly that happened when Phase 2 landed: the
        # Phase 1 volume-load test jumped from 27 % to 81 % dissipation because
        # filtration had joined in.)
        self.slow_stress_relaxation_enabled = True
        self.slow_fluid_exchange_enabled    = True
        self.slow_raas_enabled              = True
        self.slow_adh_enabled               = True

        # Drug infusion window. Defaults reproduce the historical behaviour
        # exactly — drug_factors applied for the whole run — so nothing changes
        # unless a caller sets drug_stop_s.
        #
        # This exists because slow dynamics are in DEVIATION form from the state
        # captured at SETTLE_S. A drug present from t=0 is baked into that
        # reference, so the Starling balance is zeroed at the drugged state and
        # the mechanism reports no effect at all. Validating a vasopressor
        # against slow dynamics therefore *requires* starting it after settling.
        self.drug_start_s = 0.0
        self.drug_stop_s  = float("inf")

        # Seal the parameter set. Everything above is a real field; anything
        # assigned after this point is a typo or a misremembered name.
        self.__dict__["_sealed"] = True

    # ---- typo guard ------------------------------------------------------
    # WHY THIS EXISTS. `SimParams` is a plain object, so until 2026-09-15 it
    # accepted ANY attribute silently. `p.duration_s = 90.0` looks exactly like
    # setting the run length and does nothing whatsoever — run_simulation takes
    # `duration_s` as a FUNCTION ARGUMENT and defaults to 60 s. That mistake was
    # made dozens of times in one day's measurement work before anyone noticed
    # every run had been 60 s.
    #
    # It is the same bug class the repo has now hit six times: a mechanism that
    # looks live and is inert. `venous_tone_factor` assembled into a dead local,
    # `p_stiffen` silently dropped by patient scaling, the arteriole on the wrong
    # side of `*_art`, ITP across the aortic valve, PPV's missing compartments —
    # and now a parameter that was never a parameter.
    #
    # Raising here turns a silent no-op into an immediate, named failure.
    def __setattr__(self, name: str, value) -> None:
        if getattr(self, "_sealed", False) and name not in self.__dict__:
            raise AttributeError(
                f"SimParams has no field {name!r}. If you meant the run length, "
                f"that is an argument to run_simulation(params, duration_s=...), "
                f"not a field on SimParams. Setting an unknown attribute here "
                f"would have been silently ignored."
            )
        object.__setattr__(self, name, value)


def perturbation_times(params, duration_s: float) -> list[float]:
    """Every moment in this run where something is done TO the patient.

    Backlog item 33. A long run is downsampled, and downsampling is a
    block mean — which is exactly wrong at a perturbation, because the
    interesting thing there is a fast transient and the mean smears it. The fix
    is to keep full-dt data AROUND THE EVENT rather than on a clock tick, and
    for that the events have to be derived from the params rather than typed in
    by the caller. Typing them in is how they drift out of step with the
    scenario: the whole point of an event window is that it stays attached to
    the event when the scenario is edited.

    Both the ONSET and the OFFSET of every timed intervention are returned.
    Stopping a vasopressor or finishing a bolus produces its own transient, and
    the offsets are the ones a caller is most likely to forget.

    Only events that actually happen are returned — a zero-duration haemorrhage
    or a tilt that does not move contributes nothing — so passing
    `hires_around_events` to a resting run costs nothing.
    """
    times: list[float] = []

    def _add(t):
        if t is not None and 0.0 <= t <= duration_s and t not in times:
            times.append(float(t))

    # Posture. tilt_duration_s is the ramp, so the onset and the end of the ramp
    # are different events; a tilt that does not change angle is not an event.
    if params.tilt_end_deg != params.tilt_start_deg or \
            params.hip_flexion_end_deg != params.hip_flexion_start_deg:
        _add(params.tilt_onset_s)
        _add(params.tilt_onset_s + params.tilt_duration_s)

    if getattr(params, "hemorrhage_duration_s", 0.0) > 0 and \
            getattr(params, "hemorrhage_rate_mlmin", 0.0) != 0:
        _add(params.hemorrhage_start_s)
        _add(params.hemorrhage_start_s + params.hemorrhage_duration_s)

    if getattr(params, "fluid_bolus_duration_s", 0.0) > 0 and \
            getattr(params, "fluid_bolus_ml", 0.0) != 0:
        _add(params.fluid_bolus_start_s)
        _add(params.fluid_bolus_start_s + params.fluid_bolus_duration_s)

    # Drugs. drug_start_s defaults to 0.0 and drug_stop_s to +inf, so the timing
    # fields alone cannot tell an undrugged run from a drugged one — the test is
    # whether drug_factors actually deviates from neutral. _add drops drug_stop_s
    # when it is +inf because it fails the <= duration_s bound.
    _factors = getattr(params, "drug_factors", None)
    if _factors and any(_factors.get(k, v) != v for k, v in NEUTRAL_FACTORS.items()):
        _add(params.drug_start_s)
        _add(params.drug_stop_s)

    return sorted(times)


def _drug_factors_at(params, t):
    """Drug factors in force at time `t`.

    Outside [drug_start_s, drug_stop_s) the patient is undrugged. With the
    default window (0 -> inf) this returns params.drug_factors itself, so the
    common path is unchanged and costs one comparison.
    """
    start = getattr(params, "drug_start_s", 0.0)
    stop  = getattr(params, "drug_stop_s", float("inf"))
    if start <= t < stop:
        return params.drug_factors
    return NEUTRAL_FACTORS


# ---------------------------------------------------------------------------
# Pressure helpers
# ---------------------------------------------------------------------------

def _smooth_edges(x: np.ndarray, win: int) -> np.ndarray:
    """
    Moving average that does not corrupt the ends of the series.

    `np.convolve(x, kernel, mode="same")` implicitly zero-pads, so the first
    and last ~win/2 samples are pulled toward zero — the final sample of a
    pressure trace reads about half its true value. Any mean taken over the
    tail of the run (which is what the test helpers do) is then biased low.

    Partial-window mean instead: at every sample, average over however much of
    the window actually overlaps the data. Near the ends the window is shorter,
    so the result is the true mean of the available samples, and the interior
    is unchanged.

    Assuming nothing about what lies beyond the boundary matters here. Edge-value
    replication would work for a smooth trace like aortic_p but is wrong for
    co_ts, which is a spike train (nonzero only during ejection): replicating a
    boundary sample pads with either a mid-ejection spike or a diastolic zero
    depending on where the run stops in the cardiac cycle, injecting a
    phase-dependent error larger than the effects being measured.
    """
    x = np.asarray(x, dtype=float)
    if win <= 1 or x.size == 0:
        return x
    k   = np.ones(win)
    num = np.convolve(x, k, mode="same")
    den = np.convolve(np.ones_like(x), k, mode="same")
    return num / den


def _vascular_pressure(vol: float, v0: float, compliance: float,
                       p_stiffen: float | None = None) -> float:
    vs = vol - v0
    if p_stiffen is None or vs <= 0.0:
        return vs / compliance
    # Collapsible-vein tube law: stiffens above p_stiffen (see Compartment).
    return p_stiffen * (np.exp(vs / (compliance * p_stiffen)) - 1.0)


def _cardiac_pressure(vol: float, v0: float, e: float) -> float:
    return max(0.0, e * (vol - v0))


def _valve_flow(dp: float, r_lin: float, k_orifice: float | None) -> float:
    """One-way valve flow for a pressure difference `dp`.

    `k_orifice` None  -> the linear law this model has always used, Q = dp / R.
    `k_orifice` set   -> Bernoulli orifice flow, Q = K * sqrt(dp), regularised
                         as K * dp / sqrt(dp + dP_c) so the slope at dp = 0 is
                         finite. See the note in compartments.py.

    Both forms clamp at zero: these are one-way valves.
    """
    if dp <= 0.0:
        return 0.0
    if k_orifice is None:
        return dp / r_lin
    return k_orifice * dp / math.sqrt(dp + VALVE_DP_REG)


# ---------------------------------------------------------------------------
# Main ODE function
# ---------------------------------------------------------------------------

_LEG_IDX = tuple(IDX[n] for n in LEG_COMPARTMENTS)


def lbnp_now(t: float, params: SimParams) -> float:
    """External pressure of the LBNP tank at time t (mmHg, <= 0): linear ramp on
    from lbnp_start_s, held, linear ramp off at lbnp_end_s."""
    if params.lbnp_mmhg == 0.0 or t < params.lbnp_start_s:
        return 0.0
    ramp = max(params.lbnp_ramp_s, 1e-9)
    f = min(1.0, (t - params.lbnp_start_s) / ramp)
    if params.lbnp_end_s is not None and t >= params.lbnp_end_s:
        f = max(0.0, 1.0 - (t - params.lbnp_end_s) / ramp)
    return params.lbnp_mmhg * f


_CHAMBER_IDX = (IDX["right_atrium"], IDX["right_ventricle"], IDX["left_atrium"], IDX["left_ventricle"])


def _pericardial_now(V: np.ndarray, params: SimParams) -> float:
    """Sac pressure from its current contents (four chambers + excess fluid). The
    ONE formula both the ODE and the monitor use — two parallel formulas for one
    quantity is how the arrest CVP and hr_eff defects arose."""
    if not params.pericardium_enabled:
        return 0.0
    contents = float(sum(V[k] for k in _CHAMBER_IDX)) + params.pericardial_fluid_ml
    return pericardial_pressure(contents, params.pericardial_capacity_ml,
                                params.pericardial_k_mmhg, params.pericardial_vk_ml)


def _odes(t: float, V: np.ndarray, params: SimParams, baro: BaroreflexController | None,
          cardiac_phase: float, p_out: np.ndarray | None = None, slow=None,
          hr_now: float | None = None, p_tm_out: np.ndarray | None = None,
          flow_out: dict | None = None):
    """
    Compute dV/dt for the 23-compartment system.

    Parameters
    ----------
    t             : time (s)
    V             : state vector, volumes (mL)
    params        : SimParams
    baro          : BaroreflexController (or None)
    cardiac_phase : continuously-integrated ventricular cycle phase
                    (fraction of RR interval, wrapped to [0, 1) by the
                    caller). Driving elastance from this rather than
                    (t % T)/T avoids phase discontinuities when HR varies
                    every step (baroreflex/RSA).
    """
    comp  = params.compartments
    drugs = _drug_factors_at(params, t)

    # -----------------------------------------------------------------------
    # Elastance parameters (baroreflex + drug modulation)
    # -----------------------------------------------------------------------
    emax_factor = drugs.get("lv_emax_factor", 1.0)
    if baro is not None:
        emax_factor *= baro.emax_factor

    lv_emax_eff = params.lv_emax * emax_factor
    rv_emax_eff = params.rv_emax * drugs.get("rv_emax_factor", 1.0)
    if baro is not None:
        rv_emax_eff *= baro.emax_factor

    # Frank-Starling: scale E_max with EDV
    if params.frank_starling_enabled:
        edv_lv = V[IDX["left_ventricle"]]
        edv_rv = V[IDX["right_ventricle"]]
        lv_emax_eff = frank_starling_emax(lv_emax_eff, edv_lv)
        rv_emax_eff = frank_starling_emax(rv_emax_eff, edv_rv, edv_ref=100.0)

    # -----------------------------------------------------------------------
    # Instantaneous elastances, driven by the continuously-integrated
    # cardiac phase (see docstring above for why not (t % T)/T).
    # -----------------------------------------------------------------------
    t_n_v = cardiac_phase % 1.0
    # LV: systolic elastance line blended with the Klotz diastolic curve by the
    # activation e(t) — see heart.py, VENTRICULAR DIASTOLE. RV: straight line.
    e_v = ventricular_activation(cardiac_phase,
                                 hr_now if hr_now is not None else params.hr_bpm,
                                 legacy=params.legacy_ventricular_activation,
                                 t_max_scale=params.ventricular_t_max_scale)
    E_rv = (rv_emax_eff - params.rv_emin) * e_v + params.rv_emin

    # Atria fire one PR interval before the ventricles. The offset is derived
    # from a fixed PR TIME at the current rate, not a fixed fraction of the
    # cycle — see atrial_phase_offset() in heart.py.
    t_n_a = (cardiac_phase
             + atrial_phase_offset(hr_now if hr_now is not None
                                   else params.hr_bpm)) % 1.0
    E_la = elastance_from_phase(t_n_a, params.la_emax, params.la_emin)
    E_ra = elastance_from_phase(t_n_a, params.ra_emax, params.ra_emin)

    # -----------------------------------------------------------------------
    # Compute pressures for every compartment
    # -----------------------------------------------------------------------
    # Venous tone: drug venoconstriction × baroreflex venous arm, applied as a
    # multiplier on systemic venous unstressed volume (V0). See _VENOUS_TONE_IDX.
    #   < 1  venoconstriction → lower V0 → higher venous P → ↑ preload/CO
    #   > 1  venodilation     → higher V0 → venous pooling → ↓ preload/CO
    # RESTING SYMPATHETIC VENOUS TONE — item 70 pass 2. A BACKGROUND sympathetic
    # level, independent of the reflex's dynamic deviation, withdrawn by
    # `sympathetic_outflow_scale` (the sympatholytic knob from pass 1). It works
    # whether the reflex is on or off, so reflex-off still means only "no dynamic
    # modulation" and every existing reflex-off test is untouched.
    _venous_tone_rest = getattr(params, "venous_resting_tone", 0.0)
    _ks = getattr(params, "sympathetic_outflow_scale", 1.0)
    # THE SHARED ALPHA1 STAGE — item 70 pass 3. Nerves and alpha1 drugs add their
    # DRIVE into one saturating occupancy, because they compete for one receptor
    # pool. The drug's effect therefore GROWS as tone is withdrawn, which is what
    # a fixed e_max could not express: 0.10 fits awake men and 0.30 fits
    # anaesthetised patients, and neither fits both.
    #
    # Neutral where it must be. With tone intact and no alpha1 drug the factor is
    # exactly (1 - venous_resting_tone), which is what pass 2 applied.
    # Non-alpha1 venodilators (propofol, spinal) and V1 agonists (vasopressin)
    # keep their own `venous_tone_factor` and multiply on top — different
    # receptors, so they do not share this pool.
    _a1_drive = alpha1_tone_drive(_venous_tone_rest) * _ks \
        + drugs.get("alpha1_venous_drive", 0.0)
    _alpha1_factor = (1.0 - ALPHA1_VENOUS_EMAX * (_a1_drive / (1.0 + _a1_drive))
                      if _a1_drive > 0.0 else 1.0)
    vt = drugs.get("venous_tone_factor", 1.0) * _alpha1_factor
    if baro is not None:
        vt *= baro.v0_vein_factor
    # Venous COMPLIANCE, a separate degree of freedom from unstressed volume.
    # Backlog item 70. Applied to the same compartments as `vt`, so the two
    # venous mechanisms act on the same anatomy and widen together if
    # _VENOUS_TONE_IDX ever widens.
    #   > 1  more compliant → the same volume generates LESS pressure
    #   < 1  stiffer        → the same volume generates MORE pressure
    #
    # WHY IT EXISTS, AND IT IS NOT TO CLOSE A GAP. Mean systemic filling
    # pressure is stressed volume divided by compliance, so a fall in filling
    # pressure under anaesthesia can come from V0 RISING or from C RISING, and
    # the two are indistinguishable from filling pressure alone. Measured on
    # Hahn 2022's Table 1 (validation_log.md, 2026-09-27): a 13.8 % fall in
    # stressed volume and a 16.0 % rise in compliance produce exactly the same
    # observed fall. Until 2026-09-27 the model had ONLY the V0 knob, so it was
    # forced to attribute every venous drug effect to unstressed volume — and it
    # was credited or blamed for the whole of it on that basis three times
    # (propofol against de Wit, phenylephrine against Bell, the spinal block).
    #
    # THIS IS AN IDENTIFIABILITY FIX. It lets de Wit 2016 — which reports MSFP,
    # Rvr, Ra, CVP, CO and SVV at three propofol levels — discriminate the two
    # mechanisms, instead of us choosing one because it is the only one
    # expressible. NO DRUG SETS IT YET, deliberately: every PD function returns
    # 1.0 until a source says otherwise.
    vc = drugs.get("venous_compliance_factor", 1.0)
    # Venous RESISTANCE — the third venous degree of freedom, backlog item 70.
    #   > 1  more resistance (venoconstriction narrows the vessel)
    #   < 1  less resistance (venodilation widens it)
    # NOTE THE CONVENTION IS NOT INVERTED, unlike `venous_tone_factor`. Three
    # venous factors now exist and they do not share one sign rule:
    #   venous_tone_factor        < 1 = constriction  (it multiplies V0)
    #   venous_compliance_factor  < 1 = stiffer
    #   venous_resistance_factor  > 1 = constriction  (it multiplies resistance)
    # The first is the odd one out and CLAUDE.md already warns about it.
    #
    # WHY IT EXISTS, AND IT IS MEASURED FROM BOTH DIRECTIONS IN HUMANS.
    # de Wit 2016 (PMID 27199311): deepening propofol lowered mean systemic
    # filling pressure 23 % while cardiac output held (-3.5 %, NS), because
    # resistance to venous return fell 30 % alongside it. Maas 2013
    # (PMID 23128382): noradrenaline raised Rvr x1.50 against Rsys x1.34. Both
    # measured Rvr from a venous-return-curve slope built by inspiratory holds,
    # which is the protocol tools/venous_return_curve.py reproduces.
    #
    # AND IT IS NEEDED BY AN IMPOSSIBILITY, not just by a shortfall. Measured
    # 2026-09-27: to reproduce de Wit, cardiac output must fall only 0.15 times
    # as fast as filling pressure. Unstressed volume alone gives 1.15 and
    # compliance alone 0.78, so EVERY non-negative mixture of the two lands in
    # [0.78, 1.15] and none can reach 0.15. A resistance arm is the only way out.
    # Full record in docs/validation_log.md, 2026-09-27.
    #
    # NO DRUG SETS IT YET. The sources above give magnitudes; applying them is a
    # separate change with its own validation run.
    vr = drugs.get("venous_resistance_factor", 1.0)

    i = IDX
    P = np.zeros(len(comp))

    # Vascular compartments
    for idx in _VASCULAR_IDX:
        c = comp[idx]
        in_venous_tone_set = idx in _VENOUS_TONE_IDX
        # RE-BASELINE FOR RESTING TONE — item 70 pass 2. The tabulated V0 was set
        # for a circulation whose resting venous tone was zero, so it IS the
        # resting value. With a resting tone the table must describe the
        # DENERVATED vessel instead, which is larger by 1/(1 - tone); the reflex
        # then holds it back down to the tabulated value at rest. At tone 0 this
        # divides by 1.0 and the model is bit-for-bit unchanged.
        #
        # GANGLIONIC BLOCKADE is `sympathetic_outflow_scale = 0`, which removes the
        # tone term from `vt` and leaves V0 at the denervated value. That is what
        # Appleton 1986 measured and what the calibration is checked against.
        v0 = ((c.unstressed_volume / (1.0 - _venous_tone_rest)) * vt
              if in_venous_tone_set else c.unstressed_volume)
        # THE TRANSIENT LIMB ARM — Samueloff 1966. Disjoint from the tone set, so
        # this never double-applies with `vt`. No resting re-baselining is needed
        # because the arm is a HIGH-PASS: once the drive settles, its tracker has
        # caught up and the factor is exactly 1.0, so the resting operating point
        # is untouched and only a CHANGE in drive moves these beds.
        if baro is not None and idx in _VENOUS_LIMB_IDX:
            v0 *= baro.v0_vein_limb_factor
        compliance = c.compliance * vc if in_venous_tone_set else c.compliance
        # Venous stress relaxation (slow_dynamics.py) adds a slowly-varying
        # offset to unstressed volume: sustained distension lets the wall creep,
        # accommodating volume at lower pressure. Zero at rest and when slow
        # dynamics are disabled.
        if slow is not None:
            v0 += slow.v0_relax_ml[idx]
        P[idx] = _vascular_pressure(V[idx], v0, compliance, c.p_stiffen)

    # Cardiac chambers (time-varying elastance)
    P[i["left_ventricle"]] = max(0.0,
        e_v * lv_emax_eff * (V[i["left_ventricle"]] - comp[i["left_ventricle"]].unstressed_volume)
        + (1.0 - e_v) * klotz_diastolic_pressure(V[i["left_ventricle"]], params.lv_v0_dia, params.lv_v30))
    P[i["right_ventricle"]] = _cardiac_pressure(V[i["right_ventricle"]], comp[i["right_ventricle"]].unstressed_volume, E_rv)
    P[i["left_atrium"]]     = _cardiac_pressure(V[i["left_atrium"]],     comp[i["left_atrium"]].unstressed_volume,     E_la)
    P[i["right_atrium"]]    = _cardiac_pressure(V[i["right_atrium"]],    comp[i["right_atrium"]].unstressed_volume,    E_ra)
    # The pericardial sac presses on all four chambers (heart.py). Cavity
    # pressure = wall pressure + sac pressure; flows see the cavity pressure.
    if params.pericardium_enabled:
        _pp = _pericardial_now(V, params)
        for _c in _CHAMBER_IDX:
            P[_c] += _pp

    # -----------------------------------------------------------------------
    # Tilt angle at current time  (computed first — needed for positional ITP)
    # -----------------------------------------------------------------------
    tilt = smooth_tilt_profile(
        t,
        params.tilt_start_deg, params.tilt_end_deg,
        params.tilt_onset_s, params.tilt_duration_s,
    )
    g = params.gravity

    # -----------------------------------------------------------------------
    # Intrathoracic pressure (ITP) — two additive components:
    #
    # 1. Respiratory ITP (oscillatory): cyclic pleural pressure from breathing.
    #    Applied only when ventilation_mode != 'none'.
    #
    # 2. Positional ITP (DC): a pleural pressure rise in head-down tilt. ZERO
    #    since 2026-10-04 — Drummond & Martin 1978 measured no change at 15 deg
    #    (see POSITIONAL_ITP_K_MMHG in gravity.py). Kept as a hook.
    #
    # Combined effect on cross-boundary flows:
    #   Venous return:  Q_SVC/IVC → RA = (P_SVC/IVC − (P_RA_tm + ITP)) / R
    #     → ITP_resp negative (spontaneous insp.) → venous return ↑ ✓
    #     → ITP_resp positive (PPV insp.)          → venous return ↓ ✓
    #     → ITP_pos would offset the head-down venous-return benefit; it is
    #       zero by default (see above)
    #   Intra-thoracic flows: ITP cancels between both thoracic sides ✓
    #
    # NOTE: an earlier version of this comment said the aorta was deliberately
    # EXCLUDED from the ITP set. That has been false since 2026-08-25 — the
    # aorta, brachiocephalic, SVC and coronary were all added, because leaving
    # them out put the whole pleural swing across the aortic valve and scaled it
    # with 1/VALVE_R. See the THORACIC_COMPARTMENTS note in CLAUDE.md.
    # -----------------------------------------------------------------------
    itp_resp = (
        intrathoracic_pressure(
            t, params.ventilation_mode, params.resp_rate_bpm,
            params.peep_cmh2o, params.pip_cmh2o, params.ie_ratio,
            params.hold_start_s, params.hold_duration_s,
            params.hold_mode, params.hold_pressure_cmh2o,
        )
        if params.ventilation_mode != 'none' else 0.0
    )
    itp_pos   = positional_itp_mmhg(tilt)
    itp_vals  = valsalva_itp_mmhg(t, params.valsalva_start_s,
                                  params.valsalva_duration_s, params.valsalva_mmhg)
    itp_total = itp_resp + itp_pos + itp_vals

    # TRANSMURAL SNAPSHOT — taken BEFORE any external pressure is applied.
    # The Starling balance is across the capillary WALL, and the interstitium
    # sits at the SAME external pressure as the vessel it surrounds, so an
    # external pressure cancels from (P_c - P_i) and must not reach the
    # filtration code. Lundvall 1989 (cited in Lundvall 1993, PMID 8475742)
    # measured that transmission of external negative pressure to limb tissue
    # is "total or almost total, regardless of tissue depth" — so the tank
    # pressure is applied to both sides in life, and to neither here.
    # What DOES drive filtration under LBNP is the DISTENSION: blood flows in,
    # venous transmural pressure rises, and that rise is already in this array.
    if p_tm_out is not None:
        p_tm_out[:] = P

    if itp_total != 0.0:
        for _ti in _THORACIC_IDX:
            P[_ti] += itp_total

    # Lower body negative pressure on the legs (SimParams.lbnp_mmhg).
    if params.lbnp_mmhg != 0.0:
        _lb = lbnp_now(t, params)
        if _lb != 0.0:
            for _li in _LEG_IDX:
                P[_li] += _lb

    # -----------------------------------------------------------------------
    # Abdominal pressure — the other half of the same diaphragm (item 27)
    # -----------------------------------------------------------------------
    # The ventilator pushes the diaphragm DOWN, which raises pleural pressure
    # AND pressurises the abdomen. Modelling only the thoracic half leaves the
    # venous-return gradient falling by the full pleural swing, when in a real
    # ventilated patient much of that fall is cancelled by the abdominal
    # reservoir being squeezed at the same time. van den Berg 2002 measured the
    # consequence directly: airway pressure to 19 cmH2O raised right atrial
    # pressure from 8.1 to 15.4 mmHg and cardiac output did not change.
    #
    # itp_resp ONLY, never itp_total. The positional term is Trendelenburg,
    # whose abdominal pressure comes from abdominal contents shifting cephalad
    # under gravity — a different mechanism, with no sourced coefficient, and
    # certainly not this one. See ABDOMINAL_TRANSMISSION in respiration.py for
    # why this is also restricted to mechanical ventilation.
    if params.abdominal_coupling_enabled and itp_resp != 0.0 \
            and params.ventilation_mode == 'mechanical':
        p_abd = ABDOMINAL_TRANSMISSION * itp_resp
        for _ai in _ABDOMINAL_IDX:
            P[_ai] += p_abd

    flexion = smooth_tilt_profile(
        t, params.hip_flexion_start_deg, params.hip_flexion_end_deg,
        params.tilt_onset_s, params.tilt_duration_s,
    )
    hip_h = params.hip_height_m

    def hdp(idx_name: str) -> float:
        """Hydrostatic delta (mmHg) for this compartment at current posture.
        Leg compartments pivot at the hip (item 53); with zero flexion this is
        exactly the single-angle tilt."""
        if idx_name in _LEG_NAMES:
            return articulated_hydrostatic_delta_mmhg(
                comp[IDX[idx_name]].height_m, tilt, flexion, hip_h, g)
        return hydrostatic_delta_mmhg(comp[IDX[idx_name]].height_m, tilt, g)

    # -----------------------------------------------------------------------
    # SVR scaling (baroreflex + drug)
    # -----------------------------------------------------------------------
    svr_factor = params.svr_scale * drugs.get("svr_factor", 1.0)
    if baro is not None:
        svr_factor *= baro.svr_factor
    if slow is not None:
        # Angiotensin II + AVP. Exactly 1.0 at rest, so this cannot shift
        # baseline haemodynamics; it engages only as arterial pressure falls
        # below the resting reference.
        svr_factor *= neurohumoral_svr_factor(slow)

    def R(idx_name: str, systemic_arterial: bool = False) -> float:
        r = comp[IDX[idx_name]].resistance
        return r * svr_factor if systemic_arterial else r

    # -----------------------------------------------------------------------
    # Postcapillary resistance — backlog item 18
    # -----------------------------------------------------------------------
    # The alpha-1 postcapillary effect does NOT act here. It shifts the pre/post
    # split WITHIN the exchange segment, which moves capillary pressure without
    # moving flow, and is applied in slow_dynamics.capillary_pressure_fraction().
    # It was briefly applied to the venous drainage resistance instead; that is the
    # wrong site (drainage is downstream of the venous compartment, so raising it
    # chokes venous return) and it is not applied to any resistance here now.
    #
    # The division of labour: `svr_factor` above scales the whole exchange segment
    # — the common arteriolar + venular rise — while `postcap_factor` carries only
    # the differential, that the venular response is steeper than the arterial one.
    def R_drain(idx_name: str) -> float:
        """Venous drainage resistance for an exchange bed.

        Reads `drain_resistance`, which is a separate field from `resistance` so
        that the exchange segment and the drainage path can be set independently
        (see the note on Compartment.drain_resistance).
        """
        idx = IDX[idx_name]
        r = comp[idx].drain_resistance
        return r * vr if idx in _VENOUS_DRAIN_IDX else r

    # -----------------------------------------------------------------------
    # Flows (mL/s) — Q > 0 means forward flow
    # One-way valve: max(Q, 0) for cardiac valve positions
    # -----------------------------------------------------------------------

    # Systemic arterial tree
    # Hydrostatic correction: Q = (P_up - P_down + hdp(upstream) - hdp(downstream)) / R
    # Positive hdp(up) - hdp(down) when going downhill (increases flow); negative when uphill.
    # Conduit arteries carry no arteriolar resistance and are NOT drug-scaled; the
    # arteriolar resistance (and with it `svr_factor`) now lives on the artery→vein
    # exchange segment, which is where the arterioles physically are. See the
    # placement note in compartments.py.
    Q_ao_brachio  = (P[i["aorta"]] - P[i["brachiocephalic"]] + hdp("aorta") - hdp("brachiocephalic")) / R("brachiocephalic")
    Q_brachio_ub  = (P[i["brachiocephalic"]] - P[i["upper_body_art"]] + hdp("brachiocephalic") - hdp("upper_body_art")) / R("upper_body_art")
    Q_ub_art_vein = (P[i["upper_body_art"]] - P[i["upper_body_vein"]] + hdp("upper_body_art") - hdp("upper_body_vein")) / R("upper_body_vein", True)
    # Every exchange bed now owns both its own numbers: `resistance` is its
    # arteriole + exchange segment, `drain_resistance` its outflow. (This one used
    # to read svc.resistance, leaving upper_body_vein.drain_resistance defaulting
    # to the 3.80 arteriolar value and looking like a drainage figure.)
    Q_ub_vein_svc = (P[i["upper_body_vein"]] - P[i["svc"]] + hdp("upper_body_vein") - hdp("svc")) / R_drain("upper_body_vein")

    Q_ao_abd      = (P[i["aorta"]] - P[i["abdominal_aorta"]] + hdp("aorta") - hdp("abdominal_aorta")) / R("abdominal_aorta")
    Q_abd_renal   = (P[i["abdominal_aorta"]] - P[i["renal_art"]] + hdp("abdominal_aorta") - hdp("renal_art")) / R("renal_art")
    Q_renal_vein  = (P[i["renal_art"]] - P[i["renal_vein"]] + hdp("renal_art") - hdp("renal_vein")) / R("renal_vein", True)
    Q_abd_splanch = (P[i["abdominal_aorta"]] - P[i["splanchnic_art"]] + hdp("abdominal_aorta") - hdp("splanchnic_art")) / R("splanchnic_art")
    Q_splanch_vein= (P[i["splanchnic_art"]] - P[i["splanchnic_vein"]] + hdp("splanchnic_art") - hdp("splanchnic_vein")) / R("splanchnic_vein", True)
    Q_abd_lb      = (P[i["abdominal_aorta"]] - P[i["lower_body_art"]] + hdp("abdominal_aorta") - hdp("lower_body_art")) / R("lower_body_art")

    # Capillary inflow from lower body arteries to each venous segment (30/40/30% split).
    # The old single lower_body_vein used R=0.30 (outflow resistance) for the art→vein flow,
    # giving total arteriocapillary R_total=0.30. Split across three parallel branches:
    #   R_to_thigh = 0.30/0.30 = 1.00,  R_to_calf = 0.30/0.40 = 0.75,  R_to_foot = 0.30/0.30 = 1.00
    # Equivalent parallel resistance = 1/(0.30+0.40+0.30) * 0.30 = 0.30 ✓
    # Leg arteriolar + exchange resistances now live in the compartment table
    # (see the leg-vein block in compartments.py), so the patient SVR calibration
    # and the PAD factor can reach them. Drug-scaled like every other arteriolar
    # segment.
    Q_lb_art_thigh = (P[i["lower_body_art"]] - P[i["thigh_vein"]] + hdp("lower_body_art") - hdp("thigh_vein")) / R("thigh_vein", True)
    Q_lb_art_calf  = (P[i["lower_body_art"]] - P[i["calf_vein"]]  + hdp("lower_body_art") - hdp("calf_vein"))  / R("calf_vein", True)
    Q_lb_art_foot  = (P[i["lower_body_art"]] - P[i["foot_vein"]]  + hdp("lower_body_art") - hdp("foot_vein"))  / R("foot_vein", True)

    # Muscle pump: rhythmic calf compression drives venous return.
    # sin²(2πft) profile: always ≥ 0 (no suction phase), smooth, periodic.
    # pump_p = 0 when muscle_pump_pressure = 0 → identical to current model.
    pump_p = 0.0
    if params.muscle_pump_pressure > 0:
        pump_p = params.muscle_pump_pressure * np.sin(2 * np.pi * params.muscle_pump_freq_hz * t) ** 2

    # Venous drainage: foot→calf→thigh→ivc.
    # max(0,...) implements anatomical one-way venous valves — prevents retrograde flow
    # that would otherwise occur when hydrostatic gradient exceeds driving pressure.
    # Pump boost applied to foot→calf and calf→thigh (calf contraction zone).
    Q_foot_calf  = max(0.0, (P[i["foot_vein"]]  - P[i["calf_vein"]]  + hdp("foot_vein")  - hdp("calf_vein")  + pump_p) / R_drain("foot_vein"))
    Q_calf_thigh = max(0.0, (P[i["calf_vein"]]  - P[i["thigh_vein"]] + hdp("calf_vein")  - hdp("thigh_vein") + pump_p) / R_drain("calf_vein"))
    Q_thigh_ivc  = max(0.0, (P[i["thigh_vein"]] - P[i["ivc_infrarenal"]] + hdp("thigh_vein") - hdp("ivc_infrarenal")) / R_drain("thigh_vein"))

    # THE IVC AS THREE SEGMENTS — backlog items 65 and 72, 2026-10-04.
    # Each tributary joins the segment at ITS OWN height, so none is charged a
    # climb to a fictitious centroid, and every flow now carries its height term
    # so the hydrostatic loop telescopes to zero around every circuit. The IVC is
    # valveless, so the segment-to-segment flows have no one-way guard.
    Q_infra_renalseg = (P[i["ivc_infrarenal"]] - P[i["ivc_renal"]] + hdp("ivc_infrarenal") - hdp("ivc_renal")) / R_drain("ivc_infrarenal")
    Q_renalseg_supra = (P[i["ivc_renal"]]      - P[i["ivc"]]       + hdp("ivc_renal")      - hdp("ivc"))       / R_drain("ivc_renal")

    # These two drains carried NO height term until 2026-10-04, deliberately:
    # applying it at the lumped IVC's centroid opposed splanchnic drainage by
    # 1.41 mmHg at -15 deg and broke head-down tilt. With the IVC split, each joins
    # at its own level and the term is correct.
    Q_renal_ivc   = (P[i["renal_vein"]]      - P[i["ivc_renal"]] + hdp("renal_vein")      - hdp("ivc_renal")) / R_drain("renal_vein")
    Q_splanch_ivc = (P[i["splanchnic_vein"]] - P[i["ivc"]]       + hdp("splanchnic_vein") - hdp("ivc"))       / R_drain("splanchnic_vein")

    # Right heart inflows — one-way valves prevent retrograde venous flow.
    # Without the max(0,...) guard, positive ITP (mechanical PPV) can raise
    # P_RA above P_SVC/IVC and drive blood backward through the great veins.
    # These junctions are NOT valves — see VENOATRIAL_R in compartments.py. The
    # max(0, ...) guard is retained deliberately: it substitutes for venous collapse,
    # which the great veins do not model (backlog item 11), and without it positive
    # ITP under PPV drives blood backward up the great veins without limit.
    Q_svc_ra = max(0.0, (P[i["svc"]] - P[i["right_atrium"]] + hdp("svc") - hdp("right_atrium")) / R_drain("svc"))
    Q_ivc_ra = max(0.0, (P[i["ivc"]] - P[i["right_atrium"]] + hdp("ivc") - hdp("right_atrium")) / R_drain("ivc"))

    # Valve law: None per valve means the linear form. See valve_orifice_enabled.
    _k = _ORIFICE_K if params.valve_orifice_enabled else _NO_ORIFICE

    # Tricuspid valve (RA → RV)
    Q_tricuspid = _valve_flow(P[i["right_atrium"]] - P[i["right_ventricle"]], params.tricuspid_r, _k["tricuspid"])
    # Pulmonic valve (RV → PA)
    Q_pulmonic  = _valve_flow(P[i["right_ventricle"]] - P[i["pulmonary_art"]], params.pulmonic_r, _k["pulmonic"])

    # Pulmonary circulation
    Q_pa_cap    = (P[i["pulmonary_art"]] - P[i["pulmonary_cap"]]) / R("pulmonary_cap")
    Q_cap_pv    = (P[i["pulmonary_cap"]] - P[i["pulmonary_vein"]]) / R("pulmonary_vein")

    # Mitral valve (PV → LA → LV)
    # Pulmonary veins → LA: continuous, no valve. A wedge catheter reads LA pressure
    # precisely because of this.
    Q_pv_la     = max(0.0, (P[i["pulmonary_vein"]] - P[i["left_atrium"]]) / R_drain("pulmonary_vein"))
    Q_mitral    = _valve_flow(P[i["left_atrium"]] - P[i["left_ventricle"]], params.mitral_r, _k["mitral"])
    # Aortic valve (LV → aorta). Never aorta.resistance — that is the systemic
    # arterial resistance, not a valve.
    # Aortic valve and characteristic impedance in SERIES: Q = valve(dp - Zc * Q),
    # solved by bisection (the valve law is monotone). Zc = 0 -> the old law exactly.
    _dp_ao = P[i["left_ventricle"]] - P[i["aorta"]] + hdp("left_ventricle") - hdp("aorta")
    if params.aortic_zc > 0.0 and _dp_ao > 0.0:
        _lo, _hi = 0.0, _dp_ao / params.aortic_zc
        for _ in range(40):
            _mid = 0.5 * (_lo + _hi)
            if _valve_flow(_dp_ao - params.aortic_zc * _mid, params.aortic_r, _k["aortic"]) > _mid:
                _lo = _mid
            else:
                _hi = _mid
        Q_aortic = 0.5 * (_lo + _hi)
    else:
        Q_aortic = _valve_flow(_dp_ao, params.aortic_r, _k["aortic"])
    if flow_out is not None:
        flow_out["aortic"] = Q_aortic

    # Coronary (aorta → coronary → right atrium)
    Q_ao_cor    = (P[i["aorta"]] - P[i["coronary"]] + hdp("aorta") - hdp("coronary")) / R("coronary", True)
    Q_cor_ra    = (P[i["coronary"]] - P[i["right_atrium"]] + hdp("coronary") - hdp("right_atrium")) / R("right_atrium") * 0.1

    # -----------------------------------------------------------------------
    # dV/dt for each compartment
    # -----------------------------------------------------------------------
    dV = np.zeros(len(comp))

    dV[i["aorta"]]           = Q_aortic - Q_ao_brachio - Q_ao_abd - Q_ao_cor
    dV[i["brachiocephalic"]] = Q_ao_brachio - Q_brachio_ub
    dV[i["upper_body_art"]]  = Q_brachio_ub - Q_ub_art_vein
    dV[i["upper_body_vein"]] = Q_ub_art_vein - Q_ub_vein_svc
    dV[i["svc"]]             = Q_ub_vein_svc - Q_svc_ra
    dV[i["abdominal_aorta"]] = Q_ao_abd - Q_abd_renal - Q_abd_splanch - Q_abd_lb
    dV[i["renal_art"]]       = Q_abd_renal - Q_renal_vein
    dV[i["renal_vein"]]      = Q_renal_vein - Q_renal_ivc
    dV[i["splanchnic_art"]]  = Q_abd_splanch - Q_splanch_vein
    dV[i["splanchnic_vein"]] = Q_splanch_vein - Q_splanch_ivc
    dV[i["lower_body_art"]]  = Q_abd_lb - Q_lb_art_thigh - Q_lb_art_calf - Q_lb_art_foot
    dV[i["thigh_vein"]]      = Q_lb_art_thigh + Q_calf_thigh - Q_thigh_ivc
    dV[i["calf_vein"]]       = Q_lb_art_calf  + Q_foot_calf  - Q_calf_thigh
    dV[i["foot_vein"]]       = Q_lb_art_foot                 - Q_foot_calf
    dV[i["ivc_infrarenal"]]  = Q_thigh_ivc - Q_infra_renalseg
    dV[i["ivc_renal"]]       = Q_infra_renalseg + Q_renal_ivc - Q_renalseg_supra
    dV[i["ivc"]]             = Q_renalseg_supra + Q_splanch_ivc - Q_ivc_ra
    dV[i["right_atrium"]]    = Q_svc_ra + Q_ivc_ra + Q_cor_ra - Q_tricuspid
    dV[i["right_ventricle"]] = Q_tricuspid - Q_pulmonic
    dV[i["pulmonary_art"]]   = Q_pulmonic - Q_pa_cap
    dV[i["pulmonary_cap"]]   = Q_pa_cap - Q_cap_pv
    dV[i["pulmonary_vein"]]  = Q_cap_pv - Q_pv_la
    dV[i["left_atrium"]]     = Q_pv_la - Q_mitral
    dV[i["left_ventricle"]]  = Q_mitral - Q_aortic
    dV[i["coronary"]]        = Q_ao_cor - Q_cor_ra

    # -----------------------------------------------------------------------
    # Hemorrhage / fluid bolus — net volume change to the circulation
    # -----------------------------------------------------------------------
    if params.hemorrhage_duration_s > 0:
        t_end = params.hemorrhage_start_s + params.hemorrhage_duration_s
        if params.hemorrhage_start_s <= t < t_end:
            hem_rate = params.hemorrhage_rate_mlmin / 60.0  # mL/s
            stressed = np.array([
                max(0.0, V[i[name]] - comp[i[name]].unstressed_volume)
                for name in VENOUS_RESERVOIR
            ])
            total_stressed = stressed.sum()
            if total_stressed > 1e-6:
                for name, s in zip(VENOUS_RESERVOIR, stressed):
                    dV[i[name]] -= hem_rate * (s / total_stressed)

    if params.fluid_bolus_duration_s > 0:
        t_end = params.fluid_bolus_start_s + params.fluid_bolus_duration_s
        if params.fluid_bolus_start_s <= t < t_end:
            dV[i["upper_body_vein"]] += params.fluid_bolus_ml / params.fluid_bolus_duration_s

    # Expose the pressures already computed above to the caller, without
    # recomputing them. Used by the slow-dynamics clock (slow_dynamics.py),
    # whose mechanisms need compartment pressures but run on a much coarser
    # step than this ODE. No cost when p_out is None.
    if p_out is not None:
        p_out[:] = P

    return dV


# ---------------------------------------------------------------------------
# PPV helper
# ---------------------------------------------------------------------------

# Minimum samples per cardiac cycle for pulse pressure variation to be
# recoverable from a stored pressure series. See the measurement in _compute_ppv.
PPV_MIN_SAMPLES_PER_BEAT = 20


def _compute_ppv(aortic_p: np.ndarray, dt: float, hr_bpm: float,
                 resp_rate_bpm: float) -> np.ndarray:
    """
    Compute pulse pressure variation (PPV, %) time series from the aortic
    pressure waveform.

        PPV = (PP_max − PP_min) / PP_mean × 100

    where PP_max and PP_min are the largest and smallest per-beat pulse
    pressures (SBP_i − DBP_i) within one respiratory cycle.

    Only meaningful under mechanical ventilation, but the function returns
    an array of the same length as aortic_p regardless of mode. Values near
    simulation start are unreliable (< 1 full resp cycle of data).
    """
    from scipy.signal import find_peaks as _fp

    n      = len(aortic_p)
    n_card = max(1, int(60.0 / hr_bpm / dt))
    n_resp = max(1, int(60.0 / resp_rate_bpm / dt))

    if n < 2 * n_resp:
        return np.zeros(n)

    # NOT RESOLVABLE BELOW ~20 SAMPLES PER BEAT — return NaN, never a number.
    #
    # `dt` here is the sample interval of the series actually passed in, which is
    # dt * output_every when the caller has decimated. Each stored sample is then
    # a BLOCK MEAN, which blunts the systolic peak by an amount that depends on
    # where the block boundary falls against the beat. That is phase-dependent,
    # so it manufactures beat-to-beat variation that the circulation does not
    # have, and PPV reads HIGH.
    #
    # Measured 2026-09-24, same 90 s run, PPV against samples per beat:
    #     757 -> 9.62   152 -> 9.63   76 -> 9.58   38 -> 9.88
    #      25 -> 9.85    15 -> 10.40 (+8 %)   7.6 -> 12.48 (+30 %)
    # The knee sits between 15 and 25, so the floor is 20.
    #
    # NaN rather than zeros: a zero looks like a measured absence of variation,
    # which is a clinically meaningful and wrong statement. Returning a number
    # known to be 30 % high would be worse still.
    if n_card < PPV_MIN_SAMPLES_PER_BEAT:
        return np.full(n, np.nan)

    # Detect systolic peaks: above median, separated by ≥ half cardiac cycle.
    peaks, _   = _fp(aortic_p, distance=n_card // 2,
                     height=float(np.median(aortic_p)))
    # Detect diastolic troughs (local minima in the waveform).
    troughs, _ = _fp(-aortic_p, distance=n_card // 2)

    if len(peaks) < 3 or len(troughs) < 3:
        return np.zeros(n)

    # Per-beat PP = SBP_i − DBP_i (the diastolic trough immediately preceding
    # each systolic peak).
    pp_idx, pp_vals = [], []
    for p in peaks:
        pre = troughs[troughs < p]
        if len(pre) == 0:
            continue
        pp_idx.append(int(p))
        pp_vals.append(float(aortic_p[p] - aortic_p[pre[-1]]))

    if len(pp_idx) < 3:
        return np.zeros(n)

    pp_idx  = np.asarray(pp_idx,  dtype=np.intp)
    pp_vals = np.asarray(pp_vals, dtype=float)

    # For each beat, scan the surrounding ±half-respiratory-cycle beats and
    # compute PPV = (PP_max − PP_min) / PP_mean.
    half = n_resp // 2
    ppv_beats = np.zeros(len(pp_idx))
    for j, pidx in enumerate(pp_idx):
        mask   = (pp_idx >= pidx - half) & (pp_idx <= pidx + half)
        pp_win = pp_vals[mask]
        if len(pp_win) < 2:
            continue
        pp_mean = float(pp_win.mean())
        if pp_mean <= 0:
            continue
        ppv_beats[j] = (pp_win.max() - pp_win.min()) / pp_mean * 100.0

    # Interpolate per-beat PPV to every time step; clamp to [0, 100].
    ppv_ts = np.interp(np.arange(n, dtype=float), pp_idx.astype(float), ppv_beats)
    return np.clip(ppv_ts, 0.0, 100.0)


# ---------------------------------------------------------------------------
# Public simulation runner
# ---------------------------------------------------------------------------

def run_simulation(
    params: SimParams,
    duration_s: float = 60.0,
    dt: float = 0.001,
    use_baroreflex: bool = True,
    output_every: int = 1,
    hires_windows: list[tuple[float, float]] | None = None,
    hires_around_events: tuple[float, float] | None = None,
    output_path: str | None = None,
    flush_every: int = 1000,
) -> dict:
    """
    Integrate the ODE system and return time-series haemodynamic outputs.

    Returns
    -------
    dict with keys:
        t           : np.ndarray (s)
        aortic_p    : np.ndarray (mmHg) — instantaneous aortic pressure
        map         : np.ndarray (mmHg) — running 3-beat MAP approximation
        cvp         : np.ndarray (mmHg) — right atrial end-diastolic pressure
        la_pressure : np.ndarray (mmHg) — left atrial / PCWP proxy
        co          : np.ndarray (L/min) — cardiac output (LV volume decrease)
        hr          : np.ndarray (bpm)
        sv          : np.ndarray (mL)   — stroke volume
        dbp         : np.ndarray (mmHg) — diastolic aortic pressure (rolling min)
        sbp         : np.ndarray (mmHg) — systolic aortic pressure (rolling max)
        lvedp       : np.ndarray (mmHg) — LV end-diastolic pressure
        cpp         : np.ndarray (mmHg) — cerebral perfusion pressure
        cop         : np.ndarray (mmHg) — coronary perfusion pressure (DBP − LVEDP)
        buckberg    : np.ndarray        — Buckberg subendocardial viability ratio
        ppv         : np.ndarray (%)   — pulse pressure variation (mechanical vent only; zeros otherwise)
        volumes     : np.ndarray (mL, shape [n_steps, n_compartments])
    """
    from .perfusion import (cerebral_perfusion_pressure,
                            coronary_perfusion_pressure, buckberg_index)

    comp = params.compartments
    V0   = np.array([c.init_volume for c in comp], dtype=float)

    baro: BaroreflexController | None = None
    if use_baroreflex and params.baroreflex_enabled:
        baro = BaroreflexController(
            dt=dt,
            cp_hr_enabled=bool(getattr(params, 'cardiopulmonary_hr_enabled', True)),
            sympathetic_outflow_scale=params.sympathetic_outflow_scale,
            vagal_outflow_scale=params.vagal_outflow_scale,
            responsiveness=params.reflex_responsiveness,
            venous_resting_tone=getattr(params, "venous_resting_tone", 0.0),
        )

    # Slow-timescale dynamics (minutes to hours). Inert unless explicitly
    # enabled: when off, `slow_state` stays None, `_p_scratch` is never
    # allocated, and the integration loop below costs one boolean test per
    # step — behaviour is bit-for-bit identical to having no slow dynamics.
    slow_enabled = bool(getattr(params, "slow_dynamics_enabled", False))
    slow_state = init_slow_state(comp) if slow_enabled else None
    # Always allocated. `_odes` writes the compartment pressures it has ALREADY
    # computed into this array; the slow-dynamics clock reads it, and so do the
    # ventricular pressure outputs below. Filling it does not touch dV, so a run
    # with slow dynamics off stays bit-for-bit identical to one without it.
    # THIS IS THE ONLY PLACE VENTRICULAR PRESSURE IS COMPUTED. Do not add a
    # second computation in the monitoring block — that is exactly how the
    # reported heart rate came to exclude drug chronotropy (see the 2026-09-04
    # entry in docs/validation_log.md).
    _p_scratch = np.zeros(len(comp))
    _p_tm_scratch = np.zeros(len(comp))   # transmural, for the Starling balance

    t_eval = np.arange(0.0, duration_s, dt)
    n = len(t_eval)

    # ---- OUTPUT DOWNSAMPLING (backlog item 33) --------------------------------
    # Storing every 1 ms sample costs 26 GB for a 24 h run, which does not fit in
    # memory. `output_every` stores one sample per block of that many steps.
    #
    # Each stored sample is the block MEAN, not every Nth value. That distinction
    # is load-bearing: heart rate is about 1.17 Hz, so decimating to 1 Hz would
    # ALIAS the cardiac cycle and put a beat-frequency artefact into every trend.
    # Averaging is decimation with the anti-aliasing filter built in, and it is
    # also what a trend over hours should show.
    #
    # output_every=1 is the identity and every stored value is bit-for-bit what it
    # was before this existed.
    if output_every < 1:
        raise ValueError(f"output_every must be >= 1, got {output_every}")
    n_out = (n + output_every - 1) // output_every
    _blk = np.zeros(n_out)                       # samples accumulated per block
    for _i in range(n):
        _blk[_i // output_every] += 1.0

    # ---- HIGH-RESOLUTION SLICES ----------------------------------------------
    # Downsampling destroys exactly the information this project has repeatedly
    # needed: numerical drift shows as a change in waveform MORPHOLOGY, and
    # "is this sampled mid-systole or end-systole" is invisible in a trend. Keep
    # full-dt windows alongside the trend. 30 s holds ~5 breaths and ~35 beats.
    _windows = list(hires_windows) if hires_windows else []
    if hires_around_events is not None:
        _lead, _lag = hires_around_events
        _windows += [(e - _lead, e + _lag)
                     for e in perturbation_times(params, duration_s)]
    # Sort and merge overlaps, so two events close together produce one window
    # rather than duplicate rows for the same step.
    _merged = []
    for a, b in sorted((max(0.0, a), b) for a, b in _windows):
        if _merged and a <= _merged[-1][1]:
            _merged[-1] = (_merged[-1][0], max(_merged[-1][1], b))
        else:
            _merged.append((a, b))
    _hires_ranges = []
    for (a, b) in _merged:
        i0, i1 = max(0, int(a / dt)), min(n, int(b / dt))
        if i1 > i0:
            _hires_ranges.append((i0, i1))
    _hires_ranges_s = [(i0 * dt, i1 * dt) for i0, i1 in _hires_ranges]
    _hires_n = sum(i1 - i0 for i0, i1 in _hires_ranges)
    _hires_t = np.zeros(_hires_n)
    _hires_ao = np.zeros(_hires_n)
    _hires_cvp = np.zeros(_hires_n)
    _hires_vol = np.zeros((_hires_n, len(comp)))
    _hires_map = {}                              # step -> row in the hires arrays
    _row = 0
    for i0, i1 in _hires_ranges:
        for _i in range(i0, i1):
            _hires_map[_i] = _row
            _row += 1

    # ---- DISK OUTPUT (backlog item 33) ---------------------------------------
    # `output_path` writes the downsampled trend to a directory of .npy files as
    # the run proceeds, via np.lib.format.open_memmap. Two reasons, and only the
    # second is about memory:
    #
    #  1. CRASH RESILIENCE. A 24 h run takes about 9 h of wall clock. Held only in
    #     RAM, a failure at hour 8 loses everything. Rows are written as each block
    #     completes and flushed periodically, so whatever ran is on disk and
    #     readable — a truncated .npy still loads, it just has trailing zeros.
    #  2. The run becomes re-analysable later without repeating those 9 hours.
    #
    # memmap rather than a pickle or npz because it needs no extra dependency, is
    # written incrementally rather than all at the end, and loads back with a
    # plain np.load(..., mmap_mode="r").
    # Storage
    aortic_p    = np.zeros(n_out)
    ppv_acc     = np.zeros(n_out)   # PPV, accumulated in-loop (item 69)
    cvp_ts      = np.zeros(n_out)
    ra_intra_ts = np.zeros(n_out)
    ao_intra_ts = np.zeros(n_out)
    la_p_ts     = np.zeros(n_out)
    ra_mean_ts  = np.zeros(n_out)
    peri_p_ts   = np.zeros(n_out)
    lv_p_ts     = np.zeros(n_out)
    rv_p_ts     = np.zeros(n_out)
    co_ts       = np.zeros(n_out)
    hr_ts       = np.zeros(n_out)
    dbp_ts          = np.zeros(n_out)
    sbp_ts          = np.zeros(n_out)
    brachial_sbp_ts = np.zeros(n_out)
    brachial_dbp_ts = np.zeros(n_out)
    lvedp_ts    = np.zeros(n_out)
    cpp_ts      = np.zeros(n_out)
    cop_ts      = np.zeros(n_out)
    buckberg_ts = np.zeros(n_out)
    ankle_p_ts    = np.zeros(n_out)
    brachial_p_ts = np.zeros(n_out)
    volumes_ts  = np.zeros((n_out, len(comp)))

    # Slow-dynamics diagnostics. Allocated only when the mechanism is active, so
    # an ordinary run pays nothing for them and its result dict is unchanged.
    # Validation against the human haemorrhage literature is expressed in plasma
    # volume and haematocrit (Lister 1963 measures both), which blood volume
    # alone cannot supply once red cells are leaving with the bleed.
    if slow_enabled:
        plasma_vol_ts   = np.zeros(n_out)
        haematocrit_ts  = np.zeros(n_out)
        interstitial_ts = np.zeros(n_out)
        oncotic_ts      = np.zeros(n_out)

    # We step manually so baroreflex can update each step
    V = V0.copy()
    i = IDX

    # CVP: rolling minimum of RA pressure over 2 beats (end-diastolic trough).
    from collections import deque as _deque
    _cvp_win_len = max(100, int(2 * 60.0 / params.hr_bpm / dt))
    _cvp_win     = _deque([10.0] * _cvp_win_len, maxlen=_cvp_win_len)
    _cvp_rep_win = _deque([10.0] * _cvp_win_len, maxlen=_cvp_win_len)

    # DBP / SBP: rolling min / max of aortic and brachial pressure over 2 beats.
    _bp_win_len      = _cvp_win_len
    _dbp_win         = _deque([80.0]  * _bp_win_len, maxlen=_bp_win_len)
    _sbp_win         = _deque([120.0] * _bp_win_len, maxlen=_bp_win_len)
    _brachial_dbp_win = _deque([80.0]  * _bp_win_len, maxlen=_bp_win_len)
    _brachial_sbp_win = _deque([120.0] * _bp_win_len, maxlen=_bp_win_len)

    # PPV IS BUILT IN THIS LOOP AT FULL RATE — backlog item 69.
    # It used to be computed after the loop from the STORED aortic pressure,
    # which is a block mean when output_every > 1. Block averaging blunts each
    # systolic peak by an amount that depends on where the block boundary falls
    # against the beat, so it manufactures beat-to-beat variation the
    # circulation does not have. Measured: PPV read 30 % high at output_every
    # 100 and 8 % high at 50, and (before a separate dt fix) 0.00 outright.
    # A beat is therefore measured where beats exist — every step.
    _beat_hi = _beat_lo = None          # running max/min of p_ao within a beat
    _pp_hist = _deque()                 # (time, pulse pressure) per completed beat
    _ppv_now = 0.0

    # CO / SV: LV volume decrease per step (avoids HR phase-mismatch bug).
    _prev_V_lv   = V[i["left_ventricle"]]
    _beat_ejected = 0.0
    _last_t_beat  = 0.0
    sv_ts         = np.zeros(n_out)
    _sv_current   = 70.0

    # HR / E_max from previous step (1-step lag) for consistent monitoring.
    _hr_monitor   = params.hr_bpm
    _emax_monitor = params.lv_emax
    # Continuously-integrated cardiac-cycle phase (cycles, wrapped to [0,1)).
    # _cardiac_phase drives the ODE's elastances (advanced using the HR seen
    # by _odes this step); _monitor_phase drives the 1-step-lagged E_ra/E_la
    # used for CVP/PCWP monitoring (advanced using _hr_monitor). Both replace
    # (t % T)/T, which is discontinuous whenever HR varies step-to-step.
    _cardiac_phase = 0.0
    _flow_state = {"aortic": 0.0}   # last step's aortic valve flow, for the root pressure
    _monitor_phase = 0.0

    _disk = None
    if output_path is not None:
        import json
        import os as _os
        _os.makedirs(output_path, exist_ok=True)
        # ONE list, not two. The column names and the arrays they come from are
        # defined together so they cannot drift apart. They previously were two
        # hand-maintained lists — a column name list and a positional tuple in
        # the write below — and adding `ra_intraluminal` to one and not the
        # other broke the round-trip with a shape error. Same failure mode as
        # the hand-written field list that silently dropped `p_stiffen`, and the
        # reason `apply_cardiac` exists. `t` is computed per row; `map` is a
        # placeholder written after the loop because it is derived by smoothing.
        _series = [("t", None), ("aortic_p", aortic_p), ("map", None),
                   ("aortic_intraluminal", ao_intra_ts),
                   ("cvp", cvp_ts), ("la_pressure", la_p_ts), ("ra_mean", ra_mean_ts),
                   ("pericardial_p", peri_p_ts), ("co", co_ts),
                   ("hr", hr_ts), ("sv", sv_ts), ("dbp", dbp_ts),
                   ("sbp", sbp_ts), ("lvedp", lvedp_ts), ("cpp", cpp_ts),
                   ("cop", cop_ts), ("buckberg", buckberg_ts),
                   ("ankle_p", ankle_p_ts), ("brachial_p", brachial_p_ts),
                   ("brachial_sbp", brachial_sbp_ts),
                   ("brachial_dbp", brachial_dbp_ts),
                   ("ra_intraluminal", ra_intra_ts),
                   ("lv_pressure", lv_p_ts), ("rv_pressure", rv_p_ts)]
        _cols = [_nm for _nm, _ in _series]
        _disk = {
            "trend": np.lib.format.open_memmap(
                _os.path.join(output_path, "trend.npy"), mode="w+",
                dtype=np.float64, shape=(n_out, len(_cols))),
            "volumes": np.lib.format.open_memmap(
                _os.path.join(output_path, "volumes.npy"), mode="w+",
                dtype=np.float64, shape=(n_out, len(comp))),
            "cols": _cols,
        }
        with open(_os.path.join(output_path, "meta.json"), "w") as _f:
            json.dump({
                "columns": _cols,
                "compartments": [c.name for c in comp],
                "dt": dt, "duration_s": duration_s,
                "output_every": output_every,
                "n_out": n_out,
                "hires_windows": [[a, b] for a, b in _hires_ranges_s],
                "note": "trend.npy is (n_out, len(columns)); each row is the MEAN "
                        "over its block of output_every steps, not a decimated "
                        "sample. Rows after a crash are zero. The map, co, cpp, "
                        "cop and buckberg columns are derived after the run and "
                        "written once at the end, so in a CRASHED run map is "
                        "empty and co/cpp/cop/buckberg are unsmoothed block "
                        "means; everything else is correct up to n_written.",
            }, _f, indent=2)


    for step, t in enumerate(t_eval):
        _oi = step // output_every       # output block index (see output_every above)
        c_ao = comp[i["aorta"]]
        c_ra = comp[i["right_atrium"]]
        c_la = comp[i["left_atrium"]]

        # Use E_ra/E_la from PREVIOUS step's monitor phase for consistent
        # pressure monitoring. (ODE will use the CURRENT baro state computed below.)
        # _hr_monitor is the PREVIOUS step's rate, which is the one that goes
        # with _monitor_phase. hr_now is not assigned until later in this loop.
        t_n_a_monitor = (_monitor_phase + atrial_phase_offset(_hr_monitor)) % 1.0
        E_ra_now = elastance_from_phase(t_n_a_monitor, params.ra_emax, params.ra_emin)
        E_la_now = elastance_from_phase(t_n_a_monitor, params.la_emax, params.la_emin)

        p_ao = _vascular_pressure(V[i["aorta"]], c_ao.unstressed_volume, c_ao.compliance)
        p_ra = _cardiac_pressure(V[i["right_atrium"]], c_ra.unstressed_volume, E_ra_now)
        p_la = _cardiac_pressure(V[i["left_atrium"]], c_la.unstressed_volume, E_la_now)

        # CO: measure from LV volume decrease (no elastance-timing dependency).
        curr_V_lv = V[i["left_ventricle"]]
        dV_ejected = max(0.0, _prev_V_lv - curr_V_lv)  # positive during ejection
        _beat_ejected += dV_ejected
        _prev_V_lv = curr_V_lv

        # CO (instantaneous rate): ejection rate * 60/1000 for L/min
        co_ts[_oi] += dV_ejected / dt * 60.0 / 1000.0

        # SV: sum ejected volume over one actual HR-based beat
        T_beat = 60.0 / _hr_monitor
        if t - _last_t_beat >= T_beat:
            _sv_current   = _beat_ejected
            _beat_ejected = 0.0
            _last_t_beat  = t
        sv_ts[_oi] += _sv_current

        # CVP as REPORTED: end-diastolic RA trough. The baroreflex no longer reads
        # this (2026-10-09): it reads instantaneous p_ra + sac, averaged to a mean.
        _cvp_win.append(p_ra)
        p_cvp_edi = min(_cvp_win)
        # Sac pressure: added to the reported cavity pressures and to the
        # reflex input below.
        _pp_now = _pericardial_now(V, params)
        _cvp_rep_win.append(p_ra + _pp_now)
        p_cvp_rep = min(_cvp_rep_win)

        # Update baroreflex — updates hr_delta, svr_factor etc. for NEXT ODE step
        rsa_now = 0.0
        if baro is not None:
            # The reflex reads INSTANTANEOUS right atrial pressure (wall + sac,
            # no ITP); its own 2.5 s window (baroreflex.py) turns that into the
            # CYCLE MEAN. Until 2026-10-09 it read the x-descent TROUGH
            # (p_cvp_edi). Its sources measured catheter MEANS, and the trough
            # moves with waveform SHAPE: AV-plane coupling deepens the x descent,
            # which the trough read as hypovolaemia (HR 68.6 -> 80.2 in the
            # prototype, validation log 2026-10-09). Jesper: "Switch to mean RA."
            # The reference points moved by the measured mean-trough offset
            # (baroreflex.py), so the resting state is unchanged.
            # reflex_cvp_offset re-zeroes the input when the sac is on.
            _cvp_reflex = p_ra + _pp_now - params.reflex_cvp_offset
            baro.update(p_ao, 40.0, _cvp_reflex)
        if params.ventilation_mode != 'none':
            rsa_now = respiratory_sinus_arrhythmia(
                t, params.ventilation_mode, params.resp_rate_bpm, params.ie_ratio)

        # ONE heart rate: intrinsic rate × drug chronotropy, then the baroreflex,
        # then RSA. It drives _odes's elastance AND is what gets reported.
        #
        # These were two variables computed in parallel — `hr_now` for the heart
        # and `hr_eff` for the output — and they had drifted apart: `hr_eff`
        # omitted the drug chronotropy entirely. The heart beat correctly while
        # the reported rate did not move at all with a chronotropic drug, and
        # stroke volume (derived as CO / reported HR) was inflated to match.
        # Measured 2026-09-04 at epinephrine 0.30 mcg/kg/min: reported HR 48.1
        # against a true beat rate of 76.5, and SV 145.4 against a true 93.0.
        # Every drug test asserting on HR was reading a number the drug could
        # not affect. Keep this as ONE expression.
        hr_now = params.hr_bpm * _drug_factors_at(params, t).get("hr_factor", 1.0)
        if baro is not None:
            hr_now = max(30.0, min(180.0, hr_now + baro.hr_delta))
        if params.ventilation_mode != 'none':
            hr_now = max(30.0, min(180.0, hr_now + rsa_now))
        # Demand pacing: a floor on the rate, applied AFTER the reflex and RSA so
        # it overrides both when it captures. The reflex keeps running — only its
        # rate output is superseded — so its vascular arms still act.
        if params.paced_hr_bpm is not None:
            hr_now = max(hr_now, float(params.paced_hr_bpm))
        hr_eff = hr_now

        # Carry forward updated HR for next step's monitoring
        _hr_monitor   = hr_eff
        _emax_monitor = params.lv_emax * (baro.emax_factor if baro is not None else 1.0)

        # Per-beat pulse pressure, at full rate (item 69).
        if _beat_hi is None:
            _beat_hi = _beat_lo = p_ao
        else:
            if p_ao > _beat_hi: _beat_hi = p_ao
            if p_ao < _beat_lo: _beat_lo = p_ao

        # DBP / SBP tracking (rolling min / max) at the AORTIC ROOT — the catheter
        # site the invasive references measure (Cheng 2013): elastic node + Zc x
        # flow (last step's valve flow). Diastole is unaffected (no flow). PPV, MAP
        # and the reflex stay at the node (see SimParams.aortic_zc).
        _p_root = p_ao + params.aortic_zc * _flow_state["aortic"]
        _dbp_win.append(_p_root); _sbp_win.append(_p_root)
        p_dbp = min(_dbp_win)
        p_sbp = max(_sbp_win)

        # LVEDP: the passive (Klotz) pressure at the current LV volume
        p_lvedp = klotz_diastolic_pressure(V[i["left_ventricle"]], params.lv_v0_dia, params.lv_v30)

        # Current tilt for perfusion calculations
        tilt_now = smooth_tilt_profile(
            t, params.tilt_start_deg, params.tilt_end_deg,
            params.tilt_onset_s, params.tilt_duration_s,
        )

        # Ankle / brachial pressures: compartment transmural pressure,
        # hydrostatically referenced to heart level (same convention as
        # map_at_brain in perfusion.py — P_site = P_transmural − hdp(site)).
        # lower_body_art (height_m=-0.50) is the model's only lower-limb
        # arterial compartment; brachiocephalic (height_m=0.12) is the
        # proximal-arm conduit artery used as the brachial-cuff proxy.
        # See docs/avatar caveats doc for limitations of this mapping.
        c_lba = comp[i["lower_body_art"]]
        c_bc  = comp[i["brachiocephalic"]]
        p_lba = _vascular_pressure(V[i["lower_body_art"]], c_lba.unstressed_volume, c_lba.compliance)
        p_bc  = _vascular_pressure(V[i["brachiocephalic"]], c_bc.unstressed_volume, c_bc.compliance)
        _flex_now = smooth_tilt_profile(
            t, params.hip_flexion_start_deg, params.hip_flexion_end_deg,
            params.tilt_onset_s, params.tilt_duration_s,
        )
        _p_ankle = p_lba - articulated_hydrostatic_delta_mmhg(
            c_lba.height_m, tilt_now, _flex_now,
            params.hip_height_m, params.gravity)
        _p_brach = p_bc  - hydrostatic_delta_mmhg(c_bc.height_m,  tilt_now, params.gravity)
        ankle_p_ts[_oi]    += _p_ankle
        brachial_p_ts[_oi] += _p_brach
        _brachial_dbp_win.append(_p_brach)
        _brachial_sbp_win.append(_p_brach)
        brachial_sbp_ts[_oi] += max(_brachial_sbp_win)
        brachial_dbp_ts[_oi] += min(_brachial_dbp_win)

        # Respiratory ITP at this instant, for the intraluminal RA trace below.
        _itp_resp_now = (
            intrathoracic_pressure(t, params.ventilation_mode, params.resp_rate_bpm,
                                   params.peep_cmh2o, params.pip_cmh2o, params.ie_ratio,
                                   params.hold_start_s, params.hold_duration_s,
                                   params.hold_mode, params.hold_pressure_cmh2o)
            if params.ventilation_mode != 'none' else 0.0
        )

        # Positional ITP offset for CVP and LA-pressure reporting.
        # The baroreflex uses transmural CVP (mean p_ra, no ITP) — wall-stretch drives
        # the reflex, not the absolute lumen pressure. Reported CVP is absolute
        # (transmural + positional ITP), matching what a CVC catheter reads.
        # Respiratory ITP is NOT added here: clinical CVP is read at end-
        # expiration when respiratory ITP ≈ 0 (spontaneous) or PEEP baseline
        # (mechanical); the current transmural CVP already approximates this.
        itp_pos_now = positional_itp_mmhg(tilt_now)

        aortic_p[_oi]    += p_ao
        ppv_acc[_oi]     += _ppv_now
        cvp_ts[_oi]      += p_cvp_rep + itp_pos_now
        # INTRALUMINAL right atrial pressure — what a CVC transducer actually
        # traces, continuously, including the respiratory swing. `cvp` above
        # deliberately omits respiratory ITP because clinical CVP is READ at
        # end-expiration; that is the right convention for a single reported
        # number and the wrong one for a waveform. Until this existed, no model
        # output corresponded to a catheter trace, so the respiratory swing
        # could not be compared to a measurement at all (backlog items 30, 31).
        #
        # The distinction is not cosmetic. Measured against Hoff 2019
        # (PMID 31560715, 10 healthy awake supine volunteers, dCVP 3.05 mmHg),
        # the TRANSMURAL swing is 0.14 mmHg and looks 22x too small, while the
        # INTRALUMINAL swing at the same settings is 0.86 — and at a
        # physiological -3 to -4 cmH2O pleural swing it reaches 2.6-3.5, i.e.
        # on target. Comparing `cvp` to a catheter trace compares two different
        # physical quantities.
        # A Valsalva strain is included here because a catheter reads it: the
        # whole thorax is pressurised, so intraluminal RA pressure RISES during
        # the strain even as the chamber EMPTIES. That pressure-up/volume-down
        # combination is the Ferguson 1989 signature and the point of the test —
        # a model asserting pressure alone would pass while being wrong.
        _itp_vals_now = valsalva_itp_mmhg(t, params.valsalva_start_s,
                                          params.valsalva_duration_s,
                                          params.valsalva_mmhg)
        ra_intra_ts[_oi] += p_cvp_rep + itp_pos_now + _itp_resp_now + _itp_vals_now
        # INTRALUMINAL AORTIC PRESSURE — what an arterial line reads.
        # `aortic_p` above is TRANSMURAL, (V - V0)/C with no external pressure,
        # which is the right quantity to drive the baroreflex (wall stretch) and
        # the wrong one to compare with a catheter. The distinction is invisible
        # at rest, where thoracic pressure is near zero, and dominates the moment
        # it is not. In a 40 mmHg Valsalva the transmural trace shows arterial
        # pressure COLLAPSING to 4 mmHg while the intraluminal trace shows a
        # normal manoeuvre: phase I rises to 110, phase II falls to 40, phase IV
        # overshoots to 133. Same run, opposite clinical readings.
        # Added 2026-09-15 for backlog item 29, and it is the third instance of
        # this quantity-matching trap in three days — after lumen-versus-outer-
        # wall on aortic diameter and `cvp` under sustained airway holds. The
        # right atrium got `ra_intraluminal` for exactly this reason; the
        # arterial side never did, because until Valsalva nothing exercised it.
        ao_intra_ts[_oi] += p_ao + itp_pos_now + _itp_resp_now + _itp_vals_now
        la_p_ts[_oi]     += p_la + _pp_now + itp_pos_now + _itp_vals_now
        # MEAN right atrial cavity pressure over the block — what a catheter mean
        # reads (Fujimoto 2011 reports MEAN RAP). `cvp` is the x-descent trough.
        ra_mean_ts[_oi]  += p_ra + _pp_now + itp_pos_now + _itp_vals_now
        # Intrapericardial pressure as a pericardial catheter reads it: the sac's
        # own pressure plus the same thoracic terms as ra_mean, so the two compare
        # directly (tamponade equalisation, Reddy 1978). Zero sac -> pleural only.
        peri_p_ts[_oi]   += _pp_now + itp_pos_now + _itp_vals_now
        hr_ts[_oi]       += hr_eff
        dbp_ts[_oi]      += p_dbp
        sbp_ts[_oi]      += p_sbp
        lvedp_ts[_oi]    += p_lvedp + _pp_now
        cpp_ts[_oi]      += cerebral_perfusion_pressure(p_ao, tilt_now, params.gravity)
        cop_ts[_oi]      += coronary_perfusion_pressure(p_dbp, p_lvedp)
        buckberg_ts[_oi] += buckberg_index(p_dbp, p_lvedp, hr_eff, p_sbp)
        volumes_ts[_oi]  += V

        # ---- incremental disk write, when this output block completes -------
        # Written here rather than after the loop so a crash leaves the finished
        # rows on disk. See output_path above.
        if _disk is not None and (step % output_every == output_every - 1
                                  or step == n - 1):
            _c = _blk[_oi]
            _disk["trend"][_oi] = [
                (_oi * output_every + 0.5 * (_c - 1.0)) * dt if _nm == "t"
                else 0.0 if _arr is None
                else _arr[_oi] / _c
                for _nm, _arr in _series]
            _disk["volumes"][_oi] = volumes_ts[_oi] / _c
            if _oi % flush_every == 0:
                _disk["trend"].flush()
                _disk["volumes"].flush()

        # Full-dt capture inside the requested windows (backlog item 33).
        _hr_row = _hires_map.get(step)
        if _hr_row is not None:
            _hires_t[_hr_row] = t
            _hires_ao[_hr_row] = p_ao
            _hires_cvp[_hr_row] = p_cvp_rep + itp_pos_now
            _hires_vol[_hr_row] = V

        if slow_enabled:
            _rcv = slow_state.red_cell_volume_ml
            if _rcv <= 0.0:
                # Before SETTLE_S the slow reference has not been captured and
                # red cell volume is still zero. Emit NaN rather than a number
                # that looks plausible (plasma volume would read as whole blood
                # volume, haematocrit as 0).
                plasma_vol_ts[_oi]   += np.nan
                haematocrit_ts[_oi]  += np.nan
                interstitial_ts[_oi] += np.nan
                oncotic_ts[_oi]      += np.nan
            else:
                _bv = V.sum()
                _pv = max(_bv - _rcv, 1.0)
                plasma_vol_ts[_oi]   += _pv
                haematocrit_ts[_oi]  += _rcv / max(_bv, 1.0)
                interstitial_ts[_oi] += slow_state.interstitial_volume_ml
                oncotic_ts[_oi]      += oncotic_pressure_mmhg(
                    slow_state.plasma_protein_g, _pv)

        # Euler step. When slow dynamics are active, ask _odes to hand back the
        # compartment pressures it already computed (no recomputation), then
        # advance the slow state on its own coarse clock — update_slow_state()
        # returns immediately unless SLOW_DT of simulated time has elapsed.
        dV = _odes(t, V, params, baro, _cardiac_phase, _p_scratch, slow_state,
                   p_tm_out=_p_tm_scratch,
                   hr_now=hr_now, flow_out=_flow_state)

        # Ventricular pressures, taken from the array `_odes` just filled rather
        # than recomputed. `_oi` is still this step's output index.
        #
        # THESE ARE INTRALUMINAL, NOT TRANSMURAL — and that differs from `cvp`
        # next to them, so read this before comparing anything.
        # `_odes` adds the full intrathoracic pressure (respiratory + positional)
        # to every THORACIC_COMPARTMENTS entry, and both ventricles are in that
        # tuple. So these carry the pleural swing, which is why their minima go
        # slightly negative during spontaneous inspiration where
        # `_cardiac_pressure` alone is floored at zero.
        # Intraluminal is the RIGHT choice here: a conductance or fluid-filled
        # catheter reads intraluminal pressure, so these compare directly with
        # published pressure-volume loops (Richter 2021, PMID 33655769).
        # For a transmural trace, subtract the intrathoracic term.
        # The output set now carries three conventions — `cvp` transmural,
        # `la_pressure` transmural plus POSITIONAL ITP only, and these two fully
        # intraluminal. See the match-the-quantity note in the validation log.
        lv_p_ts[_oi] += _p_scratch[i["left_ventricle"]]
        rv_p_ts[_oi] += _p_scratch[i["right_ventricle"]]

        V  = V + dV * dt

        if slow_enabled:
            # Transcapillary flux is returned as a volume change rather than
            # folded into _odes: it is a slow-clock quantity (mL moved over
            # SLOW_DT), not a rate the 1 ms integrator should see.
            dV_slow = update_slow_state(
                slow_state, t, V, _p_tm_scratch, params, baro,
                postcap_factor=_drug_factors_at(params, t).get("postcap_factor", 1.0))
            if dV_slow is not None:
                V = V + dV_slow

        # Advance integrated cardiac phases for the next step.
        # During a circulatory arrest BOTH phases are PINNED in diastole, so
        # elastance sits at E_min, the heart stops ejecting, and the reported
        # pressures describe the same heart the ODE is integrating.
        #
        # **THE MONITOR PHASE USED TO KEEP RUNNING, AND THAT WAS BACKLOG ITEM 78**
        # — fixed 2026-10-01. The justification written here was that it "keeps
        # running so the output trace stays sampled at a fixed rate", and that was
        # simply wrong: output sampling is driven by `output_every` and `_oi`, and
        # `_monitor_phase` is read in exactly ONE place — the lagged E_ra/E_la used
        # for CVP and PCWP monitoring. So it never affected sampling.
        #
        # WHAT IT DID AFFECT. With the ventricular phase pinned and the monitor
        # phase still advancing, the monitor recomputed atrial elastance across a
        # full cardiac cycle while the ODE held it fixed at 0.248. The ODE's p_ra
        # was 9.638 mmHg — equal to the venous bed it drains, as zero flow
        # requires — while the monitor swept 7.77 to 17.49 and
        # `p_cvp_edi = min(_cvp_win)` reported the TROUGH, 7.772.
        # **The reported CVP during an arrest was the trough of an atrial
        # contraction the ODE was not performing, 1.87 mmHg low.**
        #
        # It is the `hr_eff` bug again (2026-09-04): two parallel computations of
        # one quantity, and the reported one drifted from the one that acts. The
        # fix is the same shape — make the two follow ONE rule.
        #
        # HOW IT WAS FOUND, worth keeping: a sustained pressure gradient with zero
        # net flow is IMPOSSIBLE, and compartment volumes were stable out to 299 s
        # of arrest. That contradiction located it. The guard in
        # tests/test_circulation.py section 41 asserts the invariant rather than
        # the number.
        _arresting = (
            params.arrest_start_s is not None
            and params.arrest_duration_s > 0.0
            and params.arrest_start_s <= t
            < params.arrest_start_s + params.arrest_duration_s
        )
        if _arresting:
            _cardiac_phase = _ARREST_PHASE
        else:
            _phase_prev = _cardiac_phase
            _cardiac_phase = (_cardiac_phase + hr_now / 60.0 * dt) % 1.0
            if _cardiac_phase < _phase_prev and _beat_hi is not None:
                # A beat just closed. Record its pulse pressure and drop
                # anything older than one respiratory cycle.
                _pp_hist.append((t, _beat_hi - _beat_lo))
                _resp_period = 60.0 / max(1e-9, params.resp_rate_bpm)
                while _pp_hist and _pp_hist[0][0] < t - _resp_period:
                    _pp_hist.popleft()
                if len(_pp_hist) >= 2:
                    _pps = [v for _, v in _pp_hist]
                    _pp_mean = sum(_pps) / len(_pps)
                    _ppv_now = (100.0 * (max(_pps) - min(_pps)) / _pp_mean
                                if _pp_mean > 0.0 else 0.0)
                    _ppv_now = min(100.0, max(0.0, _ppv_now))
                _beat_hi = _beat_lo = None
        # Pinned under arrest for the same reason as `_cardiac_phase` above —
        # item 78. One rule, both phases.
        if _arresting:
            _monitor_phase = _ARREST_PHASE
        else:
            _monitor_phase = (_monitor_phase + _hr_monitor / 60.0 * dt) % 1.0

        # Guard: volumes can't go negative; replace NaN/inf from overflow
        V = np.maximum(V, 0.0)
        if not np.all(np.isfinite(V)):
            V = np.where(np.isfinite(V), V, np.array([c.init_volume for c in comp]))

    # Smooth MAP and CO over ~3 beats to remove pulsatility.
    #
    # Edge handling matters. np.convolve(..., mode="same") ZERO-pads beyond the
    # array ends, so the first and last ~beat_win/2 samples are dragged toward
    # zero — the final sample is roughly halved (e.g. MAP reading 46 mmHg where
    # aortic_p is 84). Every downstream mean that includes the tail is then
    # biased low: `last_half()` over a 40 s run averages through ~1.5 s of
    # corrupted signal and under-reports MAP/CO by roughly 2 %.
    #
    # Replicating the edge values instead keeps the smoothed series unbiased at
    # both ends, which is also the physically sensible assumption (the signal
    # continues at its boundary value rather than dropping to zero).
    if _disk is not None:
        _disk["trend"].flush()
        _disk["volumes"].flush()
        if _hires_n:
            import os as _os
            for _nm, _a in (("hires_t", _hires_t), ("hires_aortic_p", _hires_ao),
                            ("hires_cvp", _hires_cvp), ("hires_volumes", _hires_vol)):
                np.save(_os.path.join(output_path, _nm + ".npy"), _a)

    # ---- normalise the block accumulators to means -----------------------------
    # Every series above was accumulated with += over its block; divide to get the
    # mean. With output_every=1 every block holds one sample and this is a no-op,
    # which is what makes that case bit-for-bit identical to the old behaviour.
    for _arr in (aortic_p, ppv_acc, cvp_ts, ra_intra_ts, la_p_ts, ra_mean_ts, peri_p_ts, lv_p_ts, rv_p_ts,
                 co_ts, hr_ts, sv_ts,
                 dbp_ts, sbp_ts, brachial_sbp_ts, brachial_dbp_ts, lvedp_ts,
                 cpp_ts, cop_ts, buckberg_ts, ankle_p_ts, brachial_p_ts):
        _arr /= _blk
    volumes_ts /= _blk[:, None]
    if slow_enabled:
        for _arr in (plasma_vol_ts, haematocrit_ts, interstitial_ts, oncotic_ts):
            _arr /= _blk

    # Output timebase: the CENTRE of each block, not its leading edge.
    t_out = (np.arange(n_out) + 0.5 * (_blk - 1.0)) * dt * 1.0
    t_out = np.array([(i * output_every + 0.5 * (_blk[i] - 1.0)) * dt
                      for i in range(n_out)])

    # The 3-second smoothing window is in OUTPUT samples, not raw steps.
    beat_win = max(1, int(3.0 / (dt * output_every)))
    map_ts = _smooth_edges(aortic_p, beat_win)
    co_ts  = _smooth_edges(co_ts,    beat_win)

    # PPV: only computed for mechanical ventilation (requires positive-pressure
    # ITP cycles to modulate venous return). Returns a time-series in percent.
    # PPV comes from the loop, not from the stored waveform — backlog item 69.
    #
    # It used to be reconstructed here by `_compute_ppv` from `aortic_p`, which
    # is a BLOCK MEAN when output_every > 1. Two defects followed, both silent:
    # the function sized a cardiac cycle in RAW steps and so asked find_peaks
    # for peaks farther apart than the whole array, returning zeros; and the
    # non-mechanical branch returned an array of length `n` where every other
    # series is `n_out`.
    #
    # Now each beat's pulse pressure is measured at full rate as the beat
    # happens, and PPV is accumulated and block-averaged like every other
    # series. It no longer depends on output_every at all.
    #
    # `_compute_ppv` is kept: it is the reference implementation, it is what the
    # unit test checks against, and it still works on a full-rate series.
    ppv_ts = (ppv_acc if params.ventilation_mode == 'mechanical'
              else np.zeros(n_out))

    # ---- finalise the disk copy ------------------------------------------------
    # Five columns are derived AFTER the loop by _smooth_edges: map is built from
    # aortic_p, and co/cpp/cop/buckberg are smoothed over a 3 s window. The
    # incremental writes above cannot know them, so they are written once here.
    #
    # The incremental rows are still what gives crash resilience — they hold the
    # raw block means. A run that dies mid-way therefore has correct aortic_p,
    # cvp, hr, sv and volumes, an EMPTY map column, and UNSMOOTHED co/cpp/cop/
    # buckberg. meta.json says so, and `complete` in load_run reports it.
    if _disk is not None:
        _final = {"map": map_ts, "co": co_ts,
                  "cpp": _smooth_edges(cpp_ts, beat_win),
                  "cop": _smooth_edges(cop_ts, beat_win),
                  "buckberg": _smooth_edges(buckberg_ts, beat_win)}
        for _name, _arr in _final.items():
            _disk["trend"][:, _disk["cols"].index(_name)] = _arr
        _disk["trend"].flush()

    slow_out = {} if not slow_enabled else {
        "plasma_volume":       plasma_vol_ts,
        "haematocrit":         haematocrit_ts,
        "interstitial_volume": interstitial_ts,
        "oncotic_pressure":    oncotic_ts,
    }

    return {
        **slow_out,
        "t":           t_out,
        "aortic_p":    aortic_p,
        "map":         map_ts,
        "cvp":         cvp_ts,
        "ra_intraluminal": ra_intra_ts,
        "aortic_intraluminal": ao_intra_ts,
        "la_pressure": la_p_ts,
        "ra_mean":     ra_mean_ts,
        "pericardial_p": peri_p_ts,
        "lv_pressure": lv_p_ts,
        "rv_pressure": rv_p_ts,
        "co":          co_ts,
        "hr":          hr_ts,
        "sv":          sv_ts,
        "dbp":         dbp_ts,
        "sbp":         sbp_ts,
        "lvedp":       lvedp_ts,
        "cpp":         _smooth_edges(cpp_ts,      beat_win),
        "cop":         _smooth_edges(cop_ts,      beat_win),
        "buckberg":    _smooth_edges(buckberg_ts, beat_win),
        "ankle_p":      ankle_p_ts,
        "brachial_p":   brachial_p_ts,
        "brachial_sbp": brachial_sbp_ts,
        "brachial_dbp": brachial_dbp_ts,
        "ppv":         ppv_ts,
        "volumes":     volumes_ts,
        # Full-dt slices, empty unless hires_windows was given. See item 33: a
        # trend cannot show waveform morphology, and morphology is how numerical
        # drift and mid-systole/end-systole sampling errors become visible.
        "hires": {
            "t":        _hires_t,
            "aortic_p": _hires_ao,
            "cvp":      _hires_cvp,
            "volumes":  _hires_vol,
            "windows":  [(i0 * dt, i1 * dt) for i0, i1 in _hires_ranges],
        },
    }


def load_run(path: str) -> dict:
    """Load a run written by `run_simulation(..., output_path=path)`.

    Returns the same keys as run_simulation, so analysis code does not care
    whether a run came from memory or from disk.

    Arrays are memory-mapped, so a 26 MB trend costs nothing to open and a much
    larger one is paged rather than loaded. A run that crashed part-way still
    loads: the .npy header carries the full allocated shape, and rows that never
    completed are zero. `n_written` is the count of rows that actually got a
    non-zero timestamp, which is how far the run reached.
    """
    import json
    import os

    with open(os.path.join(path, "meta.json")) as f:
        meta = json.load(f)

    trend = np.load(os.path.join(path, "trend.npy"), mmap_mode="r")
    volumes = np.load(os.path.join(path, "volumes.npy"), mmap_mode="r")
    out = {c: trend[:, i] for i, c in enumerate(meta["columns"])}
    out["volumes"] = volumes
    out["meta"] = meta

    # How far did it get? Row 0 legitimately has t = 0, so count from row 1.
    nz = np.flatnonzero(trend[1:, 0])
    out["n_written"] = int(nz[-1] + 2) if len(nz) else 1
    out["complete"] = out["n_written"] == meta["n_out"]

    hires = {}
    for nm in ("t", "aortic_p", "cvp", "volumes"):
        fp = os.path.join(path, f"hires_{nm}.npy")
        if os.path.exists(fp):
            hires[nm] = np.load(fp, mmap_mode="r")
    hires["windows"] = [tuple(w) for w in meta.get("hires_windows", [])]
    out["hires"] = hires
    return out

