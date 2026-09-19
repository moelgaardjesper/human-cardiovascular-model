# 004 — Phenylephrine in preload-dependent vs preload-independent patients

- **Registered:** 2026-09-19
- **Model:** `v1.0.0`, artefact commit `90cc1d0`, unmodified
- **Identifier:** [PMID 27164015](https://pubmed.ncbi.nlm.nih.gov/27164015/) —
  requested AFTER the model was run and before this was pushed, per the
  procedure. `tools/check_insample.py 27164015` → NOT FOUND in code, docs or
  registrations.
- **Verdict:** YES, APPROXIMATED
- **Status:** REGISTERED — drug responses not seen

---

## Declared contamination — read this first

**The grouping PPV values were seen before registration.** The study's medians,
17 % (dependent) and 8 % (independent), were supplied while the ventilator
settings were being clarified. They are the GROUPING variable and are used here
as configuration input, the role baseline haemodynamics played in exclusion
entry 3.

**Consequence: PPV is not a scored prediction on this study.** The model's
normovolaemic PPV of 8.10 against their median of 8 is recorded below because it
was not fitted — the airway pressure was computed from the study's own tidal
volume and compliance, not tuned — but it is **not blind**, and it is excluded
from scoring.

**The drug responses were not seen.** ΔCO, ΔMAP, ΔHR and ΔSV in each group, and
the difference between groups, are what this registration predicts.

---

## The study, as supplied

Fifty ventilated surgical patients during hypotension, before and at peak MAP
effect of a phenylephrine bolus of 50–150 µg, given at the attending
anaesthetist's discretion. Measurements taken between induction and the start of
surgery, without surgical stimulation, by a resident not responsible for care.

**Groups by PPV measured before the drug:** preload-dependent ≥ 13 % (n=27),
preload-independent < 13 % (n=23). Age 65 vs 64, BMI 25 in both, men 12/27 and
16/23, **ASA 3 in 19/27 and 18/23**, with ACE inhibitors, beta blockers and
calcium antagonists common in both groups.

Anaesthesia: propofol and remifentanil TCI, atracurium. Ventilation: TV
8.2/8.3 mL/kg, PEEP 6, RR 14/13, respiratory-system compliance 48/46 mL/cmH₂O.

**Dose was comparable between groups: 1.5 (0.6) vs 1.4 (0.4) µg/kg, P = 0.279.**

**Primary outcome: cardiac output response to phenylephrine in each group.**

### What is calibrated here and what is not — the distinction matters

**The within-group response to phenylephrine is PARTLY CALIBRATED.** The suite
holds Schäfers 1999 (PMID 10073742) for exactly that: cardiac output down, heart
rate down, stroke volume up in healthy supine men, age-matched. So the
independent group's ΔCO, ΔHR and ΔSV are a generalisation test — does a response
fitted on healthy volunteers transfer to anaesthetised, comorbid 65-year-olds?
Real, but a hit there is not load-bearing.

**The BETWEEN-GROUP difference is not calibrated by anything.** Nothing in the
suite constrains how the phenylephrine response should differ with preload state;
that behaviour emerges from venous tone acting on the mobilizable reservoir,
Frank-Starling, and the baroreflex, none of which was fitted to this question.
**That is why the primary is the between-group difference and not the response
itself** — it is the part that tests unfitted structure.

---

## Why this is answerable where exclusion entry 6 was not

Entry 6 had the same propofol/remifentanil anaesthesia and failed, because the
hypotension the opioid produced **was** the trigger for the manoeuvre — the
model's anaesthetised patient was never hypotensive enough to need a vasopressor
and the titration degenerated.

**Here the grouping variable is PPV, which the model computes.** Each arm is
built by bleeding to the reported PPV rather than by reproducing the anaesthetic
state, so the missing opioid is context rather than mechanism. And the primary is
a **between-group difference**, so the anaesthetic, the comorbidity burden and
the dose are common to both arms and largely cancel.

---

## The model scenario

Runner `004_run.py`, kept local per `CLAUDE.md`. Parameters here are sufficient
to reconstruct it.

**Patient:** age 65, male, 170 cm, 72.2 kg (height not reported; assumed at the
reported BMI of 25). Sex not bracketed — in registration 002 the sex bracket on
an equivalent between-group interaction was 0.003–0.027 L/min, and this cohort
is 56 % male.

**Ventilation, computed rather than assumed:** PEEP 6 and RR 14 from the study;
tidal volume 8.2 mL/kg × 72.2 kg = 592 mL, over a compliance of 48 mL/cmH₂O,
gives a driving pressure of 12.3 and therefore **PIP 18.3 cmH₂O**.

**Groups:** preload-independent is normovolaemic; preload-dependent is bled until
PPV reaches the study's median of 17 %, which took **650 mL**.

**Drug:** phenylephrine at 2, 4 and 6 µg/kg/min. The model takes an infusion rate
and the study gave a bolus in µg/kg, and there is no pharmacokinetic mapping
between them — so the dose is **bracketed**, and the between-group primary is
insensitive to it because the study's two groups received comparable doses.

Each condition settled for 120 s with the final 40 s averaged.

---

## THE MODEL'S OUTPUT — the prediction

### PRIMARY: dependent minus independent

| quantity | dose 2 | dose 4 | dose 6 |
|---|---|---|---|
| **Δ(ΔCO), L/min** | **−0.130** | **−0.143** | **−0.142** |
| Δ(ΔMAP), mmHg | +6.12 | +6.15 | +6.12 |
| Δ(ΔHR), bpm | −2.36 | −2.31 | −2.31 |
| Δ(ΔSV), mL | −6.59 | −7.60 | −7.88 |

**Dose bracket on the primary: 0.013 L/min.** Negligible, so the prediction is
effectively a point: **phenylephrine costs about 0.14 L/min MORE cardiac output
in preload-dependent patients**, or **−10.9 percentage points** in relative terms
(−19.5 % against −8.6 %).

### Response within each group, dose 4

| | ΔCO | ΔMAP | ΔHR | ΔSV |
|---|---|---|---|---|
| independent | −0.410 | +14.40 | −13.33 | **+6.38** |
| dependent | −0.553 | +20.55 | −15.64 | **−1.22** |

**The stroke-volume prediction is the sharpest and most falsifiable thing here.**
The model says SV **rises** with phenylephrine in preload-independent patients
and **falls** in preload-dependent ones — opposite signs. The mechanism it
implies: venous recruitment raises filling in a patient who still has recruitable
volume, while in a depleted one there is little left to recruit and the afterload
rise dominates.

**This runs against one common clinical expectation**, which is that
preload-dependent patients should benefit most from an α1 agonist's venous
recruitment. The model predicts the reverse. It is stated plainly so a miss
cannot be softened afterwards.

### Baselines before the drug

| | MAP | CO | CI | HR | SV | CVP | PPV |
|---|---|---|---|---|---|---|---|
| independent | 90.45 | 4.76 | 2.58 | 77.4 | 61.5 | 3.32 | 8.10 *(not scored)* |
| dependent | 72.11 | 2.83 | 1.53 | 97.7 | 29.0 | 1.56 | 16.63 *(constructed)* |

**The dependent baseline is a registered prediction and I expect it to miss.**
Reaching PPV 17 % required a 650 mL bleed, which leaves the model at CI 1.53 —
more compromised than a typical surgical patient at that PPV. **If the study's
dependent group has a substantially higher CI, the model needs too much volume
loss to generate a given PPV**, which would be a finding about PPV sensitivity
rather than about phenylephrine.

---

## Registered caveats

**Comorbidity is heavy and uncorrectable.** ASA 3 in roughly three-quarters, with
ACE inhibitors, beta blockers and calcium antagonists common. Beta blockade and
calcium antagonism blunt the response to an α1 agonist, so **the model should
show a LARGER response than the cohort.** The between-group design contains this
but does not remove it.

**Remifentanil is unmodelled.** Its haemodynamic action is bradycardia and
sympatholysis, which lands on **ΔHR** much more than on ΔCO. **ΔCO is therefore
the better-founded comparator and ΔHR the weaker one**, and no direction is
claimed on ΔHR.

**FTc and peak velocity are excluded, and FTc for an instructive reason.** Flow
time corrected is a preload index in real patients. In this model systole is a
fixed 45 % of the cardiac cycle at every rate (backlog item 45), so flow time is
`0.45 × cycle` by construction and FTc is a pure function of heart rate with **no
preload sensitivity at all** — the model would report a constant where the study
reports the signal. Peak velocity needs a cross-sectional area the model does not
have.

**Cardiac output by oesophageal Doppler** is a flow measurement scaled by a
nomogram, not the total cardiac output the model reports. A convention flag — but
far better than a pulse-contour estimate, which the vasopressor would distort.

**No pharmacokinetics**, so this is a peak-effect comparison rather than a
trajectory. The study measured at peak MAP effect, which suits a plateau.

**Height assumed** at 170 cm; PPV values seen, as declared above.

---

## A finding from the abandoned first attempt

Before the compliance was known, PIP was bracketed over 14–20 cmH₂O. **The bleed
required to reach PPV 13 % varied five-fold across that range** — 650 mL at
PIP 14, 393 mL at 17, 135 mL at 20 — and at PIP 20 a *normovolaemic* model
patient already sat at PPV 11.6, a whisker below the threshold.

**So a PPV threshold selects a very different volaemic state depending on
ventilator settings.** The primary outcome's sign flipped across that bracket,
which is why the study's validity table mattered more than it appeared to.
Recorded because PPV thresholds are applied clinically without much attention to
airway pressure, and this is a model-derived argument that they should not be.

---

## RESULTS — appended in a LATER commit, after this is pushed

*(empty at registration)*
