# 001 — Paced breathing and posture, healthy volunteers

> ## Status: out-of-sample comparison, ordering not externally timestamped
>
> The scenario was fixed, the model run, and its outputs recorded **before the
> study's results were seen**. That ordering is documented in the project's
> working record but was not published first, so a reader cannot verify it
> independently.
>
> **Everything pre-registration protects against held.** The model is `v1.0.0`,
> unmodified. No parameter was fitted. The reported quantities were fixed in
> advance, including the ones that failed. And every caveat below was stated
> before the comparison — among them the prediction that a low baseline cardiac
> index would put the model on a steeper part of its Starling curve and make it
> over-respond to tilt, which is what happened.
>
> Later registrations are pushed before results arrive. This was the first study
> of the phase, and the procedure was corrected because of it.

- **Compared:** 2026-09-18
- **Model:** `v1.0.0`, artefact commit `90cc1d0`, unmodified
- **Study:** [PMID 38684421](https://pubmed.ncbi.nlm.nih.gov/38684421/) —
  `check_insample.py` → NOT FOUND
- **Verdict at screening:** YES, APPROXIMATED

---

## The study

Healthy volunteers, age 23 (range 19–30), 8 male and 2 female, in a quiet room at
22–24 °C. Semi-recumbent on a bench at 30° and at 60°. At each posture: 5 min
spontaneous breathing, 5 min breathing through an impedance threshold device
(ITD, −7 cmH₂O), 5 min paced breathing at 6 breaths/min. Outcomes were MAP by
finger cuff (Finometer) and cardiac output by ultrasound, with Modelflow
estimates from the finger pressure curve as a secondary measure.

**Both ITD conditions were omitted.** `SPONTANEOUS_ITP_SWING_CMH2O = -3.5` is a
module constant in `model/respiration.py`, not a `SimParams` field, so the
inspiratory swing cannot be deepened to −7 cmH₂O without editing frozen code.

## The model scenario

Runner: [`001_run.py`](001_run.py). Four independent settled runs — spontaneous
and 6 bpm, at 30° and 60° — each 300 s with the final 60 s averaged. Patient
built from demographics alone: age 23, male, 175 cm, 70 kg.

**Nothing was solved for.** No measured MAP, CO or CVP was entered, so the Tier 3
calibration defect that ended exclusion entry 3 does not apply here.

---

## Result

### Absolute values

| quantity | model | study (95 % CI) | tier |
|---|---|---|---|
| MAP 30° | 88.49 | 96.0 (92.0–104.5) | **B** |
| MAP 60° | 80.72 | 98.5 (93.0–105.5) | miss |
| CO 30° | 4.33 | 6.9 (6.0–11.2) | miss |
| CO 60° | 3.33 | 6.4 (5.6–8.8) | miss |
| HR 30° | 81.3 | 73 | — |
| HR 60° | 90.5 | 73 | — |

### Changes, 30° → 60°

No confidence interval is published on the changes, so these are **direction-only**.

| quantity | model | study | tier |
|---|---|---|---|
| ΔMAP | **−7.81** | **+2.5** | **F — direction wrong** |
| ΔCO | −0.99 | −0.5 | C |
| ΔHR | +9.2 | 0 | miss |

### Paced breathing, 6 bpm vs spontaneous — a predicted null

| quantity | model |
|---|---|
| ΔMAP at 30° | +0.01 |
| ΔCO at 30° | +0.00 |

**Predicted to be null before the comparison, and for a stated structural
reason:** respiratory rate changes the FREQUENCY of the intrathoracic pressure
swing, not its amplitude, so mean intrathoracic pressure over a cycle is
unchanged and mean venous return with it. **The model has no tidal volume** — the
swing depth is a constant — so it cannot represent the deeper breaths that are
the substance of slow paced breathing. A null here is an artefact of that gap,
not a physiological claim, and was recorded as such in advance.

---

## Reading it

**The model misses baseline and reflex compensation in the same direction.** By
the interpretation table agreed before the comparison, baseline-miss plus
Δ-miss is the confounded quadrant: we can say the model is off, not why.

**Cardiac output is the larger failure.** 4.33 against 6.9 L/min, outside even
the doubled-half-width band. The study's cohort is young, fit and hyperdynamic —
a CI around 3.7 L/min/m² — and the model produced 2.34 from demographics alone.
**The model's young-adult cardiac output is low**, which is consistent with the
reference patient being calibrated at 55.

**The MAP direction failure is the sharpest finding.** Going from 30° to 60°
head-up, the subjects' pressure ROSE by 2.5 mmHg and their heart rate did not
move at all — near-perfect orthostatic compensation. The model's pressure FELL by
7.8 mmHg and its heart rate rose by 9. **The model under-defends blood pressure
against orthostatic stress in young people**, which is what an age-independent
baroreflex calibrated on a middle-aged cohort would be expected to do
(backlog item 51).

---

## Severe limitations — why this is only somewhat modellable

**"Semi-recumbent" is not classified in the paper.** Clinically it usually means a
raised backrest with the hips flexed and the legs horizontal; the model has only
whole-body rigid tilt (backlog item 53). If the subjects were hip-flexed, the
model pooled far more blood in the legs than they did, which would account for
some of both the low cardiac output and the falling pressure. **This alone could
explain the direction failure**, and it cannot be resolved from the published
methods.

**60° is outside the tested envelope.** Validated head-up tilt stops at 45°, and
the documented failure mode in that direction is exactly this one — leg venous
collapse and underestimated MAP. The 60° row should be read as an extrapolation.

**Baseline cardiac output of 6.9 L/min is not reachable by this model** for a
patient of this description. That is the finding, but it also means the Δ
comparisons were evaluated at a different point on the Starling curve from the
subjects'.

**Registered caveats that still apply:** single sex against 8:2, assumed 175 cm /
70 kg (not reported), assumed spontaneous rate of 14 bpm (not reported),
finger-cuff MAP against a time-integrated central MAP, and the fixed-RSA point —
the model's respiratory sinus arrhythmia is a function of rate alone.

**One study. Not a verdict on the model, and not a pre-registered result.**
