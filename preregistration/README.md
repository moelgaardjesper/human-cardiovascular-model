# Pre-registration — the blind validation phase

## Why this directory exists

Every comparison in `freeze/v1.0.0/` was made against literature that was
available while the model was being built. Some of it shaped the model
directly; the rest could have, and there is no way for a reader to tell which.
That is the ordinary condition of a modelling paper and it is why such papers
persuade so little.

This directory fixes the ordering. For each study, a prediction is written,
committed and **pushed to GitHub before the result is seen**. The push is what
makes it credible: a file on the author's disk proves nothing, because it could
have been written at any time. A commit in a public repository carries a
timestamp nobody involved can move.

The model is frozen at `v1.0.0`. It does not change during this phase. If a
prediction misses, that is the finding.

## The procedure

1. **Protocol in, results withheld.** Jesper supplies a study's *methods and
   cohort only*. No results, no figures, no abstract conclusions.
2. **Feasibility screen.** Can the model mechanically run this protocol —
   can the ODE be driven that way, do the required outputs exist? Three
   verdicts: **YES**, **NO**, or **CONVENTION** (it can run it, but reports a
   different quantity than the study measured). See *the three verdicts* below.
3. **In-sample check.** `python3 tools/check_insample.py <PMID or DOI>`. If the
   paper is already cited anywhere in `model/` or `tests/`, it is **not**
   out-of-sample and is excluded. This is mechanical rather than a matter of
   anyone's memory.
4. **Register.** One file per study, from `TEMPLATE.md`. Commit and **push**.
5. **Then, and only then, results.** They are appended to the same file in a
   later commit, so the history proves the ordering.

Studies that fail the screen go in `EXCLUDED.md` with the mechanical reason.
**That list is evidence, not waste** — it maps the architecture's boundary using
real studies rather than the authors' own account of its limits.

## The three verdicts

**YES** — the protocol maps onto parameters the model already has, and every
quantity the study reports has a model counterpart.

**NO** — the model cannot be asked this question. Record *which missing
mechanism* makes it impossible: no cellular compartment, no wave propagation
(so no PWV or augmentation index), no skeletal-muscle pump (so no posture
beyond −30°/+45°), no age-dependent baroreflex, and so on.

**CONVENTION** — it can run the protocol, but the model reports a different
quantity than the study measured. Transmural versus intraluminal pressure;
lumen versus outer-wall diameter; a cycle mean versus an end-expiratory
reading. **Four apparent model defects dissolved into exactly this during
development.** These are registered, with the convention pinned explicitly and
the comparison flagged as convention-sensitive.

The verdict is about **mechanics only**. Never about whether the model would
look good. The moment "can it?" becomes "would it do well?", the screen has
become the fitting step this whole procedure exists to avoid.

## What counts as a miss — agreed before the first result

A prediction states a direction **and** a magnitude with an interval.

- **Direction wrong** → miss. Unambiguous.
- **Magnitude outside the registered interval** → miss, even if the direction
  is right.
- **Inside the interval** → hit.

Direction-only predictions are nearly free and prove almost nothing, so they do
not count as registered predictions on their own.

**The interval is set before the result and is not renegotiated afterwards.**
If it turns out to have been too wide to be meaningful, that is reported as a
weak prediction rather than quietly retold as a success. A miss that is
explained afterwards is still a miss; the explanation goes in the write-up
beside it, not instead of it.

## Integrity rules

- **Nothing is removed from this directory.** A registration that turns out
  badly stays, results and all.
- **The model does not change during the phase.** If a bug is found, it is
  recorded and fixed *after* the phase, and the affected predictions are
  reported as made against a model with a known defect.
- **Every registration names the model commit and the artefact it was made
  against** — `v1.0.0`, `90cc1d0`.
- **No peeking at a result before its registration is pushed.** If it happens
  by accident, that study is excluded and the reason recorded here.
