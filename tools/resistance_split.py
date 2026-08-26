"""Where does systemic resistance sit relative to the mean-filling-pressure point?

Maas 2009 (PMID 19237896) measured the venous return curve directly in humans:
slope -0.465 +/- 0.151 L/min/mmHg, giving Rvr = 0.129 mmHg.s/mL, and reports

    Rvr / Rsys = 15 %   at baseline
               = 23 %   with volume loading
               = 15 %   with hypovolaemia

That ratio locates pmsf within the circulation. It is DIMENSIONLESS, which per
CLAUDE.md makes it the most transferable target in the venous literature — it
survives the cohort difference that every absolute in that paper does not.

    Rsys = (MAP - CVP) / CO        Rvr = (MSFP - CVP) / CO

This tool reports the model's split and attributes it per compartment, so the
fix for backlog item 28 can be aimed rather than guessed.

Usage:  python3 tools/resistance_split.py
"""

import sys
import os

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.circulation import SimParams, run_simulation  # noqa: E402
from model.compartments import ARTERIOLAR_SEGMENTS  # noqa: E402
from model.compartments import IDX                                            # noqa: E402
from tools.venous_state import solve_msfp, PULMONARY, CARDIAC                 # noqa: E402

MAAS = dict(rvr=0.1290, rsys=0.8575, ratio=0.145, slope=0.465)


def main():
    p = SimParams()
    p.ventilation_mode = "none"
    p.baroreflex_enabled = False
    r = run_simulation(p, duration_s=60.0, dt=0.001, use_baroreflex=False)

    comps = p.compartments
    h = len(r["volumes"]) // 2
    Vmean = r["volumes"][h:].mean(axis=0)
    names = [c.name for c in comps
             if c.name not in PULMONARY and c.name not in CARDIAC]
    v_sys = float(sum(Vmean[IDX[n]] for n in names))
    msfp = solve_msfp(comps, names, v_sys)

    mapp = float(np.mean(r["map"][h:]))
    cvp = float(np.mean(r["cvp"][h:]))
    co = float(np.mean(r["co"][h:])) * 1000.0 / 60.0   # mL/s

    rsys = (mapp - cvp) / co
    rvr = (msfp - cvp) / co
    ratio = rvr / rsys

    print(f"  MAP {mapp:.1f}   MSFP {msfp:.2f}   CVP {cvp:.2f}   "
          f"CO {co * 60 / 1000:.2f} L/min\n")
    print(f"{'':28s} {'model':>10} {'Maas 2009':>10} {'ratio':>8}")
    print(f"{'Rsys  (MAP-CVP)/CO':28s} {rsys:10.4f} {MAAS['rsys']:10.4f} "
          f"{rsys / MAAS['rsys']:8.2f}")
    print(f"{'Rvr   (MSFP-CVP)/CO':28s} {rvr:10.4f} {MAAS['rvr']:10.4f} "
          f"{rvr / MAAS['rvr']:8.2f}")
    print(f"{'Rvr/Rsys':28s} {ratio * 100:9.1f}% {MAAS['ratio'] * 100:9.1f}% "
          f"{ratio / MAAS['ratio']:8.2f}")
    print(f"{'VR curve slope L/min/mmHg':28s} {1.0 / (rvr * 1000 / 60):10.3f} "
          f"{MAAS['slope']:10.3f} {(1.0 / (rvr * 1000 / 60)) / MAAS['slope']:8.2f}")

    # What would have to change. Hold Rsys, move the split.
    target_rvr = MAAS["ratio"] * rsys
    print(f"\n  To reach Rvr/Rsys = 15 % at unchanged Rsys:")
    print(f"    Rvr must go {rvr:.4f} -> {target_rvr:.4f}  "
          f"(x{target_rvr / rvr:.2f}), i.e. +{(target_rvr - rvr) * co:.2f} mmHg "
          f"of pressure drop moved downstream of pmsf")
    print(f"    arteriolar drop must fall by the same amount to hold MAP")

    # Where the drop currently happens, per segment.
    print(f"\n  Where the systemic pressure drop sits now "
          f"(pressures from the settled state):")
    def pres(n):
        c = comps[IDX[n]]
        vs = Vmean[IDX[n]] - c.unstressed_volume
        if c.p_stiffen is not None and vs > 0:
            return c.p_stiffen * (np.exp(vs / (c.compliance * c.p_stiffen)) - 1.0)
        return vs / c.compliance

    beds = (("upper body", "upper_body_art", "upper_body_vein", "svc"),
            ("renal", "renal_art", "renal_vein", "ivc"),
            ("splanchnic", "splanchnic_art", "splanchnic_vein", "ivc"),
            ("lower body", "lower_body_art", "thigh_vein", "ivc"))
    print(f"    {'bed':14s} {'P_art':>7} {'P_vein':>7} {'P_cav':>7} "
          f"{'arteriolar':>11} {'venous':>8} {'venous %':>9}")
    for tag, art, vein, cav in beds:
        pa, pv, pc = pres(art), pres(vein), pres(cav)
        art_drop, ven_drop = pa - pv, pv - pc
        tot = art_drop + ven_drop
        print(f"    {tag:14s} {pa:7.2f} {pv:7.2f} {pc:7.2f} "
              f"{art_drop:11.2f} {ven_drop:8.2f} "
              f"{100 * ven_drop / tot if tot else float('nan'):8.1f}%")
    print(f"\n  ARTERIOLAR_SEGMENTS carry the arteriolar resistance since item 20: "
          f"{ARTERIOLAR_SEGMENTS}")
    print("  The venous side is each vein's `drain_resistance` plus the caval "
          "conduits.")


if __name__ == "__main__":
    main()
