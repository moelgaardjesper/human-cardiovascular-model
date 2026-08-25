# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A 23-compartment lumped-parameter cardiovascular simulator for clinical use.  
Models blood pressure dynamics, cardiac output, and fluid shifts under:
- Intraoperative posture changes (Trendelenburg, reverse Trendelenburg)
- Vasopressor administration (norepinephrine, phenylephrine, vasopressin, epinephrine)
- Reduced gravity (Mars, Moon, microgravity)

Inputs scale from minimal (MAP + BMI) to full intracardiac monitoring (CO, CVP, PCWP, PAP).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Fast regression suite — the ratchet. ~10 min. This is what CI runs.
pytest

# Slow-dynamics suite — multi-hour simulations, deselected by default.
# ~20-40 min. Run on demand, not routinely.
pytest -m slow

# Everything
pytest -m ""

# Run a single test
pytest tests/test_circulation.py::test_resting_baseline -v

# Start the web server (opens at http://localhost:5000)
python -m api.app
```

Simulation runs at roughly **3x real time**, so a 2-hour scenario costs ~38 min of wall
clock per arm. Budget accordingly before launching long validation runs, and run them in
the background.

## Architecture

```
model/
  compartments.py   23 compartments (index 0-22), Compartment dataclass, IDX dict.
                    Limb veins use a nonlinear collapsible-tube law (p_stiffen)
  heart.py          Time-varying elastance (Suga-Sagawa), Frank-Starling scaling
  gravity.py        Hydrostatic pressure correction: ρgh·sin(α); smooth tilt profile;
                    positional_itp_mmhg() — Trendelenburg intrathoracic pressure
  baroreflex.py     BaroreflexController — 4-step ABR+CPR, impulse response convolution
  respiration.py    Intrathoracic pressure (spontaneous / mechanical), RSA
  slow_dynamics.py  Minutes-to-hours mechanisms on a separate coarse clock:
                    venous stress relaxation, transcapillary refill, (planned)
                    RAAS/ADH and baroreflex resetting. Default OFF
  perfusion.py      Derived-output sub-models: cerebral (CPP/ICP), coronary (Buckberg).
                    Pure outputs — no coupling back into the ODE
  pharmacology.py   Hill-equation PD for NE, phenylephrine, vasopressin, epinephrine,
                    propofol, spinal anaesthesia
  patient.py        Allometric parameter scaling (BSA/Mosteller), 3-tier calibration
  circulation.py    ODE system (_odes), SimParams, run_simulation() — main entry point

api/
  app.py            Flask factory, serves frontend/
  routes.py         POST /api/simulate, GET /api/defaults, POST /api/estimate
  live.py           Real-time mode: threaded sim + SSE stream, mid-run parameter
                    updates, session trend / measured-value drift view

frontend/
  index.html        Single-page UI (no build step)
  js/main.js        Form collection, fetch, chart rendering
  vendor/           Vendored Plotly — the UI must run fully offline, so no CDN
                    assets. Removing this leaves the UI with no plots

tools/
  generate_diagram.py  Regenerates the README compartment diagram (PNG + SVG)
```

### Key data flow

1. `build_patient_params()` in `patient.py` scales compartments from clinical inputs.
2. Caller fills a `SimParams` and passes it to `run_simulation()`.
3. `run_simulation()` steps the ODE with Euler integration (dt = 1 ms), updating the `BaroreflexController` every step.
4. Results (time-series pressures, flows, HR) are returned as a dict and serialised to JSON by the Flask route.

### Compartment index order

See `IDX` dict in `compartments.py`. Cardiac chambers: RA=15, RV=16, LA=20, LV=21.  
State vector `V[0..22]` stores volumes in mL. Pressures are derived at every step — not stored in the state.

### Adding a new intervention

1. Add a PD function to `pharmacology.py` returning the standard `{svr_factor, hr_factor, ...}` dict.
2. Register it in `combined_drug_factors()`.
3. Add a UI input in `frontend/index.html` and wire it in `buildPayload()` in `js/main.js`.

**Watch the `venous_tone_factor` sign.** It multiplies venous *unstressed* volume
(V0), so the convention is inverted relative to the other factors: **< 1 is
venoconstriction** (lowers V0, recruits blood centrally, raises preload/CO) and
**> 1 is venodilation**. α1 pressors venoconstrict (`1 − hill`); propofol and
spinal block venodilate (`1 + hill`). It is applied only to the mobilizable
reservoir (`MOBILIZABLE_VENOUS_RESERVOIR` in `circulation.py` — splanchnic +
upper-body veins), which is the physiology and keeps drug magnitudes at
literature values. This pathway was once assembled but never applied — a dead
variable that silently zeroed all venoconstriction — so two calibration-independent
regression guards in `tests/test_circulation.py` §14 assert the mechanism is live
and correctly signed. Do not weaken them to make a calibration fit.

**`THORACIC_COMPARTMENTS` is anatomy, not a knob.** Intrathoracic pressure is a
*uniform external pressure*: applied around a closed elastic system it produces
no internal flow, so it can only drive flow where a vessel crosses the chest
wall. Membership of that tuple therefore fixes **where the boundaries are**, and
a compartment wrongly left out invents a pressure step at an internal junction.
The aorta, brachiocephalic, SVC and coronary were all missing until 2026-08-25,
which put the whole pleural swing across the *aortic valve* and scaled it with
`1/VALVE_R` — so the valve rebuild silently grew it eightfold. Never add or
remove a compartment here to move a number; argue it from where the vessel
actually is.

## Validation discipline

This project is a clinical model, so a number is only as good as the source behind it.
Every change that touches physiology follows the same loop:

1. **Scope the literature first** — find the source before writing the mechanism.
2. **Implement the minimal version.**
3. **Add a pytest test citing the source** (DOI/PMID in the test docstring).
4. **Add a `docs/validation_log.md` entry** recording what was measured and why.
5. **The full suite must still pass — without loosening any existing assertion.**

The regression suite is a ratchet. If a change cannot leave it green without weakening a
test, that is a finding to report, not a licence to retune.

### Model the physiology, not the result

**Always align the model with physiology as it actually is, rather than tuning it to make
a number come out right.** Work from first principles: what does the vessel, the reflex,
the Starling equation actually do — and then live with whatever the model produces.

**Getting the physiology right will sometimes make a validation number worse. That is
acceptable, and it is information.** A model that agrees with the literature for the wrong
structural reason is worth less than one that disagrees for a reason you understand,
because the first will mislead you the moment you ask it a question nobody has validated.

In practice:

- **Never tune a sourced parameter to hit an endpoint.** If Kf came from Guyton and the
  postcapillary magnitude from Abboud, they are what they are; a shortfall downstream is a
  finding about the structure, not permission to inflate them. Every large gap this project
  has closed turned out to be a wiring or structural error, and each would have been hidden
  by tuning: the dead `venous_tone_factor`, venous compliance 10x low, the arteriolar
  resistance on the wrong side of `*_art`, the postcapillary effect on the wrong site.
- **Prefer a structural fix to a calibration fix**, and when you cannot tell which you are
  making, say so.
- **Do not treat another model's parameter table as ground truth.** Heldt 2002 is this
  model's ancestor, not its validation target — it has 12 compartments to our 23, and its
  own tables mark several values "Estimate". Anchor on quantities measured in humans and
  use a source model only as a starting point or cross-check.
- **Do not encode a known gap as correct.** If the model recovers 4x faster than the
  literature, do not add an assertion that accepts 4x — record the gap and leave the test
  honest.
- **When a test fails after a physiologically-motivated change, ask which is wrong before
  touching either.** Sometimes the test was asserting something its own cited source never
  claimed.

**Check the species before adopting a number as a calibration target.** The fast model is
almost entirely human-validated; the slow-dynamics work drifted onto dog data without
anyone noticing, and it cost real time. A tau of 39 min from dogs turned out to be
untransferable because their vascular compliance is 3.3x higher per kg than the (human-
calibrated) model's. When only animal data exists, **prefer ratios over absolute values** —
a ratio survives a species jump far better than an absolute time constant.

**Record EVERY number from a paper you read, not just the ones you need today.**
`docs/reference_values.md` is the ledger. When a source is read in full, transcribe its
whole relevant table — including values the model has no use for yet — with the PMID/DOI,
the cohort, and a note on what is and is not used. This has already paid off repeatedly:
Gao's atrial tables were fetched for one item and immediately settled the ordering of the
next; Heldt Table 3 was fetched for the pulmonary bed and settled the systemic comparison.
Re-fetching and re-reading a paper costs far more than writing the table down once, and a
number you skipped is a number you will later half-remember and get wrong.

**Do not cite a paper whose numbers you have not read.** A source was once added to the
validation log on the strength of its title; when finally retrieved it reported a value 9x
different and did not support the calibration it was cited for.

### Slow dynamics — three rules

`model/slow_dynamics.py` is gated by `SimParams.slow_dynamics_enabled` (default `False`)
plus per-mechanism switches.

- **Everything is in deviation form** from a resting reference captured at `SETTLE_S`, taken
  from the model's own settled state — *not* from `init_volume`, which is not the true
  equilibrium. Consequence: **slow-dynamics scenarios must settle before being perturbed.**
- **Every new mechanism needs its own switch.** When a second mechanism landed, the first
  one's test silently became a combined test and failed. Validate each phase in isolation
  *and* in combination.
- **Some phases are deliberately under-calibrated**, because a later phase supplies the
  rest of the observed effect. Check the validation log before "fixing" a phase to match a
  literature figure on its own.

## References

- PMC9363491 — primary model basis (21-compartment orthostatic stress model, Heldt-based; expanded to 23 compartments here)  
- Heldt T et al. (2002) J Appl Physiol 92:1239-1254 — foundational lumped-parameter model  
- DOI 10.1038/s41598-022-18831-3 — VoM-PhyS: 3D multiscale blood-flow and heat transfer  
- VaMpy (JORS): https://openresearchsoftware.metajnl.com/articles/10.5334/jors.159 — 1D arterial wave model
