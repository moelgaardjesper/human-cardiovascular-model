# 007 — Tilt angles recovered from stroke volume, and phenylephrine during head-up tilt

- **Registered:** 2026-09-23
- **Model:** `v1.0.0`, artefact commit `90cc1d0`, unmodified
- **Identifier:** [PMID 31705432](https://pubmed.ncbi.nlm.nih.gov/31705432/) —
  requested after the model was run and before this was pushed.
  `tools/check_insample.py 31705432` -> NOT FOUND in code, docs or registrations.
- **Verdict:** YES, APPROXIMATED
- **Status:** REGISTERED — the phenylephrine results have not been seen

---

## 1. The study

Twenty patients under general anaesthesia. Seventeen are women. Age 67 ± 8,
height 167 ± 8 cm, weight 74 ± 11 kg. Hypertension in 12.

A radial artery catheter feeds a LiDCO monitor. It reports mean pressure, stroke
volume and cardiac output. Anaesthesia is propofol and remifentanil. The lungs
are ventilated at 8 mL/kg of ideal body weight with PEEP 6.

The table is tilted head-up for 3 minutes, then head-down, then flat. Five
minutes later the table is tilted head-up again and the patient is given
phenylephrine. The dose is repeated if stroke volume variation stays at or above
12 per cent.

Each value is the mean of the last 30 seconds before the next step. The paper
reports changes as percentages.

**The paper does not give the tilt angles.** The senior author estimates head-up
10 to 40 degrees and head-down −5 to −40.

---

## 2. The scenario

Runner `007_run.py`, kept local.

| | |
|---|---|
| patient | female, 67 years, 167 cm, 74 kg |
| ventilation | PEEP 6, PIP 21, rate 14, tidal volume 470 mL |
| propofol proxy | 2.5 mg/kg (bracketed 2.0 to 3.0) |
| head-up angle | **17.1°, recovered from the data** |
| phenylephrine | 0.25 to 4 µg/kg/min, bracketed |

**The sex is matched, not bracketed.** The cohort is 85 per cent female.

**The angle is recovered from stroke volume.** Tilt makes blood pool in the leg
veins. This lowers filling, and stroke volume shows it most directly. The model
also handles stroke volume well — it was tier A in registration 002. The method
was fixed before the data arrived: run a grid across the author's bracket, take
the angle that best matches the reported change, and report the whole grid.

**Spent values.** The change in stroke volume on head-up tilt (−27 per cent) and
on head-down tilt (+29 per cent), and the supine stroke volume variation
(11 per cent). The first two set the angles. The third sets the airway pressure.
**None of these is scored.** The response to phenylephrine is not spent.

**Caveats registered now.** The model has no opioid, so its anaesthetised heart
rate rises where these patients are bradycardic. Hypertension in 60 per cent
should make the model's pressor response larger than the cohort's. Six patients
received vasoactive drugs. LiDCO derives stroke volume from the pressure
waveform, and an α1 agonist changes that waveform.

---

## 3. The prediction

### 3a. The head-up angle is 17.1 degrees

| angle | model ΔSV | | angle | model ΔSV |
|---|---|---|---|---|
| 10° | −16.6 % | | 25° | −37.4 % |
| 15° | −24.1 % | | 30° | −43.3 % |
| **17.1°** | **−27 %** | | 35° | −48.6 % |
| 20° | −31.0 % | | 40° | −53.3 % |

The study reports −27 per cent, with a quartile range of −31 to −23. That maps to
**14.3 to 20.0 degrees**.

**This is inside the author's bracket.** It is also inside the model's validated
range of −30 to +45 degrees.

Two parameters were unknown, so both were bracketed. Across propofol 2.0 to 3.0
and PIP 12 to 21, the fitted change stays between −26.74 and −27.29 per cent.
**The angle does not depend on either unknown.**

### 3b. The head-down angle cannot be recovered

| angle | ΔSV from head-up | | angle | ΔSV |
|---|---|---|---|---|
| −5° | **+37.8 %** | | −25° | +49.8 % |
| −10° | +40.5 % | | −30° | +53.5 % |
| −15° | +43.3 % | | −40° | +60.9 % |
| −20° | +46.3 % | | | |

The study reports +29 per cent. **The model is above that at every angle.** The
smallest head-down tilt already gives +37.8. Airway pressure does not explain it:
at −5 degrees the value moves only from +37.2 to +38.4 across the whole bracket.

**So the model moves more blood back on head-down tilt than these patients did.**

### 3c. The phenylephrine response

At 17.1 degrees. Before the drug: MAP 72.3, HR 94.3, SV 37.8, CO 3.55, SVV 14.9.

| dose | ΔMAP | ΔHR | **ΔSV** | ΔCO | SVV | below 12 %? |
|---|---|---|---|---|---|---|
| 0.25 | +16.4 % | −8.6 % | **−4.2 %** | −12.4 % | 15.5 | no |
| 0.50 | +20.5 % | −11.2 % | **−4.5 %** | −14.7 % | 13.8 | no |
| 1.00 | +23.9 % | −13.5 % | **−4.0 %** | −16.9 % | 14.6 | no |
| 2.00 | +26.3 % | −15.3 % | **−3.1 %** | −17.5 % | 14.0 | no |
| 4.00 | +27.8 % | −16.3 % | **−2.2 %** | −18.0 % | 13.9 | no |

**Stroke volume falls by about 4 per cent.** The dose bracket is narrow, so this
is close to a point prediction.

**The drug never abolishes preload-dependency.** Stroke volume variation stays
between 13.8 and 15.5 at every dose. It never reaches the study's target of below
12 per cent. The study titrated until it did.

---

## 4. Analysis

**The angle recovery worked.** Two independent routes agree on 17 degrees, and
the answer holds across both unreported parameters. This is a check on the
model's tilt sensitivity that no other study has given us.

**The head-down failure points at the venous bed.** The model releases pooled
blood too readily when the patient is tilted head-down.

**And the same bed cannot recruit what tilt has trapped.** The model gives −4.2
per cent for preload-dependency made by bleeding (registration 004) and −4.2 per
cent for preload-dependency made by pooling. The two are identical. The legs are
not in the model's mobilizable venous reservoir, so pooled blood is out of reach
of venoconstriction.

That settles backlog item 64 on the model's own evidence. `docs/serendipity.md`
entry 1 set the test before this was run: if the sign does not flip, the model
cannot represent the preload-dependency that occurs under anaesthesia. It does
not flip.

Whether any of this is a MISS depends on what the patients did. That has not been
seen.
