# 006 — 30 minutes of 60° head-up tilt, young versus older volunteers

- **Registered:** 2026-09-22
- **Model:** `v1.0.0`, artefact commit `90cc1d0`, unmodified
- **Identifier:** [PMID 9404222](https://pubmed.ncbi.nlm.nih.gov/9404222/).
  `tools/check_insample.py 9404222` → NOT FOUND in code, docs or registrations.
- **Verdict:** YES, APPROXIMATED
- **Status:** REGISTERED — study results not seen

---

## Why this registration exists, and it is not the usual reason

**Three of the four things registered here are predictions that the model will
FAIL.** Each names the mechanism responsible, and each is expected to fail in a
stated direction.

That is deliberate. This project claims two architectural limitations — pulse
pressure amplification is inverted, and the model collapses beyond 45° of
head-up tilt. Both currently rest on our own assertion plus one in-house
measurement. **A pre-registered prediction of our own failure, confirmed against
a cohort we have never seen, is much stronger evidence than either.**

This study was first declined on the grounds that the model was expected to
fail. That was the wrong call and it was reversed the same day; see the design
history in `README.md`.

---

## Declared spent values

**Nothing is spent.** No reported haemodynamic value was used to configure the
patients. The model is built from age, sex and anthropometrics only.

---

## The study, as supplied

Sixteen young volunteers, **21–30 years (25 ± 3, mean ± s.e.m.)**, and sixteen
older, **60–83 years (68 ± 7)**. **Eight male and eight female in each group.**
All sedentary or in light training — no more than 20–30 min of low-intensity
exercise twice weekly. All within 20 % of ideal body weight. No cardiovascular
symptoms and no history of syncope.

Light standardised breakfast; no caffeine or alcohol for 12 h. Intravenous line
in the right antecubital vein for sampling. **Automated arm cuff (Dinamap,
Critikon) on the left arm for blood pressure and heart rate.** Thirty minutes
supine in a darkened quiet room, then the table was **rapidly inclined to 60°**
with the feet on a base platform and held for **30 minutes**, then returned
horizontal for 30 minutes.

Haemodynamics every 5 min. Blood for neurohormones at baseline and at 5, 10, 15
and 30 min. Heart rate variability in 5 min segments. Height and weight are not
reported.

**Only the protocol and cohort were supplied. No results were seen.**

---

## What is scored

**Heart rate and brachial pressures. Comparator: 1 SD for tier A, 2 SD for tier
B.** The paper reports mean ± s.e.m. with n = 16 per group, so SD = s.e.m. × 4.

**Sex is bracketed, not assumed.** The cohort is exactly 8 male and 8 female per
group, so the headline figure is the mean of the two model runs and the bracket
width is reported beside it.

### PRIMARY — the heart rate response to tilt

Supine to 5 minutes of tilt, within each age group. Clean: a cuff measures heart
rate reliably and the model computes it directly, with no convention problem.

### PREDICTED FAILURE 1 — the age difference in that response is zero

**The model gives +23.4 bpm in the young and +23.5 in the older.** A difference
of **0.1 bpm** across a 43-year age gap.

Orthostatic tachycardia is blunted in older people. This is well established.
**The model cannot produce that, because `BaroreflexController` takes no age
argument of any kind** — age reaches only arterial compliance and chamber
volumes (backlog item 51). **This should fail, and a failure is direct
out-of-sample evidence for item 51, which currently rests only on a reading of
the code.**

### PREDICTED FAILURE 2 — mean pressure collapses at 60°

**The model's brachial mean pressure falls about 31 mmHg on tilting, to 56.** A
mean pressure of 56 is near-syncopal. These subjects held the position for
thirty minutes and none had a syncope history.

The mechanism is documented: beyond 45° the hydrostatic penalty exceeds
transmural venous pressure, leg venous return collapses, and the baroreflex
cannot compensate. The validated range is −30° to +45°.

**Declared: we have seen the model at 60° before**, in comparison 001 (MAP 80.7
against a measured 98.5). Blind with respect to this study, not blind to the
model.

### PREDICTED FAILURE 3 — the pulse pressure is about half

**Model brachial pulse pressure supine: 22.7 young, 34.4 older.** Adult brachial
values are nearer 45 and 60.

Pulse pressure amplification in the model is **inverted** — 0.88 against a
measured 1.33 ± 0.16 — and it cannot be repaired in a lumped model, which has no
wave travel or reflection. **Note the age direction is right:** the older pulse
pressure is wider, by 11.7 mmHg. The age law works; the absolute width does not.

### EXPLORATORY — the drift from 5 to 30 minutes

**The model barely moves: heart rate −0.4 bpm, mean pressure +1.0, cardiac
output −0.1 L/min over 25 minutes.**

This was the reason to want the study. Every tilt test in the suite runs for 40
seconds; this is the first protocol that could load venous stress relaxation
(τ = 250 s) and transcapillary refill. **Registration 005 tried it at 10° and saw
nothing. This is the second attempt, at the opposite end of the range, and the
model is flat again.**

**Labelled exploratory because attribution is weak.** The starting state is
already wrong — see failure 2 — so a miss here cannot be cleanly assigned to the
slow mechanisms rather than to the 60° collapse.

### Not scored

Neurohormones have no counterpart: the model carries hormone ACTIVATIONS on a
0–1 scale, not concentrations. Heart rate variability needs an autonomic
spectrum the model does not have.

---

## The model scenario

Runner `006_run.py`, kept local per `CLAUDE.md`.

**Patients:** ages 25.0 and 68.0, built through `build_patient_params` from age
and sex only. No measured haemodynamics supplied, so the Tier 3 calibration path
is not invoked and backlog item 58 does not bite.

**Anthropometrics.** Height is not reported and is assumed at 175 cm (male) and
162 cm (female). **Weight follows from Devine ideal body weight** — 70.5 and
54.2 kg — which the paper supports directly: all subjects were within 20 % of
ideal body weight. That is an estimate with a stated basis rather than a guess.

**Height is deliberately NOT bracketed.** Registration 005 measured a 172–182 cm
bracket and it moved the primary by 0.03 mmHg. Backlog item 66 explains why:
patient height reaches this model only through body surface area and never
scales the hydrostatic column. Re-running it would measure a known null.

**Ventilation:** spontaneous, 14 breaths/min. Nothing is paced.
**Slow dynamics:** ON, at the `v1.0.0` default.

**Timeline**, with apply times and measure windows as separate quantities:

| phase | t (s) |
|---|---|
| settle, discarded | 0 → 120 |
| supine baseline | 120 → 300 |
| tilt ramp to 60° | 300 → 310 |
| head-up tilt | 310 → 2110 |

Readings are 30 s windows ending at each time point. The baseline window ends at
tilt onset; every tilt window begins after the ramp completes.

**Arm cuff, so the BRACHIAL output is read.** Mean pressure is reconstructed as
(S+2D)/3 from `brachial_sbp` and `brachial_dbp` — the same formula on the same
site. Registration 005 compared the model's AORTIC pressure against a finger
measurement and the resulting 11 mmHg gap turned out to be mostly the site.

---

## Registered caveats

**The identifier was supplied before the model was run**, because the study was
initially going to be excluded. It was not looked up; the in-sample check was run
on it and returned NOT FOUND.

**Sex is bracketed but the cohort is mixed within each measurement.** The model
runs one sex at a time; the study averages eight of each. The bracket widths are
reported so a reader can see the size of that approximation.

**Age 68 is outside the range the age law was validated at.** `aging.py` is
validated against McEniery at 25, 55 and 75, so 68 is an interpolation between
validated points rather than an extrapolation.

**The older group spans 60–83 years.** A single model age of 68 stands for a
23-year spread.

---

## THE MODEL'S OUTPUT — the prediction

Mean of the male and female runs, with the sex bracket beside it.

### Supine baseline

| | young (25) | older (68) | sex bracket |
|---|---|---|---|
| heart rate | **71.7** | **70.2** | 1.5–1.9 bpm |
| brachial MAP | **88.7** | **86.9** | 2.5–2.7 mmHg |
| brachial SBP/DBP | 103.7 / 81.1 | 109.8 / 75.5 | |
| **brachial pulse pressure** | **22.7** | **34.4** | 0.1–0.5 mmHg |
| cardiac output | 5.51 | 5.41 | 0.74–0.77 L/min |

### Response to tilt, supine → 5 minutes

| | young | older | **age difference** |
|---|---|---|---|
| **Δ heart rate** | **+23.4** | **+23.5** | **+0.1 bpm** |
| Δ brachial MAP | −32.2 | −30.4 | +1.8 mmHg |
| Δ cardiac output | −2.45 | −2.58 | −0.13 L/min |

### At 60°, 5 minutes

| | young | older |
|---|---|---|
| heart rate | 95.1 | 93.7 |
| brachial MAP | 56.5 | 56.5 |
| brachial pulse pressure | 9.5 | 15.1 |
| cardiac output | 2.78 | 2.83 |

### Drift, 5 → 30 minutes of tilt

| | young | older |
|---|---|---|
| Δ heart rate | −0.45 | −0.35 bpm |
| Δ brachial MAP | +1.00 | +0.90 mmHg |
| Δ cardiac output | −0.11 | −0.09 L/min |
