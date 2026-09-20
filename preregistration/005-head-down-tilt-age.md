# 005 — 10° head-down tilt in young and older healthy men

- **Registered:** 2026-09-19
- **Model:** `v1.0.0`, artefact commit `90cc1d0`, unmodified
- **Identifier:** [PMID 9925894](https://pubmed.ncbi.nlm.nih.gov/9925894/) —
  requested AFTER the model was run and before this was pushed, per the
  procedure. `tools/check_insample.py 9925894` -> NOT FOUND in code, docs or
  registrations. **Hand-checked for bare author-year citations** as the tool's
  own caveat requires: the only late-1990s citations in the suite are Wieling
  1998 (PMID 9640339) and Schaefers 1999 (PMID 10073742), both different, and
  "Surname 1998" is a regex template in `parameter_audit.py` rather than a
  source.
- **Verdict:** YES, APPROXIMATED
- **Status:** REGISTERED — study results not seen.

> **READ THIS FIRST: THE PRIMARY IS A STRUCTURAL NULL.** The model predicts a
> between-group difference of **+0.02 mmHg**, which is no difference at all. It
> is registered anyway, labelled as a null, for the reasons in the section
> below. The substantive predictions here are the WITHIN-group responses.

---

## Declared spent values — read this first

**NOTHING IS SPENT.** No reported haemodynamic value was used to configure the
patient. The model is built from **age, sex and anthropometrics only**, so
resting MAP and heart rate remain predictions rather than inputs.

This was a deliberate choice and it has a consequence worth stating: it would
have been easy to configure the patient to the cohort's reported resting
pressure through the Tier 3 path, and doing so would have produced a better-
looking baseline. It would also have spent the one quantity this comparison is
most interesting for. **The baseline gate (procedure step 3) is therefore passed
trivially here — precisely because the model is not being asked to hit measured
values**, which is also why backlog item 58 does not bite.

---

## The study, as supplied

**Eleven young men, 23 ± 1 years, and ten older men, 64 ± 1 years** (mean ±
s.e.m.). All healthy, normotensive, non-obese, non-smoking, free of overt
cardiovascular disease; older subjects additionally screened by physical
examination and resting and maximal exercise ECG. None took medication
affecting autonomic-circulatory function. BMI 23.9 (young) and 25.0 (older).

**Protocol:** heart rate and arterial blood pressure measured continuously
through **10 min of supine baseline control** and **10 min of 10° head-down
tilt**, subjects positioned supine.

**Instruments:** beat-to-beat arterial pressure by finger photoplethysmography
(Finapres 2300, Ohmeda). Forearm blood flow by venous occlusion
plethysmography. Venous blood sampled in the last minute.

**Reported:** SBP, DBP, MAP, pulse pressure, peripheral venous pressure and
heart rate. **Results are mean with SD.**

**Only the protocol, cohort and instrument list were supplied. No results were
seen.**

---

## What is scored, and what is not

**SCORED: MAP and heart rate. Nothing else.** The comparator is **1 SD for
tier A and 2 SD for tier B**, as the study reports mean with SD. *n* is 11 and
10, so the distance is additionally reported in SEM units per the scoring rule.

### PRIMARY — Δ(ΔMAP), young minus older. **A DECLARED NULL.**

The between-group difference in the MAP response to head-down tilt. It was
chosen because nothing in the suite constrains it, and because the instrument,
the posture and the convention mismatch are common to both arms and therefore
cancel — the reasoning that made registration 004's primary a between-group
difference.

**IT CAME OUT AT +0.02 mmHg, AND THE REASON IS STRUCTURAL.** The response to
tilt is governed by the baroreflex, and **the baroreflex has no age dependence
of any kind** — `BaroreflexController.__init__` takes no age, no body size and
no sex, and `patient.py` never touches a gain (backlog item 51). An
age-invariant reflex must produce an age-invariant reflex response. The two
model patients differ in arterial compliance and chamber volumes, and those
move PULSE pressure (24.85 vs 37.84 mmHg) while leaving the MEAN and its tilt
response almost untouched.

**THIS SHOULD HAVE BEEN CAUGHT AT SCREENING AND WAS NOT.** It is close to
rejection shape 2 — the model answering by construction rather than by
physiology — and it is the same failure as 0 G being identical to supine. The
screen checked that the model could represent 10 degrees of head-down tilt in a
23-year-old and a 64-year-old. It did not ask whether anything in the model
could make those two answers DIFFERENT. **That question belongs in the screen**
and is proposed for `README.md` on the strength of this.

**WHY IT IS REGISTERED RATHER THAN EXCLUDED.** Three reasons, and the third is
the operative one.

1. **It is not arithmetic vanishing.** At 0 G the gravitational term is
   multiplied by `sin(0)` and disappears; nothing could ever make it non-zero.
   Here the quantity is live and the model has every mechanism except one, so
   the null is a physiological claim — *"an ageing circulation responds to a
   small postural change exactly as a young one does"* — and it is wrong in a
   way that names its own cause.
2. **The within-group predictions are NOT degenerate**, and there are four of
   them. The study is not reduced to the null.
3. **A null that is expected to fail is worth more than a safe prediction.**
   Baroreflex sensitivity falls steeply with age in humans; this is among the
   best-established facts in cardiovascular ageing. **So the registered
   expectation is that this primary FAILS**, and its failure is direct
   out-of-sample evidence for item 51, which currently rests on nothing but a
   reading of the code.

**Scoring it honestly.** Tier A requires landing inside the study's reported
spread for the between-group difference. A null will do that if — and only if —
the study also finds no age difference. **A tier A here would be uninformative
and must be reported as such**, because a model that cannot produce ANY
age difference is not being tested by a study that happens not to find one.

### Secondary, and weaker for a stated reason

Within-group ΔMAP and ΔHR are **generalisation tests, not tests of unfitted
structure.** Head-down tilt is already calibrated at 6°, 15°, 20° and 30°
(Sejersen 2022, Verdini 2019, Sibbald 1979), so 10° is an interpolation between
fitted angles. A hit there is real but not load-bearing.

### Resting MAP and HR — reported, and flagged

These are predictions, since nothing was spent.

**AN EXPECTATION STATED EARLIER IN THIS SCREEN WAS WITHDRAWN BEFORE
REGISTRATION, and the withdrawal is recorded because it changes what a miss
would mean.** The expectation was that the model's resting MAP would be badly
wrong in the young group and near-right in the older, as a fourth replication
of item 62.

**The model's own sources say otherwise.** `aging.py` cites Franklin 1997
(PMID 9236450, n=2036 normotensive Framingham men, up to 30 years of follow-up):
**MAP slope +0.016 mmHg/year** against a pulse-pressure slope of +0.68. Mean
pressure is essentially FIXED across the adult span in normotensive men, and
that is precisely why this model scales arterial compliance with age rather than
resistance.

Over 23 to 64 Franklin predicts **+0.66 mmHg**. The model produces **+0.23**.
So an age-invariant resting MAP is not a defect here — it is the sourced
behaviour, and the model reproduces the accompanying signature correctly:
pulse pressure widens, the mean does not.

**The registered expectation is therefore the opposite of the original one:**

> **Resting MAP should be close to age-invariant, near 95 mmHg in both groups.**
> If the study's two groups differ substantially in resting MAP, the model
> misses in BOTH — and the interesting question becomes whether the cohort
> differs from Franklin's, not whether the model differs from the cohort.

**This also puts a question against item 62**, which is the highest-priority
open item and whose headline is that the model "defends the wrong number" for
young people. Its evidence is two young cohorts sitting near MAP 76 against a
model at 92-95. If population MAP is near-flat with age, **there is very little
age law available to add**, and the 76 is more likely a cohort or convention
difference — supine catheterised volunteers against seated screened
populations — than a missing age dependence in the setpoint. Recorded here,
raised in the backlog, and NOT acted on: the model is frozen and this study's
results have not been seen.

### NOT SCORED, with the mechanical reason for each

**Systolic pressure, diastolic pressure and pulse pressure.** The model's pulse
pressure amplification is INVERTED — 0.88 against a measured 1.33 ± 0.16 — and
correcting it needs wave travel and reflection a lumped model does not have.
**The age interaction is what makes this disqualifying rather than merely
noisy:** amplification falls with age, so a finger-versus-central convention
error would be systematically larger in the young group — landing directly on
the age contrast that is the primary. MAP is nearly constant along the arterial
tree and survives this; SBP and DBP do not.

**Peripheral venous pressure.** The only compartment that could carry it,
`upper_body_vein`, sits at `height_m = 0.05` — heart level — and the code
comment gives the reason: *"a mid-neck height (0.15–0.20) would pool ~200 mL
into the upper body in head-down tilt and steal preload."* **Scoring a venous
pressure under head-down tilt would therefore be scoring that calibration
choice rather than physiology.** Screening this quantity also turned up backlog
item 65 — the hydrostatic term is omitted from every artery-to-vein exchange
segment — which is recorded there and is not claimed as a result of this study.

**Forearm blood flow.** Venous occlusion plethysmography requires an occlusion
mechanism the model does not have (the same absence that excluded the thigh
cuffs in `EXCLUDED.md` entry 2), and the forearm is not a model compartment.

**Venous catecholamines.** No counterpart anywhere in the model.

---

## The model scenario

Runner `005_run.py`, kept local per `CLAUDE.md`. Parameters here are sufficient
to reconstruct it.

**Patients:** male, ages 23.0 and 64.0, built through `build_patient_params`
with age and sex; no measured haemodynamics supplied.

**Anthropometrics — assumed and BRACKETED.** Height is not reported. Weight
follows from the reported BMI at the assumed height:

| height | young (BMI 23.9) | older (BMI 25.0) |
|---|---|---|
| 172 cm | 70.7 kg | 74.0 kg |
| **177 cm (headline)** | **74.9 kg** | **78.3 kg** |
| 182 cm | 79.2 kg | 82.8 kg |

**The SAME height is used in both arms**, so the between-group primary is not
polluted by an assumed anthropometric difference; only age and BMI differ.

**THIS IS A BSA BRACKET, NOT A STATURE BRACKET, AND THE CORRECTION MATTERS.**
The bracket was set up on the assumption that height reaches the tilt physics
through the hydrostatic lever arm. **It does not.** `build_patient_params` uses
`height_cm` in exactly one place — `bsa_mosteller(height_cm, weight_kg)` — and
every compartment's `height_m` is a fixed constant that is never rescaled. So a
172 cm and a 182 cm patient have **identical hydrostatic columns**, and this
bracket varies body-surface area alone. Opened as backlog item 66; recorded here
because it changes what the bracket is evidence about.

**Ventilation:** spontaneous, 14 breaths/min — awake volunteers breathing
freely. Nothing is paced, so backlog item 61 (inspiratory swing is a constant,
no tidal volume) does not bite here as it did in registration 001.

**Slow dynamics:** ON, at the `v1.0.0` default.

**Timeline, with apply times and measure windows as separate quantities** —
the stage-timing bug in registration 001 came from using one variable for both:

| phase | t (s) |
|---|---|
| settle, discarded | 0 → 120 |
| supine baseline | 120 → 720 |
| tilt ramp to −10° | 720 → 730 |
| head-down tilt | 730 → 1330 |

**Windows — BRACKETED, because the paper does not state its averaging window.**
Venous blood was taken in the last minute, which suggests but does not establish
a last-minute reading. Both are produced: a **last-minute** window (660–720 and
1270–1330) and a **whole-block** mean (120–720 and 730–1330). The baseline
window ENDS at tilt onset and the tilt windows begin only after the ramp
completes, so no window ever spans a transition.

**This bracket is not cosmetic.** Every existing tilt test in the suite runs
40 s, and `SETTLE_S = 60.0` in `slow_dynamics.py` — so **no tilt comparison this
project has ever made had slow dynamics active.** This run carries 540 s past
that threshold, with venous stress relaxation (τ = 250 s) roughly 88 % complete
by the end. If the two windows diverge, that divergence is itself a result about
structure nothing has constrained.

---

## Registered caveats

**Finapres measures finger pressure; the model reports a time-integrated central
MAP.** A convention flag on the absolute values. It largely cancels in ΔMAP and
again in Δ(ΔMAP), which is the reason the primary is answerable at all — but it
is not zero, and the age-dependence of amplification means it does not cancel
perfectly even in the primary. Registered as the main threat to the primary.

**The age law is partly fitted against McEniery 2005**, which supplies
population-mean MAP by decade and is used to validate `aging.py` at 25/55/75.
So the model's resting pressures at 23 and 64 are not innocent of age data,
even though this study's own values were not used. **The tilt RESPONSE is not
fitted by anything**, which is why the primary sits there.

**Head-down tilt at 10° is an interpolation between calibrated angles**, as
above. Registered so that a hit on the within-group deltas is not later
presented as more than it is.

**The older group is 64 and the model's reference is 55.** Nine years, against
32 for the young group. If the expected asymmetry in the MAP error does NOT
appear, that is evidence against item 62 and should be reported as such.

**No comorbidity correction is possible or needed** — this cohort is unusually
clean: healthy, normotensive, non-smoking, unmedicated, exercise-ECG screened.
**This is the best-matched cohort the blind phase has screened.**

---

## THE MODEL'S OUTPUT — the prediction

Headline run, assumed height 177 cm. Young 74.9 kg, older 78.3 kg.

### PRIMARY — young minus older. **NULL.**

| window | Δ(ΔMAP), mmHg | Δ(ΔHR), bpm |
|---|---|---|
| last minute | **+0.02** | **−0.04** |
| whole block | **+0.02** | **+0.00** |

### Response to head-down tilt, within each group

| | window | ΔMAP | ΔHR | ΔCVP | ΔCO |
|---|---|---|---|---|---|
| young (23) | last minute | **+0.36** | **−0.80** | +1.61 | +0.13 |
| young (23) | whole block | +0.35 | −0.75 | +1.60 | +0.13 |
| older (64) | last minute | **+0.34** | **−0.76** | +1.60 | +0.13 |
| older (64) | whole block | +0.33 | −0.76 | +1.60 | +0.13 |

**These four are the substantive predictions of this registration.** MAP rises
slightly and heart rate falls slightly on 10 degrees of head-down tilt, in both
age groups, by almost the same amount.

### Baselines and tilt values

| | | MAP | HR | SBP | DBP | PP | CVP | CO |
|---|---|---|---|---|---|---|---|---|
| young | supine | **94.97** | **70.80** | 108.2 | 83.3 | 24.85 | 4.04 | 5.90 |
| young | −10 deg | 95.33 | 70.01 | 108.8 | 83.3 | 25.53 | 5.65 | 6.03 |
| older | supine | **95.20** | **68.90** | 115.8 | 78.0 | 37.84 | 4.49 | 5.95 |
| older | −10 deg | 95.53 | 68.14 | 116.7 | 77.8 | 38.88 | 6.10 | 6.09 |

**Resting MAP differs by 0.23 mmHg across a 41-year age gap**, against
Franklin's +0.66. **Pulse pressure differs by 12.99 mmHg** over the same gap.
The age law moves the pulse and not the mean, which is what it was built to do.
SBP, DBP and PP are shown for completeness and are **not scored**, for the
reason given above.

### THE HEIGHT BRACKET — immaterial on every scored quantity

Last-minute window. Height is assumed, so it is bracketed; recall from the
scenario section that this varies **body-surface area only**, not the
hydrostatic column (backlog item 66).

| height | young ΔMAP | older ΔMAP | **Δ(ΔMAP)** | young ΔHR | older ΔHR |
|---|---|---|---|---|---|
| 172 cm | +0.37 | +0.34 | +0.02 | −0.76 | −0.75 |
| **177 cm** | **+0.36** | **+0.34** | **+0.02** | **−0.80** | **−0.76** |
| 182 cm | +0.36 | +0.33 | +0.03 | −0.77 | −0.75 |

**Bracket width: 0.03 mmHg on the primary, 0.01 mmHg on each within-group
ΔMAP, 0.04 bpm on ΔHR.** Resting MAP moves 94.83 → 95.10 in the young arm and
95.04 → 95.31 in the older across the whole 10 cm span.

**The assumed height is therefore not a threat to any registered quantity**, and
the headline run at 177 cm stands for all three. This is the fourth time
bracketing an unreported parameter has settled it rather than leaving a caveat
— and unlike registration 004's PIP bracket, which spanned zero on the primary
and was decisive, this one is simply harmless. **Both outcomes are worth having;
only measuring the bracket tells you which you have.**

### THE WINDOW BRACKET CAME OUT IMMATERIAL — a registered prediction that failed

The registration predicted, before the run, that the last-minute and whole-block
windows might diverge, because 10 minutes of tilt carries 540 s past
`SETTLE_S = 60.0` and venous stress relaxation has a 250 s time constant, so
**no tilt comparison in this project has ever had slow dynamics active.**

**They did not diverge. The bracket width is 0.01 to 0.05 mmHg on every
quantity**, and ΔCVP is flat at +1.61 against +1.60 — no measurable
stress-relaxation decay over 600 s.

**That is a measured negative and it is recorded as one.** Either a 10 degree
tilt is too small a perturbation to engage the mechanism measurably, or the
slow-dynamics path does less over ten minutes than its time constant suggests.
**The distinction is not resolved here and must not be asserted** — the model is
frozen, and chasing it now would be measuring rather than registering. Noted for
after the phase.

---

## RESULTS — appended 2026-09-20, after registration was pushed at `74f0e62`

**Comparator confirmed as s.e.m., not SD.** The registration had fixed SD on the
information available at screening. The paper reports mean ± s.e.m. throughout,
which the cohort line ("23 ± 1 years, mean ± s.e.m.") already indicated and
which an SD of 3 mmHg for systolic pressure across 11 men would not survive.
**SD is recovered as s.e.m. × √n** — ×3.32 young, ×3.16 older — and every tier
below uses it. This was confirmed from the paper before any tier was assigned,
not chosen afterwards.

### The study

| | young control | young HDT | young Δ | older control | older HDT | older Δ |
|---|---|---|---|---|---|---|
| systolic | 117 ± 3 | 120 ± 3 | +3 ± 1 | 130 ± 4 | 133 ± 4 | +2 ± 1 |
| **MAP** | **84 ± 3** | **85 ± 3** | **+2 ± 1** | **89 ± 3** | **90 ± 2** | **+1 ± 1** |
| diastolic | 67 ± 3 | 68 ± 3 | +1 ± 1 | 68 ± 3 | 69 ± 3 | +1 ± 1 |
| pulse pressure | 51 ± 2 | 53 ± 2 | +2 ± 1 | 62 ± 4 | 64 ± 4 | +2 ± 1 |
| **heart rate** | **63 ± 3** | **62 ± 2** | **−1 ± 1** | **58 ± 2** | **58 ± 2** | **0 ± 1** |

### Every scored quantity landed. Six tier A, two tier B, no misses.

| quantity | model | study | SD | distance | SD units | s.e.m. units | tier |
|---|---|---|---|---|---|---|---|
| ΔMAP young | +0.36 | +2 | 3.32 | 1.64 | 0.49 | 1.64 | **A** |
| ΔMAP older | +0.34 | +1 | 3.16 | 0.66 | 0.21 | 0.66 | **A** |
| ΔHR young | −0.80 | −1 | 3.32 | 0.20 | 0.06 | 0.20 | **A** |
| ΔHR older | −0.76 | 0 | 3.16 | 0.76 | 0.24 | 0.76 | **A** |
| resting MAP young | 94.97 | 84 | 9.95 | **10.97** | 1.10 | 3.66 | **B** |
| resting MAP older | 95.20 | 89 | 9.49 | **6.20** | 0.65 | 2.07 | **A** |
| resting HR young | 70.80 | 63 | 9.95 | 7.80 | 0.78 | 2.60 | **A** |
| resting HR older | 68.90 | 58 | 6.32 | **10.90** | 1.72 | 5.45 | **B** |

### AND IT IS WORTH ALMOST NOTHING. READ THIS BEFORE THE TABLE ABOVE.

**A model that predicted exactly zero for all four tilt responses would also
have scored tier A on all four.**

| quantity | study | a null model's distance | tier it would score |
|---|---|---|---|
| ΔMAP young | +2 ± 1 | 2.00 | 0.60 SD → **A** |
| ΔMAP older | +1 ± 1 | 1.00 | 0.32 SD → **A** |
| ΔHR young | −1 ± 1 | 1.00 | 0.30 SD → **A** |
| ΔHR older | 0 ± 1 | 0.00 | 0.00 SD → **A** |

**The study's tilt effects are 0 to 2 units against between-subject SDs of 3.2.**
Ten degrees of head-down tilt in a healthy man barely moves mean pressure or
heart rate, so **the test has essentially no power to discriminate between
models.** Four tier A results here are not evidence that the model is right;
they are evidence that the question was easy.

**This is registration 004's lesson in a new form.** There, wide spreads let a
model with the two groups swapped score well on each group separately. Here,
small effects let any model land. **Both are failures of the COMPARISON, not of
the model — and both are only visible because the scoring rule forces the
distance to be printed beside the tier.**

### PRIMARY — tier A, and uninformative exactly as registered

Model **+0.02**, study **+1** (young +2 minus older +1). Distance 0.98 mmHg,
which is 0.69 × the combined standard error of the difference.

**The study's own difference sits 0.71 SE from zero, so it did not find an age
difference either.** The registration said, before any result was seen:

> *"A tier A here would be uninformative and must be reported as such, because a
> model that cannot produce ANY age difference is not being tested by a study
> that happens not to find one."*

**That is precisely what happened, and it is recorded as a non-result.** The
direction is nominally right — both values positive — but claiming direction on
a predicted +0.02 against a measured +1 would be generous to the point of
dishonesty. **Item 51 remains untested by this study.** A study with enough
power to resolve an age difference in the reflex response would still be worth
finding.

### THE INFORMATIVE PART IS THE RESTING ABSOLUTES

Both tilt responses and the primary were flat. The four resting values were not.

**The model runs high on mean pressure in both groups, and FURTHER OUT IN THE
YOUNG: +10.97 mmHg against +6.20.** That is the pattern behind backlog item 62,
appearing for a fourth time and for the first time with both age groups measured
by one instrument in one laboratory — which removes the cohort-and-method
confound that weakened the earlier evidence.

**The model also under-predicts the age gap itself.** The study's groups differ
by **+5 mmHg** in resting MAP across 41 years; the model produces **+0.23**.

Resting heart rate is high in both, and worst in the older group: 68.90 against
58 ± 2, a distance of 10.90 and 5.45 s.e.m.

### AN EXPECTATION I WITHDREW BEFORE REGISTERING WAS RIGHT, AND THE WITHDRAWAL WAS THE ERROR

The original expectation, stated during screening, was that the model's resting
MAP would be badly wrong in the young group and closer in the older. **It was
withdrawn before this document was pushed**, citing Franklin 1997's MAP slope of
+0.016 mmHg/year, and the registered expectation was replaced with
near-invariance near 95 in both groups.

**Measured: +10.97 in the young and +6.20 in the older. The original expectation
was correct.**

**The mistake is specific and worth naming: Franklin's slope is LONGITUDINAL and
this study is CROSS-SECTIONAL, and one was applied to the other.** Backlog item
48 already documents exactly that divergence — Franklin followed men who were
normotensive at entry, while cross-sectional cohorts exclude at measurement the
people whose pressure rose, which is why the two designs disagree about ageing.
This cohort differs by +0.12 mmHg/year where Franklin gives +0.016.

**What the withdrawal did and did not cost.** The registered statement's second
clause — *"if the study's two groups differ substantially in resting MAP, the
model misses in BOTH"* — is borne out: the model is high in both. Both values
still land inside 2 SD, so "miss" is stronger than the scoring supports. The
withdrawal therefore changed the FRAMING of a correct prediction rather than
producing a wrong one. **It is recorded because a correction that makes a right
answer look surprising is a defect in the reasoning even when the score is
unaffected** — and because the error was made while attempting to be more
rigorous, which is the pattern this project has now hit three times.

### Quantities excluded in advance — reported, NOT scored

Systolic, diastolic and pulse pressure were excluded at registration because
the model's pulse-pressure amplification is inverted and the convention error is
age-dependent. **The exclusion was correct:** the model's central pulse pressure
is 24.85 and 37.84 against the study's finger values of 51 and 62.

**One observation, offered as unscored and confounded.** The model's PP widens
by **+12.99 mmHg** across the age span against the study's **+11**. That looks
like agreement, but peripheral amplification falls with age, which compresses
the measured widening relative to a central one — so the two errors push in
opposite directions and the agreement may be coincidental. **It cannot be
claimed either way and is not counted.** It would be worth a proper look against
a study reporting CENTRAL pressures by age.

**Also recorded:** the runner read the model's `sbp`/`dbp` outputs, which are
aortic. The model also exposes `brachial_sbp`/`brachial_dbp`, which would have
been the nearer convention for a finger measurement. This changes no tier,
because none of these quantities is scored, but a future registration comparing
peripheral pressures should use the brachial outputs.

### What this registration is worth

**A pre-registered null that behaved as declared, a set of tier A results that
the document itself argues should not be counted as success, and one real
finding: the age asymmetry in resting mean pressure, now measured within a
single cohort and a single instrument.**

The most useful output is methodological. **Two registrations in a row have now
produced tier A results that a broken model would also have earned** — 004 by
wide spreads, 005 by small effects. **A power check belongs in the screen:** can
this study's spread and effect size distinguish the model from a null? It would
have flagged this study before an hour of computation, and it would not have
excluded it — it would have set the expectation correctly in advance.
