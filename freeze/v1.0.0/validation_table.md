# Validation table — v1.0.0 (90cc1d0f2955)

Measured fresh at the freeze commit by `tools/validation_table.py --markdown`.

**THIS TABLE IS REPRESENTATIVE, NOT EXHAUSTIVE.** It holds the first literature that went into the model, kept as a readable summary. It is NOT the evidence base and a reader should not count its rows as the validation. **`suite_fast.txt`, `suite_slow.txt` and `suite_overnight.txt` in this directory are the complete record** — every assertion, every cited source, every strict xfail. Carrying every paper and how each was used would make reading the table a project in itself.

Where a source records its cohort's age the row says so and the model is run at that age. Where it does not, the row says that too: an unmatched comparison shown as matched is how a generation gap gets read as a model error.

Rows in the second table are measured by the slow suite and are TRANSCRIBED WITH THEIR DATE, not re-measured by this tool — `suite_slow.txt` is the actual run.

| Scenario | Reference | Literature target | Model now |
|---|---|---|---|
| Supine resting, AGE-MATCHED (reference patient, 55) | McEniery 2005 PMID 16256881, males 50-59, n=429 | MAP 95+/-7, peripheral SBP 125+/-9, peripheral PP 46+/-8, HR 65+/-11 | MAP 95.4, HR 69, CO 5.99, SV 87 |
| Supine resting, size-matched but NOT age-matched | Sejersen 2022 (10 healthy males 177/80, age not reported); Lie 2023 for CO | MAP 83+/-8, HR 62+/-8 bpm; CO 7+/-2 (Sejersen) vs 4.85+/-1.08 (Lie) | MAP 95.7, HR 69, CO 6.11, SV 89 |
| 20 deg head-down tilt, normovolaemic | Sejersen 2022 | dSV ~0 (n.s.), dCO ~0, dMAP +2 mmHg (n.s.) | dMAP +0.7, dCO +0.23, dSV +5.9 |
| -30 deg Trendelenburg vs supine (mid-range of the pooled protocol) | Likhvantsev 2025 meta-analysis, n=333, 16 studies spanning -5 to -45 deg | dCVP +4.13 (CI 2.42-5.84), dCO +0.33, dSV +8.27, dHR -1.65 | dCVP +4.65, dCO +0.48, dSV +10.1, dHR -2.6 |
| 30 deg head-up tilt | Wieling 1998 (at 90 deg: SV -39+/-9%, CO -26+/-10%, MAP +1+/-7) | SV and CO fall, MAP partially defended (no muscle pump in model) | dSV -35%, dCO -25%, dMAP -6.2 |
| Graded HUT 0/20/30 deg monotonicity | Sarafian 2017, graded tilt 0-60 deg | HR rises and CO falls monotonically with angle | CO 6.05/4.95/4.56, HR 69/76/80 |
| Microgravity CVP vs upright Earth | Buckey 1996 | CVP in orbit ~2.5 mmHg, still ABOVE upright standing on Earth | CVP micro-g 4.40 vs upright 45 deg 2.48 |
| Cerebral perfusion pressure, upright | Pohl & Cullen 2005 (beach chair; CPP risk < 50 mmHg) | CPP falls substantially head-up; risk threshold 50 mmHg | CPP supine 86 -> 45 deg 67 |
| Norepinephrine vs phenylephrine, CO preservation | Ngan Kee 2015, n=104 | NE CO 102.7% vs phenylephrine 93.8% (p=0.004); NE HR higher | NE CO 5.84 / HR 64; PE CO 5.68 / HR 60 |
| Vasopressin dose-response | Patel 2002, n=13 septic shock | MAP rises monotonically with dose; CO maintained | MAP 95.5/103.8/105.7, CO 6.05/5.89/5.93 |
| Epinephrine dose-response | Freyschuss 1986, n=11 | CO rises monotonically with dose; MAP_high > MAP_low (alpha dominance) | low CO 6.53 MAP 97.7; high CO 6.85 MAP 107.8 |
| Phenylephrine flow response, AGE-MATCHED (27) | Schaefers 1999 PMID 10073742, 12 healthy supine men, median age 27 | dCO -1.15 (-1.25 to -0.40), dHR -16 (-19.5 to -14.2), dSV +9 (-0.5 to +18.5) | at 4 mcg/kg/min: dCO -0.73, dHR -15.2, dSV +9.9 |
| Norepinephrine postcapillary constriction | Abboud & Eckstein 1968 II (venous dose-response 1.80x steeper) | venous/arterial slope ratio 1.80 over a dose doubling | ratio 1.84 |

Slow-dynamics rows — measured by `pytest -m slow`, transcribed with the date they were measured:

| Scenario | Reference | Literature target | Model now |
|---|---|---|---|
| Transcapillary refill after haemorrhage | Lister 1963, 550 mL over 15 min, human | refill incomplete at 2 h; 50-80% by 24 h | PASSES. Correctly incomplete at 2 h; model refills ~1.6x fast on cumulative volume  [2026-08-22] |
| Norepinephrine plasma-volume cost | Lister 1963 Fig 5, unbled healthy men | plasma volume falls 15-19% | PASSES at 16.07%. Was a strict xfail at 0.13% until 2026-08-22; closed by two structural fixes (backlog 20 then 18), no parameter fitted to this endpoint |
| Norepinephrine recovery timescale | Lister 1963 Fig 5 | recovery over ~1 h; not near-complete within minutes | PASSES both bounds. Model still recovers ~4x faster than Lister overall — deliberately not asserted  [2026-08-22] |
| Venous stress relaxation + filtration, CVP dissipation | Guyton (~82% of an acute CVP rise dissipated) | ~82% | PASSES. 79.8% combined (creep alone 27.4%)  [2026-08-22] |
| RAAS/ADH pressure defence after 1000 mL bleed | Bussien 1984 (human), Hasser & Bishop 1988, Rascher 1985 | no effect at rest; pressor reserve unmasked when reflexes overwhelmed | PASSES. +3.50 mmHg MAP, CO slightly DOWN (vasoconstrictor signature), blood volume unchanged  [2026-08-22] |
| Autonomic modulation of refill time constant | Shigemi (dog): autonomic blockade doubles recovery tau, 39 -> 74 min | ratio ~1.9 | NOT REPRODUCED, open. 9.31 -> 9.11 min, ratio 0.98. No test asserts it; candidate for a baroreflex arm on the postcapillary split  [2026-08-10] |

