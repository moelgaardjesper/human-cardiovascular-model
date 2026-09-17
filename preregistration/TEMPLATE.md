# NNN — <Author Year>, <one-line description>

- **Registered:** YYYY-MM-DD
- **Model:** `v1.0.0`, artefact commit `90cc1d0`
- **Identifier:** PMID / DOI
- **In-sample check:** `tools/check_insample.py <id>` → NOT FOUND *(paste output)*
- **Verdict:** YES / CONVENTION
- **Status:** REGISTERED — no results seen

---

## The study, as supplied

**Cohort.** n, age, sex, height/weight, health status, medication, posture.
Anything that changes what the model should be set to.

**Protocol.** The intervention, its magnitude, its timing, and what was measured
when. Include the respiratory state and the measurement site — both have caused
false disagreements here before.

**Reported quantities.** *(Names only — no values.)*

---

## The model scenario

Exact and runnable, so a reader can reproduce it without interpreting prose.

```python
# parameters, verbatim
```

**Cohort matching.** Age and body size set to the study's, or a statement of why
not. If the study reports no age, say so — the reference patient is 55 and that
must not pass silently.

**Settling and averaging.** Run length, the window averaged over, and why that
window is long enough.

---

## Quantity convention — pin this before predicting

| study measured | site / phase | model output | convention |
|---|---|---|---|
| e.g. CVP | catheter, end-expiratory | `ra_intraluminal` | INTRALUMINAL, not `cvp` |

**Transmural or intraluminal? Lumen or outer wall? Cycle mean or
end-expiratory? Central or peripheral?** Four apparent defects during
development were this and nothing else.

---

## PREDICTION

One row per quantity. Direction and magnitude, with an interval.

| quantity | predicted direction | predicted magnitude | interval | basis |
|---|---|---|---|---|
| ΔCO | falls | −0.8 L/min | −0.4 to −1.2 | the model's own response, measured at registration |

**Basis** says where the number came from: a scenario actually run at
registration time, an extrapolation from a neighbouring validated case, or a
structural argument. An unrun prediction is weaker and must say so.

**Confidence, stated honestly.** Which of these am I least sure of, and why?

**What would make this fail, and what that would mean.** If the miss would
implicate a specific mechanism, name it now — a diagnosis written in advance is
worth far more than one produced after seeing the answer.

---

## RESULTS — appended in a LATER commit, after the prediction is pushed

*(leave empty at registration)*

| quantity | predicted | interval | reported | hit/miss |
|---|---|---|---|---|

**Verdict:**

**What it means.** For a miss: which mechanism, and does it match the failure
mode named above? For a hit: is it load-bearing, or would a wide interval have
caught anything?
