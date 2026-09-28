"""Internal-consistency audit: every place the model states ONE quantity, side by side.

WHY THIS EXISTS
---------------
The model states some physiological quantities in more than one place. Nothing ties
those statements together, so they can disagree without any test failing — each one is
individually plausible, and only the comparison reveals the problem. Backlog item 50 is
the archetype (the reference operating point typed twice), and on 2026-09-27 the resting
sympathetic tone turned out to be stated FOUR times, inconsistently.

This tool needs NO literature. It asks only whether the model agrees with itself. That
makes it cheap to re-run and impossible to argue with: a disagreement here is a defect
by construction, whichever side is wrong.

    CONVERGENCE pins a number.  DIVERGENCE localises a structural error.

Both outcomes are useful, which is why agreements are printed too.

READ THIS BEFORE BELIEVING A FLAG
---------------------------------
`state_dump.py` cried wolf on its first run — three false flags from applying the wrong
implied-pressure law. Every check here prints its two routes and the code location of
each, so a flag can be verified against the source rather than trusted. Some "routes"
are deliberately NOT equivalent and are marked EXPECTED DIFFERENT with the reason; they
are printed because the size of the gap is informative even when its existence is not a
defect.

MOSTLY NOT ASSERTED BY ANY TEST — this is a reporting tool, and CLAUDE.md step 7 says
such things rot. THREE of its checks were promoted to assertions on 2026-09-27 and live in
`tests/test_circulation.py` section 36: the reference operating point, the venous tuple
agreement, and the exchange-bed/capillary-bed match (that one is a strict xfail because it
fails today — backlog item 74). Everything else here is unguarded, because deciding WHICH
of two disagreeing routes is right needs judgement a test cannot carry. Re-run this after
any change to a constant, a compartment or a tuple.

    python tools/consistency_audit.py            # static checks only, instant
    python tools/consistency_audit.py --settle   # adds the checks needing a run
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import math

from model import baroreflex as B
from model import compartments as C
from model import heart as H
from model import patient as P
from model import perfusion as PF
from model import pharmacology as PH
from model import respiration as R
from model import slow_dynamics as S
from model import circulation as CIRC


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

_ROWS = []


def check(quantity, routes, tol_frac=0.10, expected_different=None, note=None):
    """Record one quantity and every route the model offers to it.

    routes: list of (label, value, where). value None = not computable here.
    tol_frac: fractional spread above which the routes are called DISAGREED.
    expected_different: if set, a string saying why the routes need not match.
    """
    _ROWS.append({
        "quantity": quantity,
        "routes": routes,
        "tol": tol_frac,
        "expected_different": expected_different,
        "note": note,
    })


def report():
    n_dis = n_agree = n_info = 0
    for row in _ROWS:
        vals = [v for _, v, _ in row["routes"] if v is not None]
        verdict = "INFO"
        if len(vals) >= 2:
            lo, hi = min(vals), max(vals)
            ref = max(abs(lo), abs(hi)) or 1.0
            spread = (hi - lo) / ref
            if row["expected_different"]:
                verdict = "EXPECTED DIFFERENT"
                n_info += 1
            elif spread > row["tol"]:
                verdict = f"DISAGREE  (spread {spread * 100:.0f} %)"
                n_dis += 1
            else:
                verdict = f"agree     (spread {spread * 100:.1f} %)"
                n_agree += 1
        else:
            n_info += 1

        print()
        print(f"{row['quantity']}")
        print(f"  VERDICT: {verdict}")
        for label, value, where in row["routes"]:
            shown = "not computed here" if value is None else f"{value:>12.4f}"
            print(f"    {label:<44s} {shown}   [{where}]")
        if row["expected_different"]:
            print(f"  WHY THEY DIFFER: {row['expected_different']}")
        if row["note"]:
            for line in row["note"].strip().splitlines():
                print(f"  {line.strip()}")

    print()
    print("=" * 78)
    print(f"{n_dis} disagreed, {n_agree} agreed, {n_info} informational")
    print("=" * 78)
    return n_dis


# ---------------------------------------------------------------------------
# Helpers over the compartment table
# ---------------------------------------------------------------------------

COMP = {c.name: c for c in C.default_compartments()}
SYSTEMIC_VENOUS = CIRC.VENOUS_RESERVOIR
EXCHANGE_BEDS = ("upper_body_vein", "renal_vein", "splanchnic_vein",
                 "thigh_vein", "calf_vein", "foot_vein")


def total(field, names=None):
    names = names or COMP.keys()
    return sum(getattr(COMP[n], field) for n in names)


# ---------------------------------------------------------------------------
# STATIC CHECKS — constants and the compartment table only
# ---------------------------------------------------------------------------

def static_checks():

    # --- 1. The resting operating point ------------------------------------
    check(
        "RESTING MEAN ARTERIAL PRESSURE the model is built around (mmHg)",
        [("baroreflex setpoint (what the reflex defends)", B.MAP_SETPOINT, "baroreflex.MAP_SETPOINT"),
         ("patient-scaling reference operating point", B.REFERENCE_MAP_MMHG, "baroreflex.REFERENCE_MAP_MMHG")],
        note="THEY AGREE BY COINCIDENCE, NOT BY CONSTRUCTION. Item 50 removed patient.py's\n"
             "hard-coded copy — it now imports — but baroreflex.py still writes 93.0 as TWO\n"
             "separate literals. An earlier version of this note claimed item 50 had made them\n"
             "one definition; it had not. Now guarded by\n"
             "test_the_reference_operating_point_is_stated_once_and_consistently.")

    check(
        "RESTING FILLING PRESSURE the model is built around (mmHg)",
        [("baroreflex SVR-arm setpoint", B.CVP_SETPOINT, "baroreflex.CVP_SETPOINT"),
         ("cardiopulmonary HR-arm reference", B.CP_HR_REFERENCE_CVP_MMHG, "baroreflex.CP_HR_REFERENCE_CVP_MMHG"),
         ("patient-scaling reference", B.REFERENCE_CVP_MMHG, "baroreflex.REFERENCE_CVP_MMHG")],
        note="Backlog items 37 and 39. Three numbers for one physiological quantity. "
             "The 4.7 was chosen to match where the model settles; the 3.0 is uncited; "
             "the 5.0 is a patient-scaling reference. Only 3.0 and 4.7 are BOTH used as a "
             "deviation reference, which is what makes the gap operative.")

    # --- 2. Resting sympathetic ARTERIAL tone ------------------------------
    spinal_full = PH.spinal_anaesthesia(1.0)
    check(
        "FRACTION OF SVR THAT IS WITHDRAWABLE SYMPATHETIC TONE",
        [("baroreflex vasodilator limit (1 - svr clip floor)", 1.0 - 0.5, "baroreflex.update clip, svr_factor floor 0.5"),
         ("complete spinal block (1 - svr_factor)", 1.0 - spinal_full["svr_factor"], "pharmacology.spinal_anaesthesia(1.0)")],
        tol_frac=0.10,
        note="A REFLEX CANNOT WITHDRAW MORE TONE THAN EXISTS. The reflex is allowed to "
             "dilate further than removing all sympathetic tone does. "
             "CAVEAT: Malmqvist's block is T4 and spares the upper body, so 38 % is not the "
             "whole sympathetic contribution. This is a flag, not a proof.")

    # --- 3. Resting sympathetic VENOUS tone, in mL -------------------------
    reservoir_v0 = total("unstressed_volume", CIRC.MOBILIZABLE_VENOUS_RESERVOIR)
    propofol_2 = PH.propofol(2.0)["venous_tone_factor"] - 1.0
    propofol_max = PH._hill(1e6, ec50=2.0, e_max=0.12)     # the ceiling, not a dose
    check(
        "VENOUS TONE AVAILABLE TO WITHDRAW, as mL of reservoir unstressed volume",
        [("baroreflex ceiling (v0 clip max 1.0 = zero tone)", 0.0,
          "baroreflex.update clip, v0_vein_factor ceiling 1.0"),
         ("complete spinal block", (spinal_full["venous_tone_factor"] - 1.0) * reservoir_v0,
          "pharmacology.spinal_anaesthesia(1.0)"),
         ("propofol at its e_max ceiling", propofol_max * reservoir_v0,
          "pharmacology.propofol, ec50 2.0 e_max 0.12")],
        note=f"Mobilizable reservoir V0 = {reservoir_v0:.0f} mL "
             f"({' + '.join(CIRC.MOBILIZABLE_VENOUS_RESERVOIR)}).\n"
             "THE CONTRADICTION: the baroreflex says resting venous tone is ZERO, so nothing "
             "can be withdrawn, while two drugs withdraw a definite volume. Backlog item 70 "
             "pass 2. External comparison: Hahn 2022 puts the whole anaesthesia-induced "
             "unstressed-volume rise at 0.5-1.2 L, so BOTH internal figures are far below it.")

    # --- 4. Total blood volume --------------------------------------------
    check(
        "TOTAL BLOOD VOLUME of the reference patient (mL)",
        [("sum of compartment init_volume", total("init_volume"), "compartments.default_compartments()"),
         ("patient-scaling reference", P.BV_REF, "patient.BV_REF")],
        note="BV_REF is the number every patient is scaled against; the init sum is what the "
             "ODE actually starts with. They are the same physical quantity.")

    # --- 5. Pre/post-capillary resistance ratio ---------------------------
    implied = (1.0 - S.CAPILLARY_PRESSURE_FRACTION) / S.CAPILLARY_PRESSURE_FRACTION
    per_bed = {n: COMP[n].resistance / COMP[n].drain_resistance for n in EXCHANGE_BEDS}
    mean_ratio = sum(per_bed.values()) / len(per_bed)
    check(
        "PRE / POST-CAPILLARY RESISTANCE RATIO",
        [("implied by CAPILLARY_PRESSURE_FRACTION = 0.20", implied,
          "slow_dynamics.CAPILLARY_PRESSURE_FRACTION"),
         ("mean of resistance/drain_resistance over the 6 beds", mean_ratio,
          "compartments table")],
        note="Backlog item 18. The constant 0.20 IS R_post/(R_pre+R_post) at a ratio of 4, so "
             "it is a statement about the resistances and can be checked against them.\n"
             "Per bed: " + ", ".join(f"{n.replace('_vein','')} {v:.1f}" for n, v in per_bed.items()))

    # --- 6. Maximum heart rate --------------------------------------------
    hr_from_reflex = 70.0 + 45.0                       # base + the hr_delta clip ceiling
    hr_from_reserve = 70.0 + B.HR_REFLEX_GAIN_BPM + B.CP_HR_RESERVE_BPM
    check(
        "MAXIMUM HEART RATE the model can reach (bpm)",
        [("hard clip in circulation.py", 180.0, "circulation, min(180, ...)"),
         ("baroreflex hr_delta clip ceiling, from base 70", hr_from_reflex,
          "baroreflex.update clip, hr_delta max +45"),
         ("sum of both arms' saturating reserves, from base 70", hr_from_reserve,
          "HR_REFLEX_GAIN_BPM + CP_HR_RESERVE_BPM"),
         ("age law, 220 - age at the reference age", 220.0 - P.__dict__.get("REF_AGE", 55.0)
          if "REF_AGE" in P.__dict__ else 220.0 - 55.0, "220 - aging.REFERENCE_AGE_YEARS")],
        note="Backlog items 55 and 56. Four statements of one ceiling. The 180 is uncited and "
             "is NOT age-scaled although the model has an age law. Note the two reflex routes "
             "differ from each other: the tanh saturates at +30/+40 per arm, so the +45 clip "
             "can only be reached with both arms summing.")

    # --- 7. Brain height --------------------------------------------------
    check(
        "HEIGHT OF THE BRAIN ABOVE THE HEART (m)",
        [("perfusion module constant", PF.H_BRAIN_M, "perfusion.H_BRAIN_M"),
         ("height of the compartment representing the head",
          COMP["upper_body_art"].height_m, "compartments table, upper_body_art")],
        note="Two modules independently state how high the head is, and they match. "
             "A FALSE FLAG WAS REMOVED HERE ON 2026-09-27, recorded so it is not re-added: "
             "the first version also listed brachiocephalic (0.15 m) as a competing route and "
             "called the check a disagreement. It is not — brachiocephalic is a different "
             "vessel. And a second suspicion, that applying a 0.25 m column to the AORTIC "
             "pressure double-counts the aorta's own 0.05 m height, is also wrong: "
             "circulation.py states the convention as P_site = P_transmural - hdp(site), so "
             "compartment pressures are HEART-referenced and the brain's own height is the "
             "right column to apply. Checked against the source before reporting, which is "
             "what state_dump.py's three false flags taught.")

    # --- 8. Systolic fraction --------------------------------------------
    hr = 70.0
    rr = 60.0 / hr
    model_systole = 0.45 * rr
    # Anchor a sqrt(RR) law on the model's own value at 70 bpm, then ask what it
    # gives at 70 bpm (identity) and at 180 — reported in the note, not compared.
    check(
        "MECHANICAL SYSTOLE as a fraction of the cardiac cycle",
        [("model, at every heart rate", 0.45, "heart._normalised_activation, flat above 0.45"),
         ("implied at 180 bpm by a sqrt(RR) law anchored at 70 bpm",
          (model_systole * math.sqrt((60.0 / 180.0) / rr)) / (60.0 / 180.0),
          "derived, Weissler-shape; NOT a sourced coefficient")],
        expected_different="The model's fraction is constant BY CONSTRUCTION. This row exists to "
                           "price backlog item 45, not to flag a contradiction.",
        note="At 180 bpm a sqrt-law systole is ~0.72 of the cycle against the model's 0.45, so "
             "the model gives a tachycardic heart far MORE diastolic filling time than it "
             "should have. Item 45, and the cause of item 56.")

    # --- 9. Membership consistency across the tuples ---------------------
    vr = set(CIRC.VENOUS_RESERVOIR)
    sr = set(S.STRESS_RELAX_COMPARTMENTS)
    mob = set(CIRC.MOBILIZABLE_VENOUS_RESERVOIR)
    cap_veins = {v for _, v, _ in S.CAPILLARY_BEDS}
    print()
    print("MEMBERSHIP OF THE VENOUS / BED TUPLES — set comparisons, not numbers")
    print(f"  VENOUS_RESERVOIR ({len(vr)})            == STRESS_RELAX_COMPARTMENTS ({len(sr)})?  "
          f"{'YES' if vr == sr else 'NO -> ' + str(vr ^ sr)}")
    print(f"  MOBILIZABLE_VENOUS_RESERVOIR ({len(mob)})  subset of VENOUS_RESERVOIR?           "
          f"{'YES' if mob <= vr else 'NO -> ' + str(mob - vr)}")
    print(f"  exchange beds in the ODE ({len(EXCHANGE_BEDS)})       vs CAPILLARY_BEDS in slow dynamics ({len(cap_veins)})")
    print(f"     beds with flow but NO Starling filtration: {sorted(set(EXCHANGE_BEDS) - cap_veins)}")
    print(f"  CAPILLARY_BEDS weights sum to {sum(w for _, _, w in S.CAPILLARY_BEDS):.2f} (should be 1.00)")
    print("  NOTE: VENOUS_RESERVOIR and STRESS_RELAX_COMPARTMENTS are two identical literal")
    print("  tuples in two modules with nothing tying them together — the item 50 shape.")

    # --- 10. Valve conductance, linear vs orifice ------------------------
    # Linear: dP = Q * VALVE_R. Orifice: Q = K*dP/sqrt(dP + dP_c).
    # Compare the pressure drop each produces at a representative peak aortic flow.
    q_peak = 500.0                      # mL/s, representative peak systolic aortic flow
    dp_linear = q_peak * C.AORTIC_R
    k = C.orifice_k("aortic")
    # invert Q = K*dP/sqrt(dP+c) numerically for dP
    lo, hi = 0.0, 100.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        q = k * mid / math.sqrt(mid + C.VALVE_DP_REG)
        if q < q_peak:
            lo = mid
        else:
            hi = mid
    dp_orifice = 0.5 * (lo + hi)
    check(
        f"AORTIC VALVE pressure drop at {q_peak:.0f} mL/s (mmHg)",
        [("linear law, AORTIC_R", dp_linear, "compartments.AORTIC_R = VALVE_R"),
         ("orifice law from a 3.5 cm2 area", dp_orifice, "compartments.orifice_k('aortic')")],
        note="Two statements of the same valve. The orifice path is present but OFF by default "
             "(`valve_orifice_enabled`), so the model carries an anatomical area AND an "
             "unrelated linear resistance. If they disagree, the area is decorative and the "
             "resistance is what the model actually is.")

    # --- 11. Stressed volume and the Pmsf it implies ---------------------
    sys_names = [n for n in COMP if n not in
                 ("pulmonary_art", "pulmonary_cap", "pulmonary_vein",
                  "right_atrium", "right_ventricle", "left_atrium", "left_ventricle")]
    stressed = total("init_volume", sys_names) - total("unstressed_volume", sys_names)
    compliance = total("compliance", sys_names)
    check(
        "SYSTEMIC STRESSED VOLUME / COMPLIANCE, i.e. the static Pmsf it implies (mmHg)",
        [("stressed volume divided by summed compliance", stressed / compliance,
          "compartments table, systemic compartments only")],
        note=f"Systemic stressed volume {stressed:.0f} mL over compliance "
             f"{compliance:.1f} mL/mmHg.\n"
             "ONE ROUTE ONLY here; the second route is the MEASURED arrest plateau, which "
             "needs --settle. They should agree, and if they do not the nonlinear leg-vein "
             "law (p_stiffen) or the pulmonary split is the likely reason.")


# ---------------------------------------------------------------------------
# DYNAMIC CHECKS — one settled run, reused
# ---------------------------------------------------------------------------

def dynamic_checks():
    import numpy as np
    from model.circulation import SimParams, run_simulation

    p = SimParams()
    r = run_simulation(p, duration_s=60.0, dt=0.001)
    t = np.asarray(r["t"])
    tail = t >= t[-1] - 20.0
    m = lambda k: float(np.mean(np.asarray(r[k])[tail]))

    check(
        "RESTING MEAN ARTERIAL PRESSURE (mmHg): stated vs where the model settles",
        [("patient-scaling reference", B.REFERENCE_MAP_MMHG, "baroreflex.REFERENCE_MAP_MMHG"),
         ("measured, settled 40-60 s", m("map"), "run_simulation, default patient")],
        note="A PROPORTIONAL reflex settles ABOVE its setpoint, so a gap is structural and "
             "correct — do not add an integrator. But the PATIENT-SCALING reference is a "
             "different claim: feeding the model its own operating point must return "
             "svr_scale = 1.0. Item 50's xfail.")

    check(
        "RESTING FILLING PRESSURE (mmHg): stated vs where the model settles",
        [("cardiopulmonary HR-arm reference", B.CP_HR_REFERENCE_CVP_MMHG, "baroreflex"),
         ("patient-scaling reference", B.REFERENCE_CVP_MMHG, "baroreflex"),
         ("measured transmural cvp", m("cvp"), "run_simulation"),
         ("measured intraluminal (what a catheter reads)", m("ra_intraluminal"), "run_simulation")],
        note="FOUR numbers. And note the last two are DIFFERENT QUANTITIES — transmural vs "
             "intraluminal — which is the match-the-quantity trap that cost this project six "
             "days. A reference constant should say which one it is; neither does.")

    check(
        "RESTING CARDIAC OUTPUT (L/min): stated vs where the model settles",
        [("patient-scaling reference", B.REFERENCE_CO_LPM, "baroreflex.REFERENCE_CO_LPM"),
         ("measured, settled", m("co"), "run_simulation")],
        note="Item 50 names this the worst of the three reference values.")

    # Arrest plateau -> measured static filling pressure
    pa = SimParams()
    pa.arrest_start_s = 40.0
    pa.arrest_duration_s = 40.0
    pa.baroreflex_enabled = False
    pa.ventilation_mode = "none"
    ra = run_simulation(pa, duration_s=80.0, dt=0.001)
    ta = np.asarray(ra["t"])
    win = (ta >= 74.0) & (ta <= 79.0)
    pmsf_measured = float(np.mean(np.asarray(ra["ra_intraluminal"])[win]))

    sys_names = [n for n in COMP if n not in
                 ("pulmonary_art", "pulmonary_cap", "pulmonary_vein",
                  "right_atrium", "right_ventricle", "left_atrium", "left_ventricle")]
    stressed = total("init_volume", sys_names) - total("unstressed_volume", sys_names)
    compliance = total("compliance", sys_names)
    # Is the hr_delta clip a GUARD, as baroreflex.py claims, or is it OPERATIVE?
    pb = SimParams()
    pb.hemorrhage_rate_mlmin = 3000.0
    pb.hemorrhage_start_s = 20.0
    pb.hemorrhage_duration_s = 30.0
    seen = {"max": -1e9, "min": 1e9}
    _orig = B.BaroreflexController.update

    def spy(self, mm, pp, cvp):
        _orig(self, mm, pp, cvp)
        fv = self._frac_hr_vagal
        raw = -self._gain_hr * (
            fv * (self._r_hr_vagal * math.tanh(self.vagal_outflow / self._scale_hr))
            + (1.0 - fv) * (self._r_hr_symp * math.tanh(-self.cardiac_sympathetic_outflow / self._scale_hr)))
        if self.cp_hr_enabled:
            raw += -self._gain_hr_cp * math.tanh(
                self._symp_hr_cvp * self.sympathetic_outflow_scale / self._scale_hr_cp)
        seen["max"] = max(seen["max"], raw)
        seen["min"] = min(seen["min"], raw)

    B.BaroreflexController.update = spy
    try:
        run_simulation(pb, duration_s=90.0, dt=0.001)
    finally:
        B.BaroreflexController.update = _orig

    check(
        "PEAK REFLEX hr_delta REACHED IN A 1500 mL BLEED (bpm), against its clip",
        [("clip ceiling in baroreflex.update", 45.0, "np.clip(hr_delta, -35, 45)"),
         ("largest PRE-CLIP value actually reached", seen["max"], "measured, 1500 mL bleed")],
        tol_frac=0.02,
        note="baroreflex.py asserts the clip is 'a GUARD, not the operative limit', on the "
             "grounds that the tanh saturates at +/-30 first. That is true of the ARTERIAL arm "
             "alone. With the cardiopulmonary arm enabled (the default) the two sum to a "
             "possible +/-70, so the clip can bind. This measures whether it actually does.\n"
             f"Pre-clip range seen: {seen['min']:+.1f} to {seen['max']:+.1f} bpm.")

    check(
        "STATIC FILLING PRESSURE (mmHg): implied by the table vs measured by arrest",
        [("systemic stressed volume / summed compliance", stressed / compliance,
          "compartments table"),
         ("measured arrest plateau, reflexes off, apnoeic", pmsf_measured,
          "run_simulation with arrest_start_s")],
        expected_different="RESOLVED 2026-09-27: THEY ARE NOT THE SAME QUANTITY. With one-way "
                           "aortic and pulmonic valves the arterial side cannot drain back at "
                           "arrest, so `ra_intraluminal` settles at the VENOUS equilibrium, not "
                           "at the mean circulatory filling pressure. The gap is a convention, "
                           "not a defect.",
        note="The identity Pmsf = stressed volume / compliance still holds where it applies; this\n"
             "pair simply does not test it. **USE A VENOUS RETURN CURVE, NOT AN ARREST**, to\n"
             "compare against a literature Pmsf: four inspiratory holds with a fit to zero flow,\n"
             "as tools/venous_return_curve.py does and as Maas and de Wit both did. Measured that\n"
             "way the model gives 20.81 mmHg, not 7.78. This was the SECOND false flag this tool\n"
             "produced, and both were mine — see the brain-height check.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--settle", action="store_true",
                    help="also run the checks that need a settled simulation (~3 min)")
    args = ap.parse_args()

    print(__doc__.split("READ THIS")[0].strip())
    print()
    print("=" * 78)
    print("STATIC CHECKS — constants and the compartment table, no simulation")
    print("=" * 78)
    static_checks()
    if args.settle:
        print()
        print("=" * 78)
        print("DYNAMIC CHECKS — one settled run plus one arrest run")
        print("=" * 78)
        dynamic_checks()
    n_dis = report()
    return 0 if n_dis == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
