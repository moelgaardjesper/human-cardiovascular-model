#!/usr/bin/env python3
"""
Regenerate the validation scoreboard: literature target vs current model value.

The pytest suite asserts RANGES — it tells you pass/fail but not how close you
are, and a test can sit at the very edge of its bound for months without anyone
noticing. This prints the actual numbers side by side so drift is visible.

    python3 tools/validation_table.py            # fast scenarios (~6 min)
    python3 tools/validation_table.py --markdown # emit a README-ready table

Rows marked LOGGED are measured by the slow suite (multi-hour simulations); their
values come from docs/validation_log.md and are dated, not re-measured here.
Re-measure them with `pytest -m slow`.

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


# --- Resting and postural ---------------------------------------------------

row("Supine resting haemodynamics",
    "Sejersen 2022 (10 healthy males 177/80); Lie 2023 for CO",
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

row("-15 deg Trendelenburg vs supine",
    "Likhvantsev 2025 meta-analysis, n=333",
    "dCVP +4.13 (CI 2.42-5.84), dCO +0.33, dSV +8.27, dHR -1.65",
    lambda: (lambda a, b: f"dCVP {b['cvp']-a['cvp']:+.2f}, dCO {b['co']-a['co']:+.2f}, "
                          f"dSV {b['sv']-a['sv']:+.1f}, dHR {b['hr']-a['hr']:+.1f}")(
        run_scenario(tilt_deg=0), run_scenario(tilt_deg=-15)))

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
     "model refills ~1.6x too fast on cumulative volume, ~1.45x on mean rate; "
     "correctly incomplete at 2 h  [2026-08-10]"),
    ("Norepinephrine plasma-volume cost",
     "Lister 1963 Fig 5, unbled healthy men",
     "plasma volume falls 15-19%",
     "1.19% (was 0.13% before the postcapillary pathway) — STRICT XFAIL, "
     "blocked by backlog item 20  [2026-08-21]"),
    ("Venous stress relaxation + filtration, CVP dissipation",
     "Guyton (~82% of an acute CVP rise dissipated)",
     "~82%",
     "79.8% combined (creep alone 27.4%)  [2026-08-10]"),
    ("RAAS/ADH pressure defence after 1000 mL bleed",
     "Bussien 1984 (human), Hasser & Bishop 1988, Rascher 1985",
     "no effect at rest; pressor reserve unmasked when reflexes overwhelmed",
     "MAP 71.44 -> 74.94 (+3.50 mmHg), CO slightly DOWN (vasoconstrictor "
     "signature), blood volume unchanged  [2026-08-12]"),
    ("Autonomic modulation of refill time constant",
     "Shigemi (dog): autonomic blockade doubles recovery tau, 39 -> 74 min",
     "ratio ~1.9",
     "9.31 -> 9.11 min, ratio 0.98 — NOT REPRODUCED, open  [2026-08-10]"),
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
        print("Slow-dynamics rows (from `pytest -m slow`, see validation_log.md):")
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
