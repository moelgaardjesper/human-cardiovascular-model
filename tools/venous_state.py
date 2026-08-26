"""Measure the model's mean systemic filling pressure and systemic vascular
compliance the way they are measured in patients, so the comparison with human
data is like-for-like.

WHY THIS EXISTS. Backlog item 28 opened on a number obtained by SUMMING the
compartment compliances: 130.7 mL/mmHg against Maas's measured 64.3 +/- 32.7.
That sum is wrong in a knowable direction. The limb veins use the collapsible
tube law

    P = p_stiffen * (exp(Vs / (C * p_stiffen)) - 1)

whose local compliance is dV/dP = C / (1 + P/p_stiffen) — strictly BELOW the
nominal C at any positive pressure. `thigh_vein` has C = 4.0 and p_stiffen = 12,
so at 10 mmHg it holds 2.18 mL/mmHg, not 4.0. Summing nominal C therefore
overstates the model's real compliance, and item 28's headline ratio has to be
re-derived before anything is changed on the strength of it.

METHOD. Mean systemic filling pressure is the pressure the systemic bed settles
to at zero flow while holding the volume it currently has. Solve

    sum_i V_i(P*) = V_systemic

for P*, using each compartment's own tube law, then report the effective
compliance as sum_i dV_i/dP at P*. Compliance is also reported the way Maas
measures it — a chord, dV / dPmsf across a fluid bolus — because that is what
the human number is and the two differ when the bed is nonlinear.

Usage:  python3 tools/venous_state.py [--bolus ML]
"""

import argparse
import sys
import os

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.circulation import SimParams, run_simulation      # noqa: E402
from model.compartments import IDX                           # noqa: E402

# The systemic bed: everything that is neither pulmonary nor a cardiac chamber.
# Mean SYSTEMIC filling pressure excludes the pulmonary circulation by
# definition; the heart is excluded because at zero flow its chambers are not
# part of the systemic capacitance being measured.
PULMONARY = ("pulmonary_art", "pulmonary_cap", "pulmonary_vein")
CARDIAC = ("right_atrium", "right_ventricle", "left_atrium", "left_ventricle")


def _volume_at(c, p):
    """Volume held by compartment `c` at transmural pressure `p`, via its own
    tube law (the inverse of _vascular_pressure)."""
    if p <= 0.0:
        return c.unstressed_volume + p * c.compliance
    if c.p_stiffen is None:
        return c.unstressed_volume + p * c.compliance
    return c.unstressed_volume + c.compliance * c.p_stiffen * np.log(
        1.0 + p / c.p_stiffen)


def _dvdp_at(c, p):
    """Local compliance dV/dP at pressure `p`."""
    if c.p_stiffen is None or p <= 0.0:
        return c.compliance
    return c.compliance / (1.0 + p / c.p_stiffen)


def solve_msfp(comps, names, target_volume, lo=0.0, hi=200.0):
    """Bisect for the pressure at which these compartments hold target_volume."""
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        v = sum(_volume_at(comps[IDX[n]], mid) for n in names)
        if v < target_volume:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def measure(bolus_ml=0.0, verbose=True):
    p = SimParams()
    p.ventilation_mode = "none"
    p.baroreflex_enabled = False
    if bolus_ml:
        p.fluid_bolus_ml = bolus_ml
        p.fluid_bolus_start_s = 5.0
        p.fluid_bolus_duration_s = 20.0
    r = run_simulation(p, duration_s=90.0, dt=0.001, use_baroreflex=False)

    comps = p.compartments
    names = [c.name for c in comps
             if c.name not in PULMONARY and c.name not in CARDIAC]
    Vmean = r["volumes"][2 * len(r["volumes"]) // 3:].mean(axis=0)
    v_sys = float(sum(Vmean[IDX[n]] for n in names))

    msfp = solve_msfp(comps, names, v_sys)
    c_eff = sum(_dvdp_at(comps[IDX[n]], msfp) for n in names)
    v_unstressed = sum(comps[IDX[n]].unstressed_volume for n in names)
    c_nominal = sum(comps[IDX[n]].compliance for n in names)

    if verbose:
        print(f"{'compartment':20s} {'V now':>8} {'V at MSFP':>10} {'C nom':>7} "
              f"{'C at MSFP':>10} {'loss':>7}")
        for n in names:
            c = comps[IDX[n]]
            print(f"{n:20s} {Vmean[IDX[n]]:8.1f} {_volume_at(c, msfp):10.1f} "
                  f"{c.compliance:7.2f} {_dvdp_at(c, msfp):10.2f} "
                  f"{_dvdp_at(c, msfp) - c.compliance:+7.2f}")

    return dict(msfp=msfp, c_eff=c_eff, c_nominal=c_nominal,
                v_sys=v_sys, v_unstressed=v_unstressed,
                stressed=v_sys - v_unstressed,
                total_bv=float(Vmean.sum()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bolus", type=float, default=500.0,
                    help="fluid bolus (mL) for the chord-compliance measurement")
    a = ap.parse_args()

    base = measure(0.0)
    print()
    print(f"  total blood volume        {base['total_bv']:8.1f} mL")
    print(f"  systemic volume           {base['v_sys']:8.1f} mL")
    print(f"  systemic unstressed       {base['v_unstressed']:8.1f} mL")
    print(f"  systemic stressed         {base['stressed']:8.1f} mL "
          f"({base['stressed'] / base['total_bv'] * 100:.1f} % of blood volume)")
    print()
    print(f"  MSFP (zero-flow solve)    {base['msfp']:8.2f} mmHg")
    print(f"  compliance, NOMINAL sum   {base['c_nominal']:8.1f} mL/mmHg "
          f"  <- what backlog item 28 was opened on")
    print(f"  compliance, at MSFP       {base['c_eff']:8.1f} mL/mmHg "
          f"  <- corrected for the nonlinear limb veins")

    if a.bolus:
        after = measure(a.bolus, verbose=False)
        dv = after["v_sys"] - base["v_sys"]
        dp = after["msfp"] - base["msfp"]
        print(f"\n  after a {a.bolus:.0f} mL bolus:")
        print(f"    systemic volume         {after['v_sys']:8.1f} mL "
              f"({dv:+.1f})")
        print(f"    MSFP                    {after['msfp']:8.2f} mmHg "
              f"({dp:+.2f})")
        print(f"    CHORD compliance dV/dP  {dv / dp if dp else float('nan'):8.1f} "
              f"mL/mmHg  <- Maas's method")

    print("\n  human reference (Maas, ventilated post-cardiac-surgery patients;")
    print("  see docs/reference_values.md for the cohort caveat):")
    print(f"    Csys        64.3 +/- 32.7 mL/mmHg   (0.97 +/- 0.49 per kg)")
    print(f"    stressed    1265 +/- 541 mL         (28.5 +/- 15 % of blood volume)")
    print(f"    Pmsf        18.8-20.9 mmHg")


if __name__ == "__main__":
    main()
