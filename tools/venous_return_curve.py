"""Construct the model's venous return curve exactly the way Maas 2009 did.

WHY THIS RATHER THAN DERIVING IT FROM MSFP. `tools/resistance_split.py` reports
Rvr as (MSFP - CVP)/CO, which needs MSFP — and MSFP is the one quantity in this
literature whose method is genuinely contested. Maas extrapolates it and gets
18.8; Jellinek (n=10) and Schipke (n=85) stop the heart outright and get 10.2 and
12; this model solves for zero flow and gets 10.4. Deriving Rvr from a contested
number and then declaring Rvr wrong is circular.

Maas's SLOPE is not contested. He measured it directly:

    four 12-second inspiratory holds at plateau pressures 5, 15, 25, 35 cmH2O,
    one minute apart, reading steady-state Pcv and CO over the final 3 seconds,
    then a linear fit through the four points.

    slope = -0.465 +/- 0.151 L/min/mmHg   (baseline, n=12)
          = -0.429 +/- 0.160              (hypovolaemia, 30 deg HUT, p=0.388)
          = -0.389 +/- 0.135              (hypervolaemia, +500 mL, p=0.134)

    Rvr = 1 / |slope|,  and the zero-flow intercept is pmsf.

That is reproducible here: hold the ventilator at a fixed plateau, let the model
settle, read CO and CVP. This tool does exactly that and reports the slope, so
the comparison rests on a measurement rather than on an inference.

It also reproduces Maas's structural finding — the slope is UNALTERED by volume
state (p = 0.388 and 0.134) — which is an assertion the model can be held to
independently of any absolute value.

Usage:  python3 tools/venous_return_curve.py
"""

import sys
import os

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.circulation import SimParams, run_simulation   # noqa: E402
from model.respiration import intrathoracic_pressure       # noqa: E402

# Maas's four plateau pressures, cmH2O.
PLATEAUS = (5.0, 15.0, 25.0, 35.0)
MAAS = {"baseline": -0.465, "hypo": -0.429, "hyper": -0.389}


def hold(plateau_cmh2o, hem_ml=0.0, bolus_ml=0.0, tilt_deg=0.0, dur=45.0):
    """One sustained inspiratory hold. PEEP == PIP gives a flat plateau, which
    is what a hold is; the model then settles to a new steady state."""
    p = SimParams()
    p.ventilation_mode = "mechanical"
    p.peep_cmh2o = plateau_cmh2o
    p.pip_cmh2o = plateau_cmh2o          # no tidal swing: a held plateau
    p.resp_rate_bpm = 12.0
    p.baroreflex_enabled = False          # Maas: holds are too short for reflexes
    if hem_ml:
        p.hemorrhage_rate_mlmin = hem_ml / (20.0 / 60.0)
        p.hemorrhage_start_s, p.hemorrhage_duration_s = 2.0, 20.0
    if bolus_ml:
        p.fluid_bolus_ml = bolus_ml
        p.fluid_bolus_start_s, p.fluid_bolus_duration_s = 2.0, 20.0
    if tilt_deg:
        p.tilt_end_deg = tilt_deg
        p.tilt_onset_s, p.tilt_duration_s = 2.0, 5.0
    r = run_simulation(p, duration_s=dur, dt=0.001, use_baroreflex=False)
    h = int(len(r["t"]) * 0.75)           # last quarter: settled

    # CRITICAL: the model reports TRANSMURAL CVP (respiratory ITP is excluded by
    # design — see the cvp_ts note in circulation.py). A catheter reads
    # INTRALUMINAL pressure. Raising the plateau squeezes the atrium, so its
    # transmural pressure FALLS where a real transducer sees it RISE, and the
    # uncorrected curve comes out with a POSITIVE slope, which is nonsense for a
    # venous return curve. Add ITP back to compare with Maas. Backlog item 31.
    itp = intrathoracic_pressure(0.0, "mechanical", p.resp_rate_bpm,
                                 p.peep_cmh2o, p.pip_cmh2o, p.ie_ratio)
    return (float(np.mean(r["cvp"][h:])) + itp, float(np.mean(r["co"][h:])))


def curve(label, **kw):
    pts = [hold(pl, **kw) for pl in PLATEAUS]
    cvp = np.array([p[0] for p in pts])
    co = np.array([p[1] for p in pts])
    slope, intercept = np.polyfit(cvp, co, 1)
    pmsf = -intercept / slope             # CO = 0
    rvr = (1.0 / abs(slope)) / (1000.0 / 60.0)
    print(f"\n  {label}")
    print(f"    {'Pvent cmH2O':>12} {'CVP lumen':>10} {'CO L/min':>9}")
    for pl, (c, q) in zip(PLATEAUS, pts):
        print(f"    {pl:12.0f} {c:10.2f} {q:9.3f}")
    r2 = np.corrcoef(cvp, co)[0, 1] ** 2
    print(f"    slope {slope:+.3f} L/min/mmHg   r2 {r2:.4f}   "
          f"zero-flow intercept (pmsf) {pmsf:.2f} mmHg   Rvr {rvr:.4f}")
    return slope, pmsf, rvr


print("Model venous return curves, Maas 2009 protocol "
      "(sustained plateaus 5/15/25/35 cmH2O, reflexes off)")
b = curve(f"baseline            (Maas slope {MAAS['baseline']:+.3f})")
h = curve(f"hypovolaemia 500 mL (Maas slope {MAAS['hypo']:+.3f}, p=0.388 vs base)",
          hem_ml=500.0)
y = curve(f"hypervolaemia 500 mL(Maas slope {MAAS['hyper']:+.3f}, p=0.134 vs base)",
          bolus_ml=500.0)

print(f"\n  {'':22s} {'model':>9} {'Maas':>9} {'ratio':>7}")
for tag, (s, _, _), m in (("baseline", b, MAAS["baseline"]),
                          ("hypovolaemia", h, MAAS["hypo"]),
                          ("hypervolaemia", y, MAAS["hyper"])):
    print(f"  {'slope, ' + tag:22s} {s:+9.3f} {m:+9.3f} {abs(s / m):7.2f}")
print(f"\n  Maas's structural finding: the slope is UNALTERED by volume state.")
print(f"    model spread {min(b[0], h[0], y[0]):+.3f} to {max(b[0], h[0], y[0]):+.3f}"
      f"  ({abs(max(b[0], h[0], y[0]) / min(b[0], h[0], y[0])):.2f}x)")
