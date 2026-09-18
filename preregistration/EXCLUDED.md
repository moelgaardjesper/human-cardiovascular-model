# Excluded studies — and the mechanical reason

Studies supplied for the blind phase that the model cannot be asked, or that
are not out-of-sample.

**EVERY STUDY SCREENED IS LOGGED HERE, whatever the verdict.** Not to demonstrate
a comprehensive literature search — two entries would be poor evidence for that,
and no systematic search was performed. Studies were supplied opportunistically
and screened against the criteria in `README.md`.

The reason is narrower and stronger: **a partial exclusion log is worse than
none.** The first question anyone asks of a pre-registration is what was left
out, and the only answer that survives scrutiny is a log that is complete by
policy rather than by inclination.

**This list is a result.** It maps the architecture's boundary using real
published protocols rather than the authors' own account of the model's limits,
which a reader has more reason to trust. A model that could attempt everything
would be one whose limits nobody had tested.

| # | study | identifier | reason | category |
|---|---|---|---|---|
| 1 | Knee arthroscopy, Trendelenburg vs PLR before tourniquet release | [10.21608/ijma.2021.62396.1262](https://doi.org/10.21608/ijma.2021.62396.1262) | Three absent mechanisms — see below | NO MECHANISM *(temporary)* |
| 2 | Parabolic flight, seated and supine, with thigh-cuff venous occlusion | *(supplied 2026-09-18)* | Gravity acts only through the tilt term; seated posture, cuffs and transients all unrepresentable | NO MECHANISM |

---

## 1 — Trendelenburg vs passive leg raise, before tourniquet release

**Screened 2026-09-18.** Int J Med Arts 2021. n = 49 + 49, unilateral knee
arthroscopy under spinal plus general anaesthesia, proximal thigh tourniquet.
Group 1 placed head-down 20°, group 2 given bilateral passive leg raise to 45°.
MAP by cuff at baseline — post-spinal, already tilted, tourniquet still inflated
— then at 1, 2, 3, 4, 5 and 10 minutes after release. Mean ± SD.

**Only methods, cohort and timing were supplied. No results were seen.**

### Why the model cannot be asked this

**The two arms are the same manoeuvre to this model.** Passive leg raise is
implemented *as* head-down tilt, and tilt is global — one angle applied to every
compartment through its fixed height. The legs cannot move relative to the trunk,
so the comparison the study exists to make is the one thing the architecture
cannot express.

**The tourniquet is unilateral and the model has no laterality.** The leg
compartments represent both legs at once. In group 2 that matters directly: one
leg is excluded from the circulation while both are raised, so the manoeuvre
mobilises one leg's volume rather than two.

**Every measurement is after release, and release has no mechanism.** Nothing in
the model accumulates ischaemic metabolites, so there is no vasodilator load to
wash out and no reactive hyperaemia. Compartment resistance is also fixed at
setup, so even the release *event* cannot be staged, let alone the ten minutes of
physiology that follow it.

### Status, and two honest notes

**Temporarily excluded, not permanently.** The blockers are missing mechanisms,
not a mismatch of kind. If per-segment posture and a tourniquet model are ever
built, this becomes answerable — and it stays a clean out-of-sample target,
because only methods and timing were ever read. Six post-release time points is
unusually well sampled.

**Quality caveat, recorded rather than left to be discovered.** Not indexed in
PubMed, and judged probably low quality by the clinician who supplied it. That
matters for a validation target: if a source is unreliable, a disagreement does
not cleanly implicate the model. Better used as a shape target — how fast, how
deep, how long to recover — than a magnitude one.


## 2 — Parabolic flight, seated and supine, with thigh-cuff venous occlusion

**Screened 2026-09-18.** Healthy volunteers, age 35. Thirty parabolic
manoeuvres: the first twenty seated, the last ten supine. MAP (Portapres) and HR
continuous; CO by rebreathing over 20-second windows at either 1 G or 0 G.
Seated conditions randomised across 1 G, 0 G, 0 G with bilateral thigh cuffs
inflated to 60 mmHg from before the 1.8 G pull-up, and 0 G with the cuffs
released on entering 0 G.

**Only methods, cohort and timing were supplied. No results were seen.**

### Why the model cannot be asked this

**Gravity reaches the model only through the tilt term**, as
`rho * g * h * sin(tilt)` in `model/gravity.py`. At tilt zero the sine is zero,
so the term vanishes whatever the gravity is. **This is readable from the code
and needs no simulation to establish.**

So the supine arm, which looked like the salvageable half, is the clearest
failure. **The model answers "no change" by construction**, and a prediction of
identically zero is arithmetic rather than physiology.

**The seated arm is unrepresentable for two separate reasons** — it is beyond the
validated posture range of −30° to +45°, and a seated posture needs hip
articulation the model does not have, since one tilt angle is applied to every
compartment through a fixed height.

**Thigh-cuff venous occlusion is not a model parameter.** The cuffs are
bilateral, so limb laterality is not the obstacle here; occlusion simply does not
exist as a mechanism. This is also why the live-mode UI has no cuff control —
there is nothing in the model for it to expose.

**Every measurement is a transient.** Twenty-second 0 G windows, a 1.8 G pull-up,
and cuff release timed to 0 G entry. Live mode can step gravity mid-run but only
between four named environments, so 1.8 G is unreachable, and it cannot vary
regional resistance at all.

**Convention flag, recorded although it is not the blocker:** Portapres measures
finger arterial pressure; the model reports a time-integrated central MAP.

### What was learned by screening it

**Every microgravity result in the suite is really a supine result.** The finding
generalises well beyond this study: at tilt zero, `GravityEnvironment.MICROGRAVITY`
and Earth gravity enter the equations identically, so the Buckey 1996 row in the
validation table compares supine CVP against upright CVP under a different name.
The README already carried the symptom — "CVP paradox in microgravity not fully
reproduced" — but attributed it to unmodelled chest-wall compliance. **That is
incomplete: fixing chest-wall compliance would not help, because the
gravitational term is gone before any of it applies.** Opened as backlog item 57.

This is the second time a screen has found that a named scenario is a synonym for
another one. The first was passive leg raise, which is implemented as head-down
tilt.

## Categories

- **IN-SAMPLE** — already cited in `model/` or `tests/`; was available during
  development, so it cannot test anything. Detected by
  `tools/check_insample.py`, not by memory. *(Likhvantsev 2025 is the known
  example: used from the beginning, so unavailable for this phase.)*
- **NO MECHANISM** — the model lacks the structure the protocol requires. Name
  it: no cellular compartment, no 1-D wave propagation, no skeletal-muscle
  pump, no age-dependent baroreflex, no pregnancy or sepsis physiology, no
  postural articulation, no limb laterality.
  **Mark it *(temporary)* if building the mechanism would make the study
  answerable.** "We cannot ask this yet" and "this can never test us" are
  different statements about the model, and a reader should be able to tell
  them apart.
- **OUT OF VALIDATED RANGE** — mechanically runnable but outside the envelope
  where outputs mean anything, e.g. posture beyond −30°/+45°.
- **NO COMPARABLE OUTPUT** — the model runs the protocol but reports nothing
  that corresponds to what was measured, and no convention mapping exists.
  Distinct from CONVENTION, where a mapping exists but differs.
- **NO SPREAD REPORTED** — *not* an exclusion. The study is registered, but
  quantities with no reported spread can only reach tier C or F, and are counted
  separately from the tiered ones. Listed here only when a study reports no
  spread for *any* quantity, which makes the whole comparison direction-only.
- **RESULT SEEN** — the result reached the model author before registration.
  Excluded regardless of everything else, and recorded rather than hidden.
