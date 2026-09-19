#!/usr/bin/env python3
"""Registration 003 — phenylephrine vs noradrenaline at MATCHED mean pressure.

    PYTHONPATH=. python3 preregistration/003_run.py

The study titrated each drug to the same MAP target (80-100 % of the awake
value), so the comparison is at matched PRESSURE, not matched dose. That is
reproduced here by bisecting each drug's dose until the model reaches the same
target. **Matching on pressure means the drug concentrations, which the paper
does not give in mcg, are never needed** — dose becomes an output.

It also means the known setpoint defect (backlog item 62) largely cancels: both
arms start from the same anaesthetised state and are driven to the same
pressure, so the NE-minus-PE difference is insensitive to where that pressure
sits.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from model.circulation import SimParams, run_simulation
from model.patient import build_patient_params, apply_cardiac, bsa_mosteller
from model.pharmacology import combined_drug_factors

AGE = 57.0
SEXES = ("female", "male")          # cohort is ~70 % female; both run
HEIGHT_CM = 168.0                    # NOT REPORTED — assumed for this cohort
BMI = 26.6                           # midpoint of the two groups, 27.7 and 25.5
WEIGHT_KG = BMI * (HEIGHT_CM / 100.0) ** 2

PROPOFOL_MG_KG = 2.0    # proxy for TCI Ce 2.5 ug/mL — see the registration
PEEP, PIP = 5.0, 17.0   # PEEP from the study; PIP inferred from TV 8 mL/kg
RR = 12.0               # NOT REPORTED — set to etCO2 in the study
MAP_TARGET_FRAC = 0.90  # study titrated to 80-100 % of awake; midpoint used

DURATION, WINDOW = 90.0, 20.0


def settle(sex, drugs, ventilated):
    comps, cardiac = build_patient_params(HEIGHT_CM, WEIGHT_KG, sex=sex,
                                          age_years=AGE)
    p = SimParams(compartments=comps)
    apply_cardiac(p, cardiac)
    if ventilated:
        p.ventilation_mode = "mechanical"
        p.peep_cmh2o, p.pip_cmh2o, p.resp_rate_bpm = PEEP, PIP, RR
    else:
        p.ventilation_mode = "spontaneous"
        p.resp_rate_bpm = 14.0
    if drugs:
        p.drug_factors = combined_drug_factors(drugs)
    r = run_simulation(p, duration_s=DURATION, dt=0.001)
    t = np.asarray(r["t"]); m = t >= t[-1] - WINDOW
    f = lambda k: float(np.mean(np.asarray(r[k])[m]))
    co, hr = f("co"), f("hr")
    return {"map": f("map"), "co": co, "hr": hr, "sv": 1000.0 * co / hr,
            "sbp": f("sbp"), "rpp": hr * f("sbp")}


def titrate(sex, drug, target_map, lo=0.0, hi=8.0, iters=9):
    """Bisect the dose until settled MAP reaches target_map."""
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        got = settle(sex, {"propofol": PROPOFOL_MG_KG, drug: mid}, True)["map"]
        if got < target_map:
            lo = mid
        else:
            hi = mid
    dose = 0.5 * (lo + hi)
    return dose, settle(sex, {"propofol": PROPOFOL_MG_KG, drug: dose}, True)


def main():
    bsa = bsa_mosteller(HEIGHT_CM, WEIGHT_KG)
    print(f"age {AGE:.0f}  {HEIGHT_CM:.0f} cm  {WEIGHT_KG:.1f} kg  BSA {bsa:.3f}")
    print(f"propofol {PROPOFOL_MG_KG} mg/kg proxy   PEEP {PEEP}  PIP {PIP}  RR {RR}")
    print(f"target = {MAP_TARGET_FRAC:.0%} of the model's own awake MAP\n")

    out = {}
    for sex in SEXES:
        awake = settle(sex, None, False)
        anaes = settle(sex, {"propofol": PROPOFOL_MG_KG}, True)
        target = MAP_TARGET_FRAC * awake["map"]
        print(f"  --- {sex} ---")
        print(f"    awake         MAP {awake['map']:6.2f}  CO {awake['co']:5.2f}  HR {awake['hr']:5.1f}")
        print(f"    anaesthetised MAP {anaes['map']:6.2f}  CO {anaes['co']:5.2f}  HR {anaes['hr']:5.1f}")
        print(f"    target MAP    {target:6.2f}")
        for drug in ("phenylephrine", "norepinephrine"):
            dose, st = titrate(sex, drug, target)
            out[(sex, drug)] = (dose, st)
            print(f"    {drug:15s} dose {dose:5.3f}  MAP {st['map']:6.2f}  "
                  f"CO {st['co']:5.2f}  CI {st['co']/bsa:5.2f}  HR {st['hr']:5.1f}  "
                  f"SV {st['sv']:5.1f}  RPP {st['rpp']:7.0f}")

    print("\nPRIMARY — noradrenaline MINUS phenylephrine, at matched MAP")
    print(f"  {'sex':8s} {'dMAP':>7s} {'dCI':>7s} {'dSV':>7s} {'dHR':>7s} {'dRPP':>8s}")
    for sex in SEXES:
        p_ = out[(sex, "phenylephrine")][1]
        n_ = out[(sex, "norepinephrine")][1]
        print(f"  {sex:8s} {n_['map']-p_['map']:+7.2f} "
              f"{(n_['co']-p_['co'])/bsa:+7.3f} {n_['sv']-p_['sv']:+7.2f} "
              f"{n_['hr']-p_['hr']:+7.2f} {n_['rpp']-p_['rpp']:+8.0f}")


if __name__ == "__main__":
    main()
