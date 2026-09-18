# Excluded studies — and the mechanical reason

Studies supplied for the blind phase that the model cannot be asked, or that
are not out-of-sample.

**EVERY STUDY SCREENED IS LOGGED HERE, whatever the verdict.** Not to demonstrate
a comprehensive literature search — two entries would be poor evidence for that,
and no systematic search was performed. Studies were supplied opportunistically
and screened against the criteria in `README.md`.

The reason is narrower and stronger: **a partial exclusion log is worse than
none.** The first question anyone asks of a pre-registration is what was left
out, and the only answer that survives scrutiny is a log that is complete by
policy rather than by inclination.

**This list is a result.** It maps the architecture's boundary using real
published protocols rather than the authors' own account of the model's limits,
which a reader has more reason to trust. A model that could attempt everything
would be one whose limits nobody had tested.

| # | study | identifier | reason | category |
|---|---|---|---|---|
| 1 | Knee arthroscopy, Trendelenburg vs PLR before tourniquet release | [10.21608/ijma.2021.62396.1262](https://doi.org/10.21608/ijma.2021.62396.1262) | Three absent mechanisms — see below | NO MECHANISM *(temporary)* |
| 2 | Parabolic flight, seated and supine, with thigh-cuff venous occlusion | [PMID 21636570](https://pubmed.ncbi.nlm.nih.gov/21636570/) | Gravity acts only through the tilt term; seated posture, cuffs and transients all unrepresentable | NO MECHANISM |
| 3 | ICU postural manoeuvres and fluid challenge, responders | *(supplied 2026-09-18)* | Passed the screen, then could not be configured to the cohort's baseline | CANNOT BE CONFIGURED *(temporary)* |
| 4 | Major GI surgery, open vs laparoscopic, steep Trendelenburg | [PMID 40770328](https://pubmed.ncbi.nlm.nih.gov/40770328/) | MAP held at 65-80 by the clinician, so the reported haemodynamics cannot be attributed to posture | CONTROLLED VARIABLE *(permanent)* |

---

## 1 — Trendelenburg vs passive leg raise, before tourniquet release

**Screened 2026-09-18.** Int J Med Arts 2021. n = 49 + 49, unilateral knee
arthroscopy under spinal plus general anaesthesia, proximal thigh tourniquet.
Group 1 placed head-down 20°, group 2 given bilateral passive leg raise to 45°.
MAP by cuff at baseline — post-spinal, already tilted, tourniquet still inflated
— then at 1, 2, 3, 4, 5 and 10 minutes after release. Mean ± SD.

**Only methods, cohort and timing were supplied. No results were seen.**

### Why the model cannot be asked this

**The two arms are the same manoeuvre to this model.** Passive leg raise is
implemented *as* head-down tilt, and tilt is global — one angle applied to every
compartment through its fixed height. The legs cannot move relative to the trunk,
so the comparison the study exists to make is the one thing the architecture
cannot express.

**The tourniquet is unilateral and the model has no laterality.** The leg
compartments represent both legs at once. In group 2 that matters directly: one
leg is excluded from the circulation while both are raised, so the manoeuvre
mobilises one leg's volume rather than two.

**Every measurement is after release, and release has no mechanism.** Nothing in
the model accumulates ischaemic metabolites, so there is no vasodilator load to
wash out and no reactive hyperaemia. Compartment resistance is also fixed at
setup, so even the release *event* cannot be staged, let alone the ten minutes of
physiology that follow it.

### Status, and two honest notes

**Temporarily excluded, not permanently.** The blockers are missing mechanisms,
not a mismatch of kind. If per-segment posture and a tourniquet model are ever
built, this becomes answerable — and it stays a clean out-of-sample target,
because only methods and timing were ever read. Six post-release time points is
unusually well sampled.

**Quality caveat, recorded rather than left to be discovered.** Not indexed in
PubMed, and judged probably low quality by the clinician who supplied it. That
matters for a validation target: if a source is unreliable, a disagreement does
not cleanly implicate the model. Better used as a shape target — how fast, how
deep, how long to recover — than a magnitude one.


## 2 — Parabolic flight, seated and supine, with thigh-cuff venous occlusion

**Screened 2026-09-18.** Healthy volunteers, age 35. Thirty parabolic
manoeuvres: the first twenty seated, the last ten supine. MAP (Portapres) and HR
continuous; CO by rebreathing over 20-second windows at either 1 G or 0 G.
Seated conditions randomised across 1 G, 0 G, 0 G with bilateral thigh cuffs
inflated to 60 mmHg from before the 1.8 G pull-up, and 0 G with the cuffs
released on entering 0 G.

**Only methods, cohort and timing were supplied. No results were seen.**

### Why the model cannot be asked this

**Gravity reaches the model only through the tilt term**, as
`rho * g * h * sin(tilt)` in `model/gravity.py`. At tilt zero the sine is zero,
so the term vanishes whatever the gravity is. **This is readable from the code
and needs no simulation to establish.**

So the supine arm, which looked like the salvageable half, is the clearest
failure. **The model answers "no change" by construction**, and a prediction of
identically zero is arithmetic rather than physiology.

**The seated arm is unrepresentable for two separate reasons** — it is beyond the
validated posture range of −30° to +45°, and a seated posture needs hip
articulation the model does not have, since one tilt angle is applied to every
compartment through a fixed height.

**Thigh-cuff venous occlusion is not a model parameter.** The cuffs are
bilateral, so limb laterality is not the obstacle here; occlusion simply does not
exist as a mechanism. This is also why the live-mode UI has no cuff control —
there is nothing in the model for it to expose.

**Every measurement is a transient.** Twenty-second 0 G windows, a 1.8 G pull-up,
and cuff release timed to 0 G entry. Live mode can step gravity mid-run but only
between four named environments, so 1.8 G is unreachable, and it cannot vary
regional resistance at all.

**Convention flag, recorded although it is not the blocker:** Portapres measures
finger arterial pressure; the model reports a time-integrated central MAP.

### What was learned by screening it

**Every microgravity result in the suite is really a supine result.** The finding
generalises well beyond this study: at tilt zero, `GravityEnvironment.MICROGRAVITY`
and Earth gravity enter the equations identically, so the Buckey 1996 row in the
validation table compares supine CVP against upright CVP under a different name.
The README already carried the symptom — "CVP paradox in microgravity not fully
reproduced" — but attributed it to unmodelled chest-wall compliance. **That is
incomplete: fixing chest-wall compliance would not help, because the
gravitational term is gone before any of it applies.** Opened as backlog item 57.

This is the second time a screen has found that a named scenario is a synonym for
another one. The first was passive leg raise, which is implemented as head-down
tilt.

## 3 — ICU postural manoeuvres and fluid challenge, responders

**Screened and accepted 2026-09-18, then excluded at configuration the same day.**

ICU patients, lightly sedated, mechanically ventilated with spontaneous breathing
activity, with signs of inadequate tissue perfusion. Responders only: age
69.3 +/- 14.2, BMI 22.5 +/- 2.5, sex about 1:1, noradrenaline in 66.6 % at
< 0.1 mcg/kg/min, fentanyl in 81 %, PEEP 5, PIP median 14, tidal volume
8.9 +/- 1.8 mL/kg. Supine baseline, reverse Trendelenburg +10 deg for 1 min,
Trendelenburg -13 deg for 1 min, supine 1 min, then 4 mL/kg of 5 % albumin over
15 min. CI, CVP, MAP, PPV and SVV reported.

**Baseline: MAP 79.2 +/- 14.7, CI 3.1 +/- 1.5, CVP 6.4 +/- 4.6. No outcome data
was seen.**

### This one failed at a different stage from entries 1 and 2

**It passed the feasibility screen**, as YES APPROXIMATED. The protocol maps onto
parameters the model has: both tilt angles sit inside the validated range, the
four-stage sequence runs through `LiveSimulator`, PEEP and PIP are settable and
match the cohort exactly, and noradrenaline exists. The substitutions —
crystalloid for albumin, one sex for a mixed cohort, a single noradrenaline dose,
no opioid — were registrable rather than disqualifying.

**It failed when the patient was built.** Configured through the Tier 3 path on
the study's own baseline, the model settled a long way from what it was asked
for:

| | requested | model settled at |
|---|---|---|
| MAP | 79.2 | 94.07 |
| CVP | 6.4 | 2.52 |
| CI | 3.1 | 2.77 |

MAP overshoots by about 15 mmHg and CVP undershoots by nearly 4. **"Matched on
operating point" was the entire justification for accepting this study, and the
model is not at that operating point.**

The direction compounds it. The model's patient sits at a much lower filling
pressure, so further up the steep part of its Starling curve, and should
therefore be MORE fluid-responsive than the cohort — biasing precisely the
comparison the study exists to make.

**The reason for exclusion: there is no way to test this quantitatively, only
direction could be compared.** A direction-only comparison is worth little here,
because the postural directions are already established in-sample.

### What informed the exclusion, stated because it matters

**Only the baseline mismatch.** The model's responses to the manoeuvres played no
part in the decision. That distinction is the difference between a defensible
exclusion and a biased one: discarding a study because its outputs looked
unfavourable is exactly what this log exists to prevent, whereas discarding one
because the patient cannot be built is a fact about the model, settled before any
comparison is attempted.

### The finding is worth more than the study would have been

**The frozen model cannot be configured to a measured MAP, CI and CVP.** This is
out-of-sample evidence for a defect previously visible only against the model's
own reference patient. Opened as backlog item 58, high priority: the calibration
should adjust other operating parameters within physiological bounds until all
three measured values are met, rather than accepting whatever falls out.

**Temporarily excluded.** If calibration is fixed this study becomes usable —
only methods, cohort and baseline were read, so it stays clean.

## 4 — Major GI surgery, open vs laparoscopic, steep Trendelenburg

**Screened 2026-09-18.** [PMID 40770328](https://pubmed.ncbi.nlm.nih.gov/40770328/).
n = 80, major gastrointestinal surgery, open against laparoscopic. Desflurane
anaesthesia. Oesophageal Doppler cardiac measurements supine and in Trendelenburg
steeper than 45 deg. MAP held at 65-80 mmHg with individualised fluids and
vasoactive agents. Laparoscopic arm measured after pneumoperitoneum and
Trendelenburg were established; open arm supine at the start, then Trendelenburg
until the end. Measurement times given only as "regular intervals".

**Only methods were supplied. No results were seen.**
`tools/check_insample.py 40770328` -> NOT FOUND.

### The reason, after two of the original three were withdrawn

**THE BLOCKER IS THE CONTROLLED VARIABLE.** MAP was actively held at 65-80 mmHg
with individualised fluids and vasoactive agents, so the reported haemodynamics
cannot be attributed to posture. See the rule below.

**Pneumoperitoneum blocks only the LAPAROSCOPIC arm.** Abdominal pressure is
DERIVED from pleural pressure through `ABDOMINAL_TRANSMISSION = 0.21`, a
consequence of ventilation rather than a settable quantity, so insufflation
cannot be applied — and with it the open-versus-laparoscopic comparison. **The
open arm has no pneumoperitoneum and is unaffected.** Backlog item 59.

### TWO REASONS WITHDRAWN, 2026-09-18 — recorded because both were mine

**"Tilt beyond the validated range" was wrong, and it cited a limit whose own
rationale points the other way.** The paper says 45 deg exactly in its methods,
not "greater than 45" as the abstract has it. More importantly,
`known_model_limitations.md` §2 argues the envelope entirely from EXTREME UPRIGHT
posture — at 90 deg head-up the hydrostatic penalty exceeds transmural venous
pressure and leg venous return collapses. The -30 deg head-down end is stated but
never argued: it is simply the steepest head-down angle any test uses. **So 45
deg head-down is an extrapolation beyond what has been TESTED, not a mechanism
boundary** — and it extrapolates in the direction with no documented failure
mode. That is a registrable caveat, not an exclusion.

**"Timing undefined" was overstated.** "Regular intervals" describes sampling,
not reporting. If the paper gives a supine value and a Trendelenburg value, those
are two defined states the model can produce.

**The pattern is worth recording.** This was the second consecutive study
rejected on an accumulation of margins rather than on impossibility, after the
screening standard had already been rewritten to stop exactly that. Defaulting to
exclusion and calling it rigour protects the model from being tested, which is
the opposite of the point.

### THE RULE THIS STUDY ESTABLISHED

**A variable the clinician actively controls cannot be used to validate the
model.** MAP here is not an outcome, it is a set-point maintained by an
unrecorded feedback loop. Worse, the loop acts through fluids and vasopressors,
so cardiac output and stroke volume are confounded by administration the paper
does not quantify. **Check for a controlled variable early** — it is common in
intraoperative work and invalidates more than it first appears to.

### Not temporary, but for one reason only

Entries 1, 2 and 3 are temporary: build the mechanism, or fix the calibration,
and they become usable. **This one is not — because the controlled variable is a
property of the STUDY.** Pneumoperitoneum could be built and the tested tilt
range could be widened, and neither would help: a perfect simulator could not be
tested against haemodynamics that were held where the clinician wanted them.

**Without the MAP protocol the open arm would have been registrable**, with the
45 deg tilt and the desflurane substitution as stated caveats. It is worth being
clear that the model was not the limiting factor here.

### Lesser notes, recorded but not decisive

Desflurane has no counterpart — propofol is the model's only anaesthetic. And
oesophageal Doppler estimates cardiac output from descending aortic flow through
a nomogram, so it is not the total cardiac output the model reports; that would
be a convention flag if the study were ever otherwise usable.

## Categories

- **IN-SAMPLE** — already cited in `model/` or `tests/`; was available during
  development, so it cannot test anything. Detected by
  `tools/check_insample.py`, not by memory. *(Likhvantsev 2025 is the known
  example: used from the beginning, so unavailable for this phase.)*
- **NO MECHANISM** — the model lacks the structure the protocol requires. Name
  it: no cellular compartment, no 1-D wave propagation, no skeletal-muscle
  pump, no age-dependent baroreflex, no pregnancy or sepsis physiology, no
  postural articulation, no limb laterality.
  **Mark it *(temporary)* if building the mechanism would make the study
  answerable.** "We cannot ask this yet" and "this can never test us" are
  different statements about the model, and a reader should be able to tell
  them apart.
- **OUT OF VALIDATED RANGE** — mechanically runnable but outside the envelope
  where outputs mean anything, e.g. posture beyond −30°/+45°.
- **NO COMPARABLE OUTPUT** — the model runs the protocol but reports nothing
  that corresponds to what was measured, and no convention mapping exists.
  Distinct from CONVENTION, where a mapping exists but differs.
- **NO SPREAD REPORTED** — *not* an exclusion. The study is registered, but
  quantities with no reported spread can only reach tier C or F, and are counted
  separately from the tiered ones. Listed here only when a study reports no
  spread for *any* quantity, which makes the whole comparison direction-only.
- **CANNOT BE CONFIGURED** — the protocol is representable and the study passed
  the feasibility screen, but the model cannot be set up AS the cohort. Distinct
  from NO MECHANISM: nothing about the intervention is missing, the PATIENT
  cannot be built. **Record which inputs were requested and what the model
  settled at, and state explicitly that the model's outputs on the protocol
  played no part in the decision** — otherwise this category becomes a route for
  quietly discarding studies whose results looked unpromising.
- **RESULT SEEN** — the result reached the model author before registration.
  Excluded regardless of everything else, and recorded rather than hidden.
