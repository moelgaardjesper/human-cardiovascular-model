# THE v1.0.0 BLIND PHASE IS CLOSED — 2026-09-24

**Fourteen studies screened. Six taken forward. Eight excluded. Five scored.**

**What this phase was for.** We froze the model and then gave it studies chosen
to find out how it would break. That is what it did.

**What it found, and these are load-bearing.**

**The baroreflex has no age dependence.** Registration 006 predicted a zero
difference between 25-year-olds and 68-year-olds in the heart-rate response to
tilt. The study measured 15 bpm against 3.6. Before this the gap rested on
reading `BaroreflexController.__init__` and noticing it takes no age argument.

**The legs cannot be recruited by venoconstriction.** Registration 007 predicted
that phenylephrine would lower stroke volume in a patient made preload-dependent
by head-up tilt. It nearly doubled it — measured +96 per cent against a predicted
−4. The model's leg veins respond to gravity but not to drugs, because they sit
outside the mobilizable venous reservoir. Backlog items 9 and 64 are one defect.

**Match the quantity before comparing.** Registration 005 reported the model's
resting mean pressure as 11 mmHg too high. It was measured at the finger and the
model reports an aortic pressure. Most of the gap was the site. This is the fifth
instance in the project and the first one found inside a pre-registered test,
which makes it the best evidence for it.

**Five more defects were found by reading code to build the scenarios**, not by
any study result: the hydrostatic loop does not close, patient height does not
scale the hydrostatic column, pulse pressure variation is destroyed by the
output-decimation parameter, brachial diastolic pressure is about 19 mmHg high,
and the tilt suite asserts only signs and wide bands — `dsv < 0` passes for any
fall.

**What it cost.** A blind study is single-use. These fourteen are spent and
cannot test the model again. Six of the eight exclusions were screened on methods
alone with no results seen, so those stay clean and become available as each
blocking mechanism is built.

**What the record is worth.** Every prediction was committed and pushed before
its result was seen. Three of the failures were predicted in advance with the
mechanism named. A model that was frozen, tested and found to fail in specific
diagnosable ways is the point of the exercise, not a problem for it.

**What happens next.** The faults above are fixed toward **v1.1.0**. The next
blind phase runs against that version, on studies not used here.

---

# Pre-registration — the blind validation phase

## Why this directory exists

Every comparison in `freeze/v1.0.0/` was made against literature available while
the model was being built. Some of it shaped the model directly; the rest could
have, and there is no way for a reader to tell which. That is the ordinary
condition of a modelling paper and it is why such papers persuade so little.

This directory fixes the ordering. For each study, the model is run and **its
output committed and pushed to GitHub before the result is seen**. The push is
what makes it credible: a file on the author's disk proves nothing, because it
could have been written at any time. A commit in a public repository carries a
timestamp nobody involved can move.

The model is frozen at `v1.0.0`. It does not change during this phase. If a
prediction misses, that is the finding.

## The procedure

**The order of these steps is the whole mechanism. Step 5 in particular is later
than it looks, and deliberately so.**

1. **Protocol in, results withheld, AND NO IDENTIFIER YET.** Jesper supplies a
   study's *methods and cohort only*. No results, no figures, no abstract
   conclusions — and no PMID or DOI.
2. **Feasibility screen**, by reading the code. **The model is not run.** Verdicts
   and the three rejection shapes are below, together with three checks to make
   first: a controlled variable, a supplied independent variable, and — at
   step 3 — a patient that cannot be built.
3. **Baseline gate: build the patient and check where it lands.** This is the
   one stage that runs the model, and it is decided on the BASELINE ALONE. See
   below for why that is not a contradiction of step 2.
4. **If it passes: build the scenario, run the frozen model, record its output.**
   That output is the prediction.
5. **NOW ask for the identifier**, and run
   `python3 tools/check_insample.py <PMID or DOI>`. If the study is already cited
   in `model/`, `tests/` or `tools/`, discard the comparison and log it as
   IN-SAMPLE.
6. **Commit and PUSH the registration**, outputs included.
7. **Then results**, appended in a later commit so the history proves the
   ordering.

### Why the identifier comes AFTER the run, not before

**A PMID is a key to the results.** Anyone holding one can fetch the abstract,
and an abstract carries the findings. Requesting it early — which an earlier
version of this file did, precisely to keep identifier requests and results
requests distinct — creates the contamination route it was trying to close.

Running first costs nothing that matters. If the in-sample check then fails, a
few minutes of computation is discarded; **the prediction was already fixed, so
nothing can flow backwards into it.** The check protects the VALIDITY of a
comparison, not the independence of the prediction, and it does that equally well
after the fact.

**Exclusions are different.** A study rejected at screening is never run, so its
identifier can be requested whenever — there is no prediction left to protect.

## THE MODEL'S OUTPUT IS THE PREDICTION

This is the core of the design, and it is worth being explicit about why.

An earlier draft had the author register an expected value with an uncertainty
interval — "ΔCO should fall by about 0.8, somewhere between 0.4 and 1.2". That
was wrong twice over.

**It measured the wrong thing.** Whether the author correctly anticipates the
model's own output is a fact about the author. A reader wants to know whether
the *model* reproduces physiology. Authorial confidence belongs in a paper about
a simulator approximately nowhere.

**And it was redundant.** The model is deterministic — no random number
generation anywhere, which is part of the freeze. Once the scenario and the
quantity convention are fixed, the model produces exactly one number. There is
nothing left to estimate. An interval wrapped around it is not a prediction but
a hedge around a prediction that already exists.

So a registration does not say *"I expect roughly −0.8"*. It says:

> The model, frozen at `v1.0.0`, run at these parameters, reading this quantity,
> produces **−0.73 L/min**. Here is that number, timestamped, before the study's
> result has been seen.

Falsifiable without ambiguity, and impossible to sandbag, because the author
does not choose it. You run the model and write down what it says.

## The verdicts

**Reject only when the model cannot be ASKED the study's question. Not when the
setup is imperfect.**

That sentence is the whole standard, and it replaced a much stricter one on
2026-09-18 after three consecutive rejections, of which one was wrong.

**YES** — the model can be asked the study's question. Some inputs will differ
from the study; say which, and register the difference. This is the NORMAL case,
not a concession.

**YES, APPROXIMATED** — as above, but a substitution is material enough to name
in the result. Crystalloid standing in for albumin. A subgroup standing in for a
mixed cohort. A patient matched on measured haemodynamics rather than on the
disease that produced them. **Register what was substituted and in which
direction it is likely to matter.**

**CONVENTION** — the model can run the protocol but reports a *different
quantity* than the study measured: transmural versus intraluminal pressure,
lumen versus outer-wall diameter, a cycle mean versus an end-expiratory reading.
Four apparent defects during development dissolved into exactly this. Register
with the convention pinned and the comparison flagged as convention-sensitive.

**NO** — the model cannot be asked the question at all. Three shapes, and
nothing else qualifies:

- **A required mechanism is absent.** No reactive hyperaemia after tourniquet
  release, because nothing accumulates ischaemic metabolites.
- **The quantity collapses into another one**, so the model answers by
  arithmetic rather than physiology. At tilt zero the gravitational term
  vanishes, so 0 G is identical to supine and a microgravity prediction is
  "no change" by construction.
- **The comparison itself is unrepresentable.** Passive leg raise is implemented
  as head-down tilt, so a study contrasting the two is asking the model to
  distinguish a thing from itself.

### Check for a controlled variable before anything else

**A variable the clinician actively controls cannot be used to validate the
model.** If a protocol says blood pressure was *maintained* in some range with
fluids and vasoactive agents, then blood pressure is not an outcome — it is a
set-point held by a feedback loop the paper does not record.

It is worse than losing that one variable. The loop acts through fluids and
vasopressors, so **cardiac output, stroke volume and filling pressures are all
confounded** by administration that is usually described only as
"individualised".

This is common in intraoperative studies and invalidates more than it first
appears to, so check for it early — before spending effort on mechanisms. It is
also a property of the STUDY, which makes it permanent: no amount of model
development makes such a protocol testable.

### Does the model COMPUTE what the study varies, or is it TOLD?

**Ask this of the study's independent variable.** It is read from the code and
takes a minute, so ask it alongside the controlled-variable check.

If the quantity the study manipulates is a model **input** rather than something
the model derives, then the two arms differ only by what the modeller assigns
them, and the comparison prescribes its own answer.

**Exclusion entry 7 is the case that put this here.** Ten degrees of head-up
tilt during spinal anaesthesia works by changing the cephalad spread of the
local anaesthetic. `spinal_anaesthesia(block_height)` takes the block level as
an argument — there is no cerebrospinal fluid, no baricity, no drug
distribution — so posture cannot move it. The two arms would have differed by
two numbers chosen by hand.

**THIS IS NOT A FOURTH REJECTION SHAPE. It is a detector for the first and the
third**, in the one case where they are easy to miss. The absent mechanism here
is intrathecal drug spread, which is shape 1 — but because the quantity it would
have produced happens to be a settable argument, the absence can be papered over
without noticing, by typing a number in.

**That is what makes it worth a check of its own.** Shape 1 usually announces
itself: ask for reactive hyperaemia and the model does nothing at all. Here the
model answers fluently, with a plausible difference between arms, and **nothing
about the output looks wrong.** Silence is easy to spot; fluency is not.

Compare the two synonym cases, which are shape 2. Passive leg raise IS head-down
tilt and 0 G IS supine (backlog items 53 and 57) — there, two named scenarios
collapse into one and the model returns a difference of zero. **A zero is
visible. A fabricated non-zero is not.**

**It is not the same as a spent value.** A spent value is a legitimate
configuration input that is then barred from scoring. This is worse: the
supplied quantity IS the study's mechanism, so nothing downstream of it is a
prediction at all.

### Can the patient be built? — the baseline gate

**Screening checks the MANOEUVRE and misses the PATIENT.** Two of seven
exclusions passed the feasibility screen and then failed when the starting state
would not build:

- **Entry 3** could not reach the cohort's operating point. Asked for MAP 79.2,
  CVP 6.4 and CI 3.1, the model settled at 94.07, 2.52 and 2.77.
- **Entry 6** could not reach the anaesthetic state. The model's anaesthetised
  patient never became hypotensive enough to need the vasopressor the protocol
  titrates, so the study's central manoeuvre could not be staged.

Both were real work spent after a verdict of YES. So configuration is its own
gate, between the screen and the prediction.

**This is the one stage that RUNS the model, and that does not contradict "do
not run the model while screening".** That rule protects the prediction.
Building a patient does not touch the prediction: a baseline is a starting
state, and the model's response to the protocol is still unmeasured when this
gate is decided.

**THE INTEGRITY CONDITION IS NOT OPTIONAL.** The decision must rest on the
**baseline alone**. The model's output on the study's manoeuvre must play no
part, and the exclusion entry must say so explicitly, as entry 3 does. Without
that sentence this gate becomes a route for quietly discarding studies whose
results looked unpromising — the exact failure the exclusion log exists to
prevent.

**Record what was requested and what the model settled at, as a table.** That
turns a rejected study into a measurement of the calibration rather than a lost
afternoon: entry 3's table is the evidence behind backlog item 58.

### The failure mode this standard exists to prevent

The first three studies screened were all rejected, and the third was rejected on
an accumulation of margins: a colloid the model substitutes with crystalloid, a
cohort that was 13/21 on the ventilation mode the model has, a tilt sequence
wrongly believed impossible, and a patient configurable from measured MAP, CVP
and CI.

**"Every element matches or reject" is not a screen — it is a way of never being
tested**, and it fails in the flattering direction, because a model that is never
asked a question is never wrong. That is the opposite of what a freeze is for.

**An imperfect comparison, with the imperfections registered in advance, is worth
far more than a perfect comparison that never happens.** If a substitution turns
out to matter, the miss says so, and the registered caveat is what lets a reader
tell a substitution artefact from a model defect.

### Caveats are registered, never used afterwards

A caveat written before the result explains a miss. The same words written after
it excuse one. Everything that might be blamed later must be named at
registration — and a caveat that was *not* registered cannot be introduced once
the result is known.

## Using reported data as INPUT — a value is spent once

**A study's reported values may be used to configure the scenario. Better a
comparison built on some of a study's data than a study discarded.** The model
is validated on a short list of quantities — cardiac output, cardiac index, mean
arterial pressure, heart rate, stroke volume — and everything else a paper
reports is available as setup.

**The rule that keeps this honest: a value is SPENT ONCE.** Use it to configure,
or score it, never both.

1. **Any reported value may be used as configuration input.**
2. **A value used as input cannot be scored.** It is no longer a prediction; the
   model was told the answer.
3. **Nor can anything trivially derived from it.** Cardiac index is cardiac
   output over body surface area, so spending one spends the other. Mean
   pressure spent as input compromises systolic and diastolic. Ask whether a
   reader could recompute the "prediction" from the input; if so, it is spent.
4. **Declare at registration which values were spent**, in the registration
   itself rather than in a footnote, so a reader can see exactly what the model
   was given and what it had to produce.

### Why this is not a loophole

The worry is obvious: given enough of a study's data as "configuration", a model
can be walked to any answer. Three things stop that.

**The spent values are declared**, so the reader sees the size of the input.
**The scored quantities are fixed before the result**, so nothing can be
reclassified afterwards. And **a between-group or before-after difference is
usually the primary**, which is insensitive to a configuration that is common to
both arms — registration 004 spends PPV to build its two groups, and the
grouping cannot manufacture a difference in how each group responds to a drug.

### Precedents

**Exclusion entry 3** — the ICU study's baseline MAP, CVP and CI were to be spent
configuring the patient. It failed for an unrelated reason: the model could not
be configured to them at all.

**Registration 004** — the study's PPV medians, 17 % and 8 %, were spent
constructing the two groups. **PPV is therefore not scored there**, and the
registration says so in its opening section. The drug responses, which were never
supplied, are what it predicts.

## Scoring

Tiers are computed from the data. **Nobody nominates a target beforehand**, for
two reasons: the tier a result lands in is an objective fact that a prior claim
cannot move, and letting the author call the tier invites sandbagging — call the
loosest tier every time and every result becomes a hit.

| tier | meaning |
|---|---|
| **A** | inside the study's own reported spread |
| **B** | a defined stretch beyond it |
| **C** | direction correct, magnitude outside B |
| **F** | direction wrong |

**Tier A means the model's value would not look out of place inside that study's
own data.** Each comparator type is a different expression of the same idea:

| study reports | tier A | tier B |
|---|---|---|
| mean ± SD | inside 1 SD | inside 2 SD |
| median (Q1–Q3) | inside the IQR | within one further IQR beyond the **nearer** quartile |
| mean (95 % CI) | inside the CI | within twice the CI half-width |
| range (min–max) only | inside the range | within 25 % of the range beyond the nearer end |
| point value, no spread | *not available* | *not available* |

**The comparator is named per quantity at registration**, because it is a
property of the study and must be fixed before anyone can choose it
conveniently. After the fact, "within 1 SD" can be made to mean a door twenty
times wider or narrower.

**A study reporting no spread can only reach C or F.** That is the truth rather
than a defect: with no spread there is nothing to be close to, and supplying an
SD would be fabrication. Those quantities are labelled **direction-only** at
registration and **counted separately**, so they never dilute the tier-A rate.

**Asymmetric spreads keep their asymmetry.** Schäfers reports median −1.15 with
quartiles −1.25 to −0.40 — wider on one side. Tier B extends by one further IQR
from the *nearer* quartile rather than symmetrising into a spread the study
never reported.

### Always report the distance, not only the tier

Every result records **how far** the model sat from the study's central value,
as a number. A tier is a label on a continuous quantity, and printing only the
label is what lets a 1.8-SD miss be retold as "within 2 SD ✓".

Where the study publishes *n*, the distance is given in **both** SD and SEM
units. The tier comes from the SD, because the model runs as a representative
individual — age- and size-matched to the cohort — so "would this look like a
plausible participant?" is the claim it is actually making. The SEM figure sits
beside it for a reader who wants to ask the stricter question, whether the model
reproduces the cohort *mean*. Two numbers, no extra judgement.

### Direction is a floor

A wrong direction is **F** however small the numerical gap. A model that moves
cardiac output the wrong way has failed, and being wrong by a little is not a
partial success.

## Reporting a result — over-stating failure is also a distortion

**Report what landed and what did not, at equal weight.** A write-up that leads
with the failure and treats the successes as footnotes is as distorted as the
reverse, and it is the easier mistake to make while feeling scrupulous.

Registration 004 is the example. The first draft of its results led with the
direction failure, described eight individual predictions inside the study's
spread as "six of eight" (an undercount), and framed them as a caveat — *"and
the primary still fails"*. **All eight landed, five within one standard
deviation.** The honest headline is narrower and more useful than "the model
failed": the model is not wrong about phenylephrine, it is wrong about which
preload state responds which way.

**A precise failure is worth more than a dramatic one**, and precision requires
saying what worked.

## What a registration file contains — four parts, and keep it short

**Registrations 004, 005 and 006 run to 335-370 lines each. That is too long**
(Jesper, 2026-09-23). They were not retrofitted; the shape below applies from
registration 007 onward.

**1. The study.** What was done, to whom, measured how. Plain sentences.

**2. The scenario.** The patient, the settings, the spent values, the registered
caveats. A table where a table fits.

**3. The result.** The numbers, with the tier for each. This is the part a reader
came for.

**4. Analysis.** Short. A few paragraphs at most.

**EVERYTHING ELSE GOES IN `docs/validation_log.md`.** The method, the reasoning,
the rejected alternatives, the failed attempts, the sensitivity checks. That file
is the working record and it is not published. **A reader of the registration
wants the prediction and the score, not the deliberation behind it.**

Registration 007 is the worked example: 144 lines public, with the inversion
method, the airway-pressure fit and a method error moved to the ledger.

### Write it plainly

**ASD-STE100 as a guide**, which is the standing rule for everything in this
project. Short sentences. One idea each. Active voice. Keep the clinical terms —
MAP, stroke volume, preload-dependency — and simplify the structure around them.

**Say the simple version first and add detail after.** The first paragraph should
stand on its own.

## Integrity rules

- **Nothing is removed from this directory.** A registration that turns out
  badly stays, results and all.
- **The model does not change during the phase.** A bug found mid-phase is
  recorded and fixed afterwards, and the affected predictions are reported as
  having been made against a model with a known defect.
- **Every registration names the model commit** — `v1.0.0`, artefact `90cc1d0`.
- **A miss explained afterwards is still a miss.** The explanation goes beside
  the result, never instead of it.
- **No peeking.** If a result reaches the author before registration is pushed,
  that study is excluded and the reason recorded.

## Design history

This scheme was argued into shape by Jesper, and two layers were removed:

1. **The author-nominated target tier** — collapsed because calling the loosest
   tier every time would have guaranteed a perfect record while proving nothing.
   Tiers are now computed from data only.
2. **The author's prediction interval** — collapsed because the model's own
   output already *is* the prediction, and because calibration of the author
   measures the wrong thing for a paper about a model.

Both were mine. Both made the scheme weaker while looking more rigorous, which
is worth recording as its own small lesson.

3. **The screening standard itself**, rewritten 2026-09-18 after three
   consecutive rejections. The third was wrong: it rested on an accumulation of
   margins plus one plain factual error — that a tilt sequence could not be run,
   when `LiveSession.update_params()` changes tilt mid-run and is directly
   scriptable. **A screen that demands every element match is a way of never
   being tested.** The standard is now "can the model be ASKED this question",
   and imperfections are registered rather than refused.

4. **A fourth screening standard, proposed and withdrawn the same day,
   2026-09-21.** A study was declined not because the model could not be asked
   it, but because a failure would have been hard to ATTRIBUTE — the useful
   measurement sat on an operating point already known to be wrong. A new
   exclusion category was written for it. **Jesper reversed it within the hour,
   and the reversal is the correct one.**

   **The argument that settles it: declining a study because the model is
   expected to fail is the flattering direction.** It is the same error as the
   over-rejections above, wearing a more sophisticated argument.

   **And it discards the most valuable thing the study offers.** This project
   claims two ARCHITECTURAL limitations — pulse pressure amplification is
   inverted, and the model collapses beyond 45 degrees of head-up tilt. Those are
   currently supported by our own assertion plus one in-house measurement. **A
   pre-registered prediction of our own failure, confirmed blind against a cohort
   we have never seen, is far stronger evidence than either.** `article_notes.md`
   says the paper should report "which of its failures were predicted in
   advance". A known limitation is therefore an ASSET in a blind test, not a
   reason to skip one.

   The category was deleted. **Poor attributability is a caveat to register, not
   a reason to decline.** It belongs in the registration, next to the predicted
   failure it qualifies.

The pattern across all FOUR is the same: each version looked more rigorous than
its replacement while protecting the model from being tested. **Three of the four
were mine, and the fourth was too. That is the failure mode to watch for in this
role — not carelessness, but caution that flatters.**
