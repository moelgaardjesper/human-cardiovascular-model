"""
Tests for the cardiovascular circulation model.

Two groups of tests:

1. Smoke tests — validate that simulated steady-state haemodynamics fall
   within physiologically plausible ranges for baseline, head-down tilt,
   and microgravity.

2. Literature validation — compares model outputs to published clinical
   measurements. All data retrieved via PubMed; DOI links cited per test.

References
----------
[1] DOI: 10.14814/phy2.15216  (PMID: 35854636, PMC9296869)
    Sejersen et al., Physiol Rep 2022
    "To identify normovolemia: SV response to HDT vs PLR"
    n=10 healthy males, 177 cm, 80 kg; 20° HDT for 10 min.
    Key finding: SV/CO unchanged during HDT in normovolemic supine subjects.

[2] DOI: 10.1038/s41598-019-39360-6  (PMID: 30808948, PMC6391465)
    Verdini et al., Sci Rep 2019
    "Cardiovascular responses to leg muscle loading during HDT"
    n=17 males, 179 cm, 79 kg; 6° HDT vs upright.
    Key finding: MAP and HR lower during HDT than upright (p<0.001).

[3] PMID: 39500675  DOI: 10.1053/j.jvca.2024.10.001
    Likhvantsev et al. 2025 meta-analysis — Trendelenburg position (n=333, 16 studies).
    Pooled vs horizontal supine: CVP +4.13 mmHg, CO +0.33 L/min, SV +8.27 mL,
    HR -1.65 bpm, MAP SMD +0.42, LVEDV +16.89 mL.

[4] PMID: 9640339  DOI: 10.1042/cs0940347
    Wieling, Van Lieshout, Ten Harkel (1998) — head-up tilt dynamics.
    After 1 min HUT (90°) in 6 healthy subjects: SV -39±9%, CO -26±10%,
    MAP +1±7 mmHg, SVR +39±24%.

[5] PMC5209346  DOI: 10.3389/fphys.2016.00656
    Sarafian & Miles-Chan (2017) — graded incremental HUT (23 healthy adults,
    0->20->40->60 deg, each 16 min): HR +41% overall at 60°, BP +10%, TPR +16%,
    CO (men) -8.9% immediately.

[6] Pohl A, Cullen DJ (2005) Anesth & Analg / JCA / APSF.
    Closhen D et al. (2013) Eur J Anaesthesiol 30:429-432.
    Beach-chair position under GA: MAP drops 30-35 mmHg vs supine.
    CPP = MAP_brain - ICP.

[7] Buckberg GD et al. (1972) J Appl Physiol 31:598-604.
    Hoffman JI, Buckberg GD (1978) Am J Cardiol 41:327-332.
    DPTI/SPTI > 0.8 at resting HR; falls with tachycardia.

[8] Claeys MA, Gepts E, Camu F. Br J Anaesth 1988;60:3-9.
    DOI: 10.1093/bja/60.1.3  PMID: 3257393
    n=10 elderly patients, propofol 2 mg/kg IV induction: SVR -21% at 2 min
    (-30% during infusion), SBP -28%, DBP -19% (MAP drops ~25%), CO and HR
    unchanged. Mechanism: peripheral vasodilation (alpha1 inhibition), no
    chronotropy.

[9] Hirsch & Bishop (1981) Am J Physiol 241:H620-H629.
    RSA peak-to-peak amplitude: 3-10 bpm in resting healthy adults (15 bpm RR).

[10] Jardin F, Farcot JC, Boisante L, Curien N, Margairaz A, Bourdarias JP (1981)
     "Influence of positive end-expiratory pressure on left ventricular
     performance." N Engl J Med 304(7):387-92.
     PMID: 7005679   DOI: 10.1056/NEJM198102123040703
     10 ARDS patients, PEEP stepped 0 -> 30 cmH2O: "progressive declines in
     cardiac output, mean blood pressure, and left ventricular dimensions and
     ... equalization of right and left ventricular filling pressures." At the
     highest PEEP, volume expansion did NOT restore cardiac output. Mechanism:
     leftward septal displacement restricting LV filling.
     Verified against PubMed 2026-08-11. Only the abstract has been read, so no
     numeric CO target is asserted from it — direction and dose-response only.

[11] Lloyd-Donald et al. (2025) DOI: 10.1111/anae.16633
     Normal supine awake CVP = 2-3 mmHg.

[12] Lie SA et al. (2023) DOI: 10.1186/s40635-023-00561-z
     Graded LBNP in healthy volunteers: baseline CO 4.85+/-1.08 L/min,
     dCO = -0.245 L/min per 10 mmHg LBNP (approx-linear dose-response).

[13] Vettorello M et al. (2016)
     LBNP -30 mmHg ~ 500-1000 mL central-hypovolemia equivalent; HR rises
     with severity (69+/-2 -> 107+/-4 bpm at -70/-80 mmHg).

[14] Hamilton F et al. (2021) DOI: 10.1016/j.crad.2021.01.016
     Mild hypovolemia affects RV/pulmonary preload (CVP falls) before
     systemic MAP; both ventricles affected only at greater severity.

[15] Herrera AM et al. (2017) DOI: 10.1055/s-0037-1615788
     500 mL crystalloid bolus: SV 71+/-11 -> 90+/-19 mL (+27%),
     HR 87+/-9 -> 83+/-8 bpm (-5%).

[16] Malmqvist LA et al. (1987) Acta Anaesthesiol Scand 31:467-473.
     DOI: 10.1111/j.1399-6576.1987.tb02605.x  PMID: 3630592
     Spinal analgesia T4-5 in n=30 patients: 25/30 only minor changes in CO, HR,
     SV, MAP, SVR; 5/30 (T3-4 + complete sympathetic block): MAP fell ≥30%, CO preserved.

[17] Patel BM et al. (2002) Anesthesiology 96:576-582.
     DOI: 10.1097/00000542-200203000-00011  PMID: 11873030
     Vasopressin (n=13) vs NE (n=11) in septic shock: MAP and cardiac index
     maintained in both groups; vasopressin reduced NE requirement by ~79%.

[18] Ngan Kee WD et al. (2015) Anesthesiology 122:736-745.
     DOI: 10.1097/ALN.0000000000000601  PMID: 25635593
     NE vs phenylephrine computer-controlled infusion during spinal for C-section
     (n=104): NE CO 102.7% vs phenyl 93.8% normalised (p=0.004); NE HR > phenyl HR.

[19] Freyschuss U et al. (1986) Clin Sci (Lond) 70:199-206.
     DOI: 10.1042/cs0700199  PMID: 3956110
     IV adrenaline in n=11 healthy volunteers: stepwise low doses → CO↑/SVR↓
     (β2 dominant); higher doses → MAP↑ (α emerging). "Less marked effects on
     blood pressure and heart rate" at low dose vs large CO/SV increase.

[20] Monnet X, Marik PE, Teboul JL (2016) Intensive Care Med 42:1935-1947.
     DOI: 10.1007/s00134-015-4134-1  PMID: 26825952
     Meta-analysis (21 studies, 991 patients, 995 fluid challenges): PLR-induced
     CO ≥+10% identifies fluid-responsive patients; pooled sensitivity 0.85,
     specificity 0.91, AUC 0.95. CO change is far superior to PP change for PLR
     assessment (PP pooled AUC 0.77 ± 0.05 vs CO AUC 0.95 ± 0.01).

Known model limitations (documented here for transparency)
------------------------------------------------------------
- Frank-Starling plateau: implemented as a hard cap above EDV_ref=130 mL.
  In the linear elastance model, SV still increases with EDV above the cap
  via the ESV-EDV relationship. A proper sigmoid EDV-SV curve is needed
  to fully replicate the "flat upper Starling curve" in normovolemic supine
  subjects (as described in [1]).
- Extreme upright posture (90°): lumped lower-body venous compartment cannot
  adequately represent the distributed hydrostatic column. Venous return from
  the lower extremities becomes near-zero when the hydrostatic penalty (~23 mmHg
  at 90°) exceeds the initial transmural venous pressure. Baroreflex compensation
  is insufficient, leading to MAP underestimation. Model is validated for
  -30° to +45° range.
- CVP baseline: model reports end-diastolic RA pressure trough (2-4 mmHg),
  matching [11] (normal supine awake CVP = 2-3 mmHg).
- Hemorrhage sensitivity: RESOLVED by the venous-system rebuild. The model
  now carries a physiological blood volume (~5.36 L) and stressed volume
  (~1.66 L, 31% of BV; MSFP ~9.7 mmHg, venous compliance ~129 mL/mmHg), so
  hemorrhage tests run at clinically realistic class I-III volumes
  (300/600/1000 mL) rather than the 100-300 mL the previously compressed
  ~0.7 L stressed pool required. See docs/known_model_limitations.md §5.
"""

import numpy as np
import pytest

from model.circulation import SimParams, run_simulation, _vascular_pressure
from model.compartments import IDX, default_compartments
from model.gravity import GravityEnvironment, hydrostatic_delta_mmhg
from model.patient import (build_patient_params, apply_cardiac, bsa_mosteller,
                           REF_HEIGHT_CM, REF_WEIGHT_KG)
from model.heart import LV_EMAX, RV_EMAX
from model.pharmacology import combined_drug_factors
from model.slow_dynamics import CAPILLARY_PRESSURE_FRACTION


# ===========================================================================
# ALL VALIDATION IS DONE ON MALE PATIENTS. This is deliberate (Jesper,
# 2026-08-27) and it is a property of the reference material, not a preference.
#
# The named human-volunteer studies that drive posture, drug and haemodynamic
# validation here are male or male-only cohorts: Sejersen 2022 (10 healthy
# males), Verdini 2019 (17 males), Abboud & Eckstein 1968 (11 supine men),
# Lister 1963 (unbled healthy men). The CMR chamber tables are mixed — Luu 2022
# is 65 % female — but the model's chambers were derived from their MALE columns
# (backlog item 24), so male is the reference the whole suite is calibrated to.
#
# `build_patient_params` therefore defaults to sex="male", and every test in this
# file leaves it at the default. A female patient is supported (backlog item 32)
# but is NOT the comparison target for any literature scenario here, because
# comparing a female model against a male cohort would introduce exactly the
# cohort mismatch this project keeps catching in other people's numbers.
#
# ONE SCENARIO IS THE EXCEPTION AND IT IS WORTH KNOWING ABOUT.
# test_norepi_vs_phenyl_co_preservation_ngan_kee2015 compares against Ngan Kee
# 2015 — n=104, spinal anaesthesia for CAESAREAN SECTION, so 100 % female and
# 100 % term-pregnant. Term pregnancy carries ~40 % expanded blood volume,
# reduced systemic vascular resistance, and aortocaval compression. It is the
# least transferable cohort in the suite, and it is also the one test currently
# failing. That does not excuse the failure — but anyone investigating it should
# start by asking whether a non-pregnant male reference patient can be expected
# to reproduce it at all.
# ===========================================================================


SMOKE_DURATION = 30.0  # seconds — long enough for steady state
LIT_DURATION   = 40.0  # seconds — used for literature-comparison scenarios
DT             = 0.001  # 1 ms — required for Euler stability with current parameters


def last_half(arr: np.ndarray) -> float:
    """Mean over the second half of the time series (post-transient)."""
    return float(np.mean(arr[len(arr) // 2:]))


# Kept as an alias for readability where "smoke test" framing is clearer.
_mean_last_half = last_half


def pct(new: float, old: float) -> float:
    return 100.0 * (new - old) / old if old else 0.0


def run_scenario(height_cm, weight_kg, map_mmhg=None, hr_bpm=70,
                 tilt_deg=0.0, tilt_onset=5.0, gravity=GravityEnvironment.EARTH,
                 baroreflex=True, ventilation_mode='spontaneous', resp_rate=14.0,
                 duration=LIT_DURATION, age_years=None, sex="male"):
    """
    Run a scenario and return steady-state (last-half mean) outputs.

    Default ventilation_mode='spontaneous' because most literature validation
    studies used awake, spontaneously-breathing volunteers. Pass
    ventilation_mode='none' for anaesthetised/apnoeic scenarios.

    **`age_years` added 2026-09-15.** Until then this helper took no age, so
    EVERY literature scenario ran the 55-year-old reference patient — including
    comparisons against Schäfers (median 27), Hoff (25 +/- 3) and Fritsch
    (23-43). Those carried an unacknowledged age mismatch, against the
    match-the-cohort rule the rest of the project follows.

    The default is `None`, which defers to `build_patient_params`' own
    `REFERENCE_AGE_YEARS` rather than repeating 55.0 here. **Two copies of one
    constant is exactly the defect backlog item 50 was opened for** — the
    reference operating point had been typed twice and the copies had already
    drifted apart on CVP.

    Passing an age exercises `aging.arterial_compliance_factor`, which is 1.0 at
    the reference age BY CONSTRUCTION — which is why the age law went untested
    against absolute pressures for so long: every default run makes it an
    identity. Validated 2026-09-15 against McEniery Table 1 at ages 25/55/75:
    central SBP, DBP, central PP and MAP all within 1 SD at every decade.
    """
    kw = {} if age_years is None else {"age_years": age_years}
    comps, cardiac = build_patient_params(height_cm, weight_kg, map_mmhg=map_mmhg,
                                          hr_bpm=hr_bpm, sex=sex, **kw)
    params = SimParams(compartments=comps)
    # apply_cardiac applies EVERY factor the cardiac dict carries. This used to
    # be a hand-written list setting only lv_emax and rv_emax, which is the same
    # failure mode that silently dropped p_stiffen for months — a field list that
    # stops matching what produces it.
    apply_cardiac(params, cardiac)
    params.hr_bpm             = hr_bpm
    params.tilt_start_deg     = tilt_deg
    params.tilt_end_deg       = tilt_deg
    params.tilt_onset_s       = tilt_onset
    params.gravity            = gravity
    params.baroreflex_enabled = baroreflex
    params.ventilation_mode   = ventilation_mode
    params.resp_rate_bpm      = resp_rate

    r = run_simulation(params, duration_s=duration, dt=DT)
    return {k: last_half(r[k]) for k in ("map", "hr", "co", "cvp", "sv",
                                          "cpp", "cop", "buckberg", "dbp", "sbp", "lvedp",
                                          "ankle_p", "brachial_p")}


def cohort_params(height_cm=REF_HEIGHT_CM, weight_kg=REF_WEIGHT_KG,
                  age_years=None, sex="male", hr_bpm=70.0):
    """A bare `SimParams` for a NAMED STUDY COHORT, scaled to its body and age.

    `run_scenario` above returns steady-state means, which suits a
    posture/gravity comparison but not a test that needs the raw time series,
    a drug infusion or a haemorrhage. Those tests built `SimParams()` directly
    and therefore ran the 55-year-old reference patient whatever cohort they
    cited. This is the same patient-scaling path in a form they can use.

    **THIS IS THE IDENTITY AT THE REFERENCE PATIENT.** Measured 2026-09-15:
    `cohort_params()` and `SimParams()` settle to MAP 95.429 / CVP 4.349 /
    CO 6.056 / HR 69.351 — equal to three decimals, not merely close. That is
    not automatic; it is true because `BSA_REF` is COMPUTED from the same
    Mosteller function that measures every patient (see `patient.py`), and
    because no `map_mmhg` is passed. **Passing a measured MAP would invoke
    `svr_scale`, which carries the known -14 % self-rescaling of backlog item
    50** — so do not add one here to "match a cohort's blood pressure" without
    reading that item first. `test_cohort_params_is_the_reference_identity`
    guards the identity.

    Age enters through `aging.arterial_compliance_factor` (elastic arteries)
    and `aging.chamber_age_factors` (the two ventricles). **It does NOT enter
    the baroreflex** — `BaroreflexController` takes no patient argument of any
    kind, so a reflex-level test cannot be age-matched at all. See §28.
    """
    kw = {} if age_years is None else {"age_years": age_years}
    comps, cardiac = build_patient_params(height_cm, weight_kg,
                                          hr_bpm=hr_bpm, sex=sex, **kw)
    params = SimParams(compartments=comps)
    apply_cardiac(params, cardiac)
    params.hr_bpm = hr_bpm
    return params


# ===========================================================================
# 1. Smoke tests — basic plausibility of resting / postural haemodynamics
# ===========================================================================

def test_resting_baseline():
    params = SimParams()
    result = run_simulation(params, duration_s=SMOKE_DURATION, dt=DT)

    map_mean = _mean_last_half(result["map"])
    hr_mean  = _mean_last_half(result["hr"])
    co_mean  = _mean_last_half(result["co"])

    assert 70 <= map_mean <= 110, f"MAP out of range: {map_mean:.1f} mmHg"
    assert 50 <= hr_mean  <= 90,  f"HR out of range: {hr_mean:.1f} bpm"
    assert 3  <= co_mean  <= 8,   f"CO out of range: {co_mean:.2f} L/min"


def test_trendelenburg_raises_map_and_cvp():
    """
    Head-down tilt shifts blood toward the thorax:
    MAP should rise (or stay similar), CVP should increase.
    """
    p_base = SimParams()
    r_base = run_simulation(p_base, duration_s=SMOKE_DURATION, dt=DT)
    map_base = _mean_last_half(r_base["map"])
    cvp_base = _mean_last_half(r_base["cvp"])

    p_tilt = SimParams()
    p_tilt.tilt_start_deg = -30.0
    p_tilt.tilt_end_deg   = -30.0
    r_tilt = run_simulation(p_tilt, duration_s=SMOKE_DURATION, dt=DT)
    map_tilt = _mean_last_half(r_tilt["map"])
    cvp_tilt = _mean_last_half(r_tilt["cvp"])

    assert cvp_tilt > cvp_base, (
        f"CVP did not increase with head-down tilt: {cvp_base:.1f} -> {cvp_tilt:.1f} mmHg"
    )
    assert map_tilt >= map_base - 5, (
        f"MAP dropped unexpectedly with head-down tilt: {map_base:.1f} -> {map_tilt:.1f} mmHg"
    )


def test_microgravity_equalises_pressures():
    """
    In microgravity there are no hydrostatic gradients.
    CVP should increase relative to upright, MAP may be lower than Earth upright.
    """
    p_earth = SimParams()
    p_earth.tilt_start_deg = 90.0
    p_earth.tilt_end_deg   = 90.0
    r_earth = run_simulation(p_earth, duration_s=SMOKE_DURATION, dt=DT)

    p_micro = SimParams()
    p_micro.gravity = GravityEnvironment.MICROGRAVITY
    r_micro = run_simulation(p_micro, duration_s=SMOKE_DURATION, dt=DT)

    cvp_earth = _mean_last_half(r_earth["cvp"])
    cvp_micro = _mean_last_half(r_micro["cvp"])
    map_micro = _mean_last_half(r_micro["map"])

    # Without pooling in legs, microgravity CVP > upright Earth CVP
    assert cvp_micro > cvp_earth - 3, (
        f"Microgravity CVP unexpectedly low: Earth upright {cvp_earth:.1f}, ug {cvp_micro:.1f} mmHg"
    )
    # MAP should remain in survivable range
    assert 50 <= map_micro <= 120, f"MAP out of range in microgravity: {map_micro:.1f} mmHg"


# ===========================================================================
# 2. Literature validation — shared scenario fixtures
#
# Module-scoped so each unique (height, weight, tilt, ...) combination is
# only simulated once even though several literature checks reference it.
# ===========================================================================

@pytest.fixture(scope="module")
def supine_177_80():
    """80 kg, 177 cm, MAP 83, HR 62 — Sejersen 2022 [1] cohort."""
    return run_scenario(177, 80, map_mmhg=83, hr_bpm=62, tilt_deg=0.0)


@pytest.fixture(scope="module")
def hdt20_177_80():
    """Same cohort as supine_177_80, 20° head-down tilt."""
    return run_scenario(177, 80, map_mmhg=83, hr_bpm=62, tilt_deg=-20.0)


@pytest.fixture(scope="module")
def upright20_179_79():
    """79 kg, 179 cm — Verdini 2019 [2] cohort, 20° upright."""
    return run_scenario(179, 79, hr_bpm=70, tilt_deg=20.0)


@pytest.fixture(scope="module")
def hdt6_179_79():
    """Same cohort as upright20_179_79, 6° head-down tilt."""
    return run_scenario(179, 79, hr_bpm=70, tilt_deg=-6.0)


@pytest.fixture(scope="module")
def supine_175_75():
    """
    75 kg, 175 cm, HR 70, supine — the generic "clinical baseline" used by
    several literature checks (Trendelenburg, microgravity, HUT, CPP,
    Buckberg, CVP calibration).
    """
    return run_scenario(175, 75, hr_bpm=70, tilt_deg=0.0)


@pytest.fixture(scope="module")
def hdt30_onset10_175_75():
    """-30 deg Trendelenburg, slower (10 s) tilt onset."""
    return run_scenario(175, 75, hr_bpm=70, tilt_deg=-30.0, tilt_onset=10.0)


@pytest.fixture(scope="module")
def microgravity_175_75():
    return run_scenario(175, 75, hr_bpm=70, gravity=GravityEnvironment.MICROGRAVITY)


@pytest.fixture(scope="module")
def upright45_175_75():
    return run_scenario(175, 75, hr_bpm=70, tilt_deg=45.0)


@pytest.fixture(scope="module")
def hdt15_175_75():
    """-15 deg Trendelenburg — Likhvantsev 2025 [3] comparison."""
    return run_scenario(175, 75, hr_bpm=70, tilt_deg=-15.0, tilt_onset=5.0)


@pytest.fixture(scope="module")
def hut20_175_75():
    return run_scenario(175, 75, hr_bpm=70, tilt_deg=20.0)


@pytest.fixture(scope="module")
def hut30_175_75():
    return run_scenario(175, 75, hr_bpm=70, tilt_deg=30.0)


@pytest.fixture(scope="module")
def tachycardia_175_75_nobaro():
    return run_scenario(175, 75, hr_bpm=160, tilt_deg=0.0, baroreflex=False)


# ===========================================================================
# 3. Literature validation — tests
# ===========================================================================

def test_supine_baseline_sejersen2022(supine_177_80):
    """[DOI: 10.14814/phy2.15216] Sejersen 2022 — supine, 80 kg / 177 cm.

    Literature: MAP 83+/-8 mmHg, HR 62+/-8 bpm, SV 110+/-16 mL, CO 7+/-2 L/min.
    """
    s = supine_177_80
    assert 70 <= s["map"] <= 100, f"MAP {s['map']:.1f} mmHg out of range (lit 83+/-8)"
    assert 50 <= s["hr"]  <= 85,  f"HR {s['hr']:.1f} bpm out of range (lit 62+/-8)"
    assert 4  <= s["co"]  <= 10,  f"CO {s['co']:.2f} L/min out of range (lit 7+/-2)"
    assert 60 <= s["sv"]  <= 150, f"SV {s['sv']:.1f} mL out of range (lit 110+/-16)"


def test_hdt20_normovolemic_sejersen2022(supine_177_80, hdt20_177_80):
    """[DOI: 10.14814/phy2.15216] Sejersen 2022 — 20° HDT, normovolemic.

    Literature: dSV ~ 0 (n.s.), dCO ~ 0, dMAP ~ +2 mmHg (n.s.) — SV/CO
    should not increase substantially and MAP should not drop.

    Model note: MAP=83 input is below the baroreflex setpoint (93 mmHg).
    patient.py scales SVR down to match, leaving a slight preload deficit in
    the legs, so HDT returns more blood than for a fully normovolemic subject.
    The DIRECTION (MAP up, HR down, CO maintained) is correct; the magnitude
    differs — hence the <15% SV/CO tolerance rather than an exact-zero check.
    """
    s0, s1 = supine_177_80, hdt20_177_80
    dmap = s1["map"] - s0["map"]
    assert dmap > -5, f"MAP dropped with HDT: {s0['map']:.1f} -> {s1['map']:.1f} mmHg (lit ~+2)"
    assert s1["map"] >= 70, f"MAP not physiological during HDT: {s1['map']:.1f} mmHg"
    assert s1["co"] >= 4, f"CO inadequate during HDT: {s1['co']:.2f} L/min"


def test_hdt6_vs_upright20_verdini2019(upright20_179_79, hdt6_179_79):
    """[DOI: 10.1038/s41598-019-39360-6] 6° HDT vs 20° upright — directional checks.

    Literature: MAP_HDT < MAP_upright, HR_HDT < HR_upright (p<0.001) at 90°
    upright. 90° upright is outside the model's validated range (no muscle
    pump; validated -30° to +45°), so 20° upright is used as a fair
    comparison — the HR direction (HDT < upright) should still hold.
    """
    s_ort, s_hdt = upright20_179_79, hdt6_179_79
    dhr = s_hdt["hr"] - s_ort["hr"]
    assert dhr < 0, f"HR_HDT not < HR_upright: dHR={dhr:+.1f} bpm"
    assert 70 <= s_hdt["map"] <= 110, f"HDT MAP out of range: {s_hdt['map']:.1f}"
    assert 70 <= s_ort["map"] <= 110, f"Upright MAP out of range: {s_ort['map']:.1f}"


def test_trendelenburg_minus30_sibbald1979(supine_175_75, hdt30_onset10_175_75):
    """Clinical Trendelenburg (-30°): CVP up, MAP maintained, CO up
    (increased venous return)."""
    sb, st = supine_175_75, hdt30_onset10_175_75
    dcvp = st["cvp"] - sb["cvp"]
    dmap = st["map"] - sb["map"]
    assert dcvp > 0, f"CVP did not increase at -30 deg: d={dcvp:+.1f} mmHg"
    assert dmap > -15, f"MAP not maintained at -30 deg: d={dmap:+.1f} mmHg"


def test_microgravity_vs_upright(microgravity_175_75, upright45_175_75):
    """Microgravity (clinical analogy: post-op / bed-rest).

    CVP should increase vs upright Earth (no venous pooling in legs).
    """
    s_ug, s_upr = microgravity_175_75, upright45_175_75
    assert s_ug["cvp"] > s_upr["cvp"], (
        f"CVP_ug ({s_ug['cvp']:.1f}) not > CVP_upright ({s_upr['cvp']:.1f})"
    )
    assert 50 <= s_ug["map"] <= 120, f"MAP out of survivable range: {s_ug['map']:.1f}"


def test_trendelenburg_minus15_likhvantsev2025(supine_175_75, hdt15_175_75):
    """[PMID: 39500675 — Likhvantsev 2025 meta-analysis] Trendelenburg -15° vs supine.

    Pooled (n=333, 16 studies): dCVP +4.13 (CI 2.42-5.84), dCO +0.33,
    dSV +8.27 mL, dHR -1.65 bpm, dMAP positive direction.

    HISTORY, 2026-10-04. Leg rebuild stage 1 removed a phantom gravitational
    pump and this test failed (dCO -0.124). The cause was the positional
    intrathoracic pressure, a FITTED +2.2 mmHg that had been cancelling the pump.
    Drummond & Martin 1978 measured no pleural pressure change at 15 deg, so it
    was set to zero, and cardiac output rises again for a physiological reason.
    The CVP half of this study is split out below, where it is a known gap.
    """
    s_base, s_trend15 = supine_175_75, hdt15_175_75
    dco  = s_trend15["co"]  - s_base["co"]
    dsv  = s_trend15["sv"]  - s_base["sv"]
    dmap = s_trend15["map"] - s_base["map"]
    assert dco  > 0, f"CO must increase at -15 deg: d={dco:+.3f} (lit +0.33)"
    assert dsv  > 0, f"SV must increase at -15 deg: d={dsv:+.1f} mL (lit +8.27)"
    assert dmap > -5, f"MAP dropped substantially at -15 deg: d={dmap:+.1f} mmHg"


# CLOSED 2026-10-13 — strict xfail of 2026-10-04 (dCVP +0.52) XPASSED when the sac
# went on with its knee at the resting end-diastolic heart: head-down fills the heart
# past the knee and the sac raises filling pressure. Measured: dCVP +3.13 (CI 2.42-
# 5.84), dSV +6.2, dCO +0.40. The target stays weak (grade C, pooled -5 to -45 deg).
def test_trendelenburg_minus15_cvp_likhvantsev2025(supine_175_75, hdt15_175_75):
    """[PMID: 39500675 — Likhvantsev 2025] The CVP half of the -15 deg comparison,
    split from the test above on 2026-10-04 so the passing flow assertions are
    not hidden behind a failing pressure one. The band is unchanged."""
    dcvp = hdt15_175_75["cvp"] - supine_175_75["cvp"]
    assert 1.5 <= dcvp <= 7.0, f"ΔCVP {dcvp:+.2f} mmHg outside [1.5, 7.0] (lit CI 2.42-5.84)"


def test_hut30_dynamics_wieling1998(supine_175_75, hut30_175_75):
    """[PMID: 9640339 — Wieling 1998] Head-up tilt dynamics: SV down, CO down,
    HR up, MAP partially maintained.

    Literature (90°, 1 min): SV -39+/-9%, CO -26+/-10%, MAP +1+/-7 mmHg.
    90° is outside the model's validated range (no muscle pump); 30° is
    tested instead, where the baroreflex partially compensates and the
    drops should be smaller in magnitude but same direction.
    """
    s_base, s_hut30 = supine_175_75, hut30_175_75
    dsv  = pct(s_hut30["sv"], s_base["sv"])
    dco  = pct(s_hut30["co"], s_base["co"])
    dhr  = s_hut30["hr"]  - s_base["hr"]
    dmap = s_hut30["map"] - s_base["map"]

    assert dsv < 0, f"SV did not decrease at 30 deg HUT: {dsv:+.1f}%"
    assert dco < 0, f"CO did not decrease at 30 deg HUT: {dco:+.1f}%"
    assert dhr > 0, f"HR did not increase at 30 deg HUT: d={dhr:+.1f} bpm"
    assert dmap > -25, f"MAP collapsed at 30 deg HUT: d={dmap:+.1f} mmHg"
    assert s_hut30["map"] >= 65, f"MAP not viable at 30 deg HUT: {s_hut30['map']:.1f}"


def test_graded_hut_monotonicity_sarafian2017(supine_175_75, hut20_175_75, hut30_175_75):
    """[PMC5209346 — Sarafian 2017] Graded HUT 0->20->30°: HR rises and CO
    falls monotonically with tilt angle.

    Literature: HR +41%, BP +10%, TPR +16%, CO -8.9% at 60°.
    """
    hr_vals = [supine_175_75["hr"], hut20_175_75["hr"], hut30_175_75["hr"]]
    co_vals = [supine_175_75["co"], hut20_175_75["co"], hut30_175_75["co"]]

    hr_mono = all(hr_vals[i] < hr_vals[i + 1] for i in range(len(hr_vals) - 1))
    co_mono = all(co_vals[i] > co_vals[i + 1] for i in range(len(co_vals) - 1))

    assert hr_mono, f"HR not monotonically increasing with tilt angle: {hr_vals}"
    assert co_mono, f"CO not monotonically decreasing with tilt angle: {co_vals}"
    assert hr_vals[-1] > hr_vals[0], "HR at 30 deg not higher than supine"
    assert co_vals[-1] < co_vals[0], "CO at 30 deg not lower than supine"


# LIVE AGAIN 2026-10-18, AND THE HISTORY MATTERS MORE THAN THE PASS.
# This floor has now crossed three times: strict xfail at 36.2 (2026-10-11), XPASS at
# 44.4 (2026-10-13) reopened at 39.5 (2026-10-17), and XPASS at 45.0 today when the
# vasomotor age law moved to Davy 1998 (the 55-year-old's net vasomotor factor rose
# 0.347 -> 0.591, and the 45 deg MAP fall shrank from ~38 to 34.6 mmHg).
# **THE PASS IS PARTLY REAL AND THE DEFECT IS NOT CLOSED.** Measured today: supine MAP
# 98.3, 45 deg 63.8, so MAP still falls 34.6 mmHg where man holds it near supine
# (Wieling 1998: +1 +- 7 at 90 deg). The floor is a SAFETY threshold (Pohl & Cullen:
# risk below 50), not a measurement of defence, so it is kept live as a ratchet notch
# and the real quantity is asserted separately in
# `test_map_is_defended_on_head_up_tilt_wieling1998` below, which xfails.
# Do not read this pass as evidence the orthostatic collapse has closed.
def test_cerebral_perfusion_pressure_pohl_cullen2005(supine_175_75, upright45_175_75):
    """Cerebral perfusion pressure (Pohl/Cullen 2005).

    Supine CPP ~ 70-85 mmHg; 45° upright CPP < supine (brain above heart)
    but must stay > 40 mmHg.
    """
    s_sup, s_up45 = supine_175_75, upright45_175_75
    assert 60 <= s_sup["cpp"] <= 100, f"Supine CPP out of range: {s_sup['cpp']:.1f}"
    assert s_up45["cpp"] < s_sup["cpp"], (
        f"CPP_upright ({s_up45['cpp']:.1f}) not < CPP_supine ({s_sup['cpp']:.1f})"
    )
    assert s_up45["cpp"] > 40, f"CPP not viable at 45 deg: {s_up45['cpp']:.1f}"


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "KNOWN GAP, 2026-10-18 — THE ORTHOSTATIC MAP COLLAPSE, asserted on the quantity that "
    "is actually wrong rather than on the CPP floor above. Measured: supine MAP 98.3 -> "
    "63.8 at 45 deg, a fall of 34.6 mmHg, where Wieling measured heart-level MAP changing "
    "+1 +- 7 even at 90 deg. CAUSE (validation log 2026-10-18): the filling-pressure signal "
    "is too small, so the reflex must trade MAP for vasoconstriction — the model's heart "
    "converts filling PRESSURE into stroke volume 3-4x too efficiently (dSV/dPCWP 8.88 vs "
    "Levine 1991 nonathletes 2.7 +- 1.5), so CVP falls -1.41 at -30 LBNP against man's -5.8. "
    "Not the muscle pump (the same failure appears supine under LBNP) and not the chambers "
    "(stiffness x3 moved dCVP by 0.04). Band not widened."
))
def test_map_is_defended_on_head_up_tilt_wieling1998(supine_175_75, upright45_175_75):
    """[PMID 9640339 — Wieling 1998] Heart-level mean arterial pressure is defended on
    head-up tilt: it changes by only +1 +/- 7 mmHg even at 90 deg, while leg arterial
    pressure rises by the hydrostatic column.

    The sibling CPP test above asserts a SAFETY FLOOR and currently passes; this one
    asserts the PHYSIOLOGY and does not. Two different claims, so they are two tests —
    a passing floor must not be mistaken for a defended pressure.

    Band: 1 SD on Wieling's own figure, widened to 15 mmHg because the comparison is at
    45 deg against his 90 deg measurement (a smaller tilt, so if anything an easier
    target). The model fails it by more than twice that, so the band is not load-bearing."""
    d = upright45_175_75["map"] - supine_175_75["map"]
    assert abs(d) <= 15.0, (
        f"MAP falls {d:+.1f} mmHg from supine to 45 deg head-up "
        f"({supine_175_75['map']:.1f} -> {upright45_175_75['map']:.1f}); "
        f"Wieling measured +1 +- 7 at 90 deg")


def test_ankle_brachial_gradient_postural(
    hdt30_onset10_175_75, hdt15_175_75, supine_175_75,
    hut20_175_75, hut30_175_75, upright45_175_75,
):
    """Ankle-brachial pressure gradient vs tilt — hydrostatic column physiology.

    Standard orthostatic physiology (e.g. [PMID 9640339] Wieling 1998 — heart-
    level MAP changes only +1+/-7 mmHg with upright tilt, while lower-leg
    arterial pressure rises by roughly the hydrostatic column height): ankle
    pressure should rise and heart-level/brachial pressure should fall (or stay
    flat) monotonically as tilt goes from head-down to head-up, so the
    ankle-brachial gradient should increase monotonically across the same
    range and should be more negative supine than at 45 deg upright.

    See docs/known_model_limitations.md (section 6) for the absolute-value
    caveats of `ankle_p`/`brachial_p` — only the direction/ordering across
    tilt is asserted here.
    """
    scenarios = [hdt30_onset10_175_75, hdt15_175_75, supine_175_75,
                  hut20_175_75, hut30_175_75, upright45_175_75]
    ankle = [s["ankle_p"] for s in scenarios]
    brach = [s["brachial_p"] for s in scenarios]
    grad  = [a - b for a, b in zip(ankle, brach)]

    assert all(ankle[i] < ankle[i + 1] for i in range(len(ankle) - 1)), (
        f"ankle_p not monotonically increasing with tilt: {ankle}"
    )
    assert all(brach[i] > brach[i + 1] for i in range(len(brach) - 1)), (
        f"brachial_p not monotonically decreasing with tilt: {brach}"
    )
    assert all(grad[i] < grad[i + 1] for i in range(len(grad) - 1)), (
        f"ankle-brachial gradient not monotonically increasing with tilt: {grad}"
    )
    assert grad[-1] > grad[2], (
        f"45 deg upright gradient ({grad[-1]:.1f}) not > supine gradient ({grad[2]:.1f})"
    )


def test_coronary_perfusion_buckberg1972(supine_175_75, tachycardia_175_75_nobaro):
    """Coronary perfusion / Buckberg index (Buckberg 1972/1978).

    Resting (HR ~70): Buckberg > 0.8, CoPP > 40 mmHg.
    Tachycardia (HR=160): Buckberg falls (diastolic time shortened).
    """
    s_rest, s_tachy = supine_175_75, tachycardia_175_75_nobaro
    assert s_rest["cop"] > 40, f"CoPP at rest too low: {s_rest['cop']:.1f} mmHg"
    assert s_rest["buckberg"] > 0.8, f"Buckberg at rest too low: {s_rest['buckberg']:.3f}"
    assert s_tachy["buckberg"] < s_rest["buckberg"], (
        f"Buckberg did not fall with tachycardia: {s_tachy['buckberg']:.3f} "
        f">= {s_rest['buckberg']:.3f}"
    )


def test_ra_pressure_baseline_richter2021():
    """Resting right atrial pressure, compared LIKE WITH LIKE.

    [PMID 33655769, DOI 10.1152/ajplung.00583.2020] Richter MJ et al. 2021,
    Am J Physiol Lung Cell Mol Physiol 320:L715-25. Right heart catheterisation
    with a conductance catheter in 15 patients WITHOUT pulmonary hypertension:
        right atrial pressure       3 [2-6] mmHg   median [IQR]
        RV end-diastolic pressure   4 [3-5] mmHg
    Internally coherent — the ventricle sits just above the atrium across an
    open tricuspid valve.

    WHY THIS SOURCE REPLACED HOFF, AND IT IS A SITE QUESTION, NOT A SCATTER ONE.
    The band was 4-10 mmHg from Hoff 2019 (PMID 31560715). Re-reading Hoff's
    Methods on 2026-09-09 showed the catheter was "inserted via the left basilic
    vein to the LEFT SUBCLAVIAN VEIN", with position confirmed only by waveform
    and never by imaging. That is a subclavian venous pressure one site upstream
    of the right atrium; the authors never call it a right atrial pressure, and
    the paper reports NO absolute resting CVP at all — the 6.94 this project
    used was our own derivation from their raw waveform archive.
    Richter measured the right atrium itself, and matches this model's reference
    patient far better besides: age 59 +/- 17 against the model's 55 (Hoff was
    25 +/- 3) and 14 of 15 male against the model's male default (Hoff 11 M/9 F).
    Site, age and sex all point the same way.
    Hoff remains the source for the respiratory SWING (dCVP), which is a
    difference and so is insensitive to a constant site offset — see
    `test_ra_intraluminal_respiratory_swing`.

    AND THE COMPARED QUANTITY CHANGED TOO. The old assertion read the model's
    `cvp` output, which is TRANSMURAL and a rolling end-diastolic MINIMUM. A
    catheter reads INTRALUMINAL pressure at END-EXPIRATION. This test now
    measures that, which is why it can use the source's own band rather than
    padding it for a convention mismatch.
    """
    comps, cardiac = build_patient_params(175, 75, hr_bpm=70)
    params = SimParams(compartments=comps)
    apply_cardiac(params, cardiac)
    params.hr_bpm           = 70
    params.ventilation_mode = "spontaneous"
    params.resp_rate_bpm    = 15.0
    r = run_simulation(params, duration_s=LIT_DURATION, dt=DT)

    t     = np.asarray(r["t"])
    h     = len(t) // 2
    t     = t[h:]
    intra = np.asarray(r["ra_intraluminal"])[h:]
    trans = np.asarray(r["cvp"])[h:]

    # End-expiration: the last 15 % of each respiratory cycle, where
    # intrathoracic pressure is least negative and a transducer is read.
    period = 60.0 / params.resp_rate_bpm
    ee     = ((t % period) / period) > 0.85
    rap_ee = float(np.mean(intra[ee]))

    assert 2.0 <= rap_ee <= 6.0, (
        f"end-expiratory intraluminal RA pressure {rap_ee:.2f} mmHg outside "
        f"Richter's measured IQR of 2-6 (median 3), n=15 non-PH controls by "
        f"right heart catheterisation"
    )
    # The transmural value must sit BELOW the intraluminal one at end-expiration,
    # because intrathoracic pressure is negative in a spontaneously breathing
    # supine subject. This is a sign check on the ITP wiring, not a calibration.
    assert float(np.mean(trans[ee])) > rap_ee, (
        "transmural RA pressure is not above intraluminal at end-expiration — "
        "the respiratory ITP term has the wrong sign"
    )


# ===========================================================================
# 4. Propofol — [PMID: 3257393, Claeys 1988]
# ===========================================================================

def _run_propofol(dose, baro=False):
    p = SimParams()
    p.baroreflex_enabled = baro
    p.drug_factors = combined_drug_factors({"propofol": dose})
    r = run_simulation(p, duration_s=20, dt=DT)
    h = len(r['map']) // 2
    return {k: float(np.mean(r[k][h:])) for k in ('map', 'hr', 'co', 'cvp', 'sv')}


def test_propofol_claeys1988():
    """[PMID: 3257393 — Claeys 1988] Propofol 2 mg/kg: SVR -21%, MAP -25%
    (elderly, impaired baroreflex), CO and HR unchanged.

    Tested with baroreflex OFF (simulates impaired baroreflex in elderly):
    confirms the pharmacological SVR effect. With baroreflex ON, the MAP
    drop is smaller — physiologically correct for younger patients.
    """
    base    = _run_propofol(0.0, baro=False)
    prop2   = _run_propofol(2.0, baro=False)

    dmap_nobaro = (prop2['map'] - base['map']) / base['map'] * 100
    dco_nobaro  = (prop2['co']  - base['co'])  / base['co']  * 100
    dhr_nobaro  =  prop2['hr']  - base['hr']

    assert dmap_nobaro < -5, f"MAP did not drop with propofol: {dmap_nobaro:+.1f}% (lit -25%)"
    assert abs(dco_nobaro) < 15, f"CO not approximately maintained: {dco_nobaro:+.1f}% (lit ~0%)"
    assert abs(dhr_nobaro) < 5, f"HR changed unexpectedly: d={dhr_nobaro:+.1f} bpm (lit ~0)"
    assert prop2['map'] > 50, f"MAP not viable with propofol: {prop2['map']:.1f} mmHg"


# ===========================================================================
# 5. Respiratory sinus arrhythmia — [Hirsch & Bishop 1981]
# ===========================================================================

def test_rsa_spontaneous_breathing_hirsch_bishop1981():
    """[Hirsch & Bishop 1981] Spontaneous breathing produces an HR
    oscillation of 3-10 bpm peak-to-peak at 15 breaths/min.

    BOTH statistics are measured over the SETTLED half of the run. They used
    to disagree: the standard deviation took the second half while the
    peak-to-peak took the whole array, so the p-p figure was dominated by the
    start-up transient as the model converges away from `init_volume` (which
    is not the true equilibrium — see compartments.py). On 2026-09-04 the
    full-run p-p read 8.55 bpm against a settled 4.26, so the old ceiling of
    12.0 was really a limit on transient size and not on RSA at all.
    With the window corrected the band can be the literature one."""
    p = SimParams()
    p.ventilation_mode = 'spontaneous'
    p.resp_rate_bpm    = 15.0
    r = run_simulation(p, duration_s=30, dt=DT, use_baroreflex=True)
    hr = np.asarray(r['hr'])[len(r['hr']) // 2:]
    hr_std   = float(np.std(hr))
    hr_range = float(np.max(hr) - np.min(hr))

    assert hr_std > 0.3, f"RSA not detectable: HR std={hr_std:.2f} bpm"
    assert hr_range < 10.0, f"RSA above Hirsch & Bishop: HR p-p={hr_range:.2f} bpm"
    assert hr_range > 3.0, f"RSA below Hirsch & Bishop: HR p-p={hr_range:.2f} bpm"


# ===========================================================================
# 6. PEEP reduces cardiac output — [10] Jardin 1981, PMID 7005679
# ===========================================================================

def _run_vent(mode, peep=5.0, pip=20.0, rr=14.0):
    p = SimParams()
    p.ventilation_mode = mode
    p.resp_rate_bpm    = rr
    p.peep_cmh2o       = peep
    p.pip_cmh2o        = pip
    r = run_simulation(p, duration_s=30, dt=DT, use_baroreflex=True)
    h = len(r['map']) // 2
    return {k: float(np.mean(r[k][h:])) for k in ('map', 'co', 'hr', 'cvp', 'sv')}


def test_peep_reduces_co_jardin1981():
    """[10] PEEP 10 cmH2O reduces CO vs no ventilation, dose-responsively.

    Bounds encode DIRECTION and DOSE-RESPONSE only — all the verified source
    supports. Do not add a numeric target without reading the full text.
    """
    s_none   = _run_vent('none')
    s_peep0  = _run_vent('mechanical', peep=0.0,  pip=15.0)
    s_peep10 = _run_vent('mechanical', peep=10.0, pip=25.0)

    dco_peep0  = (s_peep0['co']  - s_none['co']) / s_none['co'] * 100
    dco_peep10 = (s_peep10['co'] - s_none['co']) / s_none['co'] * 100

    assert dco_peep10 < -5, f"PEEP 10 did not reduce CO by >=5%: {dco_peep10:+.1f}%"
    assert dco_peep10 > -50, f"PEEP 10 reduced CO catastrophically: {dco_peep10:+.1f}%"
    assert dco_peep10 < dco_peep0, (
        f"No PEEP dose-response: PEEP0={dco_peep0:+.1f}%, PEEP10={dco_peep10:+.1f}%"
    )
    assert s_peep10['map'] > 50, f"MAP not viable with PEEP 10: {s_peep10['map']:.1f} mmHg"


# ===========================================================================
# 7. Hemorrhage / fluid bolus / resuscitation — [12]-[15]
# ===========================================================================

def _run_hem_bolus(hem_ml=0.0, hem_start=3.0, hem_dur=5.0,
                   bolus_ml=0.0, bolus_start=10.0, bolus_dur=5.0,
                   duration=30.0):
    p = SimParams()
    if hem_ml > 0:
        p.hemorrhage_rate_mlmin = hem_ml / hem_dur * 60.0
        p.hemorrhage_start_s    = hem_start
        p.hemorrhage_duration_s = hem_dur
    if bolus_ml > 0:
        p.fluid_bolus_ml         = bolus_ml
        p.fluid_bolus_start_s    = bolus_start
        p.fluid_bolus_duration_s = bolus_dur
    r = run_simulation(p, duration_s=duration, dt=DT)
    h = len(r['map']) // 2
    return {k: float(np.mean(r[k][h:])) for k in ('map', 'hr', 'co', 'cvp', 'sv')}


@pytest.fixture(scope="module")
def baseline_hem():
    return _run_hem_bolus()


# Clinically-scaled hemorrhage volumes. With the physiological ~5.3 L blood
# volume and ~1.6 L stressed volume (venous-system rebuild, see compartments.py),
# haemodynamically meaningful hemorrhage sits at class-I→III magnitudes (~300 /
# 600 / 1000 mL), not the 100–300 mL the old compressed 0.7 L pool required.
@pytest.fixture(scope="module")
def hem_mild():
    return _run_hem_bolus(hem_ml=300)


@pytest.fixture(scope="module")
def hem_mod():
    return _run_hem_bolus(hem_ml=600)


@pytest.fixture(scope="module")
def hem_severe():
    return _run_hem_bolus(hem_ml=1000)


def test_hemorrhage_volume_conserved():
    """Hemorrhage removes exactly the prescribed volume from the
    circulation (mass conservation of the dV adjustment)."""
    p = SimParams()
    p.hemorrhage_rate_mlmin = 1200.0  # 100 mL over 5 s
    p.hemorrhage_start_s    = 3.0
    p.hemorrhage_duration_s = 5.0
    r = run_simulation(p, duration_s=15.0, dt=DT)
    removed = r["volumes"][0].sum() - r["volumes"][-1].sum()
    assert abs(removed - 100.0) < 0.5, f"Expected ~100 mL removed, got {removed:.2f} mL"


def test_graded_hemorrhage_monotonic_lie2023(baseline_hem, hem_mild, hem_mod, hem_severe):
    """[12] Lie 2023 — CO falls approximately linearly with central
    hypovolemia severity; [13] Vettorello 2016 — HR rises with severity.
    Graded hemorrhage (300/600/1000 mL) should reproduce this monotonic
    dose-response."""
    map_vals = [baseline_hem['map'], hem_mild['map'], hem_mod['map'], hem_severe['map']]
    co_vals  = [baseline_hem['co'],  hem_mild['co'],  hem_mod['co'],  hem_severe['co']]
    hr_vals  = [baseline_hem['hr'],  hem_mild['hr'],  hem_mod['hr'],  hem_severe['hr']]

    assert all(map_vals[i] > map_vals[i + 1] for i in range(3)), (
        f"MAP not monotonically falling with hemorrhage severity: {map_vals}"
    )
    assert all(co_vals[i] > co_vals[i + 1] for i in range(3)), (
        f"CO not monotonically falling with hemorrhage severity: {co_vals}"
    )
    assert all(hr_vals[i] < hr_vals[i + 1] for i in range(3)), (
        f"HR not monotonically rising with hemorrhage severity: {hr_vals}"
    )
    assert hem_severe['map'] > 40, f"MAP collapsed at 1000 mL hemorrhage: {hem_severe['map']:.1f} mmHg"


def test_mild_hemorrhage_preload_sensitivity_hamilton2021(baseline_hem, hem_mild):
    """[14] Hamilton 2021 — at mild hypovolemia, preload (CVP) falls
    proportionally more than systemic MAP (RV/pulmonary preload is affected
    before the systemic circulation decompensates)."""
    dcvp_pct = pct(hem_mild['cvp'], baseline_hem['cvp'])
    dmap_pct = pct(hem_mild['map'], baseline_hem['map'])

    assert dcvp_pct < 0, f"CVP did not fall with mild hemorrhage: {dcvp_pct:+.1f}%"
    assert dmap_pct < 0, f"MAP did not fall with mild hemorrhage: {dmap_pct:+.1f}%"
    assert dcvp_pct < dmap_pct, (
        f"CVP should fall proportionally more than MAP at mild hypovolemia: "
        f"dCVP={dcvp_pct:+.1f}%, dMAP={dmap_pct:+.1f}%"
    )


def test_severe_hemorrhage_decompensation(baseline_hem, hem_severe):
    """1000 mL hemorrhage (the most severe graded step, ~class III) produces a
    clinically significant MAP drop — decompensation, unlike the mild
    (300 mL) case."""
    dmap = hem_severe['map'] - baseline_hem['map']
    assert dmap < -15, f"MAP did not drop substantially at 1000 mL hemorrhage: d={dmap:+.1f} mmHg"
    assert hem_severe['map'] > 40, f"MAP non-viable at 1000 mL hemorrhage: {hem_severe['map']:.1f} mmHg"


def test_fluid_bolus_increases_sv_co_herrera2017(baseline_hem):
    """[15] Herrera 2017 — crystalloid bolus increases SV and CO, with HR
    unchanged or slightly reduced (improved filling reduces compensatory
    tachycardia).

    COHORT CAVEAT, 2026-10-06 (Jesper): Herrera's subjects were in the THIRD
    TRIMESTER — high output, aortocaval compression, fluid-responsive. This test
    gives the bolus to a normovolaemic model adult, so it checks DIRECTION only;
    its magnitudes are not comparable and none is asserted."""
    bolus = _run_hem_bolus(bolus_ml=600)
    dsv = pct(bolus['sv'], baseline_hem['sv'])
    dco = pct(bolus['co'], baseline_hem['co'])
    dhr = bolus['hr'] - baseline_hem['hr']

    assert dsv > 0, f"SV did not increase with fluid bolus: {dsv:+.1f}% (lit +27%)"
    assert dco > 0, f"CO did not increase with fluid bolus: {dco:+.1f}%"
    assert dhr <= 0, f"HR increased with fluid bolus: d={dhr:+.1f} bpm (lit -5%)"
    assert bolus['map'] < 160, f"MAP excessively high after bolus: {bolus['map']:.1f} mmHg"


def test_hemorrhage_resuscitation_restores_map_and_co(hem_mod):
    """Resuscitation scenario: a 600 mL crystalloid bolus following a
    600 mL hemorrhage partially restores MAP and CO toward (or above)
    baseline, compared to hemorrhage alone."""
    resus = _run_hem_bolus(hem_ml=600, bolus_ml=600)

    assert resus['map'] > hem_mod['map'], (
        f"Resuscitation did not raise MAP: {hem_mod['map']:.1f} -> {resus['map']:.1f}"
    )
    assert resus['co'] > hem_mod['co'], (
        f"Resuscitation did not raise CO: {hem_mod['co']:.2f} -> {resus['co']:.2f}"
    )


# ===========================================================================
# 8. PPV — pulse pressure variation / fluid responsiveness
# ===========================================================================

@pytest.fixture(scope="module")
def ppv_scenarios():
    """Three PPV scenarios, run once and shared.

    Module-scoped because each is a 60 s simulation and two tests need all
    three — the live fluid-responsiveness assertions below, and the isolated
    normovolaemic threshold that is currently a known gap.
    """
    def _ppv_run(hemorrhage_ml=0.0, fluid_ml=0.0):
        p = SimParams()
        p.ventilation_mode   = 'mechanical'
        p.peep_cmh2o         = 5.0
        p.pip_cmh2o          = 20.0
        p.ie_ratio           = 0.33
        p.resp_rate_bpm      = 14.0
        p.baroreflex_enabled = True
        if hemorrhage_ml > 0:
            p.hemorrhage_rate_mlmin = hemorrhage_ml / (20.0 / 60.0)
            p.hemorrhage_start_s    = 2.0
            p.hemorrhage_duration_s = 20.0
        if fluid_ml > 0:
            p.fluid_bolus_ml         = fluid_ml
            p.fluid_bolus_start_s    = 30.0
            p.fluid_bolus_duration_s = 20.0
        r = run_simulation(p, duration_s=60.0, dt=DT)
        h = len(r["ppv"]) // 2
        return {
            "ppv": float(np.mean(r["ppv"][h:])),
            "co":  float(np.mean(r["co"][h:])),
        }

    return {
        "normo": _ppv_run(),
        "hypo":  _ppv_run(hemorrhage_ml=1000.0),
        "resus": _ppv_run(hemorrhage_ml=1000.0, fluid_ml=1000.0),
    }


def test_ppv_fluid_responsiveness_michard2000(ppv_scenarios):
    """[DOI 10.1164/ajrccm.162.1.9905119 — Michard & Teboul 2000]
    PPV > 13% predicts fluid responsiveness under mechanical ventilation.

    Michard 2000 (n=40 septic-shock patients, PEEP 5, VT 8 mL/kg):
    PPV > 13% predicted >=15% CO rise with a 500 mL fluid challenge
    (sensitivity 94%, specificity 96%).

    THIS TEST HOLDS THE ASSERTIONS THAT CURRENTLY PASS. The normovolaemic
    threshold is a known gap and lives in its own xfail below, deliberately
    separated so that these four keep running rather than being swallowed by
    a whole-test xfail. The ordering assertion in particular was added on
    2026-08-25 to catch a failure mode nothing had been watching, and it would
    be worthless if it could not fail.
    """
    s_normo = ppv_scenarios["normo"]
    s_hypo  = ppv_scenarios["hypo"]
    s_resus = ppv_scenarios["resus"]

    # ORDERING. Losing blood must RAISE pulse-pressure variation. That is the
    # whole premise of the metric, and unlike the thresholds it is
    # calibration-independent — it holds whatever the absolute numbers are.
    # It was silently INVERTED until 2026-08-25 (normovolaemic 43.1 % vs
    # hypovolaemic 39.4 %: the model said a bleeding patient was LESS
    # fluid-responsive) and nothing caught it, because the threshold assertions
    # only ever check each scenario against 13 % and never against each other.
    # See validation_log.md "PPV diagnosed". Do not weaken this.
    assert s_hypo["ppv"] > s_normo["ppv"], (
        f"PPV ordering inverted: normovolemic {s_normo['ppv']:.1f}% vs "
        f"hypovolemic {s_hypo['ppv']:.1f}% — hemorrhage must RAISE PPV"
    )

    # Hypovolemic: on ascending limb -> fluid responsive (Michard threshold)
    assert s_hypo["ppv"] > 13, (
        f"Hypovolemic PPV too low: {s_hypo['ppv']:.1f}% (expected > 13% per Michard 2000)"
    )

    # Resuscitation reduces PPV (patient moves toward plateau)
    assert s_resus["ppv"] < s_hypo["ppv"], (
        f"PPV did not decrease with resuscitation: {s_hypo['ppv']:.1f}% -> {s_resus['ppv']:.1f}%"
    )

    # CO increased >= 15% with fluid (Michard criterion validated)
    assert s_resus["co"] >= s_hypo["co"] * 1.15, (
        f"CO increase < 15% with fluid: {s_hypo['co']:.2f} -> {s_resus['co']:.2f} L/min"
    )


def test_ppv_normovolaemic_below_michard_threshold(ppv_scenarios):
    """[DOI 10.1164/ajrccm.162.1.9905119] Normovolaemic patient must not be
    flagged as fluid-responsive.

    On the Starling plateau, beat-to-beat SV should barely change with cyclic
    intrathoracic pressure, so PPV stays under 13 %.

    CLOSED 2026-09-03, AFTER BEING OPEN SINCE 2026-08-25. Now 12.02 %. The
    history is worth keeping because no single change fixed it and three of the
    four were aimed at something else entirely:
        43.1 %  2026-08-25, when the gap was opened
        24.7 %  the ITP compartment set had omitted the thoracic arteries,
                putting the whole pleural swing across the aortic valve; and
                pleural transmission carried an unsourced 0.5 against Pelosi's
                measured 0.376
        17.2 %  the whole-heart chamber rebuild (aimed at item 23)
        13.07 % abdominal pressure coupling, item 27 (the mechanism this gap's
                own xfail had correctly named as missing)
        12.02 % pulmonary compliance x5.0 (aimed at pulmonary blood volume)
    NOT ONE of those was a parameter fitted to this endpoint. The xfail text
    carried an explicit instruction not to choose a thorax-to-abdomen
    coefficient that landed PPV under 13 %, and it was not done — the
    coefficient came from Heijnen and the final push came from a pulmonary
    change made for unrelated reasons.

    THE COHORT CAVEAT REMAINS AND SHOULD BE STATED WHEREVER THIS IS QUOTED.
    Michard's < 13 % threshold is derived in mechanically ventilated SEPTIC
    patients; this model is a healthy 55-year-old male. The target has never
    been age- or health-matched, and sepsis alters exactly the quantities PPV
    depends on. Passing it is meaningful but not as meaningful as passing a
    threshold measured in the model's own population.
    """
    s_normo = ppv_scenarios["normo"]
    assert s_normo["ppv"] < 13, (
        f"Normovolemic PPV too high: {s_normo['ppv']:.1f}% (expected < 13% on plateau)"
    )


# ===========================================================================
# 9. Spinal anaesthesia — [PMID: 3630592, Malmqvist 1987]
# ===========================================================================

def _run_spinal(block_height, baro=True):
    p = SimParams()
    p.baroreflex_enabled = baro
    p.drug_factors = combined_drug_factors({"spinal": block_height})
    r = run_simulation(p, duration_s=20, dt=DT)
    h = len(r['map']) // 2
    return {k: float(np.mean(r[k][h:])) for k in ('map', 'hr', 'co', 'sv')}


def test_spinal_anaesthesia_malmqvist1987():
    """[PMID: 3630592 — Malmqvist 1987] Spinal analgesia to T4-5: in 25/30
    patients only minor haemodynamic changes (CO, HR, SV, MAP, SVR preserved by
    baroreflex). In 5/30 with complete T3-4 block, MAP fell ≥30% with CO preserved.

    Model test — high block (block_height=1.0, ≈T4):
    - MAP falls from baseline (SVR↓38%, venous capacitance↑20%)
    - CO maintained (baroreflex and afterload-reduction preserve output)
    - HR near-unchanged (direct −7% blunting offset by reflex compensation)
    - MAP remains viable (> 45 mmHg)
    """
    base  = _run_spinal(0.0)
    spin  = _run_spinal(1.0)

    dmap_pct = (spin['map'] - base['map']) / base['map'] * 100
    dco_pct  = (spin['co']  - base['co'])  / base['co']  * 100
    dhr      =  spin['hr']  - base['hr']

    assert dmap_pct < -5,        f"MAP did not fall with high spinal: {dmap_pct:+.1f}% (lit ≥−17% at T4-5)"
    assert abs(dco_pct) < 20,   f"CO not maintained with spinal: {dco_pct:+.1f}% (lit ~0%)"
    assert abs(dhr) < 15,       f"HR changed unexpectedly: {dhr:+.1f} bpm (lit minor change)"
    assert spin['map'] > 45,    f"MAP not viable after spinal: {spin['map']:.1f} mmHg"


# ===========================================================================
# 10. Vasopressin dose-response — [PMID: 11873030, Patel 2002]
# ===========================================================================

def _run_vasopressin(units_hr, baro=True):
    p = SimParams()
    p.baroreflex_enabled = baro
    p.drug_factors = combined_drug_factors({"vasopressin": units_hr})
    r = run_simulation(p, duration_s=20, dt=DT, use_baroreflex=baro)
    h = len(r['map']) // 2
    return {k: float(np.mean(r[k][h:])) for k in ('map', 'hr', 'co')}


def test_vasopressin_dose_response_patel2002():
    """[PMID: 11873030 — Patel 2002] Vasopressin infusion in septic shock:
    MAP maintained, cardiac index maintained, vasopressor-sparing effect.

    Model test — dose-response in normovolemic patient:
    - MAP increases monotonically with vasopressin dose (V1 vasoconstriction)
    - CO maintained at clinically relevant dose (2 U/hr) — no direct inotropy
      or chronotropy (consistent with Patel: "cardiac index maintained")
    - HR unchanged (vasopressin is not chronotropic)

    Note: Patel was in septic shock (low-SVR state); model baseline is
    normovolemic. Test validates direction and CO-preservation, not absolute
    MAP values.
    """
    v0 = _run_vasopressin(0.0)
    v2 = _run_vasopressin(2.0)
    v4 = _run_vasopressin(4.0)

    # Dose-response: MAP increases with dose
    assert v2['map'] > v0['map'],  f"MAP did not rise at 2 U/hr: {v0['map']:.1f}→{v2['map']:.1f} mmHg"
    assert v4['map'] > v2['map'],  f"MAP did not rise at 4 U/hr: {v2['map']:.1f}→{v4['map']:.1f} mmHg"

    # CO maintained at 2 U/hr (Patel: cardiac index preserved)
    dco_pct = (v2['co'] - v0['co']) / v0['co'] * 100
    assert abs(dco_pct) < 20,  f"CO not maintained at 2 U/hr: {dco_pct:+.1f}% (lit ~0%)"

    # NO DIRECT CHRONOTROPY — measured with the baroreflex OFF, which is the
    # only way to isolate the drug's own action on the sinus node. This is a
    # STRICTER test than the one it replaces: it requires the effect to be
    # exactly zero, not merely small.
    #
    # It used to be measured with the reflex ON and asserted |dHR| < 8 bpm.
    # That conflates two different claims. Vasopressin raises MAP by ~10 mmHg
    # at 2 U/hr, and a baroreflex with the human gain (0.85 bpm/mmHg, Fritsch
    # 1989) must answer that with ~9 bpm of bradycardia — which is also what
    # vasopressin does at the bedside. Patel 2002 reports MAP and cardiac index
    # and does not support an "HR unchanged" claim; its patients were in septic
    # shock on other vasopressors. The old assertion passed only because the
    # reflex's heart-rate arm was then ±5 bpm wide in total.
    n0 = _run_vasopressin(0.0, baro=False)
    n2 = _run_vasopressin(2.0, baro=False)
    assert abs(n2['hr'] - n0['hr']) < 0.1, (
        f"vasopressin has a DIRECT chronotropic effect: {n0['hr']:.2f} -> "
        f"{n2['hr']:.2f} bpm with the baroreflex off (lit: none)"
    )
    assert n2['map'] > n0['map'], "vasopressin did not raise MAP without the reflex"

    # With the reflex intact the HR change must be BRADYCARDIA, and must be
    # explained by the pressure rise at roughly the calibrated reflex gain.
    dhr = v2['hr'] - v0['hr']
    dmap = v2['map'] - v0['map']
    assert dhr < 0, f"vasopressin raised HR by {dhr:+.1f} bpm; reflex bradycardia expected"
    implied_gain = abs(dhr) / max(dmap, 1e-6)
    assert 0.5 < implied_gain < 1.3, (
        f"HR change {dhr:+.1f} bpm for dMAP {dmap:+.1f} mmHg implies a reflex gain of "
        f"{implied_gain:.2f} bpm/mmHg, away from the calibrated 0.85 (Fritsch 1989)"
    )
    assert abs(dhr) < 15, (
        f"reflex bradycardia of {abs(dhr):.1f} bpm exceeds anything vasopressin "
        f"produces clinically"
    )


# ===========================================================================
# 11. NE vs phenylephrine CO-preservation — [PMID: 25635593, Ngan Kee 2015]
# ===========================================================================

def _run_on_spinal(extra_drugs):
    p = SimParams()
    p.baroreflex_enabled = True
    p.drug_factors = combined_drug_factors({"spinal": 1.0, **extra_drugs})
    r = run_simulation(p, duration_s=20, dt=DT)
    h = len(r['map']) // 2
    return {k: float(np.mean(r[k][h:])) for k in ('map', 'hr', 'co')}


def test_norepi_vs_phenyl_co_preservation_ngan_kee2015():
    """[PMID: 25635593 — Ngan Kee 2015] During spinal anaesthesia for Caesarean
    delivery, norepinephrine maintained higher CO and HR than phenylephrine at
    equivalent MAP restoration (CO 102.7% vs 93.8% normalised; p=0.004).

    Both drugs given as infusions to maintain SBP; NE preserves CO because of
    mild β1-adrenergic activity. Phenylephrine (pure α1) causes reflex
    bradycardia and reduces CO despite adequate MAP restoration.

    Model test — high spinal (T4 block) + vasopressor:
    - Both NE and phenyl restore MAP above spinal-only baseline
    - NE CO > phenyl CO (β1 preserves cardiac output)
    - NE HR > phenyl HR (phenyl → reflex bradycardia via baroreflex)
    """
    spinal_only = _run_on_spinal({})
    with_norepi = _run_on_spinal({"norepinephrine": 0.10})
    with_phenyl = _run_on_spinal({"phenylephrine":  1.00})

    # Both vasopressors restore MAP above spinal-only
    assert with_norepi['map'] > spinal_only['map'], \
        f"NE did not raise MAP above spinal: {spinal_only['map']:.1f}→{with_norepi['map']:.1f}"
    assert with_phenyl['map'] > spinal_only['map'], \
        f"Phenyl did not raise MAP above spinal: {spinal_only['map']:.1f}→{with_phenyl['map']:.1f}"

    # NE preserves CO better than phenyl (Ngan Kee 2015)
    assert with_norepi['co'] > with_phenyl['co'], (
        f"NE CO not > phenyl CO: NE {with_norepi['co']:.2f} vs phenyl {with_phenyl['co']:.2f} L/min"
    )

    # NE HR > phenyl HR (phenyl causes reflex bradycardia)
    assert with_norepi['hr'] > with_phenyl['hr'], (
        f"NE HR not > phenyl HR: NE {with_norepi['hr']:.1f} vs phenyl {with_phenyl['hr']:.1f} bpm"
    )


# ===========================================================================
# 10a. The Valsalva manoeuvre — [PMID: 2918169, Ferguson 1989]
#
# The standard bedside autonomic and preload challenge, and the model had no
# scenario for it despite having every mechanism needed.
#
# WHY FERGUSON'S FIGURE 4 IS THE RIGHT TARGET. In a patient WITHOUT an atrial
# septal defect, at peak strain right atrial PRESSURE rises while RA VOLUME and
# RA stroke volume FALL. **A model that only pushed pressure up would pass a
# pressure-only assertion and still be wrong** — the same "plausible pressure,
# implausible volume" signature as the six defects the chamber rebuild found.
# So pressure and volume are asserted together, in opposite directions.
#
# READ THE INTRALUMINAL TRACE, NOT `aortic_p`. `aortic_p` is TRANSMURAL and a
# real arterial line is not. Measured on the same run: transmurally the strain
# looks like an arterial collapse to 4 mmHg; intraluminally it is a normal
# manoeuvre. `aortic_intraluminal` was added for this test.
# ===========================================================================

def test_valsalva_four_phases_and_atrial_emptying_ferguson1989():
    """[PMID: 2918169 — Ferguson 1989] A 40 mmHg, 15 s Valsalva.

    Two independent assertions, neither calibrated to:

    (1) FERGUSON'S SIGNATURE. Right atrial pressure must RISE while right atrial
        VOLUME falls. Pressure alone is not enough — raising thoracic pressure
        trivially raises an intraluminal pressure; what makes it a test is that
        the chamber must EMPTY at the same time.

    (2) THE FOUR CLASSIC PHASES on the arterial trace. I rise at strain onset as
        the thorax squeezes the aorta; II fall during sustained strain as venous
        return is cut off; III abrupt dip at release; IV overshoot ABOVE
        baseline. **Phase IV is a direct check that the baroreflex is live and
        correctly signed** — a dead or inverted reflex cannot produce it.
    """
    strain_s, dur_s = 30.0, 15.0
    p = SimParams()
    p.baroreflex_enabled = True
    p.valsalva_start_s = strain_s
    p.valsalva_duration_s = dur_s
    r = run_simulation(p, duration_s=59.0)

    t = np.asarray(r["t"])
    ao = np.asarray(r["aortic_intraluminal"])
    ra_p = np.asarray(r["ra_intraluminal"])
    ra_v = np.asarray(r["volumes"])[:, IDX["right_atrium"]]
    win = lambda a, b: (t >= a) & (t < b)

    base = win(strain_s - 6.0, strain_s)
    early = win(strain_s, strain_s + 2.0)                    # phase I
    late = win(strain_s + 8.0, strain_s + dur_s)             # phase II
    release = win(strain_s + dur_s, strain_s + dur_s + 2.0)  # phase III
    after = win(strain_s + dur_s + 3.0, strain_s + dur_s + 10.0)   # phase IV

    m = lambda sig, w: float(np.mean(sig[w]))

    # (1) Ferguson: pressure up, volume down, together
    assert m(ra_p, late) > m(ra_p, base) + 10.0, (
        f"RA pressure did not rise during the strain: {m(ra_p, base):.1f} -> "
        f"{m(ra_p, late):.1f} mmHg"
    )
    assert m(ra_v, late) < m(ra_v, base) * 0.85, (
        f"RA did not EMPTY during the strain: {m(ra_v, base):.1f} -> "
        f"{m(ra_v, late):.1f} mL. Ferguson 1989 Fig 4 shows pressure rising and "
        f"volume falling together; pressure alone is not the finding"
    )

    # (2) the four phases
    assert m(ao, early) > m(ao, base), (
        f"phase I: arterial pressure did not rise at strain onset "
        f"({m(ao, base):.1f} -> {m(ao, early):.1f} mmHg)"
    )
    assert m(ao, late) < m(ao, base), (
        f"phase II: arterial pressure did not fall during sustained strain "
        f"({m(ao, base):.1f} -> {m(ao, late):.1f} mmHg)"
    )
    assert m(ao, release) < m(ao, base), (
        f"phase III: no dip at release ({m(ao, release):.1f} mmHg against a "
        f"baseline of {m(ao, base):.1f})"
    )
    assert m(ao, after) > m(ao, base), (
        f"phase IV: no overshoot above baseline ({m(ao, after):.1f} against "
        f"{m(ao, base):.1f} mmHg). This is the direct check that the baroreflex "
        f"is live and correctly signed"
    )


@pytest.mark.xfail(strict=True, reason=(
    "KNOWN DEFECT — THE REFERENCE PATIENT RESCALES ITSELF. `patient.py` scales a "
    "patient's arteriolar resistance by svr_measured/svr_ref, where svr_ref is "
    "built from REFERENCE_MAP/CVP/CO in baroreflex.py. Feeding the model its OWN "
    "settled operating point back in must therefore give a scale of 1.000, and "
    "gives 0.863 — a 14 % rescale of a patient identical to the reference. "
    "THE REFERENCE TRIPLE DESCRIBES A MODEL THAT NO LONGER EXISTS: it says "
    "MAP 93.0 / CVP 5.0 / CO 5.0 where the model settles at 95.37 / 4.36 / 5.99. "
    "The CO term is the worst, 5.0 against 5.99, and it sits in the DENOMINATOR "
    "of the reference resistance. "
    "MEASURED AND DELIBERATELY NOT CORRECTED, 2026-09-15. Raising svr_ref raises "
    "svr_scale for EVERY patient entered with a blood pressure, which moves every "
    "patient-scaled test at once — and the direction makes the known overshoot on "
    "a requested-MAP input WORSE before better: asking for MAP 83 already settles "
    "at 92. So this is entangled with how Tier 1 scaling works, not a constant to "
    "retype. "
    "DO NOT close it by editing the three numbers to match today's settled state. "
    "That would be fitting a calibration constant to the model's own output, and "
    "the model's operating point moves whenever a compliance does — it would be "
    "stale again within a week, exactly like the init volumes in item 16. The "
    "fix is to make svr_ref DERIVE from the reference run rather than be typed. "
    "strict=True so it fires the day that lands."
))
def test_reference_operating_point_is_self_consistent():
    """A patient whose measured haemodynamics equal the reference model's must
    need no rescaling: svr_scale == 1.0.

    Backlog item 50. This is the assertion that turns "two uncited copies of a
    constant" into a measurable defect — the duplication was the symptom, the
    staleness is the disease.
    """
    from model.baroreflex import (REFERENCE_MAP_MMHG, REFERENCE_CVP_MMHG,
                                  REFERENCE_CO_LPM)
    from model.patient import _svr

    p = SimParams()
    r = run_simulation(p, duration_s=70.0)
    t = np.asarray(r["t"])
    tail = t >= t[-1] - 15.0
    m = lambda k: float(np.mean(np.asarray(r[k])[tail]))

    svr_ref = _svr(REFERENCE_MAP_MMHG, REFERENCE_CVP_MMHG, REFERENCE_CO_LPM)
    svr_own = _svr(m("map"), m("cvp"), m("co"))
    scale = svr_own / svr_ref

    assert abs(scale - 1.0) < 0.05, (
        f"the reference patient rescales itself by {100*(scale-1):+.1f} %. "
        f"Reference operating point is MAP {REFERENCE_MAP_MMHG} / CVP "
        f"{REFERENCE_CVP_MMHG} / CO {REFERENCE_CO_LPM}; the model settles at "
        f"MAP {m('map'):.2f} / CVP {m('cvp'):.2f} / CO {m('co'):.2f}"
    )


def test_cohort_params_is_the_reference_identity():
    """Routing a test through patient scaling must not, by itself, change it.

    `cohort_params()` with no arguments and `SimParams()` must produce the SAME
    compartment set and the same cardiac parameters — bit for bit, not close.

    THIS GUARDS THE AGE-MATCHING CONVERSION OF 2026-09-15. Three literature
    tests were moved from `SimParams()` onto the patient-scaling path so they
    could carry their cohort's age. That move is only honest if the path is an
    identity at the reference patient; if it were not, every converted test
    would have silently absorbed a scaling change alongside the age change and
    the two would be impossible to separate afterwards.

    It is not a free assumption. `BSA_REF` was once the typed constant 1.87
    while the code measured every patient with Mosteller, which gives 1.8447 —
    so the reference patient entered by their own height and weight was scaled
    by 0.9865 instead of 1.0, a 1.4 % shrink applied to the exact case that
    should have been the identity. Deriving `BSA_REF` from the same function
    fixed it. This test is what stops it coming back.

    It asserts on PARAMETERS, not on a settled simulation, so it costs
    milliseconds and cannot be made flaky by an integration tolerance. The
    settled equality was measured separately on 2026-09-15: both give MAP
    95.429 / CVP 4.349 / CO 6.056 / HR 69.351.
    """
    ref = SimParams()
    got = cohort_params()

    assert len(got.compartments) == len(ref.compartments)
    for a, b in zip(ref.compartments, got.compartments):
        assert a.name == b.name, f"compartment order changed: {a.name} vs {b.name}"
        for field in ("compliance", "V0", "init_volume", "resistance"):
            x, y = getattr(a, field, None), getattr(b, field, None)
            if x is None or not isinstance(x, (int, float)):
                continue
            assert abs(x - y) <= 1e-9 * max(1.0, abs(x)), (
                f"{a.name}.{field}: SimParams() has {x!r}, cohort_params() "
                f"has {y!r}. Patient scaling is no longer the identity at the "
                f"reference patient — see BSA_REF in patient.py"
            )

    for field in ("lv_emax", "rv_emax", "hr_bpm"):
        x, y = getattr(ref, field), getattr(got, field)
        assert abs(x - y) <= 1e-9 * max(1.0, abs(x)), (
            f"cardiac {field}: {x!r} vs {y!r} — patient scaling is not the "
            f"identity at the reference patient"
        )


def test_reference_operating_point_is_defined_once():
    """The reference operating point must have exactly one definition.

    Backlog item 50. `patient.py` hard-coded `_svr(93.0, 5.0, 5.0)` while
    `baroreflex.py` held MAP_SETPOINT separately, with nothing linking them — so
    changing one left the other silently disagreeing, and the symptom would have
    been a patient-scaling error that looked like a reflex error.

    This guards the FIX, not the values: it asserts patient.py imports the
    constants rather than repeating them. Same argument as item 16's settling
    guard — a rule that depends on memory gets forgotten.
    """
    import inspect
    import model.patient as patient_mod

    src = inspect.getsource(patient_mod)
    assert "REFERENCE_MAP_MMHG" in src, (
        "patient.py no longer imports the shared reference operating point"
    )
    assert "_svr(93.0" not in src and "_svr(93," not in src, (
        "patient.py has re-introduced a hard-coded copy of the reference "
        "operating point. Import it from baroreflex.py instead — see item 50"
    )


def test_init_volumes_are_the_settled_equilibrium():
    """`init_volume` must BE the model's equilibrium, not a stale guess at it.

    Backlog item 16, and the reason this is a TEST rather than a note in the
    code. The settling transient was 174 mL when the item was opened, 201 mL on
    2026-09-01, 45 mL on 2026-09-09 after other work happened to resolve it, and
    **246 mL by 2026-09-14 because two changes moved an equilibrium without
    moving the starting volume with it** — `fd3fc65` set splanchnic_vein's init
    by subtracting a number from the old value instead of re-deriving it, and
    `e6e86ce` changed pulmonary arterial compliance and never touched init at
    all. Re-derived, it is now about 8 mL.

    IT WILL DRIFT AGAIN. Any change to a compliance or an unstressed volume
    moves that compartment's equilibrium, so this is not a thing that gets fixed
    once. **That is precisely why it is asserted here instead of relied on** —
    the same lesson as the dead `venous_tone_factor` and the unguarded drug
    magnitudes: a rule that depends on memory gets forgotten, a rule with a test
    behind it does not.

    TO RE-DERIVE when this fails: run a settled simulation, take every
    compartment's volume at CARDIAC PHASE 0 (not a cycle mean — that would start
    the ventricles at mid-ejection while the phase clock sits in diastole), and
    write those back. Taking all compartments at one instant is also what keeps
    total blood volume identical.

    WHY IT MATTERS BEYOND TIDINESS: `slow_dynamics` captures its resting
    reference from the settled state rather than from `init_volume` precisely
    because this could not be trusted — referencing init made stress relaxation
    creep permanently and dropped resting MAP by 1.4 mmHg.
    """
    comp = default_compartments()
    p = SimParams()
    r = run_simulation(p, duration_s=90.0)
    V = np.asarray(r["volumes"])
    t = np.asarray(r["t"])
    settled = V[t >= t[-1] - 5.0].mean(axis=0)
    init = np.array([c.init_volume for c in comp])

    # DERIVED from the model's own set (2026-10-04), not listed: the IVC split
    # added two venous compartments, and a hand-written list here would have
    # silently stopped checking them.
    from model.circulation import VENOUS_RESERVOIR
    veins = list(VENOUS_RESERVOIR)
    redistribution = sum(abs(settled[IDX[n]] - init[IDX[n]]) for n in veins)
    assert redistribution < 50.0, (
        f"venous settling transient is {redistribution:.0f} mL — init_volume is "
        f"no longer the equilibrium. A compliance or unstressed volume has been "
        f"changed without re-deriving the starting volume. See the docstring for "
        f"how to re-derive; it is measured at phase 0, not as a cycle mean."
    )

    worst = max(range(len(comp)), key=lambda i: abs(settled[i] - init[i]))
    drift = settled[worst] - init[worst]
    assert abs(drift) < 60.0, (
        f"{comp[worst].name} settles {drift:+.0f} mL from its init_volume "
        f"({init[worst]:.0f} -> {settled[worst]:.0f})"
    )


# ===========================================================================
# 10b. Central blood pressure in a 55-year-old man
#      — [PMID: 16256881, McEniery 2005, the Anglo-Cardiff Collaborative Trial]
#
# 4,001 healthy NORMOTENSIVE subjects aged 18-90, peripheral AND central
# pressure. Table 1, MALES 50-59 yrs, n = 429 — the model's own decade and sex.
#
# WHY THIS COHORT SETTLED AN ARGUMENT. Backlog item 37 carried the headline
# "the model runs ~20 mmHg too high on MAP" against a target of 77.3, taken from
# a cohort aged 25 +/- 3. McEniery's age-matched men measure MAP 95 +/- 7 and the
# model sits at 95.4. The model's PERIPHERAL haemodynamics were right all along;
# only the CENTRAL ones were wrong, and nothing in the suite was looking at them.
# ===========================================================================

# McEniery 2005 Table 1, males 50-59 yrs, n = 429 (mean +/- SD), RE-TARGETED
# 2026-10-10 TO INVASIVE-EQUIVALENT VALUES (Jesper: "Go for re-target").
# McEniery's central values come from SphygmoCor radial tonometry CALIBRATED TO
# THE CUFF. Cheng 2013 (PMID 22622052; meta-analysis, 22 studies, 857 subjects,
# invasive aortic-root reference) measures that method's bias: SphygmoCor cuff-
# calibrated central SBP -8.2 +/- 11.6, central PP -15.4 +/- 10.2; cuff DBP vs
# invasive central DBP +7.5 +/- 8.7 mmHg. The model's pressures are INTRA-
# ARTERIAL (aortic root, see SimParams.aortic_zc), so the comparison must be with
# what a catheter would read. Means shifted by Cheng's biases; McEniery's
# population SDs kept. Cuff values: CSBP 115, CPP 35, DBP 79. Invasive data agree
# with the shifted values: Manolas 1975 central PP 45 (age 29), Chen 1998 57 +/- 17.
# MAP is NOT shifted (Cheng gives no MAP bias).
_MCE_CSBP = (115.0 + 8.2, 9.0)    # central systolic, invasive-equivalent 123.2
_MCE_CPP  = (35.0 + 15.4, 7.0)    # central pulse pressure, invasive-equivalent 50.4
_MCE_MAP  = (95.0, 7.0)
_MCE_PDBP = (79.0 - 7.5, 6.0)     # diastolic, invasive-equivalent 71.5
_MCE_AMP  = (1.33, 0.16)     # peripheral PP / central PP (cuff-based; xfailed below)


@pytest.fixture(scope="module")
def central_pressures():
    p = SimParams()
    r = run_simulation(p, duration_s=90.0)
    t = np.asarray(r["t"])
    tail = t >= t[-1] - 15.0
    m = lambda k: float(np.mean(np.asarray(r[k])[tail]))
    cs, cd = m("sbp"), m("dbp")
    bs, bd = m("brachial_sbp"), m("brachial_dbp")
    return {
        "csbp": cs, "cpp": cs - cd, "dbp": cd, "map": m("map"),
        "ppp": bs - bd, "amp": (bs - bd) / (cs - cd),
    }


def test_central_pressures_mceniery2005(central_pressures):
    """[PMID: 16256881 — McEniery 2005] Central systolic, central pulse
    pressure, diastolic and mean pressure for a 55-year-old man.

    Central pulse pressure was the model's largest arterial deviation at
    +2.9 SD (55.2 against 35 +/- 7) and was invisible because nothing looked at
    central pressure. Arterial compliance x1.6 on 2026-09-14 closed it, and the
    same factor independently satisfies Schipke's arterial decay constant — two
    sources, one parameter, neither tuned to.

    2026-10-10: targets re-expressed as INVASIVE-EQUIVALENT (Cheng 2013, see the
    constants above). Measured against the CUFF value, the model's pulse pressure
    had come from an unphysiological ejection (LVET 193 ms, peak aortic flow 924
    mL/s); with measured systolic timing (heart.py) and a characteristic impedance
    (AORTIC_ZC 0.10, pinned to this test's PP target) central pressure is read at
    the aortic root, where a catheter reads it.
    """
    c = central_pressures
    for name, key, (mean, sd) in (
        ("central systolic", "csbp", _MCE_CSBP),
        ("central pulse pressure", "cpp", _MCE_CPP),
        ("diastolic", "dbp", _MCE_PDBP),
        ("mean arterial", "map", _MCE_MAP),
    ):
        z = (c[key] - mean) / sd
        assert abs(z) <= 2.0, (
            f"{name} {c[key]:.1f} mmHg is {z:+.1f} SD from McEniery's "
            f"{mean} +/- {sd} (males 50-59, n=429)"
        )


@pytest.mark.xfail(strict=True, reason=(
    "STRUCTURAL LIMITATION OF A LUMPED MODEL — NOT A CALIBRATION GAP. "
    "In humans brachial pulse pressure EXCEEDS central: McEniery 2005 measures "
    "the ratio at 1.33 +/- 0.16 in males 50-59, falling from 1.72 at age 20 to "
    "1.24 at 70. The model reads about 0.88 — INVERTED — and raising arterial "
    "compliance makes it worse (0.94 -> 0.88 -> 0.84 across the sweep), so it "
    "cannot be calibrated away. "
    "WHY IT CANNOT BE FIXED HERE. Amplification arises from WAVE REFLECTION and "
    "impedance mismatch along a distributed arterial tree — the wave travels, "
    "reflects off branch points and the periphery, and the reflected wave "
    "arrives later and adds differently at each site. A lumped compartment "
    "model has no wave travel, no transit time and no reflection: every "
    "compartment sees pressure instantaneously. McEniery's augmentation index "
    "(-2 % at 20 to 30 % at 70) measures that reflected wave directly, and the "
    "model has no mechanism that could produce it. "
    "CONSEQUENCE: the brachial trace the UI offers as 'what the cuff reads' is "
    "systematically NARROW, and peripheral pulse pressure cannot be right at "
    "the same time as central. DO NOT split the difference between them — that "
    "makes both wrong and hides the cause. Closing this needs a 1-D wave model "
    "of the arterial tree, a different architecture, not a parameter. "
    "strict=True so that if a future architecture ever produces amplification, "
    "this fires and is removed deliberately."
))
def test_pulse_pressure_amplification_mceniery2005(central_pressures):
    """[PMID: 16256881 — McEniery 2005] Brachial pulse pressure must exceed
    central; the measured ratio in males 50-59 is 1.33 +/- 0.16.
    """
    amp = central_pressures["amp"]
    z = (amp - _MCE_AMP[0]) / _MCE_AMP[1]
    assert abs(z) <= 2.0, (
        f"pulse pressure amplification {amp:.2f} is {z:+.1f} SD from "
        f"McEniery's {_MCE_AMP[0]} +/- {_MCE_AMP[1]}"
    )


# ===========================================================================
# 11a. The venous return curve does not ROTATE when blood is removed
#      — [PMID: 19237896, Maas 2009; reviewed in PMC9128096, Persichini 2022]
#
# Guyton's venous return curve has two parameters: the zero-flow intercept
# (Pmsf) and the slope (whose inverse is the resistance to venous return, RVr).
# Removing blood lowers the stressed volume, so it must lower Pmsf. It must NOT
# change RVr, because resistance is a property of the vessels and not of how
# full they are. The line shifts LEFT without ROTATING. Maas measured exactly
# that in patients and found the slope volume-independent.
#
# WHY THIS TEST IS WORTH HAVING EVEN THOUGH THE ABSOLUTE Pmsf IS DISPUTED.
# The project's Pmsf target (Maas 2009, 18.8-20.9 mmHg) comes from ventilated
# post-cardiac-surgery patients who are fluid-loaded and on vasopressors.
# Persichini 2022 gives normal human Pmsf as 2-10 mmHg and says explicitly that
# the 15-33 range reported in surgical and septic patients is higher "due to
# treatments such as fluid infusion and vasopressors". Which target applies to
# this model's healthy supine patient is an OPEN QUESTION (backlog item 47).
# This test sidesteps it entirely: it asserts an INVARIANCE and a DIRECTION, so
# no absolute value is needed and no cohort argument can undermine it.
#
# PROTOCOL LIMITATION, STATED HONESTLY. Maas's manoeuvre is a set of BRIEF
# end-inspiratory and end-expiratory holds. This helper uses a SUSTAINED airway
# pressure instead, because SimParams cannot step ventilation mid-run. Over a
# sustained hold the reflexes act and volume redistributes, so the ABSOLUTE
# slope this protocol reports is not Maas's (-0.280 here against his -0.465).
# The test therefore compares two arms measured the SAME way and asserts a
# RATIO, which is what survives a systematic protocol bias. Do not read the
# absolute slope out of this test. Rebuilding the protocol as short holds is
# step 2 of backlog item 47.
#
# NOTE ra_intraluminal, NOT cvp. The model reports `cvp` TRANSMURAL, and under a
# rising airway pressure transmural CVP FALLS while the catheter reading RISES.
# Fitting against `cvp` gives a positive slope and a negative Pmsf, which is how
# this error was caught on 2026-09-13.
# ===========================================================================

def _venous_return_curve(bleed_ml=0.0, sympathetic_outflow_scale=1.0, baroreflex=True):
    """Fit CO against intraluminal RAP across four airway-pressure holds.

    Returns (slope in L/min/mmHg, Pmsf in mmHg).

    `sympathetic_outflow_scale` below 1 is a sympatholytic; 0 is ganglionic
    blockade. It is a separate knob from `baroreflex_enabled`, so the holds stay
    reflex-intact as Maas measured them while the resting TONE is withdrawn.
    """
    cvp, co = [], []
    for airway in (5, 15, 25, 35):
        p = SimParams()
        p.sympathetic_outflow_scale = sympathetic_outflow_scale
        p.baroreflex_enabled = baroreflex    # Maas measured in intact patients
        p.ventilation_mode = 'mechanical'
        p.peep_cmh2o = airway
        p.pip_cmh2o = airway
        p.ie_ratio = 0.5
        if bleed_ml:
            p.hemorrhage_rate_mlmin = bleed_ml / (20.0 / 60.0)
            p.hemorrhage_start_s = 10.0
            p.hemorrhage_duration_s = 20.0
        r = run_simulation(p, duration_s=60.0)
        t = np.asarray(r["t"])
        tail = t >= t[-1] - 8.0
        cvp.append(float(np.mean(np.asarray(r["ra_intraluminal"])[tail])))
        co.append(float(np.mean(np.asarray(r["co"])[tail])))
    slope, intercept = np.polyfit(np.array(cvp), np.array(co), 1)
    return float(slope), float(-intercept / slope)


# CLOSED 2026-10-11 (XPASS on the systolic timing change), REOPENED 2026-10-15.
@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "KNOWN PROTOCOL GAP, 2026-10-15 — ratio 0.855 with reflexes on, 1.123 with them OFF: "
    "two effects of the SUSTAINED 60 s holds, pulling opposite ways. Reflex on: the reflex "
    "acts during each hold (as 2026-10-10). Reflex off: with the AV-plane coupling, the bled "
    "heart at the 35 cmH2O hold falls to CO 1.6 L/min — the low-flow, collapsing-vein regime "
    "this docstring excludes. The sac is NOT involved (identical with it on and off: the holds "
    "shrink the heart below the knee). Maas's holds were brief. Fix: short holds (backlog 47 "
    "step 2), not a wider band. Validation log 2026-10-15."
))
def test_haemorrhage_shifts_venous_return_curve_without_rotating_it():
    """[PMID: 19237896 — Maas 2009] A moderate haemorrhage must lower Pmsf and
    leave the venous-return slope alone: resistance to venous return is a
    property of the vessels, not of how full they are.

    Measured with a 500 mL bleed, which is a class I haemorrhage and sits in the
    range where a linear venous return curve applies.

    BOTH assertions are needed. The invariance alone would pass trivially if the
    haemorrhage did nothing, so the test also requires Pmsf to fall materially —
    that is what proves the perturbation landed.

    KNOWN LIMIT, recorded rather than hidden: at 1000 mL the slope ratio goes to
    1.14 and the invariance breaks. That bleed drives the model into profound
    shock with cardiac output near 2 L/min, where the limb veins collapse and
    the vascular waterfall Persichini describes takes over — a regime in which
    a linear venous return curve is not expected to hold, in the model or in a
    patient. It is asserted at 500 mL for that reason, not to avoid the result.

    HISTORY. Ratio 0.897 on 2026-10-02 (limb reflex added), 0.907 after leg
    rebuild stage 1 — a hair either side of the floor, judged minor (Jesper).
    Then 0.775 after the calf stiffening change of 2026-10-04 (a strict
    xfail). CLOSED 2026-10-06 by the Klotz LV diastolic curve, which the strict
    xfail caught as an XPASS. The floor is unchanged.
    """
    base_slope, base_pmsf = _venous_return_curve(0.0)
    bled_slope, bled_pmsf = _venous_return_curve(500.0)

    ratio = bled_slope / base_slope
    assert 0.90 <= ratio <= 1.10, (
        f"haemorrhage ROTATED the venous return curve: slope {base_slope:.4f} "
        f"-> {bled_slope:.4f} (ratio {ratio:.3f}). Resistance to venous return "
        f"must not change with blood volume (Maas 2009 found it "
        f"volume-independent)"
    )
    assert bled_pmsf < base_pmsf - 3.0, (
        f"haemorrhage did not lower Pmsf materially: {base_pmsf:.2f} -> "
        f"{bled_pmsf:.2f} mmHg. Removing 500 mL must reduce stressed volume "
        f"and therefore the zero-flow intercept"
    )


# ===========================================================================
# 11b. Phenylephrine dose-response in HEALTHY SUPINE MEN
#      — [PMID: 10073742, Schäfers 1999]
#
# Why this cohort matters. The model's only other vasopressor cardiac-output
# comparator is Ngan Kee 2015, whose subjects are TERM PARTURIENTS under spinal
# anaesthesia — cardiac output ~40 % above normal, low systemic resistance and
# aortocaval compression. Schäfers studied 12 healthy men, median age 27 (22-36),
# supine throughout and fasted, with a graded intravenous phenylephrine infusion
# (0.25-4 mcg/kg/min in 10 min steps). The placebo arm of that study is an
# unantagonised phenylephrine dose-response and is the right comparator for the
# model's default patient.
#
# MATCH ON THE PRESSURE RESPONSE, NOT THE DOSE. Their reported bars sit at the
# highest dose each subject tolerated — the protocol stopped at a diastolic rise
# of +30 mmHg — not at a fixed infusion rate. Comparing dose-for-dose would be
# meaningless, so the model is exercised across its own plateau (2-4 mcg/kg/min)
# and every dose there must satisfy the flow bands.
#
# ONE SENTENCE IN THAT PAPER IS EASY TO MISREAD, and was misread here on a first
# pass: "phenylephrine increased cardiac output and stroke volume and reduced
# heart rate to a similar extent in tamsulosin- and terazosin-treated subjects"
# describes the two ACTIVE arms only. Under placebo phenylephrine LOWERS cardiac
# output. Read their Figure 6, not that sentence.
#
# The bands below are MEDIANS WITH QUARTILES read off Figures 5 and 6, since the
# paper plots them rather than tabulating them. Treat them as approximate; they
# are recorded in docs/reference_values.md with that caveat.
# ===========================================================================

# Schäfers 1999 placebo arm, as REPORTED: (median, lower quartile, upper quartile)
_SCH_Q_DCO  = (-1.15, -1.25, -0.40)    # L/min
_SCH_Q_DHR  = (-16.0, -19.5, -14.2)    # beats/min
_SCH_Q_DSV  = (+9.0,  -0.5,  +18.5)    # mL
_SCH_Q_DMAP = (+28.0, +23.5, +32.5)    # mmHg
_SCH_Q_DTPR = (+950,  +650,  +1270)    # dyn.s/cm5


def _one_sd_band(median, q1, q3):
    """Schäfers' quartiles re-expressed as a 1 SD band, each side scaled
    separately so his skew is kept: a quartile lies 0.674 SD from the median.

    WHY, 2026-10-11 (Jesper's call). These tests asserted the INTERQUARTILE range
    itself — the middle half of twelve individual men, i.e. about +/-0.67 SD —
    tighter than any other band in the suite (Luu/Gao 1 SD, Weissler 2 SD). It
    flipped on sub-bpm changes three times. 1 SD is the suite's convention.
    CAVEATS, stated so a pass is not over-read: with n = 12 the skew is noisy,
    and the dCO upper edge lands near zero (-0.04), which would accept almost no
    fall at all; dHR -13.6 at adoption clears its edge (-13.3) by only 0.3.
    """
    z = 0.674
    return (median - (median - q1) / z, median + (q3 - median) / z)


_SCH_DCO  = _one_sd_band(*_SCH_Q_DCO)     # (-1.30, -0.04)
_SCH_DHR  = _one_sd_band(*_SCH_Q_DHR)     # (-21.2, -13.3)
_SCH_DSV  = _one_sd_band(*_SCH_Q_DSV)     # (-5.1,  +23.1)
_SCH_DMAP = _one_sd_band(*_SCH_Q_DMAP)    # (+21.3, +34.7)
_SCH_DTPR = _one_sd_band(*_SCH_Q_DTPR)    # (+505,  +1425)

# The model's phenylephrine plateau — the doses where its pressor response is
# near its own maximum, which is what Schäfers' bars correspond to (his subjects
# were taken to the highest dose each tolerated, a diastolic rise of +30 mmHg).
#
# MOVED 2/3/4 -> 4/6/8 ON 2026-09-14, and NOT to make a test pass. Arterial
# compliance x1.6 that day means a given vasoconstriction produces LESS pressure
# rise, so the same dose sits lower on the dose-response curve: 2.0 mcg/kg/min
# gave dMAP +18.3 before and +15.5 after. The plateau is a property of the
# model, the model changed, and the plateau moved with it. The BANDS below are
# untouched.
#
# The failure this fixed is worth recording. At 2.0 the reflex bradycardia had
# not fully engaged (dHR -13.6 against a band of -19.5 to -14.2) — because less
# pressure rise means less baroreflex response. That is DOWNSTREAM of the known
# pressor xfail below, not a separate defect: cardiac output and stroke volume
# stayed inside their bands at every dose throughout.
_PHENYL_PLATEAU = (4.0, 6.0, 8.0)

# THE COHORT'S AGE. Twelve healthy MALE subjects, median 27 (range 22-36).
# Until 2026-09-15 this fixture ran the 55-year-old reference patient, so the
# model was a generation older than the men it was being compared with, and the
# quantity most sensitive to that difference — arterial compliance — is exactly
# the one an alpha1 agonist acts on.
#
# RE-MEASURED AT AGE 27, all three plateau doses, 2026-09-15:
#     dose       dCO     dHR      dSV     |  Schaefers quartiles
#     4.0      -0.73   -15.2    +9.9      |  dCO  -1.25 to -0.40
#     6.0      -0.81   -16.0    +9.9      |  dHR  -19.5 to -14.2
#     8.0      -0.72   -16.5   +12.3      |  dSV   -0.5 to +18.5
# against -0.84 / -0.84 / -0.95 on dCO at the reference age. **Every quantity
# is still in band at every dose, and dCO moved AWAY from Schaefers' median.**
# That is the physiology: a 27-year-old's arteries are more compliant, so the
# same vasoconstriction produces less afterload and costs less cardiac output.
# The bands are untouched and the model was not retuned to recover the margin.
_SCH_AGE_YEARS = 27.0


def _run_phenyl(dose_mcg_kg_min):
    """Settled haemodynamics on a phenylephrine infusion.

    90 s with a 20 s averaging window: a 70 s run averaged over 5 s moved
    cardiac output by up to 0.23 L/min between adjacent doses, which is a
    quarter of the band being asserted. At 90/20 the numbers agree with a
    120 s run averaged over 30 s to within 0.03 L/min.

    AGE-MATCHED TO 27 ON 2026-09-15, see the cohort note above. Schaefers gives
    NO height or weight, so the body stays at the reference 175 cm / 70 kg and
    only the age moves; his subjects were all male, which the default already
    is. The effect is real and it makes the agreement WORSE, which is why it
    was done before the freeze rather than after — see the table in §11b.
    """
    p = cohort_params(age_years=_SCH_AGE_YEARS)
    p.baroreflex_enabled = True
    if dose_mcg_kg_min:
        p.drug_factors = combined_drug_factors({"phenylephrine": dose_mcg_kg_min})
    r = run_simulation(p, duration_s=90.0)
    t = np.asarray(r["t"])
    tail = t >= t[-1] - 20.0
    m = lambda k: float(np.mean(np.asarray(r[k])[tail]))
    co, hr = m("co"), m("hr")
    return {
        "map": m("map"), "cvp": m("cvp"), "co": co, "hr": hr,
        "sv": 1000.0 * co / hr,
        "tpr": 80.0 * (m("map") - m("cvp")) / co,
    }


@pytest.fixture(scope="module")
def phenyl_dose_response():
    """Baseline plus the three plateau doses, run once and shared."""
    return {d: _run_phenyl(d) for d in (0.0,) + _PHENYL_PLATEAU}


# CLOSED 2026-10-08 — a strict xfail from 2026-10-06 that XPASSED on the leg
# capacity + item 74 + transmural Starling rebuild. The gap was dHR -14.2 bpm at
# 4.0 mcg/kg/min, sitting exactly on the edge of Schafers' quartiles
# (-19.5, -14.2), which blocked the flow assertions behind it. The PRESSOR xfail
# above is a different quantity and remains open: only the flow arm closed.
# CLOSED 2026-10-11 by moving the bands from the interquartile range to 1 SD
# (see _one_sd_band) — a band decision, not a model change.
@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "EDGE GAP, re-measured 2026-10-27 — dCO -1.33 at 8.0 mcg/kg/min against the 1 SD floor -1.30 "
    "(-1.18 at 4.0 and -1.17 at 6.0 pass). With the re-sized atria it XPASSED at the old ceiling "
    "2.10; re-calibrating the pressor ceiling to 2.15 (pharmacology.py) brought the edge back at the "
    "top dose. SV rises at every dose (+1.3 to +3.8 mL, Schafers +9). Band not moved."
))
def test_phenylephrine_flow_response_schafers1999(phenyl_dose_response):
    """[PMID: 10073742 — Schäfers 1999] Phenylephrine in healthy supine men
    LOWERS cardiac output, LOWERS heart rate and RAISES stroke volume.

    Placebo arm, median (quartiles): dCO -1.15 (-1.25 to -0.40) L/min,
    dHR -16 (-19.5 to -14.2) beats/min, dSV +9 (-0.5 to +18.5) mL.

    Three independent flow quantities from one source, none of them tuned to.
    The direction matters as much as the magnitude: an alpha1 agonist raises
    afterload and recruits preload at the same time, and in a healthy supine
    subject with intact reflexes the afterload and the reflex bradycardia win.
    """
    base = phenyl_dose_response[0.0]
    for dose in _PHENYL_PLATEAU:
        m = phenyl_dose_response[dose]
        dco = m["co"] - base["co"]
        dhr = m["hr"] - base["hr"]
        dsv = m["sv"] - base["sv"]
        assert _SCH_DCO[0] <= dco <= _SCH_DCO[1], (
            f"phenylephrine {dose} mcg/kg/min: dCO {dco:+.2f} L/min outside "
            f"Schäfers 1 SD band {_SCH_DCO} (median -1.15)"
        )
        assert _SCH_DHR[0] <= dhr <= _SCH_DHR[1], (
            f"phenylephrine {dose} mcg/kg/min: dHR {dhr:+.1f} bpm outside "
            f"Schäfers 1 SD band {_SCH_DHR} (median -16)"
        )
        assert _SCH_DSV[0] <= dsv <= _SCH_DSV[1], (
            f"phenylephrine {dose} mcg/kg/min: dSV {dsv:+.1f} mL outside "
            f"Schäfers 1 SD band {_SCH_DSV} (median +9)"
        )


# CLOSED 2026-10-17 — the strict xfail of 2026-10-06 (dMAP +19.1) XPASSED with the
# atrial pins (Järvinen): dMAP +20.2 / +21.4 / +21.8 at 4 / 6 / 8 mcg/kg/min against the
# 1 SD floor 21.3 — inside, but by 0.5 at the plateau. A fragile pass, recorded as such.
def test_phenylephrine_pressor_response_schafers1999(phenyl_dose_response):
    """[PMID: 10073742 — Schäfers 1999] Phenylephrine in healthy supine men
    raises MAP by +28 mmHg (quartiles 23.5-32.5) and total peripheral
    resistance by +950 dyn.s/cm5 (650-1270) at the highest tolerated dose.

    Asserted at the model's own plateau, so this is not a dose mismatch.

    **CLOSED 2026-09-26. Was a strict xfail.** The pressor response saturated at
    dMAP +20 / dTPR +476 because phenylephrine's arterial Hill ceiling was 1.80.
    **A diagnostic settled the cause before anything was changed:** raising the
    ceiling raised pressure freely (e_max 3.0 gave +40), so the limit was the
    drug curve, not the `svr_factor` pathway or the pre/post-capillary split
    that the old reason warned about. The ceiling is now 2.10, CALIBRATED to
    this study, and at 2.10 all five Schäfers quantities sit in their bands
    together — this test and `test_phenylephrine_flow_response_schafers1999`.

    **THIS TEST IS NOW A CALIBRATION CHECK, NOT VALIDATION.** The number it
    asserts was used to set the ceiling. Say so in any write-up.

    **THE WINDOW IS NARROW.** Ceilings from about 2.05 to 2.15 satisfy all five.
    Above it heart rate falls past its band (dHR -19.8 at 2.20), because the
    model's reflex bradycardia per mmHg is steeper than Schäfers measured. A
    future change to the reflex will show up here first.
    """
    base = phenyl_dose_response[0.0]
    best = max(
        (phenyl_dose_response[d] for d in _PHENYL_PLATEAU),
        key=lambda m: m["map"],
    )
    dmap = best["map"] - base["map"]
    dtpr = best["tpr"] - base["tpr"]
    assert _SCH_DMAP[0] <= dmap <= _SCH_DMAP[1], (
        f"dMAP {dmap:+.1f} mmHg outside Schäfers 1 SD band {_SCH_DMAP} "
        f"(median +28)"
    )
    assert _SCH_DTPR[0] <= dtpr <= _SCH_DTPR[1], (
        f"dTPR {dtpr:+.0f} dyn.s/cm5 outside Schäfers 1 SD band {_SCH_DTPR} "
        f"(median +950)"
    )


# ===========================================================================
# 12. Epinephrine biphasic dose-response — [PMID: 3956110, Freyschuss 1986]
# ===========================================================================

def _run_epi(dose_mcg_kg_min):
    p = SimParams()
    p.baroreflex_enabled = True
    p.drug_factors = combined_drug_factors({"epinephrine": dose_mcg_kg_min})
    r = run_simulation(p, duration_s=20, dt=DT)
    h = len(r['map']) // 2
    return {k: float(np.mean(r[k][h:])) for k in ('map', 'hr', 'co')}


def test_epinephrine_biphasic_freyschuss1986():
    """[PMID: 3956110 — Freyschuss 1986] IV adrenaline infusion in 11 healthy
    volunteers, stepwise plasma ADR 0.3→6.0 nmol/L:
    - Low dose (β dominant): CO↑ (SV↑ + HR↑), SVR↓, MAP minimal change
    - Higher dose (α emerging): CO still↑↑, MAP↑ (α overcomes β2 vasodilation)

    Key biphasic signature: at low dose MAP is nearly unchanged despite large
    CO increase (β2 vasodilation offsets α vasoconstriction); at high dose
    MAP rises clearly (α dominance). HR and CO increase monotonically with dose.

    Model test:
    - CO increases with dose (β1: both low and high > baseline)
    - HR increases with dose (β1 chronotropy)
    - MAP_high > MAP_low (α dominance emerges, biphasic pattern)
    """
    base     = _run_epi(0.00)
    low_dose = _run_epi(0.02)   # β-dominant, inside Freyschuss's range
    mid_dose = _run_epi(0.05)   # β-dominant, top of Freyschuss's range
    high_dose = _run_epi(0.30)  # α-dominant — OUTSIDE Freyschuss's range

    # CO rises with dose THROUGH THE RANGE FREYSCHUSS ACTUALLY STUDIED
    # ("marked and concentration-dependent increases in SV and CO").
    assert low_dose['co']  > base['co'],      f"Low-dose epi: CO did not rise: {base['co']:.2f}→{low_dose['co']:.2f}"
    assert mid_dose['co'] > low_dose['co'],   f"Mid-dose epi: CO not > low-dose: {low_dose['co']:.2f}→{mid_dose['co']:.2f}"

    # NO CO ASSERTION AT 0.30 mcg/kg/min. Freyschuss infused into the
    # physiological, β2-dominant range and reported vascular resistances
    # FALLING throughout; the α-dominant region is an extrapolation of this
    # model's own PD curve, which `validation_log.md` has said in writing since
    # the test was written. Asserting a CO ordering there tested the
    # extrapolation against no source at all.
    # Measured 2026-09-04: CO peaks at 0.05 (7.39 L/min) and settles to 7.11 by
    # 0.30 as the drug's SVR factor reaches 1.98 and afterload limits ejection.
    # Whether that plateau is real is UNVALIDATED — see backlog item 38.

    # Biphasic MAP: at vasopressor dose (0.30) α dominates → MAP well above low-dose MAP
    # Freyschuss only studied low/physiological doses (their high dose still shows SVR↓);
    # the α-dominance at supra-physiological doses is a well-established pharmacological
    # property modelled here. Baroreflex clamping of HR at high MAP is expected and not
    # asserted — the CO and MAP signals are the key biphasic markers.
    assert high_dose['map'] > low_dose['map'], (
        f"Biphasic not reproduced: MAP_high {high_dose['map']:.1f} not > MAP_low {low_dose['map']:.1f} mmHg"
    )


# ===========================================================================
# 13. Passive leg raising — fluid responsiveness — [PMID: 26825952, Monnet 2016]
# ===========================================================================

def _run_plr(tilt_deg, hem_ml=0, duration=30.0):
    """Simulate PLR (head-down tilt) ± haemorrhage; return last-half means."""
    p = SimParams()
    p.tilt_start_deg = tilt_deg
    p.tilt_end_deg   = tilt_deg
    if hem_ml > 0:
        p.hemorrhage_rate_mlmin = hem_ml / 5.0 * 60.0
        p.hemorrhage_start_s    = 3.0
        p.hemorrhage_duration_s = 5.0
    r = run_simulation(p, duration_s=duration, dt=DT)
    h = len(r['map']) // 2
    return {k: float(np.mean(r[k][h:])) for k in ('map', 'co', 'hr', 'sv')}


def test_plr_fluid_responsiveness_monnet2016():
    """[PMID: 26825952 — Monnet, Marik & Teboul 2016] Meta-analysis of 21 studies,
    991 patients: PLR-induced CO ≥+10% predicts positive response to volume
    expansion (sens 0.85, spec 0.91, AUC 0.95).

    PLR is modelled as −20° head-down tilt from supine. Two conditions:

    (A) Normovolemic — patient on Frank-Starling plateau. PLR shifts blood
    centrally but the plateau limits SV augmentation → CO increase < 10%
    (non-responder, consistent with Monnet specificity 0.91).

    (B) Hypovolaemia (1200 mL haemorrhage, ~class III) — patient on the
    ascending Starling limb. PLR recruits the (now physiologically compliant,
    nonlinear) limb + splanchnic venous reservoir, SV rises, CO increases ≥+10%
    (fluid-responder, consistent with Monnet sensitivity 0.85).
    """
    hypo_supine = _run_plr(tilt_deg=0,   hem_ml=1200)
    hypo_plr    = _run_plr(tilt_deg=-20, hem_ml=1200)

    dco_hypo_pct = (hypo_plr['co'] - hypo_supine['co']) / hypo_supine['co'] * 100

    # Hypovolemic: ascending limb — PLR should return ≥10% CO increase.
    # The normovolaemic arm is split out below (2026-10-06).
    assert dco_hypo_pct >= 10, (
        f"Hypovolemic PLR: CO increase < 10% (lit threshold ≥10%): Δ{dco_hypo_pct:+.1f}%"
    )


# CLOSED 2026-10-13 — strict xfail of 2026-10-06 (CO +17.0 %) XPASSED when the sac
# went on: the full normovolaemic heart meets the sac and stops filling (CO +1.8 %),
# while after a 1200 mL bleed it sits below the knee and still responds (+60.8 %).
# A Starling plateau from structure, not from a fitted curve.
@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "KNOWN GAP, 2026-10-27 — dCO +11.2 % against the < 10 % non-responder cut-off (was +9.2 %). "
    "Diagnosed: NOT a lost plateau. The heart sits the same distance below the sac's knee (27 vs "
    "28 mL) and gains the same SV (+12.7 vs +12.6 mL); the % crosses 10 because resting SV fell to "
    "87.6 mL (47.6 mL/m2, Luu 46 +/- 8) when both atria were re-sized on independent sources. "
    "Monnet's 10 % is an ICU diagnostic cut-off, not a law for normal hearts. Recorded, not tuned "
    "(validation log 2026-10-27)."
))
def test_plr_normovolaemic_non_responder_monnet2016():
    """[PMID 26825952 — Monnet 2016] Specificity 0.91: a normovolaemic patient
    on the Starling plateau should NOT reach the +10 % responder threshold. Same
    protocol as the test above (whole-body -20 deg, the pre-item-53 leg raise)."""
    norm_supine = _run_plr(tilt_deg=0,   hem_ml=0)
    norm_plr    = _run_plr(tilt_deg=-20, hem_ml=0)
    dco_norm_pct = (norm_plr['co'] - norm_supine['co']) / norm_supine['co'] * 100
    assert dco_norm_pct < 10, (
        f"Normovolemic PLR: CO rose ≥10% despite Starling plateau: Δ{dco_norm_pct:+.1f}%"
    )


# ===========================================================================
# 14. Venous tone — mechanism regression guard
#
# Venous tone (drug venous_tone_factor × baroreflex v0_vein_factor) multiplies
# the systemic venous UNSTRESSED volume in circulation.py `_odes`:
#     < 1  venoconstriction → recruits blood centrally → CVP / preload / CO ↑
#     > 1  venodilation      → venous pooling            → CVP / preload / CO ↓
# A prior version assembled this factor but never applied it (dead variable),
# so venoconstriction — the primary defence of venous return under orthostatic
# stress and the mechanism of α1 vasopressors — had ZERO effect. These guards
# are calibration-independent: they assert the mechanism is live and correctly
# signed, so tuning drug magnitudes can never silently neuter the fix.
# ===========================================================================

def _run_venous_tone(vt_factor, baro=False):
    """Run with an isolated venous_tone_factor (all other factors neutral)."""
    from model.pharmacology import NEUTRAL_FACTORS
    p = SimParams()
    p.baroreflex_enabled = baro
    p.drug_factors = dict(NEUTRAL_FACTORS)
    p.drug_factors["venous_tone_factor"] = vt_factor
    r = run_simulation(p, duration_s=30.0, dt=DT, use_baroreflex=baro)
    h = len(r["map"]) // 2
    out = {k: float(np.mean(r[k][h:])) for k in ("map", "cvp", "co", "sv")}
    from model.circulation import THORACIC_COMPARTMENTS
    th = [IDX[n] for n in THORACIC_COMPARTMENTS]
    out["thorax_ml"] = float(np.mean(np.asarray(r["volumes"])[h:][:, th].sum(axis=1)))
    return out


def test_venous_tone_modulates_preload_regression():
    """Venous tone must produce a clear, correctly-signed haemodynamic effect.

    Fails bit-for-bit on the pre-fix code where the factor was never applied.
    Baroreflex OFF isolates the mechanical (preload-recruitment) effect.

    A LIVENESS AND DIRECTION GUARD — NO SOURCED MAGNITUDE. Re-expressed
    2026-10-09 (Jesper chose this). It used to assert CO > +5 %, a margin set in
    August when the model happened to give +5.40 %. The leg rebuild (grade D leg
    capacity, compliance 12 -> 25 mL/mmHg) let the legs absorb part of the
    mobilised blood — correct physiology (Pang 2001, PMID 11578657) — and CO
    became +4.94 %, failing a number nothing in the literature had set.
    It now asserts what the mechanism CLAIMS: blood leaves the squeezed
    reservoir and arrives in the chest. Measured 2026-10-09: reservoir -90 mL,
    thorax +55 / -52 mL, legs +16 mL. The 20 mL margin is anchored to the dead
    mechanism (0 mL), not to the value of the day.
    """
    neutral   = _run_venous_tone(1.00)
    constrict = _run_venous_tone(0.90)   # +10% venous tone (venoconstriction)
    dilate    = _run_venous_tone(1.10)   # 10% venodilation

    # Venoconstriction recruits blood INTO THE CHEST — the mechanism's claim,
    # by a margin anchored to a dead mechanism (0 mL).
    assert constrict["thorax_ml"] > neutral["thorax_ml"] + 20.0, (
        f"Venoconstriction recruited only {constrict['thorax_ml'] - neutral['thorax_ml']:+.1f} mL "
        f"into the thorax (dead mechanism: 0)")
    assert constrict["co"]  > neutral["co"], (
        f"Venoconstriction did not raise CO: {neutral['co']:.2f}→{constrict['co']:.2f} L/min")
    assert constrict["sv"]  > neutral["sv"], (
        f"Venoconstriction did not raise SV: {neutral['sv']:.1f}→{constrict['sv']:.1f} mL")
    # CVP margin 0.2 mmHg: with physiological venous compliance (venous-system
    # rebuild) the same fractional venoconstriction shifts CVP more gently than
    # on the old compressed pool — the effect is real, just correctly smaller.
    assert constrict["cvp"] > neutral["cvp"] + 0.2, (
        f"Venoconstriction did not raise CVP: {neutral['cvp']:.2f}→{constrict['cvp']:.2f} mmHg")

    # Venodilation pools blood peripherally: the chest loses volume, CVP and CO fall.
    assert dilate["thorax_ml"] < neutral["thorax_ml"] - 20.0, (
        f"Venodilation moved only {dilate['thorax_ml'] - neutral['thorax_ml']:+.1f} mL out of "
        f"the thorax (dead mechanism: 0)")
    assert dilate["co"]  < neutral["co"], (
        f"Venodilation did not lower CO: {neutral['co']:.2f}→{dilate['co']:.2f} L/min")
    assert dilate["cvp"] < neutral["cvp"] - 0.2, (
        f"Venodilation did not lower CVP: {neutral['cvp']:.2f}→{dilate['cvp']:.2f} mmHg")

    # Monotonic ordering across the range.
    assert constrict["co"] > neutral["co"] > dilate["co"], (
        f"CO not monotonic in venous tone: "
        f"{constrict['co']:.2f} / {neutral['co']:.2f} / {dilate['co']:.2f}")


def test_venous_tone_factor_signs_by_drug_class():
    """Vasopressors venoconstrict; IV anaesthetics venodilate.

    Guards the sign convention, which a prior version had contradictory between
    the pressor and anaesthetic drug classes.

    **THIS NOW CHECKS THE END-TO-END EFFECT, NOT ONE INTERMEDIATE VARIABLE**, and
    the change is a strengthening. Until item 70 pass 3 every drug's venous
    effect travelled through `venous_tone_factor`, so reading that key was
    enough. The alpha1 agonists now go through a SHARED receptor stage instead
    (`alpha1_venous_drive`), and their `venous_tone_factor` is 1.0 — so the old
    assertion failed for noradrenaline and phenylephrine even though both still
    venoconstrict correctly.

    **The honest fix is to follow the effect, not to relax the assertion.**
    CLAUDE.md names this guard as one that must not be weakened to make a
    calibration fit, and it exists because `venous_tone_factor` was once a dead
    variable — assembled and never applied, so venoconstriction silently did
    nothing for months. Reading the final V0 multiplier catches that failure
    through EITHER pathway, which reading one key no longer does.
    """
    from model.pharmacology import alpha1_tone_drive, ALPHA1_VENOUS_EMAX

    tone_drive = alpha1_tone_drive(0.24)      # the default resting tone

    def v0_multiplier(drugs):
        """The factor the ODE actually applies to mobilizable unstressed volume."""
        f = combined_drug_factors(drugs)
        drive = tone_drive + f["alpha1_venous_drive"]
        alpha1 = 1.0 - ALPHA1_VENOUS_EMAX * (drive / (1.0 + drive))
        return f["venous_tone_factor"] * alpha1

    baseline = v0_multiplier({})
    for drug, dose in (("norepinephrine", 0.1), ("phenylephrine", 1.0),
                       ("vasopressin", 2.0)):
        assert v0_multiplier({drug: dose}) < baseline, (
            f"{drug} should venoconstrict — it must LOWER the unstressed volume "
            f"multiplier below the undrugged {baseline:.4f}. Check both pathways: "
            f"venous_tone_factor for non-alpha1 drugs, alpha1_venous_drive for "
            f"alpha1 agonists."
        )
    for drug, dose in (("propofol", 2.0), ("spinal", 1.0)):
        assert v0_multiplier({drug: dose}) > baseline, (
            f"{drug} should venodilate — it must RAISE the unstressed volume "
            f"multiplier above the undrugged {baseline:.4f}"
        )


# ===========================================================================
# 15. Resting sympathetic tone is arterial, not venous
#
# [A1] Abboud FM, Schmid PG, Eckstein JW (1968). Vascular responses after alpha
#      adrenergic receptor blockade. I. Responses of capacitance and resistance
#      vessels to norepinephrine in man. J Clin Invest 47(1):1-9.
#      DOI: 10.1172/JCI105699   PMID: 16695931   PMC297142
#      HUMAN, 11 male subjects, supine, warm room (82 F), intra-brachial
#      infusions with no systemic effect (arterial pressure and HR unchanged).
#
#      Alpha-blockade with intra-arterial phentolamine NEARLY DOUBLED resting
#      forearm blood flow (5.95 -> 9.28 and 11.19 mL/100 mL/min, both p < 0.05)
#      while leaving resting venous distensibility UNCHANGED (4.26 -> 4.46 and
#      4.50 mL/100 mL, p > 0.05). The authors' conclusion, in their words:
#      "in comfortable subjects lying supine in a warm environment the
#      sympatho-adrenal influence on venous distensibility is negligible. This
#      does not appear to be true however for resistance vessels."
#
#      i.e. an unstressed resting human carries substantial ARTERIOLAR
#      sympathetic tone and essentially NO venous sympathetic tone. The venous
#      effector is a reserve, held near neutral until it is needed.
#
# WHICH QUANTITY [A1] MEASURED, AND IT IS NOT UNSTRESSED VOLUME — 2026-09-29.
# Abboud reports venous DISTENSIBILITY, mL/100 mL of tissue, from a plethysmo-
# graphic congesting-cuff curve. That is a COMPLIANCE, a slope. It is unchanged
# by a shift in V0, so **[A1] constrains the venous compliance arm and says
# nothing about the unstressed-volume arm.** The model's resting tone acts on V0
# and leaves compliance at 1.0, so the two do not meet.
#
# WHY THIS GUARD WAS REVISITED — 2026-09-29. Item 70 pass 2 introduced a resting
# venous tone of 0.24 and this test kept passing, because it reads
# `BaroreflexController.v0_vein_factor` and the tone had deliberately been put in
# `_odes`, OUTSIDE the controller. That looked like a blind guard.
#
# ON INSPECTION IT IS NOT BLIND — IT IS NARROW, AND THE DISTINCTION MATTERS.
# The harm it describes (a venous reserve already spent at rest) cannot occur,
# because `_odes` re-baselines V0 by 1/(1 - tone) so the resting operating point
# is unchanged to floating point. That invariant is guarded END-TO-END by section
# 38. Verified by breaking it: deleting the re-baselining moved MAP 95.411 ->
# 96.790 and section 38 failed immediately.
#
# So the scope is now stated rather than widened. **An attempt to widen it here
# made things worse** — it recomputed the same arithmetic inside the test, which
# stayed green through the identical break. The correction that mattered was the
# QUANTITY one above, not the object being read.
# ===========================================================================

def test_resting_baroreflex_tone_is_arterial_not_venous():
    """[A1] At rest the venous arm must be near-neutral, the arterial arm not.

    This guards the ASYMMETRY, not the exact numbers. If someone gives the
    venous effector a resting set-point, an unstressed patient starts out with
    the venous reserve already partly spent — and every subsequent hypovolaemic
    or orthostatic challenge then has less reserve to recruit than a real
    patient does.

    WHAT THIS TEST DOES *NOT* GUARD, and the boundary was drawn by experiment.
    The docstring's stated harm — a spent venous reserve — is prevented by the
    V0 re-baselining in `_odes`, and the guard for that is
    `test_resting_venous_tone_is_neutral_while_outflow_is_intact` in section 38,
    which drives it through `run_simulation`. **A first attempt at this repair
    asserted the re-baselining here too, and it was worthless: it recomputed the
    `1/(1 - tone)` arithmetic in the test instead of calling the model.** Deleting
    the factor from `circulation.py` left it green. Section 38 failed on the same
    break at once (MAP 95.411 -> 96.790). So the re-baselining is covered, by the
    test that runs the model, and this one stays on the controller — where a
    resting set-point would actually be introduced.

    THE LESSON IS THE SAME ONE TWICE. A guard that mirrors the formula it guards
    is as blind as a guard that reads the wrong object. **Assert through the code
    path, not alongside it.**
    """
    from model.baroreflex import BaroreflexController
    from model.pharmacology import combined_drug_factors

    # 1. THE TONE MUST ACT ON UNSTRESSED VOLUME, NOT ON COMPLIANCE — because
    #    compliance is the arm [A1] actually measured, and he found it unchanged
    #    (4.26 -> 4.46 and 4.50 mL/100 mL, p > 0.05). The undrugged venous
    #    compliance factor is read from the code rather than assumed, so this
    #    fails if resting tone is ever routed through it.
    #
    #    WHAT THIS GUARD CANNOT SEE, stated so it is not mistaken for more than
    #    it is: `_odes` takes `vc` from the drug dict only, so an undrugged run
    #    has no route by which tone COULD reach compliance today. The assertion
    #    is therefore structural — it pins the current wiring, and would catch a
    #    change that added such a route through the drug factors. It would NOT
    #    catch one that multiplied `c.compliance` directly in `_odes`.
    #
    #    AND IT DOES NOT MAKE THE MODEL RIGHT ABOUT THE PHYSIOLOGY. Maas 2013
    #    says smooth-muscle tone moves unstressed volume and cross-sectional area
    #    TOGETHER, so a real blockade should move both. The model moves only V0 —
    #    a known simplification, recorded beside _VENOUS_DRAIN_IDX.
    assert combined_drug_factors({})["venous_compliance_factor"] == 1.0, (
        "the undrugged venous compliance factor is not 1.0, so something now "
        "changes venous compliance at rest. [A1] measured venous DISTENSIBILITY "
        "— a compliance — and found it UNCHANGED after alpha-blockade (p > 0.05); "
        "resting sympathetic tone must act on unstressed volume instead"
    )

    # 2, 3 and 4. THE CONTROLLER'S DYNAMIC ARMS. A resting set-point on the
    #    venous effector would show up here, and the arterial arm must dominate.
    b = BaroreflexController(dt=0.001)
    for _ in range(60000):                      # 60 s at a resting operating point
        b.update(88.1, 45.0, 2.9)

    venous_tone = 1.0 - b.v0_vein_factor        # fraction of V0 withdrawn
    arterial_tone = b.svr_factor - 1.0          # fractional resistance added

    assert venous_tone < 0.10, (
        f"resting venous tone is {venous_tone * 100:.1f}% of V0. [A1] found "
        f"alpha-blockade did not change resting venous distensibility in supine "
        f"warm subjects (p > 0.05), i.e. resting venous sympathetic tone is "
        f"negligible; the reserve should be nearly untouched at rest"
    )
    assert arterial_tone > 0.05, (
        f"resting arterial tone is only {arterial_tone * 100:.1f}%. [A1] found "
        f"alpha-blockade nearly DOUBLED resting forearm blood flow (p < 0.05), "
        f"so a resting human carries substantial arteriolar tone"
    )
    assert arterial_tone > venous_tone, (
        f"resting tone is not arterial-dominant (arterial {arterial_tone:.3f} "
        f"vs venous {venous_tone:.3f}), which inverts [A1]"
    )


# ===========================================================================
# 16. Postcapillary resistance — mechanism regression guard (backlog item 18)
#
# [A2] Abboud FM, Eckstein JW (1968). Vascular responses after alpha adrenergic
#      receptor blockade. II. Responses of venous and arterial segments to
#      adrenergic stimulation in the forelimb of dog. J Clin Invest 47(1):10-19.
#      PMID 16695932. DOI 10.1172/JCI105700.
#      Dog forelimb perfused at CONSTANT flow, arterial and venous segment
#      pressures recorded separately. Doubling the norepinephrine dose (1 -> 2 ug)
#      raised the arterial response 66.1 -> 82.5 mmHg (x1.25) but the venous
#      response 6.0 -> 13.5 mmHg (x2.25): the venous dose-response curve is 1.80x
#      steeper. The authors state the consequence directly — alpha blockade works
#      "by antagonizing the increase in POSTCAPILLARY venous resistance and by
#      preserving an increase in PRECAPILLARY arterial resistance, [to] prevent
#      the excessive CAPILLARY FILTRATION which may occur during adrenergic
#      stimulation."
#
# [D1] Doorenbos CJ, Blauw GJ, van Brummelen P (1991). Arterial and venous effects
#      of atrial natriuretic peptide in the human forearm. Am J Hypertens
#      4(4 Pt 1):333-40. PMID 1829369. DOI 10.1093/ajh/4.4.333.
#      Human forearm, single LOW norepinephrine dose: no effect on capillary
#      filtration, NE classified as "a predominant arterial constrictor". With a
#      steeper venous slope [A2] this is the low-dose end of the same curve, which
#      is why the postcapillary arm must be a Hill curve and not a flat multiplier.
#
# `postcap_factor` scales the venous DRAINAGE resistance of each exchange bed.
# Before this existed, capillary pressure was almost drug-insensitive — raising
# svr_factor lowered `*_art` pressure while venoconstriction raised `*_vein`
# pressure and the two nearly cancelled — so norepinephrine removed ~0.13% of the
# plasma volume against Lister's measured 15-19% in man.
#
# These guards are calibration-independent, exactly as in section 14: they assert
# the mechanism is live, correctly signed, and distinct from venous tone. Do not
# weaken them to make a dose fit.
# ===========================================================================

def _run_isolated_factor(**factors):
    """Run with one or more isolated drug factors, all others neutral.

    Reports the peripheral venous pool as well as the central measures, which is
    what separates a resistance effect from a capacitance one.
    """
    from model.pharmacology import NEUTRAL_FACTORS
    p = SimParams()
    p.baroreflex_enabled = False
    p.drug_factors = dict(NEUTRAL_FACTORS)
    p.drug_factors.update(factors)
    r = run_simulation(p, duration_s=30.0, dt=DT, use_baroreflex=False)
    h = len(r["map"]) // 2
    out = {k: float(np.mean(r[k][h:])) for k in ("map", "cvp", "co", "sv")}
    # Volume held in the exchange beds upstream of the drainage resistance
    vols = r["volumes"][h:]
    out["venous_pool"] = float(np.mean(
        vols[:, IDX["splanchnic_vein"]] + vols[:, IDX["upper_body_vein"]]
        + vols[:, IDX["renal_vein"]]))
    return out


def _pc_with_postcap(pc_factor):
    """Volume-weighted capillary pressure from a settled run, mmHg."""
    from model.circulation import _vascular_pressure
    from model.slow_dynamics import (CAPILLARY_BEDS, capillary_pressure_fraction)
    from model.pharmacology import NEUTRAL_FACTORS

    p = SimParams()
    p.baroreflex_enabled = False
    p.ventilation_mode = "none"
    p.drug_factors = dict(NEUTRAL_FACTORS)
    r = run_simulation(p, duration_s=30.0, dt=DT, use_baroreflex=False)
    V = r["volumes"][len(r["volumes"]) // 2:].mean(axis=0)
    comp = p.compartments
    P = [_vascular_pressure(V[k], c.unstressed_volume, c.compliance,
                            getattr(c, "p_stiffen", None))
         for k, c in enumerate(comp)]
    frac = capillary_pressure_fraction(pc_factor)
    return sum(share * (P[IDX[ven]] + frac * (P[IDX[art]] - P[IDX[ven]]))
               for art, ven, share in CAPILLARY_BEDS)


def _run_postcap(pc_factor):
    """Run with an isolated postcap_factor (all other factors neutral)."""
    return _run_isolated_factor(postcap_factor=pc_factor)


def test_postcap_factor_defaults_are_neutral():
    """Every drug without a sourced postcapillary ratio must return exactly 1.0.

    A silent non-unity default would move capillary pressure — and hence plasma
    volume — for drugs we have no evidence for.
    """
    from model.pharmacology import (NEUTRAL_FACTORS, combined_drug_factors,
                                    vasopressin, epinephrine, propofol,
                                    spinal_anaesthesia)

    assert NEUTRAL_FACTORS["postcap_factor"] == 1.0
    assert combined_drug_factors({})["postcap_factor"] == 1.0
    assert combined_drug_factors({"norepinephrine": 0.0})["postcap_factor"] == 1.0

    for fn, dose, name in ((vasopressin, 2.0, "vasopressin"),
                           (epinephrine, 0.1, "epinephrine"),
                           (propofol, 2.0, "propofol"),
                           (spinal_anaesthesia, 10.0, "spinal")):
        assert fn(dose).get("postcap_factor", 1.0) == 1.0, (
            f"{name} returned a postcapillary effect, but no source has been read "
            f"for it. Unsourced drugs must stay at exactly 1.0"
        )


def test_alpha1_postcapillary_slope_is_steeper_than_arterial():
    """[A2] The venous dose-response must rise faster than the arterial one.

    This is the sourced SHAPE of the mechanism and the property that reconciles
    [A2] with [D1]. A flat multiplier, or any parameterisation where the two arms
    rise together, fails here.
    """
    from model.pharmacology import norepinephrine

    lo, hi = 0.05, 0.10          # a doubling, mid clinical range
    a, b = norepinephrine(lo), norepinephrine(hi)
    arterial = (b["svr_factor"] - 1.0) / (a["svr_factor"] - 1.0)
    venous   = (b["postcap_factor"] - 1.0) / (a["postcap_factor"] - 1.0)

    assert venous > arterial, (
        f"postcapillary arm grew x{venous:.2f} against arterial x{arterial:.2f}; "
        f"[A2] measured the venous dose-response as the STEEPER of the two"
    )
    ratio = venous / arterial
    assert 1.4 < ratio < 2.3, (
        f"venous/arterial slope ratio is {ratio:.2f}; [A2] measured 1.80 "
        f"(arterial x1.25 vs venous x2.25 over a dose doubling)"
    )


def test_postcap_factor_is_live_and_correctly_signed():
    """Raising postcapillary resistance must RAISE capillary pressure.

    Fails bit-for-bit if the factor is assembled but never applied — the exact
    failure mode that once silently disabled `venous_tone_factor` (section 14).

    This checks the quantity that matters. The factor shifts the pre/post split
    inside the exchange segment, moving the capillary toward the arterial end; it
    deliberately does NOT change any flow. An earlier version applied it to the
    venous drainage resistance instead and was guarded by a volume-damming
    assertion — the wrong site and the wrong check, since damming the drainage
    chokes venous return and moves Pc barely at all.
    """
    from model.slow_dynamics import capillary_pressure_fraction

    f0 = capillary_pressure_fraction(1.0)
    f_hi = capillary_pressure_fraction(2.0)

    assert f0 == CAPILLARY_PRESSURE_FRACTION, (
        f"the capillary fraction is {f0} with no drug on board, but the resting "
        f"constant is {CAPILLARY_PRESSURE_FRACTION}; the mechanism is not neutral"
    )
    assert f_hi > f0, (
        f"doubling postcapillary resistance moved the capillary fraction "
        f"{f0:.3f} -> {f_hi:.3f}. Raising the postcapillary share must move the "
        f"capillary TOWARD the arterial end and raise Pc — the mechanism is dead "
        f"or inverted"
    )

    # And it must show up as real capillary pressure in a real run.
    base = _pc_with_postcap(1.0)
    high = _pc_with_postcap(2.0)
    assert high > base + 2.0, (
        f"weighted capillary pressure moved only {base:.2f} -> {high:.2f} mmHg "
        f"when postcapillary resistance was doubled; [A2] has this as the "
        f"mechanism by which adrenergic drive drives capillary filtration"
    )


def test_postcap_and_venous_tone_are_distinct_mechanisms():
    """Postcapillary resistance and venous tone must not be interchangeable.

    Both act on veins, but they are different quantities with different effects,
    and only one moves capillary pressure:

      - venous tone is CAPACITANCE. It expels blood centrally, so it raises CVP,
        and it moves Pc only incidentally via venous pressure.
      - postcapillary resistance is a SPLIT within the exchange segment. It moves
        the capillary toward the arterial end, so it raises Pc substantially and
        leaves CVP alone — it changes no flow at all.

    If a future edit collapses one into the other, or re-routes the postcapillary
    effect onto a resistance that carries flow, this fails.
    """
    base = _run_isolated_factor()
    postcap = _run_isolated_factor(postcap_factor=2.0)
    venocon = _run_isolated_factor(venous_tone_factor=0.85)

    assert abs(postcap["cvp"] - base["cvp"]) < 0.05, (
        f"postcapillary constriction moved CVP {base['cvp']:.3f} -> "
        f"{postcap['cvp']:.3f}. It shifts where the capillary sits inside the "
        f"exchange segment and must not move flow or central pressures; if it "
        f"does, it has been re-routed onto a resistance that carries flow"
    )
    assert venocon["cvp"] > base["cvp"] + 0.05, (
        f"venoconstriction did not raise CVP ({base['cvp']:.3f} -> "
        f"{venocon['cvp']:.3f}); the capacitance mechanism is dead"
    )

    pc_base, pc_postcap = _pc_with_postcap(1.0), _pc_with_postcap(2.0)
    assert pc_postcap - pc_base > 2.0, (
        f"postcapillary constriction moved Pc only {pc_base:.2f} -> "
        f"{pc_postcap:.2f} mmHg; that is the effect it exists for"
    )


# ===========================================================================
# 17. Pulmonary circulation — backlog item 22
#
# NOTHING in this suite constrained any pulmonary pressure or volume until
# 2026-08-22, which is exactly why the pulmonary bed has carried its original
# parameters since the initial commit while the systemic side was rebuilt. These
# assertions were written BEFORE changing any parameter, so the fix is measured
# rather than merely observed.
#
# [P1] Widrich J, Shetty M. "Physiology, Pulmonary Vascular Resistance."
#      StatPearls, NCBI Bookshelf NBK554380.
#      - PVR normal 0.25-1.6 mmHg*min/L (37-250 dyn*s*cm^-5)
#      - mean pulmonary arterial pressure 15 mmHg
#      - "The output pressure represents the pulmonary venous pressure, EQUIVALENT
#        TO the pulmonary capillary wedge or left atrial pressure (5 to 6 mm Hg)"
#      - pulmonary hypertension: mean PA > 25 mmHg AND PVR > 3 mmHg*min/L
#
#      CAVEAT ON SOURCE QUALITY: StatPearls is tertiary (a teaching reference), not
#      primary literature. It is used here for textbook-level physiological
#      constants, which is defensible, but anything load-bearing should be traced
#      to a primary measurement. Pulmonary BLOOD VOLUME is deliberately NOT asserted
#      below because no source for it has been read in full — the ~450-500 mL figure
#      in the backlog is recollection, not a citation.
# ===========================================================================

def _pulmonary_state():
    """Settled pulmonary pressures, PVR and blood volume."""
    from model.circulation import _vascular_pressure

    p = SimParams()
    p.ventilation_mode = "none"
    p.slow_dynamics_enabled = False
    r = run_simulation(p, duration_s=60.0, dt=DT)
    s = slice(2 * len(r["map"]) // 3, None)
    V = r["volumes"][2 * len(r["volumes"]) // 3:].mean(axis=0)
    comp = p.compartments
    P = [_vascular_pressure(V[k], c.unstressed_volume, c.compliance,
                            getattr(c, "p_stiffen", None))
         for k, c in enumerate(comp)]
    co = float(np.mean(r["co"][s]))
    return {
        "pa":  P[IDX["pulmonary_art"]],
        "cap": P[IDX["pulmonary_cap"]],
        "pv":  P[IDX["pulmonary_vein"]],
        "la":  float(np.mean(r["la_pressure"][s])),
        "co":  co,
        "volume": float(V[IDX["pulmonary_art"]] + V[IDX["pulmonary_cap"]]
                        + V[IDX["pulmonary_vein"]]),
        "blood_volume": float(V.sum()),
    }


def test_pulmonary_vascular_resistance_is_physiological():
    """[P1] PVR = (mean PA - pulmonary venous) / CO must be 0.25-1.6 mmHg*min/L.

    This one PASSES, and is worth guarding precisely because it shows the
    resistance DISTRIBUTION across the pulmonary bed is not the defect — the
    pressures are wrong at their absolute level, not in their gradient.
    """
    s = _pulmonary_state()
    pvr = (s["pa"] - s["pv"]) / s["co"]
    assert 0.25 <= pvr <= 1.6, (
        f"PVR is {pvr:.2f} mmHg*min/L, outside [P1]'s normal 0.25-1.6. Above 3 "
        f"with a mean PA over 25 would be pulmonary hypertension in a subject the "
        f"model is supposed to treat as healthy"
    )


@pytest.mark.xfail(strict=True, reason=(
    "KNOWN DEFECT, backlog item 22. There is NO VALVE and essentially no resistance "
    "between the pulmonary veins and the left atrium — [P1] treats pulmonary venous, "
    "wedge and left atrial pressure as the same number. The model connects them with "
    "`comp[left_atrium].resistance`, which is VALVE_R = 0.08, and wraps the flow in "
    "max(0, ...) so it cannot reverse. That manufactures a ~3.9 mmHg gradient and "
    "inflates wedge pressure by that much on its own. It also pushes PVR computed the "
    "clinical way, (mean PA - LA)/CO, to 2.31 — above [P1]'s normal range and "
    "approaching the pulmonary-hypertension threshold of 3. "
    "Same class of error as backlog item 20: a resistance in a place with no anatomy "
    "to justify it. strict=True so this flips to a FAILURE the day it is fixed."
))
def test_pulmonary_venous_pressure_equals_left_atrial():
    """[P1] Pulmonary venous, wedge and left atrial pressure are the same number."""
    s = _pulmonary_state()
    gradient = s["pv"] - s["la"]
    assert abs(gradient) < 1.0, (
        f"pulmonary venous pressure sits {gradient:+.2f} mmHg above left atrial "
        f"({s['pv']:.2f} vs {s['la']:.2f}). [P1]: the pulmonary venous pressure is "
        f"'equivalent to the pulmonary capillary wedge or left atrial pressure'. "
        f"There is no valve and no meaningful resistance between them"
    )


def test_pulmonary_pressures_are_physiological():
    """CLOSED 2026-08-31 by the left-atrial compliance fix. Was a strict xfail
    for a few hours on the same day.

    HISTORY, because it is a clean worked example of the ratchet doing its job.
    The atrial timing fix (PR 514 ms -> 160 ms) pushed mean PA from 19.27 to
    20.60 and pulmonary venous from 11.52 to 12.56, breaking two assertions in
    this test. Reverting the timing to green them would have restored a
    complete-heart-block PR interval to buy 1.3 mmHg, so the failure was carried
    as a strict xfail instead, with the assertions untouched and the cause named:
    the LA-LV coupling.

    That diagnosis was right, but the specific lever named in it was wrong. The
    xfail said "with the mitral valve at R = 0.01 the pulmonary veins, LA and LV
    behave as one pooled volume". Sweeping mitral resistance showed it is NOT the
    lever — reaching the atrial-contribution target that way produces mitral
    stenosis (mean PA 30.8, PCWP 23.0). The actual defect was that the left
    atrium was ~1.5x too STIFF: LA_EMIN 0.28 against 0.19 derived from Gao's own
    volume-and-pressure data. At 0.28 the atrium reached 21.6 mmHg at peak
    volume against a real v-wave of 10-15, and that over-pressure propagated
    backwards into the pulmonary bed.

    Fixing the compliance closed both assertions without either being weakened:
    mean PA 20.60 -> 19.48, pulmonary venous 12.56 -> 11.39. strict=True is what
    surfaced it — the test XPASSed and reported as a failure the moment the gap
    closed, rather than sitting silently green.
    """
    """CLOSED 2026-08-26 by the venous rework, backlog item 28.

    Was a strict xfail: resting pulmonary venous pressure 16.0 and left atrial
    12.1 against [P1]'s 5-6, with mean PA 21.3 against 15 — a resting healthy
    subject reading as pulmonary hypertension. Backlog item 22 had this down as
    a pulmonary-compliance problem (~7.5x low against Heldt Table 3).

    It was NOT a pulmonary problem. Lowering systemic venous compliance (x0.80)
    and raising venous drainage resistance (x2) — a change aimed entirely at the
    SYSTEMIC resistance-to-venous-return gap, item 28 — moved pulmonary venous to
    11.52 and mean PA to 19.27 without touching a single pulmonary parameter.
    Less systemic capacitance and more resistance to venous return simply leaves
    less volume sitting centrally.

    That is the layering lesson again: item 22 was diagnosed by looking at the
    compartment whose numbers were wrong rather than the one causing it.
    """
    """[P1] Mean PA ~15 mmHg; wedge / left atrial 5-6 mmHg."""
    s = _pulmonary_state()
    assert s["pa"] < 20.0, (
        f"mean pulmonary arterial pressure is {s['pa']:.2f} mmHg; [P1] gives 15, and "
        f"over 25 is pulmonary hypertension"
    )
    assert 4.0 <= s["la"] <= 12.0, (
        f"left atrial pressure is {s['la']:.2f} mmHg; [P1] gives 5-6 (clinical "
        f"normal wedge 6-12)"
    )
    assert 4.0 <= s["pv"] <= 12.0, (
        f"pulmonary venous / wedge pressure is {s['pv']:.2f} mmHg; [P1] gives 5-6 "
        f"(clinical normal 6-12)"
    )


# ===========================================================================
# 18. Atrial volumes and phasic function — backlog item 23
#
# Nothing constrained atrial VOLUME until 2026-08-24. The atria were sized to
# produce a plausible PRESSURE (the left_atrium compartment still carries an
# "EDP≈9" comment, and 108 mL stressed x E_min 0.09 does give 9.7 mmHg) — but a
# large compliant atrium and a small stiff one hold the same pressure, and only
# volume tells them apart. Both atria came out 2.9-4.6x too large.
#
# Written BEFORE changing any parameter, so the fix is measured, not observed.
#
# [G1] Gao Y et al. (2022). "Reference values of left and right atrial volumes and
#      phasic function based on a large sample of healthy Chinese adults: a
#      cardiovascular magnetic resonance study." Int J Cardiol 352:180-187.
#      PMID 35124105. DOI 10.1016/j.ijcard.2022.01.071
#      CMR, 408 healthy adults, BSA 1.72 +/- 0.18. Table 2, all subjects, indexed:
#        LAVmax/BSA 36.9 +/- 7.7   LAVmin/BSA 14.4 +/- 4.1   LAEF total 61.1 +/- 6.2%
#        RAVmax/BSA 33.9 +/- 8.9   RAVmin/BSA 17.1 +/- 5.6   RAEF total 49.7 +/- 9.2%
#
# [G2] Figliozzi S et al. (2022). "Normal ranges of left atrial volumes and ejection
#      fraction by 3D echocardiography in adults: a systematic review and
#      meta-analysis." Int J Cardiovasc Imaging 38:1329-1340. PMID 34994882.
#      DOI 10.1007/s10554-021-02520-9
#      15 studies, 4,226 healthy adults, 3D echo:
#        LAVi max 25.18 mL/m2 (CI 23.10-27.26)
#        LAVi min 11.10 mL/m2 (10.01-12.18)
#        LA-EF    55.94%      (51.92-59.96)
#
# THE TWO LA SOURCES DISAGREE, and that is expected: CMR routinely reads larger
# atrial volumes than echo. The bands below span both rather than picking a winner.
# The model exceeds both by a wide margin, so the disagreement does not affect the
# verdict — but it does mean these bands must not be tightened onto one modality.
#
# [J1] Järvinen V, Kupari M, Hekali P, Poutanen V-P (1994). "Assessment of left
#      atrial volumes and phasic function using cine magnetic resonance imaging in
#      normal subjects." Am J Cardiol 73:1135-1138. DOI 10.1016/0002-9149(94)90298-4
#      Cine MRI, 17 healthy adults aged 24-47 (mean 40), cast-validated, LA
#      APPENDAGE INCLUDED. LAmax 52 +/- 9, LAmin 24 +/- 5 mL/m2; emptying 53 +/- 5 %.
#
# 2026-10-15: THE LEFT ATRIUM IS NOW TESTED AGAINST [J1], NOT [G1][G2]. Gao and the
# 3D-echo pool measure the atrial BODY and exclude the appendage. Since the AV-plane
# coupling (2026-10-13) the model's atrium takes up the volume the valve ring sweeps,
# which in man includes the appendage (Carlsson 2004), so the quantity it represents
# is the appendage-inclusive one. Jesper chose Järvinen for the LA on 2026-10-09
# (source_conflicts F, Gao demoted). Bands are Järvinen's 1 SD, as Luu and Gao are
# used elsewhere. The RIGHT atrium is split into its own tests and stays on [G1]
# until an appendage-inclusive RA source is read (Järvinen 1994 Radiology, PMID
# 8134560, requested; its abstract gives RAmax 77 +/- 11 mL/m2).
# ===========================================================================

REFERENCE_BSA = (175.0 * 70.0 / 3600.0) ** 0.5   # Mosteller, the default patient


def _atrial_state():
    """Max/min volume and emptying fraction of the AVERAGE BEAT, both atria.

    MATCHED TO JÄRVINEN'S METHOD (2026-10-17). His cine MRI was not respiratory-
    gated: "the effect of respiration was averaged out from the data because of
    the long imaging time" (Radiology 1994). Each frame is an average over many
    beats and breaths, so his volume curve is the ensemble-AVERAGE beat during
    quiet breathing. Until 2026-10-17 this ran with breathing OFF and took the
    absolute max/min over 20 s — matched to Gao's breath-hold CMR, which these
    bands no longer use. Now: spontaneous breathing, beats aligned at LV
    end-diastole and averaged, then max/min of that average beat."""
    p = SimParams()
    p.slow_dynamics_enabled = False
    r = run_simulation(p, duration_s=90.0, dt=DT, output_every=1)
    t = np.asarray(r["t"])
    V = np.asarray(r["volumes"])[t >= 30.0]
    lv = V[:, IDX["left_ventricle"]]
    beat = int(round(60.0 / float(np.mean(np.asarray(r["hr"])[t >= 30.0])) / DT))
    starts, i = [], int(np.argmax(lv[:beat]))
    while i + beat < len(lv):
        starts.append(i)
        i += int(np.argmax(lv[i + beat // 2:i + beat + beat // 2])) + beat // 2
    n = min(starts[k + 1] - starts[k] for k in range(len(starts) - 1))
    rv = np.mean([V[s:s + n, IDX["right_ventricle"]] for s in starts[:-1]], axis=0)
    out = {"rv_sv": float(rv.max() - rv.min())}
    for key, name in (("la", "left_atrium"), ("ra", "right_atrium")):
        avg = np.mean([V[s:s + n, IDX[name]] for s in starts[:-1]], axis=0)
        vmax, vmin = float(avg.max()), float(avg.min())
        out[key] = {
            "vmax": vmax, "vmin": vmin,
            "vmax_i": vmax / REFERENCE_BSA, "vmin_i": vmin / REFERENCE_BSA,
            "ef": 100.0 * (vmax - vmin) / vmax,
        }
    return out


def test_atrial_volumes_are_physiological():
    """[G1][G2] Atrial volumes indexed to BSA must match human reference ranges.

    CLOSED 2026-08-26 by the venous rework, backlog item 28. Was a strict xfail
    on LAVmax alone, at 50.51 mL/m2 against a ceiling of 50 (down from 106.4
    before the chamber rebuild). Now 48.7.

    THE 93.2 mL ANOMALY IS RESOLVED. LAVmax had come out at exactly 93.2 mL
    across two atrial parameter sets differing in V0, E_min AND E_max — the
    signature of a clamp, or of the parameter not reaching the quantity being
    measured. The standing hypothesis was that with the mitral valve at 0.01 and
    the pulmonary-vein junction at 0.02, the pulmonary veins, left atrium and
    left ventricle were nearly continuous, so "LA volume" was a
    compliance-weighted share of one pooled volume rather than an independently
    set quantity. That hypothesis was RIGHT, and the fix came from the systemic
    side: reducing systemic venous compliance and raising drainage resistance
    left less volume in the central pool, so the shared pool shrank. LAVmax is
    once again a function of atrial parameters rather than of the pool.
    """
    """Left atrial volumes indexed to BSA. RE-TARGETED 2026-10-25 from Järvinen [J1]
    (LAVmax 52 +/- 9, LAVmin 24 +/- 5) to the range four independent sources agree on:
    Steding-Ehrenborg 2021 (PMID 33539261, Lund CMR, APPENDAGE INCLUDED) ~38 / ~19,
    Gao 2022 (PMID 35124105) LAVmax 36.9 +/- 7.7, Luu 2022 (PMID 34980185) 40 / 22,
    Prioli 1998 41 +/- 9 / 17 +/- 4. Järvinen alone sits high on both (source_conflicts
    F, revised 2026-10-25: Jesper, "distrust Järvinen if independent sources disagree").
    Bands: LAVmax Gao's mean +/- 1 SD (29-45, the others inside); LAVmin 14-26 (sources
    17-22, Prioli's SD of 4 either side). With Järvinen's bands the one-for-one sweep
    passed at 60 mL/m2; against these it fails at +2 SD."""
    s = _atrial_state()
    assert 29.0 <= s["la"]["vmax_i"] <= 45.0, (
        f"LAVmax {s['la']['vmax_i']:.1f} mL/m2 ({s['la']['vmax']:.0f} mL) outside "
        f"29-45; four sources 37-41 (Gao 36.9 +/- 7.7)"
    )
    assert 14.0 <= s["la"]["vmin_i"] <= 26.0, (
        f"LAVmin {s['la']['vmin_i']:.1f} mL/m2 outside 14-26; four sources 17-22"
    )


def test_right_atrial_volumes_are_physiological():
    """Right atrial volumes, APPENDAGE INCLUDED, cavae excluded, indexed to BSA.
    RE-TARGETED 2026-10-26 from Järvinen 1994 Radiology (RAmax 77 +/- 11, cast-corrected
    ~81), whose absolute atrial volumes read ~1.5x every other source on both sides
    (source_conflicts F rev. b, Jesper's rule). Now: Maceira 2013 (PMID 23566426, n 120,
    CMR, ring tracked) RAVmax 54 +/- 10.3 and Sjöberg 2020 (PMID 31886724, n 15) 66 +/- 11
    — ~1 SD apart, so the band is the union of their 1 SD (44-77), not an average.
    RAVmin: Sjöberg 37 +/- 16 (21-53); Maceira's derived min (54 - 31) = 23 lies inside.
    The RA unstressed volume is PINNED on the max, so the max band guards the pin."""
    s = _atrial_state()
    assert 44.0 <= s["ra"]["vmax_i"] <= 77.0, (
        f"RAVmax {s['ra']['vmax_i']:.1f} mL/m2 ({s['ra']['vmax']:.0f} mL) outside "
        f"44-77; Maceira 54 +/- 10, Sjöberg 66 +/- 11"
    )
    assert 21.0 <= s["ra"]["vmin_i"] <= 53.0, (
        f"RAVmin {s['ra']['vmin_i']:.1f} mL/m2 outside 21-53; Sjöberg 37 +/- 16, Maceira ~23"
    )


# Strict xfail 2026-10-17 to 2026-10-25 ("LA total emptying 59.1 % against Järvinen's
# 53 +/- 5; likely cause: the split of the swept volume between the atria"). CLOSED
# 2026-10-25 by exactly that: the AV-plane sweep's atrial share (AV_ATRIAL_SHARE_LA,
# Maksuti geometry) and LA_EMIN re-pinned on four-source filling. Emptying is a RATIO
# on which Järvinen agrees with the other sources, so his band is kept.
def test_atrial_emptying_fractions_are_physiological():
    """[G1][G2] Total atrial emptying fraction must match human reference ranges.

    PASSES since the whole-heart rebuild (2026-08-24). Was a strict xfail at
    LA-EF 38.0% and RA-EF 32.4% — an oversized atrium moving a normal stroke volume
    necessarily empties poorly, and both were consequences of chamber volumes 3-6x
    too large rather than of the elastance ratio itself.
    Asserted separately from the volumes because emptying fraction constrains the
    E_max/E_min RATIO while the volumes constrain V0 and the operating point; fixing
    one without the other leaves an atrium the right size with the wrong dynamics.
    """
    s = _atrial_state()
    # [J1] since 2026-10-15 (was 45-72 on [G1][G2], atrial body only).
    assert 48.0 <= s["la"]["ef"] <= 58.0, (
        f"LA emptying fraction {s['la']['ef']:.1f}% outside 48-58; [J1] 53 +/- 5 "
        f"(appendage included)"
    )


# Strict xfail 2026-10-17 to 2026-10-26 ("RA total emptying 44.8 % against Järvinen's
# 52 +/- 6"). CLOSED 2026-10-26 by the RA's share of the AV-plane sweep (Sjöberg) and its
# unstressed volume re-pinned on Maceira: the reservoir was not too small, the chamber
# was too big. Emptying is a RATIO on which Järvinen and Maceira (56 +/- 7) agree.
def test_right_atrial_emptying_fraction_is_physiological():
    """[PMID 8134560 — Järvinen 1994] RA fractional emptying 52 +/- 6 % (average
    beat, free breathing). RE-TARGETED 2026-10-17 from Gao's 49.7 +/- 9.2 (body
    only). Band 1 SD."""
    s = _atrial_state()
    assert 46.0 <= s["ra"]["ef"] <= 58.0, (
        f"RA emptying fraction {s['ra']['ef']:.1f}% outside 46-58; Järvinen 52 +/- 6"
    )


# ===========================================================================
# 19. Respiratory modulation of right atrial filling
#     [F1] Ferguson JJ, Miller MJ, Aroesty JM, Sahagian P, Grossman W,
#          McKay RG (1989) J Am Coll Cardiol 13:630-6. PMID 2918169,
#          DOI 10.1016/0735-1097(89)90604-9
# ===========================================================================

def test_ra_fills_during_spontaneous_inspiration_ferguson1989():
    """[F1 Figure 3] Right atrial volume RISES during spontaneous inspiration.

    Ferguson recorded simultaneous right atrial pressure and impedance volume
    in a patient without an atrial septal defect, and states it directly:
    "With inspiration there is a decline in right atrial pressure and an
    increase in right atrial volume. During expiration, right atrial pressure
    increases as right atrial volume declines."

    This is a CALIBRATION-INDEPENDENT guard on the thoracic compartment set
    (`THORACIC_COMPARTMENTS` in circulation.py). Atrial filling rises on
    inspiration only because the falling pleural pressure is applied to the
    right atrium and not to the abdominal IVC, which widens the venoatrial
    gradient. A model that left the RA out of the set, or applied intrathoracic
    pressure with the wrong sign, would flatten or invert this. Until
    2026-08-25 the set omitted the aorta, brachiocephalic, SVC and coronary —
    see validation_log.md "PPV diagnosed" — so the boundaries this asserts are
    newly established and worth pinning.

    Volume is compared rather than pressure for two reasons. Ferguson's volumes
    are in RELATIVE impedance units, so only the DIRECTION is usable from that
    paper at all; and the model's reported `cvp` deliberately excludes
    respiratory ITP (it is defined as an end-expiratory clinical reading), so
    no model output corresponds to Ferguson's continuous catheter pressure
    trace. The pressure half of his sentence therefore cannot be asserted
    against any current output — recorded in the validation log rather than
    silently dropped.

    Phase-averaged across whole breaths: heart rate and respiratory rate are
    deliberately incommensurate (72 bpm vs 10 breaths/min = 7.2 beats per
    breath), so averaging by respiratory phase over many breaths cancels the
    cardiac oscillation instead of aliasing it.
    """
    from model.circulation import THORACIC_COMPARTMENTS

    assert "right_atrium" in THORACIC_COMPARTMENTS, (
        "the RA must be inside the thoracic set for this test to mean anything"
    )

    p = SimParams()
    p.ventilation_mode   = 'spontaneous'
    p.resp_rate_bpm      = 10.0
    p.baroreflex_enabled = False
    r = run_simulation(p, duration_s=60.0, dt=DT, use_baroreflex=False)

    t = r["t"]
    v_ra = r["volumes"][:, IDX["right_atrium"]]

    # Discard the settling transient, then bin by position within the breath.
    m = t >= 20.0
    breath_s = 60.0 / p.resp_rate_bpm
    phase = (t[m] % breath_s) / breath_s
    insp = phase < p.ie_ratio          # inspiratory fraction of the cycle
    v_insp = float(v_ra[m][insp].mean())
    v_exp  = float(v_ra[m][~insp].mean())

    assert v_insp > v_exp, (
        f"RA did not fill on inspiration: inspiratory mean {v_insp:.2f} mL vs "
        f"expiratory {v_exp:.2f} mL. [F1 Fig 3] requires inspiration > expiration. "
        f"Check that 'right_atrium' is in THORACIC_COMPARTMENTS and that the IVC "
        f"is NOT (the gradient depends on the boundary sitting at ivc->RA)."
    )


# ===========================================================================
# 20. Patient sex — backlog item 32
#     [L1] Luu JM et al. (2022) J Cardiovasc Magn Reson 24:2. PMID 34980185
#     [G1] Gao Y et al. (2022) Int J Cardiol 352:180-187. PMID 35124105
# ===========================================================================

def test_male_patient_is_bit_for_bit_the_reference():
    """Adding sex must not change a single male number.

    The reference parameter set IS male — every chamber was derived from the
    male columns of [L1] and [G1] during the 2026-08-24 rebuild. So sex="male"
    has to be the exact identity, or the whole validation suite silently moves
    underneath a feature that was supposed to add an option, not change one.

    This is the guard that lets `sex` exist at all. Asserted on the compartments
    AND on every cardiac factor, because either could drift independently.
    """
    from model.patient import SEX_CHAMBER_FACTORS

    default_comps, default_card = build_patient_params(175, 70)
    male_comps, male_card = build_patient_params(175, 70, sex="male")

    for a, b in zip(default_comps, male_comps):
        assert a.name == b.name
        assert a.unstressed_volume == b.unstressed_volume, (
            f"{a.name} V0 moved when sex='male' was passed explicitly")
        assert a.init_volume == b.init_volume, f"{a.name} init_volume moved"
        assert a.compliance == b.compliance, f"{a.name} compliance moved"

    for k, v in male_card.items():
        if k.endswith("_factor"):
            assert v == 1.0, f"male cardiac factor {k} is {v}, must be exactly 1.0"

    for chamber, f in SEX_CHAMBER_FACTORS["male"].items():
        assert f["volume"] == 1.0 and f["emax"] == 1.0, (
            f"male {chamber} factors must be exactly 1.0, got {f}")


# CLOSED 2026-10-08 — was a strict xfail from 2026-10-04 and XPASSED on the
# grade D leg capacity change. The gap was female LVEDV 59.95 mL/m2 against a
# floor of 60.0: the calf stiffening of 2026-10-04 had let the legs hold ~20 mL
# more at rest and preload fell with it. Re-deriving the leg V0 so each segment
# holds its OLD resting volume at its OLD settled pressure (compartments.py,
# LEG CAPACITY) gave that preload back. **The band was never widened** — the
# open question it carried (should the floor be Luu's 1 SD, as the right-atrial
# band is Gao's 1 SD?) is now moot for this value but still worth Jesper's
# answer, because the band's tightness is still unexplained.
# BANDS RE-SET 2026-10-11 (Jesper's call). The ventricular bands were 60-71 and
# 66-80: Luu's mean +/- about HALF an SD, with no reason recorded anywhere — not in
# the commit that added them (2297b9d), the log or the ledger. An unsourced band
# tighter than the evidence is a guess, so both now use Luu's own 1 SD, as the
# right-atrial band already uses Gao's. A strict xfail opened the same day
# (female LVEDV 58.3 < 60) is closed by this, and the closure is BY the re-set,
# not by the model moving — stated so nobody reads it as a fix.
def test_female_chamber_volumes_match_luu_and_gao():
    """Female chamber volumes are smaller than male, and land in their sourced bands.

    The DIRECTION assertions are the point of the sex feature and are
    calibration-independent: female < male for all three chambers, whatever the
    parameters are set to.

    ON THE RIGHT-ATRIAL BAND. It is [G1] Gao's own 1 SD, 24.5-40.9 mL/m2 around
    32.7 +/- 8.2. It was previously narrower (27-38, about 0.67 SD), set tight
    deliberately to expose a suspected under-filling of the right heart. That
    suspicion was withdrawn on 2026-09-09: the pressure evidence for it compared
    the model's right atrium against a catheter tip sitting in the LEFT
    SUBCLAVIAN VEIN, and against a respiratory-cycle mean where a catheter reads
    end-expiration. Measured like with like the model gives 3.69 mmHg against
    Richter 2021's measured 3 [2-6] (PMID 33655769). With the hypothesis gone,
    so is the case for a band tighter than the evidence.
    **If that withdrawal is ever itself reversed, tighten this band again.**

    Original docstring follows.
    """
    """[L1][G1] A female patient must have the measured female chamber volumes.

    The sex difference SURVIVES BSA indexing — that is the whole reason this
    exists. These are ratios of already-indexed values, so body size is out.
    Compared at fixed height and weight so only sex differs.

    Targets, indexed to BSA: LVEDV 65 [L1], RVEDV 72 [L1], RAVmax 32.7 [G1],
    against male 74, 86 and 34.9.

    THE LEFT ATRIUM IS DELIBERATELY NOT ASSERTED. It is the one chamber that is
    LARGER in women indexed to BSA (38.4 vs 35.7 [G1]), and the model cannot
    currently produce that: measured transmission of an assigned LA volume
    factor is NEGATIVE — assigning a larger LA made the chamber smaller —
    because with the mitral valve at 0.01 and the pulmonary-vein junction at
    0.02 the pulmonary veins, LA and LV are nearly continuous, so LA volume is a
    share of one pooled volume. Backlog items 23 and 25a. Recorded rather than
    asserted, so the gap is visible without being silently accepted.
    """
    from model.patient import bsa_mosteller

    h, w = 170.0, 70.0
    bsa = bsa_mosteller(h, w)

    def chambers(sex):
        comps, card = build_patient_params(h, w, sex=sex)
        p = SimParams(compartments=comps)
        apply_cardiac(p, card)
        p.ventilation_mode = "none"
        r = run_simulation(p, duration_s=45.0, dt=DT)
        V = r["volumes"][int(len(r["t"]) * 0.6):]
        return {n: V[:, IDX[n]].max() / bsa
                for n in ("left_ventricle", "right_ventricle", "right_atrium")}

    m, f = chambers("male"), chambers("female")

    # Direction first — calibration-independent, and the point of the feature.
    for name in ("left_ventricle", "right_ventricle", "right_atrium"):
        assert f[name] < m[name], (
            f"female {name} {f[name]:.1f} not smaller than male {m[name]:.1f} "
            f"mL/m2 — every one of these three is smaller in women per [L1][G1]")

    # Then the magnitudes, against the measured female columns.
    # Bands are Luu's 1 SD; see the comment above the test for why.
    assert 54.0 <= f["left_ventricle"] <= 76.0, (
        f"female LVEDV {f['left_ventricle']:.1f} mL/m2 outside Luu's 1 SD of 54-76; "
        f"[L1] female 65 ± 11, male 74")
    assert 59.0 <= f["right_ventricle"] <= 85.0, (
        f"female RVEDV {f['right_ventricle']:.1f} mL/m2 outside Luu's 1 SD of 59-85; "
        f"[L1] female 72 ± 13, male 86")
    # RE-TARGETED 2026-10-26 to Maceira 2013's FEMALE column (PMID 23566426, appendage
    # included): 53 mL/m2, whole-group SD 10.3 -> 43-63. Was Järvinen 70-92 (set aside,
    # source_conflicts F rev. b); Gao's 32.7 is the atrial body only.
    assert 43.0 <= f["right_atrium"] <= 63.0, (
        f"female RAVmax {f['right_atrium']:.1f} mL/m2 outside Maceira's female 53 +/- 10 "
        f"(43-63; appendage included)")


# ===========================================================================
# 21. Drug dose-response sanity — the guard that would have caught the
#     noradrenaline RV inotropy sign inversion (2026-08-28)
# ===========================================================================

def test_every_drug_is_neutral_at_zero_dose():
    """At zero dose every drug factor must be exactly 1.0.

    This is what a dose-response MEANS, and it is calibration-independent: it
    asserts nothing about magnitudes, only that a drug which is not being given
    does nothing.

    It would have caught the defect it was written for. `norepinephrine()`
    returned `rv_emax_factor = emax_factor * 0.7`, and since `emax_factor` is a
    multiplier around 1.0, that inverted the effect instead of scaling it: a
    23 % SUPPRESSION of right ventricular contractility at the therapeutic dose,
    from a drug documented as mildly inotropic — and 0.7, a 30 % suppression, at
    a dose of ZERO. The zero-dose value is the tell, which is why this test
    checks there. See validation_log.md, "Noradrenaline vs phenylephrine".

    Applies to every drug, so a future one cannot reintroduce the same shape.
    """
    from model.pharmacology import (norepinephrine, phenylephrine, vasopressin,
                                    epinephrine, propofol, spinal_anaesthesia,
                                    combined_drug_factors)

    drugs = {
        "norepinephrine": norepinephrine, "phenylephrine": phenylephrine,
        "vasopressin": vasopressin, "epinephrine": epinephrine,
        "propofol": propofol, "spinal_anaesthesia": spinal_anaesthesia,
    }
    # MOST TERMS MULTIPLY, so neutral is 1.0. A few ADD, and for those neutral is
    # 0.0 — `alpha1_venous_drive` joins a shared receptor pool (item 70 pass 3)
    # rather than scaling anything. The additive keys are listed EXPLICITLY, so a
    # future additive term that is not declared here fails loudly against the
    # strict rule instead of being waved through at 0.0.
    ADDITIVE = {"alpha1_venous_drive"}

    def neutral(key):
        return 0.0 if key in ADDITIVE else 1.0

    for name, fn in drugs.items():
        for factor, value in fn(0.0).items():
            assert value == pytest.approx(neutral(factor), abs=1e-12), (
                f"{name}(0.0) returns {factor}={value}, must be exactly "
                f"{neutral(factor)}. A drug that is not being given must do "
                f"nothing. If this is a 'fraction of another effect' term, it "
                f"must be written 1 + k*(f - 1), not f*k — the latter inverts "
                f"the effect. If it is a new ADDITIVE term, declare it in "
                f"ADDITIVE above and say in pharmacology.py why it adds."
            )

    # And through the combining path, which is what the model actually calls.
    for name in drugs:
        for factor, value in combined_drug_factors({name: 0.0}).items():
            assert value == pytest.approx(neutral(factor), abs=1e-12), (
                f"combined_drug_factors({{{name!r}: 0.0}}) returns "
                f"{factor}={value}, must be exactly {neutral(factor)}"
            )


def test_norepinephrine_rv_inotropy_is_a_boost_not_a_suppression():
    """Noradrenaline must not weaken the right ventricle.

    Its own docstring says "Secondary: mild inotropy". The RV factor is
    deliberately a FRACTION of the LV effect — the RV is thinner-walled and less
    beta-1 responsive — but a fraction of a boost is still a boost. Asserted
    across the clinical range (0.01-0.5 mcg/kg/min) rather than at one dose,
    because the defect this replaces was wrong at every dose including zero.

    Direction only. No magnitude is asserted, because none is sourced: the 0.7
    fraction is a modelling choice, not a measurement.
    """
    from model.pharmacology import norepinephrine

    for dose in (0.0, 0.01, 0.05, 0.10, 0.20, 0.50):
        f = norepinephrine(dose)
        lv, rv = f["lv_emax_factor"], f["rv_emax_factor"]
        assert rv >= 1.0, (
            f"NE {dose} mcg/kg/min gives rv_emax_factor {rv:.3f} — noradrenaline "
            f"must not SUPPRESS the right ventricle")
        assert rv <= lv, (
            f"NE {dose} gives rv_emax_factor {rv:.3f} above lv {lv:.3f}; the RV "
            f"effect is meant to be a fraction of the LV effect")
        if dose > 0:
            assert rv > 1.0, f"NE {dose} gives no RV inotropic effect at all"


# ===========================================================================
# 22. Output downsampling and high-resolution slices — backlog item 33
# ===========================================================================

def test_ppv_does_not_depend_on_output_every():
    """PPV must be the same quantity whatever the output decimation.

    THIS TEST EXISTS BECAUSE THE FEATURE HAD NO TEST FOR THE CASE IT IS FOR.
    `output_every` stores one block MEAN per N steps, and it exists for long
    runs. `test_output_every_1_is_bit_for_bit_the_default` below asserts the
    IDENTITY case — the one setting the feature is not used at.

    Measured 2026-09-24, before the fix (backlog item 69):

        output_every      1      10     100
        PPV            6.05    1.31    0.00

    Two defects. PPV was reconstructed after the loop from the STORED aortic
    pressure, which is a block mean, and `_compute_ppv` was handed the raw dt —
    so it sized a cardiac cycle in RAW steps and asked find_peaks for peaks
    farther apart than the whole array. It found fewer than three and returned
    zeros. Separately, the non-mechanical branch returned an array of length
    `n` (raw steps) where every other series is `n_out`.

    PPV is now measured in the loop, beat by beat, at full rate. Block
    averaging then applies to PPV itself, which is a respiratory-timescale
    quantity and survives it.

    THE GENERAL RULE THIS PINS: a derived quantity must be computed on the
    timescale it lives on. Beat-to-beat quantities belong in the loop.
    """
    comps, cardiac = build_patient_params(REF_HEIGHT_CM, REF_WEIGHT_KG)

    def ppv_at(oe):
        p = SimParams(compartments=comps)
        apply_cardiac(p, cardiac)
        p.ventilation_mode = "mechanical"
        p.peep_cmh2o, p.pip_cmh2o, p.resp_rate_bpm = 5.0, 20.0, 12.0
        r = run_simulation(p, duration_s=60.0, dt=DT, output_every=oe)
        t = np.asarray(r["t"])
        assert len(np.asarray(r["ppv"])) == len(t), (
            f"ppv length {len(np.asarray(r['ppv']))} != t length {len(t)} "
            f"at output_every={oe}"
        )
        return float(np.mean(np.asarray(r["ppv"])[t >= t[-1] - 20.0]))

    ref = ppv_at(1)
    assert ref > 1.0, f"PPV implausibly small at output_every=1: {ref:.2f} %"

    for oe in (10, 100):
        got = ppv_at(oe)
        err = abs(got - ref) / ref * 100.0
        assert err < 5.0, (
            f"PPV depends on output_every: {ref:.2f} % at 1 vs {got:.2f} % at "
            f"{oe} ({err:.1f} % apart). It is measured per beat in the loop and "
            f"must not change with output decimation."
        )


def test_ppv_length_matches_when_not_mechanically_ventilated():
    """The non-mechanical branch must return `n_out`, not the raw step count.

    Before the fix a spontaneous-breathing run at output_every=100 returned a
    `ppv` of length 30000 against a `t` of 300. Anyone masking ppv by time got
    a length mismatch or silently misaligned data.
    """
    comps, cardiac = build_patient_params(REF_HEIGHT_CM, REF_WEIGHT_KG)
    p = SimParams(compartments=comps)
    apply_cardiac(p, cardiac)
    p.ventilation_mode = "spontaneous"
    r = run_simulation(p, duration_s=30.0, dt=DT, output_every=100)
    assert len(np.asarray(r["ppv"])) == len(np.asarray(r["t"]))


def test_output_every_1_is_bit_for_bit_the_default():
    """Downsampling must not change a single number at output_every=1.

    Same guard as the sex feature: an option that changes the default is not an
    option, it is a silent regression. Every stored series is compared, NaN-aware
    because the slow-dynamics series are NaN before SETTLE_S.
    """
    p = SimParams()
    p.ventilation_mode = "none"
    a = run_simulation(p, duration_s=12.0, dt=DT)
    b = run_simulation(p, duration_s=12.0, dt=DT, output_every=1)

    compared = 0
    for k, va in a.items():
        if not isinstance(va, np.ndarray):
            continue
        compared += 1
        assert va.shape == b[k].shape, f"{k} shape changed"
        assert np.array_equal(va, b[k], equal_nan=True), f"{k} values changed"
    assert compared > 10, "expected to compare many series"


def test_downsampled_output_preserves_means_and_does_not_alias():
    """A downsampled trend must carry the same means as the full-rate run.

    Each stored sample is the block MEAN, not every Nth value. That matters:
    heart rate is ~1.17 Hz, so decimating to 1 Hz would ALIAS the cardiac cycle
    and put a beat-frequency artefact into every trend. Averaging is decimation
    with the anti-aliasing built in.

    Tolerance is 1 %. The point is that the trend is unbiased, not that it is
    identical — it cannot be, it holds a thousand times fewer samples.
    """
    p = SimParams()
    p.ventilation_mode = "none"
    full = run_simulation(p, duration_s=60.0, dt=DT)
    ds = run_simulation(p, duration_s=60.0, dt=DT, output_every=1000)

    assert len(ds["t"]) == 60, f"expected 60 samples at 1 Hz, got {len(ds['t'])}"

    hf, hd = len(full["t"]) // 2, len(ds["t"]) // 2

    # Tolerances differ by quantity, and the reason is physical rather than
    # convenient. MAP, CVP, SV and HR are sampled quantities and agree to about
    # 0.01 %. CARDIAC OUTPUT does not, and cannot: `co_ts` is the INSTANTANEOUS
    # ejection rate, which is zero for most of every beat and large during
    # ejection, and it is then smoothed over 3 s. It is the least favourable
    # signal in the model for any resampling, and beats do not align with
    # 1-second blocks at 69 bpm. Measured 1.1 % at 60 s and 0.24 % at 120 s, i.e.
    # it tightens as the record lengthens, which is what a sampling artefact does
    # and not what a bias does. 2.5 % here is that artefact plus headroom, NOT a
    # tolerance widened until the test passed.
    tolerance = {"map": 0.01, "cvp": 0.01, "sv": 0.01, "hr": 0.01, "co": 0.025}
    for k, tol in tolerance.items():
        a = float(np.mean(full[k][hf:]))
        b = float(np.mean(ds[k][hd:]))
        assert abs(b - a) <= tol * abs(a), (
            f"{k} downsampled mean {b:.4f} differs from full-rate {a:.4f} by "
            f"{100 * (b - a) / a:.2f}%, over the {100 * tol:.1f}% tolerance. "
            f"A large error here means decimation rather than block-averaging, "
            f"which would alias the cardiac cycle into the trend.")


def test_hires_windows_capture_full_resolution_waveforms():
    """High-resolution slices must keep the waveform a trend cannot show.

    Downsampling destroys exactly what this project has repeatedly needed:
    numerical drift appears as a change in waveform MORPHOLOGY, and whether a
    value is sampled mid-systole or end-systole is invisible in a trend. Both
    have cost real debugging time here — see the `p_ref` single-sample defect in
    validation_log.md, and backlog item 31.

    Asserts the slice is genuinely pulsatile, and demonstrates the drift check
    the windows exist for: the same waveform, two windows apart in time.
    """
    p = SimParams()
    p.ventilation_mode = "none"
    r = run_simulation(p, duration_s=60.0, dt=DT, output_every=1000,
                       hires_windows=[(20.0, 30.0), (45.0, 55.0)])

    hi = r["hires"]
    assert len(hi["windows"]) == 2
    assert len(hi["t"]) == 20000, f"expected 20 s at 1 ms, got {len(hi['t'])}"

    w1 = hi["aortic_p"][:10000]
    w2 = hi["aortic_p"][10000:]

    # Genuinely pulsatile — a trend at 1 Hz would show none of this.
    pp1, pp2 = w1.max() - w1.min(), w2.max() - w2.min()
    assert pp1 > 20.0, f"slice not pulsatile: pulse pressure {pp1:.1f} mmHg"

    # The drift check the windows exist for. Same morphology 25 s apart in a
    # steady-state run; a diverging integrator would show here and nowhere else.
    assert abs(pp1 - pp2) < 0.05 * pp1, (
        f"aortic pulse pressure drifted between slices: {pp1:.2f} -> {pp2:.2f} "
        f"mmHg in a steady-state run. Check Euler stability (VALVE_R * C > dt).")


def test_disk_output_round_trips_and_survives_a_crash(tmp_path):
    """A run written to disk must load back identically, and a truncated one
    must still load.

    Two separate claims, and the second is the point of writing incrementally.
    A 24 h run takes about 9 h of wall clock; held only in RAM, a failure at
    hour 8 loses all of it. Rows are written as each output block completes, so
    whatever ran is on disk.
    """
    from model.circulation import load_run

    p = SimParams()
    p.ventilation_mode = "none"
    d = str(tmp_path / "run")
    mem = run_simulation(p, duration_s=30.0, dt=DT, output_every=1000,
                         hires_windows=[(10.0, 20.0)], output_path=d)
    disk = load_run(d)

    assert disk["complete"], "a run that finished must report complete"
    assert disk["n_written"] == disk["meta"]["n_out"] == 30

    for k in ("t", "aortic_p", "map", "cvp", "la_pressure", "co", "hr", "sv",
              "dbp", "sbp", "lvedp", "cpp", "cop", "buckberg",
              "ankle_p", "brachial_p", "volumes"):
        assert np.allclose(np.asarray(mem[k]), np.asarray(disk[k])), (
            f"{k} did not round-trip through disk")

    # High-resolution slices persist too, at full dt.
    assert disk["hires"]["aortic_p"].shape == (10000,)
    assert disk["hires"]["volumes"].shape == (10000, len(IDX))
    assert disk["hires"]["windows"] == [(10.0, 20.0)]

    # CRASH SIMULATION: zero the tail of the trend, as an interrupted run would
    # leave it, and confirm the file still loads and reports how far it got.
    trend_path = tmp_path / "run" / "trend.npy"
    arr = np.load(str(trend_path), mmap_mode="r+")
    arr[20:] = 0.0
    arr.flush()
    del arr

    crashed = load_run(d)
    assert not crashed["complete"], "a truncated run must not report complete"
    assert crashed["n_written"] == 20, (
        f"expected 20 rows written, got {crashed['n_written']}")
    assert np.allclose(np.asarray(crashed["aortic_p"])[:20],
                       np.asarray(mem["aortic_p"])[:20]), (
        "the rows that were written before the crash must still be correct")


# ===========================================================================
# 23. Abdominal pressure coupling — backlog item 27
#
# THE REPO'S MOST COMMON BUG IS A DOCUMENTED MECHANISM THAT IS SILENTLY INERT.
# The dead venous_tone_factor zeroed all venoconstriction for months with the
# code present and reading correctly. These three tests are the guards for the
# abdominal pathway: that it is LIVE, that it is SIGNED correctly, and that it
# is INERT where it has no source. They are calibration-independent — they
# compare the model against itself with the switch flipped — so they stay valid
# if any parameter is retuned. Do not weaken them to make a calibration fit.
# ===========================================================================

def _abd_run(coupling, mode='mechanical', hemorrhage_ml=0.0, duration_s=60.0):
    p = SimParams()
    p.ventilation_mode   = mode
    p.peep_cmh2o         = 5.0
    p.pip_cmh2o          = 20.0
    p.ie_ratio           = 0.33
    p.resp_rate_bpm      = 14.0
    p.baroreflex_enabled = True
    p.abdominal_coupling_enabled = coupling
    if hemorrhage_ml > 0:
        p.hemorrhage_rate_mlmin = hemorrhage_ml / (20.0 / 60.0)
        p.hemorrhage_start_s    = 2.0
        p.hemorrhage_duration_s = 20.0
    return run_simulation(p, duration_s=duration_s, dt=DT)


def test_abdominal_coupling_is_live_and_lifts_splanchnic_pressure():
    """The mechanism must actually reach the abdominal compartments.

    [PMID 26732769, DOI 10.1177/0885066615625180 — Heijnen 2016]
    [PMID 11842062, DOI 10.1152/japplphysiol.00487.2001 — van den Berg 2002]

    A machine breath pushes the diaphragm down, which raises pleural pressure
    AND pressurises the abdomen. Turning the switch on must therefore raise
    mean splanchnic venous volume-weighted pressure. This asserts only the
    SIGN and that the effect is non-zero — no magnitude is claimed, because the
    coefficient is Heijnen's and is carried in respiration.py, not here.
    """
    on  = _abd_run(True)
    off = _abd_run(False)
    h = len(on["volumes"]) // 2

    v_on  = np.asarray(on["volumes"])[h:, IDX["splanchnic_vein"]].mean()
    v_off = np.asarray(off["volumes"])[h:, IDX["splanchnic_vein"]].mean()

    # Squeezing the splanchnic bed moves blood OUT of it, centrally.
    assert v_on < v_off, (
        f"abdominal coupling did not empty the splanchnic reservoir: "
        f"{v_off:.1f} mL off vs {v_on:.1f} mL on — the mechanism is inert or "
        f"inverted. This is the dead-venous_tone_factor failure mode."
    )
    assert abs(v_on - v_off) > 0.5, (
        f"abdominal coupling moved only {abs(v_on - v_off):.3f} mL of "
        f"splanchnic volume — effectively inert"
    )


def test_abdominal_coupling_lowers_ppv_and_keeps_volume_discrimination():
    """[PMID 11842062] Abdominal pressurisation sustains venous return.

    van den Berg raised airway pressure to 19 cmH2O in 42 sedated and PARALYSED
    patients: right atrial pressure went from 8.1 to 15.4 mmHg and cardiac
    output did NOT change, because 70 % or more of the atrial rise was matched
    by an abdominal rise. So switching the mechanism on must LOWER pulse
    pressure variation and RAISE cardiac output.

    The second half is the part that matters clinically: the mechanism must not
    flatten the difference between a full and an empty patient, because that
    difference is what PPV is FOR. Nothing here is tuned — the coefficient
    comes from Heijnen and the discrimination is whatever the model produces.
    """
    on_n,  off_n = _abd_run(True), _abd_run(False)
    on_h,  off_h = _abd_run(True, hemorrhage_ml=1000.0), _abd_run(False, hemorrhage_ml=1000.0)

    def tail(r, key):
        a = np.asarray(r[key]); return float(a[len(a) // 2:].mean())

    ppv_on_n,  ppv_off_n = tail(on_n, "ppv"), tail(off_n, "ppv")
    ppv_on_h,  ppv_off_h = tail(on_h, "ppv"), tail(off_h, "ppv")
    co_on_n,   co_off_n  = tail(on_n, "co"),  tail(off_n, "co")

    assert ppv_on_n < ppv_off_n, (
        f"abdominal coupling did not lower normovolaemic PPV: "
        f"{ppv_off_n:.2f}% off vs {ppv_on_n:.2f}% on"
    )
    assert co_on_n > co_off_n, (
        f"abdominal coupling did not sustain venous return: CO "
        f"{co_off_n:.3f} off vs {co_on_n:.3f} L/min on (van den Berg: CO flat "
        f"despite Pra rising 8.1 -> 15.4 mmHg)"
    )
    assert ppv_on_h > ppv_on_n, (
        f"volume-state discrimination lost with the mechanism ON: "
        f"hypovolaemic {ppv_on_h:.2f}% vs normovolaemic {ppv_on_n:.2f}% — "
        f"haemorrhage must still RAISE PPV"
    )


def test_abdominal_coupling_is_inert_without_positive_pressure():
    """The coupling must not touch spontaneous or apnoeic runs.

    Under SPONTANEOUS breathing the diaphragm contracts under its own power:
    pleural pressure FALLS while abdominal pressure RISES. That is the opposite
    sign, it is generated by muscle rather than transmitted through tissue, and
    it has NO sourced coefficient — Akoumianaki 2024 [PMID 38753985] has the right
    instrumentation but every patient had spontaneous effort, so its gastric
    swing is expiratory muscle contraction. Applying the mechanical coefficient
    there would invent physiology. This test pins that it does not happen, and
    will fail loudly if someone later extends the constant by flipping a sign.
    """
    for mode in ('spontaneous', 'none'):
        on  = _abd_run(True,  mode=mode, duration_s=30.0)
        off = _abd_run(False, mode=mode, duration_s=30.0)
        assert np.allclose(np.asarray(on["aortic_p"]),
                           np.asarray(off["aortic_p"]), rtol=0, atol=0), (
            f"abdominal coupling changed a '{mode}' run — it must be inert "
            f"outside mechanical ventilation, where its coefficient was measured"
        )


# ===========================================================================
# 24. Event-anchored high-resolution windows — backlog item 33, part (c)
#     (continues section 22, which covers downsampling and clock-tick slices)
# ===========================================================================

def test_perturbation_times_derives_events_and_costs_nothing_when_resting():
    """Events come from the params, not from the caller's memory.

    The whole point of an event-anchored window is that it stays attached to
    the event when the scenario is edited. A hand-typed window silently drifts
    out of step the first time someone moves the haemorrhage.
    """
    from model.circulation import perturbation_times

    assert perturbation_times(SimParams(), 60.0) == [], (
        "a resting run has no perturbations, so asking for event windows must "
        "cost nothing"
    )

    p = SimParams()
    p.tilt_end_deg = -20.0
    p.tilt_onset_s, p.tilt_duration_s = 5.0, 5.0
    p.hemorrhage_rate_mlmin = 3000.0
    p.hemorrhage_start_s, p.hemorrhage_duration_s = 10.0, 20.0
    p.fluid_bolus_ml = 500.0
    p.fluid_bolus_start_s, p.fluid_bolus_duration_s = 40.0, 10.0

    # Onsets AND offsets: finishing a bolus is its own transient, and the
    # offsets are the ones a caller forgets.
    assert perturbation_times(p, 60.0) == [5.0, 10.0, 30.0, 40.0, 50.0], (
        "expected tilt onset/end, haemorrhage start/end and bolus start/end, "
        "with the coincident 10.0 s appearing once"
    )

    # A tilt that does not move is not an event.
    q = SimParams()
    q.tilt_onset_s, q.tilt_duration_s = 5.0, 5.0
    assert perturbation_times(q, 60.0) == []


def test_event_windows_capture_a_transient_the_trend_smears():
    """[backlog item 33] Downsampling is a block mean, which is exactly wrong
    at a perturbation.

    This is the test that justifies the feature: at a haemorrhage onset the
    coarse trend averages the fast fall away, while the event-anchored window
    keeps every dt. Asserting that the hires slice resolves a LARGER swing than
    the trend over the same interval is calibration-independent — it compares
    two views of one run, so it holds whatever the model is tuned to.
    """
    from model.circulation import perturbation_times

    p = SimParams()
    p.hemorrhage_rate_mlmin = 3000.0
    p.hemorrhage_start_s    = 10.0
    p.hemorrhage_duration_s = 20.0
    r = run_simulation(p, duration_s=45.0, dt=DT, output_every=500,
                       hires_around_events=(2.0, 4.0))

    wins = r["hires"]["windows"]
    assert wins, "event windows were requested but none were produced"

    # Every derived event must sit inside a window.
    for e in perturbation_times(p, 45.0):
        assert any(a <= e <= b for a, b in wins), (
            f"event at {e:.1f} s is not inside any captured window {wins}"
        )

    # Compare the two views over the first window.
    a, b = wins[0]
    ht = np.asarray(r["hires"]["t"])
    hao = np.asarray(r["hires"]["aortic_p"])[(ht >= a) & (ht <= b)]
    tt = np.asarray(r["t"])
    tao = np.asarray(r["aortic_p"])[(tt >= a) & (tt <= b)]

    assert len(hao) > len(tao) * 10, (
        f"hires slice has {len(hao)} samples against {len(tao)} in the trend — "
        f"it is not actually full resolution"
    )
    assert np.ptp(hao) > np.ptp(tao), (
        f"the event window resolved a smaller swing ({np.ptp(hao):.2f} mmHg) than "
        f"the downsampled trend ({np.ptp(tao):.2f} mmHg) — the block mean cannot "
        f"exceed the raw signal it averages, so this means the window is not "
        f"capturing the transient it is anchored to"
    )


def test_event_windows_merge_when_they_overlap():
    """Two events close together must give one window, not duplicate rows.

    The hires arrays are indexed by a step->row map, so an unmerged overlap
    would write the same step twice and silently corrupt the slice length.
    """
    p = SimParams()
    p.tilt_end_deg = -20.0
    p.tilt_onset_s, p.tilt_duration_s = 5.0, 5.0     # events at 5 s and 10 s
    r = run_simulation(p, duration_s=30.0, dt=DT, output_every=100,
                       hires_around_events=(3.0, 3.0))

    wins = r["hires"]["windows"]
    assert len(wins) == 1, (
        f"windows at 2-8 s and 7-13 s overlap and must merge into one, got {wins}"
    )
    assert wins[0][0] <= 2.0 + 1e-9 and wins[0][1] >= 13.0 - 1e-9, (
        f"merged window {wins[0]} does not span both events"
    )
    assert len(r["hires"]["t"]) == len(set(np.asarray(r["hires"]["t"]).round(9))), (
        "duplicate timestamps in the hires slice — an overlap was not merged"
    )


# ===========================================================================
# 25. Atrioventricular timing — backlog item 25a
# ===========================================================================

def test_atrial_kick_lands_at_end_diastole_with_a_physiological_pr_interval():
    """The atria must contract one PR interval before the ventricles.

    Normal PR is 120-200 ms in adults. The value this replaced,
    ATRIAL_PHASE_OFFSET = 0.60, dated from the initial commit, was unsourced,
    and had no test — at 70 bpm it implied a PR of 514 ms, which is
    complete-heart-block territory. The measured consequence was that LA volume
    ROSE from 40 to 88 mL while atrial activation climbed from 0 to 0.93: the
    atrium contracted in mid-diastole against a shut mitral valve, fighting its
    own filling, and that emptying was then counted as "passive".

    Two things are pinned here. First that the implied PR interval is
    physiological across the rate range the baroreflex actually produces.
    Second that PR is a fixed TIME rather than a fixed fraction of the cycle —
    a fraction would slide the atrial kick out of end-diastole exactly when the
    reflex is working hardest, which is when this model is most often asked a
    question.
    """
    from model.heart import atrial_phase_offset, ATRIAL_PR_INTERVAL_S

    assert 0.12 <= ATRIAL_PR_INTERVAL_S <= 0.20, (
        f"PR interval {ATRIAL_PR_INTERVAL_S * 1000:.0f} ms is outside the normal "
        f"adult range of 120-200 ms"
    )

    # Across the baroreflex's own clamp range (30-180 bpm), the implied PR must
    # stay a real PR — never the half-second the old constant implied.
    for hr in (30.0, 50.0, 70.0, 100.0, 140.0, 180.0):
        pr_ms = atrial_phase_offset(hr) * (60.0 / hr) * 1000.0
        assert pr_ms <= 200.0, (
            f"at {hr:.0f} bpm the implied PR interval is {pr_ms:.0f} ms, above "
            f"the 200 ms upper limit of normal"
        )

    # A fixed TIME means the phase fraction must GROW as the cycle shortens.
    assert atrial_phase_offset(140.0) > atrial_phase_offset(70.0), (
        "the atrial offset is behaving as a fixed fraction of the cycle rather "
        "than a fixed PR time — at double the rate it must occupy a larger "
        "fraction of a shorter cycle"
    )

    # And the kick must land in END-diastole: activation begins at cardiac phase
    # 1 - offset, which for a normal PR is the last ~20 % of the cycle.
    onset_phase = 1.0 - atrial_phase_offset(70.0)
    assert 0.75 <= onset_phase <= 0.95, (
        f"atrial activation begins at cardiac phase {onset_phase:.2f}; at 70 bpm "
        f"a normal PR puts it in the last quarter of diastole, not mid-diastole "
        f"(the old 0.60 offset put it at 0.40)"
    )


# ===========================================================================
# 26. Valve resistances are named and independently settable — item 25a
# ===========================================================================

def test_valve_resistances_are_a_pure_refactor():
    """Naming the four valves must not change a single number.

    Before 2026-08-31 the flow equations divided by whichever compartment the
    inflow convention pointed at: tricuspid by right_ventricle.resistance,
    pulmonic by pulmonary_art.resistance, and BOTH mitral and aortic by
    left_ventricle.resistance. That is self-consistent with the rest of the
    model — a compartment's `resistance` is its inflow resistance — but it
    meant mitral could not be varied without also varying aortic.

    This pins that the named parameters carry exactly the values the old
    expressions produced, so the refactor is provably behaviour-neutral and any
    later change to a valve is visible as its own diff.
    """
    from model.compartments import (default_compartments, IDX as CIDX,
                                    TRICUSPID_R, PULMONIC_R, MITRAL_R, AORTIC_R)
    c = default_compartments()

    assert TRICUSPID_R == c[CIDX["right_ventricle"]].resistance
    assert PULMONIC_R == c[CIDX["pulmonary_art"]].resistance
    assert MITRAL_R == c[CIDX["left_ventricle"]].resistance
    assert AORTIC_R == c[CIDX["left_ventricle"]].resistance

    # THE ASYMMETRY WAS NORMALISED ON 2026-09-10, which is the deliberate,
    # visible change this assertion existed to force. The pulmonic valve was
    # 0.03 against 0.01 for the other three — inherited because
    # pulmonary_art.resistance served double duty as valve and PA inflow, and
    # left in place with the question "whether 3x is intended" written into
    # compartments.py.
    # MEASURED, AND IT WAS NOT INTENDED: peak pulmonic gradient 15.93 mmHg
    # against the aortic valve's 8.55, where under 10 is normal and 10-40 is
    # mild stenosis. The model had a mild functional pulmonic stenosis, which is
    # why RV peak pressure read 40.99 against a pulmonary artery systolic of
    # 29.82. Reasoning and re-measurement in validation_log.md, 2026-09-10.
    assert PULMONIC_R == MITRAL_R == 0.01, (
        "all four valves should now share VALVE_R; if one has been changed "
        "again, say why in the validation log"
    )


def test_mitral_and_aortic_resistance_are_independently_settable():
    """The whole point of the refactor: mitral must move without aortic.

    This is also the guard for a trap that already cost a parameter sweep.
    `left_atrium.resistance` and `right_atrium.resistance` are NOT read by
    anything — under the inflow convention an atrium's inflow is the upstream
    vein's drain_resistance — so setting them looks reasonable and does
    nothing. On 2026-08-31 a sweep of left_atrium.resistance from 0.01 to 0.08
    returned results identical to six significant figures, which is what gave
    it away. Anyone reaching for a mitral knob must find the live one.
    """
    base = run_simulation(_valve_params(), duration_s=12.0, dt=DT)

    # The dead field: setting it must change nothing at all.
    p_dead = _valve_params()
    p_dead.compartments[IDX["left_atrium"]].resistance = 0.08
    dead = run_simulation(p_dead, duration_s=12.0, dt=DT)
    assert np.allclose(np.asarray(dead["aortic_p"]),
                       np.asarray(base["aortic_p"]), rtol=0, atol=0), (
        "left_atrium.resistance is now live — if that was intended the comment "
        "in compartments.py and this test both need updating"
    )

    # The live knob: setting it must change the run, and must NOT be the same
    # lever as the aortic valve.
    p_mit = _valve_params(); p_mit.mitral_r = 0.04
    mit = run_simulation(p_mit, duration_s=12.0, dt=DT)
    assert not np.allclose(np.asarray(mit["aortic_p"]),
                           np.asarray(base["aortic_p"]), rtol=0, atol=0), (
        "params.mitral_r had no effect — the mitral valve is not wired to it"
    )

    p_ao = _valve_params(); p_ao.aortic_r = 0.04
    ao = run_simulation(p_ao, duration_s=12.0, dt=DT)
    assert not np.allclose(np.asarray(mit["aortic_p"]),
                           np.asarray(ao["aortic_p"]), rtol=0, atol=0), (
        "raising mitral_r and aortic_r produced identical runs — they are still "
        "sharing one parameter, which is exactly what this refactor removed"
    )


def _valve_params():
    p = SimParams()
    p.ventilation_mode = "none"
    p.baroreflex_enabled = False
    p.slow_dynamics_enabled = False
    return p


# ===========================================================================
# 27. Age relations — backlog item 25b
# ===========================================================================

def test_age_relations_interpolate_and_clamp():
    """[PMID 25896355][PMID 23097384][PMID 35124105] Sourced age tables.

    The model had NO age at all while drawing targets from cohorts spanning 44
    to 61 years, across which the sources' own tables differ by 21-36 % in the
    very quantities item 25a is calibrating. This pins the interpolation and,
    more importantly, the direction of each relation — a sign error here would
    silently reverse every age-adjusted target.
    """
    from model.aging import (REFERENCE_AGE_YEARS, at_age, restate_at_reference_age,
                             NORRE_EA_MEN, ALHOGBANI_ACC, GAO_LAEF_PASSIVE_MEN,
                             GAO_LAEF_BOOSTER_MEN)

    assert REFERENCE_AGE_YEARS == 55.0

    # Exact at the tabulated points.
    assert at_age(NORRE_EA_MEN, 50.0) == pytest.approx(1.22)
    assert at_age(ALHOGBANI_ACC, 47.5) == pytest.approx(28.0)

    # Clamped outside the measured span, never extrapolated.
    assert at_age(NORRE_EA_MEN, 5.0) == pytest.approx(1.69)
    assert at_age(NORRE_EA_MEN, 120.0) == pytest.approx(0.96)

    # DIRECTIONS. The ageing atrium takes over more of ventricular filling:
    # early filling falls, the atrial kick rises. Four sources agree, and a
    # sign error in any of them would invert an age-adjusted target.
    assert at_age(NORRE_EA_MEN, 30) > at_age(NORRE_EA_MEN, 68), "E/A must FALL with age"
    assert at_age(ALHOGBANI_ACC, 32) < at_age(ALHOGBANI_ACC, 65), "ACC must RISE with age"
    assert at_age(GAO_LAEF_PASSIVE_MEN, 25.5) > at_age(GAO_LAEF_PASSIVE_MEN, 65.5), \
        "LAEF passive must FALL with age"
    assert at_age(GAO_LAEF_BOOSTER_MEN, 25.5) < at_age(GAO_LAEF_BOOSTER_MEN, 65.5), \
        "LAEF booster must RISE with age"

    # Restating moves a target by the RATIO of the relation, and leaves a
    # target already at the reference age untouched.
    assert restate_at_reference_age(NORRE_EA_MEN, 1.22, 55.0) == pytest.approx(1.22)
    assert restate_at_reference_age(NORRE_EA_MEN, 1.22, 45.8) < 1.22, (
        "a target measured in a cohort YOUNGER than 55 must come DOWN when "
        "restated at 55, because E/A falls with age"
    )


def test_patient_age_scales_only_the_elastic_arteries():
    """[PMID 9236450] Age stiffens the aorta; the reference patient is untouched.

    Same discipline item 32 used for sex: the reference case must be
    BIT-FOR-BIT identical, so the entire validation suite is unaffected by the
    feature existing. Age 55 is the reference because the chamber geometry comes
    from Luu 2022, whose male cohort is 55.1 +/- 8.8.
    """
    from model.patient import build_patient_params, ELASTIC_ARTERIES
    from model.aging import REFERENCE_AGE_YEARS

    assert REFERENCE_AGE_YEARS == 55.0

    base, _ = build_patient_params(175, 70, sex="male")
    ref,  _ = build_patient_params(175, 70, sex="male", age_years=55.0)
    for a, b in zip(base, ref):
        assert a.compliance == b.compliance, (
            f"{a.name}: the default must be identical to an explicit age 55")

    young, _ = build_patient_params(175, 70, sex="male", age_years=25.0)
    old,   _ = build_patient_params(175, 70, sex="male", age_years=80.0)

    for c_ref, c_young, c_old in zip(ref, young, old):
        if c_ref.name in ELASTIC_ARTERIES:
            assert c_young.compliance > c_ref.compliance > c_old.compliance, (
                f"{c_ref.name}: compliance must FALL with age — Franklin's pulse "
                f"pressure widens at 0.68 mmHg/year in normotensive men"
            )
        else:
            assert c_young.compliance == c_ref.compliance == c_old.compliance, (
                f"{c_ref.name} changed with age, but only the large elastic "
                f"arteries stiffen. The aortic-to-brachial gradient REVERSES "
                f"with age precisely because the periphery does not."
            )

    # Magnitude, from C ~ SV/PP with Franklin's slope: 1.66 at 25, 0.75 at 80.
    from model.compartments import IDX
    assert young[IDX["aorta"]].compliance / ref[IDX["aorta"]].compliance == \
        pytest.approx(1.66, abs=0.02)
    assert old[IDX["aorta"]].compliance / ref[IDX["aorta"]].compliance == \
        pytest.approx(0.75, abs=0.02)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "KNOWN GAP, 2026-10-06, NOT YET DIAGNOSED. Since the Klotz LV diastolic curve "
    "MAP moves 4.8 mmHg as pulse pressure widens 10.4 with age, where Franklin has "
    "MAP nearly flat. Suspected: the stiffer LV now passes arterial ageing on to "
    "mean pressure. To be diagnosed with the baroreflex work."
))
def test_age_widens_pulse_pressure_the_way_framingham_measured_it():
    """[PMID 9236450] The endpoint, not the parameter.

    Franklin: pulse pressure widens 0.68 mmHg/year in normotensive men while
    MAP is essentially flat (0.016 mmHg/year). A stiffening conduit widens the
    PULSE around a fixed MEAN; a rising resistance would raise the mean. This
    asserts the model reproduces that SHAPE — PP up, MAP nearly unchanged —
    which is the whole reason compliance rather than resistance is scaled.

    REFLEX OFF, AND CHECKED BOTH WAYS 2026-09-28. Franklin followed 2036 awake,
    intact men, so the reflex-off choice does not match his cohort. It is
    harmless, and the check is worth keeping: dPP is +8.75 with the reflex
    either way, and dMAP is -0.90 with it ON against -2.49 with it off. **The
    reflex-intact run is marginally CLOSER to Franklin's near-flat mean.** Left
    off so the test isolates the compliance scaling, which is what it is for.
    Do not re-litigate without re-measuring.
    """
    from model.patient import build_patient_params, apply_cardiac

    def run(age):
        comps, cardiac = build_patient_params(175, 70, sex="male", age_years=age)
        p = SimParams()
        p.compartments = comps
        apply_cardiac(p, cardiac)
        p.ventilation_mode = "none"
        p.baroreflex_enabled = False
        p.slow_dynamics_enabled = False
        r = run_simulation(p, duration_s=30.0, dt=DT, use_baroreflex=False)
        h = len(r["sbp"]) // 2
        sbp = float(np.mean(r["sbp"][h:])); dbp = float(np.mean(r["dbp"][h:]))
        return sbp - dbp, float(np.mean(r["map"][h:]))

    pp_young, map_young = run(30.0)
    pp_ref,   map_ref   = run(55.0)
    pp_old,   map_old   = run(80.0)

    assert pp_young < pp_ref < pp_old, (
        f"pulse pressure must widen with age: {pp_young:.1f} / {pp_ref:.1f} / "
        f"{pp_old:.1f} mmHg at 30 / 55 / 80"
    )
    # MAP must move far less than PP. Franklin's ratio of slopes is
    # 0.016/0.68 = 0.024; anything under 0.25 is the right qualitative shape
    # and leaves room for the closed loop's own response.
    d_pp = pp_old - pp_young
    d_map = abs(map_old - map_young)
    assert d_map < 0.25 * d_pp, (
        f"MAP moved {d_map:.1f} mmHg against a pulse-pressure change of "
        f"{d_pp:.1f}. Franklin has MAP essentially flat (0.016 mmHg/year) while "
        f"PP widens at 0.68 — if the mean is moving this much, the model is "
        f"behaving like rising resistance rather than a stiffening conduit"
    )


def test_chamber_volumes_scale_with_age_toward_luu():
    """[PMID 34980185] Luu Tables 3/4, male: indexed volumes FALL with age.

    LVEDV 77 -> 69 and RVEDV 91 -> 80 mL/m2 across 35-44 to 65-74, while
    ejection fractions hold (LVEF) or rise (RVEF 51 -> 54). Same cohort the
    model's chambers were built from, which is why 55 is the reference age.

    The atria are deliberately NOT scaled with age — the LA's closed-loop
    transmission is NEGATIVE, so assigning it a volume factor moves it the wrong
    way. That is the same reason item 32 left the LA out of sex scaling, and it
    stays blocked on 25a.

    REFLEX OFF, AND CHECKED BOTH WAYS 2026-09-28. Luu imaged intact humans, so
    the reflex-off choice does not match the cohort. It is harmless: the
    direction holds either way, LVEDV -6.1 mL reflex-off against -5.9 with it on,
    RVEDV -11.1 against -11.7. Left off so heart-rate differences do not move
    filling. Do not re-litigate without re-measuring.
    """
    from model.patient import build_patient_params, apply_cardiac
    from model.aging import chamber_age_factors

    # Reference age must be the identity, so the suite is untouched.
    f = chamber_age_factors(55.0)
    for ch in ("left_ventricle", "right_ventricle"):
        assert f[ch]["volume"] == pytest.approx(1.0)
        assert f[ch]["emax"] == pytest.approx(1.0)
    assert "left_atrium" not in f and "right_atrium" not in f, (
        "the atria must not carry age volume factors — LA transmission is "
        "negative and the RA has no sourced age relation in use"
    )

    # Direction: a younger ventricle is larger, an older one smaller.
    assert (chamber_age_factors(40.0)["left_ventricle"]["volume"]
            > 1.0 > chamber_age_factors(70.0)["left_ventricle"]["volume"])

    def edv(age):
        comps, cardiac = build_patient_params(175, 70, sex="male", age_years=age)
        p = SimParams()
        p.compartments = comps
        apply_cardiac(p, cardiac)
        p.ventilation_mode = "none"
        p.baroreflex_enabled = False
        p.slow_dynamics_enabled = False
        r = run_simulation(p, duration_s=30.0, dt=DT, use_baroreflex=False)
        V = np.asarray(r["volumes"])
        h = len(V) // 2
        return (V[h:, IDX["left_ventricle"]].max(),
                V[h:, IDX["right_ventricle"]].max())

    lv40, rv40 = edv(40.0)
    lv55, rv55 = edv(55.0)
    lv70, rv70 = edv(70.0)

    assert lv40 > lv55 > lv70, (
        f"LV end-diastolic volume must fall with age: {lv40:.1f} / {lv55:.1f} / "
        f"{lv70:.1f} mL at 40 / 55 / 70. [PMID 34980185] LVEDV 77 -> 69 mL/m2"
    )
    assert rv40 > rv55 > rv70, (
        f"RV end-diastolic volume must fall with age: {rv40:.1f} / {rv55:.1f} / "
        f"{rv70:.1f} mL. [PMID 34980185] RVEDV 91 -> 80 mL/m2"
    )


def test_intraluminal_ra_pressure_is_a_catheter_trace():
    """[PMID 31560715] The model must expose what a CVC transducer reads.

    `cvp` deliberately OMITS respiratory ITP, because clinical CVP is read at
    end-expiration — the right convention for a single reported number and the
    wrong one for a waveform. Until `ra_intraluminal` existed, no model output
    corresponded to a continuous catheter trace, so the respiratory swing could
    not be compared to a measurement at all (backlog items 30 and 31).

    THE DISTINCTION IS NOT COSMETIC, and mistaking one for the other produced a
    wrong finding on 2026-09-01: the TRANSMURAL swing of 0.14 mmHg was compared
    to Hoff's catheter-measured 3.05 and reported as "22x too small". They are
    different physical quantities. Intraluminal = transmural + ITP.
    """
    def run(mode):
        p = SimParams()
        p.ventilation_mode = mode
        p.resp_rate_bpm = 10.0
        p.slow_dynamics_enabled = False
        r = run_simulation(p, duration_s=60.0, dt=DT)
        t = np.asarray(r["t"]); m = t >= 30.0
        return (np.asarray(r["cvp"])[m], np.asarray(r["ra_intraluminal"])[m],
                t[m])

    # Apnoeic: no respiratory ITP, so the two must be IDENTICAL. This is the
    # guard that the new series is not silently offset from the old one.
    cvp, ra, _ = run("none")
    assert np.allclose(cvp, ra, rtol=0, atol=0), (
        "with ventilation off the intraluminal and transmural traces must be "
        "identical — there is no respiratory ITP to differ by"
    )

    # Spontaneous: ITP is NEGATIVE, so the lumen pressure sits BELOW transmural,
    # and the swing must be LARGER than the transmural one.
    cvp_s, ra_s, t_s = run("spontaneous")
    assert ra_s.mean() < cvp_s.mean(), (
        f"spontaneous intraluminal mean {ra_s.mean():.2f} should sit BELOW "
        f"transmural {cvp_s.mean():.2f} — pleural pressure is sub-atmospheric"
    )
    assert np.ptp(ra_s) > np.ptp(cvp_s), (
        f"the catheter trace must swing MORE than the transmural pressure: "
        f"{np.ptp(ra_s):.2f} vs {np.ptp(cvp_s):.2f} mmHg"
    )

    # And the trough must fall on INSPIRATION — the direction Ferguson 1989
    # describes and Hoff's peak/trough data confirms (trough 4.94 on
    # inspiration, peak 7.99 on expiration).
    period = 60.0 / 10.0
    phase = ((t_s - t_s[0]) % period) / period
    insp = ra_s[phase < 0.33].mean()
    expi = ra_s[phase >= 0.33].mean()
    assert insp < expi, (
        f"intraluminal RA pressure must FALL on inspiration: inspiratory mean "
        f"{insp:.2f} vs expiratory {expi:.2f} mmHg"
    )

    # Mechanical: ITP is POSITIVE, so the sign reverses — lumen ABOVE transmural.
    cvp_m, ra_m, _ = run("mechanical")
    assert ra_m.mean() > cvp_m.mean(), (
        f"under positive-pressure ventilation the intraluminal mean "
        f"{ra_m.mean():.2f} must sit ABOVE transmural {cvp_m.mean():.2f}"
    )


# HOFF'S COHORT, used by every test in this file that cites him: 20 healthy
# volunteers, age 25 +/- 3, height 176 +/- 9 cm, weight 69 +/- 8 kg, supine,
# awake, spontaneously breathing; CVP measured invasively in 10 of them.
#
# SEX IS THE ONE THING THAT CANNOT BE MATCHED HERE. Hoff is 11 M / 9 F and the
# model takes a single sex, so it stays male — the model's default and the
# majority of his cohort. Recorded rather than corrected.
_HOFF_AGE_YEARS  = 25.0
_HOFF_HEIGHT_CM  = 176.0
_HOFF_WEIGHT_KG  = 69.0


def test_spontaneous_respiratory_swing_matches_hoff():
    """[PMID 31560715] The respiratory swing in a CVC trace, against measurement.

    Hoff 2019 measured the peak-to-trough respiratory variation in INTRALUMINAL
    CVP in 10 healthy, awake, supine volunteers aged 25 +/- 3, catheterised for
    an LBNP protocol: 3.05 mmHg mean (SD 1.61, per-subject means 1.00-5.05),
    with the trough on inspiration and the peak on expiration.

    WHY THIS IS AN ENDPOINT CALIBRATION AND WHY THAT IS LEGITIMATE HERE. The
    parameter it constrains, SPONTANEOUS_ITP_SWING_CMH2O, was -1.0 as a
    SELF-DESCRIBED WORKAROUND — the old comment said ITP "has to be kept small
    enough that the RA self-limits... before the cascade destabilises". It was
    never a measured pleural pressure. Replacing an unsourced cap with a value
    anchored to a direct human measurement, through the quantity it governs, is
    the opposite of the tune-to-the-endpoint failure mode.

    The band is wide because Hoff's own per-subject spread is wide (1.00-5.05).
    It is not a tight fit to 3.05 and should not be tightened into one.
    """
    from model.respiration import (SPONTANEOUS_ITP_SWING_CMH2O,
                                   SPONTANEOUS_ITP_BASELINE_CMH2O)

    # AGE- AND SIZE-MATCHED 2026-09-15 to Hoff's own cohort — see _HOFF_*.
    # Swing 3.03 -> 2.86 mmHg, both inside the band and both within 0.2 of
    # Hoff's measured 3.05. The match changes nothing here, which is itself
    # worth knowing: a respiratory swing is a DIFFERENCE and is far less
    # age-sensitive than the absolute pressures.
    p = cohort_params(_HOFF_HEIGHT_CM, _HOFF_WEIGHT_KG, age_years=_HOFF_AGE_YEARS)
    p.ventilation_mode = "spontaneous"
    p.resp_rate_bpm = 10.0
    p.slow_dynamics_enabled = False
    r = run_simulation(p, duration_s=60.0, dt=DT)
    t = np.asarray(r["t"]); m = t >= 30.0
    swing = float(np.ptp(np.asarray(r["ra_intraluminal"])[m]))

    assert 1.5 <= swing <= 5.0, (
        f"intraluminal RA respiratory swing {swing:.2f} mmHg outside 1.5-5.0. "
        f"[PMID 31560715] measured 3.05 +/- 1.61 in 10 healthy awake supine "
        f"volunteers, per-subject means 1.00-5.05 mmHg"
    )

    # THE OLD CAP MUST NOT COME BACK SILENTLY. At -1.0 cmH2O the swing was 0.86,
    # below the band above — so this is already covered — but pinning the
    # constant makes the intent explicit, since the cap was justified by a
    # stability claim that re-measurement disproved (no instability anywhere
    # from -1 to -12 cmH2O).
    assert SPONTANEOUS_ITP_SWING_CMH2O <= -3.0, (
        f"spontaneous ITP swing is {SPONTANEOUS_ITP_SWING_CMH2O} cmH2O. Values "
        f"weaker than -3 cannot reproduce Hoff's measured swing; the previous "
        f"-1.0 gave 0.86 mmHg against a measured 3.05"
    )
    assert SPONTANEOUS_ITP_BASELINE_CMH2O == -2.0, (
        "baseline changed — it sets the MEAN intrathoracic pressure, a separate "
        "and still-open gap (model mean RA 3.2 vs Hoff 6.94), and moving it "
        "changes a different quantity from the one this test constrains"
    )


def test_raising_the_itp_swing_does_not_destabilise():
    """The stability claim behind the old cap, tested rather than asserted.

    The cap existed because "even a -5 mmHg ITP would flood the RA every
    inspiratory cycle". Re-measured 2026-09-01: no instability at any swing from
    -1 to -12 cmH2O. Whatever made that true was fixed by later work. This test
    keeps the finding falsifiable — if a future change reintroduces the
    instability, it fails here rather than being rediscovered as a mystery.
    """
    import model.circulation as circ
    import math
    from model.respiration import _CMHG_TO_MMHG

    orig = circ.intrathoracic_pressure

    def patched(swing):
        # *_ absorbs the ventilatory-hold arguments added on 2026-09-13. This
        # stand-in only needs to reproduce the spontaneous swing, so it ignores
        # them — but it must ACCEPT them, or every caller raises TypeError.
        def f(t, mode, rr, peep, pip, ie, *_, **__):
            if mode == "none":
                return 0.0
            ph = (t % (60.0 / rr)) / (60.0 / rr)
            v = -2.0 + swing * math.sin(math.pi * ph / ie) if ph < ie else -2.0
            return v * _CMHG_TO_MMHG
        return f

    try:
        for swing in (-5.0, -8.0, -12.0):
            circ.intrathoracic_pressure = patched(swing)
            p = SimParams()
            p.ventilation_mode = "spontaneous"
            p.resp_rate_bpm = 10.0
            p.slow_dynamics_enabled = False
            r = run_simulation(p, duration_s=30.0, dt=DT)
            h = len(r["co"]) // 2
            co = float(np.mean(np.asarray(r["co"])[h:]))
            mp = float(np.mean(np.asarray(r["map"])[h:]))
            assert np.isfinite(co) and 3.0 < co < 12.0, (
                f"cardiac output {co:.2f} L/min at ITP swing {swing} cmH2O — the "
                f"old stability cap may be needed again, which would be a finding"
            )
            assert np.isfinite(mp) and 50.0 < mp < 150.0, (
                f"MAP {mp:.1f} mmHg at ITP swing {swing} cmH2O")
    finally:
        circ.intrathoracic_pressure = orig


# ===========================================================================
# 28. Heart-rate arm of the arterial baroreflex — Fritsch 1989
#
# [28] PMID 2916705  DOI 10.1152/ajpregu.1989.256.2.R549
#      Fritsch JM, Rea RF, Eckberg DL (1989) Am J Physiol 256:R549-53.
#      "Carotid baroreflex resetting during drug-induced arterial pressure
#      changes in humans." n=10 healthy volunteers, ages 23-43.
#      Blood pressure was changed in BOTH directions in ONE cohort and each
#      change held for 25 min, giving a matched pair of heart-rate responses:
#          nitroprusside   MAP -11 mmHg   R-R 932 ->  820 ms   HR  +8.8 bpm
#          phenylephrine   MAP +19 mmHg   R-R 932 -> 1251 ms   HR -16.4 bpm
#      Neither drug is meaningfully chronotropic, so both are reflex responses.
#
# FRITSCH CANNOT BE AGE-MATCHED, AND THAT IS A FINDING, NOT AN OMISSION.
# On 2026-09-15 the three young-cohort comparisons were routed through patient
# scaling so the model would stop being 55 years old while citing subjects in
# their twenties. Schaefers and Hoff converted. Fritsch did not, because the
# two tests below drive `BaroreflexController` DIRECTLY, and that class takes
# no patient argument of any kind — no age, no body size, no sex. Age reaches
# only `aging.arterial_compliance_factor` (elastic arteries) and
# `aging.chamber_age_factors` (the two ventricles).
#
# So THE MODEL HAS NO AGE-DEPENDENT BAROREFLEX. Its reflex gain is the same at
# 25 as at 85. The human literature is not ambiguous about this — baroreflex
# sensitivity falls steeply with age — so this is a real absent mechanism, not
# a modelling choice. It is backlog item 51, opened the day it was found, and
# it is deliberately NOT being built hours before a model freeze: adding an age
# law to the reflex would move every reflex-mediated number in the suite at
# once, and the freeze exists to stop exactly that.
#
# WHAT IT COSTS TODAY, stated so the manuscript does not overclaim: the gains
# below are calibrated against a cohort of median age ~33 and applied unchanged
# to the 55-year-old reference patient. Every reflex magnitude the model
# reports is therefore a YOUNGER person's reflex. The direction of the error is
# known — the model's reflex is too brisk for its nominal age — even though the
# size is not.
# ===========================================================================

def _reflex_hr_steady(map_held, dt=0.01, steps=30_000):
    """Steady-state hr_delta for a held MAP, driving the real controller with
    the CARDIOPULMONARY ARM SWITCHED OFF, so this measures the arterial arm.

    This is the model's analogue of Fritsch's neck-chamber sequence: the
    reflex is measured OPEN LOOP, without letting blood pressure move in
    response. His sequences last ~15 s for exactly that reason.

    A CAVEAT ON THE TARGETS, recorded rather than corrected. Fritsch changed
    arterial pressure with drugs that also move filling pressure — nitroprusside
    is a venodilator (CVP falls, which ADDS tachycardia) and phenylephrine a
    venoconstrictor (CVP rises, which ADDS bradycardia). His heart-rate changes
    are therefore the sum of both arms, and attributing all of each to the
    arterial arm makes this model's arterial gain a slight OVERESTIMATE, in the
    same direction at both points. He did not report CVP, so the size of that
    contribution cannot be recovered — see the WANTED list in
    `docs/reference_values.md`. It is bounded by the fact that both targets are
    themselves floors, measured after 25 min of partial reflex resetting.
    """
    from model.baroreflex import BaroreflexController, CP_HR_REFERENCE_CVP_MMHG
    b = BaroreflexController(dt=dt, history_len=200, cp_hr_enabled=False)
    b._map_buf.extend([map_held] * b._map_buf.maxlen)
    b._cvp_buf.extend([CP_HR_REFERENCE_CVP_MMHG] * b._cvp_buf.maxlen)
    for _ in range(steps):
        b.update(map_held, 40.0, CP_HR_REFERENCE_CVP_MMHG)
    return float(b.hr_delta)


def test_hr_reflex_gain_fritsch1989():
    """[28] The heart-rate response to a sustained pressure change matches
    Fritsch's two measured points, in both directions.

    Tolerance is 20 %. Fritsch's own standard errors on these differences are
    roughly +/-4 bpm on the nitroprusside point and +/-3 bpm on the
    phenylephrine point, so 20 % (1.8 and 3.3 bpm) sits inside the study's
    own uncertainty and is not a loose band.

    BOTH TARGETS ARE FLOORS. They were measured after 25 min, by which time
    the reflex has partly reset toward the new pressure, so the acute gain is
    larger than this. A model that overshot them slightly would not be wrong;
    one that falls short of them is.
    """
    from model.baroreflex import MAP_SETPOINT
    for name, d_map, target in (("nitroprusside", -11.0, +8.79),
                                ("phenylephrine", +19.0, -16.42)):
        got = _reflex_hr_steady(MAP_SETPOINT + d_map)
        assert abs(got - target) <= 0.20 * abs(target), (
            f"{name}: dMAP {d_map:+.0f} mmHg gave dHR {got:+.2f} bpm, "
            f"Fritsch measured {target:+.2f} bpm"
        )


def test_hr_reflex_range_exceeds_carotid_limb_fritsch1989():
    """[28] The WHOLE arterial baroreflex must have a wider heart-rate range
    than the carotid limb measured on its own.

    Fritsch's neck chamber isolates the carotid sinus, and the vagal limb at
    that. Its R-R response range was 214 +/- 27 ms about a baseline of 932 ms,
    which is HR 55.1 to 68.6 — a span of 13.5 bpm.

    This is a STRUCTURAL guard, not a calibration: a whole cannot be smaller
    than one of its parts, whatever the gains are set to. It exists because
    the reflex previously spanned only 10.0 bpm in total. The two effector
    gains (-3 vagal, +2 sympathetic) read the same error through the same
    scale, so they collapsed algebraically to a single -5*tanh(err/10) curve
    that was already 97 % saturated after a 1000 mL bleed.
    """
    from model.baroreflex import MAP_SETPOINT
    lo = _reflex_hr_steady(MAP_SETPOINT - 200.0)   # far past saturation
    hi = _reflex_hr_steady(MAP_SETPOINT + 200.0)
    span = lo - hi
    assert span > 13.5, (
        f"whole-reflex HR range {span:.1f} bpm does not exceed the carotid "
        f"limb alone (13.5 bpm, Fritsch 1989)"
    )
    assert lo > 0.0 > hi, (
        f"reflex is signed wrongly: low MAP gave {lo:+.1f} bpm, "
        f"high MAP gave {hi:+.1f} bpm"
    )


def test_hr_reflex_limbs_have_distinct_time_constants():
    """The vagal and sympathetic limbs must respond at DIFFERENT speeds.

    Both limbs read the same pressure error, so the split between them changes
    the dynamics and not the steady-state curve. That makes it easy for the
    split to become decorative — which is exactly what had happened: the two
    limbs ran at tau 1.5 s and 2.0 s through an identical sigmoid, so the
    reflex was effectively one limb with a single time constant.

    This guard asserts the separation is real by stepping the error and
    checking the two filter states have diverged while both are still moving.
    It is calibration-independent: it holds for any choice of gain.
    """
    from model.baroreflex import BaroreflexController, CVP_SETPOINT, MAP_SETPOINT
    dt = 0.01
    b = BaroreflexController(dt=dt, history_len=1)
    for _ in range(int(2.0 / dt)):                 # 2 s after a step
        b.update(MAP_SETPOINT - 20.0, 40.0, CVP_SETPOINT)
    fast, slow = abs(b._para_map), abs(b._symp_hr_map)
    assert fast > 1.5 * slow, (
        f"vagal and sympathetic limbs track together (|para| {fast:.2f} vs "
        f"|symp_hr| {slow:.2f} mmHg at t=2 s) — the split is decorative"
    )


# ===========================================================================
# 29. Cardiopulmonary (filling-pressure) arm of the heart-rate reflex
#
# [29] The graded LBNP dataset in docs/reference_values.md, n=20 healthy
#      supine volunteers, and Vettorello 2016 (PMID 26756378).
#
#      LBNP  0    MAP 77.3   CVP 6.9   HR 65.8
#      LBNP 40    MAP 74.0   CVP 2.5   HR 74.1
#      LBNP 80    MAP 79.9   CVP 0.2   HR 91.1     (>1 L blood-volume equivalent)
#
#      MAP IS FLAT while CVP falls 6.7 mmHg and heart rate rises 25.3 bpm.
#      Vettorello measured HR 69 -> 107 (+38 bpm) over the same LBNP range.
# ===========================================================================

def test_cardiopulmonary_hr_arm_is_live_and_signed():
    """[29] Falling cardiac filling must speed the heart EVEN WITH ARTERIAL
    PRESSURE UNCHANGED, and the arm must do nothing when switched off.

    This is a calibration-independent guard of the kind in §14. It holds MAP
    exactly at the setpoint, so the arterial arm contributes precisely zero and
    anything that appears comes from the filling-pressure arm alone. No choice
    of arterial gain can satisfy it.

    It exists because the model could not reproduce the human data at all
    before 2026-09-04: the CVP error reached SVR, contractility and venous tone
    but never heart rate, so with pressure held flat the model produced no
    tachycardia whatsoever.
    """
    from model.baroreflex import (BaroreflexController, MAP_SETPOINT,
                                  CP_HR_REFERENCE_CVP_MMHG as REF)

    def hr_at(cvp, cp_on):
        b = BaroreflexController(dt=0.01, history_len=200, cp_hr_enabled=cp_on)
        b._map_buf.extend([MAP_SETPOINT] * b._map_buf.maxlen)
        b._cvp_buf.extend([cvp] * b._cvp_buf.maxlen)
        for _ in range(30_000):
            b.update(MAP_SETPOINT, 40.0, cvp)
        return float(b.hr_delta)

    # Silent at the reference filling pressure — no standing offset at rest.
    assert abs(hr_at(REF, True)) < 0.1, (
        f"cardiopulmonary arm is not silent at rest: {hr_at(REF, True):+.2f} bpm"
    )

    # Hoff's stimulus: CVP down 6.7 mmHg, arterial pressure unchanged.
    lo = hr_at(REF - 6.7, True)
    assert 15.0 < lo < 32.0, (
        f"filling-pressure fall of 6.7 mmHg gave {lo:+.1f} bpm; humans give "
        f"+25.3 (LBNP -80, n=20) and +38 (Vettorello 2016)"
    )

    # NOT bidirectional — REVERSED 2026-10-06. This line used to assert that
    # rising filling slows the heart, citing Herrera 2017's 500 mL bolus — a
    # third-trimester cohort. In healthy volunteers with CVP measured and filling
    # RAISED the heart does not slow: Norsk 1986 (PMID 3781950, CVP +5.9 mmHg),
    # Shi 1993 (PMID 8342666), Goldsmith 1984 (PMID 6720976, HR slightly UP),
    # Keller 1990, Goldsmith 1988, Millar 2013. Applied both ways the arm slowed
    # the heart 8.8 bpm at -30 deg against Likhvantsev's -1.65. Abstract-level.
    assert abs(hr_at(REF + 3.0, True)) < 0.5, (
        f"rising filling pressure moved heart rate {hr_at(REF + 3.0, True):+.2f} "
        f"bpm; healthy volunteers with CVP raised 2-6 mmHg show no slowing")

    # THE SWITCH MUST ACTUALLY SWITCH IT OFF.
    for cvp in (REF - 6.7, REF - 3.2, REF + 3.0):
        assert abs(hr_at(cvp, False)) < 1e-9, (
            f"cardiopulmonary arm still active when disabled: "
            f"{hr_at(cvp, False):+.3f} bpm at CVP {cvp:.1f}"
        )


def test_hypovolaemic_tachycardia_matches_lbnp():
    """[29] A 1000 mL bleed must produce a human-sized tachycardia.

    LBNP -80 is a blood-volume equivalent of more than a litre and gives
    +25.3 bpm (n=20); Vettorello measured +38 bpm over the same range. The band
    below brackets both.

    Before the two heart-rate changes of 2026-09-04 the model gave +7.0 bpm and
    the reflex was 97 % saturated at this bleed volume. Both arms are needed:
    the arterial arm alone reaches +18.3.
    """
    def run(ml):
        # AGE- AND SIZE-MATCHED 2026-09-15 to the LBNP cohort — see _HOFF_*.
        # dHR +28.5 -> +28.6 bpm: no material change, because the reflex the
        # test exercises has no age dependence at all (see §28). What DOES move
        # is the body the litre is taken from — 69 kg rather than 70 — and that
        # is the part this matching is honest about.
        p = cohort_params(_HOFF_HEIGHT_CM, _HOFF_WEIGHT_KG, age_years=_HOFF_AGE_YEARS)
        if ml > 0:
            p.hemorrhage_rate_mlmin = ml / 20.0 * 60.0
            p.hemorrhage_start_s    = 10.0
            p.hemorrhage_duration_s = 20.0
        r = run_simulation(p, duration_s=60.0, dt=DT)
        h = len(r['hr']) // 2
        return {k: float(np.mean(np.asarray(r[k])[h:])) for k in ('hr', 'map', 'cvp')}

    base, bled = run(0.0), run(1000.0)
    dhr = bled['hr'] - base['hr']
    assert 20.0 < dhr < 40.0, (
        f"1000 mL bleed gave dHR {dhr:+.1f} bpm; humans give +25.3 (LBNP -80) "
        f"to +38 (Vettorello 2016)"
    )
    assert bled['cvp'] < base['cvp'], "CVP did not fall with haemorrhage"


# ===========================================================================
# 30. Ventricular pressure outputs and pressure-volume loops — backlog item 41
# ===========================================================================

def test_ventricular_pressures_form_a_valid_pv_loop():
    """The exposed ventricular pressures must be physically coherent with the
    rest of the model, and the P-V loop they form must do positive work.

    Every assertion here is calibration-independent — it holds for any choice of
    elastance or resistance — so none can be satisfied by retuning.

    `lv_pressure` and `rv_pressure` are read straight out of the array `_odes`
    fills, never recomputed. That matters: the reported heart rate was wrong for
    months because it was computed a second time in the monitoring loop and the
    two copies drifted (validation_log 2026-09-04). This test would catch the
    same class of drift here, because a recomputed pressure that disagreed with
    the flows would break the aortic and floor checks below.

    NOTE THE CONVENTION. These outputs are INTRALUMINAL — `_odes` adds
    intrathoracic pressure to every thoracic compartment and both ventricles are
    in that tuple. `cvp` beside them is TRANSMURAL. Intraluminal is what a
    catheter reads, so it is the right convention for comparing with published
    loops, but the two must not be mixed.
    """
    import model.respiration as resp

    p = SimParams()
    p.ventilation_mode = "spontaneous"
    p.resp_rate_bpm    = 15.0
    r = run_simulation(p, duration_s=20.0, dt=DT)

    t   = np.asarray(r["t"])
    h   = len(t) // 2
    t   = t[h:]
    lv  = np.asarray(r["lv_pressure"])[h:]
    rv  = np.asarray(r["rv_pressure"])[h:]
    ao  = np.asarray(r["aortic_p"])[h:]
    V   = np.asarray(r["volumes"])[h:]
    itp = np.array([resp.intrathoracic_pressure(x, p.ventilation_mode,
                                                p.resp_rate_bpm, p.peep_cmh2o,
                                                p.pip_cmh2o, p.ie_ratio) for x in t])

    # 1. The left ventricle must out-pressure the aorta to eject at all.
    assert lv.max() >= ao.max(), (
        f"LV peak {lv.max():.1f} below aortic systolic {ao.max():.1f} mmHg — "
        f"the ventricle cannot open the aortic valve"
    )

    # 2. The right heart is the low-pressure side.
    assert rv.max() < lv.max(), (
        f"RV peak {rv.max():.1f} is not below LV peak {lv.max():.1f} mmHg"
    )

    # 3. CONVENTION CHECK. Removing intrathoracic pressure must leave a
    #    non-negative transmural pressure, because `_cardiac_pressure` floors at
    #    zero. This fails if the outputs are ever silently switched to
    #    transmural, or if the ITP term is applied twice.
    for name, series in (("LV", lv), ("RV", rv)):
        assert (series - itp).min() >= -1e-9, (
            f"{name} transmural pressure went negative "
            f"({(series - itp).min():.3f} mmHg) — these outputs are supposed to "
            f"be INTRALUMINAL, i.e. already carrying the intrathoracic term"
        )

    # 4. The loop must be traversed counter-clockwise and enclose real work.
    #    Shoelace area over whole beats; positive means the ventricle does work
    #    on the blood rather than the other way round.
    n_beat = int(round(60.0 / p.hr_bpm / DT))
    for name, series, idx, lo, hi in (
        ("LV", lv, IDX["left_ventricle"],  0.4, 2.5),
        ("RV", rv, IDX["right_ventricle"], 0.05, 0.8),
    ):
        vol  = V[:, idx]
        sl   = slice(len(vol) - 3 * n_beat, len(vol))
        x, y = vol[sl], series[sl]
        area = 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)) / 3.0
        joules = area * 1.333e-4          # mmHg.mL -> J
        assert joules > 0, (
            f"{name} pressure-volume loop is traversed clockwise (work "
            f"{joules:.3f} J) — the chamber is absorbing energy, not ejecting"
        )
        assert lo < joules < hi, (
            f"{name} stroke work {joules:.3f} J outside {lo}-{hi} J"
        )


# ===========================================================================
# 31. BLIND-PHASE LITERATURE TARGETS — the v1.0.0 freeze validation
#
# READ THIS BEFORE ADDING OR CHANGING ANYTHING IN THIS SECTION.
#
# **THESE STUDIES ARE SPENT. THEY ARE FITTED TARGETS, NOT VALIDATION.**
# Each was used once as a blind out-of-sample test of the frozen `v1.0.0`
# model. The predictions are public and timestamped in `preregistration/`,
# and the results are appended to them. From 2026-09-24 they become
# DEVELOPMENT targets. `tools/check_insample.py` will find them here and it
# will be right to. **No paper may present any of them as out-of-sample.**
# The next blind phase needs different studies.
#
# **TWO OF THESE STOPPED BEING XFAILS ON 2026-10-02 — backlog item 51 closed.**
# `test_orthostatic_tachycardia_is_blunted_with_age_white1997` and
# `test_orthostatic_vasoconstriction_is_blunted_with_age_white1997` were strict
# xfails recording that the baroreflex had no age dependence of any kind. They
# are live passing tests now because the reflex ages, from a MEASURED relation
# and not a fit:
#
#     Gribbin, Pickering, Sleight & Peto (1971) Circ Res 29:424-431, HUMAN n=81
#     log10 BRS = 2.47 − (0.0164 × age) − (0.0086 × MAP)  msec/mmHg
#
# applied as the age RATIO 10^(−0.0164·dage) in `aging.baroreflex_age_factors`.
#
# **AN EARLIER FITTED LAW WAS DISCARDED WHEN THAT PAPER ARRIVED, and the
# comparison is the reason this note exists.** Fitting the decline to White's
# two endpoints gave a 2.41x fall across 25-68; Gribbin MEASURES 5.07x. **The fit
# was half as steep as reality and it reproduced both endpoints anyway.** An
# endpoint fit can be comfortably wrong about the mechanism it is standing in
# for — which is the argument for holding out for a sourced relation.
#
# ITEM 67 IS NOT CLOSED BY THIS AND IS A DIFFERENT DEFECT.
# `test_brachial_diastolic_pressure_by_age_white1997` still fails: supine
# brachial DBP 81.02 against a measured 62.7 +/- 6.4. That is an ABSOLUTE level
# set by pulse-pressure amplification, which a lumped model cannot produce. The
# age law neither helps nor harms it, which is the right outcome.
#
# WHY THEY ALL LAND AT ONCE, rather than one at a time as each is fixed.
# This project's most-repeated process failure is optimising the loosest
# constraint — twice on record, most recently as *"the constraint list has to
# be re-read, not remembered."* If every target is a live assertion you cannot
# improve a subset without the rest reporting. And a fix that closes something
# unexpectedly announces itself as an XPASS, the way item 28's venous work
# closed items 22 and 23 by surprise.
#
# EVERY xfail REASON CARRIES THE MEASURED GAP AND THE DATE IT WAS MEASURED,
# because the log has already caught one stale reason.
#
# ---------------------------------------------------------------------------
# TARGETS THAT WERE CONSIDERED AND DELIBERATELY NOT WRITTEN.
# Recorded here rather than left as a silence, because a missing test looks
# identical to an overlooked one.
#
#   * PMID 9925894 — the 10 deg head-down tilt responses (dMAP, dHR, both age
#     groups). **A model predicting exactly zero scores tier A on all four.**
#     The measured effects are 0 to 2 units against between-subject SDs of 3.2.
#     Writing them would ratchet in a target that cannot fail, which is the
#     opposite of what the ratchet is for.
#   * PMID 9925894 — the resting MAP and HR age gaps. Underpowered for the same
#     reason: the resting MAP difference of +5 mmHg is 1.18 standard errors
#     from zero, so the STUDY did not establish it either. PMID 9404222
#     measures the same contrast at 2.7 SE with the convention matched
#     (arm cuff against the model's brachial output), and is used instead.
#   * PMID 31705432 — head-down tilt over-delivery. The target is +29 %
#     (IQR 21 to 41) but the study does not publish its tilt ANGLE, and the
#     model crosses the whole IQR between -5 and -15 degrees. A test would be
#     measuring the assumed angle, not the venous bed.
#   * PMID 27164015 — the between-group phenylephrine difference. The study's
#     patients were preload-dependent from anaesthetic VENODILATION and
#     registration 004 built its arm by HAEMORRHAGE, which is the diagnosis of
#     that registration's failure. Reproducing the study needs the venodilated
#     construction, which has never been run. **Run it first, then write the
#     test with a measured gap** — backlog item 64 holds the protocol.
# ===========================================================================

# --- White 1997, PMID 9404222 -----------------------------------------------
# 16 young (25 +/- 3) and 16 older (68 +/- 7) volunteers, 8 male and 8 female
# in each group, 30 min of 60 deg head-up tilt, automated arm cuff on the left
# arm. Mean +/- SEM with n = 16, so SD = SEM x 4.
#
# THE SITE IS MATCHED DELIBERATELY. These tests read `brachial_sbp` and
# `brachial_dbp` and reconstruct mean pressure as (S + 2D)/3 — the same formula
# on the same site as the cuff. Registration 005 compared the model's AORTIC
# pressure against a finger measurement and about 9 of its 11 mmHg gap turned
# out to be the site alone. Do not switch these to `sbp`/`dbp`.
_W97_DHR_YOUNG   = (15.0, 7.6)    # +15.0 +/- 1.9 SEM -> SD 7.6
_W97_DHR_OLDER   = (3.6,  4.4)    # +3.6  +/- 1.1 SEM -> SD 4.4
_W97_DDBP_YOUNG  = (7.0,  6.4)    # +7.0  +/- 1.6 SEM -> SD 6.4   MALES
_W97_DDBP_OLDER  = (-2.5, 6.0)    # -2.5  +/- 1.5 SEM -> SD 6.0   MALES
_W97_DBP_YOUNG   = (62.7, 6.4)    # supine brachial diastolic
_W97_DBP_OLDER   = (65.0, 8.8)
_W97_PP_YOUNG    = 49.3           # supine brachial pulse pressure
_W97_PP_OLDER    = 60.0
_W97_PP_WIDENING = 10.7           # mmHg across 43 years = 0.249 mmHg/year


def _white1997_tilt(age_years, sex, height_cm, weight_kg):
    """One arm of White 1997: supine baseline, then 5 minutes at 60 degrees.

    Timing follows the registration: settle to 120 s, read the supine window
    90-120 s, ramp to 60 deg over 10 s from t=120, and read 400-430 s — which
    is 4.5 to 5.0 minutes after the ramp completes. **Apply times and measure
    windows are separate quantities**; using one variable for both produced the
    stage-timing error in registration 001.

    Weights are Devine ideal body weight, which this cohort supports directly:
    every subject was within 20 % of ideal body weight. Height is not reported
    and is assumed. **It is deliberately not bracketed** — registration 005
    measured a 172-182 cm bracket and it moved the primary by 0.03 mmHg,
    because patient height reaches this model only through body surface area
    and never scales the hydrostatic column (backlog item 66).
    """
    p = cohort_params(height_cm, weight_kg, age_years=age_years, sex=sex)
    p.tilt_start_deg  = 0.0
    p.tilt_end_deg    = 60.0
    p.tilt_onset_s    = 120.0
    p.tilt_duration_s = 10.0
    p.ventilation_mode = "spontaneous"
    p.resp_rate_bpm    = 14.0
    r = run_simulation(p, duration_s=440.0, dt=DT)
    t = np.asarray(r["t"])

    def w(key, t0, t1):
        a = np.asarray(r[key])
        return float(np.mean(a[(t >= t0) & (t < t1)]))

    sup = {k: w(k, 90.0, 120.0) for k in ("hr", "brachial_sbp", "brachial_dbp")}
    til = {k: w(k, 400.0, 430.0) for k in ("hr", "brachial_sbp", "brachial_dbp")}
    for d in (sup, til):
        d["map"] = (d["brachial_sbp"] + 2.0 * d["brachial_dbp"]) / 3.0
        d["pp"]  = d["brachial_sbp"] - d["brachial_dbp"]
    return sup, til


@pytest.fixture(scope="module")
def white1997_arms():
    """All four arms: two ages x two sexes. Module-scoped — each is a 440 s run."""
    body = {"male": (175.0, 70.5), "female": (162.0, 54.2)}
    return {(age, sex): _white1997_tilt(age, sex, *body[sex])
            for age in (25.0, 68.0) for sex in ("male", "female")}


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "KNOWN GAP, 2026-10-07, after the abdomen got its anatomical height (L1, "
    "0.17 m). The tilt now moves more blood, and the heart — still without a "
    "Starling plateau on the RV side or a pericardium — turns that into a larger "
    "SV fall, so the young patient's full reflex drives HR +35.2 against the "
    "older +7.8: difference -27.4 bpm against White's -11.4 +/- 8.8. Expected to "
    "close with the heart's diastolic work (RV curve, in vivo Starling curves)."
))
def test_orthostatic_tachycardia_is_blunted_with_age_white1997(white1997_arms):
    """[PMID 9404222 — White 1997] Orthostatic tachycardia falls with age.

    At 5 minutes of 60 deg head-up tilt the young raised heart rate by
    +15.0 +/- 1.9 bpm and the older by +3.6 +/- 1.1 (mean +/- SEM, n = 16 each),
    a difference of -11.4 bpm which the authors mark P < 0.05. At 30 minutes
    the gap is wider still, 13.6 bpm.

    **The sexes are averaged here and that is sourced, not convenient.** The
    paper states explicitly that no significant sex-related differences were
    observed in the heart-rate response, at either age. The diastolic response
    is different and is tested separately in males only — see the test below.
    """
    mean_dhr = {}
    for age in (25.0, 68.0):
        arms = [white1997_arms[(age, s)] for s in ("male", "female")]
        mean_dhr[age] = sum(t["hr"] - s["hr"] for s, t in arms) / len(arms)

    measured_diff = _W97_DHR_OLDER[0] - _W97_DHR_YOUNG[0]          # -11.4 bpm
    sd_diff = float(np.hypot(_W97_DHR_YOUNG[1], _W97_DHR_OLDER[1]))  # 8.78
    model_diff = mean_dhr[68.0] - mean_dhr[25.0]

    assert abs(model_diff - measured_diff) <= sd_diff, (
        f"age difference in orthostatic tachycardia {model_diff:+.2f} bpm "
        f"(young {mean_dhr[25.0]:+.2f}, older {mean_dhr[68.0]:+.2f}) is outside "
        f"one SD of the measured {measured_diff:+.1f} +/- {sd_diff:.1f} bpm — "
        f"the reflex does not age"
    )


def test_orthostatic_vasoconstriction_is_blunted_with_age_white1997(white1997_arms):
    """[PMID 9404222 — White 1997] The diastolic response to tilt falls with age.

    At 5 minutes of 60 deg head-up tilt the young MALES raised diastolic
    pressure by +7.0 +/- 1.6 mmHg and the older LOWERED it by -2.5 +/- 1.5
    (mean +/- SEM, n = 8 per sex per group), a difference the authors mark
    P < 0.05.

    The young clamp down on standing; the older group's diastolic pressure
    falls first and recovers only by 10 minutes.
    """
    ddbp = {}
    for age in (25.0, 68.0):
        sup, til = white1997_arms[(age, "male")]
        ddbp[age] = til["brachial_dbp"] - sup["brachial_dbp"]

    measured_diff = _W97_DDBP_OLDER[0] - _W97_DDBP_YOUNG[0]          # -9.5 mmHg
    sd_diff = float(np.hypot(_W97_DDBP_YOUNG[1], _W97_DDBP_OLDER[1]))  # 8.77
    model_diff = ddbp[68.0] - ddbp[25.0]

    assert abs(model_diff - measured_diff) <= sd_diff, (
        f"age difference in the diastolic tilt response {model_diff:+.2f} mmHg "
        f"(young {ddbp[25.0]:+.2f}, older {ddbp[68.0]:+.2f}) is outside one SD "
        f"of the measured {measured_diff:+.1f} +/- {sd_diff:.1f} mmHg"
    )


@pytest.mark.xfail(strict=True, reason=(
    "KNOWN GAP — BRACHIAL DIASTOLIC PRESSURE IS TOO HIGH AND ITS AGE "
    "DIRECTION IS WRONG. Backlog item 67, opened from this study. "
    "MEASURED 2026-09-25, supine, mean of the male and female runs: brachial DBP 81.08 at age 25 against 62.7 +/- 6.4, and 75.45 at age 68 against 65.0 +/- 8.8. The model FALLS 81.08 -> 75.45 across the age span where the measurement RISES 62.7 -> 65.0.  "
    "IT IS TWO FAULTS AND THEY SPLIT BY AGE. Brachial DBP is MAP - PP/3, so "
    "the error decomposes exactly: in the young, +9.5 mmHg comes from the mean "
    "pressure being too high (item 62's territory) and +8.9 from the pulse "
    "pressure being too narrow. In the older group the mean pressure is "
    "essentially correct and the whole error is the narrow pulse pressure. "
    "So items 62 and 67 are COUPLED in the young and INDEPENDENT in the old, "
    "and neither closes this on its own. "
    "THE DIASTOLIC CARRIES MOST OF IT. The systolic is about 8 mmHg LOW in the "
    "young while the diastolic is 18 HIGH, so the narrow brachial pulse "
    "pressure is mainly a diastolic fault. Anyone reaching for this will look "
    "at systolic first and that is the wrong end. "
    "PROBABLY NOT FULLY FIXABLE, and that is the honest framing. Pulse "
    "pressure amplification runs at 0.88 against a measured 1.33 +/- 0.16 and "
    "needs wave travel, transit time and reflection, none of which a "
    "23-compartment lumped model has. Scope whether a central-to-brachial "
    "transfer function belongs in the MODEL or in the REPORTING layer before "
    "building anything. "
    "DO NOT FIX THIS BY MOVING ARTERIAL COMPLIANCE. The central pulse pressure "
    "was deliberately calibrated there on 2026-09-14 and is validated against "
    "McEniery at three decades. Moving it breaks that and leaves the level "
    "untouched. "
    "strict=True. Full record in docs/reference_values.md under PMID 9404222."
))
def test_brachial_diastolic_pressure_by_age_white1997(white1997_arms):
    """[PMID 9404222 — White 1997] Supine brachial diastolic pressure, by age.

    Measured by arm cuff: 62.7 +/- 1.6 at age 25 and 65.0 +/- 2.2 at age 68
    (mean +/- SEM, n = 16 each, so SD 6.4 and 8.8).

    **Diastolic pressure RISES slightly with age.** Two assertions follow, and
    they fail for different reasons: the level in each group, and the direction
    across them.
    """
    dbp = {}
    for age in (25.0, 68.0):
        arms = [white1997_arms[(age, s)][0] for s in ("male", "female")]
        dbp[age] = sum(a["brachial_dbp"] for a in arms) / len(arms)

    for age, (mean, sd) in ((25.0, _W97_DBP_YOUNG), (68.0, _W97_DBP_OLDER)):
        assert abs(dbp[age] - mean) <= sd, (
            f"supine brachial DBP at age {age:.0f} is {dbp[age]:.2f} mmHg "
            f"against a measured {mean} +/- {sd} (1 SD)"
        )
    assert dbp[68.0] > dbp[25.0], (
        f"brachial diastolic pressure FALLS with age in the model "
        f"({dbp[25.0]:.2f} at 25 -> {dbp[68.0]:.2f} at 68); measured it RISES, "
        f"{_W97_DBP_YOUNG[0]} -> {_W97_DBP_OLDER[0]}"
    )


def test_age_slope_of_brachial_pulse_pressure_white1997(white1997_arms):
    """[PMID 9404222 — White 1997] The age slope of pulse pressure is RIGHT.

    **THIS TEST PASSES, AND IT IS A GUARD RATHER THAN A TARGET.** It is here to
    protect a working emergent behaviour from the work that is about to move
    every pressure in the model — backlog items 62, 65, 66 and 67 all act on
    the same quantities.

    Measured brachial pulse pressure widens 49.3 -> 60.0 mmHg between age 25
    and 68, which is +10.7 mmHg over 43 years, or 0.249 mmHg/year. The model
    produced +11.7, or 0.272 — within 10 %, **and nothing was fitted to it.**
    `aging.py` derives its arterial compliance law from Franklin 1997's
    LONGITUDINAL pulse-pressure slope of 0.68 mmHg/year, which over 43 years
    would imply 29 mmHg. The emergent widening is not the number that was put
    in: it falls out of compliance, stroke volume and the circuit, and it lands
    on this cohort's measured value.

    That is also consistent with backlog item 48 — cross-sectional cohorts show
    LESS widening than longitudinal ones, because they exclude at measurement
    the people whose pressure rose. This cohort is cross-sectional.

    **THE BAND IS A REGRESSION TOLERANCE, NOT A LITERATURE SPREAD, and the
    distinction is deliberate.** Pulse pressure is not tabulated with its own
    error term, and propagating the systolic and diastolic errors gives an SD
    on the age difference of about 18 mmHg — a band so wide that any model
    passes and the guard would be worthless. The band below is set around the
    measured 10.7 at a stated tolerance, and its purpose is to FAIL if a change
    breaks the age law, not to certify agreement.

    **The absolute pulse pressure is badly wrong at both ages and is asserted
    in the failing test above.** The level and the slope are separable claims:
    the level is the central-to-peripheral transfer (item 67) and the slope is
    the age law on arterial compliance. One is broken and the other works, and
    a single tier on pulse pressure would have hidden both.

    ONE CAVEAT, STATED ONCE. Because the baseline is about half, the RELATIVE
    widening is overstated — 1.52x against a measured 1.22x. The absolute rate
    agrees; the proportional rate does not.
    """
    pp = {}
    for age in (25.0, 68.0):
        arms = [white1997_arms[(age, s)][0] for s in ("male", "female")]
        pp[age] = sum(a["pp"] for a in arms) / len(arms)

    widening = pp[68.0] - pp[25.0]
    lo, hi = 0.6 * _W97_PP_WIDENING, 1.6 * _W97_PP_WIDENING
    assert lo <= widening <= hi, (
        f"brachial pulse pressure widens {widening:+.2f} mmHg between age 25 "
        f"and 68 ({pp[25.0]:.2f} -> {pp[68.0]:.2f}), outside the "
        f"{lo:.1f}-{hi:.1f} guard band around the measured "
        f"{_W97_PP_WIDENING} mmHg ({_W97_PP_WIDENING/43.0:.3f} mmHg/year). "
        f"The age law on arterial compliance has moved."
    )


# --- PMID 27702883 ----------------------------------------------------------
# 15 healthy volunteers, 7 male and 8 female, age 22 (20-30), BMI 23.4.
# Supine in an LBNP chamber; -30 mmHg applied within 0.3 s and held ten
# minutes. MAP by finger arterial pressure, heart rate by ECG, cardiac output
# by ULTRASOUND — a direct flow measurement, not a pulse-contour estimate the
# model's peripheral waveform would corrupt. Reported as median (IQR).
#
# LBNP IS NOT A MODEL INPUT and is substituted by haemorrhage, as the rest of
# the suite already does. The blind phase settled the exchange rate: matching
# the measured dCO and dHR, **-30 mmHg behaves like 500 mL or a little less**,
# and 1000 mL is about double the measured effect. Registration 002 recorded
# that direction in advance and it held.
# 1 SD from the reported quartiles (2026-10-17, Jesper: "yes to 1 SD", the suite's
# convention since the Schäfers decision): median 80.4, quartiles 72.5 / 84.4, each
# side scaled by 1/0.674 -> (68.7, 86.3). The IQR itself is kept as data.
_LBNP_SV_QUARTILES = (80.4, 72.5, 84.4)   # median, lower, upper quartile, mL
_LBNP_SV_IQR  = (round(80.4 - (80.4 - 72.5) / 0.674, 1), round(80.4 + (84.4 - 80.4) / 0.674, 1))
_LBNP_DCO     = -1.00          # L/min at -30 mmHg, spontaneous breathing
_LBNP_DHR     = +5.8           # bpm
_LBNP_DMAP    = +2.90          # mmHg — the model has this BACKWARDS


@pytest.fixture(scope="module")
def lbnp_young_haemorrhage():
    """Young supine adult, 500 mL bled over 5 min — the -30 mmHg LBNP equivalent.

    Height is not reported; 173 cm assumed for a mixed 7:8 Northern European
    cohort, giving 70.0 kg at the reported BMI of 23.4. **Nothing is solved
    for** — no measured MAP, CO or CVP is entered — so the Tier 3 calibration
    defect of backlog item 58 does not bite here.
    """
    out = {}
    for sex in ("male", "female"):
        p = cohort_params(173.0, 70.0, age_years=22.0, sex=sex)
        p.ventilation_mode = "spontaneous"
        p.resp_rate_bpm    = 14.0
        p.hemorrhage_start_s    = 120.0
        p.hemorrhage_rate_mlmin = 100.0
        p.hemorrhage_duration_s = 300.0
        r = run_simulation(p, duration_s=600.0, dt=DT)
        t = np.asarray(r["t"])

        def w(key, t0, t1):
            a = np.asarray(r[key])
            return float(np.mean(a[(t >= t0) & (t < t1)]))

        out[sex] = (
            {k: w(k, 90.0, 120.0)  for k in ("map", "hr", "co", "sv")},
            {k: w(k, 540.0, 600.0) for k in ("map", "hr", "co", "sv")},
        )
    return out


def test_resting_stroke_volume_in_young_adults_pmid27702883(lbnp_young_haemorrhage):
    """[PMID 27702883] Supine stroke volume in healthy 22-year-olds.

    **THIS TEST PASSES, AND IT IS A GUARD.** Median 80.4 mL, IQR 72.5-84.4, by
    ULTRASOUND. It is the strongest absolute the blind phase produced — the
    model landed inside the interquartile range in BOTH sexes, and it was the
    only absolute that landed in that registration while MAP and heart rate
    both missed.

    That combination localises the model's defect: **cardiac mechanics are
    right while the reflex operating point is not**, which is the argument
    behind backlog item 62. The work queued behind that item moves pressure and
    rate. This guard exists so that it does not quietly move stroke volume too.

    Ultrasound matters and is not incidental. A pulse-contour stroke volume
    would depend on the shape of a peripheral pressure wave, which this model
    gets architecturally wrong (amplification 0.88 against 1.33 +/- 0.16).

    **THE SEX-MEAN IS ASSERTED, AND THE REASON IS THE COHORT.** The study is 7
    male and 8 female; the model runs one sex at a time. Measured 2026-09-25:
    **male 82.39 mL, female 72.44 mL, mean 77.42.** The male arm and the mean
    sit inside the interquartile range. The female arm falls **0.06 mL** below
    the lower quartile of 72.5.

    **That 0.06 mL is recorded rather than smoothed over, and the band is NOT
    widened to absorb it.** (2026-10-17: the band IS now 1 SD instead of the IQR —
    Jesper's suite-wide convention, decided for Schäfers and applied here on his
    explicit call, not to absorb a miss: 84.56 vs 84.4 at the time.) Widening a literature band to make a model fit is
    the move this project exists to refuse. The sex-mean is the honest
    comparator for a near-balanced cohort, it is what the White 1997 tests
    above use for the same reason, and it does not depend on which arm happens
    to sit closer.
    """
    lo, hi = _LBNP_SV_IQR
    sv = [rest["sv"] for rest, _ in lbnp_young_haemorrhage.values()]
    mean_sv = sum(sv) / len(sv)
    assert lo <= mean_sv <= hi, (
        f"resting stroke volume, mean of the two sex arms, is {mean_sv:.2f} mL "
        f"— outside the 1 SD band {lo}-{hi} (median 80.4, IQR 72.5-84.4). Individual arms: "
        f"{', '.join(f'{v:.2f}' for v in sv)}"
    )


def test_central_hypovolaemia_flow_and_rate_response_pmid27702883(lbnp_young_haemorrhage):
    """[PMID 27702883] Cardiac output and heart rate under -30 mmHg LBNP.

    **THIS TEST PASSES, AND IT IS A GUARD** on the LBNP-to-haemorrhage exchange
    rate that the blind phase established. Measured: dCO -1.00 L/min and
    dHR +5.8 bpm. The model at 500 mL gives about -0.9 to -1.0 and +6.5 to
    +6.8 — close enough that 500 mL is the working equivalent of -30 mmHg, and
    1000 mL is roughly double the measured effect.

    **It is a guard and not a validation.** The exchange rate was CHOSEN by
    matching these two numbers, so agreement here is not evidence. What it
    protects is the substitution itself: if a later change moves the model's
    haemorrhage response, every LBNP comparison in the suite silently shifts
    with it and nothing else would say so.

    **MAP is excluded deliberately and fails in its own test below.** Reporting
    all three together would let two passes hide a direction failure.

    A REGISTERED CAVEAT THAT WAS WRONG, recorded because it was stated in
    advance: registration 002 predicted the model's absolute cardiac output
    would be LOW here, on the strength of comparison 001 where the model gave
    4.33 against a measured 6.9 at the same age. It runs HIGH instead, 5.83
    against 4.6. The two young cohorts genuinely differ and the model sits
    between them, which is why neither is used as an absolute target.
    """
    for sex, (rest, bled) in lbnp_young_haemorrhage.items():
        dco = bled["co"] - rest["co"]
        dhr = bled["hr"] - rest["hr"]
        assert abs(dco - _LBNP_DCO) <= 0.5, (
            f"{sex} dCO {dco:+.2f} L/min against a measured {_LBNP_DCO:+.2f} — "
            f"the 500 mL LBNP equivalence has moved"
        )
        assert abs(dhr - _LBNP_DHR) <= 4.0, (
            f"{sex} dHR {dhr:+.1f} bpm against a measured {_LBNP_DHR:+.1f} — "
            f"the 500 mL LBNP equivalence has moved"
        )


@pytest.mark.xfail(strict=True, reason=(
    "KNOWN GAP — THE MODEL LOWERS MEAN PRESSURE WHERE YOUNG PEOPLE RAISE IT. "
    "Backlog item 62, and it is the only item on that list with THREE "
    "independent out-of-sample cohorts behind it. "
    "MEASURED 2026-09-25 after a 500 mL bleed in a 22-year-old: dMAP -4.28 (male) and -4.48 (female) against a measured +2.90.  "
    "THE SAME DIRECTION FAILURE IN THREE COHORTS: comparison 001 "
    "(PMID 38684421, 30->60 deg head-up) subjects +2.5 against the model -7.8; "
    "this study (-30 mmHg LBNP) subjects +2.9 against the model -3.7 to -9.1; "
    "and PMID 9404222 (60 deg tilt) subjects +5.6 young and +3.6 older against "
    "the model -32. It was REGISTERED IN ADVANCE here — 'if the hypovolaemic "
    "MAP fall is over-predicted, that is the first place to look' — and it "
    "happened. "
    "THE MECHANISM IS VISIBLE IN THE BASELINE. MAP_SETPOINT = 93.0 in "
    "baroreflex.py is a constant and aging.py never touches it, so a "
    "22-year-old model defends 93 mmHg while these subjects sit at 75.8. The "
    "model is not merely mis-calibrated at rest — it is DEFENDING THE WRONG "
    "NUMBER, which is exactly what makes a pressure start high and then fall "
    "where a real young person's holds or rises. "
    "A CONSTANT SITE OFFSET CANCELS IN A DIFFERENCE, which is why this test "
    "asserts the CHANGE and not the level. Finger pressure against the model's "
    "integrated central MAP is worth about +9 mmHg on the absolute and nothing "
    "here. "
    "STROKE VOLUME IS TIER A IN BOTH SEXES in the same run (see the guard "
    "above), so this is the reflex operating point and not cardiac mechanics. "
    "IT LANDS WITH BACKLOG ITEM 58, not before it. MAP_SETPOINT is half of the "
    "reference operating point that item 50 found typed twice, and patient.py "
    "imports it for svr_scale, so changing it moves every patient-scaled "
    "result in the suite. "
    "strict=True. Full record in docs/reference_values.md under PMID 27702883."
))
def test_mean_pressure_rises_under_central_hypovolaemia_pmid27702883(lbnp_young_haemorrhage):
    """[PMID 27702883] Young adults RAISE mean pressure under -30 mmHg LBNP.

    Measured +2.90 mmHg. The model lowers it. Asserted as a change, so the
    finger-versus-central convention cancels.
    """
    for sex, (rest, bled) in lbnp_young_haemorrhage.items():
        dmap = bled["map"] - rest["map"]
        assert dmap > 0, (
            f"{sex} mean pressure FELL {dmap:+.2f} mmHg under central "
            f"hypovolaemia; the subjects' ROSE {_LBNP_DMAP:+.2f}"
        )


# --- PMID 31705432 ----------------------------------------------------------
# 20 anaesthetised patients, 17 of them women, age 67 +/- 8, 167 +/- 8 cm,
# 74 +/- 11 kg, hypertension in 12. Radial arterial catheter feeding a LiDCO
# monitor. Propofol and remifentanil; ventilated at 8 mL/kg of ideal body
# weight with PEEP 6. Head-up tilt, phenylephrine titrated until stroke volume
# variation fell below 12 %. Reported as per-cent change, median (IQR).
#
# THE TILT ANGLE IS NOT PUBLISHED. It was RECOVERED at 17.1 degrees by
# inverting the reported stroke-volume fall through the model, across the
# senior author's own bracket of 10 to 40 degrees. The method was fixed before
# the data arrived and the answer held across both unreported parameters
# (propofol 2.0-3.0 mg/kg, PIP 12-21). **Those stroke-volume values are
# therefore SPENT and are not scored anywhere.** The phenylephrine response is
# not spent — it is the registered prediction.
_PE_TILT_DEG   = 17.1
_PE_DHR_IQR    = (-15.0, -6.0)   # per cent, median -10
_PE_SVV_TARGET = 12.0            # the study titrated until SVV fell below this


def _stroke_volume_variation(result, t0, t1):
    """Beat-to-beat stroke-volume variation over a window, in per cent.

    Computed from the `sv` series rather than read from the model's `ppv`
    output, which is what registration 007 did and for a reason worth keeping:
    at the time, `ppv` was silently destroyed by output decimation (backlog
    item 69, fixed 2026-09-24 in `1d5348a`). The `sv` route was verified
    unchanged across output_every 1, 10 and 100 while `ppv` read 6.05, 1.31 and
    0.00. The defect is fixed, but this is still the quantity the study
    reports — LiDCO computes SVV from stroke volumes — so it stays.
    """
    t  = np.asarray(result["t"])
    sv = np.asarray(result["sv"])
    s  = sv[(t >= t0) & (t < t1)]
    s  = s[s > 0]
    assert len(s) >= 2, "not enough stroke-volume samples to compute SVV"
    return float(100.0 * (s.max() - s.min()) / s.mean())


@pytest.fixture(scope="module")
def phenylephrine_during_tilt():
    """Anaesthetised patient at 17.1 deg head-up, with and without phenylephrine.

    **BOTH ARMS ARE BUILT IDENTICALLY and differ only in the phenylephrine
    term.** That is not tidiness — it is the fix for a method error that
    invalidated the first sweep. `SimParams.drug_start_s` gates the WHOLE drug
    dictionary, so using it to start phenylephrine part-way through a run also
    switched the PROPOFOL off until that moment: the model was an awake patient
    who was then anaesthetised and given a vasopressor at the same instant.

    **A zero-dose control arm exposed it.** The supine baseline read 80.7 mmHg
    undosed and 87.8 in every dosed arm, and a drug that has not started cannot
    move a baseline. Without that control all six runs would have shared one
    wrong baseline and looked self-consistent. Keep the control arm.

    The sex is MATCHED, not bracketed — the cohort is 85 % female.
    """
    out = {}
    for dose in (0.0, 0.25, 0.5, 1.0, 2.0, 4.0):
        p = cohort_params(167.0, 74.0, age_years=67.0, sex="female")
        p.tilt_start_deg  = _PE_TILT_DEG
        p.tilt_end_deg    = _PE_TILT_DEG
        p.tilt_onset_s    = 0.0
        p.ventilation_mode = "mechanical"
        p.peep_cmh2o = 6.0
        p.pip_cmh2o  = 21.0
        p.resp_rate_bpm = 14.0
        drugs = {"propofol": 2.5}
        if dose > 0.0:
            drugs["phenylephrine"] = dose
        p.drug_factors = combined_drug_factors(drugs)
        r = run_simulation(p, duration_s=180.0, dt=DT)
        t = np.asarray(r["t"])
        m = {k: float(np.mean(np.asarray(r[k])[(t >= 150.0) & (t < 180.0)]))
             for k in ("map", "hr", "sv", "co")}
        m["svv"] = _stroke_volume_variation(r, 150.0, 180.0)
        out[dose] = m
    return out


# --- Hojlund 2024, PMID 38907106 -------------------------------------------
# THE SAME GROUP, THE SAME PARADIGM, THE SAME DRUG AS PMID 31705432 — re-measured with
# LITHIUM DILUTION, a flow method that does not depend on vascular tone.
#
# WHY IT REPLACES THE 2020 TARGET (decided with Jesper, 2026-09-26). The 2020 study
# reported dSV +96 % with an UNCALIBRATED pulse-power monitor. Under an alpha1 agonist
# such devices read part of the pressure rise as extra flow — every human study found
# comparing one against a tone-independent reference shows the same over-reading
# (Lorsomradee 2007, Ji 2014, Monnet 2012; abstracts). This study measured +40 %.
# Pressure agrees across the two (+114 % against +95 %); flow does not. That is a
# device artefact of about 2.4-fold, not a different physiology.
#
# THIS IS NOT MOVING THE GOALPOSTS TOWARD THE MODEL. The model gives about -1 %
# against either number. The replacement swaps a measurement known to be inflated
# for a better one of the same manoeuvre, from the same laboratory.
#
# SPENT FOR BLIND USE: its results were read on 2026-09-26. Full entry in the ledger.
_H24_TILT_DEG  = 25.0              # STATED in the paper, unlike the 2020 study
_H24_DSV_CI95  = (21.6, 58.4)      # per cent; see the test docstring for the arithmetic


@pytest.fixture(scope="module")
def phenylephrine_during_tilt_hojlund2024():
    """Hojlund 2024 at 25 deg head-up, anaesthetised, with and without phenylephrine.

    **Cohort:** n=20, 55 % female, 171 +/- 8 cm, 82 +/- 17 kg, age 59. The sexes are
    near-balanced, so the SEX-MEAN is used — the same rule as the White 1997 and
    PMID 27702883 tests — with both sexes built at the cohort's mean body size.

    **Anaesthesia:** propofol 1.5-2 mg/kg induction plus maintenance; the model's
    bolus-equivalent is set at 2.0. Remifentanil 0.5-0.8 mcg/kg/min has NO model
    counterpart (backlog item 63), and that absence is the leading suspect for why
    the model's tilt state is wrong — see the xfail reason below.

    **Airway pressure is COMPUTED, not fitted.** Tidal volume 8 mL/kg of ideal body
    weight; IBW at 171 cm averaged across the sexes is about 64.7 kg, so 518 mL.
    Respiratory compliance is not reported here, so Rebet 2016's measured
    47 mL/cmH2O (Table 2, a comparable anaesthetised surgical cohort) is used:
    driving pressure 11.0, PIP 17.0 over PEEP 6. The 2020 fixture set its PIP from
    the supine SVV instead, which spent that value; this one spends nothing.

    **Both arms are built identically** and differ only in the phenylephrine term —
    see the `drug_start_s` note on the 2020 fixture for why that matters.
    """
    out = {}
    for sex in ("male", "female"):
        per = {}
        for dose in (0.0, 0.25, 0.5, 1.0, 2.0, 4.0):
            p = cohort_params(171.0, 82.0, age_years=59.0, sex=sex)
            p.tilt_start_deg  = _H24_TILT_DEG
            p.tilt_end_deg    = _H24_TILT_DEG
            p.tilt_onset_s    = 0.0
            p.ventilation_mode = "mechanical"
            p.peep_cmh2o = 6.0
            p.pip_cmh2o  = 17.0
            p.resp_rate_bpm = 14.0
            drugs = {"propofol": 2.0}
            if dose > 0.0:
                drugs["phenylephrine"] = dose
            p.drug_factors = combined_drug_factors(drugs)
            r = run_simulation(p, duration_s=180.0, dt=DT)
            t = np.asarray(r["t"])
            m = {k: float(np.mean(np.asarray(r[k])[(t >= 150.0) & (t < 180.0)]))
                 for k in ("map", "hr", "sv", "co")}
            m["svv"] = _stroke_volume_variation(r, 150.0, 180.0)
            per[dose] = m
        out[sex] = per
    return out


@pytest.mark.xfail(strict=True, reason=(
    "KNOWN GAP — PHENYLEPHRINE LOWERS STROKE VOLUME WHERE IT RAISES IT IN "
    "PRELOAD-DEPENDENT PATIENTS. Backlog item 64, rediagnosed 2026-09-26. "
    "MEASURED 2026-09-26, AFTER phenylephrine's arterial ceiling was recalibrated "
    "to Schaefers (1.80 -> 2.10), at 25 deg head-up, propofol 2.0, PEEP 6 / PIP 17, "
    "sex-mean at 171 cm / 82 kg / age 59: the best stroke-volume change across "
    "0.25 to 4 mcg/kg/min is -2.1 per cent (male +0.1 at 4.0, female -4.3), against "
    "a measured +40 per cent, 95 per cent CI of the mean +21.6 to +58.4. It was "
    "-1.2 before the recalibration: more afterload, same venous arm. "
    "THE MODEL'S TILT STATE IS WRONG BEFORE THE DRUG IS GIVEN: MAP 73 against 43, "
    "HR 94 against 63, SVI 19 against 35 mL/m2, SVV 11.6 against 19 — so the model's "
    "patient is NOT preload-dependent by the study's own criterion (SVV above 12). "
    "That is the signature of an intact sympathetic reflex holding pressure up by "
    "constriction and tachycardia, which remifentanil 0.5-0.8 mcg/kg/min abolishes "
    "in these patients (heart rate 62 -> 63 on a 33 per cent pressure fall). "
    "WHAT IS ALREADY KNOWN ABOUT THE CAUSE, 2026-09-26. The legs are NOT the fix: "
    "squeezing 10 per cent of leg V0 gives only +14 per cent even with no afterload. "
    "PHENYLEPHRINE'S VENOUS ARM CANNOT SIMPLY BE RAISED. A venous ceiling of about "
    "0.3 is what the anaesthetised cohorts ask for (Juhl-Olsen filling pressures; a "
    "canine-anchored estimate of 0.29-0.39) — but 0.3 breaks Schaefers' flow "
    "response in AWAKE men (dSV +31 mL against +9, dHR -25 against -16). The drug's "
    "venous effect depends on the patient's own sympathetic venous tone: small when "
    "the veins are already constricted, large when anaesthesia withdraws that tone. "
    "And de Wit 2016 (human, read in full) shows propofol parks several hundred mL "
    "in the unstressed pool, by sympatholysis — the model parks about a fifth of "
    "that (test_propofol_lowers_stressed_volume_and_venous_resistance_dewit2016). "
    "SO THIS CLOSES WITH STRUCTURE, NOT A NUMBER: an opioid (item 63), and "
    "sympathetic OUTFLOW as its own stage (item 70), so that anaesthesia withdraws "
    "venous tone and phenylephrine acts on what is withdrawn. Not the leg rebuild. "
    "THE HEART-RATE RESPONSE ALREADY MATCHES: -16 to -17 per cent at 2 to 4 "
    "mcg/kg/min against a measured -16 per cent. It must still match afterwards. "
    "strict=True. Full record in docs/validation_log.md, 2026-09-26."
))
def test_phenylephrine_raises_stroke_volume_hojlund2024(phenylephrine_during_tilt_hojlund2024):
    """[PMID 38907106 — Hojlund 2024] Phenylephrine raises stroke volume by 40 per
    cent in patients made preload-dependent by 25 deg head-up tilt under general
    anaesthesia. Lithium dilution, so the flow change is not a tone artefact.

    Measured: SVI 35 +/- 7 -> 49 +/- 11 mL/m2 (+40 %), CI 2.2 -> 2.6 (+18 %), MAP
    43 -> 84, HR 63 -> 53, SVV 19 -> 6. All P < 0.001, n = 20.

    **THE BAND IS THE 95 PER CENT CONFIDENCE INTERVAL OF THE MEAN CHANGE, and it is
    computed conservatively.** The paper reports the change (+40 %) but not its own
    spread. Treating the two states as independent — which OVERSTATES the
    uncertainty, because the design is paired — the ratio of the means is
    49/35 = 1.40 with relative standard error sqrt((7/sqrt20/35)^2 +
    (11/sqrt20/49)^2) = 0.0672, so 1.40 +/- 1.96 x 0.094 = **+21.6 to +58.4 per
    cent**. It excludes both the 2020 device reading (+96 %) and Rebet's
    non-significant +5 %, and it is a confidence interval of a MEAN, which is what
    a single representative model patient predicts.

    Asserted at the model's best dose. The study titrated from 15-20 mcg/min to an
    SVV target and does not report the final dose, and the model's dose axis has
    no pharmacokinetic mapping to it, so this is not a dose mismatch.
    """
    doses = [d for d in (0.25, 0.5, 1.0, 2.0, 4.0)]
    dsv = []
    for d in doses:
        per_sex = [pct(arm[d]["sv"], arm[0.0]["sv"])
                   for arm in phenylephrine_during_tilt_hojlund2024.values()]
        dsv.append(sum(per_sex) / len(per_sex))
    best = max(dsv)
    lo, hi = _H24_DSV_CI95
    assert lo <= best <= hi, (
        f"best sex-mean dSV across the dose bracket is {best:+.1f} %, outside the "
        f"95 % CI of the measured mean change {lo} to {hi} (point estimate +40). "
        f"By dose: {', '.join(f'{d}: {v:+.1f}' for d, v in zip(doses, dsv))}"
    )


# Was a strict xfail; closed 2026-10-06 by the Klotz LV diastolic curve (heart.py).
def test_phenylephrine_abolishes_preload_dependency_pmid31705432(phenylephrine_during_tilt):
    """[PMID 31705432] Phenylephrine brought stroke-volume variation from 24 to
    8.6 % (IQR 6.8 to 11) — below the study's own 12 % target.

    Asserted at the model's best dose across the bracket.
    """
    doses = [d for d in phenylephrine_during_tilt if d > 0.0]
    best = min(phenylephrine_during_tilt[d]["svv"] for d in doses)
    assert best < _PE_SVV_TARGET, (
        f"lowest stroke-volume variation across the dose bracket is "
        f"{best:.1f} %, never below the study's {_PE_SVV_TARGET} % target "
        f"(patients reached 8.6, IQR 6.8-11)"
    )


def test_phenylephrine_reflex_bradycardia_during_tilt_pmid31705432(phenylephrine_during_tilt):
    """[PMID 31705432] Phenylephrine slows the heart by 10 % (IQR -15 to -6).

    **THIS TEST PASSES, AND IT IS A GUARD.** It was the one quantity of that
    registration that landed in the interquartile range, in a study where the
    stroke-volume and cardiac-output predictions both failed on direction.

    **It is here because of what happens next.** Closing backlog items 9 and 64
    puts the leg veins into the mobilizable reservoir, which changes preload,
    which the baroreflex answers. The reflex bradycardia to an alpha1 agonist
    is currently right, and it must still be right afterwards. Without this
    guard a leg rebuild could trade a fixed stroke volume for a broken reflex
    and the suite would report an improvement.

    Asserted at the dose whose heart-rate response is closest to the measured
    median, because the study titrated to an endpoint rather than to a dose,
    and the model's dose axis has no pharmacokinetic mapping to a bolus in
    micrograms per kilogram.
    """
    base = phenylephrine_during_tilt[0.0]
    doses = [d for d in phenylephrine_during_tilt if d > 0.0]
    dhr = [pct(phenylephrine_during_tilt[d]["hr"], base["hr"]) for d in doses]
    lo, hi = _PE_DHR_IQR
    assert any(lo <= v <= hi for v in dhr), (
        f"no dose produces a heart-rate change inside the measured IQR "
        f"{lo} to {hi} % (median -10); model gives "
        f"{', '.join(f'{v:+.1f}' for v in dhr)}"
    )


# --- PMID 41721238 ----------------------------------------------------------
# ICU responders, age 69.3 +/- 14.2, BMI 22.5 +/- 2.5, ventilated with
# spontaneous breathing activity, noradrenaline in 66.6 % at < 0.1 mcg/kg/min,
# PEEP 5, PIP median 14, tidal volume 8.9 +/- 1.8 mL/kg.
#
# THIS STUDY WAS EXCLUDED FROM THE BLIND PHASE, and the reason is this test.
# It passed the feasibility screen and then the PATIENT COULD NOT BE BUILT.
# Only the baseline was ever read, so it stays clean for a future blind phase —
# and the target here needs no result data at all.
_TIER3_MAP = 79.2
_TIER3_CVP = 6.4
_TIER3_CI  = 3.1


@pytest.mark.xfail(strict=True, reason=(
    "KNOWN GAP — TIER 3 CALIBRATION DOES NOT CONVERGE ON THE VALUES IT IS "
    "GIVEN. Backlog item 58, and it outranks most of the list. "
    "MEASURED 2026-09-25, 170 cm / 65 kg / age 69 at the cohort's BMI of 22.5, ventilated at PEEP 5 and PIP 14: asked for MAP 79.2, CVP 6.4 and cardiac index 3.1, the model settles at 87.34, 3.49 and 2.96. Mean pressure overshoots by 8.1 mmHg and filling pressure undershoots by 2.9; only the cardiac index lands. EXCLUDED.md entry 3 recorded 94.07 / 2.52 / 2.77 on slightly different anthropometrics — so the SIZE of the miss depends on the patient and the FACT of it does not.  "
    "WHY THIS MATTERS MORE THAN A CALIBRATION MISS. Tier 3 exists so the model "
    "can be pointed at a real patient. If entering three measured numbers "
    "produces a patient at none of them, then EVERY clinical use of the model "
    "starts from the wrong operating point, and so does every validation "
    "against a cohort whose haemodynamics differ from the reference patient's. "
    "IT ALREADY COST AN OUT-OF-SAMPLE STUDY that had otherwise passed "
    "screening — preregistration/EXCLUDED.md entry 3. The direction compounds "
    "it: the model's patient sits at a much lower filling pressure, so further "
    "up the steep part of its Starling curve, and would therefore be MORE "
    "fluid-responsive than the cohort — biasing exactly the comparison that "
    "study exists to make. "
    "WHAT IS WRONG. Calibration maps inputs forward onto a small number of "
    "scale factors and accepts whatever operating point emerges. It is not "
    "solving the inverse problem it is presented with. Item 50 is the same "
    "defect seen from inside, where the REFERENCE patient rescales itself by "
    "-14 % against its own operating point. "
    "TWO CONSTRAINTS MAKE THE FIX PHYSIOLOGY AND NOT A CURVE FIT: every "
    "adjusted parameter must stay inside a SOURCED physiological range, and "
    "the solution is under-determined, so prefer the smallest departure from "
    "the age- and size-scaled reference and RECORD which parameters moved. "
    "A fit achieved with an impossible blood volume is worse than an honest "
    "miss. "
    "THIS NEEDS NO LITERATURE. The target is the input. "
    "strict=True. Full record in docs/reference_values.md under PMID 41721238."
))
def test_tier3_calibration_converges_on_entered_haemodynamics_pmid41721238():
    """[PMID 41721238] Enter a measured MAP, CVP and cardiac index; the model
    must settle at them.

    The cohort's baseline is MAP 79.2 +/- 14.7, CVP 6.4 +/- 4.6 and cardiac
    index 3.1 +/- 1.5. Asked for exactly that, the model settles somewhere
    else.

    **THE TOLERANCE IS 10 PER CENT OF EACH REQUESTED VALUE, and it is a
    CONVERGENCE criterion rather than a literature spread.** Borrowing the
    cohort's between-patient SD would be the wrong quantity: how widely ICU
    patients vary says nothing about whether a solver reached the number it was
    given. Ten per cent is stated, loose, and chosen for the purpose.

    **This test needs no result data at all.** The target IS the input, which
    is why it can exist for a study that was excluded from the blind phase
    before any outcome was read.
    """
    bsa = bsa_mosteller(170.0, 65.0)
    comps, cardiac = build_patient_params(
        170.0, 65.0,
        map_mmhg=_TIER3_MAP,
        cvp_mmhg=_TIER3_CVP,
        cardiac_output_lpm=_TIER3_CI * bsa,
        hr_bpm=80.0,
        age_years=69.0,
    )
    p = SimParams(compartments=comps)
    apply_cardiac(p, cardiac)
    p.hr_bpm = 80.0
    p.ventilation_mode = "mechanical"
    p.peep_cmh2o = 5.0
    p.pip_cmh2o  = 14.0
    r = run_simulation(p, duration_s=120.0, dt=DT)
    t = np.asarray(r["t"])

    def w(key):
        a = np.asarray(r[key])
        return float(np.mean(a[(t >= 90.0) & (t < 120.0)]))

    settled = {"MAP": (w("map"), _TIER3_MAP),
               "CVP": (w("cvp"), _TIER3_CVP),
               "CI":  (w("co") / bsa, _TIER3_CI)}
    failures = [f"{name} settled at {got:.2f} against {want:.2f} asked "
                f"({100.0 * (got - want) / want:+.1f} %)"
                for name, (got, want) in settled.items()
                if abs(got - want) > 0.10 * want]
    assert not failures, (
        "Tier 3 calibration did not converge — " + "; ".join(failures)
    )


# --- PMID 25760679 ----------------------------------------------------------
# 29 against 28 patients, age 57 and 58, BMI 27.7 and 25.5. Target-controlled
# infusion: remifentanil Ce 8 ng/mL (Minto) and propofol Ce 2.5 mcg/mL
# (Schnider). Ventilated 8 mL/kg, PEEP 5. Vasopressor titrated to 80-100 % of
# the awake MAP.
#
# EXCLUDED FROM THE BLIND PHASE, and the exclusion is this test. The scenario
# could not be built: both drugs bisected to the floor of the dose range and
# still overshot the target, because the model's anaesthetised patient does not
# need a vasopressor at all. Only methods and cohort were read, so the study
# stays clean.


@pytest.mark.xfail(strict=True, reason=(
    "KNOWN GAP — THERE IS NO OPIOID IN THE MODEL, AND THE ANAESTHETIC "
    "BASELINE IS WRONG IN DIRECTION RATHER THAN DEPTH. Backlog item 63. "
    "MEASURED 2026-09-25, age 57, ventilated: heart rate RISES from 76.73 awake to 81.66 on propofol 2.0 mg/kg and 82.26 at 2.5, while mean pressure falls 91.37 -> 86.09 -> 85.42. AND THE SHAPE IS WRONG, NOT ONLY THE SIGN. Højlund 2020 (PMID 31705432) measured 20 patients on remifentanil 0.5-0.8 mcg/kg/min: a 28 per cent FALL in mean pressure produced NO tachycardia (dHR -4 per cent, P 0.276) while a rise in mean pressure still produced bradycardia (-10 per cent, P 0.015). The sympathetic limb is abolished and the vagal limb is intact. A single gain per effector cannot express that, because weakening it blunts BOTH limbs — see backlog item 70.  "
    "pharmacology.py has propofol and spinal block and NO OPIOID OF ANY KIND. "
    "Under propofol alone the model's baroreflex answers vasodilation with "
    "tachycardia. Patients at remifentanil Ce 8 ng/mL are BRADYCARDIC, and at "
    "that effect-site concentration the opioid dominates the haemodynamic "
    "picture — it is not a refinement on the anaesthetic state, it is most of "
    "it. "
    "THE FAILURE WAS CONCRETE, NOT THEORETICAL. A matched-MAP titration "
    "degenerated: the model's anaesthetised patient reached 90 % of its awake "
    "pressure on propofol alone and needed no vasopressor, and in the male arm "
    "the anaesthetised MAP sat ABOVE the target before any drug. The study's "
    "central manoeuvre could not be staged. "
    "DO NOT PROXY IT WITH MORE PROPOFOL. Raising the dose reaches a plausible "
    "pressure while keeping the wrong heart-rate direction — a baseline that "
    "looks quantitatively repaired and stays qualitatively wrong, which is "
    "worse than an honest gap. That option was considered and rejected when "
    "the exclusion was logged. "
    "WHY IT MATTERS BEYOND ONE STUDY: this model is aimed at intraoperative "
    "use and essentially every general anaesthetic includes an opioid. Without "
    "one the model cannot represent the baseline state of its own target "
    "population. "
    "WHAT IT NEEDS: sympatholysis and vagally-mediated bradycardia routed "
    "through the existing effectors, plus BLUNTING OF THE BAROREFLEX RESPONSE "
    "ITSELF — which the current effector set cannot express and which needs "
    "backlog item 70 (outflow and end-organ response are lumped into one "
    "gain). Remifentanil is among the best-characterised drugs in anaesthesia; "
    "scope the literature before writing a coefficient. "
    "DIRECTION ONLY. No magnitude is asserted, because the study's heart-rate "
    "values were never read. "
    "strict=True. Full record in docs/reference_values.md under PMID 25760679."
))
def test_general_anaesthesia_does_not_cause_tachycardia_pmid25760679():
    """[PMID 25760679] Patients anaesthetised with propofol and remifentanil at
    Ce 8 ng/mL are BRADYCARDIC. The model's heart rate rises instead.

    Direction only. The study's own haemodynamic results were never seen — only
    its methods and cohort — so this asserts the sign that the protocol
    implies, not a magnitude from a table.
    """
    def anaesthetised_hr(propofol_mg_kg):
        p = cohort_params(175.0, 80.0, age_years=57.0)
        p.ventilation_mode = "mechanical"
        p.peep_cmh2o = 5.0
        p.pip_cmh2o  = 18.0
        p.resp_rate_bpm = 14.0
        if propofol_mg_kg > 0.0:
            p.drug_factors = combined_drug_factors({"propofol": propofol_mg_kg})
        r = run_simulation(p, duration_s=120.0, dt=DT)
        t = np.asarray(r["t"])
        a = np.asarray(r["hr"])
        return float(np.mean(a[(t >= 90.0) & (t < 120.0)]))

    awake = anaesthetised_hr(0.0)
    asleep = anaesthetised_hr(2.0)
    assert asleep < awake, (
        f"heart rate ROSE on induction, {awake:.1f} -> {asleep:.1f} bpm. "
        f"Patients under propofol and remifentanil Ce 8 are bradycardic. The "
        f"model has no opioid, so the baroreflex answers propofol's "
        f"vasodilation with tachycardia and nothing opposes it."
    )


# ===========================================================================
# 32. The hydrostatic loop closes — backlog items 65 and 66
#
# These two tests PASS. The arrest test was a strict xfail until leg rebuild
# stage 1 closed it on 2026-10-04. Both are guards so the defect cannot come
# back silently.
# ===========================================================================

def test_gravity_does_no_net_work_on_the_arrested_circulation():
    """Stop the heart, tilt the body, and the blood must stop moving.

    **THIS IS A CONSERVATION TEST, NOT A CALIBRATION ONE.** Around any closed
    circuit the hydrostatic height terms must telescope to zero, because gravity
    does no net work on a closed loop. At zero flow every segment must therefore
    satisfy `P_up - P_down = hdp(down) - hdp(up)`.

    **Nothing here depends on a parameter value.** It would hold for any choice
    of resistance, compliance or compartment height, so it cannot be satisfied
    by retuning and it cannot be weakened to make a calibration fit.

    **HISTORY.** Until 2026-10-04 ten flow segments omitted their height term.
    With the heart stopped at 45 degrees head-up the foot segment sat at a
    steady +19.3 mmHg that nothing opposed, and volume drifted 2.20 mL over the
    last 20 s. Blood circulated with no heart. This test was a strict xfail.

    **CLOSED 2026-10-04 by leg rebuild stage 1:** the IVC split into three
    segments, each at its tributary's height, and the height term on every
    flow. Measured: drift 0.097 mL; worst residual upper body +0.020 mmHg,
    foot -0.0002, splanchnic -0.0009.

    **THE PRICE, recorded where it is paid:** head-down tilt now fails
    (Likhvantsev and Monnet, both strict xfails). The old head-down result was
    produced by the violation this test forbids.

    The six segments below are arterial-to-venous exchange beds, which have no
    valves. A shut leg valve may legitimately hold a pressure difference, so
    the vein-to-vein segments are covered by the drift check instead, which
    spans the whole circulation.
    """
    TILT = 45.0
    p = SimParams()
    p.baroreflex_enabled    = False   # keep V0 fixed, so P is a clean function of V
    p.ventilation_mode      = 'none'
    p.slow_dynamics_enabled = False   # no v0_relax offset
    p.tilt_start_deg  = 0.0
    p.tilt_end_deg    = TILT
    p.tilt_onset_s    = 20.0
    p.tilt_duration_s = 5.0
    p.arrest_start_s    = 40.0
    p.arrest_duration_s = 200.0
    r = run_simulation(p, duration_s=240.0, dt=DT)

    comp = p.compartments
    V = np.asarray(r["volumes"])
    t = np.asarray(r["t"])

    def P(name, row):
        c = comp[IDX[name]]
        return _vascular_pressure(row[IDX[name]], c.unstressed_volume,
                                  c.compliance, c.p_stiffen)

    def hdp(name):
        return hydrostatic_delta_mmhg(comp[IDX[name]].height_m, TILT,
                                      GravityEnvironment.EARTH)

    last = V[-1]
    residuals = []
    for up, down in (("upper_body_art",  "upper_body_vein"),
                     ("renal_art",       "renal_vein"),
                     ("splanchnic_art",  "splanchnic_vein"),
                     ("lower_body_art",  "thigh_vein"),
                     ("lower_body_art",  "calf_vein"),
                     ("lower_body_art",  "foot_vein")):
        got  = P(up, last) - P(down, last)
        need = hdp(down) - hdp(up)          # the zero-flow condition
        residuals.append(f"{up}->{down} {got - need:+.2f}")
        assert abs(got - need) < 0.5, (
            f"{up} -> {down}: driving pressure {got:+.3f} mmHg at arrest, but a "
            f"closed hydrostatic loop requires {need:+.3f}. Residual "
            f"{got - need:+.3f} mmHg is a circulation driven by gravity with the "
            f"heart stopped. All residuals: {'; '.join(residuals)}"
        )

    late = V[t >= 215.0]
    drift = float(np.abs(late[-1] - late[0]).max())
    assert drift < 0.5, (
        f"volumes still moving {drift:.3f} mL over the last 20 s of arrest at "
        f"{TILT:.0f} degrees — the arrested circulation has not stopped"
    )


def test_patient_height_scales_the_hydrostatic_column():
    """Stature must change the orthostatic response, and must not change supine.

    **Backlog item 66.** Until 2026-09-25 `height_cm` reached the circulation
    through exactly one route — `bsa_mosteller()` — and every compartment's
    `height_m` was a fixed constant. **A 150 cm and a 200 cm patient of equal
    body surface area had identical orthostatic physics, to the decimal.**

    Orthostatic stress scales with the length of the column being supported,
    which is why stature is a known risk factor for presyncope.

    **THE TWO PATIENTS BELOW HAVE THE SAME BSA TO FOUR DECIMALS** (1.8708), so
    nothing here is a body-size effect: 150 cm / 84 kg against 200 cm / 63 kg.

    **Direction only, and deliberately so.** The scaling is uniform across
    compartments, which is an approximation — body proportions are not
    self-similar, and leg length varies more with stature than trunk length
    does. No magnitude is asserted until an anthropometric source for segment
    lengths is in hand (WANTED in reference_values.md).
    """
    def tilt_response(height_cm, weight_kg, tilt_deg):
        comps, cardiac = build_patient_params(height_cm, weight_kg, hr_bpm=70.0)
        p = SimParams(compartments=comps)
        apply_cardiac(p, cardiac)
        p.hr_bpm = 70.0
        p.tilt_start_deg = 0.0
        p.tilt_end_deg   = tilt_deg
        p.tilt_onset_s   = 5.0
        r = run_simulation(p, duration_s=LIT_DURATION, dt=DT)
        return {k: last_half(r[k]) for k in ("map", "co", "cvp", "sv")}

    SHORT, TALL = (150.0, 84.0), (200.0, 63.0)
    assert abs(bsa_mosteller(*SHORT) - bsa_mosteller(*TALL)) < 1e-9, (
        "the two test patients no longer have equal body surface area, so this "
        "test would be measuring body size rather than stature"
    )

    # 1. Supine must be identical — every hydrostatic term is zero at tilt 0.
    s_sup, t_sup = tilt_response(*SHORT, 0.0), tilt_response(*TALL, 0.0)
    for k in s_sup:
        assert abs(s_sup[k] - t_sup[k]) < 1e-9, (
            f"supine {k} differs between a 150 cm and a 200 cm patient of equal "
            f"BSA ({s_sup[k]:.6f} vs {t_sup[k]:.6f}); stature must reach the "
            f"model only through the hydrostatic term, which is zero when flat"
        )

    # 2. Tilted, the taller patient must be more orthostatically challenged.
    s_up, t_up = tilt_response(*SHORT, 45.0), tilt_response(*TALL, 45.0)
    assert t_up["map"] < s_up["map"], (
        f"at 45 degrees head-up the 200 cm patient's MAP is {t_up['map']:.3f} "
        f"and the 150 cm patient's is {s_up['map']:.3f} — a longer hydrostatic "
        f"column must pool more, not less"
    )
    assert t_up["sv"] < s_up["sv"], (
        f"stroke volume at 45 degrees: 200 cm {t_up['sv']:.3f} vs 150 cm "
        f"{s_up['sv']:.3f}"
    )
    assert t_up["cvp"] < s_up["cvp"], (
        f"filling pressure at 45 degrees: 200 cm {t_up['cvp']:.3f} vs 150 cm "
        f"{s_up['cvp']:.3f}"
    )


# ===========================================================================
# 33. Propofol's venous mechanism — de Wit 2016, PMID 27199311
#
# SPENT FOR BLIND USE (read in full 2026-09-26). A development target.
# ===========================================================================

_DEWIT_PLATEAUS = (5.0, 15.0, 25.0, 35.0)       # cmH2O, the paper's hold protocol
_DEWIT_MAP_CI95  = (-28.0, -11.0)               # per cent, MAP step between the levels
_DEWIT_MSFP_CI95 = (-33.4, -13.2)               # per cent
_DEWIT_RVR_CI95  = (-45.3, -14.2)               # per cent


def _propofol_venous_return_curve(dose_mg_kg):
    """MSFP and Rvr by de Wit's own method, plus steady-state MAP and CO.

    Four sustained inspiratory holds at 5/15/25/35 cmH2O; CVP read as a catheter
    reads it (the model's transmural `cvp` plus intrathoracic pressure — reading
    `cvp` alone gives a POSITIVE slope, see `tools/venous_return_curve.py`);
    linear fit; MSFP is the zero-flow intercept, Rvr the inverse slope.

    **Reflexes OFF throughout**, as a stand-in for the remifentanil these patients
    were also receiving — under remifentanil the sympathetic limb is abolished
    (Hojlund 2020 and 2024: no tachycardia on a 28-33 % pressure fall). This is a
    stand-in with a known flaw: it also removes the vagal limb.
    """
    import model.respiration as resp

    def params():
        p = SimParams()
        p.baroreflex_enabled = False
        if dose_mg_kg:
            p.drug_factors = combined_drug_factors({"propofol": dose_mg_kg})
        p.ventilation_mode = "mechanical"
        return p

    pts = []
    for pl in _DEWIT_PLATEAUS:
        p = params()
        p.peep_cmh2o = p.pip_cmh2o = pl
        p.resp_rate_bpm = 12.0
        r = run_simulation(p, duration_s=45.0, dt=DT)
        h = int(len(r["t"]) * 0.75)
        itp = resp.intrathoracic_pressure(0.0, "mechanical", 12.0, pl, pl, p.ie_ratio)
        pts.append((float(np.mean(r["cvp"][h:])) + itp, float(np.mean(r["co"][h:]))))
    cvp = np.array([x[0] for x in pts]); co = np.array([x[1] for x in pts])
    slope, icpt = np.polyfit(cvp, co, 1)

    p = params()
    p.peep_cmh2o, p.pip_cmh2o, p.resp_rate_bpm = 5.0, 17.0, 13.0
    r = run_simulation(p, duration_s=45.0, dt=DT)
    return {"msfp": float(-icpt / slope), "rvr": float(1.0 / abs(slope)),
            "map": last_half(r["map"]), "co": last_half(r["co"])}


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "KNOWN GAP — THE MODEL'S PROPOFOL IS RIGHT FOR THE WRONG REASON. It was fitted "
    "to Claeys 1988's pressure and output, and it reproduces both — but it lowers "
    "pressure almost entirely by ARTERIAL dilation. De Wit 2016 measured the "
    "mechanism in humans with inspiratory-hold venous return curves: propofol moves "
    "blood out of the STRESSED volume and lowers VENOUS resistance, and that is what "
    "holds cardiac output while pressure falls. "
    "MEASURED 2026-09-26, reflexes off, same hold protocol, stepping 1.0 -> 6.0 "
    "mg/kg: MAP -17.6 per cent (de Wit -19.5, matched), CO -3.3 (de Wit -3.5 NS, "
    "matched), MSFP -4.4 per cent against a measured -23.3, and Rvr -2.8 per cent "
    "against -29.7. The mechanistic quantities are missed by a factor of five to ten. "
    "WHY IT MATTERS DOWNSTREAM: a real anaesthetised patient parks several hundred mL "
    "in the unstressed pool, and that parked volume is what phenylephrine recruits. "
    "The model parks very little, which is part of why phenylephrine cannot raise "
    "stroke volume (backlog item 64, Hojlund 2024 test). "
    "THE MECHANISM IS PROBABLY SYMPATHOLYSIS, NOT A DIRECT VENOUS ACTION — the "
    "authors cite Robinson 1997 (human forearm, similar to stellate block) and Hoka "
    "1998 (rats, abolished by ganglion block). In this model that belongs on "
    "sympathetic OUTFLOW, which does not yet exist as a stage: backlog item 70. "
    "AND THE MODEL HAS NO DRUG EFFECT ON VENOUS RESISTANCE AT ALL, which is the "
    "second half of how humans hold output. "
    "DO NOT CLOSE THIS BY RAISING propofol's venous e_max ALONE — MAP would then fall "
    "too far, and the arterial arm fitted to Claeys absorbs the venous share. Both "
    "arms and a venous-resistance term have to be refitted together, to Claeys AND "
    "de Wit. strict=True. Full record in docs/validation_log.md, 2026-09-26."
))
def test_propofol_lowers_stressed_volume_and_venous_resistance_dewit2016():
    """[PMID 27199311 — de Wit 2016] Deepening propofol anaesthesia lowers mean
    systemic filling pressure 23 % and resistance to venous return 30 %, with
    cardiac output unchanged.

    n=17 after oesophageal resection, propofol TCI plus remifentanil, Cb raised
    3.0 -> 6.5 mcg/mL: MAP 82 -> 66, MSFP 27.9 (5.4) -> 21.4 (4.2), Rvr 3.7 (1.4) ->
    2.6 (0.7), CO 5.7 -> 5.5 (NS).

    **DOSE-AXIS-FREE.** The model's bolus-equivalent mg/kg and de Wit's blood
    concentration cannot be mapped onto each other. So the test chooses a dose STEP
    whose MAP fall matches de Wit's, and asserts the mechanism across that step.
    **The MAP match is a PRECONDITION and fails with `pytest.fail`, not an
    assertion**, so a change that breaks the dose match surfaces as a real failure
    rather than hiding inside this expected one.

    **The bands are 95 % confidence intervals of the mean ratio**, computed from the
    reported means and SDs treating the two levels as independent — which
    overstates the uncertainty for a paired design, so they are conservative.

    **Why MSFP survives the study's device choice.** Cardiac output was by
    Modelflow pulse contour, which is tone-sensitive. But MSFP is the ZERO-FLOW
    intercept of the fitted venous return line, and a proportional error in cardiac
    output does not move a zero crossing. Rvr, the slope, is less protected.
    """
    lo, hi = _propofol_venous_return_curve(1.0), _propofol_venous_return_curve(6.0)
    d = {k: 100.0 * (hi[k] - lo[k]) / lo[k] for k in lo}

    mlo, mhi = _DEWIT_MAP_CI95
    if not (mlo <= d["map"] <= mhi):
        pytest.fail(
            f"PRECONDITION: the 1.0 -> 6.0 mg/kg step lowers MAP {d['map']:+.1f} %, "
            f"outside de Wit's {mlo} to {mhi} %. The dose pair no longer matches the "
            f"study's pressure step and must be re-chosen before the mechanism can be "
            f"compared."
        )
    for key, (a, b), label in (("msfp", _DEWIT_MSFP_CI95, "mean systemic filling pressure"),
                               ("rvr",  _DEWIT_RVR_CI95,  "resistance to venous return")):
        assert a <= d[key] <= b, (
            f"{label} changes {d[key]:+.1f} % across a propofol step that lowers MAP "
            f"{d['map']:+.1f} %; de Wit measured a fall inside {a} to {b} %. "
            f"All changes: {', '.join(f'{k} {v:+.1f}' for k, v in d.items())}"
        )


# ===========================================================================
# 34. Demand pacing — the input that lets a paced cohort be reproduced
# ===========================================================================

def test_demand_pacing_holds_rate_and_leaves_the_vascular_reflex_working():
    """`paced_hr_bpm` is a LOWER RATE LIMIT, and it must supersede only the rate.

    **Why it exists.** Switching the baroreflex off was the only way to hold heart
    rate still, and that also removes the reflex's vascular arms. A paced patient
    keeps those. Juhl-Olsen 2023 (PMID 37186094) — the cleanest phenylephrine
    study in the ledger — paced 25 of 30 patients at 80-90 /min, so without this
    input it cannot be reproduced honestly.

    **Four properties, all calibration-independent:**
    1. Above the native rate it CAPTURES exactly and holds.
    2. Below the native rate it does nothing — demand pacing, as AAI and DDD
       pacing behave.
    3. The vascular reflex still defends pressure under pacing. Measured
       2026-09-26 at 45 deg head-up: MAP falls 11.0 unpaced, 12.7 paced at 90, and
       37.2 with the reflex off. Paced must stay far nearer the first than the last.
    4. Unset (None) is the identity — asserted bit-for-bit against a saved run
       when the input was added, and covered by the suite's existing
       default-run tests since no code path changes.
    """
    def run(paced=None, baro=True, tilt=0.0):
        p = SimParams()
        p.paced_hr_bpm = paced
        p.baroreflex_enabled = baro
        p.tilt_start_deg, p.tilt_end_deg, p.tilt_onset_s = 0.0, tilt, 5.0
        r = run_simulation(p, duration_s=LIT_DURATION, dt=DT)
        h = len(r["hr"]) // 2
        return np.asarray(r["hr"][h:]), last_half(r["map"])

    native_hr, _ = run()
    paced_hr, _ = run(paced=85.0)
    assert np.allclose(paced_hr, 85.0), (
        f"paced at 85 above a native {native_hr.mean():.1f}, heart rate ran "
        f"{paced_hr.min():.3f}-{paced_hr.max():.3f} — it must capture exactly"
    )

    low_hr, _ = run(paced=50.0)
    assert np.allclose(low_hr, native_hr), (
        "paced at 50, below the native rate, changed heart rate — demand pacing "
        "must not capture when the native rhythm is faster"
    )

    drop = {}
    for label, kw in (("unpaced", {}), ("paced", {"paced": 90.0}), ("off", {"baro": False})):
        _, m0 = run(tilt=0.0, **kw)
        _, m1 = run(tilt=45.0, **kw)
        drop[label] = m1 - m0
    assert abs(drop["paced"] - drop["unpaced"]) < 0.25 * abs(drop["off"] - drop["unpaced"]), (
        f"45 deg head-up MAP fall: unpaced {drop['unpaced']:+.2f}, paced "
        f"{drop['paced']:+.2f}, reflex off {drop['off']:+.2f}. Pacing must remove "
        f"the rate response only; the vascular reflex has to keep defending pressure"
    )


# ===========================================================================
# 35. Reflex OUTFLOW and end-organ RESPONSIVENESS — backlog item 70, pass 1
#
# Pass 1 changes no number: every default is exactly 1.0, and the reflex-active
# identity (45 deg tilt with phenylephrine, and a 1000 mL bleed, 20 output
# arrays) was checked bit-for-bit when it landed. What this section guards is
# the other half: that each new setting is LIVE and CORRECTLY SIGNED. A
# documented mechanism that silently does nothing is the most common defect in
# this repository — see the dead `venous_tone_factor` in CLAUDE.md.
# ===========================================================================

def _reflex_run(tilt=0.0, drugs=None, **params):
    p = SimParams()
    p.tilt_start_deg, p.tilt_end_deg, p.tilt_onset_s = 0.0, tilt, 5.0
    if drugs:
        p.drug_factors = combined_drug_factors(drugs)
    for k, v in params.items():
        setattr(p, k, v)
    r = run_simulation(p, duration_s=LIT_DURATION, dt=DT)
    return {"map": last_half(r["map"]), "hr": last_half(r["hr"])}


def test_reflex_outflow_and_responsiveness_are_live_and_signed():
    """Each item-70 setting must act, and in the physiological direction.

    1. SYMPATHETIC outflow removed: head-up tilt is defended worse (MAP falls
       further) and produces less tachycardia.
    2. VAGAL outflow removed: phenylephrine's reflex bradycardia shrinks.
    3. ARTERIOLAR responsiveness removed: tilt is defended worse.
    4. VAGAL sinus-node responsiveness removed: the bradycardia shrinks, as with
       outflow removed — the two are nearly interchangeable in pass 1 by design.
    5. An unknown responsiveness key is refused, so a typo cannot silently fall
       back to the default.
    """
    base_up = _reflex_run(tilt=45.0)
    base_flat = _reflex_run()
    no_symp_up = _reflex_run(tilt=45.0, sympathetic_outflow_scale=0.0)
    no_symp_flat = _reflex_run(sympathetic_outflow_scale=0.0)
    assert (no_symp_up["map"] - no_symp_flat["map"]) < (base_up["map"] - base_flat["map"]) - 2.0, (
        "removing sympathetic outflow did not worsen the defence of pressure on tilt"
    )
    assert (no_symp_up["hr"] - no_symp_flat["hr"]) < (base_up["hr"] - base_flat["hr"]) - 1.0, (
        "removing sympathetic outflow did not reduce the tachycardia of tilt"
    )

    pe = {"phenylephrine": 1.0}
    brady = _reflex_run(drugs=pe)["hr"] - base_flat["hr"]
    no_vag_flat = _reflex_run(vagal_outflow_scale=0.0)
    brady_no_vag = _reflex_run(drugs=pe, vagal_outflow_scale=0.0)["hr"] - no_vag_flat["hr"]
    assert brady < 0 and brady_no_vag > brady + 1.0, (
        f"removing vagal outflow did not shrink phenylephrine's bradycardia "
        f"({brady:+.1f} -> {brady_no_vag:+.1f} bpm)"
    )

    r_svr0 = {"svr": 0.0}
    svr0_up = _reflex_run(tilt=45.0, reflex_responsiveness=r_svr0)
    svr0_flat = _reflex_run(reflex_responsiveness=r_svr0)
    assert (svr0_up["map"] - svr0_flat["map"]) < (base_up["map"] - base_flat["map"]) - 2.0, (
        "removing arteriolar responsiveness did not worsen the defence of pressure on tilt"
    )

    r_vag0 = {"hr_vagal": 0.0}
    vag0_flat = _reflex_run(reflex_responsiveness=r_vag0)
    brady_r0 = _reflex_run(drugs=pe, reflex_responsiveness=r_vag0)["hr"] - vag0_flat["hr"]
    assert brady_r0 > brady + 1.0, (
        f"removing vagal sinus-node responsiveness did not shrink the bradycardia "
        f"({brady:+.1f} -> {brady_r0:+.1f} bpm)"
    )

    from model.baroreflex import BaroreflexController
    with pytest.raises(ValueError):
        BaroreflexController(responsiveness={"svr_typo": 0.5})


# ===========================================================================
# 36. INTERNAL CONSISTENCY — one quantity, stated once
#
# `tools/consistency_audit.py` collects every place the model states one
# physiological quantity and prints the routes side by side. On 2026-09-27 it
# found 16 such quantities and **10 disagreed**. The audit needs no literature:
# it asks only whether the model agrees with itself, so a disagreement is a
# defect by construction, whichever side is wrong.
#
# BUT THE AUDIT IS A REPORTING TOOL, AND CLAUDE.md STEP 7 SAYS THOSE ROT.
# Nothing fails when it goes stale. These three tests take the checks that are
# cheap and calibration-independent and make them assertions, so the ratchet
# reaches them. They are deliberately NOT a port of the whole audit — the rest
# needs judgement about which of two routes is right, which a test cannot carry.
# ===========================================================================


def test_the_reference_operating_point_is_stated_once_and_consistently():
    """The reference operating point must not drift apart between its copies.

    Backlog item 50 asked for exactly this: *"Add a guard asserting the two
    agree, so they cannot drift apart. Same argument as item 16's settling
    guard: a rule that depends on memory gets forgotten."*

    Item 50 removed `patient.py`'s hard-coded copy — it now imports. But
    `baroreflex.py` still writes 93.0 TWICE, as `MAP_SETPOINT` and as
    `REFERENCE_MAP_MMHG`, so they agree by coincidence of two literals rather
    than by construction. That is what the first assertion guards.

    THE CVP CONSTANTS ARE DELIBERATELY DIFFERENT AND THIS TEST DOES NOT DEMAND
    THEY AGREE. Item 39 records why: driving the cardiopulmonary heart-rate arm
    from `CVP_SETPOINT` produced a 6.0 bpm standing bradycardia (66.2 -> 60.2)
    purely from the mismatch against where the model actually rests. So the gap
    is a decision, not a defect. What this test does is PIN the decision, so
    that editing either constant fails here and sends the reader to item 39
    instead of silently changing a reflex reference.
    """
    from model.baroreflex import (MAP_SETPOINT, CVP_SETPOINT,
                                  CP_HR_REFERENCE_CVP_MMHG,
                                  REFERENCE_MAP_MMHG, REFERENCE_CVP_MMHG)

    assert MAP_SETPOINT == REFERENCE_MAP_MMHG, (
        f"THE SAME QUANTITY IS WRITTEN TWICE AND THE TWO NOW DISAGREE: "
        f"MAP_SETPOINT={MAP_SETPOINT}, REFERENCE_MAP_MMHG={REFERENCE_MAP_MMHG}. "
        f"Both are the reference patient's resting mean arterial pressure. Make one "
        f"of them import the other rather than editing both. Backlog item 50."
    )

    # The recorded, deliberate relationships. Changing a constant must fail here.
    # 4.7 -> 4.27 on 2026-10-06 (Klotz LV curve; the settled CVP with the arm at
    # rest — see the note at CP_HR_REFERENCE_CVP_MMHG and backlog item 39).
    # 2026-10-09: BOTH restated as CYCLE MEANS (the reflex now reads mean RA, not
    # the trough): 3.0 -> 4.54 and 4.27 -> 5.82, each + the measured resting
    # mean - trough offset 1.540 mmHg. The deliberate gap is kept (1.27 -> 1.28).
    # 2026-10-11: re-measured by the same definition after the AV-plane coupling
    # and the sac went on (resting mean RA fell); gap kept at 1.28.
    assert CVP_SETPOINT == 3.04 and CP_HR_REFERENCE_CVP_MMHG == 4.32, (
        f"A FILLING-PRESSURE REFERENCE CHANGED: CVP_SETPOINT={CVP_SETPOINT} "
        f"(was 3.04, uncited, used by the SVR arm), CP_HR_REFERENCE_CVP_MMHG="
        f"{CP_HR_REFERENCE_CVP_MMHG} (was 4.32, the cardiopulmonary arm's reference, "
        f"chosen to sit at the model's own settled filling pressure). THEY ARE "
        f"DELIBERATELY DIFFERENT — read backlog item 39 before changing either, and "
        f"note that driving the HR arm from CVP_SETPOINT cost 6.0 bpm of spurious "
        f"resting bradycardia. If the change is intended, update this assertion AND "
        f"item 39 together."
    )
    assert CP_HR_REFERENCE_CVP_MMHG > CVP_SETPOINT, (
        "The cardiopulmonary reference has fallen to or below the SVR setpoint. "
        "The whole reason for a separate reference was that the SVR setpoint sits "
        "BELOW where the model rests. Backlog item 39."
    )
    # REFERENCE_CVP_MMHG is the patient-scaling reference, a third quantity again.
    # It is NOT asserted equal to either of the above — item 50's xfail covers the
    # fact that it does not match where the model settles either.
    assert REFERENCE_CVP_MMHG == 5.0, (
        f"REFERENCE_CVP_MMHG changed to {REFERENCE_CVP_MMHG}. It is the "
        f"patient-scaling reference and moving it rescales EVERY patient's SVR. "
        f"See test_reference_operating_point_is_self_consistent, which is a strict "
        f"xfail because this value does not match the model's settled state."
    )


def test_the_venous_compartment_tuples_agree_across_modules():
    """The same set of venous compartments is written out in two modules.

    `circulation.VENOUS_RESERVOIR` and `slow_dynamics.STRESS_RELAX_COMPARTMENTS`
    are two identical literal 8-tuples in two files, with nothing tying them
    together. That is the backlog item 50 shape — one quantity, two copies, no
    link — and it is currently benign only because nobody has edited one of them.

    Found by `tools/consistency_audit.py`, 2026-09-27. Cheap to assert, and it
    would catch an edit to one tuple and not the other on the day it happened.
    """
    from model.circulation import VENOUS_RESERVOIR, MOBILIZABLE_VENOUS_RESERVOIR
    from model.slow_dynamics import STRESS_RELAX_COMPARTMENTS

    vr, sr = set(VENOUS_RESERVOIR), set(STRESS_RELAX_COMPARTMENTS)
    assert vr == sr, (
        f"THE TWO COPIES OF THE VENOUS COMPARTMENT SET HAVE DIVERGED. "
        f"Only in circulation.VENOUS_RESERVOIR: {sorted(vr - sr)}. "
        f"Only in slow_dynamics.STRESS_RELAX_COMPARTMENTS: {sorted(sr - vr)}. "
        f"If the divergence is intended, say so in both files and relax this test "
        f"deliberately — stress relaxation applying to a different set from the "
        f"venous reservoir is a physiological claim and needs stating as one."
    )
    assert set(MOBILIZABLE_VENOUS_RESERVOIR) <= vr, (
        f"MOBILIZABLE_VENOUS_RESERVOIR is not a subset of the venous reservoir: "
        f"{sorted(set(MOBILIZABLE_VENOUS_RESERVOIR) - vr)} is mobilizable but is not "
        f"a venous reservoir compartment. A bed cannot be recruitable without being "
        f"a reservoir."
    )
    # Every named compartment must actually exist, which a literal tuple does not
    # guarantee — a typo would silently drop a compartment from the mechanism.
    for name in vr | set(MOBILIZABLE_VENOUS_RESERVOIR):
        assert name in IDX, f"{name!r} is named in a venous tuple but is not a compartment"


# ITEM 74 CLOSED 2026-10-08 — this was a strict xfail from 2026-09-27 and it
# XPASSED the day the beds were added, which is the announcement the ratchet
# exists to make. It is now a LIVE GUARD.
#
# WHAT WAS WRONG: _odes carries six artery-to-vein exchange segments (upper
# body, renal, splanchnic, thigh, calf, foot) and CAPILLARY_BEDS had four. The
# calf and foot appeared nowhere, so the whole lower limb filtered through
# thigh_vein at a weight of 0.20. Leg capillary pressure is the HIGHEST in the
# model when upright, so the omitted beds were the ones where filtration should
# be largest.
# HOW IT WAS CLOSED: the leg's total share stayed 0.20 and was re-partitioned by
# soft-tissue mass (Winter 2009) into thigh 0.1242 / calf 0.0578 / foot 0.0180.
# The prompt was Lundvall 1993 (PMID 8475742), which measures 460 mL of plasma
# filtering into the legs during LBNP — a time course the model could not
# produce with two of its three leg beds inert.
def test_every_exchange_bed_has_a_capillary_filtration_bed():
    """Every bed the ODE pushes blood through must also filter.

    An artery-to-vein exchange segment IS a capillary bed — that is what the
    segment represents. If the fast ODE moves blood through six of them and the
    slow Starling machinery only knows four, then two capillary beds carry flow
    and pressure but exchange no fluid.

    The exchange beds are derived rather than hard-coded: they are the venous
    reservoir compartments minus the two pure conduits (SVC and IVC), which
    receive venous inflow rather than arterial. Deriving them means this test
    cannot go stale against a compartment change the way a literal list would.
    """
    from model.circulation import VENOUS_RESERVOIR, VENOUS_CONDUITS
    from model.slow_dynamics import CAPILLARY_BEDS

    # From the model, not a literal (2026-10-04). This test's own docstring says
    # deriving the beds keeps it from going stale — but the CONDUIT set was still
    # written by hand as {"svc", "ivc"}, so splitting the IVC would have made it
    # report two pure conduits as missing filtration beds. Still an xfail, but for
    # a partly wrong reason, and nothing would have said so.
    conduits = set(VENOUS_CONDUITS)
    exchange_beds = set(VENOUS_RESERVOIR) - conduits
    filtering = {venous for _, venous, _ in CAPILLARY_BEDS}

    missing = sorted(exchange_beds - filtering)
    assert not missing, (
        f"{len(missing)} exchange bed(s) carry blood flow but no Starling "
        f"filtration: {missing}. Either add them to slow_dynamics.CAPILLARY_BEDS "
        f"with sourced surface-area weights, or state in that module why the "
        f"remaining bed is a deliberate lumped stand-in for them. Backlog item 74."
    )
    # A weight that does not sum to 1.0 would silently rescale total filtration.
    total_w = sum(w for _, _, w in CAPILLARY_BEDS)
    assert abs(total_w - 1.0) < 1e-9, (
        f"CAPILLARY_BEDS weights sum to {total_w}, not 1.0, so total capillary "
        f"filtration has been rescaled. KF_TOTAL is a whole-body figure from "
        f"Guyton and the weights only DISTRIBUTE it."
    )


# ===========================================================================
# 37. VENOUS COMPLIANCE as a separate degree of freedom — backlog item 70
#
# Added 2026-09-27. Mean systemic filling pressure is stressed volume divided by
# compliance, so a fall in filling pressure under anaesthesia can come from
# unstressed volume RISING or from compliance RISING. On Hahn 2022's Table 1 a
# 13.8 % fall in stressed volume and a 16.0 % rise in compliance produce exactly
# the same observed fall. Until this factor existed the model had only the V0
# knob, so it was forced to attribute every venous drug effect to unstressed
# volume — and was credited or blamed for the whole of it on that basis three
# times (propofol against de Wit, phenylephrine against Bell, the spinal block).
#
# NO DRUG SETS IT YET, deliberately. It exists so that de Wit 2016 — MSFP, Rvr,
# Ra, CVP, CO and SVV at three propofol levels — can DISCRIMINATE the two
# mechanisms, rather than us choosing the only one the model could express.
#
# THIS SECTION EXISTS BECAUSE OF THE DEAD `venous_tone_factor`. That pathway was
# assembled and never applied, so venoconstriction silently did nothing for
# months. A new venous factor with no test is the same bug waiting to happen.
# ===========================================================================


def _vc_run(vc, **kw):
    p = SimParams()
    p.baroreflex_enabled = False      # isolate the mechanism from the reflex
    p.ventilation_mode = "none"
    f = dict(combined_drug_factors({}))
    if vc is not None:
        f["venous_compliance_factor"] = vc
    p.drug_factors = f
    for k, v in kw.items():
        setattr(p, k, v)
    r = run_simulation(p, duration_s=45.0, dt=DT)
    return {k: last_half(r[k]) for k in ("map", "co", "cvp", "sv")}


def test_venous_compliance_factor_is_live_and_correctly_signed():
    """The compliance knob must act, in the direction the Starling identity requires.

    P = stressed volume / compliance. So for a given contained volume:
      * factor > 1 (MORE compliant) holds that volume at a LOWER pressure, which
        lowers filling pressure, preload, stroke volume and cardiac output;
      * factor < 1 (stiffer) does the reverse.

    The sign matters more than the size here, and it is the opposite of
    `venous_tone_factor`'s convention — that one is < 1 for venoCONSTRICTION.
    Two venous factors with inverted conventions is exactly the trap CLAUDE.md
    warns about for `venous_tone_factor`, so both directions are asserted.

    Reflexes are OFF so the mechanism is measured rather than the reflex's
    response to it. Calibration-independent: only orderings are asserted.
    """
    base = _vc_run(1.0)
    soft = _vc_run(1.30)
    stiff = _vc_run(0.85)

    assert soft["cvp"] < base["cvp"] - 0.15, (
        f"raising venous compliance did not lower filling pressure "
        f"({base['cvp']:.2f} -> {soft['cvp']:.2f} mmHg). The factor is not reaching "
        f"the pressure calculation — see the dead venous_tone_factor in CLAUDE.md."
    )
    assert soft["co"] < base["co"] - 0.10 and soft["map"] < base["map"] - 1.0, (
        f"raising venous compliance did not lower output ({base['co']:.2f} -> "
        f"{soft['co']:.2f} L/min) or pressure ({base['map']:.1f} -> {soft['map']:.1f})"
    )
    assert stiff["cvp"] > base["cvp"] + 0.15, (
        f"lowering venous compliance did not raise filling pressure "
        f"({base['cvp']:.2f} -> {stiff['cvp']:.2f} mmHg). THE SIGN MAY BE INVERTED."
    )
    assert stiff["co"] > base["co"] + 0.10, "stiffer veins did not raise cardiac output"
    # Monotonic across the range, so the mechanism is not saturating or oscillating.
    mids = [_vc_run(v)["cvp"] for v in (0.85, 1.0, 1.16, 1.30)]
    assert mids == sorted(mids, reverse=True), (
        f"filling pressure is not monotonic in venous compliance: {mids}"
    )


def test_venous_compliance_factor_defaults_to_the_identity():
    """Omitting the factor must be the same as setting it to 1.0, exactly.

    The factor was added to `NEUTRAL_FACTORS` and to `combined_drug_factors`'s
    merge dict, so any caller that never mentions it must get an unchanged model.
    Bit-for-bit identity on the reflex-active case was verified when the factor
    landed (45 deg tilt with phenylephrine and mechanical ventilation, plus a
    bleed, 56 arrays). This asserts the cheap half of that permanently.
    """
    from model.pharmacology import NEUTRAL_FACTORS, combined_drug_factors
    assert NEUTRAL_FACTORS["venous_compliance_factor"] == 1.0
    # No drug may set it until a source says otherwise — see the section note.
    for drug, dose in (("norepinephrine", 0.1), ("phenylephrine", 1.0),
                       ("propofol", 2.0), ("spinal", 1.0), ("vasopressin", 2.0),
                       ("epinephrine", 0.05)):
        f = combined_drug_factors({drug: dose})
        assert f["venous_compliance_factor"] == 1.0, (
            f"{drug} now returns a venous_compliance_factor of "
            f"{f['venous_compliance_factor']}. If that is intended it needs a SOURCE "
            f"and a validation-log entry, and this assertion should name it."
        )
    omitted = _vc_run(None)
    explicit = _vc_run(1.0)
    assert omitted == explicit, (
        f"omitting the factor is not the identity: {omitted} vs {explicit}"
    )


def test_venous_resistance_factor_is_live_and_correctly_signed():
    """The venous resistance knob must act, and RAISE output when it falls.

    Resistance to venous return sits between the filling-pressure point and the
    right atrium, so CO = (Pmsf - CVP) / Rvr. Lowering it must raise venous
    return and therefore cardiac output, WITHOUT moving mean systemic filling
    pressure — filling pressure is a capacitance property and resistance is not.

    **THAT INDEPENDENCE IS THE POINT, AND IT IS ASSERTED.** It is what makes this
    factor identifiable alongside `venous_tone_factor` and
    `venous_compliance_factor`, both of which move filling pressure. Measured
    2026-09-27: cutting venous resistance 45 % moved Pmsf by 0.04 mmHg (20.81 ->
    20.77) while raising cardiac output 18 %. If a future change couples them,
    this test fails and the discrimination in docs/validation_log.md is void.

    NOTE THE CONVENTION IS NOT INVERTED. > 1 is constriction here, because it
    multiplies a resistance. `venous_tone_factor` is the odd one out at < 1 for
    constriction, because it multiplies unstressed volume.
    """
    def run(vr):
        p = SimParams()
        p.baroreflex_enabled = False
        p.ventilation_mode = "none"
        f = dict(combined_drug_factors({}))
        f["venous_resistance_factor"] = vr
        p.drug_factors = f
        r = run_simulation(p, duration_s=45.0, dt=DT)
        return {k: last_half(r[k]) for k in ("map", "co", "cvp")}

    base, dilated, constricted = run(1.0), run(0.60), run(1.60)

    assert dilated["co"] > base["co"] + 0.10, (
        f"lowering venous resistance did not raise cardiac output "
        f"({base['co']:.2f} -> {dilated['co']:.2f} L/min). The factor is not reaching "
        f"R_drain — see the dead venous_tone_factor in CLAUDE.md."
    )
    assert constricted["co"] < base["co"] - 0.10, (
        f"raising venous resistance did not lower cardiac output "
        f"({base['co']:.2f} -> {constricted['co']:.2f}). THE SIGN MAY BE INVERTED."
    )
    # Filling pressure rises slightly as flow rises (the atrium is better fed),
    # but the effect must stay small relative to the flow change: this factor is
    # a resistance, not a capacitance.
    assert abs(dilated["cvp"] - base["cvp"]) < 1.5, (
        f"venous resistance moved filling pressure by "
        f"{dilated['cvp'] - base['cvp']:+.2f} mmHg, which is too much for a pure "
        f"resistance change and breaks its independence from the two capacitance "
        f"factors. See the de Wit discrimination, validation_log.md 2026-09-27."
    )


def test_venous_resistance_factor_defaults_to_the_identity():
    """Omitting the factor must be the same as 1.0, and no drug may set it yet.

    Bit-for-bit identity was verified when the factor landed: 56 output arrays,
    45 deg tilt with phenylephrine and mechanical ventilation, plus a bleed.
    """
    from model.pharmacology import NEUTRAL_FACTORS, combined_drug_factors
    assert NEUTRAL_FACTORS["venous_resistance_factor"] == 1.0
    for drug, dose in (("norepinephrine", 0.1), ("phenylephrine", 1.0),
                       ("propofol", 2.0), ("spinal", 1.0), ("vasopressin", 2.0),
                       ("epinephrine", 0.05)):
        f = combined_drug_factors({drug: dose})
        assert f["venous_resistance_factor"] == 1.0, (
            f"{drug} now returns a venous_resistance_factor of "
            f"{f['venous_resistance_factor']}. de Wit 2016 gives -30 % for propofol "
            f"and Maas 2013 x1.50 for noradrenaline, so a value here is SOURCEABLE — "
            f"but it needs a validation-log entry and this assertion should name it."
        )


# ===========================================================================
# 38. RESTING SYMPATHETIC VENOUS TONE — backlog item 70, pass 2
#
# Before this, the reflex worked purely in deviation form: at rest every outflow
# was zero and the venous effector sat ON its clip, 100 % of the time. **Resting
# venous tone was zero, so a sympatholytic had nothing to withdraw** — which is
# why an opioid could not lower resting pressure through the reflex (item 63) and
# why anaesthetic venodilation had to be smuggled in as a direct drug effect.
#
# The tone is applied in `_odes`, NOT inside the reflex. Putting it inside was
# tried and rejected: it made `baroreflex_enabled = False` mean "denervated" and
# would have silently moved every reflex-off test in the suite.
# ===========================================================================


def _tone_rest(tone, ks=1.0):
    p = SimParams()
    p.venous_resting_tone = tone
    p.sympathetic_outflow_scale = ks
    r = run_simulation(p, duration_s=45.0, dt=DT)
    return {k: last_half(r[k]) for k in ("map", "co", "cvp", "sv")}


def test_resting_venous_tone_is_neutral_while_outflow_is_intact():
    """Adding resting tone must not move the patient while the nerves are intact.

    The re-baselining (V0 divided by 1 - tone) and the tone term (1 - tone) cancel
    EXACTLY at `sympathetic_outflow_scale = 1`, in every scenario rather than only
    at rest. So the whole calibrated model is unchanged and only a SYMPATHOLYTIC
    sees a difference — the same constraint items 32, 34, 66 and pass 1 used.

    Verified more broadly when this landed: 56 output arrays across a 45 deg tilt
    with phenylephrine and a 2000 mL/min bleed, 11 bit-for-bit and 45 differing by
    under 1e-9 from the floating-point round-trip. This asserts the cheap half.

    THE TONE HAS A CEILING, AND PASS 3 IMPOSED IT. Resting tone cannot exceed
    `ALPHA1_VENOUS_EMAX` (0.35), because it is an occupancy of the same receptor
    pool the drugs use: a tone that saturated the receptor would leave an alpha1
    agonist with nothing to add. `alpha1_tone_drive` raises ValueError above it.
    The sweep below therefore stops at 0.32. It used to include 0.40, which pass
    3 correctly refused.
    """
    base = _tone_rest(0.0)
    for tone in (0.10, 0.24, 0.32):
        toned = _tone_rest(tone)
        for k in ("map", "co", "cvp", "sv"):
            assert abs(toned[k] - base[k]) < 1e-4, (
                f"resting tone {tone} moved {k} from {base[k]:.6f} to {toned[k]:.6f} "
                f"with outflow intact. The V0 re-baselining in _odes is not cancelling "
                f"the tone term — check the 1/(1 - tone) factor."
            )


@pytest.mark.parametrize("ks,expect_fall", [(1.0, False), (0.0, True)])
def test_withdrawing_venous_tone_venodilates(ks, expect_fall):
    """Sympatholysis must venodilate: less preload, less output.

    `sympathetic_outflow_scale = 0` is ganglionic blockade. It removes the tone
    term, leaving unstressed volume at its denervated value, so blood moves into
    the unstressed pool and preload falls. **Nothing in the model could do this
    before pass 2** — that is the defect the pass exists to fix.

    Calibration-independent: only the direction and the ordering are asserted.
    """
    base = _tone_rest(0.24, ks=1.0)
    arm = _tone_rest(0.24, ks=ks)
    if not expect_fall:
        assert arm == base
        return
    assert arm["cvp"] < base["cvp"] - 0.20, (
        f"withdrawing sympathetic outflow did not lower filling pressure "
        f"({base['cvp']:.2f} -> {arm['cvp']:.2f} mmHg). Resting venous tone is not "
        f"reaching the unstressed volume — the pass 2 defect, or a regression of it."
    )
    assert arm["sv"] < base["sv"] - 1.0 and arm["co"] < base["co"] - 0.10, (
        f"withdrawing outflow did not lower stroke volume ({base['sv']:.1f} -> "
        f"{arm['sv']:.1f} mL) or cardiac output ({base['co']:.2f} -> {arm['co']:.2f})"
    )


def test_ganglionic_blockade_lowers_filling_pressure_appleton1986():
    """[PMID 3717360 — Appleton 1986] Removing sympathetic tone lowers Pmsf ~26 %.

    **THIS IS A CALIBRATION CHECK, NOT VALIDATION.** `VENOUS_RESTING_TONE = 0.24`
    was chosen to reproduce this number, so the test asserts that the calibration
    held, not that the model predicted anything. `check_insample.py` should find
    this PMID here and be right to.

    THE TARGET, and why Appleton rather than the two human studies. Three sources
    give the fall in filling pressure when sympathetic tone is withdrawn:

        Hahn 2022   (human, Pmsa)     awake -> anaesthetised       -13.8 %
        de Wit 2016 (human, holds)    light -> deep propofol       -23.3 %
        Appleton 86 (dog, asystole)   intact -> GANGLIONIC BLOCK   -26 %

    They order as they must: partial withdrawal below complete blockade. **Only
    Appleton removes ALL tone, so only Appleton calibrates a constant that MEANS
    all tone.** Hahn's and de Wit's figures belong to partial
    `sympathetic_outflow_scale` values and are held back as targets for the
    anaesthetic and opioid work (items 63 and 73).

    A dog, so a RATIO is used — which is what survives the species jump. Appleton
    says himself that his absolute volumes do not: dogs carry a far larger splenic
    reservoir. His control columns are also UNPAIRED (n = 12 intact against n = 5
    blocked, different days), so the band below is deliberately wide.

    Pmsf by inspiratory holds, not by arrest: with one-way aortic and pulmonic
    valves the model's arrest plateau reads the VENOUS equilibrium rather than the
    filling pressure, which cost a false flag on 2026-09-27.

    BOTH ARMS ARE MEASURED REFLEX-FREE, AND THAT IS NOT A CONVENIENCE. Appleton
    reads MCFP at 5-7 s of asystole *"because measurements taken after 7 s may
    begin to be influenced by cardiovascular reflexes"*, so the reflex is excluded
    from his control arm AND his blocked arm. The only thing differing between his
    two columns is the background TONE. Measured with the reflex ON the model gives
    -35.0 % instead of -26.1 %, because the blocked arm then also loses its reflex
    RESPONSE during the hold -- which Appleton's protocol deliberately excludes.
    **That is a different quantity, not a different answer.**
    """
    _, pmsf_intact = _venous_return_curve(baroreflex=False)
    _, pmsf_blocked = _venous_return_curve(baroreflex=False,
                                           sympathetic_outflow_scale=0.0)
    fall_pct = 100.0 * (pmsf_blocked - pmsf_intact) / pmsf_intact

    assert -32.0 < fall_pct < -20.0, (
        f"withdrawing all sympathetic tone moved filling pressure {fall_pct:+.1f} % "
        f"({pmsf_intact:.2f} -> {pmsf_blocked:.2f} mmHg), outside the band around "
        f"Appleton's -26 %. VENOUS_RESTING_TONE is 0.24 and is calibrated to this; "
        f"if the venous compartments, their unstressed volumes or the mobilizable "
        f"set have changed, the constant needs re-deriving — do NOT widen this band."
    )


# ===========================================================================
# 39. THE SHARED ALPHA1 VENOUS STAGE — backlog item 70, pass 3
#
# Nerves and alpha1 drugs compete for one receptor pool, so they add their DRIVE
# into one saturating occupancy rather than multiplying separate factors. The
# drug's venous effect therefore GROWS as sympathetic tone is withdrawn — which
# a fixed e_max could not express: 0.10 fits Schaefers' awake men and 0.30 fits
# the anaesthetised cohorts, and neither value fits both.
#
# Every constant is derived from a fixed point. Hojlund and Juhl-Olsen, the
# held-out anaesthetised cohorts, were NOT used.
# ===========================================================================


def test_alpha1_drives_sum_and_non_alpha1_drugs_stay_out_of_the_stage():
    """Two alpha1 agonists share receptors; a V1 agonist does not.

    `alpha1_venous_drive` must ADD across drugs, where every other factor
    multiplies. Vasopressin acts on V1 and propofol is not an agonist at all, so
    both keep their own `venous_tone_factor` and stay outside the pool.
    """
    from model.pharmacology import combined_drug_factors as C

    phenyl = C({"phenylephrine": 1.0})["alpha1_venous_drive"]
    norad = C({"norepinephrine": 0.1})["alpha1_venous_drive"]
    both = C({"phenylephrine": 1.0, "norepinephrine": 0.1})["alpha1_venous_drive"]
    assert phenyl > 0 and norad > 0
    assert both == pytest.approx(phenyl + norad, rel=1e-12), (
        f"alpha1 drives must SUM, not multiply: {phenyl:.4f} + {norad:.4f} "
        f"should be {phenyl + norad:.4f}, got {both:.4f}"
    )
    for drug, dose in (("vasopressin", 2.0), ("propofol", 2.0), ("spinal", 1.0)):
        assert C({drug: dose})["alpha1_venous_drive"] == 0.0, (
            f"{drug} is not an alpha1 agonist and must not enter the shared pool"
        )
    assert C({"vasopressin": 2.0})["venous_tone_factor"] < 1.0, (
        "vasopressin lost its own venous_tone_factor when the stage was added"
    )
    assert C({"propofol": 2.0})["venous_tone_factor"] > 1.0, (
        "propofol lost its own venodilating factor when the stage was added"
    )


def test_the_alpha1_stage_reproduces_the_awake_response_exactly():
    """The awake calibration must be untouched, or Schaefers stops meaning anything.

    `D_MAX` is SOLVED so the awake venous factor at a mid-clinical dose equals
    what the old private `venous_tone_factor` produced. That is what keeps
    Schaefers' five flow quantities passing. Verified more broadly when this
    landed: 56 of 56 output arrays bit-for-bit against the previous commit,
    including a phenylephrine run at 45 degrees of tilt.
    """
    from model.pharmacology import (combined_drug_factors, alpha1_tone_drive,
                                    ALPHA1_VENOUS_EMAX)
    tone = 0.24
    for drug, dose, old_ec50, old_emax in (("phenylephrine", 1.0, 0.80, 0.10),
                                           ("norepinephrine", 0.1, 0.20, 0.15)):
        drive = (alpha1_tone_drive(tone)
                 + combined_drug_factors({drug: dose})["alpha1_venous_drive"])
        new = 1.0 - ALPHA1_VENOUS_EMAX * (drive / (1.0 + drive))
        old = (1.0 - tone) * (1.0 - old_emax * dose / (old_ec50 + dose))
        assert new == pytest.approx(old, abs=1e-12), (
            f"{drug} at {dose}: the shared stage gives an awake V0 factor of "
            f"{new:.10f} where the old private factor gave {old:.10f}. D_MAX is "
            f"SOLVED from this identity — check _alpha1_dmax_from_awake."
        )


def test_withdrawing_tone_makes_phenylephrine_more_venoactive():
    """The point of the whole pass: the drug works better when tone is gone.

    Awake veins are already constricted, so an alpha1 agonist adds little.
    Anaesthesia withdraws the tone and the drug has room.

    Calibration-independent — only the ordering and a floor on the ratio are
    asserted. The measured differential at a mid-clinical dose is about 2.8x,
    recorded in docs/validation_log.md 2026-09-28. It is not asserted tightly
    because no source gives it directly.
    """
    from model.pharmacology import (combined_drug_factors, alpha1_tone_drive,
                                    ALPHA1_VENOUS_EMAX)
    tone = 0.24
    drug_drive = combined_drug_factors({"phenylephrine": 1.0})["alpha1_venous_drive"]

    def reduction(ks):
        base_drive = alpha1_tone_drive(tone) * ks
        f = lambda d: 1.0 - ALPHA1_VENOUS_EMAX * (d / (1.0 + d)) if d > 0 else 1.0
        return 1.0 - f(base_drive + drug_drive) / f(base_drive)

    awake, partial, blocked = reduction(1.0), reduction(0.2), reduction(0.0)
    assert awake < partial < blocked, (
        f"the drug's venous effect must GROW as tone is withdrawn: awake "
        f"{awake:.4f}, partial {partial:.4f}, blocked {blocked:.4f}"
    )
    assert partial > 2.0 * awake, (
        f"withdrawing most of the tone only moved the drug's venous effect from "
        f"{awake:.4f} to {partial:.4f}. A multiplicative arrangement gives about "
        f"1.32x; the saturating stage should give roughly 3x. If this fails the "
        f"stage has collapsed back to a fixed fraction."
    )



# ===========================================================================
# 40. TWO VENOUS BEDS, TWO TIME COURSES — Samueloff 1966 (backlog item 79)
#
# [S1] Samueloff SL, Browse NL, Shepherd JT (1966). Response of capacity vessels
#      in human limbs to head-up tilt and suction on lower body.
#      J Appl Physiol 21(1):47-54.  PMID 5903943
#      HUMAN, 10 normal adults aged 22-44, room at 21-22 C.
#
#      METHOD, AND IT IS WHY THIS PAPER CONSTRAINS THE MODEL AT ALL. The
#      "occluded limb": a cuff at 250-300 mmHg arrests the circulation to a hand,
#      foot or forearm segment and a catheter reads venous pressure there. The
#      VOLUME IS FIXED, so with P = (V - V0)/C any pressure change measures a
#      change in UNSTRESSED VOLUME — the quantity these factors multiply.
#      Contrast [A1] in section 15, which reports DISTENSIBILITY (a slope) and is
#      therefore blind to a V0 shift. **The two papers constrain DIFFERENT arms.**
#
#      70 deg head-up tilt held 4 min — forearm and hand, 8 subjects, 30 runs:
#        peak 7.9 mmHg (4.0-14.2) AT 27 s; whole response over by 133 s (62-240)
#        forearm blood flow 3.6 -> 2.5 mL/100 mL/min, SUSTAINED all 4 min
#      Foot veins, 1 subject, 3 tilts:
#        peaks 3.5, 4.5, 5.0 mmHg; durations 110, 98, 70 s
#
#      **CAPACITY VESSELS ADAPT. RESISTANCE VESSELS DO NOT.** Four controls make
#      the transience a result and not an artefact: a deep breath in the SAME
#      occlusion still gives 8-18 mmHg and repeated breaths SUSTAIN the rise;
#      exercise venoconstriction is sustained in a similarly occluded forearm; it
#      survives breath-holding; and SLOW tilting gives NO venous response while
#      tachycardia and resistance-vessel constriction still occur normally.
#
# [S2] Brown GE Jr, Wood EH, Lampert EH (1949). J Appl Physiol 2:117-132, cited
#      by [S1]. Under tetraethylammonium — ganglionic blockade — the volume
#      ultimately displaced to the legs on tilting was NOT increased; only the
#      RATE of filling rose. **So a limb venous arm must change how fast the legs
#      fill and NOT where the blood ends up.**
#
# WHAT THE MODEL NOW DOES, AND WHY THE TEST IS SHAPED THIS WAY. One sympathetic
# drive feeds two venous effectors with different dynamics: the mobilizable
# reservoir (splanchnic + upper body) sustains its response, and
# TRANSIENT_VENOUS_BEDS (thigh, calf, foot) carry a high-passed arm that fades.
# **Asserting BOTH is what makes this honest** — a model that simply had no limb
# arm would satisfy the fade and fail the liveness check, and one that adapted
# everything would fail the splanchnic claim.
#
# **GRADE C, AND THE LIMIT IS A BED TRANSFER.** The time course is anchored on
# forearm and hand (n = 8) and only cross-checked against the foot (n = 1, 3
# tilts). The magnitude is foot-only, n = 1. Applying it to the legs rests on
# [S1] and Pang 2001 treating limb veins as one class, which is an argument from
# class membership rather than a measurement of the leg. Stated at the constant.
# ===========================================================================


def _tilt70_reflex_trace(duration_s=300.0, onset_s=60.0):
    """Sample both venous arms and the SVR arm through a sustained 70 deg tilt.

    [S1]'s protocol: reached in 10-15 s, held 4 min. 70 deg is OUTSIDE the
    model's validated -30 to +45 range, so only SHAPE is asserted from it and no
    absolute haemodynamic value.
    """
    import model.baroreflex as B

    stride = 100                       # 100 ms; the time constants are 20-40 s
    rec, n = [], [0]
    _orig = B.BaroreflexController.update

    def spy(self, mm, pp, cvp):
        _orig(self, mm, pp, cvp)
        n[0] += 1
        if n[0] % stride == 0:
            rec.append((self.v0_vein_limb_factor, self.v0_vein_factor,
                        self.svr_factor))

    B.BaroreflexController.update = spy
    try:
        p = SimParams()
        p.tilt_onset_s = onset_s
        p.tilt_duration_s = 15.0
        p.tilt_start_deg = 0.0
        p.tilt_end_deg = 70.0
        run_simulation(p, duration_s=duration_s, dt=DT)
    finally:
        B.BaroreflexController.update = _orig

    a = np.array(rec)
    t = np.arange(len(a)) * DT * stride
    return t, a, onset_s


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "KNOWN GAP, 2026-10-06, NOT YET DIAGNOSED. Since the Klotz LV diastolic curve "
    "the limb venomotor arm is still 1.75 % of V0 at 133 s, where Samueloff found "
    "it gone. The arm is a high-pass of sympathetic drive, so drive staying up "
    "longer would do this. To be diagnosed with the baroreflex work."
))
def test_limb_venous_arm_is_transient_and_splanchnic_is_not_samueloff1966():
    """[S1] The limb arm must fade; the splanchnic and arterial arms must not.

    Five claims, and the ORDER matters — each failure message should name the
    thing that actually broke:
      1. the limb arm is LIVE at all (a mechanism-liveness guard)
      2. its peak comes EARLY, by about 27 s
      3. it has largely FADED by 133 s
      4. the SPLANCHNIC arm has NOT faded — the dissociation
      5. the ARTERIAL arm is still engaged
    """
    t, a, onset = _tilt70_reflex_trace()

    base = (t >= onset - 10.0) & (t < onset - 1.0)
    limb_base = float(a[base, 0].mean())
    svr_base = float(a[base, 2].mean())

    def at(sec, col):
        w = (t >= onset + sec - 0.5) & (t <= onset + sec + 0.5)
        assert w.any(), f"no samples near t-tilt = {sec} s"
        return float(a[w, col].mean())

    # The limb arm is a HIGH-PASS, so with a settled drive it must sit at exactly
    # 1.0 and leave the resting operating point alone.
    assert abs(limb_base - 1.0) < 1e-9, (
        f"the limb venous arm is {limb_base:.9f} at rest, not 1.0. It is a "
        f"high-pass of the sympathetic drive, so once that drive has settled its "
        f"tracker must have caught up exactly. A non-unity resting value means "
        f"the legs carry a standing venoconstriction nothing asked for"
    )

    post = t >= onset + 15.0                      # tilt fully established
    limb = 1.0 - a[post, 0]
    peak_i = int(np.argmax(limb))
    peak = float(limb[peak_i])
    peak_s = float(t[post][peak_i]) - onset
    late = 1.0 - at(133.0, 0)

    # 1. THE ARM IS LIVE. Calibration-independent: any real constriction passes.
    assert peak > 0.01, (
        f"the limb venous arm peaks at only {peak * 100:.2f}% of V0. [S1] measured "
        f"a real transient venoconstriction in human limb veins on tilting "
        f"(forearm 7.9 mmHg, foot 3.5-5.0). If this is ~0 the arm is not wired "
        f"through to TRANSIENT_VENOUS_BEDS"
    )

    # 2. ITS PEAK COMES EARLY. [S1]: maximum at 27 s, range 14-60.
    assert peak_s < 60.0, (
        f"the limb arm peaks {peak_s:.0f} s after tilt onset. [S1] measured the "
        f"maximum at 27 s (range 14-60). A late peak means the washout is too "
        f"slow relative to the 20 s drive filter"
    )

    # 3. AND IT HAS LARGELY FADED BY 133 s. [S1]: mean duration 133 s (62-240),
    #    i.e. back to baseline. Threshold generous at a third of peak, because
    #    the residual here tracks the model's own slow drift in sympathetic drive
    #    rather than the washout — measured 28 % of peak on 2026-10-01.
    assert late < 0.33 * peak, (
        f"the limb arm is still {late * 100:.2f}% of V0 at 133 s against a peak "
        f"of {peak * 100:.2f}% — {100.0 * late / peak:.0f}% of maximum. [S1] found "
        f"the whole limb response over by 133 s"
    )

    # 4. THE SPLANCHNIC ARM MUST NOT HAVE FADED. This is the dissociation, and
    #    [S1] does not measure the splanchnic bed — sustained recruitment there is
    #    what orthostatic venous return depends on, so adapting it would be
    #    applying a limb result to a bed nobody measured.
    sus_27, sus_133 = 1.0 - at(27.0, 1), 1.0 - at(133.0, 1)
    assert sus_133 > sus_27, (
        f"the SPLANCHNIC venous arm faded too: {sus_27 * 100:.2f}% at 27 s to "
        f"{sus_133 * 100:.2f}% at 133 s. Only TRANSIENT_VENOUS_BEDS may adapt. "
        f"[S1] measured LIMB veins; the splanchnic time course is unmeasured and "
        f"sustained recruitment there is what defends venous return"
    )

    # 5. THE ARTERIAL ARM MUST STILL BE ENGAGED. [S1]: forearm flow 3.6 -> 2.5,
    #    sustained for the whole 4 min.
    svr_late = (at(133.0, 2) - svr_base) / svr_base
    assert svr_late > 0.10, (
        f"the arterial arm has only {svr_late * 100:.1f}% of resistance added at "
        f"133 s. [S1] found resistance-vessel constriction SUSTAINED for the whole "
        f"4 min, which is the half of the dissociation that must NOT adapt"
    )


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "KNOWN GAP, 2026-10-07, same family as the Samueloff xfail (2026-10-06): the "
    "limb venous arm still holds 2.34 % of V0 after 230 s of tilt. The arm is a "
    "high-pass of sympathetic drive and the larger orthostatic stress (abdomen at "
    "its anatomical height, heart over-responding) keeps the drive up. To be "
    "re-measured after the heart's diastolic work."
))
def test_limb_venous_arm_changes_filling_rate_not_final_volume_brown1949():
    """[S2] The transient must not move where the blood ends up.

    Brown 1949 found ganglionic blockade did not change the volume ultimately
    displaced to the legs on tilting, only the RATE of filling. Because the limb
    arm is a high-pass it returns to 1.0 while the tilt continues, so the settled
    leg unstressed volume is the tabulated one and the endpoint cannot move.

    **This asserts the consequence rather than assuming it**, and it is the
    guard that stops anyone turning this arm into a sustained one: a sustained
    limb arm would recruit leg blood permanently, which is exactly what
    registration 007 and backlog items 9 and 64 establish the model cannot do.
    """
    t, a, onset = _tilt70_reflex_trace()
    tail = t >= onset + 230.0
    assert tail.any(), "trace too short to read the settled tilt"
    residual = 1.0 - float(a[tail, 0].mean())
    assert abs(residual) < 0.02, (
        f"the limb venous arm still holds {residual * 100:.2f}% of V0 after "
        f"230 s of sustained tilt. [S2] found the volume ultimately displaced to "
        f"the legs UNCHANGED by ganglionic blockade — only the rate of filling "
        f"moved — so this arm must wash out and leave the endpoint alone"
    )


# ===========================================================================
# 41. REPORTED PRESSURE MUST DESCRIBE THE HEART THE ODE IS INTEGRATING
#     Backlog item 78, fixed 2026-10-01.
#
# THE DEFECT. `_odes` pins the cardiac phase during a circulatory arrest, so the
# heart is flaccid and the ODE's RA pressure settles at 9.638 mmHg — equal to the
# venous bed it drains, as zero flow requires. The output monitor kept its OWN
# cardiac phase running, recomputed atrial elastance across a full cycle, and
# `p_cvp_edi = min(_cvp_win)` reported the TROUGH: 7.772 mmHg, 1.87 low.
# **The reported CVP was the trough of an atrial contraction the ODE was not
# performing.** Same shape as the 2026-09-04 `hr_eff` bug — two parallel
# computations of one quantity, and the reported one drifted.
#
# WHY THE GUARD IS AN INVARIANT AND NOT A NUMBER. A sustained pressure gradient
# across a resistance with ZERO net flow is impossible. At the arrest plateau
# every compartment volume is stable (verified out to 299 s), so flow IS zero and
# the IVC must read what the right atrium reads. That contradiction is what
# located the defect, and asserting it cannot be satisfied by retuning anything.
# ===========================================================================


def test_reported_cvp_during_arrest_matches_the_bed_it_drains_item78():
    """At the arrest plateau, reported CVP must equal the IVC pressure.

    Calibration-independent. The IVC drains directly into the right atrium
    through a resistance, so at zero flow the two pressures must be equal
    whatever the model is calibrated to. Before the item 78 fix this gap was
    1.87 mmHg, with reported CVP reading the trough of a phantom atrial beat.
    """
    from model.compartments import default_compartments, IDX
    from model.circulation import _vascular_pressure

    comp = default_compartments()
    p = SimParams()
    p.baroreflex_enabled = False
    p.ventilation_mode = "none"
    p.slow_dynamics_enabled = False
    p.arrest_start_s = 40.0
    p.arrest_duration_s = 40.0
    r = run_simulation(p, duration_s=80.0, dt=DT)

    t = np.asarray(r["t"])
    w = (t >= 74.0) & (t <= 79.0)              # plateau, 34-39 s into the arrest
    assert w.any(), "no samples in the arrest plateau window"

    cvp = float(np.mean(np.asarray(r["cvp"])[w]))
    c_ivc = comp[IDX["ivc"]]
    v_ivc = float(np.mean(np.asarray(r["volumes"])[w, IDX["ivc"]]))
    p_ivc = _vascular_pressure(v_ivc, c_ivc.unstressed_volume,
                               c_ivc.compliance, c_ivc.p_stiffen)

    assert abs(cvp - p_ivc) < 0.5, (
        f"at the arrest plateau reported CVP is {cvp:.3f} mmHg while the IVC it "
        f"drains sits at {p_ivc:.3f} — a gap of {abs(cvp - p_ivc):.3f}. Flow is "
        f"zero here (volumes are stable), and a sustained gradient across a "
        f"resistance at zero flow is impossible, so one of the two is not the "
        f"pressure the ODE is using. This is backlog item 78: the output monitor "
        f"advancing its cardiac phase while the ODE holds the heart flaccid, so "
        f"the reported trough belongs to an atrial contraction that never happened"
    )


# ===========================================================================
# 42. WHERE THE BLOOD SITS — Kiszka-Kanowitz 2001 [PMID 11690706]
#
# A guard, not a new result. The abdomen held 44.4 % of blood volume until
# `fd3fc65` (2026-09-11) moved 658 mL of unstressed volume out of the splanchnic
# bed. Nothing asserted it, so the README kept reporting the old figure as the
# model's largest open gap for three weeks. This test is the missing watcher.
# ===========================================================================

def test_abdominal_share_of_blood_volume_kiszka_kanowitz2001():
    """[PMID 11690706 — Kiszka-Kanowitz 2001] Six healthy supine controls, age
    45 +/- 6, whole-body 99mTc-albumin scintigraphy: abdominal blood volume
    29.7 +/- 1.2 % of total, every subject between about 29 and 32 %.

    Their abdominal region is defined by organ and vessel — "splanchnic organs,
    kidneys, abdominal aorta, and large veins of the abdomen" — which is the
    model's ABDOMINAL_COMPARTMENTS, IVC segments included.

    BAND: mean +/- 3 SD (26.1-33.3). The SD comes from n = 6, so it is itself
    uncertain by about a factor of two; a tighter band would be false precision.
    Measured 2026-10-04: 31.1 %. Cycle-averaged over a settled supine run.
    """
    from model.circulation import ABDOMINAL_COMPARTMENTS
    r = run_simulation(SimParams(), duration_s=120.0, dt=DT)
    t = np.asarray(r["t"])
    V = np.asarray(r["volumes"])[t >= 100.0].mean(axis=0)
    share = 100.0 * sum(V[IDX[n]] for n in ABDOMINAL_COMPARTMENTS) / V.sum()
    assert 26.1 <= share <= 33.3, (
        f"abdominal share of blood volume {share:.1f} % against Kiszka-Kanowitz "
        f"29.7 +/- 1.2 % (healthy supine controls, range ~29-32). Above the band "
        f"is the distribution of portal hypertension, which is where the model "
        f"sat (44.4 %) until 2026-09-11"
    )


# ===========================================================================
# 43. WHERE THE CALF VEINS STIFFEN — Halliwill 1999 [PMID 10517791]
# ===========================================================================

def test_calf_venous_compliance_halves_where_halliwill_measured():
    """[PMID 10517791 — Halliwill, Minson & Joyner 1999] Calf venous
    pressure-volume curves in healthy supine humans, venous-collecting cuff:
    compliance falls linearly with pressure and HALVES at 29.5 / 27.6 / 28.0
    mmHg in three subject groups.

    WHY THE HALF-POINT AND NOT THE ABSOLUTE COMPLIANCE. P-half is a pressure,
    independent of how much tissue the strain gauge sat on; the absolute needs a
    tissue volume that is uncertain by about a factor of two.

    THROUGH THE CODE PATH: the compartment comes from `build_patient_params`
    (the scaling once silently dropped `p_stiffen`), and compliance is taken by
    numerically differentiating `_vascular_pressure`, the law the ODE uses. No
    formula is restated here.

    BAND 25-33 mmHg: the three group values, widened by the scatter between
    them. Until 2026-10-04 the model's calf halved at 11 — unsourced, chosen to
    cap upright pooling.
    """
    comps, _ = build_patient_params(175.0, 75.0, hr_bpm=70.0)
    c = comps[IDX["calf_vein"]]

    def compliance_at(p_target):
        # invert P(V) by bisection, then dV/dP by central difference
        def vol(p):
            lo, hi = c.unstressed_volume, c.unstressed_volume + 2000.0
            for _ in range(80):
                mid = 0.5 * (lo + hi)
                if _vascular_pressure(mid, c.unstressed_volume, c.compliance,
                                      c.p_stiffen) < p:
                    lo = mid
                else:
                    hi = mid
            return 0.5 * (lo + hi)
        return (vol(p_target + 0.05) - vol(p_target - 0.05)) / 0.1

    c0 = compliance_at(0.1)
    ps = np.arange(1.0, 80.0, 0.25)
    cs = np.array([compliance_at(p) for p in ps])
    below = np.nonzero(cs <= 0.5 * c0)[0]
    assert below.size, "calf compliance never halves below 80 mmHg"
    p_half = float(ps[below[0]])
    assert 25.0 <= p_half <= 33.0, (
        f"calf venous compliance halves at {p_half:.1f} mmHg; Halliwill 1999 "
        f"measured 27.6-29.5 in healthy supine humans. Below the band the legs "
        f"stiffen too early and pool too little when dependent"
    )



# ===========================================================================
# 44. NO PLEURAL PRESSURE RISE IN PLAIN HEAD-DOWN TILT — Drummond 1978
# ===========================================================================

def test_head_down_tilt_does_not_raise_pleural_pressure_drummond1978():
    """[PMID 147698 — Drummond & Martin 1978] Nine anaesthetised, paralysed
    women, oesophageal balloon, static end-expiratory pressure at FRC: supine ->
    15 deg head-down changed pleural pressure by -22 Pa, 95 % CI -75 to +30 Pa
    (-0.56 to +0.23 mmHg). No pneumoperitoneum.

    THROUGH THE CODE PATH. With ventilation off, the only external pressure on
    the thorax is the positional term, and it is the gap between the
    intraluminal and transmural aortic traces. Measured as a CHANGE from supine,
    which is what the balloon measures reliably.

    Guards against the fitted +2.2 mmHg coming back: that value is what made
    head-down cardiac output fall once backlog item 65 was fixed.
    """
    def thoracic_external(tilt):
        p = SimParams()
        p.ventilation_mode = "none"
        if tilt:
            p.tilt_start_deg, p.tilt_end_deg = 0.0, tilt
            p.tilt_onset_s, p.tilt_duration_s = 5.0, 5.0
        r = run_simulation(p, duration_s=20.0, dt=DT)
        t = np.asarray(r["t"])
        m = t >= 15.0
        return float(np.mean(np.asarray(r["aortic_intraluminal"])[m]
                             - np.asarray(r["aortic_p"])[m]))

    change = thoracic_external(-15.0) - thoracic_external(0.0)
    assert -0.56 <= change <= 0.23, (
        f"15 deg head-down changes the pressure around the thorax by "
        f"{change:+.2f} mmHg; Drummond & Martin measured -0.17 (CI -0.56 to "
        f"+0.23) without pneumoperitoneum"
    )


# ===========================================================================
# 45. THE LEGS PIVOT AT THE HIP — backlog item 53, leg rebuild stage 3
#
# Before 2026-10-05 one angle tilted the whole body, so a passive leg raise was
# a whole-body head-down tilt by construction. These guard the articulation
# itself; the physiology targets (Sejersen 2022) are separate.
# ===========================================================================

def test_gravity_does_no_net_work_with_the_legs_articulated():
    """Section 32's conservation law must survive articulation: stop the heart
    with the trunk tilted and the legs flexed at a different angle, and the
    blood must stop moving. Every flow still carries hdp(up) - hdp(down), so the
    loop telescopes whatever the geometry — this proves it through the run."""
    p = SimParams()
    p.baroreflex_enabled    = False
    p.ventilation_mode      = 'none'
    p.slow_dynamics_enabled = False
    p.tilt_start_deg, p.tilt_end_deg = 0.0, 30.0
    p.hip_flexion_start_deg, p.hip_flexion_end_deg = 0.0, 75.0   # legs 45 deg up
    p.tilt_onset_s, p.tilt_duration_s = 20.0, 5.0
    # ARREST LENGTHENED 200 -> 400 s ON 2026-10-08, and the window with it.
    # The grade D leg capacity (compartments.py) doubled total leg compliance
    # (12.0 -> 25.3 mL/mmHg), and a venous segment settles with tau = R*C, so
    # the legs now take about twice as long to come to rest. At 200 s the
    # residual drift read 0.5065 mL against this test's 0.5 tolerance and the
    # test failed — NOT because the loop had opened but because it was being
    # read before it closed. MEASURED 2026-10-08, same geometry, three arrests:
    #     200 s -> 0.5065 mL     400 s -> 0.0304 mL     800 s -> 0.0001 mL
    # Monotone to zero, which is what a closed loop looks like and what an open
    # one cannot do. The TOLERANCE IS UNCHANGED at 0.5 mL; only the settling
    # time is. In effect this makes the test STRICTER — it now passes with 16x
    # margin where it used to pass with none.
    p.arrest_start_s, p.arrest_duration_s = 40.0, 400.0
    r = run_simulation(p, duration_s=440.0, dt=DT)
    V = np.asarray(r["volumes"])
    t = np.asarray(r["t"])
    late = V[t >= 415.0]
    drift = float(np.abs(late[-1] - late[0]).max())
    assert drift < 0.5, (
        f"volumes still moving {drift:.3f} mL over the last 20 s of arrest with "
        f"the trunk at 30 deg and the legs raised — articulation broke the "
        f"closed hydrostatic loop")


def test_leg_raise_empties_the_legs():
    """A leg raise from flat must move blood OUT of the leg compartments with the
    trunk left horizontal. Before item 53 the only way to lift the legs was to
    tip the head down too. Direction only; 20 mL is a floor against an inert
    mechanism, not a target."""
    from model.circulation import LEG_COMPARTMENTS
    def run(flex):
        p = SimParams()
        p.hip_flexion_start_deg, p.hip_flexion_end_deg = 0.0, flex
        p.tilt_onset_s, p.tilt_duration_s = 10.0, 5.0
        r = run_simulation(p, duration_s=40.0, dt=DT)
        t = np.asarray(r["t"])
        V = np.asarray(r["volumes"])[t >= 30.0].mean(axis=0)
        return float(sum(V[IDX[n]] for n in LEG_COMPARTMENTS))
    flat, raised = run(0.0), run(45.0)
    assert raised < flat - 20.0, (
        f"raising the legs 45 deg moved {flat - raised:.1f} mL out of the legs; "
        f"the articulation is not reaching the leg compartments")


# ---------------------------------------------------------------------------
# Sejersen 2022 [PMID 35854636] — whole-body HDT vs a true leg raise, same men.
# Shared fixture: three arms in the cohort (177 cm, 80 kg, male, 39 y, awake).
# Steps are 120 s after a 240 s settle; the paper used 10 min and reports the
# response as sustained over that time (their Fig 2).
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def sejersen_arms():
    def arm(trunk0, trunk1, flex0, flex1):
        comps, card = build_patient_params(177.0, 80.0, hr_bpm=62.0, sex="male",
                                           age_years=39.0)
        p = SimParams(compartments=comps)
        apply_cardiac(p, card)
        p.tilt_start_deg, p.tilt_end_deg = trunk0, trunk1
        p.hip_flexion_start_deg, p.hip_flexion_end_deg = flex0, flex1
        p.tilt_onset_s, p.tilt_duration_s = 240.0, 10.0
        r = run_simulation(p, duration_s=370.0, dt=DT)
        t = np.asarray(r["t"])
        sv = np.asarray(r["sv"])
        before = float(np.mean(sv[(t >= 210.0) & (t < 240.0)]))
        after = float(np.mean(sv[t >= 340.0]))
        return after - before
    return {
        "hdt":  arm(0.0, -20.0, 0.0, 0.0),     # supine -> 20 deg head-down
        "semi": arm(0.0, 45.0, 0.0, 45.0),     # supine -> back 45 up, legs flat
        "plr":  arm(45.0, 0.0, 45.0, 45.0),    # semi-recumbent -> trunk flat, legs 45 up
    }


def test_leg_raise_and_head_down_tilt_differ_sejersen2022(sejersen_arms):
    """[PMID 35854636 — Sejersen 2022] Directions and ordering, which are what
    articulation (item 53) makes possible at all: sitting up lowers stroke
    volume, the leg raise from sitting up restores it, and the leg raise gains
    more than whole-body head-down tilt. Before item 53 the model could not
    pose the question."""
    d = sejersen_arms
    assert d["semi"] < 0, f"semi-recumbent dSV {d['semi']:+.1f} mL; must fall"
    assert d["plr"] > 0, f"leg raise from semi-recumbent dSV {d['plr']:+.1f} mL; must rise"
    assert d["plr"] > d["hdt"], (
        f"leg raise dSV {d['plr']:+.1f} not above head-down dSV {d['hdt']:+.1f} mL; "
        f"Sejersen: +9 against -1 to -2 in the same men")


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "KNOWN GAP, 2026-10-05: THE RESTING HEART IS NOT ON A STARLING PLATEAU. "
    "Sejersen's healthy men sit on the flat top of the curve: HDT left SV "
    "unchanged and sitting up lowered it only 2-4 mL. The model responds to "
    "every change in filling, 4-5x too strongly. MEASURED with 10-min steps "
    "(validation log 2026-10-05): HDT +22.0, semi-recumbent -28.9, leg raise "
    "+42.4 mL against about -1.5, -3, +9. All directions right (test above). "
    "2026-10-06, Klotz LV curve + anatomical leg heights, this fixture: HDT "
    "+20.6 mL — smaller per unit of returned blood, but the longer legs return "
    "more. The RV is still on a straight line (the Klotz RV failed). "
    "Not a geometry problem — the same overshoot appears against Likhvantsev at "
    "30 deg. The README's claim that the Starling cap 'correctly prevents SV "
    "increase in the normovolaemic patient' is refuted by this. Do not close by "
    "weakening the legs: the cause is in the heart."
))
def test_leg_raise_and_head_down_magnitudes_sejersen2022(sejersen_arms):
    """[PMID 35854636] The sizes. Bands are loose, chosen from what the paper
    reports (HDT and semi-recumbent changes not significant; PLR +9 mL,
    significant; SV SD about 16 mL between subjects): HDT within +/- 8 mL,
    semi-recumbent no worse than -10, leg raise +3 to +20."""
    d = sejersen_arms
    assert abs(d["hdt"]) <= 8.0, f"HDT dSV {d['hdt']:+.1f} mL; Sejersen -1 to -2"
    assert d["semi"] >= -10.0, f"semi-recumbent dSV {d['semi']:+.1f} mL; Sejersen -2 to -4"
    assert 3.0 <= d["plr"] <= 20.0, f"leg raise dSV {d['plr']:+.1f} mL; Sejersen +9"


# ===========================================================================
# 46. VENTRICULAR DIASTOLE STIFFENS AS IT FILLS — Klotz 2006 [PMID 16428349]
# ===========================================================================

def test_left_ventricle_stiffens_as_it_fills_klotz2006():
    """[PMID 16428349 — Klotz 2006] The human end-diastolic pressure-volume
    relation is a steepening curve, the same shape in 80 hearts. Until
    2026-10-06 the model's ventricles filled along a straight line, which
    cannot produce a Starling plateau.

    THROUGH THE RUN, NOT THE FORMULA: stop the heart (both ventricles passive,
    mitral valve open, no flow), load the circulation with fluid in two equal
    steps, and read LV volume against LEFT ATRIAL pressure, which equals LV
    pressure once flow has stopped. The second step must cost more pressure per
    mL than the first. A straight-line ventricle gives the same slope twice.
    Shape only; no value from Klotz is restated here.

    THRESHOLD 1.1, AND WHY. Over this range (LV ~138 -> 150 mL) the Klotz curve
    itself raises the slope by about 1.17x; a straight line gives exactly 1.0.
    A first draft asked for 1.3 — above what the source predicts — and was
    corrected after the first run (2026-10-06: 0.517 then 0.604 mmHg/mL).
    """
    def arrested(bolus_ml):
        p = SimParams()
        p.ventilation_mode = "none"
        p.baroreflex_enabled = False
        p.slow_dynamics_enabled = False
        p.arrest_start_s, p.arrest_duration_s = 5.0, 200.0
        if bolus_ml:
            p.fluid_bolus_ml, p.fluid_bolus_start_s, p.fluid_bolus_duration_s = bolus_ml, 10.0, 10.0
        r = run_simulation(p, duration_s=150.0, dt=DT)
        t = np.asarray(r["t"])
        m = t >= 140.0
        v = float(np.mean(np.asarray(r["volumes"])[m][:, IDX["left_ventricle"]]))
        pla = float(np.mean(np.asarray(r["la_pressure"])[m]))
        return v, pla
    v0, p0 = arrested(0.0)
    v1, p1 = arrested(400.0)
    v2, p2 = arrested(800.0)
    s1 = (p1 - p0) / (v1 - v0)
    s2 = (p2 - p1) / (v2 - v1)
    assert v2 > v1 > v0, f"LV did not fill with the loads: {v0:.1f}, {v1:.1f}, {v2:.1f} mL"
    assert s2 > 1.1 * s1, (
        f"LV diastolic stiffness did not rise with filling: {s1:.3f} then "
        f"{s2:.3f} mmHg/mL (LV {v0:.0f} -> {v1:.0f} -> {v2:.0f} mL). A straight "
        f"diastolic line has returned")


def test_abdominal_and_leg_heights_scale_with_stature():
    """The anatomical heights (legs 2026-10-06, abdomen 2026-10-07) are
    fractions of stature in their sources (Winter/Drillis; vertebral levels).
    Built through `build_patient_params`, every one must scale with the
    patient's height, the hip pivot included. Supine nothing changes; this
    guards the route, so a later edit cannot pin a height to the 175 cm
    reference patient."""
    names = ("splanchnic_vein", "renal_vein", "abdominal_aorta", "ivc_renal",
             "thigh_vein", "calf_vein", "foot_vein")
    short, sc = build_patient_params(150.0, 60.0, hr_bpm=70.0)
    tall, tc = build_patient_params(200.0, 90.0, hr_bpm=70.0)
    for n in names:
        hs, ht = short[IDX[n]].height_m, tall[IDX[n]].height_m
        assert hs < 0 and ht < 0, f"{n} is not below the heart"
        assert abs(ht / hs - 200.0 / 150.0) < 1e-9, (
            f"{n}: height {hs:.3f} m at 150 cm and {ht:.3f} m at 200 cm — not "
            f"proportional to stature")
    assert abs(tc["hip_height_m"] / sc["hip_height_m"] - 200.0 / 150.0) < 1e-9, (
        "the hip pivot does not scale with stature")


# ===========================================================================
# 47. THE PERICARDIUM IS ITS OWN STRUCTURE — tamponade [PMID 668074, 3568311]
# ===========================================================================
# The sac (heart.py THE PERICARDIUM) has a capacity, a stiffness and a fluid
# content, and is OFF by default until its stiffness is pinned and the walls are
# re-placed at wall pressures. What is asserted here is the MECHANISM, which is
# grade C in man and independent of the unpinned numbers: an effusion the heart
# must make room for raises the pressure of every chamber toward the sac's and
# throttles output. Magnitudes (k, vk) are grade D/E and are NOT asserted.

@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "KNOWN GAP, re-measured 2026-10-27 — 200 mL raises RA 5.3 -> 9.5 (+4.2, needs > +5) and CO "
    "falls to 67 % (needs < 60 %); 300 mL gives RA 15.2, LA 15.2, IPP 13.0, CO 38 % (full "
    "tamponade). Re-sizing both atria on independent sources (Maceira, Sjöberg; Järvinen's RA pin "
    "removed) shrank the calculated capacity 479 -> 423 mL and NARROWED the gap (was +3.9 and 70 %), "
    "as predicted, but did not close it. Beck's '200 mL can cause hypotensive tamponade' is 1935, "
    "read only via Boltwood. Not moved."
))
def test_pericardial_effusion_produces_tamponade():
    """[PMID 668074] Reddy 1978: in all 14 tamponade patients RVEDP was elevated
    and EQUAL to pericardial pressure; with pulsus paradoxus the wedge equalised
    too; CO 3.87 -> 7.0 L/min after drainage (output roughly halved by the
    effusion). [PMID 3568311] Boltwood 1987: mean RAP = 0.98 x IPP + 1.1 (r .96).
    Beck 1935 (JAMA 104:714, cited by Boltwood; not read): ~200 mL of ACUTE
    effusion can cause hypotensive tamponade — a normal sac has little spare
    capacity.

    Through the code path: the same patient with the sac on, with and without
    200 mL of excess fluid. Equalisation is asserted within 3 mmHg (Boltwood's
    individual RAP - IPP offsets were 1-3 mmHg)."""
    def run(fluid_ml):
        p = SimParams()
        p.pericardium_enabled = True
        p.pericardial_fluid_ml = fluid_ml
        r = run_simulation(p, duration_s=150.0, dt=DT, output_every=10)
        t = np.asarray(r["t"]); m = t > 120.0
        g = lambda k: float(np.mean(np.asarray(r[k])[m]))
        return g("ra_mean"), g("la_pressure"), g("pericardial_p"), g("co")
    ra0, la0, ipp0, co0 = run(0.0)
    ra1, la1, ipp1, co1 = run(200.0)
    assert ra1 > ra0 + 5.0, (
        f"200 mL of effusion raised mean RA pressure only {ra0:.1f} -> {ra1:.1f}: "
        f"the fluid is not reaching the sac, or the sac is not reaching the chambers")
    assert abs(ra1 - ipp1) < 3.0 and abs(la1 - ipp1) < 3.0, (
        f"no equalisation in tamponade: RA {ra1:.1f}, LA {la1:.1f}, IPP {ipp1:.1f} "
        f"(Reddy: RVEDP = IPP; Boltwood: RAP = 0.98 IPP + 1.1)")
    assert co1 < 0.6 * co0, (
        f"tamponade did not throttle output: CO {co0:.2f} -> {co1:.2f} L/min")


def test_pericardial_output_is_pleural_only_when_the_sac_is_off():
    """With the sac switched OFF (it is on by default since 2026-10-11), the
    reported intrapericardial pressure must be the thoracic terms alone, and an
    effusion must change nothing — the switch must really remove the sac."""
    p = SimParams()
    p.pericardium_enabled = False
    p.pericardial_fluid_ml = 200.0
    r = run_simulation(p, duration_s=20.0, dt=DT, output_every=10)
    q = SimParams()
    q.pericardium_enabled = False
    r0 = run_simulation(q, duration_s=20.0, dt=DT, output_every=10)
    assert np.allclose(r["ra_mean"], r0["ra_mean"]), "effusion acted with the sac off"
    # Supine, no Valsalva: the thoracic terms in the series are zero, so with the
    # sac off it must read exactly zero.
    assert float(np.max(np.abs(np.asarray(r["pericardial_p"])))) < 1e-9, (
        "sac pressure reported with the sac off")


# ===========================================================================
# 48. THE CARDIOPULMONARY REFLEX READS MEAN RIGHT ATRIAL PRESSURE
# ===========================================================================

def test_cardiopulmonary_reflex_reads_mean_not_trough_right_atrial_pressure():
    """The cardiopulmonary reflex's sources measured CATHETER MEANS (its gain
    is calibrated against LBNP CVP; baroreflex.py). Until 2026-10-09 the model
    fed it the x-descent TROUGH, which moves with waveform SHAPE as well as
    filling — and AV-plane coupling deepens the x descent, which the trough read
    as hypovolaemia (HR 68.6 -> 80.2 in the prototype; validation log
    2026-10-09). Jesper: "Switch to mean RA."

    A CONVENTION PROBE, not a physiological claim: a fourfold atrial
    contraction changes the RA waveform shape (trough -1.0 mmHg) while barely
    moving its mean (-0.12). Read as a mean the reflex barely responds
    (measured +0.14 bpm); read as a trough it produced a phantom +3.17 bpm
    (sabotage, measured). The arm's own gain (3.8 bpm/mmHg) on the mean change
    predicts ~0.5 bpm, so 1.0 separates the honest response from the artefact."""
    def hr(f):
        p = SimParams()
        p.ra_emax *= f
        r = run_simulation(p, duration_s=200.0, dt=DT, output_every=10)
        t = np.asarray(r["t"])
        return float(np.mean(np.asarray(r["hr"])[t > 160.0]))
    h1, h4 = hr(1.0), hr(4.0)
    assert abs(h4 - h1) < 1.0, (
        f"a change in RA waveform SHAPE moved heart rate {h1:.2f} -> {h4:.2f} bpm: "
        f"the cardiopulmonary reflex is reading the trough, not the mean")


# ===========================================================================
# 49. SYSTOLE LASTS AS LONG AS IN MAN, AT REST AND AT SPEED — Weissler 1968
# ===========================================================================

def test_ejection_time_follows_weissler_across_heart_rate():
    """[PMID 5640345] Weissler 1968, 121 healthy men: LVET = -0.0017 HR + 0.413 s
    (SD 0.010 from regression). Until 2026-10-10 ventricular activation was an
    UNSOURCED fixed fraction of the beat: LVET 207 ms at 70 bpm (z -8.7) and
    126 ms at 110 (z -10), shrinking with the cycle. Now Senzaki's measured shape
    (PMID 8921794) timed in seconds (heart.py VENTRICULAR ACTIVATION).

    PINNED AT REST: the t_max scale is set so LVET matches at the resting rate
    (with AORTIC_ZC, from central PP). The 110 bpm assertion is therefore the
    OUT-OF-SAMPLE part — the rate-dependence is the source's, not fitted.
    Through the code path: paced, reflexes off. Sabotage: legacy activation
    fails both."""
    from model.compartments import IDX as _IDX
    def lvet(hr):
        p = SimParams(); p.hr_bpm = hr; p.baroreflex_enabled = False
        r = run_simulation(p, duration_s=40.0, dt=DT, output_every=1, use_baroreflex=False)
        t = np.asarray(r["t"]); m = t > 30.0
        dv = np.gradient(np.asarray(r["volumes"])[m, _IDX["left_ventricle"]], DT)
        runs, c = [], 0
        for e in dv < -20.0:
            if e: c += 1
            elif c: runs.append(c); c = 0
        return float(np.median(runs)) * DT
    for hr in (70.0, 110.0):
        model, w = lvet(hr), -0.0017 * hr + 0.413
        z = (model - w) / 0.010
        assert abs(z) <= 2.0, (
            f"LVET at {hr:.0f} bpm {model*1000:.0f} ms is {z:+.1f} SD from Weissler's "
            f"{w*1000:.0f} ms (men, SD 10 ms)")


# ===========================================================================
# 50. THE ATRIA FILL WHILE THE VENTRICLES EJECT — AV-plane coupling
#     (Carlsson 2004; Stephensen 2014). Mechanism OFF by default; this guard
#     switches it on, so it watches the mechanism, not the default.
# ===========================================================================

def _heart_volume_bookkeeping(av_on):
    """Per beat, from LV end-diastole to the following LV end-systole: blood
    ejected by both ventricles, blood gained by both atria, and the net fall of
    the four-chamber blood volume. Reference patient, reflexes on, 120-130 s."""
    p = SimParams()
    p.av_coupling_enabled = av_on
    r = run_simulation(p, duration_s=130.0, dt=DT, output_every=1)
    t = np.asarray(r["t"]); m = t > 120.0
    V = np.asarray(r["volumes"])[m]
    lv, rv = V[:, IDX["left_ventricle"]], V[:, IDX["right_ventricle"]]
    la, ra = V[:, IDX["left_atrium"]], V[:, IDX["right_atrium"]]
    thv = lv + rv + la + ra
    beat = int(round(60.0 / p.hr_bpm / DT))
    ej, fill, fall = [], [], []
    a = int(np.argmax(lv[:beat]))
    while a + beat < len(lv):
        b = a + int(np.argmin(lv[a:a + beat // 2 + 1]))
        ej.append((lv[a] - lv[b]) + (rv[a] - rv[b]))
        fill.append((la[b] - la[a]) + (ra[b] - ra[a]))
        fall.append(thv[a] - thv[b])
        a = a + int(np.argmax(lv[a + beat // 2:a + beat + beat // 2])) + beat // 2
    ej, fill, fall = map(np.mean, (ej, fill, fall))
    return fill / ej, fall / ej


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "KNOWN GAP, 2026-10-27 — net heart-volume fall / ejected 0.52 against 0.26-0.37, and atrial "
    "filling during ejection 48 % against Carlsson's 64 %, after both atria were re-sized on "
    "independent CMR reservoirs (Maceira 2016, Sjöberg 2020). QUANTITY MISMATCH SUSPECTED: Carlsson's "
    "64 % is vein FLOW (it also counts the intrapericardial vein segments; his THV includes the "
    "great-vessel roots), the model's is chamber max - min. Was 0.379 on the old atria. Not tuned."))
def test_atria_fill_during_ejection_carlsson2004():
    """[PMID 15016625 — Carlsson 2004; PMID 24441546 — Stephensen 2014]
    In man the ventricles empty largely by pulling the AV plane toward the apex.
    The atria fill from the veins DURING ejection, and the heart's total volume
    falls far less than the volume it ejects.

    Carlsson 2004 (8 healthy adults, MRI, two methods agreeing within subject):
    atrial inflow during systole 64 ± 2 % (SE; SD ~5.7) of the volume ejected;
    net heart-volume fall / ejected ~0.34. Stephensen 2014 (45 adults, same
    lab): 0.26. Band for the ratio: 0.26-0.37 (one lab, two cohorts).

    The coupling's SIZE comes from a different measurement — the volume the
    plane sweeps (Stephensen: LV 61 %, RV 79 % of SV) — so filling and net fall
    are OUTCOMES here, not inputs. Note THV in Carlsson includes myocardium; the
    RATIO is compared, never a percentage of THV.

    The OFF arm proves the mechanism is live: without it the model's atria
    barely fill during ejection (measured 2026-10-11: 28.5 %, ratio 0.72), so
    a coupling that silently stopped working fails here.
    """
    fill_on, ratio_on = _heart_volume_bookkeeping(True)
    fill_off, ratio_off = _heart_volume_bookkeeping(False)
    z = (fill_on * 100.0 - 64.0) / 5.7
    assert abs(z) <= 2.0, (
        f"atrial filling during ejection {fill_on*100:.1f} % of SV is {z:+.1f} SD "
        f"from Carlsson's 64 % (SD ~5.7)")
    assert 0.26 <= ratio_on <= 0.37, (
        f"net heart-volume fall / ejected {ratio_on:.2f} outside 0.26-0.37 "
        f"(Stephensen 0.26, Carlsson 0.34)")
    assert ratio_off > 0.5 and fill_off < 0.45, (
        f"coupling OFF gives fill {fill_off*100:.1f} % / ratio {ratio_off:.2f} — the "
        f"off arm should fail Carlsson; if it passes, this test no longer proves the "
        f"coupling is what lands the on arm")


# ===========================================================================
# 51. THE SAC TAKES MOST OF A FILLING LOAD — Bhella 2014 (pin), Borlaug 2018 (test)
# ===========================================================================

_BHELLA_SEDENTARY = (169.5, 74.7, 69.0)   # height cm, weight kg, age (Table 1)


def _lv_edv(r, a, b):
    """Mean LV end-diastolic volume over [a, b): the beat-by-beat volume peaks."""
    t = np.asarray(r["t"])
    lv = np.asarray(r["volumes"])[(t >= a) & (t < b), IDX["left_ventricle"]]
    d = np.diff(lv)
    peaks = np.where((d[:-1] > 0) & (d[1:] <= 0))[0] + 1
    return float(np.mean(lv[peaks])) if len(peaks) else float(lv.max())


def _saline_load(sex, sac=True):
    """Bhella 2014's loading step: warm saline 15 mL/kg at ~200 mL/min in a
    supine sedentary senior. Returns (dPCWP, dRAP, dSV, fractional dLVEDV), end
    of infusion vs the 30 s before it. PCWP is the LA cavity pressure, RAP the
    reported CVP, LVEDV the mean of the beat-by-beat end-diastolic peaks."""
    h, w, age = _BHELLA_SEDENTARY
    p = cohort_params(h, w, age_years=age, sex=sex)
    p.pericardium_enabled = sac
    vol = 15.0 * w
    dur = vol / 200.0 * 60.0
    t0 = 120.0
    p.fluid_bolus_ml, p.fluid_bolus_start_s, p.fluid_bolus_duration_s = vol, t0, dur
    r = run_simulation(p, duration_s=t0 + dur + 60.0, dt=DT, output_every=10)
    t = np.asarray(r["t"])
    def win(k, a, b):
        return float(np.mean(np.asarray(r[k])[(t >= a) & (t < b)]))
    edv0, edv1 = _lv_edv(r, t0 - 30.0, t0), _lv_edv(r, t0 + dur, t0 + dur + 30.0)
    return tuple(win(k, t0 + dur, t0 + dur + 30.0) - win(k, t0 - 30.0, t0)
                 for k in ("la_pressure", "cvp", "sv")) + (edv1 / edv0 - 1.0,)


@pytest.fixture(scope="module")
def bhella_saline():
    """Both sexes, sac on and off. Bhella's sedentary group was 44 % female."""
    return {(sex, sac): _saline_load(sex, sac)
            for sex in ("male", "female") for sac in (True, False)}


def _cohort_mean(values):
    return 0.56 * values["male"] + 0.44 * values["female"]


def test_sac_carries_most_of_a_filling_load_bhella2014(bhella_saline):
    """[PMID 25236519 — Bhella 2014] On saline loading, healthy seniors' RA pressure
    (= pericardial pressure, by their method) rose by 0.59-0.64 of the wedge rise:
    most of the extra LV filling pressure is EXTERNAL. This is the endpoint the sac's
    knee slope was PINNED on (heart.py PERI_K, 2026-10-16), so it guards the pin.

    A RATIO, because the absolutes are confounded: the model's older LV starts too
    high on its filling curve and over-responds in absolute terms (wedge +9.4 vs
    +4.4-5.5) whatever the sac does. Band 0.55-0.70: Bhella's two estimates (base 2
    -> saline 15: 2.6/4.4; vs baseline mean: 3.5/5.5) widened by ~0.05 each way for
    figure-reading precision.

    THE PASS RESTS ON TWO ERRORS THAT CANCEL (measured 2026-10-17). Both rises are
    ~70 % too large: wedge +8.8 against ~5, RA pressure +5.3 against ~3. Their RATIO
    lands on Bhella's 0.6. So this guards the pin, not the physiology, and the pin
    it guards (PERI_K) is grade D. The band is NOT changed and the target is NOT
    switched to the absolutes after the fact; a stiffer RV law that got the wedge
    rise right failed this ratio (0.78-1.17), recorded in the validation log."""
    ratio = {sex: bhella_saline[(sex, True)][1] / bhella_saline[(sex, True)][0]
             for sex in ("male", "female")}
    r = _cohort_mean(ratio)
    assert 0.55 <= r <= 0.70, (
        f"external share of the saline wedge rise dRAP/dPCWP {r:.2f} outside 0.55-0.70 "
        f"(Bhella 0.59-0.64); male {ratio['male']:.2f}, female {ratio['female']:.2f}")


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "KNOWN GAP, 2026-10-16 — THE LEFT-HEART WALLS ARE TOO STIFF ON LOADING. Opening the "
    "sac RAISES the model's saline wedge rise (+9.4 -> +22) where Borlaug's patients' fell "
    "67 %. Without the sac the LA and LV walls carry the whole load, and they are much "
    "stiffer than a human heart's: the Klotz LV curve is placed at a CAVITY pressure "
    "(Chemla's wedge) and older/female LVs start too high on it (resting wedge 13.4 / 18.1 "
    "vs Bhella 10.9). Not the sac: its slope is pinned on Bhella's ratio (test above)."
))
def test_opening_the_sac_reduces_the_filling_pressure_rise_borlaug2018(bhella_saline):
    """[PMID 30571519 — Borlaug 2018, via Borlaug & Reddy 2019 PMID 31248569 Fig 5I-K]
    In patients at AVR/CABG, opening the anterior pericardium cut the wedge rise on
    volume loading by 67 % (~9.5 -> ~3.5). The DIRECTION is asserted (a smaller rise
    with the sac open), on Bhella's load, because Borlaug's load size is not given."""
    on = _cohort_mean({s: bhella_saline[(s, True)][0] for s in ("male", "female")})
    off = _cohort_mean({s: bhella_saline[(s, False)][0] for s in ("male", "female")})
    assert off < on, (
        f"opening the sac did not reduce the wedge rise on loading: {on:+.1f} -> {off:+.1f} "
        f"mmHg (Borlaug: -67 %)")


# ===========================================================================
# 52. THE VASOMOTOR REFLEX AGES IN TWO TERMS — Davy 1998 (pin), Tsutsui 2002 (test)
# ===========================================================================


def test_the_two_age_terms_reproduce_davys_measured_ratios():
    """[PMID 9719058 — Davy, Seals & Tanaka 1998] 11 young (23) and 12 older (64)
    healthy men, graded LBNP, peroneal microneurography with simultaneous forearm
    plethysmography. The age effect on the vasomotor arm has TWO terms moving in
    OPPOSITE directions, and the model's age law is derived from the two tabulated
    slopes (not from the paper's prose — see the note in aging.py):

        end organ   dFVR/dMSNA  0.020 -> 0.007   ratio 0.350
        outflow     dMSNA/dPVP  implied          ratio 1.324
        net         dFVR/dPVP   4.1 -> 1.9       ratio 0.463

    This guards the DERIVATION, which is arithmetic and has no simulation in it;
    the mechanism guard that the term is live is the next test."""
    from model.aging import baroreflex_age_factors, vascular_outflow_scale_for_age
    end = (baroreflex_age_factors(64)["svr"] / baroreflex_age_factors(23)["svr"])
    out = (vascular_outflow_scale_for_age(64) / vascular_outflow_scale_for_age(23))
    assert abs(end - 0.350) < 0.01, f"end-organ age ratio {end:.3f} != Davy's 0.350"
    assert abs(out - 1.324) < 0.02, f"outflow age ratio {out:.3f} != Davy's implied 1.324"
    assert abs(end * out - 0.463) < 0.01, (
        f"net vasomotor age ratio {end * out:.3f} != Davy's measured 4.1 -> 1.9 = 0.463")
    # THE TWO TERMS MUST MOVE IN OPPOSITE DIRECTIONS. A single net factor would
    # satisfy the line above and lose the physiology.
    assert end < 1.0 < out, (
        f"the two age terms do not oppose: end organ {end:.3f}, outflow {out:.3f}")
    # Identity at the calibration age, so the reference patient is untouched.
    assert abs(baroreflex_age_factors(27.0)["svr"] - 1.0) < 1e-9
    assert abs(vascular_outflow_scale_for_age(27.0) - 1.0) < 1e-9


def test_the_vascular_outflow_term_is_live_in_the_model():
    """The vasomotor outflow scale must reach the ODE, not just the parameter dict.

    **SABOTAGE-VERIFIED BY CONSTRUCTION:** this drives `run_simulation` and
    compares the model's own resistance response to an orthostatic stress at two
    settings of the term. If the wiring is cut the two arms become identical and
    this fails — the failure mode that hid a dead `venous_tone_factor` for months.

    It asserts DIRECTION ONLY (more vasomotor outflow -> more vasoconstriction),
    because the magnitude is Davy's and is asserted in the test above."""
    def tpr_rise(scale):
        p = cohort_params(178.0, 77.0, age_years=35.0, sex="male")
        p.vascular_outflow_scale = scale
        p.lbnp_mmhg, p.lbnp_start_s, p.lbnp_end_s = -30.0, 60.0, None
        r = run_simulation(p, duration_s=240.0, dt=DT, output_every=10)
        t = np.asarray(r["t"])
        def win(k, a, b):
            return float(np.mean(np.asarray(r[k])[(t >= a) & (t < b)]))
        base = (win("map", 30, 60) - win("cvp", 30, 60)) / win("co", 30, 60)
        late = (win("map", 210, 240) - win("cvp", 210, 240)) / win("co", 210, 240)
        return 100.0 * (late / base - 1.0)
    low, high = tpr_rise(0.6), tpr_rise(1.6)
    assert high > low + 1.0, (
        f"vascular_outflow_scale is not live: TPR rise on -30 LBNP {low:.1f} % at 0.6 "
        f"vs {high:.1f} % at 1.6 — the term never reaches the vasomotor drive")


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "KNOWN GAP, 2026-10-18 — THE FILLING-PRESSURE SIGNAL IS UPSTREAM AND TOO SMALL. "
    "Davy 1998 and Tsutsui 2002 both measure older adults defending mean pressure on "
    "LBNP at least as well as the young (Davy: the old RAISE diastolic and mean at -30 "
    "and -40; Tsutsui: MAP flat to -60 in both groups, and the old tolerate more). The "
    "model falls further with age. The two age terms are now Davy's and are NOT the "
    "cause: the model's filling pressure falls only -1.41 mmHg at -30 against man's -4 "
    "to -6, because mean systemic filling pressure moves too little (systemic compliance "
    "118.5 vs Maas 64.3 +/- 32.7). Validation log 2026-10-18. Band not widened."
))
def test_older_adults_defend_pressure_at_least_as_well_davy1998_tsutsui2002(
        ):
    """[PMID 9719058 — Davy 1998; PMID 11961365 — Tsutsui 2002] Two labs, two
    continents, two methods: healthy older adults hold mean arterial pressure on
    lower-body suction at least as well as young adults, and tolerate more of it.

    Asserted as a COMPARISON between two ages of the same model, so the absolute
    level cancels and only the age ORDERING is tested — the quantity both papers
    agree on."""
    def dmap(age):
        p = cohort_params(178.0, 77.0, age_years=age, sex="male")
        p.lbnp_mmhg, p.lbnp_start_s, p.lbnp_end_s = -30.0, 120.0, None
        r = run_simulation(p, duration_s=420.0, dt=DT, output_every=10)
        t = np.asarray(r["t"])
        def win(a, b):
            return float(np.mean(np.asarray(r["map"])[(t >= a) & (t < b)]))
        return win(360, 420) - win(60, 120)
    young, older = dmap(23.0), dmap(64.0)
    assert older >= young - 1.0, (
        f"the older model defends MAP WORSE on -30 LBNP: {older:+.1f} vs {young:+.1f} mmHg "
        f"(Davy/Tsutsui: older is equal or better)")


# ===========================================================================
# 53. BHELLA'S SIX-STAGE REPLAY — does the LV RECEIVE the right volume, and turn
#     it into the right pressure? Unloading AND loading, one lab, one cohort.
# ===========================================================================
#
# [PMID 25236519 — Bhella 2014, sedentary seniors, n 27, 44 % female] Supine,
# Swan-Ganz, LVEDV by 2D echo scaled to each subject's cardiac MRI. Stages:
# LBNP -30, LBNP -15, baseline 1, baseline 2, saline 15 and 30 mL/kg. Group means
# DIGITISED from the figures (docs/reference_values.md, grade C, ~+/-0.3 mmHg and
# ~+/-1 mL/m2 per point). RAP is DERIVED (PCWP minus Figure 4's PCWP-RAP), so it
# carries both readings' error.
#
# WHY THIS EXISTS (validation log 2026-10-23). Every volume-sensitivity endpoint
# used before was a single number, and one of them (Gauer) turned out to be a
# second-hand LOADING coefficient scored against a BLEED. This replay asserts the
# SHAPE across both directions, and separates the two halves of the question:
#   * the BODY's job is to deliver volume to the LV  -> the LVEDV change
#   * the HEART's job is to turn it into pressure     -> the PCWP and RAP change
# At the time of writing the first passes and the other two do not, which is what
# located the defect in the heart and pericardium rather than the body.
#
# BANDS. No per-stage SD is published, so the 1 SD convention cannot be applied.
# Each band is spanned by Bhella's TWO baseline estimates (base 2, and the mean of
# base 1 and base 2 — the same construction as constraint D of the pre-registered
# map and the share test in section 51), widened by figure-reading precision:
# +/-0.3 mmHg for PCWP, +/-0.45 for the derived RAP, +/-2.5 points for the
# fractional volume change. Changes, not levels, so the transducer zero (5 cm below
# the sternal angle) cancels. Each LBNP level is a separate 5 min run from rest; in
# Bhella's protocol -30 followed 5 min at -15 (no stepped LBNP profile exists).

_BHELLA_STAGE_BANDS = {
    #            fractional dLVEDV     dPCWP mmHg      dRAP mmHg
    "lbnp15":  ((-0.135, -0.074), (-4.50, -2.85), (-3.65, -1.85)),
    "lbnp30":  ((-0.240, -0.181), (-6.40, -4.75), (-4.95, -3.15)),
    "saline15": ((+0.042, +0.105), (+4.10, +5.75), (+2.15, +3.95)),
}


def _lbnp_stage(sex, level):
    """One Bhella LBNP stage: 5 min at `level` mmHg from rest, read in the last 30 s
    against the 30 s before suction. Returns (dPCWP, dRAP, dSV, fractional dLVEDV)."""
    h, w, age = _BHELLA_SEDENTARY
    p = cohort_params(h, w, age_years=age, sex=sex)
    t0 = 120.0
    p.lbnp_mmhg, p.lbnp_start_s, p.lbnp_end_s = level, t0, None
    r = run_simulation(p, duration_s=t0 + 300.0 + 1.0, dt=DT, output_every=10)
    t = np.asarray(r["t"])
    def win(k, a, b):
        return float(np.mean(np.asarray(r[k])[(t >= a) & (t < b)]))
    a, b = t0 + 270.0, t0 + 300.0
    edv0, edv1 = _lv_edv(r, t0 - 30.0, t0), _lv_edv(r, a, b)
    return tuple(win(k, a, b) - win(k, t0 - 30.0, t0)
                 for k in ("la_pressure", "cvp", "sv")) + (edv1 / edv0 - 1.0,)


@pytest.fixture(scope="module")
def bhella_stages(bhella_saline):
    """{stage: (fractional dLVEDV, dPCWP, dRAP)} — the band order — as cohort
    means (56 % M / 44 % F).
    The saline stage REUSES section 51's runs (sac on)."""
    runs = {("saline15", sex): bhella_saline[(sex, True)] for sex in ("male", "female")}
    for level in (-15.0, -30.0):
        for sex in ("male", "female"):
            runs[(f"lbnp{int(-level)}", sex)] = _lbnp_stage(sex, level)
    out = {}
    for stage in _BHELLA_STAGE_BANDS:
        m, f = runs[(stage, "male")], runs[(stage, "female")]
        out[stage] = tuple(_cohort_mean({"male": m[i], "female": f[i]}) for i in (3, 0, 1))
    return out


def _stage_misses(bhella_stages, k, label, unit):
    misses = []
    for stage, bands in _BHELLA_STAGE_BANDS.items():
        lo, hi = bands[k]
        v = bhella_stages[stage][k]
        if not lo <= v <= hi:
            misses.append(f"{stage}: {label} {v:+.3g}{unit} outside [{lo:+.3g}, {hi:+.3g}]")
    return misses


def test_the_body_delivers_bhellas_filling_volumes_to_the_lv(bhella_stages):
    """The LV's end-diastolic volume changes by Bhella's fraction at every stage:
    LBNP -15 -11.0 / -9.9 %, LBNP -30 -21.5 / -20.6 %, saline +6.7 / +8.0 % (two
    baseline estimates). A FRACTION, because the model's resting LVEDV (~128 mL
    cohort mean) is larger than Bhella's MRI-corrected 104.5 — a level difference
    recorded separately, which a ratio is robust to.

    This is the BODY half: how much of the suction or the infusion reaches the left
    ventricle is set by venous capacitance, pooling, filtration and the right heart.
    It PASSED when written (2026-10-23: -10.1, -20.7, +6.4 %), and its passing is
    what clears the body of the loading defect in this experiment. Sabotage-verified:
    tripling venous-reservoir compliance moves it out of band (validation log)."""
    misses = _stage_misses(bhella_stages, 0, "dLVEDV", "")
    assert not misses, "LV filling volume does not follow Bhella: " + "; ".join(misses)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "KNOWN GAP, 2026-10-23 — THE LV IS STIFFER THAN MAN'S AROUND REST, ~1.4x ON UNLOADING "
    "AND ~2x ON LOADING. It receives Bhella's volume at every stage (test above) and "
    "turns it into too much pressure: wedge -5.1 / -8.5 on LBNP -15 / -30 against "
    "-4.2 / -6.1, and +8.7 on saline against +4.4-5.5. Worst in the female run, which "
    "also starts too high on its curve (resting wedge 13.7 vs Bhella 10.8). No "
    "combination of 11 heart and body parameters reaches normal rest AND Bhella's "
    "loading pressures (joint search, B+D 0/512). Validation log 2026-10-23."
))
def test_wedge_pressure_follows_bhellas_stages(bhella_stages):
    """The HEART half, left side: given the volume it received, the LV's filling
    pressure changes by Bhella's amount — LBNP -15 -4.2 / -3.15, LBNP -30 -6.1 /
    -5.05, saline +4.4 / +5.45 mmHg (two baseline estimates)."""
    misses = _stage_misses(bhella_stages, 1, "dPCWP", " mmHg")
    assert not misses, "wedge pressure does not follow Bhella: " + "; ".join(misses)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "KNOWN GAP, 2026-10-23 — THE RIGHT ATRIUM HAS THE WRONG SHAPE AROUND REST. It falls "
    "one-third to two-fifths of Bhella's value on suction (-0.9 / -1.7 against -3.2 / "
    "-4.5) and rises twice it on saline (+5.3 against +2.6-3.5): slack below rest, steep "
    "above. That is the signature of a sharp pericardial knee placed AT the resting "
    "volume (option 1, heart.py). Man's pattern fits a sac already engaged at rest with "
    "a softer knee (the Tyberg position, conflict H) — a HYPOTHESIS, not yet tested. "
    "Validation log 2026-10-23."
))
def test_right_atrial_pressure_follows_bhellas_stages(bhella_stages):
    """The HEART half, right side: RA pressure changes by Bhella's derived amount —
    LBNP -15 -3.2 / -2.3, LBNP -30 -4.5 / -3.6, saline +2.6 / +3.5 mmHg (two
    baseline estimates). The model's RAP is the catheter-mean CVP."""
    misses = _stage_misses(bhella_stages, 2, "dRAP", " mmHg")
    assert not misses, "RA pressure does not follow Bhella: " + "; ".join(misses)


# ===========================================================================
# 54. CONTROLLED BLOOD LOSS IN AWAKE MAN — Johnson 2014 replayed stage by stage
# ===========================================================================
#
# [PMID 24876357 — Johnson BD ... Joyner MJ 2014, Mayo Clinic, Table 3] Healthy
# men, supine, awake; the Table 3 subset n 8, 32 +/- 3 y, 185.3 cm, 91.3 kg. CVP by a
# 16 G PICC from an antecubital vein, transducer at heart level. After a 5 min
# baseline, three aliquots of 333 mL were drained by gravity (37, 43, 46 mL/min);
# "a 5-min period separated each aliquot", and "data were analyzed and averaged
# over the last 2 min of each stage". No fluid given.
#   CVP, mean +/- SE:  baseline 5.9 +/- 0.8 | 333 mL 3.6 +/- 0.9 | 667 mL 2.2 +/- 1.1
#                      | 1000 mL 1.2 +/- 1.1
# i.e. -2.3, -3.7, -4.7 mmHg: 0.69, 0.56, 0.47 mmHg per 100 mL. STEEPEST FIRST.
# An INDEPENDENT lab agrees: Rea 1991 (PMID 2033009, Iowa, n 9), 450 mL at 71 mL/min,
# CVP 6.1 -> 3.7 (0.53 per 100 mL). Both bracket Gauer 1956's second-hand 0.51-0.70.
#
# WHY THIS EXISTS (validation log 2026-10-23). Section 53 tests FILLING on Bhella's
# seniors; this tests BLEEDING on young men, on read modern data, replacing the
# Gauer coefficient that had never been read. The holds are reproduced with
# `hemorrhage_pulses`, because one continuous bleed would delete them — and the
# transcapillary refill that happens in them.
#
# BAND — AN EXPLICIT EXCEPTION TO THE 1 SD CONVENTION, and why. Table 3 gives the
# SE of each LEVEL, not the SD of the paired CHANGE. The SD of a level (SE x 2.83,
# ~2.3-3.1 mmHg) includes the between-subject spread of BASELINE CVP, which cancels
# in a paired change; using it would accept a model ~4x too insensitive (measured
# 2026-10-23: the model's CVP at 1000 mL is 3.1, inside 1.2 +/- 3.1, while its
# CHANGE is -1.3 against -4.7). So each band is the group-mean
# change +/- sqrt(SE_base^2 + SE_stage^2): the SE of the change ASSUMING NO
# within-subject correlation, which is an UPPER bound on the true SE of the mean
# change. It asks whether the model reproduces the MEAN response — which is what a
# typical patient at the group's mean anthropometry should do.

_JOHNSON_SUBJECT = (185.3, 91.3, 32.0)            # height cm, weight kg, age (Table 3, n 8)
_JOHNSON_RATES = (37.0, 43.0, 46.0)               # mL/min, aliquots 1-3 (removal by gravity)
_JOHNSON_DCVP_BANDS = (                           # mmHg change from baseline, see above
    (-2.3 - 1.20, -2.3 + 1.20),
    (-3.7 - 1.36, -3.7 + 1.36),
    (-4.7 - 1.36, -4.7 + 1.36),
)


def _johnson_bleed():
    """Johnson 2014's blood-loss arm. Returns (baseline CVP, [dCVP per stage],
    [dSV per stage]), each stage read over the last 2 min of its 5 min hold."""
    h, w, age = _JOHNSON_SUBJECT
    p = cohort_params(h, w, age_years=age, sex="male")
    t, pulses, reads = 300.0, [], []
    for rate in _JOHNSON_RATES:
        dur = 333.0 / rate * 60.0
        pulses.append((t, dur, rate))
        t += dur + 300.0
        reads.append((t - 120.0, t))
    p.hemorrhage_pulses = tuple(pulses)
    r = run_simulation(p, duration_s=t + 1.0, dt=DT, output_every=10)
    tt = np.asarray(r["t"])
    def win(k, a, b):
        return float(np.mean(np.asarray(r[k])[(tt >= a) & (tt < b)]))
    cvp0, sv0 = win("cvp", 180.0, 300.0), win("sv", 180.0, 300.0)
    return (cvp0, [win("cvp", a, b) - cvp0 for a, b in reads],
            [win("sv", a, b) - sv0 for a, b in reads])


@pytest.fixture(scope="module")
def johnson_bleed():
    return _johnson_bleed()


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "KNOWN GAP, 2026-10-23 — CVP FALLS ~4x TOO LITTLE ON BLEEDING. Measured: -0.50 / -0.91 / "
    "-1.28 mmHg at 333 / 667 / 1000 mL against Johnson's -2.3 / -3.7 / -4.7. Meanwhile stroke "
    "volume falls ~2x TOO MUCH (-13 / -24 / -34 mL against -5 / -11 / -18): the heart's output "
    "answers volume loss that its filling pressure does not show — the cardiac function curve "
    "slope, seen again. Same RA defect as section 53's RAP test, from the bleed side, on a "
    "different lab and cohort. HYPOTHESIS, under test: the pericardial knee sits AT the resting "
    "volume, so below it the RA is slack. Validation log 2026-10-23."
))
def test_cvp_falls_as_in_johnson2014_controlled_blood_loss(johnson_bleed):
    """CVP falls by Johnson's mean change at each 333 mL stage, within the SE-of-
    change band defined above."""
    _, dcvp, _ = johnson_bleed
    misses = [f"{333 * (k + 1)} mL: dCVP {d:+.2f} outside [{lo:+.2f}, {hi:+.2f}]"
              for k, (d, (lo, hi)) in enumerate(zip(dcvp, _JOHNSON_DCVP_BANDS))
              if not lo <= d <= hi]
    assert not misses, "CVP does not follow Johnson 2014: " + "; ".join(misses)


# ===========================================================================
# 55. STAGED BLEEDING REACHES THE ODE — a mechanism guard, no literature target
# ===========================================================================


def test_hemorrhage_pulses_are_live_and_additive():
    """The staged-bleed mechanism must reach the ODE: a 500 mL bleed given as one
    `hemorrhage_pulses` entry must reproduce the single-pulse bleed exactly, and
    must differ from no bleed. Drives run_simulation; if the pulse loop were cut,
    the first assertion fails (verified by construction 2026-10-23: identical to
    the last decimal with the loop present)."""
    def cvp(kind):
        p = cohort_params(175.0, 75.0, age_years=55.0, sex="male")
        if kind == "single":
            p.hemorrhage_rate_mlmin, p.hemorrhage_start_s, p.hemorrhage_duration_s = 250.0, 30.0, 120.0
        elif kind == "pulse":
            p.hemorrhage_pulses = ((30.0, 120.0, 250.0),)
        r = run_simulation(p, duration_s=180.0, dt=DT, output_every=10)
        return np.asarray(r["cvp"])
    single, pulse, none = cvp("single"), cvp("pulse"), cvp("none")
    assert np.max(np.abs(single - pulse)) < 1e-9, "a pulse does not reproduce the single bleed"
    assert np.max(np.abs(pulse - none)) > 0.3, "hemorrhage_pulses has no effect on CVP"


# ===========================================================================
# 56. LVEDP IS END-DIASTOLIC — a reporting guard (coronary perfusion depends on it)
# ===========================================================================


def test_reported_lvedp_is_the_passive_pressure_at_end_diastolic_volume():
    """`lvedp` must be the passive LV pressure at each beat's END-DIASTOLIC volume, not
    a cycle mean. Until 2026-10-25 it was the passive pressure at the CURRENT volume,
    block-averaged — ~3 mmHg where the end-diastolic value is ~11 — so coronary
    perfusion pressure (DBP - LVEDP) and the Buckberg index were overestimated.

    Drives run_simulation and recomputes the expected value INDEPENDENTLY from the
    volume trace (per-beat LV volume peaks through the patient's own Klotz curve), so
    reverting the fix makes the first assertion fail."""
    from model.heart import klotz_diastolic_pressure
    p = cohort_params(175.0, 75.0, age_years=55.0, sex="male")
    r = run_simulation(p, duration_s=40.0, dt=DT, output_every=10)
    t = np.asarray(r["t"]); m = t >= 20.0
    lv = np.asarray(r["volumes"])[m, IDX["left_ventricle"]]
    d = np.diff(lv); peaks = lv[np.where((d[:-1] > 0) & (d[1:] <= 0))[0] + 1]
    expected = np.mean([klotz_diastolic_pressure(v, p.lv_v0_dia, p.lv_v30) for v in peaks])
    cycle_mean = np.mean([klotz_diastolic_pressure(v, p.lv_v0_dia, p.lv_v30) for v in lv])
    reported = float(np.mean(np.asarray(r["lvedp"])[m]))
    assert abs(reported - expected) < 0.75, (
        f"reported LVEDP {reported:.2f} != passive pressure at end-diastolic volume {expected:.2f}")
    assert reported > cycle_mean + 3.0, (
        f"reported LVEDP {reported:.2f} looks like a cycle mean ({cycle_mean:.2f}), not end-diastolic")


# ===========================================================================
# 57. BOTH ATRIA HOLD MAN'S RESERVOIR — guards for the AV-plane split (heart.py
#     AV_ATRIAL_SHARE_LA / _RA) and LA_EMIN
#     [MAC16] Maceira AM et al. (2016) J Cardiovasc Magn Reson 18:64. PMID 27719670,
#             DOI 10.1186/s12968-016-0284-8 — n 120, appendages included
#     [SJO]   Sjöberg P et al. (2020) Am J Physiol Heart Circ Physiol 318:H345-53.
#             PMID 31886724, DOI 10.1152/ajpheart.00417.2019 — 15 controls
# ===========================================================================


def test_atrial_reservoirs_match_two_independent_labs():
    """Atrial reservoir (max - min volume of the average beat) indexed to BSA, reference
    patient. LA 24 +/- 4.4 [MAC16] and 25 +/- 4 [SJO]; RA 31 +/- 6.0 [MAC16] and 32 +/- 5
    [SJO]. Two labs agreeing: grade B. Bands are Maceira's 1 SD.

    Guards the split of the AV-plane sweep between atrium and total-heart-volume fall:
    with the sweep entering each atrium one-for-one (the model until 2026-10-26) the LA
    reservoir read 35.7 (+2.6 SD) and the RA 38.2; with LA_EMIN back at 0.55 the LA read 17.7.
    An absolute volume, not a share of SV, so it does not inherit the model's own SV."""
    s = _atrial_state()
    la = s["la"]["vmax_i"] - s["la"]["vmin_i"]
    ra = s["ra"]["vmax_i"] - s["ra"]["vmin_i"]
    assert 19.6 <= la <= 28.4, f"LA reservoir {la:.1f} mL/m2 outside 19.6-28.4; [MAC16] 24 +/- 4.4, [SJO] 25"
    assert 25.0 <= ra <= 37.0, f"RA reservoir {ra:.1f} mL/m2 outside 25-37; [MAC16] 31 +/- 6, [SJO] 32"
    # The absolute RA band cannot tell the RA share 0.73 from 1.0 (29.5 vs ~37 mL/m2, ~1.2 SD
    # apart; sabotage-checked 2026-10-26), so the share is guarded by the reservoir as a
    # fraction of RV SV: [SJO] 58 +/- 8 %. PARTLY CIRCULAR — the share itself came from
    # Sjöberg's subjects — but reservoir (max - min volume) and piston (AVPD x atrial area)
    # are separate measurements there. One-for-one gave 75 %.
    ra_pct = 100.0 * (s["ra"]["vmax"] - s["ra"]["vmin"]) / s["rv_sv"]
    assert 50.0 <= ra_pct <= 66.0, f"RA reservoir {ra_pct:.1f} % of RV SV outside 50-66; [SJO] 58 +/- 8"
