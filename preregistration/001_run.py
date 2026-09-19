#!/usr/bin/env python3
"""Registration 001 — scenario runner. Produces the registered prediction.

    PYTHONPATH=. python3 preregistration/001_run.py

Four conditions: spontaneous and 6 bpm paced breathing, each at 30 and 60
degrees head-up. Both ITD conditions are omitted — the inspiratory swing depth
is a module constant in model/respiration.py, not a SimParams field, so it
cannot be deepened to -7 cmH2O without editing frozen code.

WHY FOUR INDEPENDENT SETTLED RUNS AND NOT A LIVE SEQUENCE. Each condition in the
study is a 5-minute block, long enough for the fast dynamics to settle, unlike
the 1-minute stages of a postural-challenge protocol. And the sequence is ALREADY
broken for us: the two ITD blocks sit between the ones we can run, so a faithful
live sequence is impossible whatever we do. Independent runs through the
canonical run_simulation are then the honest choice — deterministic, reproducible
and free of the threading this project's live path needs. The cost is registered
as a caveat: no carry-over between blocks.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from model.circulation import SimParams, run_simulation
from model.patient import build_patient_params, apply_cardiac, bsa_mosteller

AGE, SEX = 23.0, "male"
HEIGHT_CM, WEIGHT_KG = 175.0, 70.0   # NOT REPORTED — model reference body, registered as an assumption
SB_RATE = 14.0                        # NOT REPORTED — SimParams default, registered as an assumption
PACED_RATE = 6.0
DURATION, WINDOW = 300.0, 60.0        # 5-min block, averaged over the final minute
BSA = bsa_mosteller(HEIGHT_CM, WEIGHT_KG)


def run(tilt_deg, resp_rate):
    comps, cardiac = build_patient_params(HEIGHT_CM, WEIGHT_KG, sex=SEX, age_years=AGE)
    p = SimParams(compartments=comps)
    apply_cardiac(p, cardiac)
    p.tilt_start_deg = p.tilt_end_deg = float(tilt_deg)
    p.ventilation_mode = "spontaneous"
    p.resp_rate_bpm = float(resp_rate)
    r = run_simulation(p, duration_s=DURATION, dt=0.001)
    t = np.asarray(r["t"]); m = t >= t[-1] - WINDOW
    f = lambda k: float(np.mean(np.asarray(r[k])[m]))
    return {"map": f("map"), "co": f("co"), "hr": f("hr"), "sv": f("sv")}


def main():
    print(f"age {AGE:.0f}  {SEX}  {HEIGHT_CM:.0f} cm  {WEIGHT_KG:.0f} kg  BSA {BSA:.3f} m2")
    print(f"spontaneous {SB_RATE:.0f} bpm   paced {PACED_RATE:.0f} bpm   "
          f"{DURATION:.0f} s per condition, last {WINDOW:.0f} s averaged\n")

    conds = {}
    for tilt in (30.0, 60.0):
        for label, rate in (("SB", SB_RATE), ("6bpm", PACED_RATE)):
            key = f"{label}-{tilt:.0f}"
            conds[key] = run(tilt, rate)
            c = conds[key]
            print(f"  {key:9s}  MAP {c['map']:7.2f}  CO {c['co']:6.2f}  "
                  f"CI {c['co']/BSA:5.2f}  HR {c['hr']:6.1f}  SV {c['sv']:6.1f}")

    print("\nPRIMARY — paced breathing effect at 30 deg")
    a, b = conds["SB-30"], conds["6bpm-30"]
    print(f"  dMAP {b['map']-a['map']:+6.2f} mmHg    dCO {b['co']-a['co']:+6.2f} L/min")

    print("\nSECONDARY — paced breathing effect at 60 deg (extrapolation)")
    a2, b2 = conds["SB-60"], conds["6bpm-60"]
    print(f"  dMAP {b2['map']-a2['map']:+6.2f} mmHg    dCO {b2['co']-a2['co']:+6.2f} L/min")

    print("\nSECONDARY — posture effect, 30 -> 60 deg, spontaneous breathing")
    print(f"  dMAP {a2['map']-a['map']:+6.2f} mmHg    dCO {a2['co']-a['co']:+6.2f} L/min")

    print("\nSECONDARY — interaction (does posture change the breathing effect?)")
    print(f"  d(dMAP) {(b2['map']-a2['map'])-(b['map']-a['map']):+6.2f}    "
          f"d(dCO) {(b2['co']-a2['co'])-(b['co']-a['co']):+6.2f}")

    print("\nSECONDARY — absolute baseline at SB-30 (sensitive to assumed body size)")
    print(f"  MAP {a['map']:.2f} mmHg   CO {a['co']:.2f} L/min   CI {a['co']/BSA:.2f}")


if __name__ == "__main__":
    main()
