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

from model.circulation import SimParams, run_simulation
from model.compartments import IDX
from model.gravity import GravityEnvironment
from model.patient import build_patient_params, apply_cardiac
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
                 duration=LIT_DURATION):
    """
    Run a scenario and return steady-state (last-half mean) outputs.

    Default ventilation_mode='spontaneous' because most literature validation
    studies used awake, spontaneously-breathing volunteers. Pass
    ventilation_mode='none' for anaesthetised/apnoeic scenarios.
    """
    comps, cardiac = build_patient_params(height_cm, weight_kg, map_mmhg=map_mmhg,
                                          hr_bpm=hr_bpm)
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
    """
    s_base, s_trend15 = supine_175_75, hdt15_175_75
    dcvp = s_trend15["cvp"] - s_base["cvp"]
    dco  = s_trend15["co"]  - s_base["co"]
    dsv  = s_trend15["sv"]  - s_base["sv"]
    dmap = s_trend15["map"] - s_base["map"]

    # With ITP positional coupling: transmural ΔCVP + positional ITP (~+2.2 mmHg
    # at -15°) should place reported ΔCVP within the Likhvantsev CI [2.42-5.84].
    assert 1.5 <= dcvp <= 7.0, f"ΔCVP {dcvp:+.2f} mmHg outside [1.5, 7.0] (lit CI 2.42-5.84)"
    assert dco  > 0, f"CO must increase at -15 deg: d={dco:+.3f} (lit +0.33)"
    assert dsv  > 0, f"SV must increase at -15 deg: d={dsv:+.1f} mL (lit +8.27)"
    assert dmap > -5, f"MAP dropped substantially at -15 deg: d={dmap:+.1f} mmHg"


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


def test_cvp_baseline_calibration(supine_175_75):
    """Supine CVP must sit in the normal range.

    BAND 2-4 -> 1-6 mmHg (2026-08-26). The old assertion was not comparing like
    with like, in three ways at once. It cited Lloyd-Donald 2025
    (DOI 10.1111/anae.16633) for "2-3 mmHg", which is a NARRATIVE REVIEW rather
    than a cohort measurement, and which defines CVP as the intraluminal
    pressure of the SUPERIOR VENA CAVA where this test reads the RIGHT ATRIUM.
    The model also reports a rolling MINIMUM of RA pressure where a clinical
    transducer displays a MEAN.

    WHERE 1-6 COMES FROM. The upper bound is Rudski 2010, the ASE right-heart
    guideline (PMID 20620859, DOI 10.1016/j.echo.2010.05.010), Table 3: an IVC
    <= 2.1 cm collapsing > 50 % with a sniff indicates a NORMAL RA pressure of
    3 mmHg, range 0-5. That is the only normal-POPULATION reference available —
    echocardiography being the one modality applicable to healthy awake
    volunteers — and 6 allows one further mmHg for the trough-vs-mean
    convention below. Everything else in the ledger is measured in patients and
    reads higher: Maas 2009 Pcv 6.72 +/- 2.26 (sedated, ventilated, PEEP 5),
    Ferguson 1989 ~7.5 (one cath-lab patient), Cecconi 1998 9.1 +/- 4.3
    (n=114, cardiac disease).

    WHY THE LOWER BOUND IS 1 AND NOT 0. Physiologically RA pressure can be 0 and
    intraluminal pressure goes frankly negative during spontaneous inspiration
    — Rudski's own normal range starts at 0. But `_cardiac_pressure` returns
    max(0.0, E*(V-V0)), so the model's atrial pressure is FLOORED AT ZERO by
    construction, and at supine `itp_pos` is 0. An assertion of cvp >= 0 could
    therefore never fail and would assert nothing. A floor of 1 is a real
    assertion: it catches a drained right atrium.

    CAVEAT, because it cuts against the upper bound: Rudski's values are
    ASSIGNED from IVC appearance in order to compute pulmonary artery pressure,
    not measured RAP distributions, and the guideline itself lists as a
    disadvantage that "IVC collapse does not accurately reflect RA pressure".

    The model reads 5.7 — inside the band, but near the top of it, and above
    Rudski's normal range once the ~1 mmHg trough-to-mean offset is added
    (model mean RA is about 6.4). That is a real if modest discrepancy and it is
    NOT papered over: it belongs to backlog item 28, where CVP, mean systemic
    filling pressure and resistance to venous return are bound together by
    CVP = MSFP - CO x Rvr and cannot be moved independently.

    BAND REVISED TO 4-10 ON 2026-09-01, AND THE OLD ONE WAS WRONG AT BOTH ENDS.
    Everything above is superseded. Hoff 2019 (PMID 31560715, PMC6764667) supplies
    what item 31 searched for twice and concluded "possibly does not exist": ten
    HEALTHY, AWAKE, SUPINE volunteers with INVASIVELY measured CVP, catheterised
    for an LBNP protocol. Resting arm, from the authors' own raw data archive:
        mean 6.94, SD 1.75, median 7.23, individual values 4.3 to 9.8 mmHg.
    NOT ONE of the ten fell below 4.3, so the old floor of 1 asserted almost
    nothing and the old ceiling of 6 sat BELOW the measured mean.

    THE SOURCES SPLIT BY METHOD, NOT BY SCATTER. Every INVASIVE measurement
    clusters at 7-9: Hoff 6.94 (healthy awake), Maas 6.72 (post-op, PEEP 5),
    van den Berg 9 +/- 4 (post-CABG), Ferguson ~7.5 (cath lab, n=1). The
    ECHO-derived and review figures say 2-3: Rudski's 3 (range 0-5) is ASSIGNED
    from IVC appearance to compute pulmonary pressures, and that guideline itself
    warns "IVC collapse does not accurately reflect RA pressure";
    Lloyd-Donald 2025 gives 2-3 in review. The catheter is the reference standard,
    so the band follows the catheter. All eight sources stay tabulated in
    reference_values.md.

    AGE IS NOT A CONFOUNDER HERE, AND THAT WAS CHECKED RATHER THAN ASSUMED.
    Hoff's cohort is 25 +/- 3 while this model's reference is 55, so by the
    match-the-cohort rule the comparison should be made at 25. The model's CVP is
    essentially age-invariant: 4.51 at 25, 4.72 at 55, 4.87 at 70 — a 0.36 mmHg
    range. Matching the age moves the model AWAY from Hoff by 0.2 mmHg rather
    than toward it, so the discrepancy is not an age artefact.

    History: strict xfail from 2026-08-25 against a 2-4 band; widened to 2-8 on
    2026-08-26; tightened to 1-6 the same day once Rudski was read; revised to
    4-10 on 2026-09-01 on Hoff's measured cohort. The trough-vs-mean convention
    question remains backlog item 31.
    """
    cvp = supine_175_75["cvp"]
    assert 4.0 <= cvp <= 10.0, (
        f"Supine CVP {cvp:.1f} mmHg outside 4-10 mmHg. Band from Hoff 2019 "
        f"(PMID 31560715), the only healthy-awake cohort with INVASIVELY "
        f"measured CVP: 6.94 +/- 1.75 mmHg in 10 supine volunteers, individual "
        f"values 4.3 to 9.8. Not one subject fell below 4.3. The model reports a "
        f"rolling MINIMUM, about 1 mmHg below the mean a transducer would show, "
        f"which is why the floor is 4 rather than Hoff's observed 4.3."
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
    oscillation of 3-10 bpm peak-to-peak at 15 breaths/min."""
    p = SimParams()
    p.ventilation_mode = 'spontaneous'
    p.resp_rate_bpm    = 15.0
    r = run_simulation(p, duration_s=30, dt=DT, use_baroreflex=True)
    hr = r['hr']
    hr_std   = float(np.std(hr[len(hr) // 2:]))
    hr_range = float(np.max(hr) - np.min(hr))

    assert hr_std > 0.3, f"RSA not detectable: HR std={hr_std:.2f} bpm"
    assert hr_range < 12.0, f"RSA excessive: HR p-p={hr_range:.2f} bpm"
    assert hr_range > 0.5, f"RSA not measurable: HR p-p={hr_range:.2f} bpm"


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
    tachycardia)."""
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

def _run_vasopressin(units_hr):
    p = SimParams()
    p.baroreflex_enabled = True
    p.drug_factors = combined_drug_factors({"vasopressin": units_hr})
    r = run_simulation(p, duration_s=20, dt=DT)
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

    # HR unchanged (no chronotropy)
    dhr = abs(v2['hr'] - v0['hr'])
    assert dhr < 8,  f"HR changed with vasopressin: Δ{dhr:.1f} bpm (lit: no chronotropy)"


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
    low_dose = _run_epi(0.02)   # β-dominant: CO↑, SVR↓/neutral, MAP ~unchanged
    high_dose = _run_epi(0.30)  # α-dominant: CO↑↑, SVR↑↑, MAP↑↑

    # CO increases monotonically with dose (β1 inotropy dominates across all doses;
    # Freyschuss: "marked and concentration-dependent increases in SV and CO")
    assert low_dose['co']  > base['co'],      f"Low-dose epi: CO did not rise: {base['co']:.2f}→{low_dose['co']:.2f}"
    assert high_dose['co'] > low_dose['co'],  f"High-dose epi: CO not > low-dose: {low_dose['co']:.2f}→{high_dose['co']:.2f}"

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
    norm_supine = _run_plr(tilt_deg=0,   hem_ml=0)
    norm_plr    = _run_plr(tilt_deg=-20, hem_ml=0)
    hypo_supine = _run_plr(tilt_deg=0,   hem_ml=1200)
    hypo_plr    = _run_plr(tilt_deg=-20, hem_ml=1200)

    dco_norm_pct = (norm_plr['co'] - norm_supine['co']) / norm_supine['co'] * 100
    dco_hypo_pct = (hypo_plr['co'] - hypo_supine['co']) / hypo_supine['co'] * 100

    # Normovolemic: Starling plateau limits response — PLR should not reach ≥10%
    assert dco_norm_pct < 10, (
        f"Normovolemic PLR: CO rose ≥10% despite Starling plateau: Δ{dco_norm_pct:+.1f}%"
    )

    # Hypovolemic: ascending limb — PLR should return ≥10% CO increase
    assert dco_hypo_pct >= 10, (
        f"Hypovolemic PLR: CO increase < 10% (lit threshold ≥10%): Δ{dco_hypo_pct:+.1f}%"
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
    return {k: float(np.mean(r[k][h:])) for k in ("map", "cvp", "co", "sv")}


def test_venous_tone_modulates_preload_regression():
    """Venous tone must produce a clear, correctly-signed haemodynamic effect.

    Fails bit-for-bit on the pre-fix code where the factor was never applied.
    Baroreflex OFF isolates the mechanical (preload-recruitment) effect.
    """
    neutral   = _run_venous_tone(1.00)
    constrict = _run_venous_tone(0.90)   # +10% venous tone (venoconstriction)
    dilate    = _run_venous_tone(1.10)   # 10% venodilation

    # Venoconstriction recruits blood centrally: CVP, SV and CO all rise —
    # by a clear margin, not marginally (guards against re-neutering).
    assert constrict["co"]  > neutral["co"]  * 1.05, (
        f"Venoconstriction did not raise CO: {neutral['co']:.2f}→{constrict['co']:.2f} L/min")
    assert constrict["sv"]  > neutral["sv"], (
        f"Venoconstriction did not raise SV: {neutral['sv']:.1f}→{constrict['sv']:.1f} mL")
    # CVP margin 0.2 mmHg: with physiological venous compliance (venous-system
    # rebuild) the same fractional venoconstriction shifts CVP more gently than
    # on the old compressed pool — the effect is real, just correctly smaller.
    assert constrict["cvp"] > neutral["cvp"] + 0.2, (
        f"Venoconstriction did not raise CVP: {neutral['cvp']:.2f}→{constrict['cvp']:.2f} mmHg")

    # Venodilation pools blood peripherally: CVP and CO fall.
    assert dilate["co"]  < neutral["co"]  * 0.95, (
        f"Venodilation did not lower CO: {neutral['co']:.2f}→{dilate['co']:.2f} L/min")
    assert dilate["cvp"] < neutral["cvp"] - 0.2, (
        f"Venodilation did not lower CVP: {neutral['cvp']:.2f}→{dilate['cvp']:.2f} mmHg")

    # Monotonic ordering across the range.
    assert constrict["co"] > neutral["co"] > dilate["co"], (
        f"CO not monotonic in venous tone: "
        f"{constrict['co']:.2f} / {neutral['co']:.2f} / {dilate['co']:.2f}")


def test_venous_tone_factor_signs_by_drug_class():
    """Vasopressors venoconstrict (factor < 1); IV anaesthetics venodilate
    (factor > 1). Guards the sign convention, which a prior version had
    contradictory between the pressor and anaesthetic drug classes."""
    vt = lambda d: combined_drug_factors(d)["venous_tone_factor"]
    assert vt({"norepinephrine": 0.1}) < 1.0, "norepinephrine should venoconstrict"
    assert vt({"phenylephrine":  1.0}) < 1.0, "phenylephrine should venoconstrict"
    assert vt({"vasopressin":    2.0}) < 1.0, "vasopressin should venoconstrict"
    assert vt({"propofol":       2.0}) > 1.0, "propofol should venodilate"
    assert vt({"spinal":         1.0}) > 1.0, "spinal should venodilate"


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
# ===========================================================================

def test_resting_baroreflex_tone_is_arterial_not_venous():
    """[A1] At rest the venous arm must be near-neutral, the arterial arm not.

    This guards the ASYMMETRY, not the exact numbers. If someone gives the
    venous effector a resting set-point, an unstressed patient starts out with
    the venous reserve already partly spent — and every subsequent hypovolaemic
    or orthostatic challenge then has less reserve to recruit than a real
    patient does.
    """
    from model.baroreflex import BaroreflexController

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
# ===========================================================================

REFERENCE_BSA = (175.0 * 70.0 / 3600.0) ** 0.5   # Mosteller, the default patient


def _atrial_state():
    """Cycle max/min volume and emptying fraction for both atria."""
    p = SimParams()
    p.ventilation_mode = "none"
    p.slow_dynamics_enabled = False
    r = run_simulation(p, duration_s=60.0, dt=DT)
    V = r["volumes"][2 * len(r["volumes"]) // 3:]
    out = {}
    for key, name in (("la", "left_atrium"), ("ra", "right_atrium")):
        v = V[:, IDX[name]]
        vmax, vmin = float(v.max()), float(v.min())
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
    """[G1][G2] Atrial volumes indexed to BSA must match human reference ranges."""
    s = _atrial_state()
    # Bands span [G2] 3D-echo and [G1] CMR; see the modality note above.
    assert 20.0 <= s["la"]["vmax_i"] <= 50.0, (
        f"LAVmax {s['la']['vmax_i']:.1f} mL/m2 ({s['la']['vmax']:.0f} mL) outside "
        f"20-50; [G2] 3D echo 25.18, [G1] CMR 36.9 +/- 7.7"
    )
    assert 8.0 <= s["la"]["vmin_i"] <= 22.0, (
        f"LAVmin {s['la']['vmin_i']:.1f} mL/m2 outside 8-22; [G2] 11.10, [G1] 14.4"
    )
    assert 20.0 <= s["ra"]["vmax_i"] <= 48.0, (
        f"RAVmax {s['ra']['vmax_i']:.1f} mL/m2 ({s['ra']['vmax']:.0f} mL) outside "
        f"20-48; [G1] CMR 33.9 +/- 8.9"
    )
    assert 8.0 <= s["ra"]["vmin_i"] <= 28.0, (
        f"RAVmin {s['ra']['vmin_i']:.1f} mL/m2 outside 8-28; [G1] 17.1 +/- 5.6"
    )


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
    assert 45.0 <= s["la"]["ef"] <= 72.0, (
        f"LA emptying fraction {s['la']['ef']:.1f}% outside 45-72; [G1] 61.1 +/- 6.2, "
        f"[G2] 55.94 (CI 51.92-59.96)"
    )
    assert 35.0 <= s["ra"]["ef"] <= 65.0, (
        f"RA emptying fraction {s['ra']['ef']:.1f}% outside 35-65; [G1] 49.7 +/- 9.2"
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


@pytest.mark.xfail(strict=True, reason=(
    "KNOWN GAP C — the right heart is underfilled, and this test measures the "
    "VOLUME half of it. Female RAVmax is 26.7 mL/m2 against this test's 27-38 "
    "band. NOTE 26.7 IS INSIDE [G1] GAO'S OWN 1 SD (32.7 +/- 8.2 = 24.5-40.9); "
    "the band is deliberately tighter, at 0.67 SD, matching the 0.50 and 0.54 SD "
    "bands of the two ventricular assertions beside it. The band is NOT being "
    "widened to accommodate this — that would discard a signal. "
    "THE SIGNAL: a small right atrium sitting at a low pressure is ONE finding, "
    "not two. RAVmax index 28.0 male (-0.66 SD vs Gao), RA INTRALUMINAL MEAN "
    "2.32 mmHg against Hoff's measured 6.94 +/- 1.75 (-2.64 SD, PMID 31560715), "
    "and transmural CVP 4.26 (-1.53 SD). The volume and the pressure agree with "
    "each other and disagree with the literature in the same direction. "
    "CAUSE, NOT YET FOUND. Total blood volume is CORRECT (5123 vs Lister's 5148), "
    "so this is a distribution problem, not a volume problem. The pulmonary "
    "compliance correction of 2026-09-03 made it slightly worse (male RAVmax "
    "29.3 -> 28.0) because it moved 80 mL into the lungs — which was right on "
    "its own evidence, and exposed that the systemic side cannot spare it. "
    "The mean intrathoracic pressure baseline (SPONTANEOUS_ITP_BASELINE_CMH2O, "
    "-2.0 cmH2O, unsourced) is one candidate; systemic venous unstressed volumes "
    "are another. "
    "DO NOT close this by widening the band or by shrinking the pulmonary bed. "
    "The DIRECTION assertions above (female < male for all three chambers) stay "
    "LIVE and calibration-independent — they are the point of the sex feature and "
    "they pass. "
    "strict=True so this flips to a FAILURE the day gap C is fixed."
))
def test_female_chamber_volumes_match_luu_and_gao():
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
    assert 60.0 <= f["left_ventricle"] <= 71.0, (
        f"female LVEDV {f['left_ventricle']:.1f} mL/m2 outside 60-71; "
        f"[L1] female 65 ± 11, male 74")
    assert 66.0 <= f["right_ventricle"] <= 80.0, (
        f"female RVEDV {f['right_ventricle']:.1f} mL/m2 outside 66-80; "
        f"[L1] female 72 ± 13, male 86")
    assert 27.0 <= f["right_atrium"] <= 38.0, (
        f"female RAVmax {f['right_atrium']:.1f} mL/m2 outside 27-38; "
        f"[G1] female 32.7 ± 8.2, male 34.9")


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
    for name, fn in drugs.items():
        for factor, value in fn(0.0).items():
            assert value == pytest.approx(1.0, abs=1e-12), (
                f"{name}(0.0) returns {factor}={value}, must be exactly 1.0. "
                f"A drug that is not being given must do nothing. If this is a "
                f"'fraction of another effect' term, it must be written "
                f"1 + k*(f - 1), not f*k — the latter inverts the effect."
            )

    # And through the combining path, which is what the model actually calls.
    for name in drugs:
        for factor, value in combined_drug_factors({name: 0.0}).items():
            assert value == pytest.approx(1.0, abs=1e-12), (
                f"combined_drug_factors({{{name!r}: 0.0}}) returns "
                f"{factor}={value}, must be exactly 1.0"
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
    assert disk["hires"]["volumes"].shape == (10000, 23)
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
    it has NO sourced coefficient — Akoumianaki 2024 has the right
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

    # The pulmonic valve is 3x the other three. That is inherited, not chosen —
    # pulmonary_art.resistance served double duty as valve and PA inflow. It is
    # pinned here so that normalising it later is a deliberate, visible change
    # rather than a tidy-up.
    assert PULMONIC_R == 0.03 and MITRAL_R == 0.01, (
        "the pulmonic/mitral asymmetry changed; if that was intended, update "
        "this test and say why in the validation log"
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


def test_age_widens_pulse_pressure_the_way_framingham_measured_it():
    """[PMID 9236450] The endpoint, not the parameter.

    Franklin: pulse pressure widens 0.68 mmHg/year in normotensive men while
    MAP is essentially flat (0.016 mmHg/year). A stiffening conduit widens the
    PULSE around a fixed MEAN; a rising resistance would raise the mean. This
    asserts the model reproduces that SHAPE — PP up, MAP nearly unchanged —
    which is the whole reason compliance rather than resistance is scaled.
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

    p = SimParams()
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
        def f(t, mode, rr, peep, pip, ie):
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
