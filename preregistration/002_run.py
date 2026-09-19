#!/usr/bin/env python3
"""Registration 002 — NIV positive-pressure ventilation crossed with LBNP.

    PYTHONPATH=. python3 preregistration/002_run.py

A 2x2: normovolaemia and simulated central hypovolaemia, each with spontaneous
breathing and with volume-controlled positive-pressure ventilation. The primary
target is the INTERACTION — does positive-pressure ventilation cost more under
hypovolaemia than it does at normal filling?

LBNP IS NOT A MODEL INPUT, so it is substituted by haemorrhage, which is how the
existing suite already treats it: "LBNP -30 mmHg ~ 500-1000 mL central-
hypovolemia equivalent". **That equivalence spans a factor of two, so both ends
are run and the prediction is a BRACKET, not a point.**

The substitution is not exact in kind either. LBNP SEQUESTERS blood below the
seal — it stays in the circulation and filters into the legs — whereas
haemorrhage REMOVES it, so total blood volume differs even when the central
effect is similar. Registered as a caveat rather than hidden.

The study's recovery phase is deliberately not modelled: releasing LBNP restores
volume instantly, while undoing a haemorrhage needs a re-infusion, which is a
different manoeuvre.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from model.circulation import SimParams, run_simulation
from model.patient import build_patient_params, apply_cardiac, bsa_mosteller

# --- cohort ----------------------------------------------------------------
# 15 volunteers, 7 male and 8 female, age 22 (20-30), BMI 23.4 (18.0-26.7).
AGE = 22.0

# SEX IS BRACKETED, NOT CHOSEN. The model takes one sex; the cohort is 7:8, so
# picking either would be arbitrary. Both are run and the span reported — the
# same treatment given to the LBNP magnitude. A narrow bracket would make the
# limitation immaterial, which is itself worth establishing.
SEXES = ("male", "female")

# HEIGHT IS NOT REPORTED. 173 cm assumed for a mixed 7:8 Northern European
# cohort of this age; with the reported BMI of 23.4 that gives 70.0 kg. Stated
# as an assumption, and it matters most for absolute cardiac output, which
# scales with body surface area.
HEIGHT_CM = 173.0
BMI = 23.4
WEIGHT_KG = BMI * (HEIGHT_CM / 100.0) ** 2

# --- ventilator, all taken from the study ----------------------------------
RF          = 14.0    # breaths/min, both modes (subjects trained to synchronise)
PIP         = 14.0    # cmH2O, maximum inspiratory pressure
PEEP        = 1.5     # cmH2O, study set 1 or 2
INSP_TIME_S = 1.25    # median inspiratory time
IE_RATIO    = INSP_TIME_S / (60.0 / RF)   # inspiratory FRACTION of the cycle

# --- LBNP -30 mmHg as a central-hypovolaemia equivalent ---------------------
BLEED_BRACKET = (500.0, 1000.0)
BLEED_START_S, BLEED_DUR_S = 60.0, 30.0   # study induced LBNP abruptly (0.3 s)

DURATION, WINDOW = 600.0, 60.0            # 10-min period, final minute averaged


def run(bleed_ml, mode, sex):
    comps, cardiac = build_patient_params(HEIGHT_CM, WEIGHT_KG, sex=sex,
                                          age_years=AGE)
    p = SimParams(compartments=comps)
    apply_cardiac(p, cardiac)
    p.resp_rate_bpm = RF
    if mode == "ppv":
        p.ventilation_mode = "mechanical"
        p.peep_cmh2o, p.pip_cmh2o, p.ie_ratio = PEEP, PIP, IE_RATIO
    else:
        p.ventilation_mode = "spontaneous"
    if bleed_ml:
        p.hemorrhage_rate_mlmin = bleed_ml / BLEED_DUR_S * 60.0
        p.hemorrhage_start_s    = BLEED_START_S
        p.hemorrhage_duration_s = BLEED_DUR_S
    r = run_simulation(p, duration_s=DURATION, dt=0.001)
    t = np.asarray(r["t"]); m = t >= t[-1] - WINDOW
    f = lambda k: float(np.mean(np.asarray(r[k])[m]))
    return {"map": f("map"), "co": f("co"), "hr": f("hr"), "sv": f("sv")}


def main():
    bsa = bsa_mosteller(HEIGHT_CM, WEIGHT_KG)
    print(f"age {AGE:.0f}  sex bracketed {SEXES}  {HEIGHT_CM:.0f} cm  "
          f"{WEIGHT_KG:.1f} kg  BSA {bsa:.3f}")
    print(f"PPV: RF {RF:.0f}  PIP {PIP}  PEEP {PEEP}  insp fraction {IE_RATIO:.3f}")
    print(f"LBNP -30 mmHg as a bleed of {BLEED_BRACKET[0]:.0f}-{BLEED_BRACKET[1]:.0f} mL\n")

    vols = [(0.0, "normo")] + [(b, f"hypo{b:.0f}") for b in BLEED_BRACKET]
    res = {}
    for sex in SEXES:
        print(f"  --- {sex} ---")
        for bleed, vlabel in vols:
            for mode in ("spont", "ppv"):
                k = (sex, vlabel, mode)
                res[k] = run(bleed, mode, sex)
                c = res[k]
                print(f"    {vlabel:9s} {mode:6s} MAP {c['map']:7.2f}  CO {c['co']:6.2f}"
                      f"  HR {c['hr']:6.1f}  SV {c['sv']:6.1f}")

    def eff(sex, vlabel):
        a, b = res[(sex, vlabel, "spont")], res[(sex, vlabel, "ppv")]
        return (b["map"] - a["map"], b["co"] - a["co"], b["hr"] - a["hr"])

    print("\nEFFECT OF PPV (ppv - spontaneous), within each volaemic state")
    for sex in SEXES:
        for _b, vlabel in vols:
            e = eff(sex, vlabel)
            print(f"  {sex:7s} {vlabel:9s} dMAP {e[0]:+6.2f}  dCO {e[1]:+6.2f}  dHR {e[2]:+6.1f}")

    print("\nPRIMARY — INTERACTION: does PPV cost more under hypovolaemia?")
    print(f"  {'sex':8s} {'bleed':>7s} {'d(dMAP)':>9s} {'d(dCO)':>9s} {'d(dHR)':>9s}")
    for sex in SEXES:
        n = eff(sex, "normo")
        for b in BLEED_BRACKET:
            h = eff(sex, f"hypo{b:.0f}")
            print(f"  {sex:8s} {b:7.0f} {h[0]-n[0]:+9.2f} {h[1]-n[1]:+9.2f} {h[2]-n[2]:+9.1f}")

    print("\nSECONDARY — effect of hypovolaemia alone (spontaneous breathing)")
    for sex in SEXES:
        a = res[(sex, "normo", "spont")]
        for b in BLEED_BRACKET:
            h = res[(sex, f"hypo{b:.0f}", "spont")]
            print(f"  {sex:8s} {b:7.0f} dMAP {h['map']-a['map']:+6.2f}  "
                  f"dCO {h['co']-a['co']:+6.2f}  dHR {h['hr']-a['hr']:+6.1f}")

    print("\nSEX BRACKET WIDTH on the primary interaction (dCO)")
    for b in BLEED_BRACKET:
        vals = [eff(s, f"hypo{b:.0f}")[1] - eff(s, "normo")[1] for s in SEXES]
        print(f"  bleed {b:.0f} mL: {min(vals):+.3f} to {max(vals):+.3f}  "
              f"(width {abs(vals[0]-vals[1]):.3f} L/min)")


if __name__ == "__main__":
    main()
