#!/usr/bin/env python3
"""
Full model-state dump with expected values beside every number.

WHY THIS EXISTS. Backlog item 20 — the arteriolar resistance sitting on the wrong
side of each `*_art` compartment — survived for months because nothing displayed
capillary pressure and no test constrained it. Two more bugs found the same day
(`p_stiffen` silently dropped by the patient scaling, leg arterioles unreachable by
the SVR calibration) had the same shape: real, documented, and invisible.

A list of 23 pressures reveals nothing on its own. What catches errors is a number
NEXT TO WHAT IT SHOULD BE. `upper_body_art 8.63` looks unremarkable;
`upper_body_art 8.63 (its own parameters imply 88.0)` is a bug report.

THE PRIMARY CHECK IS SELF-CONSISTENCY, and it needs no external source. Every
vascular compartment's `init_volume` encodes a design pressure:

    P0_implied = (init_volume - unstressed_volume) / compliance

If a compartment does not settle near its own implied P0, then the compartment
table and the flow network disagree about what that compartment IS. That single
comparison would have flagged item 20 immediately: upper_body_art implied 88.0 and
settled at 8.6.

    python3 tools/state_dump.py                  # default supine, 60 s
    python3 tools/state_dump.py --tilt 45        # a scenario
    python3 tools/state_dump.py --slow           # include slow-dynamics panel

Diagnostic only. Runs no model changes and asserts nothing — the pytest suite
remains the ratchet. The nominal ranges below are eyeball guides, NOT validation
targets; the sourced targets live in the test suite and docs/validation_log.md.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from model.circulation import (SimParams, run_simulation, _vascular_pressure,
                               region_volumes)
from model.compartments import IDX
from model.slow_dynamics import (CAPILLARY_BEDS, CAPILLARY_PRESSURE_FRACTION,
                                 oncotic_pressure_mmhg)

DT = 0.001

# Cardiac chambers run on the time-varying elastance model and never read their
# `compliance` field, so the implied-P0 check does not apply to them.
CARDIAC = ("right_atrium", "right_ventricle", "left_atrium", "left_ventricle")

# Nominal resting pressure ranges (mmHg) for eyeballing. Textbook magnitudes, NOT
# sourced validation targets — deliberately wide, meant to catch order-of-magnitude
# errors rather than to grade calibration. Absent = no expectation encoded.
NOMINAL_P = {
    "aorta":            (70, 110),
    "brachiocephalic":  (70, 110),
    "upper_body_art":   (60, 100),
    "upper_body_vein":  (2, 12),
    "svc":              (1, 8),
    "abdominal_aorta":  (70, 110),
    "renal_art":        (60, 100),
    "renal_vein":       (3, 14),
    "splanchnic_art":   (60, 100),
    "splanchnic_vein":  (4, 16),
    "lower_body_art":   (60, 110),
    "thigh_vein":       (5, 20),
    "calf_vein":        (5, 22),
    "foot_vein":        (5, 25),
    "ivc":              (1, 10),
    "pulmonary_art":    (10, 25),
    "pulmonary_cap":    (5, 15),
    "pulmonary_vein":   (4, 14),
    # Not an arterial compartment despite the name: its resistance is upstream,
    # its own parameters imply ~10 mmHg, and perfusion.py never reads its
    # pressure (coronary perfusion pressure is computed as DBP - LVEDP). It is
    # a flow/volume bookkeeping compartment. An arterial range here was a false
    # flag on the first run of this tool.
    "coronary":         (5, 20),
}

# Nominal capillary pressure. Human mid-capillary is usually quoted 15-25 mmHg;
# Maspers 1990 measured 16.7 in cat skeletal muscle at a venous pressure of 7.
NOMINAL_PC = (15.0, 25.0)


def settle(tilt=0.0, duration=60.0, slow=False, ventilation="none"):
    p = SimParams()
    p.tilt_start_deg = p.tilt_end_deg = tilt
    p.tilt_onset_s = 5.0
    p.ventilation_mode = ventilation
    p.slow_dynamics_enabled = slow
    r = run_simulation(p, duration_s=duration, dt=DT)
    keep = slice(2 * len(r["map"]) // 3, None)
    V = r["volumes"][2 * len(r["volumes"]) // 3:].mean(axis=0)
    comp = p.compartments
    P = np.array([_vascular_pressure(V[k], c.unstressed_volume, c.compliance,
                                     getattr(c, "p_stiffen", None))
                  for k, c in enumerate(comp)])
    scalars = {k: float(np.mean(r[k][keep]))
               for k in ("map", "co", "cvp", "sv", "hr")}
    return p, comp, V, P, scalars, r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tilt", type=float, default=0.0)
    ap.add_argument("--duration", type=float, default=60.0)
    ap.add_argument("--slow", action="store_true")
    ap.add_argument("--ventilation", default="none")
    args = ap.parse_args()

    p, comp, V, P, s, r = settle(args.tilt, args.duration, args.slow,
                                 args.ventilation)

    print(f"\nscenario: tilt {args.tilt:+.0f} deg, {args.duration:.0f} s, "
          f"ventilation {args.ventilation}, slow dynamics "
          f"{'ON' if args.slow else 'off'}")
    print(f"MAP {s['map']:.2f}   CO {s['co']:.3f}   CVP {s['cvp']:.3f}   "
          f"SV {s['sv']:.1f}   HR {s['hr']:.0f}   BV {V.sum():.0f} mL")

    # ---- compartment table -------------------------------------------------
    print(f"\n{'compartment':20s} {'vol':>8s} {'press':>8s} {'own P0':>8s} "
          f"{'dev':>7s} {'nominal':>12s}")
    print("-" * 70)
    flags = []
    for k, c in enumerate(comp):
        if c.name in CARDIAC:
            # Cardiac chambers use time-varying elastance; the compliance-based
            # pressure is meaningless for them, so print volume only rather than a
            # number that looks like a pressure and is not one.
            print(f"{c.name:20s} {V[k]:8.1f} {'(elastance)':>8s}")
            continue
        implied = ""
        dev = ""
        if c.name not in CARDIAC and c.compliance:
            # Use the compartment's OWN pressure law, not the linear one — the
            # limb veins carry p_stiffen and a linear implied-P0 understates them
            # by ~40%, which produced false flags on the first run of this tool.
            p0 = _vascular_pressure(c.init_volume, c.unstressed_volume,
                                    c.compliance, getattr(c, "p_stiffen", None))
            implied = f"{p0:8.1f}"
            # Ratio, not difference: an order-of-magnitude error is the target.
            if p0 > 1.0:
                ratio = P[k] / p0 if p0 else float("inf")
                dev = f"{ratio:6.2f}x"
                if ratio < 0.5 or ratio > 2.0:
                    flags.append(
                        f"{c.name}: settles at {P[k]:.2f} mmHg but its own "
                        f"init_volume/compliance imply {p0:.1f} ({ratio:.2f}x)")
        nom = ""
        rng = NOMINAL_P.get(c.name)
        if rng:
            nom = f"{rng[0]:.0f}-{rng[1]:.0f}"
            if not (rng[0] <= P[k] <= rng[1]):
                nom += " !"
                flags.append(
                    f"{c.name}: {P[k]:.2f} mmHg outside nominal {rng[0]}-{rng[1]}")
        print(f"{c.name:20s} {V[k]:8.1f} {P[k]:8.2f} {implied:>8s} {dev:>7s} "
              f"{nom:>12s}")

    # ---- Starling panel per bed -------------------------------------------
    print(f"\n{'exchange bed':20s} {'P_art':>7s} {'P_vein':>7s} {'Pc':>7s} "
          f"{'Kf share':>9s}   nominal Pc {NOMINAL_PC[0]:.0f}-{NOMINAL_PC[1]:.0f}")
    print("-" * 70)
    weighted = 0.0
    for art, ven, share in CAPILLARY_BEDS:
        pa, pv = P[IDX[art]], P[IDX[ven]]
        pc = pv + CAPILLARY_PRESSURE_FRACTION * (pa - pv)
        weighted += share * pc
        mark = "" if NOMINAL_PC[0] <= pc <= NOMINAL_PC[1] else "  !"
        print(f"{ven:20s} {pa:7.2f} {pv:7.2f} {pc:7.2f} {share:9.2f}{mark}")
        if mark:
            flags.append(f"{ven} bed: Pc {pc:.2f} outside nominal "
                         f"{NOMINAL_PC[0]:.0f}-{NOMINAL_PC[1]:.0f} mmHg")
    print(f"{'weighted':20s} {'':7s} {'':7s} {weighted:7.2f}")

    # ---- regions -----------------------------------------------------------
    print("\nregion volumes (mL):")
    for region, vol in region_volumes(V).items():
        print(f"  {region:10s} {vol:8.1f}")

    if args.slow and "plasma_volume" in r:
        n = len(r["plasma_volume"])
        late = slice(2 * n // 3, None)
        print("\nslow-dynamics state:")
        for key, unit in (("plasma_volume", "mL"), ("haematocrit", ""),
                          ("interstitial_volume", "mL"),
                          ("oncotic_pressure", "mmHg")):
            val = float(np.nanmean(r[key][late]))
            print(f"  {key:22s} {val:9.3f} {unit}")

    # ---- verdict -----------------------------------------------------------
    print("\n" + "=" * 70)
    if flags:
        print(f"{len(flags)} THING(S) TO LOOK AT")
        for f in flags:
            print(f"  - {f}")
        print("\nA flag is a prompt to investigate, not a failure. The 'own P0'"
              "\ncolumn is the load-bearing one: a compartment far from the"
              "\npressure its own parameters imply means the compartment table and"
              "\nthe flow network disagree about what it is.")
    else:
        print("Nothing flagged: every compartment sits near the pressure its own "
              "parameters imply, and within nominal range.")


if __name__ == "__main__":
    main()
