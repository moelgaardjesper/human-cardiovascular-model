"""Age relations for cardiac structure and diastolic function.

WHY THIS EXISTS (backlog item 25b, 2026-08-31). The model had no age at all —
not an input, not a parameter, not referenced anywhere — while its calibration
targets were drawn from cohorts spanning 44 to 61 years. That is not a
cosmetic gap. Across that span the sources' own age tables give:

    E/A ratio            1.22 at 40-60  ->  0.96 at >=60      21 % apart
    atrial contribution  28 % at 40-55  ->  38 % at >55       36 % apart
    LAVmax indexed       36.9 (Gao, 44) ->  48.4 (Ugander, 61) 31 % apart

Those gaps are LARGER than most of the discrepancies chased in item 25a. The
model was being compared against a moving target it could not represent, and
the "left atrium is 2.4 SD too large" reading turned out to be partly an
artefact of comparing a nominally 55-year-old model against a 44-year-old
cohort.

THIS MODULE DOES ONE THING: it makes the age of every target explicit, and
lets a target measured in one cohort be restated at the model's reference age.
It does NOT yet scale model parameters with age — see the note at the bottom.

All tables are MALE where the source separates by sex, because this project
validates on male patients (see the footnote at the top of
tests/test_circulation.py).
"""

import numpy as np


# ---------------------------------------------------------------------------
# THE MODEL'S REFERENCE AGE
# ---------------------------------------------------------------------------
# 55 years, chosen because the model's chamber geometry — the structural
# backbone everything else sits on — was calibrated against Luu 2022
# (PMID 34980185), whose cohort is 55.1 +/- 8.8 in men and which at n=3206 is
# by far the largest dataset used here. Gao (n=408, age 44.4) and NORRE
# (n=449, age 45.8) supply the atrial and diastolic targets and sit about a
# decade younger; Ugander (n=21, age 61) sits half a decade older.
#
# The alternative was to anchor at ~45 and re-derive the chambers, which would
# mean recalibrating against a dataset an order of magnitude smaller. Adjusting
# the targets is the cheaper and better-supported direction.
REFERENCE_AGE_YEARS = 55.0


# ---------------------------------------------------------------------------
# SOURCED AGE RELATIONS
# ---------------------------------------------------------------------------
# Each table is (age_years, value) with the age being the MIDPOINT of the
# source's reported band. Midpoints are an approximation the sources do not
# make themselves — a band mean is not its midpoint if the age distribution
# inside it is skewed — so these are interpolations for COMPARISON, not
# measurements. Never present an interpolated value as a measured one.

# NORRE 2015 (PMID 25896355, DOI 10.1093/ehjci/jev083), Table 3, MEN.
# Bands 20-40, 40-60, >=60. The last band has no upper bound; 68 is used as a
# working midpoint given the cohort mean of 45.8 +/- 13.7.
NORRE_EA_MEN = ((30.0, 1.69), (50.0, 1.22), (68.0, 0.96))
NORRE_E_VELOCITY_MEN = ((30.0, 0.79), (50.0, 0.72), (68.0, 0.67))   # m/s
NORRE_A_VELOCITY_MEN = ((30.0, 0.50), (50.0, 0.61), (68.0, 0.73))   # m/s
NORRE_DECEL_TIME_MEN = ((30.0, 179.8), (50.0, 186.6), (68.0, 217.5))  # ms

# Alhogbani 2012 (PMID 23097384, DOI 10.1002/jmri.23881), CMR, n=120.
# Atrial contraction contribution to LV filling, as % of LV stroke volume.
# Bands <40, 40-55, >55.
ALHOGBANI_ACC = ((32.0, 15.0), (47.5, 28.0), (65.0, 38.0))          # %

# Gao 2022 (PMID 35124105, DOI 10.1016/j.ijcard.2022.01.071), Table 3, MEN.
# Decades 21-30 through 61-70, midpoints used.
GAO_LAEF_PASSIVE_MEN = ((25.5, 39.9), (35.5, 39.0), (45.5, 35.6),
                        (55.5, 29.4), (65.5, 28.5))                 # %
GAO_LAEF_BOOSTER_MEN = ((25.5, 33.3), (35.5, 36.2), (45.5, 38.7),
                        (55.5, 39.3), (65.5, 42.3))                 # %


def at_age(table, age_years: float) -> float:
    """Linearly interpolate a sourced age relation.

    Clamps outside the table's range rather than extrapolating: every relation
    here is measured over a bounded adult span, and the underlying physiology
    is not linear beyond it.
    """
    ages = np.array([a for a, _ in table], dtype=float)
    vals = np.array([v for _, v in table], dtype=float)
    return float(np.interp(float(age_years), ages, vals))


def restate_at_reference_age(table, value: float, cohort_age: float,
                             reference_age: float = REFERENCE_AGE_YEARS) -> float:
    """Move a target measured in a cohort of `cohort_age` to `reference_age`.

    Applies the RATIO of the age relation between the two ages, not its
    absolute difference, so a cohort whose absolute value differs from the
    relation's own (different modality, different population) keeps its own
    level while acquiring the relation's age dependence.

    Example: Gao measures LAEF passive 35.6 % at a cohort mean of 44.4. At the
    model's reference age of 55 the same relation gives 30.3 %, so a model at
    age 55 should be compared against ~30 %, not 35.6.
    """
    base = at_age(table, cohort_age)
    if base == 0.0:
        return value
    return value * at_age(table, reference_age) / base


# Tanaka H et al. 2000, Circulation 102(11):1270-1275, SEDENTARY men — the
# general-population arm. Central (carotid) arterial compliance relative to the
# young group, from a 45 % young-to-older difference with no significant
# difference between the middle-aged and older bands.
#
# THIS IS A RATIO, NOT AN ABSOLUTE. Tanaka measures carotid cross-sectional AREA
# compliance in mm2/mmHg; the model's `aorta.compliance` is a VOLUME compliance
# in mL/mmHg. They are not convertible without an arterial length assumption, so
# only the age ratio transfers — the same rule this project applies to
# cross-species numbers.
#
# AND IT IS A LOWER BOUND. The aorta stiffens more with age than peripheral
# elastic arteries do, which is why the aortic-to-brachial stiffness gradient
# reverses in old age. A 45 % fall measured at the carotid understates the
# aortic fall. Not corrected, because no aortic figure is in hand.
TANAKA_ARTERIAL_COMPLIANCE_SEDENTARY = ((28.0, 1.00), (50.0, 0.55), (64.0, 0.55))

# Franklin SS et al. 1997, Circulation 96(1):308-315 (PMID 9236450), Table 2,
# MALE, Group 1 — normotensive, index blood pressure 110/70, mean age 56.3.
# n=2036 from the original Framingham cohort with up to 30 years of biennial
# follow-up, subjects on antihypertensives excluded.
#
#   SBP slope  +0.47 mmHg/year        DBP slope  -0.21 mmHg/year
#   PP  slope  +0.68 mmHg/year        MAP slope  +0.016 mmHg/year
#
# THE MAP SLOPE IS THE ONE THAT SETTLES THE RESISTANCE QUESTION. At 0.016
# mmHg/year the mean pressure is essentially fixed across the adult span in
# normotensive men, while pulse pressure widens at 0.68/year. A rising systemic
# vascular resistance would raise the MEAN; a stiffening conduit widens the
# PULSE around a fixed mean. This is why the model scales arterial COMPLIANCE
# with age and not resistance.
FRANKLIN_PP_SLOPE_MALE_NORMOTENSIVE = 0.68   # mmHg per year
FRANKLIN_PP_REFERENCE_MMHG = 51.5            # the model's own PP at age 55


def pulse_pressure_at_age(age_years: float,
                          reference_age: float = REFERENCE_AGE_YEARS) -> float:
    """Expected pulse pressure (mmHg) for a normotensive man of this age."""
    return (FRANKLIN_PP_REFERENCE_MMHG
            + FRANKLIN_PP_SLOPE_MALE_NORMOTENSIVE * (age_years - reference_age))


def arterial_compliance_factor(age_years: float,
                               reference_age: float = REFERENCE_AGE_YEARS) -> float:
    """Multiplier on arterial compliance for a patient of `age_years`.

    Returns 1.0 at the reference age by construction, so the reference patient
    is untouched and only a patient of a DIFFERENT age moves.

    DERIVED FROM FRANKLIN, NOT TANAKA, and the reason matters. Total arterial
    compliance is estimated as C ~ SV/PP, so with stroke volume roughly constant
    the compliance ratio between two ages is the inverse ratio of their pulse
    pressures. Franklin's directly reported PP slope for normotensive men then
    gives the whole relation.

    | age | 25 | 30 | 40 | 55 | 65 | 80 |
    | factor | 1.66 | 1.49 | 1.25 | 1.00 | 0.88 | 0.75 |

    WHY NOT TANAKA. Tanaka's carotid measurements give a similar young-to-middle
    ratio (1.74 at 30 against Franklin's 1.49) but then go FLAT after 50 — he
    found no significant difference between his middle-aged and older bands.
    That plateau cannot be reconciled with Framingham, where pulse pressure
    rises STEEPLY after 50-60 in a cohort 100x larger with 30 years of
    follow-up. The likely explanation is the vessel: the aorta keeps stiffening
    into old age while peripheral elastic arteries plateau, which is exactly why
    the aortic-to-brachial stiffness gradient reverses with age. Tanaka measured
    the carotid. For a model whose compliance parameter is aortic, Franklin is
    the right source and Tanaka corroborates only the young end.

    CAVEAT ON THE ESTIMATOR. C ~ SV/PP is the standard two-element estimate and
    it is crude: it ignores wave reflection and treats diastolic runoff as
    negligible, both of which change with age in the same direction as the
    effect being measured. It is a ratio between two ages, which is more robust
    than either absolute value, but it is not a measurement of compliance.
    """
    ref_pp = pulse_pressure_at_age(reference_age, reference_age)
    return ref_pp / pulse_pressure_at_age(age_years, reference_age)


# ---------------------------------------------------------------------------
# CHAMBER VOLUMES AND EJECTION FRACTIONS BY AGE
# ---------------------------------------------------------------------------
# Luu JM et al. 2022 (PMID 34980185), Tables 3 and 4, MALE columns, indexed to
# BSA. n=1126 men in four bands: 35-44 (n=141), 45-54 (n=408), 55-64 (n=383),
# 65-74 (n=194). Band MIDPOINTS are used as the age coordinate.
#
# This is the same cohort the model's chamber geometry was built from, which is
# why 55 is the reference age — so these relations are self-consistent with the
# calibration rather than imported from a different population.
#
# The trends: every indexed VOLUME falls with age, stroke volumes fall with
# them, ejection fractions hold or RISE, and the mass-to-volume ratio rises
# (concentric remodelling — the chamber shrinks faster than the wall thins).
LUU_LVEDV_MEN = ((39.5, 77.0), (49.5, 75.0), (59.5, 74.0), (69.5, 69.0))  # mL/m2
LUU_LVESV_MEN = ((39.5, 30.0), (49.5, 29.0), (59.5, 28.0), (69.5, 26.0))
LUU_LVEF_MEN  = ((39.5, 61.0), (49.5, 62.0), (59.5, 62.0), (69.5, 62.0))  # %
LUU_RVEDV_MEN = ((39.5, 91.0), (49.5, 88.0), (59.5, 86.0), (69.5, 80.0))
LUU_RVESV_MEN = ((39.5, 45.0), (49.5, 42.0), (59.5, 41.0), (69.5, 37.0))
LUU_RVEF_MEN  = ((39.5, 51.0), (49.5, 53.0), (59.5, 53.0), (69.5, 54.0))

# Closed-loop transmission of an ASSIGNED chamber volume factor, measured during
# the sex work (item 32). A chamber does not keep the volume it is given — the
# circulation pushes back — so an assigned factor is only partly realised and
# the raw ratio has to be divided through by the transmission to land on target.
# Same lesson as RA_EMIN in heart.py: elastance and V0 set volume, and how much
# volume they actually get is the circulation's decision.
_VOLUME_TRANSMISSION = {"lv": 0.62, "rv": 0.71, "ra": 0.87}
# The LEFT ATRIUM IS ABSENT DELIBERATELY. Its measured transmission is NEGATIVE
# (-0.11): assigning a larger LA volume made the chamber smaller, because the
# pulmonary veins, LA and LV behave as one pooled volume. Item 32 excluded the
# LA from sex scaling for this reason and age is excluded for the same one.
# Luu's male LA does vary with age (max 36 -> 38 -> 40 -> 38 mL/m2), so this is
# a real gap, not a rounding decision. It needs item 25a's structural fix.


def chamber_age_factors(age_years: float,
                        reference_age: float = REFERENCE_AGE_YEARS) -> dict:
    """Volume and E_max factors for LV and RV at `age_years`.

    Returns the same shape SEX_CHAMBER_FACTORS uses, so the two compose:
        {"left_ventricle": {"volume": v, "emax": e}, "right_ventricle": {...}}
    All factors are exactly 1.0 at the reference age.

    `volume` is the Luu end-diastolic-volume ratio, divided by the closed-loop
    transmission so that the chamber actually LANDS near the target rather than
    at a fraction of it. `emax` is the raw ejection-fraction ratio, applied
    directly, because ESV = V0 + P_sys/E_max and the EF difference is what E_max
    carries (again following item 32).
    """
    def _factor(table, tag):
        raw = at_age(table, age_years) / at_age(table, reference_age)
        return 1.0 + (raw - 1.0) / _VOLUME_TRANSMISSION[tag]

    return {
        "left_ventricle": {
            "volume": _factor(LUU_LVEDV_MEN, "lv"),
            "emax": at_age(LUU_LVEF_MEN, age_years) / at_age(LUU_LVEF_MEN, reference_age),
        },
        "right_ventricle": {
            "volume": _factor(LUU_RVEDV_MEN, "rv"),
            "emax": at_age(LUU_RVEF_MEN, age_years) / at_age(LUU_RVEF_MEN, reference_age),
        },
    }


# ---------------------------------------------------------------------------
# WHAT THIS MODULE DELIBERATELY DOES NOT DO
# ---------------------------------------------------------------------------
# It does not scale any MODEL PARAMETER with age. That is the second half of
# item 25b and it is not attempted here, for a specific reason: the age
# relations above are all OUTPUTS (E/A, atrial contribution, emptying
# fractions), and to make an output move with age some parameter has to move.
# The 25a sweeps identified which one — lv_emin, the LV diastolic stiffness, is
# the only parameter found that moves LAEF passive — and the physiology agrees,
# since impaired LV relaxation is the accepted driver of the whole age pattern.
#
# But there is NO SOURCED lv_emin(age) RELATION in hand. Fitting one so that
# E/A comes out right would be tuning a parameter to an endpoint, which is the
# failure mode this project keeps catching. What is needed is a measured
# age relation for LV diastolic stiffness or the LV end-diastolic
# pressure-volume relation — see the WANTED list.
#
# Until then this module serves interpretation only, which is what item 25a
# actually needed: knowing that a target measured at 44 is not the same target
# at 55.


# ---------------------------------------------------------------------------
# THE BAROREFLEX AGES — backlog item 51
# ---------------------------------------------------------------------------
# **WHAT AGEING DOES TO THE REFLEX, AND THE MECHANISM IS MEASURED.**
# White 1997 (PMID 9404222), 16 young (25 +/- 3) against 16 older (68 +/- 7),
# 60 deg head-up tilt for 30 min, in one lab with one protocol:
#
#   | at 5 min of tilt        | young | older |
#   | dHR, bpm                | +15.0 | +3.6  |
#   | dDBP, mmHg (MALES)      | +7.0  | -2.5  |
#   | resting noradrenaline   | 183   | 267   |
#   | NA rise over 30 min     | +173  | +194  |
#
# **THE OLDER SUBJECTS HAVE MORE SYMPATHETIC DRIVE AND LESS EFFECT FROM IT.**
# So the age law belongs on END-ORGAN RESPONSIVENESS — the stage backlog item 70
# built — and NOT on outflow. A single lumped gain reproduces the haemodynamics
# either way and encodes the wrong mechanism. **Do not rename these factors to
# anything implying that sympathetic activation falls with age: it rises.**
#
# **ALL FIVE EFFECTORS AGE TOGETHER, and that is sourced too.** White found
# LF/HF unchanged between the groups at every time point, with total power
# falling in BOTH bands. The ageing reflex is globally quieter, not shifted
# toward sympathetic dominance, so vagal and sympathetic responsiveness move
# together and the vascular effectors move with them.
#
# **GRADE C, AND THE REASON IS THE PROVENANCE OF THE TABLE ITSELF.** Every other
# relation in this module is a measured quantity interpolated by `at_age`. This
# one is NOT: end-organ responsiveness is a MODEL quantity and White measures an
# ENDPOINT, so the table below is FITTED — the responsiveness pair that puts the
# model's age DIFFERENCE inside one SD of White's. It is one study, one lab, and
# a fit rather than a measurement.
#   **WANTED: a measured baroreflex-sensitivity-by-age relation in humans**
#   (ms/mmHg by decade, sequence method or neck chamber). That would replace the
#   fit with a sourced RATIO and put this on the same footing as
#   `arterial_compliance_factor`.
#
# **WHAT THIS DOES NOT FIX, stated so nobody reads more into it.**
# Responsiveness 1.0 is, by construction, the reflex Fritsch 1989 measured in a
# cohort of median age ~33 — the gains in `baroreflex.py` came from there.
# Normalising this law at REFERENCE_AGE_YEARS therefore asserts that Fritsch's
# 33-year-old gain IS a 55-year-old's, and it is not. Correcting THAT means
# re-levelling the whole reflex downward, which moves the haemorrhage, tilt, PLR,
# PPV and drug tests together. It is a separate and larger change, deliberately
# not smuggled in here.
#
# WHY THE TABLE IS CLAMPED RATHER THAN EXTRAPOLATED. `at_age` holds the end
# values outside 25-68, so a 20-year-old gets the age-25 factor and an
# 85-year-old the age-68 one. Baroreflex sensitivity does keep falling past 68,
# so the old end is CONSERVATIVE — it understates the deficit in the very old.
# Extrapolating a two-point fit would be worse.
# SUPERSEDED 2026-10-02 BY GRIBBIN 1971, WHICH MEASURES THIS DIRECTLY. The fit
# below is kept only as the record of what the model needed before a source
# existed, and because the comparison is informative: the fitted decline is
# 2.41x across 25-68 and the MEASURED one is 5.07x. **The fit was half as steep
# as reality.** See `_GRIBBIN_LOG10_PER_YEAR` below for what is actually used.
#
# FITTED 2026-10-02 by a JOINT solve against BOTH of White's endpoints at once —
# the age difference in tilt tachycardia AND in the diastolic response — under
# the constraint that the law passes through 1.0 at REFERENCE_AGE_YEARS. One
# knob, two independent quantities, neither of them fitted alone:
#
#   | endpoint                | model  | White  | error    |
#   | ΔHR(68) − ΔHR(25)       | −13.40 | −11.4  | −0.23 SD |
#   | ΔDBP(68) − ΔDBP(25), M  |  −6.94 |  −9.5  | +0.29 SD |
#
# The ratio across the 43 years is **2.41**, which is the order human baroreflex
# sensitivity is reported to fall over that span — so the law is not merely
# arithmetically convenient. **The RATIO is the claim here, not the two levels.**
#
# DERIVED FROM MEASURED POINTS, NOT EXTRAPOLATED. Both values sit inside a
# responsiveness sweep run at 0.6, 0.8, 1.0, 1.2, 1.4 (and 1.774 at age 25) in
# the real model, so the solve interpolates and never extends the curve. At the
# fitted young value nothing clips: svr_factor 1.667 against its 1.8 ceiling,
# hr_delta 34.8 against 45, 0.0 % of samples at any bound. **Check that again if
# these numbers move** — a clipped young arm compresses the age difference and
# silently invalidates the fit.
#
# THE AGE OFFSET THIS HAD TO OVERCOME. At EQUAL responsiveness the model already
# shows an age difference of **+3.8 mmHg** in the diastolic tilt response, and it
# points the WRONG WAY (older defending better). It comes from
# `arterial_compliance_factor`, not from the reflex: a stiffer artery turns the
# same stroke volume into a wider pulse pressure. So the reflex law has to spend
# 3.8 mmHg before it reaches zero. **Do NOT "fix" the compliance term to help
# this** — it is validated against McEniery at three decades.
WHITE_REFLEX_RESPONSIVENESS = ((25.0, 1.690), (68.0, 0.701))

# The effectors this law acts on. Keys must match
# baroreflex.DEFAULT_REFLEX_RESPONSIVENESS exactly, so a key added there and not
# here is caught by a test rather than silently left age-blind.
REFLEX_EFFECTORS = ("svr", "venous", "emax", "hr_sympathetic", "hr_vagal")


# ---------------------------------------------------------------------------
# GRIBBIN 1971 — THE MEASURED RELATION, AND IT REPLACES THE FIT ABOVE
# ---------------------------------------------------------------------------
# Gribbin, Pickering, Sleight & Peto (1971) Circ Res 29:424-431. HUMAN, n = 81
# (61 M, 20 F), aged 19-66, supine, brachial artery catheter, phenylephrine
# (Oxford) method. Age and MAP were UNCORRELATED in the cohort, which is what
# lets the two be separated:
#
#     log10 BRS = 2.47 − (0.0164 × age) − (0.0086 × MAP)   msec/mmHg
#     SE on the age coefficient ±0.0019; the authors state ±10 %.
#
# At constant MAP the pressure term cancels and the AGE RATIO is
#     BRS(a2)/BRS(a1) = 10^(−0.0164 × (a2 − a1))
# which is a SOURCED RATIO — the same shape `arterial_compliance_factor` takes
# from Franklin. **Across 25 to 68 that is 0.197, a 5.07x fall.**
_GRIBBIN_LOG10_PER_YEAR = 0.0164

# **THE SLOPE IS SOURCED. THE ANCHOR IS NOT, AND THE TWO MUST NOT BE CONFUSED.**
# Gribbin gives the RATIO between any two ages. He does not say which age the
# gains in `baroreflex.py` already represent, and that is what the anchor sets.
# **Everything Gribbin contributes is anchor-independent; only the LEVEL moves.**
#
# WHAT THE ANCHOR CANNOT BE. REFERENCE_AGE_YEARS (55) would need r(25) = 3.105,
# and measured at that value on White's 60 deg tilt `hr_delta` sits at **45.00
# with 100 % of samples against its +45 ceiling** — the reflex is pinned and the
# relation cannot be expressed at all. So the module's own convention is ruled
# out by measurement, not by preference.
#
# **TWO CANDIDATES REMAINED, AND THEY ARE DIFFERENT KINDS OF CLAIM.**
#   PROVENANCE says 33: the heart-rate gains were calibrated against Fritsch
#   1989, median age ~33, and section 28 of the suite drives the controller
#   DIRECTLY with default responsiveness, so that calibration pins r = 1.0 to
#   that cohort. Fritsch is open-loop — pressure held fixed — which is the
#   cleaner measurement.
#   BEHAVIOUR says ~25: two independent human cohorts, Schaefers (27) and the
#   LBNP series (22), both match at r = 1.0 and both OVER-respond above it.
#
# MEASURED 2026-10-02 on the decisive subset:
#   anchor 33 -> 3 failures (Schaefers dHR -20.2 and dMAP +21.5, LBNP dHR +10.3)
#   anchor 25 -> 1 marginal failure (Schaefers dTPR +634 against a floor of 650)
#
# **ANCHORED AT 27 — Schaefers' own cohort (Jesper, 2026-10-03).**
# Setting an UNSOURCED level from a study that measured the relevant population
# is calibration, not fitting. The rule this project enforces is narrower than it
# first looks: do not bend a parameter that has its OWN measurement to hit a
# downstream endpoint, and do not claim a study validates what it was used to
# set. The anchor has no independent measurement, so pinning it from data is
# exactly what should happen — and the blind phase is closed, so these studies
# are development targets by design.
#
# **THE AGE LAW REMAINS FALSIFIABLE AFTER THIS, which is why it is safe.**
# White's two age tests assert a DIFFERENCE between 25 and 68, so they test
# Gribbin's SLOPE and are anchor-independent. Using Schaefers to set the level
# does not make the law untestable; it only means Schaefers is no longer one of
# the things testing it.
#
# **AND THE TWO YOUNG COHORTS DO NOT ACTUALLY DISAGREE — measured 2026-10-03, and
# this corrected an earlier reading.** It looked as though Schaefers (27) and the
# LBNP series (22) implied different anchors, five years apart. They do not:
#
#   | anchor | Schaefers 27            | LBNP 22        |
#   |   33   | FAILS dHR and dMAP      | FAILS r = 1.45 |
#   |   25   | FAILS dTPR (r = 0.927)  | passes r= 1.12 |
#   |   27   | **PASSES all three**    | **passes 1.20**|
#
# **Schaefers pins r(27) TIGHTLY** — it fails below at 0.927 and above at 1.254 —
# **while LBNP is permissive up to about 1.20.** One is a point constraint and the
# other is a range, so a loose constraint was mistaken for a competing estimate.
# Anchor 27 satisfies both; anchor 25 satisfies only one.
_BRS_CALIBRATION_AGE = 27.0


def baroreflex_responsiveness_factor(
        age_years: float,
        reference_age: float = _BRS_CALIBRATION_AGE) -> float:
    """End-organ reflex responsiveness at `age_years`, from Gribbin's slope.

    1.0 at `_BRS_CALIBRATION_AGE` — the age at which the underlying gains were
    MEASURED — and NOT at REFERENCE_AGE_YEARS. That is the one place this module
    deliberately breaks its own convention; see the note above for why the clip
    leaves no choice.

    A RATIO, which is what transfers: Gribbin's absolute is msec/mmHg and the
    model's gain is bpm/mmHg, and converting between them needs the baseline
    pulse interval. He found no correlation between resting pulse interval and
    age, so the conversion factor is the same at both ends and the ratio carries
    over unchanged. **The absolute does not.**

    NOT EXTRAPOLATED BEYOND SENSE. Gribbin's cohort is 19-66; the relation is
    clamped to that span, so a 15-year-old gets the age-19 value and a
    90-year-old the age-66 one. Sensitivity does keep falling past 66, so the old
    end is CONSERVATIVE — it understates the deficit in the very old.
    """
    a = min(max(float(age_years), 19.0), 66.0)
    ref = min(max(float(reference_age), 19.0), 66.0)
    return 10.0 ** (-_GRIBBIN_LOG10_PER_YEAR * (a - ref))


def baroreflex_age_factors(age_years: float,
                           reference_age: float = _BRS_CALIBRATION_AGE) -> dict:
    """Per-effector responsiveness for `BaroreflexController(responsiveness=...)`.

    **EVERY EFFECTOR GETS THE SAME FACTOR, AND THAT IS PART SOURCED AND PART
    EXTRAPOLATION. Both halves are stated because they are not equally strong.**

    SOURCED, for the two heart-rate limbs. Gribbin measures the cardiac vagal
    arm, and White 1997 found LF/HF unchanged between the age groups with total
    power falling in BOTH bands — the ageing reflex is globally quieter, not
    shifted toward sympathetic dominance. So vagal and sympathetic chronotropic
    responsiveness move together, and they move with Gribbin's slope.

    EXTRAPOLATION, for `svr`, `venous` and `emax`. **Gribbin measured pulse
    interval against pressure. He did not measure the vasomotor arm at all**, so
    applying his slope there assumes the two arms age alike. White supports the
    DIRECTION — his diastolic tilt response falls from +7.0 to −2.5 mmHg across
    the same ages — but not the rate. The check that this is not absurd is that
    the resulting model lands White's diastolic endpoint within one SD; it is a
    consistency check, not an independent measurement.

    **WANTED: an age relation for the VASOMOTOR baroreflex** (muscle sympathetic
    nerve activity per mmHg, or forearm vascular resistance per mmHg, by decade).
    That would let the two arms age at their own rates instead of one.
    """
    f = baroreflex_responsiveness_factor(age_years, reference_age)
    return {k: f for k in REFLEX_EFFECTORS}
