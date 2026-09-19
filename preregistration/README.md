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

**The order of these steps is the whole mechanism. Step 4 in particular is later
than it looks, and deliberately so.**

1. **Protocol in, results withheld, AND NO IDENTIFIER YET.** Jesper supplies a
   study's *methods and cohort only*. No results, no figures, no abstract
   conclusions — and no PMID or DOI.
2. **Feasibility screen**, by reading the code. **The model is not run.** Verdicts
   and the three rejection shapes are below.
3. **If it passes: build the scenario, run the frozen model, record its output.**
   That output is the prediction.
4. **NOW ask for the identifier**, and run
   `python3 tools/check_insample.py <PMID or DOI>`. If the study is already cited
   in `model/`, `tests/` or `tools/`, discard the comparison and log it as
   IN-SAMPLE.
5. **Commit and PUSH the registration**, outputs included.
6. **Then results**, appended in a later commit so the history proves the
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

The pattern across all three is the same: each version looked more rigorous than
its replacement while protecting the model from being tested.
