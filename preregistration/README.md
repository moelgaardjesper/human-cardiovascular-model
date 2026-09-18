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

1. **Protocol in, results withheld.** Jesper supplies a study's *methods and
   cohort only*. No results, no figures, no abstract conclusions.
2. **Feasibility screen.** Can the model mechanically run this protocol? Three
   verdicts: **YES**, **NO**, **CONVENTION** — see below.
3. **In-sample check.** `python3 tools/check_insample.py <PMID or DOI>`. If the
   paper is already cited in `model/`, `tests/` or `tools/`, it is **not**
   out-of-sample and is excluded. Mechanical, not a matter of memory.
4. **Register.** Scenario, quantity convention, comparator, and **the model's
   measured output**. Commit and **push**.
5. **Then results.** Appended to the same file in a later commit, so the git
   history proves the ordering. Tier computed.

Studies that fail the screen go in `EXCLUDED.md` with the mechanical reason.
**That list is evidence, not waste** — it maps the architecture's boundary using
real studies rather than the authors' own account of its limits.

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

## The three verdicts

**YES** — the protocol maps onto parameters the model already has, and every
quantity the study reports has a model counterpart.

**NO** — the model cannot be asked this question. Record *which missing
mechanism* makes it impossible: no cellular compartment, no 1-D wave propagation
(so no pulse wave velocity, no augmentation index), no skeletal-muscle pump (so
no posture beyond −30°/+45°), no age-dependent baroreflex, no pregnancy or
sepsis physiology.

**CONVENTION** — the model can run the protocol, but reports a *different
quantity* than the study measured. Transmural versus intraluminal pressure;
lumen versus outer-wall diameter; a cycle mean versus an end-expiratory reading.
**Four apparent model defects during development dissolved into exactly this**,
so these are registered with the convention pinned explicitly and the comparison
flagged as convention-sensitive.

The verdict concerns **mechanics only** — can the ODE be driven this way, do the
required outputs exist. Never whether the model would look good. The moment
"can it?" becomes "would it do well?", the screen has become the fitting step
this procedure exists to prevent.

### DO NOT RUN THE MODEL WHILE SCREENING

**Feasibility is decided by reading the code, not by running scenarios.** If a
protocol is rejected, no simulation of it should ever have been performed.

**Why, in Jesper's words:** if the model is run on a study that is then rejected,
and the output happens to look plausible, there is pressure to reclassify the
study as feasible — and pressure the other way when the output looks poor. That
makes the feasibility verdict depend on the answer, which selects studies by how
well the model does on them. **It is the fitting step re-entering through the
screen**, which is precisely what the previous paragraph forbids and precisely
what is easiest to do without noticing.

**This rule was added because it had already been broken twice**, on the first
two studies screened. Both times the run was also unnecessary: each blocker was
established by reading a single expression in `model/gravity.py` or
`model/circulation.py`. **If you need to run the model to find out whether it can
do something, you are already measuring** — stop, and look at the mechanism
instead.

Once a study passes the screen, running the model is not merely allowed but
required: the registered prediction *is* its output. The line falls at the
verdict, not at the keyboard.

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
