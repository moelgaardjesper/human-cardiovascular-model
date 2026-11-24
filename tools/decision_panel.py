"""The decision panel: a fixed, fast subset of the suite for choosing between candidate variants.

WHY (Jesper, 2026-11-23): a candidate used to wait ~4 h for the full suite before we learnt whether it helped. Most tests
do not move for a given change. The panel runs ~24 DECISIVE tests in parallel shards (~30-40 min), scores every variant on
the same targets, and only the winner goes to the full suite.

THE GUARDRAIL — read before using it:
  * Variants must be PHYSIOLOGICALLY DISTINCT and PRE-REGISTERED (validation log), not a grid over one number. A search over
    a parameter on these tests is fitting, and this project has lost a month to grids that never converged.
  * The panel CHOOSES; the rest of the suite VALIDATES. A winner is adopted only after the full suite, by the usual rules.
  * The panel's membership is FIXED. Changing it to make a candidate look better defeats it; change it only between
    comparisons, with a dated note below.

WHAT IT REPORTS, per variant:
  * outcome of each panel test run with --runxfail (so a strict xfail reports its real pass / fail, not "xfailed");
  * every scorecard row the panel tests emit (tests/scorecard.py), and the AGGREGATE: mean |z_sd| over rows with an SD
    (lower is closer to man), plus the count of rows beyond 1 and 2 SD;
  * a side-by-side table of every variant run under the same --out directory.

USAGE
  python tools/decision_panel.py run  --root <repo copy> --tag <name> [--out DIR] [--shards 6]
  python tools/decision_panel.py table [--out DIR]

PANEL MEMBERSHIP — 2026-11-23 (first version); 2026-11-24 the two Negishi heart-volume tests added (a new comparison round:
re-run the baseline before comparing variants against it). Groups share an expensive module fixture and must stay in one shard.
"""
import argparse
import json
import os
import subprocess
import sys

T = "tests/test_circulation.py::"

# Each inner tuple is one fixture group (kept together in one shard).
PANEL = [
    # resting anchors
    ("test_resting_baseline", "test_ra_pressure_baseline_richter2021"),
    ("test_supine_baseline_sejersen2022", "test_hdt20_normovolemic_sejersen2022"),
    # mild tilt, head-up (problem 1)
    ("test_mild_tilt_moves_cvp_and_stroke_volume_as_in_man_petersen2014",),
    ("test_heart_rate_does_not_rise_at_20_deg_head_up_kostas2014",
     "test_stroke_volume_falls_little_at_20_deg_head_up_kostas2014"),
    ("test_young_raise_mean_pressure_on_60_deg_tilt_white1997",),
    ("test_volume_state_shifts_venous_return_curve_without_rotating_it_maas2009",),
    # head-down and leg raise
    ("test_head_down_wedge_rise_as_in_man_van_lieshout2005",),
    ("test_abdomen_receives_red_cells_head_down_bivins1985",),
    ("test_trendelenburg_minus15_cvp_likhvantsev2025",),
    ("test_leg_raise_and_head_down_magnitudes_sejersen2022",),
    ("test_plr_normovolaemic_non_responder_monnet2016",),
    # real blood loss
    ("test_cvp_falls_as_in_johnson2014_controlled_blood_loss",
     "test_map_is_held_in_johnson2014_blood_loss",
     "test_heart_rate_rises_in_johnson2014_blood_loss"),
    ("test_graded_hemorrhage_monotonic_lie2023",),
    # loading and the heart's filling relations
    ("test_lv_filling_pressure_per_volume_follows_bhella2014",
     "test_right_and_left_filling_pressures_fall_together_bhella2014",
     "test_sac_carries_most_of_a_filling_load_bhella2014"),
    ("test_mild_unloading_empties_the_atrium_not_the_ventricles_oren1993",),
    ("test_pulmonary_bed_on_a_colloid_load_giuntini1966",),
    # legs
    ("test_calf_loses_man_s_share_of_its_blood_on_elevation_warren1992",),
    # the heart's volume under gravity — added 2026-11-24 (Negishi 2017; the defect behind problem 1 and the 60 deg collapse)
    ("test_heart_loses_little_volume_at_22_deg_negishi2017", "test_heart_keeps_most_of_its_volume_at_80_deg_negishi2017"),
]
PANEL_TESTS = [t for g in PANEL for t in g]


def _shards(n):
    """Spread fixture groups over n shards, largest groups first (a crude cost proxy)."""
    out = [[] for _ in range(n)]
    for g in sorted(PANEL, key=len, reverse=True):
        min(out, key=len).extend(g)
    return [s for s in out if s]


def run(root, tag, out, n_shards):
    root, out = os.path.abspath(root), os.path.abspath(out)
    d = os.path.join(out, tag)
    os.makedirs(d, exist_ok=True)
    procs = []
    for i, shard in enumerate(_shards(n_shards)):
        env = dict(os.environ, SCORECARD_PATH=os.path.join(d, f"score_{i}.json"))
        cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--runxfail", "-rA",
               *[T + t for t in shard]]
        log = open(os.path.join(d, f"out_{i}.txt"), "w")
        procs.append((subprocess.Popen(cmd, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT), log))
    for p, log in procs:
        p.wait()
        log.close()
    summary = summarise(d)
    with open(os.path.join(d, "summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1)
    print(json.dumps({k: summary[k] for k in ("tag", "passed", "failed", "mean_abs_z_sd", "rows_over_1sd",
                                               "rows_over_2sd", "n_rows")}))


def summarise(d):
    outcomes, rows = {}, []
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f)
        if f.startswith("out_"):
            for line in open(p):
                for word in ("PASSED", "FAILED", "ERROR"):
                    if line.startswith(word + " ") and "::" in line:
                        outcomes[line.split("::")[1].split()[0]] = word.lower()
        elif f.startswith("score_"):
            rows += [r for r in json.load(open(p)) if r["test"] in PANEL_TESTS]
    z = [abs(r["z_sd"]) for r in rows if r.get("z_sd") is not None]
    # Second aggregate (2026-11-23): rows scored only against an SE (Johnson's bleed etc.) never enter z_sd. Use z_se where
    # there is no z_sd, so every scored row counts. Mixes two spreads: report it BESIDE mean |z_sd|, never instead of it.
    z_any = [abs(r["z_sd"]) if r.get("z_sd") is not None else abs(r["z_se"]) for r in rows
             if r.get("z_sd") is not None or r.get("z_se") is not None]
    return {
        "tag": os.path.basename(d),
        "passed": sum(v == "passed" for v in outcomes.values()),
        "failed": sum(v != "passed" for v in outcomes.values()),
        "missing": [t for t in PANEL_TESTS if t not in outcomes],
        "outcomes": outcomes,
        "mean_abs_z_sd": round(sum(z) / len(z), 3) if z else None,
        "rows_over_1sd": sum(v > 1 for v in z),
        "rows_over_2sd": sum(v > 2 for v in z),
        "n_rows": len(z),
        "mean_abs_z_any": round(sum(z_any) / len(z_any), 3) if z_any else None,
        "n_rows_any": len(z_any),
        "rows": [{k: r.get(k) for k in ("test", "quantity", "model", "mean", "z_sd", "z_se")} for r in rows],
    }


def table(out):
    out = os.path.abspath(out)
    sums = []
    for tag in sorted(os.listdir(out)):
        p = os.path.join(out, tag, "summary.json")
        if os.path.exists(p):
            sums.append(json.load(open(p)))
    if not sums:
        print("no summaries under", out)
        return
    print("| variant | passed | failed | mean abs z (SD rows) | rows > 1 SD | rows > 2 SD | mean abs z (all scored rows) |")
    print("|---|---|---|---|---|---|---|")
    for s in sums:
        print(f"| {s['tag']} | {s['passed']} | {s['failed']} | {s['mean_abs_z_sd']} | {s['rows_over_1sd']} | "
              f"{s['rows_over_2sd']} | {s.get('mean_abs_z_any')} (n {s.get('n_rows_any')}) |")
    print("\nper test (P = passed, F = failed):")
    for t in PANEL_TESTS:
        print(f"  {t[:70]:70s} " + " ".join((s["outcomes"].get(t, "?")[0].upper()) for s in sums))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--root", required=True)
    r.add_argument("--tag", required=True)
    r.add_argument("--out", default="panel_runs")
    r.add_argument("--shards", type=int, default=6)
    t = sub.add_parser("table")
    t.add_argument("--out", default="panel_runs")
    a = ap.parse_args()
    run(a.root, a.tag, a.out, a.shards) if a.cmd == "run" else table(a.out)
