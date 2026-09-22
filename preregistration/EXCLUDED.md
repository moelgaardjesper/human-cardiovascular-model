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
| 3 | ICU postural manoeuvres and fluid challenge, responders | [PMID 41721238](https://pubmed.ncbi.nlm.nih.gov/41721238/) | Passed the screen, then could not be configured to the cohort's baseline | CANNOT BE CONFIGURED *(temporary)* |
| 4 | Major GI surgery, open vs laparoscopic, steep Trendelenburg | [PMID 40770328](https://pubmed.ncbi.nlm.nih.gov/40770328/) | MAP held at 65-80 by the clinician, so the reported haemodynamics cannot be attributed to posture | CONTROLLED VARIABLE *(permanent)* |
| 5 | Isometric handgrip, supine vs 10 deg head-down tilt, healthy volunteers | [PMID 29595918](https://pubmed.ncbi.nlm.nih.gov/29595918/) | No exercise pressor reflex; stroke volume derived from a peripheral waveform the model cannot reproduce | NO MECHANISM *(temporary)* |
| 6 | Phenylephrine vs noradrenaline under propofol/remifentanil anaesthesia | [PMID 25760679](https://pubmed.ncbi.nlm.nih.gov/25760679/) | No opioid — at remifentanil Ce 8 the missing drug IS the anaesthetic state, and the titration degenerated | NO MECHANISM *(temporary)* |
| 7 | Head-up tilt 10 deg during spinal anaesthesia in parturients | [PMID 29952519](https://pubmed.ncbi.nlm.nih.gov/29952519/) | Blood pressure defended with ephedrine; and the block level, which is the study's mechanism, is a model INPUT | CONTROLLED VARIABLE *(permanent)* |
| 8 | Hyperoxic rebreathing chemoreflex test at five tilt positions | [PMID 25194198](https://pubmed.ncbi.nlm.nih.gov/25194198/) | Every reported value is respiratory; the model computes none of them | NO COMPARABLE OUTPUT *(temporary)* |

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
was seen.** [PMID 41721238](https://pubmed.ncbi.nlm.nih.gov/41721238/).
`tools/check_insample.py 41721238` -> NOT FOUND.

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

## 5 — Isometric handgrip, supine vs 10 deg head-down tilt

**Screened 2026-09-18.** [PMID 29595918](https://pubmed.ncbi.nlm.nih.gov/29595918/).
Healthy volunteers supine on a tilt bed, neck neutral. Recordings horizontal and
at 10 deg head-down. After 3 min of rest, isometric handgrip at 30 % of maximum
voluntary contraction for 3 min with continuous dynamometer feedback, then 5 min
rest before changing tilt and repeating. Run twice per subject, first round
randomised to start horizontal or head-down, second round reversed. Outcomes:
MAP by Finometer, stroke volume estimated from the pressure curve, and heart rate.

**Only methods were supplied. No results were seen.**
`tools/check_insample.py 29595918` -> NOT FOUND.

### Why the model cannot be asked this

**There is no exercise pressor reflex.** No metaboreflex, no mechanoreflex, no
central command — nothing driven by muscle afferents anywhere in the model.
Isometric handgrip raises arterial pressure through group III/IV muscle afferents
and central command, and that pathway does not exist here.

**`muscle_pump_pressure` is not it**, and the distinction matters because the
name invites the mistake. That parameter is rhythmic calf compression,
`sin^2(2*pi*f*t)`, applied to the LEG venous drainage path — the walking pump.
Wrong limb, wrong mechanism, mechanical rather than neural. Sustained handgrip at
30 % MVC involves almost no rhythmic pumping and would not act on leg veins in
any case.

**The response could only be produced by imposing it.** Raising SVR and heart
rate by hand would prescribe the study's outcome rather than predict it.

### A second, independent blocker

**Stroke volume estimated from a peripheral pressure waveform is a quantity this
model is architecturally unable to reproduce.** Pulse-contour methods derive
stroke volume from the SHAPE of a peripheral pressure wave, and the model's
peripheral waveform is known-wrong in exactly that respect: pulse pressure
amplification is inverted, 0.88 against a measured 1.33 +/- 0.16, and correcting
it needs wave travel and reflection a lumped model does not have. **This would
bite even if handgrip existed.** Finometer MAP carries a milder version of the
same convention problem — finger pressure against a time-integrated central MAP.

### Recorded because it is the best-designed study screened so far

No clinician in the loop, a fixed protocol, defined time points, randomised order
with sequence reversal to control for drift — and a **non-additive interaction**
at its centre: does head-down tilt modulate the handgrip response? That is
precisely the out-of-sample criterion the blind phase was designed around, two
interventions fitted separately and tested together.

**The first four exclusions were the studies' designs meeting the model's limits.
This one is purely the model's limit.** Marked temporary: the exercise pressor
reflex is a bounded, well-characterised human mechanism rather than a sub-model,
and building it would unlock a whole class of volunteer studies of this quality.
Backlog item 60, low priority. Only methods were read, so this stays clean.

## 6 — Phenylephrine vs noradrenaline under propofol/remifentanil anaesthesia

**Screened and accepted 2026-09-19, then excluded the same day when the scenario
would not build.** 29 vs 28 patients, age 57 vs 58, slightly male-majority,
BMI 27.7 and 25.5. Hypertension on beta blockers or antihypertensives in 9/29
and 13/28. Target-controlled infusion: remifentanil Ce 8 ng/mL (Minto), propofol
Ce 2.5 mcg/mL (Schnider). Volume-control ventilation, TV 8 mL/kg, PEEP 5,
FiO2 0.4, rate set to end-tidal CO2. Vasopressor by 1 mL bolus then
0.3 mL/kg/h, titrated to 80-100 % of the awake MAP, anaesthetist blinded.
Outcomes HR, SV, CI, SctO2, SptO2 and rate-pressure product, from 3 s before to
240 s after administration.

**Only methods and cohort were supplied. No results seen.**
[PMID 25760679](https://pubmed.ncbi.nlm.nih.gov/25760679/).
`tools/check_insample.py 25760679` -> NOT FOUND in code, docs or registrations.

**The check matters here because the entry is TEMPORARY.** Had the study turned
out to be in-sample, building an opioid would not have made it usable, and the
entry would be permanent rather than a target worth returning to. It is clean, so
it stays available.

### The design that nearly worked

The study titrates both drugs to the SAME pressure target, so the comparison is
at matched MAP rather than matched dose. That is reproducible: bisect each
drug's dose in the model until it reaches the same target, then compare flow.
**Matching on pressure makes the drug concentrations unnecessary** — the paper
gives doses only in mL, with no dilution stated — and it largely cancels the
setpoint defect of backlog item 62, since both arms start from the same
anaesthetised state.

It was accepted on that basis, with a long but stated caveat list.

### Why it failed, and how the failure showed itself

**The titration degenerated.** Both drugs bisected to the floor of the dose
range and still overshot the target:

| | awake MAP | anaesthetised | target (90 %) | achieved, phenylephrine |
|---|---|---|---|---|
| female | 93.12 | 83.14 | 83.81 | 83.95 |
| male | 95.39 | **85.96** | **85.85** | 86.65 |

**The model's anaesthetised patient does not need a vasopressor.** In the male
arm the anaesthetised pressure is already ABOVE the target before any drug is
given. There is nothing to titrate, so the study's central manoeuvre cannot be
staged.

**The cause is the missing opioid.** Propofol at 2.0 mg/kg drops MAP by 11 %.
The real patients required vasopressors, which by the protocol means their
pressure had fallen below 80 % of awake — and the agent responsible is
remifentanil at Ce 8 ng/mL, a high effect-site concentration that dominates the
haemodynamic picture. **The model has no opioid at all.**

**A second sign in the same output confirms it is qualitative, not just
quantitative.** The model's anaesthetised heart rate RISES, 69.9 to 83.2, because
propofol vasodilates and the baroreflex answers with tachycardia. Patients under
remifentanil Ce 8 are BRADYCARDIC. The anaesthetic baseline is wrong in
direction, not merely in depth — and heart rate was among the few comparators
that had survived the other caveats.

### Why a deeper propofol proxy was rejected

Raising propofol to 4-5 mg/kg would reach a realistic anaesthetised pressure and
would be protocol-driven rather than result-driven, since "below 80 % of awake"
comes from the methods. **It was still rejected: propofol's profile is not
remifentanil's.** It would produce tachycardia where the patients are
bradycardic, so the baseline would remain qualitatively wrong while looking
quantitatively repaired — which is worse than an honest exclusion.

### The other caveats, recorded since they remain true

Cardiac index and stroke volume were measured by Nexfin, which derives them from
the finger pressure waveform assuming fixed aortic properties — **the very
property an alpha1 agonist changes.** SctO2 and SptO2 have no counterpart: there
is no oxygen transport anywhere in the model. The 240 s trajectory needs
pharmacokinetics the model does not have; its drug window is a step function.
Hypertension on beta blockers or antihypertensives in 31 % and 46 % of the two
groups is comorbidity, which this project treats as uncorrectable. And the
noradrenaline-versus-phenylephrine ordering is already calibrated in the suite
against Ngan Kee 2015, so this would have been a generalisation test rather than
a test of unfitted structure.

### Status

**Temporary.** An opioid is a bounded, well-characterised addition rather than a
sub-model, and remifentanil is among the best-described drugs in anaesthesia.
Built, this study becomes answerable — and only methods and cohort were read, so
it stays clean. **Backlog item 63.**

**The exclusion rests on the failed titration, not on a judgement.** The model's
outputs on the comparison itself were never examined; the scenario could not be
constructed at all.

## 7 — Head-up tilt 10 deg during spinal anaesthesia in parturients

**Screened 2026-09-19.** [PMID 29952519](https://pubmed.ncbi.nlm.nih.gov/29952519/).
Parturients allocated equally to 10 deg head-up tilt or the horizontal position
during conduction of spinal anaesthesia, the position continued through the
operation. Outcomes: blood pressure, heart rate, incidence of hypotension,
ephedrine consumption, and anaesthesia level.

**Only the protocol and the outcome list were supplied. No results were seen.**
`tools/check_insample.py 29952519` -> NOT FOUND in code, docs or registrations.

### The tilt is not the problem, and that is worth saying first

**10 deg head-up is well inside the validated -30 to +45 deg range**, and a
two-arm posture contrast held through a procedure is exactly the shape this
phase wants. Nothing below is about the manoeuvre.

### Why the model cannot be asked this

Four blockers. Two are decisive on their own.

**DECISIVE 1 — THE BLOCK LEVEL IS A MODEL INPUT, AND IT IS THE STUDY'S OWN
MECHANISM.** `spinal_anaesthesia(block_height)` in `pharmacology.py` takes the
block as given and clamps it to [0, 1]. There is no cerebrospinal fluid, no
baricity, no drug distribution — **nothing through which posture could change
the level a spinal reaches.** But cephalad spread is WHY 10 deg head-up is used,
and the block level sets the extent of the sympathectomy that produces the
hypotension. So the two arms differ, in the model, only by whatever block height
the modeller assigns them. **That prescribes the study's result instead of
predicting it**, and no amount of care in choosing the numbers repairs it.

**DECISIVE 2 — BLOOD PRESSURE IS A CONTROLLED VARIABLE.** Ephedrine is given to
treat hypotension as it appears, so the reported pressures are not what these
circulations did; they are what they did after being corrected toward a target.
This is the rule established by entry 4, and here it takes MAP, heart rate and
the hypotension incidence together, because all three sit downstream of one
unrecorded feedback loop. **There is also no ephedrine in the model** — six
drugs only, and ephedrine's indirect mixed alpha/beta action is none of them —
so the rescue cannot even be reproduced in order to be reasoned about.

**Ephedrine consumption is not the clean outcome it looks like.** It is the
better-founded of the study's endpoints, because it records the untreated
tendency rather than the treated pressure. But producing it needs the drug the
model lacks AND a clinician applying an unstated threshold, so the model cannot
generate the quantity at all.

**LESSER 3 — TERM PREGNANCY, and the missing mechanism sits on the study's own
independent variable.** There is no pregnancy physiology anywhere in the model
(backlog item 12, Tier 5 — a genuinely new sub-model, not a bounded mechanism).
The suite already states this about itself at `tests/test_circulation.py:175`:
Ngan Kee's parturients are *"the least transferable cohort in the suite, and it
is also the one test currently failing."* What raises it above an ordinary
cohort caveat here is **aortocaval compression** — a POSTURE-DEPENDENT mechanism
the model does not have, in a study whose entire design is a posture contrast.

**LESSER 4 — INCIDENCE IS NOT A QUANTITY THIS MODEL PRODUCES.** The model is
deterministic, with no random number generation anywhere, and it runs one
representative patient. It yields a pressure trace, not a rate across a
population. An incidence needs between-subject variability that does not exist
here, and manufacturing one would be fabrication.

### What is left once those are removed

A 10 deg tilt, applied to a non-pregnant patient, at a block height chosen by
the modeller. **Both halves of that are already in-sample** — the block is
calibrated against Malmqvist 1987 and tilt is calibrated throughout the suite.
So the residue is not a weak out-of-sample comparison; it is not out-of-sample
at all.

### Status: PERMANENT, and the model is not the limiting factor

Pregnancy could be built, and intrathecal drug spread could in principle be
modelled. **Neither would help.** A perfect simulator cannot be tested against
pressures that were held where the anaesthetist wanted them. This is the second
permanent exclusion and it has the same single cause as the first: **a
controlled variable is a property of the STUDY**, and no model development
reaches it.

### What would make this class of study usable

Recorded because the design is otherwise good — randomised, a fixed protocol, a
position held throughout, and a genuine two-arm contrast. **Tilt during spinal
in NON-PREGNANT patients, with no rescue vasopressor until after a defined
measurement window, reporting MAP with a spread and STATING the block level
rather than measuring it.** That is registrable today, with no new mechanism.

### A pattern worth recording

**This is the third time a screen has found the model answering by construction
rather than by physiology.** Passive leg raise IS head-down tilt (item 53); 0 G
IS supine (item 57); and now the block level is whatever it is set to.

**The first two return a ZERO, and this one would not.** A synonym makes the two
arms identical, so the difference comes out at exactly zero and the artefact
announces itself. Here the absent mechanism — intrathecal drug spread — happens
to correspond to a settable argument, so the gap gets filled by hand and the
model produces a confident, plausible difference instead. **Silence is easy to
spot; fluency is not.**

**Added to the screen as its own question**, in `README.md`: *does the model
COMPUTE the thing the study varies, or is it TOLD?* It is not a fourth rejection
shape — the underlying reason is still an absent mechanism — but it is the check
that finds one when the absence is hidden behind an input.

## 8 — Hyperoxic rebreathing chemoreflex test at five tilt positions

**Screened 2026-09-21.** [PMID 25194198](https://pubmed.ncbi.nlm.nih.gov/25194198/).
Subjects secured on a tilt table with ankle restraints and placed in five
steady-state positions in random order: 90 deg head-up, 45 deg head-up, supine,
45 deg head-down, 90 deg head-down. In each position a hyperoxic rebreathing
test followed a 10 min baseline. Subjects hyperventilated voluntarily for 1 min
to bring end-tidal CO2 to 20 Torr, then rebreathed until end-tidal CO2 reached
50-55 Torr or they signalled their limit, then 2 min of recovery on room air.
Baseline values are a 2 min mean taken from minutes 7-9, at least 1 min before
the hyperventilation.

**Only the protocol was supplied. No results were seen.**
`tools/check_insample.py 25194198` -> NOT FOUND in code, docs or registrations.

### Why the model cannot be asked this

**THE DECIDING REASON IS THE SIMPLEST ONE: EVERYTHING REPORTED IS RESPIRATORY,
AND THE MODEL COMPUTES NONE OF IT.** Confirmed by Jesper, who has the paper:
there is no reported value the model produces. This is not a convention
mismatch, where the same physical quantity is read at a different site or in a
different respiratory phase and a mapping exists. **A ventilation or an
end-tidal CO2 is not a pressure measured differently. It is a quantity the model
does not have.** That is what separates NO COMPARABLE OUTPUT from CONVENTION.

**SECOND AND INDEPENDENT: there is no chemoreflex.** The rebreathing test drives
CO2 up and measures the ventilatory and cardiovascular response to it. The model
has no CO2, no gas exchange, no oxygen transport and no chemoreceptor of any
kind. Even if the haemodynamics had been reported, the intervention itself is
unrepresentable.

**THIRD, AND IT WAS NEVER REACHED: two of the five positions are outside the
validated range** of -30 to +45 deg. At 90 deg head-up the hydrostatic penalty
exceeds transmural venous pressure, leg venous return collapses and the model
underestimates MAP — a documented failure mode, not merely an untested angle.
90 deg head-down (the table is an inversion table) is further out still.

### What the screen DID establish, and it is worth keeping

**The two tilt limits are not symmetric, and only one of them is argued.** The
head-up limit has a stated mechanism and a documented failure. The head-down
limit of -30 deg is simply the steepest angle any test in the suite uses; its
own rationale in `known_model_limitations.md` argues entirely from EXTREME
UPRIGHT posture. So **45 deg head-down is an extrapolation beyond what has been
tested, with no documented failure mode, and would be a registrable caveat** —
while 45 deg head-up sits inside the range outright. That distinction was
established for exclusion entry 4 and holds here.

So had this study reported a pressure or a flow, **three of its five positions
would have been usable**: supine, 45 deg head-up, and 45 deg head-down with a
stated caveat.

### A near miss worth recording, because the design is good

Five graded tilt positions, held to steady state, randomised in order, with a
clean 2 min baseline bin taken a full minute before any intervention. That is a
better posture protocol than most studies screened.

**And 45 deg is a large enough stimulus to discriminate between models**, which
registration 005's 10 deg was not — there a model predicting exactly zero would
have scored tier A on every quantity. A graded tilt series at 45 deg would test
the SHAPE of the posture response across five points rather than a single
contrast.

**THE FILTER THIS GIVES, and it is cheap to apply early:** *does the study report
a pressure or a flow, or only a gas?* One question, asked before anything else,
would have closed this screen in a sentence.

### Status

**Temporary, but distant.** A chemoreflex with CO2 transport and gas exchange
would make the rebreathing arm answerable and would give the model quantities
this study reports. That is a new SUB-MODEL rather than a bounded mechanism —
the same class as pregnancy or sepsis, which sit in Tier 5 of the backlog — so
this is not a near-term target. Only the protocol was read, so the study stays
clean if it is ever revisited.

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
