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

# Fast regression suite — the ratchet. **~100 min** (measured 2026-09-28:
# 112 passed, 15 xfailed, 1 h 39 min 34 s; it was 1 h 19 min the day before,
# and the item 70 pass 2 tests added the difference). This file said ~10 min and
# pytest.ini said ~20 until then; the blind-phase fixtures added in step 2
# of the v1.1 plan are long multi-arm runs and the figure never moved with
# them. This is what CI runs.
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

Simulation runs at roughly **2.2x real time** (measured 2026-08-30; this file said 3x until
2026-09-18, and the model has grown since the original figure). Budget from 2.2x: a 2 h
scenario costs ~55 min per arm, 12 h costs ~5.5 h, 24 h costs ~11 h. Run long validation in
the background. `pytest.ini` carries the same table.

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
                    RAAS/ADH and (planned) baroreflex resetting. Default ON since `66b6231`
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

tools/                 Reporting and audit tools. NONE of them is asserted by a test —
                       see step 7 of the validation discipline, which exists because of it
  generate_diagram.py  Regenerates the README compartment diagram (PNG + SVG)
  validation_table.py  Literature target vs model value. REPRESENTATIVE, not exhaustive
  source_index.py      Every cited PMID/PMC/DOI and the test asserting it — derived
  check_insample.py    Is a study already in the model? Gate for the blind phase
  emit_freeze.py       Emits the whole frozen artefact from one command
  verify_freeze.py     Checks an artefact against its manifest; refuses local paths
  consistency_audit.py Every place the model states ONE quantity, side by side. Needs NO
                       literature — asks only whether the model agrees with itself, so a
                       disagreement is a defect whichever side is wrong. `--settle` adds
                       the checks needing a run. 10 of 16 disagreed on 2026-09-27
  state_dump.py        Full model state with expected values beside every number
  parameter_audit.py   Provenance and constraint status of every parameter
  sensitivity_map.py, resistance_split.py, venous_return_curve.py, venous_state.py
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
6. **Re-measure the headline claim of any open backlog item touching the same
   compartments**, and annotate the entry with a dated claim-versus-measured table.
7. **Re-measure every number the change touches in `README.md`** — and withdraw,
   in the README itself, any claim the change refutes.

The regression suite is a ratchet. If a change cannot leave it green without weakening a
test, that is a finding to report, not a licence to retune.

### Assert through the code path, not alongside it

**A guard must be able to fail. Break the mechanism and watch it fire — if it stays green,
it is not a guard.** Two ways to get this wrong, and both happened on 2026-09-29:

- **It reads the wrong object.** Section 15 watched `BaroreflexController`, so it slept
  through a resting venous tone added in `_odes`.
- **It mirrors the formula it guards.** The repair recomputed `1/(1 - tone)` inside the
  test. Deleting that factor from `circulation.py` left the repaired test green. Section 38
  drives the same invariant through `run_simulation` and failed at once.

The second is worse, because it looks like coverage of exactly the right thing. **Prefer a
test that runs the model to one that recomputes it**, and verify by sabotage before trusting
a new guard.

**And before rewriting a guard that did not fire, ask whether it was measuring the right
QUANTITY.** Section 15's real defect was that Abboud measured venous distensibility — a
compliance — while the model's tone acts on unstressed volume. The guard could never have
fired, and widening it would not have helped.

**Step 6 exists because backlog entries go stale SILENTLY.** An item gets fixed as a side
effect of other work and nothing closes it. Three instances were found in a single audit on
2026-09-01: item 20's pre/post-capillary ratio (claimed 25, measured 4.0 — fixed by
`5ff2317`, which was aimed at a wiring error), item 24's "the ventricles do not empty"
(claimed LVEF 40.8 %, measured 61.8 % — closed by the chamber rebuild, which was aimed at
item 23), and a note claiming Luu's age tables were unavailable five days after they were
transcribed. **Also re-measure BEFORE acting on an item** — one of those stale entries was
picked as the next piece of work and the error was only caught because the first
measurement disagreed with the entry.

Staleness is not all-or-nothing: item 30 in the same audit had an exactly-correct pressure
claim beside a volume claim that was 35x out. Check each number, not the entry.

**Step 7 exists because the README is the document with the widest readership and the
weakest defences.** Steps 5 and 6 both assume something is watching — a test that fails, or
a backlog entry someone re-reads before acting on it. **Nothing watches published prose.**

The instance that put this rule here, 2026-09-18: the README stated that resting MAP ~96 sat
against "a literature expectation nearer 77 ± 14 for a 55-year-old" and called it *the
largest open discrepancy in the resting operating point*. That claim had been refuted days
earlier — the 77 ± 14 came from a cohort aged 25 ± 3, and age-matched against McEniery the
model sits inside 0.1 SD. The correction reached the backlog and the working notes. It never
reached the README, so **the repository's front page advertised a defect the project had
already disproved, while the private notes were correct.** Fixing a claim privately is not
withdrawing it publicly.

Found in the same pass: baseline haemodynamics in `docs/known_model_limitations.md` two
months stale (MAP 88 / CO 4.5 / CVP 3.2 against a measured 95.4 / 5.99 / 4.36), a limitation
that had silently RESOLVED while the document still warned readers away from the output
(absolute `ankle_p`, ~24 mmHg when written, 82.6 now), and a validation table comparing a
−15° tilt against a meta-analysis pooling −5° to −45°.

**The general rule this generalises to: anything that REPORTS numbers but ASSERTS nothing
rots undetected.** That includes `README.md`, `FREEZE.md`, the reporting tools in `tools/`,
and every document written to be dropped into a manuscript. The ratchet does not reach them.
Re-measure them on a schedule, because nothing will fail to remind you.

**What survives such a pass is as informative as what breaks.** The ankle–brachial section
recommended validating the Δ-gradient rather than absolute pressures. Every absolute in that
table moved 50–65 mmHg across a year of structural change; the Δ at 45° moved 1.8 mmHg. A
target chosen because it *ought* to be robust turned out to be robust — which is an argument
for choosing validation targets that way in the first place.

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

### Name the convention where the number is defined

**Every pressure constant must say three things: which SITE, TRANSMURAL or INTRALUMINAL, and
over what WINDOW.** An unstated convention is indistinguishable from a wrong value, so this
is not documentation — it is what makes a comparison possible at all.

Measured on the reference patient, 2026-09-27: central aortic MAP 95.41 against a brachial
cuff 88.95 (**6.47 mmHg**); CVP transmural 4.39 against intraluminal 2.34 (**2.05 mmHg**,
and larger under positive-pressure ventilation).

**The cost of not doing it, three times on record:** a finger pressure compared against an
integrated central one (about 9 of an 11 mmHg "error"); a transmural CVP fitted where a
catheter reading belonged, which made a venous return curve slope come out POSITIVE; and
`build_patient_params` comparing an entered CUFF pressure against a CENTRAL reference, which
leaves `svr_scale` about 5 % low for every patient built from a measurement (item 77, found
by writing these conventions down).

### Evidence grades — every parameter carries one, and "unmeasured" is a grade, not a sin

Jesper, 2026-09-27. **Many of this model's parameters will never have a literature value.
Refusing to parameterise them would forbid exactly the quantities the model exists to
supply** — organ-level flow and volume in a named state. So the rule is not "sourced or
nothing". It is: **grade the evidence, record the grade, and never let a low grade pass as
a high one.**

| grade | evidence | how it may be used |
|---|---|---|
| **A** | a human measurement matching on quantity, site, cohort and respiratory phase | as a calibration target |
| **B** | several INDEPENDENT sources AGREE | ground truth — agreement across methods rules out method artefact |
| **C** | an indication of the true value (one cohort, or a mismatched one) | a best guess, labelled, and never asserted tightly in a test |
| **D** | an indication of MAGNITUDE or ORDER only, often cross-species | assume the magnitude; prefer a RATIO to an absolute |
| **E** | nothing in the literature | **pinned by the model, and reported as a PREDICTION** |
| **F** | the literature CONTRADICTS it and it is kept anyway | **must be named in the code, the log AND the README** |

**GRADE A IS NOT BEATEN BY COUNTING SOURCES.** One well-matched human measurement outranks
three mismatched ones. This project has lost six days to a site mismatch and has twice
retracted a claim built on an age-mismatched cohort. **Match quality first, then number of
routes.**

**GRADE B HAS ONE PRECONDITION: THE SOURCES MUST BE INDEPENDENT.** Several sources agreeing
is ground truth only if they COULD have disagreed. Three papers descending from one original
carry one paper's weight, and **their agreement is the more seductive error, because
agreement reads as confirmation.** The live instance is in this repository: *"the arteries
hold 13-15 % of blood volume"* is repeated everywhere, agrees with itself everywhere, and a
PubMed scope found no human study behind it. **Check provenance before counting a source.**
Independence means different labs, different methods, different cohorts — Maas 2009 and Maas
2013 are the same lab and the same method, so they are one route with scatter, not two.

**AND WHEN SOURCES DISAGREE, DO NOT AVERAGE THEM — FIND OUT WHY.** A disagreement is either
scatter, in which case take the range and grade C; or it is systematic, in which case the two
numbers describe DIFFERENT QUANTITIES and averaging manufactures one that describes nothing.
A cuff MAP and an integrated central MAP differ by ~9 mmHg for a reason. **The reason is
sometimes the most valuable thing in the comparison:** Franklin and McEniery disagree on
arterial compliance by age, and that gap turned out to be what hypertension does on top of
normal ageing (item 48).

**GRADE E IS A REAL CLAIM AND CARRIES TWO OBLIGATIONS.** A parameter the model pins where
the literature is silent is one of this project's intended contributions. It is only honest
if:
1. **The neighbourhood is validated.** Extrapolation is worth exactly as much as the
   structure doing it, and this repository has found five structural errors that left MAP,
   CO and CVP looking fine. A pinned number sitting inside an unvalidated structure is an
   artefact with a confidence interval, not a discovery.
2. **The parameter is IDENTIFIABLE.** Check that the endpoint pinning it actually moves when
   it moves, and that no second free parameter pins it equally well. Two unmeasured
   parameters that trade off pin their product, not themselves.

**GRADE F IS THE DANGEROUS ONE AND THE PROJECT HAS AT LEAST ONE.** Phenylephrine's venous
`e_max = 0.10` is kept because Schaefers' awake flow response demands it, while Bell 1991
measures the splanchnic bed moving the OTHER WAY in conscious man. That is defensible, and
it must never be silent: a grade-F parameter is a stated limitation, not an implementation
detail.

**WHAT THIS CHANGES IN PRACTICE.** Not the tuning rule — a grade A or B number is still
never bent to fit an endpoint. What changes is that a grade D or E parameter is now
LEGITIMATE where before it was either avoided or smuggled in uncited. **The grade must be
written where the parameter is defined**, so the next reader sees it without consulting the
log. `tools/parameter_audit.py` should report the distribution of grades; a manuscript
should publish it.

### Slow dynamics — three rules

`model/slow_dynamics.py` is gated by `SimParams.slow_dynamics_enabled` (default **`True`** since
`66b6231`, "slow dynamics on by default" — this file said `False` in two places until
2026-08-28, which mattered because the rules below are premised on what a DEFAULT run does)
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

## Committing and pushing

**Accumulate work; push at boundaries. Do not push per message.**

**Exactly one thing has timing pressure:** a blind-phase registration must be
public *before* that study's results arrive, because the whole mechanism is a
timestamp outside the author's control. See `preregistration/README.md`.

**Nothing else does.** Exclusions, results, backlog entries, documentation fixes,
process changes and tooling can all wait for a batch. An exclusion has no
prediction to protect; results are appended after the fact by definition.

So: **push when a registration needs its timestamp, or when Jesper asks.**
Otherwise let the work build and land it as one reviewed change.

**Name files explicitly when staging. Never `git add <directory>`.** That is how
`preregistration/003_run.py` — a runner for a study that had just been excluded —
reached a public commit, needing a second commit three minutes later to remove
it.

**Runners belong with registrations, never with exclusions.** Attached to a
registration a runner lets a reader reproduce a prediction. Attached to an
exclusion it only invites them to run a scenario the entry has explained cannot
be built. **Registration DOCUMENTS carry the public record; the `.py` runners
stay local**, so a scenario can be iterated on — and abandoned — without locking
each attempt into the repository. This puts the burden on the documents: they
must carry enough parameter detail (patient, ventilation, doses, timing,
averaging window) to reconstruct the scenario without the code.

### Why this is a rule and not a preference

A history whose last four commits read *add entry, correct entry, remove file
added by mistake* looks less careful than one where a batch lands complete — and
it undercuts the exact thing the pre-registration record exists to demonstrate.
**The mess becomes an argument against the work.**

This was asked for three times before it was written down. An intention was not
sufficient; that is why it lives here, in the file that gets read before work
starts, rather than in a memory of a preference.

## References

- PMC9363491 — primary model basis (21-compartment orthostatic stress model, Heldt-based; expanded to 23 compartments here)  
- Heldt T et al. (2002) J Appl Physiol 92:1239-1254 — foundational lumped-parameter model  
- DOI 10.1038/s41598-022-18831-3 — VoM-PhyS: 3D multiscale blood-flow and heat transfer  
- VaMpy (JORS): https://openresearchsoftware.metajnl.com/articles/10.5334/jors.159 — 1D arterial wave model
