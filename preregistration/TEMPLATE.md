# NNN — <Author Year>, <one-line description>

- **Registered:** YYYY-MM-DD
- **Model:** `v1.0.0`, artefact commit `90cc1d0`
- **Identifier:** PMID / DOI
- **In-sample check:** `tools/check_insample.py <id>` → NOT FOUND *(paste the output)*
- **Verdict:** YES / CONVENTION
- **Status:** REGISTERED — no results seen

---

## The study, as supplied

**Cohort.** n, age, sex, height/weight, health status, medication, posture —
anything that changes what the model must be set to.

**Protocol.** The intervention, its magnitude, its timing, and what was measured
when. Include **respiratory state** and **measurement site**: both have produced
false disagreements in this project before.

**Reported quantities.** *(Names and their comparator type only — no values.)*

| quantity | study reports | comparator for scoring |
|---|---|---|
| e.g. ΔCO | mean ± SD, n=20 | between-subject SD |
| e.g. ΔHR | median (Q1–Q3) | IQR |
| e.g. ΔMAP | point value, no spread | **direction-only** |

---

## The model scenario

Exact and runnable, so a reader reproduces it without interpreting prose.

```python
# parameters, verbatim
```

**Cohort matching.** Age and body size set to the study's — or a statement of
why not. If the study reports no age, say so explicitly: the reference patient
is 55 and that must never pass silently.

**Settling and averaging.** Run length, the averaging window, and why that
window is long enough to be stable.

---

## Quantity convention — pin this BEFORE running

| study measured | site / phase | model output | convention |
|---|---|---|---|
| e.g. CVP | catheter, end-expiratory | `ra_intraluminal` | INTRALUMINAL, not `cvp` |

**Transmural or intraluminal? Lumen or outer wall? Cycle mean or
end-expiratory? Central or peripheral?** Four apparent defects during
development were this and nothing else.

---

## THE MODEL'S OUTPUT — this is the prediction

Run the frozen model at the scenario above, reading the quantities above.
Record what it produces. **This is not an estimate and carries no interval:**
the model is deterministic, so these numbers are what it says.

| quantity | model output | comparator declared |
|---|---|---|
| ΔCO | −0.73 L/min | between-subject SD |

**Command used, and its output pasted verbatim:**

```
$ PYTHONPATH=. python3 ...
```

**What a miss would implicate.** If the model is wrong here, which mechanism is
the likely cause? A diagnosis written in advance is worth far more than one
produced after seeing the answer — and if the eventual miss matches it, that is
a much stronger result than a hit.

---

## RESULTS — appended in a LATER commit, after registration is pushed

*(leave empty at registration)*

| quantity | model | study reported | distance (SD) | distance (SEM) | tier |
|---|---|---|---|---|---|

**Tier summary:** A · B · C · F, and separately the direction-only quantities.

**What it means.** For a miss: which mechanism, and does it match the failure
mode named above? For a hit: is it load-bearing, or would any plausible value
have landed inside a wide spread?
