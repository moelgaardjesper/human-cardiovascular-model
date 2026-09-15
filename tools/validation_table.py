#!/usr/bin/env python3
"""
Regenerate the validation scoreboard: literature target vs current model value.

The pytest suite asserts RANGES — it tells you pass/fail but not how close you
are, and a test can sit at the very edge of its bound for months without anyone
noticing. This prints the actual numbers side by side so drift is visible.

    python3 tools/validation_table.py            # fast scenarios (~6 min)
    python3 tools/validation_table.py --markdown # emit a README-ready table

Rows marked LOGGED are measured by the slow suite (multi-hour simulations); their
values are transcribed WITH THE DATE they were measured, not re-measured here.
Re-measure them with `pytest -m slow`.

COHORT AGE IS PART OF A COMPARISON. Where a source records its cohort's age the
row says so, and the model is run at that age. Where it does not, the row says
that too — an unmatched comparison shown as if it were matched is how a
generation gap gets read as a model error.

This is a REPORTING tool. It asserts nothing and must never be the thing that
decides whether a change is acceptable — the pytest suite is the ratchet.
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tests"))

import numpy as np

from model.circulation import SimParams, run_simulation
from model.gravity import GravityEnvironment
from model.patient import build_patient_params
from model.heart import LV_EMAX, RV_EMAX
from model.pharmacology import combined_drug_factors

DT = 0.001
LIT_DURATION = 40.0


def last_half(arr):
    return float(np.mean(arr[len(arr) // 2:]))


def run_scenario(height_cm=175, weight_kg=75, map_mmhg=None, hr_bpm=70,
                 tilt_deg=0.0, gravity=GravityEnvironment.EARTH,
                 baroreflex=True, ventilation_mode="spontaneous",
                 duration=LIT_DURATION, drugs=None):
    """Mirror of the helper in tests/test_circulation.py."""
    comps, cardiac = build_patient_params(height_cm, weight_kg,
                                          map_mmhg=map_mmhg, hr_bpm=hr_bpm)
    p = SimParams(compartments=comps)
    p.hr_bpm = hr_bpm
    p.lv_emax = LV_EMAX * cardiac.get("lv_emax_factor", 1.0)
    p.rv_emax = RV_EMAX * cardiac.get("rv_emax_factor", 1.0)
    p.tilt_start_deg = p.tilt_end_deg = tilt_deg
    p.tilt_onset_s = 5.0
    p.gravity = gravity
    p.baroreflex_enabled = baroreflex
    p.ventilation_mode = ventilation_mode
    if drugs:
        p.drug_factors = combined_drug_factors(drugs)
    r = run_simulation(p, duration_s=duration, dt=DT)
    return {k: last_half(r[k]) for k in
            ("map", "hr", "co", "cvp", "sv", "cpp", "buckberg")}


# (label, reference, literature target, callable -> measured string)
ROWS = []


def row(label, ref, target, fn):
    ROWS.append((label, ref, target, fn))


def _phenyl_row():
    """Phenylephrine at the model's pressor plateau, in a 27-year-old."""
    from model.pharmacology import combined_drug_factors
    from model.patient import build_patient_params, apply_cardiac

    def run(dose):
        comps, cardiac = build_patient_params(175, 70, hr_bpm=70.0, sex="male",
                                              age_years=27.0)
        p = SimParams(compartments=comps)
        apply_cardiac(p, cardiac)
        p.hr_bpm = 70.0
        p.baroreflex_enabled = True
        if dose:
            p.drug_factors = combined_drug_factors({"phenylephrine": dose})
        r = run_simulation(p, duration_s=90.0)
        t = np.asarray(r["t"]); tail = t >= t[-1] - 20.0
        m = lambda k: float(np.mean(np.asarray(r[k])[tail]))
        co, hr = m("co"), m("hr")
        return co, hr, 1000.0 * co / hr

    b = run(0.0)
    d = run(4.0)
    return (f"at 4 mcg/kg/min: dCO {d[0]-b[0]:+.2f}, dHR {d[1]-b[1]:+.1f}, "
            f"dSV {d[2]-b[2]:+.1f}")

# --- Resting and postural ---------------------------------------------------

# TWO RESTING ROWS, AND THE REASON IS COHORT AGE.
#
# This table carried ONE resting row, against Sejersen — 10 healthy males whose
# height and weight are recorded but whose AGE is not. The model's reference
# patient is 55. Reporting "MAP 95.7" beside "MAP 83 +/- 8" therefore showed a
# +1.6 SD miss that is substantially a generation gap, not a model error:
# McEniery 2005, males 50-59, n=429, measures MAP 95 +/- 7 and the model sits
# at 95.4, which is +0.06 SD.
#
# Both rows stay. Deleting Sejersen would be fitting the comparison to the
# answer; showing only McEniery would hide that the model is high against
# younger cohorts. The pair IS the finding, and the cohort ages are stated so a
# reader can see which comparison is like-for-like.
row("Supine resting, AGE-MATCHED (reference patient, 55)",
    "McEniery 2005 PMID 16256881, males 50-59, n=429",
    "MAP 95+/-7, peripheral SBP 125+/-9, peripheral PP 46+/-8, HR 65+/-11",
    lambda: (lambda s: f"MAP {s['map']:.1f}, HR {s['hr']:.0f}, "
                       f"CO {s['co']:.2f}, SV {s['sv']:.0f}")(
        run_scenario(175, 70)))

row("Supine resting, size-matched but NOT age-matched",
    "Sejersen 2022 (10 healthy males 177/80, age not reported); Lie 2023 for CO",
    "MAP 83+/-8, HR 62+/-8 bpm; CO 7+/-2 (Sejersen) vs 4.85+/-1.08 (Lie)",
    lambda: (lambda s: f"MAP {s['map']:.1f}, HR {s['hr']:.0f}, "
                       f"CO {s['co']:.2f}, SV {s['sv']:.0f}")(
        run_scenario(177, 80)))

row("20 deg head-down tilt, normovolaemic",
    "Sejersen 2022",
    "dSV ~0 (n.s.), dCO ~0, dMAP +2 mmHg (n.s.)",
    lambda: (lambda a, b: f"dMAP {b['map']-a['map']:+.1f}, "
                          f"dCO {b['co']-a['co']:+.2f}, dSV {b['sv']-a['sv']:+.1f}")(
        run_scenario(177, 80), run_scenario(177, 80, tilt_deg=-20)))

# RUN AT -30 deg, NOT -15, AND THE CHANGE IS A PROTOCOL FIX.
#
# Likhvantsev pools 16 studies spanning -5 to -45 deg. This row ran the model at
# -15 and compared it against that pooled mean, which is not a like-for-like
# comparison: it asks a shallow tilt to reproduce the average of a range whose
# steep end is three times steeper. -30 deg is mid-range for the pooled
# protocol. At -15 the model reported dCVP +2.35 against a pooled +4.13 and
# looked like a miss; at -30 it lands inside the pooled CI on all four
# quantities. The MODEL did not change — only the angle it is asked at.
#
# This is the same class of error as comparing a transmural pressure against a
# catheter reading, and it is why the tilt row was re-measured before the
# freeze rather than published as it stood.
row("-30 deg Trendelenburg vs supine (mid-range of the pooled protocol)",
    "Likhvantsev 2025 meta-analysis, n=333, 16 studies spanning -5 to -45 deg",
    "dCVP +4.13 (CI 2.42-5.84), dCO +0.33, dSV +8.27, dHR -1.65",
    lambda: (lambda a, b: f"dCVP {b['cvp']-a['cvp']:+.2f}, dCO {b['co']-a['co']:+.2f}, "
                          f"dSV {b['sv']-a['sv']:+.1f}, dHR {b['hr']-a['hr']:+.1f}")(
        run_scenario(tilt_deg=0), run_scenario(tilt_deg=-30)))

row("30 deg head-up tilt",
    "Wieling 1998 (at 90 deg: SV -39+/-9%, CO -26+/-10%, MAP +1+/-7)",
    "SV and CO fall, MAP partially defended (no muscle pump in model)",
    lambda: (lambda a, b: f"dSV {100*(b['sv']-a['sv'])/a['sv']:+.0f}%, "
                          f"dCO {100*(b['co']-a['co'])/a['co']:+.0f}%, "
                          f"dMAP {b['map']-a['map']:+.1f}")(
        run_scenario(), run_scenario(tilt_deg=30)))

row("Graded HUT 0/20/30 deg monotonicity",
    "Sarafian 2017, graded tilt 0-60 deg",
    "HR rises and CO falls monotonically with angle",
    lambda: (lambda a, b, c: f"CO {a['co']:.2f}/{b['co']:.2f}/{c['co']:.2f}, "
                             f"HR {a['hr']:.0f}/{b['hr']:.0f}/{c['hr']:.0f}")(
        run_scenario(tilt_deg=0), run_scenario(tilt_deg=20), run_scenario(tilt_deg=30)))

row("Microgravity CVP vs upright Earth",
    "Buckey 1996",
    "CVP in orbit ~2.5 mmHg, still ABOVE upright standing on Earth",
    lambda: (lambda a, b: f"CVP micro-g {a['cvp']:.2f} vs upright 45 deg {b['cvp']:.2f}")(
        run_scenario(gravity=GravityEnvironment.MICROGRAVITY),
        run_scenario(tilt_deg=45)))

row("Cerebral perfusion pressure, upright",
    "Pohl & Cullen 2005 (beach chair; CPP risk < 50 mmHg)",
    "CPP falls substantially head-up; risk threshold 50 mmHg",
    lambda: (lambda a, b: f"CPP supine {a['cpp']:.0f} -> 45 deg {b['cpp']:.0f}")(
        run_scenario(), run_scenario(tilt_deg=45)))

# --- Pharmacology -----------------------------------------------------------

row("Norepinephrine vs phenylephrine, CO preservation",
    "Ngan Kee 2015, n=104",
    "NE CO 102.7% vs phenylephrine 93.8% (p=0.004); NE HR higher",
    lambda: (lambda ne, pe: f"NE CO {ne['co']:.2f} / HR {ne['hr']:.0f}; "
                            f"PE CO {pe['co']:.2f} / HR {pe['hr']:.0f}")(
        run_scenario(drugs={"norepinephrine": 0.05}),
        run_scenario(drugs={"phenylephrine": 0.5})))

row("Vasopressin dose-response",
    "Patel 2002, n=13 septic shock",
    "MAP rises monotonically with dose; CO maintained",
    lambda: (lambda a, b, c: f"MAP {a['map']:.1f}/{b['map']:.1f}/{c['map']:.1f}, "
                             f"CO {a['co']:.2f}/{b['co']:.2f}/{c['co']:.2f}")(
        run_scenario(), run_scenario(drugs={"vasopressin": 2.0}),
        run_scenario(drugs={"vasopressin": 4.0})))

row("Epinephrine dose-response",
    "Freyschuss 1986, n=11",
    "CO rises monotonically with dose; MAP_high > MAP_low (alpha dominance)",
    lambda: (lambda a, b: f"low CO {a['co']:.2f} MAP {a['map']:.1f}; "
                          f"high CO {b['co']:.2f} MAP {b['map']:.1f}")(
        run_scenario(drugs={"epinephrine": 0.02}),
        run_scenario(drugs={"epinephrine": 0.2})))

# AGE-MATCHED TO THE COHORT, 27. Added at the freeze because it is the
# project's best-matched vasopressor comparison — 12 healthy supine men rather
# than the parturients under spinal that every other pressor row rests on — and
# because three INDEPENDENT flow quantities land in band from one source with
# none of them fitted to. Dosed on the model's own pressor plateau rather than
# dose-for-dose: Schaefers took each subject to his own tolerance (+30 mmHg
# diastolic), so a fixed-rate comparison would be meaningless.
row("Phenylephrine flow response, AGE-MATCHED (27)",
    "Schaefers 1999 PMID 10073742, 12 healthy supine men, median age 27",
    "dCO -1.15 (-1.25 to -0.40), dHR -16 (-19.5 to -14.2), dSV +9 (-0.5 to +18.5)",
    lambda: _phenyl_row())

row("Norepinephrine postcapillary constriction",
    "Abboud & Eckstein 1968 II (venous dose-response 1.80x steeper)",
    "venous/arterial slope ratio 1.80 over a dose doubling",
    lambda: (lambda a, b: f"ratio {((b['postcap_factor']-1)/(a['postcap_factor']-1)) / ((b['svr_factor']-1)/(a['svr_factor']-1)):.2f}")(
        combined_drug_factors({"norepinephrine": 0.05}),
        combined_drug_factors({"norepinephrine": 0.10})))

# --- Slow dynamics (measured by `pytest -m slow`; values from the log) -------

LOGGED = [
    ("Transcapillary refill after haemorrhage",
     "Lister 1963, 550 mL over 15 min, human",
     "refill incomplete at 2 h; 50-80% by 24 h",
     "PASSES. Correctly incomplete at 2 h; model refills ~1.6x fast on cumulative "
     "volume  [2026-08-22]"),
    ("Norepinephrine plasma-volume cost",
     "Lister 1963 Fig 5, unbled healthy men",
     "plasma volume falls 15-19%",
     "PASSES at 16.07%. Was a strict xfail at 0.13% until 2026-08-22; closed by two "
     "structural fixes (backlog 20 then 18), no parameter fitted to this endpoint"),
    ("Norepinephrine recovery timescale",
     "Lister 1963 Fig 5",
     "recovery over ~1 h; not near-complete within minutes",
     "PASSES both bounds. Model still recovers ~4x faster than Lister overall — "
     "deliberately not asserted  [2026-08-22]"),
    ("Venous stress relaxation + filtration, CVP dissipation",
     "Guyton (~82% of an acute CVP rise dissipated)",
     "~82%",
     "PASSES. 79.8% combined (creep alone 27.4%)  [2026-08-22]"),
    ("RAAS/ADH pressure defence after 1000 mL bleed",
     "Bussien 1984 (human), Hasser & Bishop 1988, Rascher 1985",
     "no effect at rest; pressor reserve unmasked when reflexes overwhelmed",
     "PASSES. +3.50 mmHg MAP, CO slightly DOWN (vasoconstrictor signature), blood "
     "volume unchanged  [2026-08-22]"),
    ("Autonomic modulation of refill time constant",
     "Shigemi (dog): autonomic blockade doubles recovery tau, 39 -> 74 min",
     "ratio ~1.9",
     "NOT REPRODUCED, open. 9.31 -> 9.11 min, ratio 0.98. No test asserts it; "
     "candidate for a baroreflex arm on the postcapillary split  [2026-08-10]"),
]



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--markdown", action="store_true")
    args = ap.parse_args()

    results = []
    for label, ref, target, fn in ROWS:
        sys.stderr.write(f"  running: {label}\n")
        sys.stderr.flush()
        try:
            measured = fn()
        except Exception as exc:                      # noqa: BLE001
            measured = f"ERROR: {type(exc).__name__}: {exc}"
        results.append((label, ref, target, measured))

    if args.markdown:
        print("| Scenario | Reference | Literature target | Model now |")
        print("|---|---|---|---|")
        for label, ref, target, measured in results:
            print(f"| {label} | {ref} | {target} | {measured} |")
        print()
        print("Slow-dynamics rows — measured by `pytest -m slow`, transcribed "
              "with the date they were measured:")
        print()
        print("| Scenario | Reference | Literature target | Model now |")
        print("|---|---|---|---|")
        for label, ref, target, measured in LOGGED:
            print(f"| {label} | {ref} | {target} | {measured} |")
    else:
        for label, ref, target, measured in results:
            print(f"\n{label}\n  ref    : {ref}\n  target : {target}\n  model  : {measured}")
        print("\n--- slow dynamics (logged, not re-measured) ---")
        for label, ref, target, measured in LOGGED:
            print(f"\n{label}\n  ref    : {ref}\n  target : {target}\n  model  : {measured}")


if __name__ == "__main__":
    main()
