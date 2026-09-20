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
