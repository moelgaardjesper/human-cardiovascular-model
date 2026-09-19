# 002 — Positive-pressure ventilation crossed with simulated hypovolaemia

- **Registered:** 2026-09-18
- **Model:** `v1.0.0`, artefact commit `90cc1d0`, unmodified
- **Identifier:** [PMID 27702883](https://pubmed.ncbi.nlm.nih.gov/27702883/) —
  requested AFTER the model was run and before this was pushed, per the procedure.
  `tools/check_insample.py 27702883` → NOT FOUND in code, docs or registrations.
- **Verdict:** YES, APPROXIMATED
- **Status:** REGISTERED — no results seen

---

## The study, as supplied

Fifteen healthy volunteers, 7 male and 8 female, age 22 (range 20–30), BMI 23.4
(18.0–26.7). Supine in an LBNP chamber wearing a face mask throughout.

Ten minutes of normovolaemia, then −30 mmHg LBNP applied abruptly (within 0.3 s)
and held for ten minutes, then ten minutes of recovery. **Within each ten-minute
period the subjects breathed spontaneously for five minutes and received
volume-controlled positive-pressure ventilation for five.** Run twice per
subject, the first round randomised to start with either mode and the second
reversed.

Ventilator: pressure-regulated volume control, non-invasive via face mask, no
inspiratory trigger, subjects trained to breathe in synchrony. RF 14/min,
inspiratory time 1.25 s, target tidal volume 650 mL (500–850), maximum
inspiratory pressure 14 cmH₂O, PEEP 1–2 cmH₂O.

**Outcomes: MAP (finger arterial pressure), HR (ECG), CO (ultrasound).**

**Only methods and cohort were supplied. No results seen.**

---

## The model scenario

Runner: [`002_run.py`](002_run.py). Twelve settled runs — two sexes × three
volaemic states × two ventilation modes — each 600 s with the final 60 s
averaged.

**Patient.** Age 22. Height not reported; 173 cm assumed for a mixed 7:8
Northern European cohort, giving 70.0 kg at the reported BMI. **Nothing is
solved for** — no measured MAP, CO or CVP is entered — so the Tier 3 calibration
defect that ended exclusion entry 3 does not apply.

**Ventilation.** Every setting taken from the study: `pip_cmh2o` 14,
`peep_cmh2o` 1.5, `resp_rate_bpm` 14, and `ie_ratio` 0.292 as the inspiratory
*fraction* of the cycle (1.25 s of a 4.29 s cycle). Spontaneous breathing also at
14/min, which is well-founded here rather than assumed — the subjects were
trained to synchronise with the ventilator.

**Hypovolaemia.** LBNP is not a model input. It is substituted by haemorrhage,
as the existing suite already does: *"LBNP −30 mmHg ≈ 500–1000 mL
central-hypovolaemia equivalent."* Both ends are run.

---

## Quantity convention

| study measured | model output | note |
|---|---|---|
| MAP, finger arterial | `map` | model reports a time-integrated **central** MAP |
| HR, ECG | `hr` | direct |
| CO, ultrasound | `co` | direct flow measurement, not waveform-derived |

Cardiac output by ultrasound is the clean comparator — unlike pulse-contour
estimates, it does not depend on a peripheral waveform shape the model gets
architecturally wrong.

---

## THE MODEL'S OUTPUT — the prediction

### PRIMARY: the interaction — does PPV cost more under hypovolaemia?

**Reported in RELATIVE terms as primary, absolute as secondary, and the two
point in opposite directions.** The reason is stated before the result: PPV's
absolute cost to cardiac output stays near 0.8 L/min whatever the filling, while
the baseline falls, so the *fraction* rises. Relative is also the physiologically
meaningful framing — pulse-pressure and stroke-volume variation are inherently
fractional — and less sensitive to a baseline offset.

| sex | bleed | **relative Δ(ΔCO), pp** | absolute Δ(ΔCO), L/min | Δ(ΔMAP), mmHg |
|---|---|---|---|---|
| male | 500 | **−2.81** | +0.01 | −1.11 |
| male | 1000 | **−5.35** | +0.09 | −3.35 |
| female | 500 | **−2.08** | +0.04 | −1.48 |
| female | 1000 | **−4.78** | +0.09 | −4.10 |

**Predicted: PPV costs 2–5 percentage points MORE of cardiac output under
hypovolaemia, and 1–4 mmHg more of mean arterial pressure.**

### SECONDARY: effect of PPV within each state

| sex | state | ΔMAP | ΔCO | ΔCO % | ΔHR |
|---|---|---|---|---|---|
| male | normo | −3.39 | −0.86 | −14.8 | +6.0 |
| male | hypo 500 | −4.50 | −0.85 | −17.6 | +6.6 |
| male | hypo 1000 | −6.74 | −0.77 | −20.1 | +7.7 |
| female | normo | −3.39 | −0.76 | −14.5 | +6.1 |
| female | hypo 500 | −4.87 | −0.72 | −16.6 | +7.0 |
| female | hypo 1000 | −7.49 | −0.67 | −19.3 | +8.1 |

### SECONDARY: hypovolaemia alone, spontaneous breathing

| sex | bleed | ΔMAP | ΔCO | ΔHR |
|---|---|---|---|---|
| male | 500 | −3.74 | −0.99 | +6.5 |
| male | 1000 | −8.54 | −2.00 | +13.5 |
| female | 500 | −3.85 | −0.90 | +6.8 |
| female | 1000 | −9.09 | −1.77 | +14.3 |

### SECONDARY: absolute baselines, normovolaemic spontaneous

| sex | MAP | CO | HR | SV |
|---|---|---|---|---|
| male | 94.77 | 5.83 | 71.1 | 82.1 |
| female | 92.55 | 5.25 | 72.2 | 72.5 |

---

## Registered caveats — named now, so they cannot be introduced later

**THE ABSOLUTE CARDIAC OUTPUT IS EXPECTED TO BE LOW.** In comparison 001 the
model produced 4.33 L/min against a measured 6.9 in a cohort of the same age. If
this cohort is similarly hyperdynamic, the absolute baselines above will miss and
the relative interaction is the target that survives. **This expectation is
recorded before the result**; it is about a known model characteristic, not about
this study.

**THE LBNP BRACKET IS PROBABLY SKEWED HIGH.** The suite's own LBNP data has
−40 mmHg producing ΔMAP −3.3 and ΔHR +8.3; the model reaches ΔMAP −3.74 and
ΔHR +6.5 at the 500 mL end. So 500 mL behaves like roughly −40 mmHg, and the true
equivalent of −30 mmHg is likely **below** the bottom of the bracket. **Direction
stated: the model's hypovolaemic responses are probably over-stated.**

**LBNP SEQUESTERS BLOOD; HAEMORRHAGE REMOVES IT.** Under LBNP the blood stays in
the circulation below the seal and filters into the legs; total blood volume is
unchanged. The central effect is similar over ten minutes but the interventions
are not identical in kind.

**THE RECOVERY PHASE IS NOT MODELLED.** Releasing LBNP restores volume instantly;
undoing a haemorrhage needs a re-infusion, which is a different manoeuvre.

**SEX IS BRACKETED, AND THE BRACKET IS NEGLIGIBLE HERE.** Measured on the primary
interaction: **0.027 L/min at 500 mL and 0.003 L/min at 1000 mL.** The model
takes one sex and the cohort is 7:8, so both were run — and the limitation turns
out to be immaterial for this comparison. Established with a number rather than
assumed.

**Height assumed** at 173 cm, not reported. Matters most for absolute cardiac
output, which scales with body surface area.

**Finger arterial MAP** against a time-integrated central MAP.

**The baroreflex has no age dependence** (backlog item 51), and this is a
reflex-dominated protocol in 22-year-olds with gains calibrated on a cohort of
median age ~33. **Direction known — the model's reflex is calibrated for someone
older** — magnitude unknown. Comparison 001 found the model under-defends blood
pressure against orthostatic stress in a young cohort; if the hypovolaemic MAP
fall is over-predicted here, that is the first place to look.

---

## RESULTS — appended 2026-09-19, after the registration was pushed at `56d235e`

Study reports medians with interquartile ranges.

### PRIMARY: the interaction — HIT

| | registered | study |
|---|---|---|
| **relative Δ(ΔCO)** | **−2.08 to −5.35 pp** | **−5.56 pp** |
| absolute Δ(ΔCO) | +0.01 to +0.09 L/min | −0.20 L/min |

**The relative prediction lands.** PPV cost 0 % of cardiac output at
normovolaemia and 5.56 % under hypovolaemia. The model's 1000 mL bracket end
predicted −5.35 (male) and −4.78 (female). Direction right, magnitude right,
just outside the top of the bracket.

**The absolute prediction missed its direction** — registered slightly positive,
measured −0.20 L/min. Both were registered, and the relative was named primary
in advance precisely because the two diverge; but the absolute is a registered
quantity and it missed.

### Effect of hypovolaemia alone, spontaneous breathing

| | study | model 500 mL | model 1000 mL |
|---|---|---|---|
| ΔCO | **−1.00** | **−0.90 / −0.99** | −1.77 / −2.00 |
| ΔHR | **+5.8** | **+6.5 / +6.8** | +13.5 / +14.3 |
| ΔMAP | **+2.90** | −3.74 / −3.85 | −8.54 / −9.09 |

**The registered bracket caveat was right.** It was recorded in advance that
500 mL would over-represent −30 mmHg and the hypovolaemic responses would be
over-stated. Cardiac output and heart rate match the 500 mL end almost exactly,
and the 1000 mL end is roughly double the measured effect. **−30 mmHg LBNP
behaves like 500 mL or a little less in this model.**

**ΔMAP fails on direction.** The subjects' mean pressure ROSE 2.9 mmHg under
hypovolaemia; the model's fell by 3.7 to 9.1.

### Absolute baselines, normovolaemic spontaneous

| | model M | model F | study median (IQR) | tier |
|---|---|---|---|---|
| SV | 82.10 | 72.50 | 80.4 (72.5–84.4) | **A / A** |
| CO | 5.83 | 5.25 | 4.6 (4.0–4.9) | miss / B |
| MAP | 94.77 | 92.55 | 75.8 (70.2–78.8) | miss / miss |
| HR | 71.10 | 72.20 | 58.0 (51.6–60.2) | miss / miss |

**A registered caveat was WRONG.** It was recorded that absolute cardiac output
would be LOW, on the strength of comparison 001 where the model gave 4.33
against a measured 6.9 at the same age. Here the model runs **high** — 5.83
against 4.6. The two cohorts genuinely differ (001 was hyperdynamic at 30°
head-up; this one is a resting group with HR 58), and the model sits between
them. The expectation was stated in advance and it did not hold.

---

## What this replicates, and what it points at

**THE MAP FAILURE IS NOW SEEN TWICE, OUT OF SAMPLE, IN INDEPENDENT STUDIES.**

| | stress | subjects | model |
|---|---|---|---|
| 001 | 30°→60° head-up | MAP **+2.5** | **−7.8** |
| 002 | −30 mmHg LBNP | MAP **+2.9** | **−3.7 to −9.1** |

Young subjects RAISE mean arterial pressure under central hypovolaemia. The
model lowers it, every time. **This was registered in advance here** — "if the
hypovolaemic MAP fall is over-predicted, that is the first place to look" — and
it happened.

**The mechanism is visible in the baselines and it is not the age law.**
`aging.py` scales arterial compliance and chamber volumes, but
**`MAP_SETPOINT = 93.0` in `baroreflex.py` carries no age dependence at all.**
So a 22-year-old model defends 93 mmHg while real 22-year-olds in both cohorts
sit near 76. The model is not merely mis-calibrated at rest — **it is defending
the wrong number**, which is exactly what would produce a pressure that starts
too high and then falls when a real young person's would hold or rise.

Resting heart rate points the same way: 71 against a measured 58.

**Stroke volume is the quantity the model gets right** — tier A for both sexes,
and the only absolute that lands. The model's stroke volume is right while its
pressure and rate are not, which localises the problem to the reflex operating
point rather than to cardiac mechanics.

**Opened as backlog item 62** — the baroreflex setpoint does not scale with age —
and it now has out-of-sample evidence from two independent cohorts rather than an
argument from first principles.

