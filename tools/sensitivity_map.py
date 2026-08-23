#!/usr/bin/env python3
"""
Stage 2 of the item-20 diagnostic: which parameters move CAPILLARY PRESSURE
without disturbing the outputs the test suite already validates?

Backlog item 20 says the systemic pre/post-capillary resistance ratio is ~25
where physiology says ~4, which pins capillary pressure to venous pressure. The
question that decides whether that is fixable by re-calibration or needs a
topology change is:

    is there any direction in parameter space that moves Pc but leaves
    MAP, CO and CVP where the literature says they should be?

If such directions exist, item 20 is a constrained re-fit. If they do not, no
amount of re-tuning will work and the compartment structure has to change. That
is worth knowing BEFORE anyone starts editing.

Method: perturb each compartment's resistance and compliance one at a time by
+/-20%, measure the fractional response of MAP, CO, CVP and volume-weighted Pc,
and report

    selectivity = |dPc/Pc| / max(|dMAP/MAP|, |dCO/CO|, |dCVP/CVP|)

High selectivity = a free direction: buys capillary pressure cheaply in terms of
the validated outputs. Selectivity near or below 1 = the parameter drags the
validated outputs with it and cannot be used.

    python3 tools/sensitivity_map.py                 # full sweep, ~30 min
    python3 tools/sensitivity_map.py --quick         # resistances only, ~15 min

Diagnostic only. Runs simulations, changes no model code, asserts nothing.
"""
import argparse
import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from model.circulation import SimParams, run_simulation, _vascular_pressure
from model.compartments import IDX
from model.slow_dynamics import CAPILLARY_BEDS, CAPILLARY_PRESSURE_FRACTION

DT = 0.001
DURATION = 60.0        # past the ~40 s settling transient (backlog item 16)
DELTA = 0.20           # +/-20% perturbation


def measure(compartments=None):
    """Steady-state panel: MAP, CO, CVP and volume-weighted capillary pressure."""
    p = SimParams() if compartments is None else SimParams(compartments=compartments)
    p.baroreflex_enabled = True          # the condition the suite validates under
    p.ventilation_mode = "none"          # remove respiratory modulation from the signal
    p.slow_dynamics_enabled = False      # isolate the passive network from filtration
    r = run_simulation(p, duration_s=DURATION, dt=DT)

    keep = slice(2 * len(r["map"]) // 3, None)     # last third
    out = {k: float(np.mean(r[k][keep])) for k in ("map", "co", "cvp")}

    comp = p.compartments
    V = r["volumes"][2 * len(r["volumes"]) // 3:].mean(axis=0)
    P = np.array([_vascular_pressure(V[k], c.unstressed_volume, c.compliance,
                                     getattr(c, "p_stiffen", None))
                  for k, c in enumerate(comp)])
    pc = 0.0
    for art, ven, share in CAPILLARY_BEDS:
        pa, pv = P[IDX[art]], P[IDX[ven]]
        pc += share * (pv + CAPILLARY_PRESSURE_FRACTION * (pa - pv))
    out["pc"] = float(pc)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true",
                    help="resistances only")
    args = ap.parse_args()

    base_params = SimParams()
    names = [c.name for c in base_params.compartments]
    fields = ["resistance"] if args.quick else ["resistance", "compliance"]

    sys.stderr.write("baseline...\n")
    base = measure()
    sys.stderr.write(f"  MAP {base['map']:.2f}  CO {base['co']:.3f}  "
                     f"CVP {base['cvp']:.3f}  Pc {base['pc']:.3f}\n")

    rows = []
    total = len(names) * len(fields)
    done = 0
    for name in names:
        for field in fields:
            done += 1
            sys.stderr.write(f"  [{done}/{total}] {name}.{field}\n")
            sys.stderr.flush()
            resp = {}
            for sign in (+1, -1):
                comps = copy.deepcopy(base_params.compartments)
                c = comps[IDX[name]]
                val = getattr(c, field)
                if val is None or val == 0:
                    resp = None
                    break
                setattr(c, field, val * (1.0 + sign * DELTA))
                try:
                    resp[sign] = measure(comps)
                except Exception as exc:                        # noqa: BLE001
                    sys.stderr.write(f"      failed: {type(exc).__name__}\n")
                    resp = None
                    break
            if not resp:
                continue

            # Central difference, as a fractional change per unit fractional
            # change in the parameter (i.e. a normalised elasticity).
            d = {}
            for k in ("map", "co", "cvp", "pc"):
                hi, lo = resp[+1][k], resp[-1][k]
                if not np.isfinite(hi) or not np.isfinite(lo) or base[k] == 0:
                    d[k] = float("nan")
                else:
                    d[k] = ((hi - lo) / (2 * DELTA)) / base[k]

            cost = max(abs(d["map"]), abs(d["co"]), abs(d["cvp"]))
            sel = abs(d["pc"]) / cost if cost > 1e-9 else float("inf")
            rows.append((f"{name}.{field}", d, sel))

    rows.sort(key=lambda r: (-r[2] if np.isfinite(r[2]) else -1e18))

    print(f"\nbaseline: MAP {base['map']:.2f}  CO {base['co']:.3f}  "
          f"CVP {base['cvp']:.3f}  Pc {base['pc']:.3f}")
    print(f"perturbation +/-{DELTA*100:.0f}%, elasticities (fractional out per "
          f"fractional in)\n")
    print(f"{'parameter':30s} {'dPc':>8s} {'dMAP':>8s} {'dCO':>8s} {'dCVP':>8s} "
          f"{'selectivity':>12s}")
    print("-" * 82)
    for name, d, sel in rows:
        if abs(d["pc"]) < 1e-4 and sel < 1.0:
            continue                     # inert: moves nothing worth reporting
        s = "inf" if not np.isfinite(sel) else f"{sel:.2f}"
        print(f"{name:30s} {d['pc']:+8.4f} {d['map']:+8.4f} {d['co']:+8.4f} "
              f"{d['cvp']:+8.4f} {s:>12s}")

    useful = [r for r in rows if np.isfinite(r[2]) and r[2] > 2.0
              and abs(r[1]["pc"]) > 1e-3]
    print(f"\n{'='*82}")
    if useful:
        print(f"FREE DIRECTIONS (selectivity > 2, meaningful Pc effect): {len(useful)}")
        for name, d, sel in useful:
            print(f"  {name:30s} moves Pc {d['pc']:+.4f} per unit, "
                  f"selectivity {sel:.1f}")
        print("\nItem 20 is reachable by constrained re-fit along these axes.")
    else:
        print("NO FREE DIRECTIONS FOUND.")
        print("Every parameter that moves Pc drags MAP/CO/CVP with it by a "
              "comparable or larger fraction.")
        print("Item 20 is NOT a re-calibration problem — it needs a topology "
              "change (a genuine pre/post split inside each exchange bed).")


if __name__ == "__main__":
    main()
