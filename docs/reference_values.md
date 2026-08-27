# Reference values from papers read in full

**Purpose (Jesper, 2026-08-24): record EVERY number from a source we have actually
read, not only the ones the model currently uses.** Numbers that look irrelevant today
have repeatedly turned out to matter later — Gao's atrial data was fetched for item 23
and immediately answered item 24's ordering question; Heldt Table 3 was fetched for the
pulmonary bed and settled the systemic comparison. Re-fetching a paper costs far more
than writing the table down once.

RULE: only numbers from a source READ IN FULL (or from an abstract that states them
directly, marked as such). Never transcribe from recollection. If a value is used in
the model, say where.

---

## Luu JM et al. 2022 — CMR ventricular + LA reference values
J Cardiovasc Magn Reson 24(1):2. PMID 34980185, PMC8722350, DOI 10.1186/s12968-021-00819-z
n=3206 (1126 M, 2080 F), age 55.1±8.8 M / 55.2±8.4 F, 35-75 y. Multi-ethnic (77% white
Caucasian, ~17% Chinese, ~4% South Asian). Excluded CVD AND hypertension, diabetes,
obesity (BMI>30), smoking, dyslipidaemia — 64% of consented participants screened out.
Anatomically correct contouring: papillary muscle + trabeculae counted as MASS.

Indexed to BSA, mean ± SD:
| | male | female |
|---|---|---|
| LVSV | 46 ± 8 mL/m2 | 42 ± 7 |
| LVEDV | 74 ± 13 | 65 ± 11 |
| LVESV | 28 ± 7 | 23 ± 6 |
| LV mass | 61 ± 10 g/m2 | 48 ± 8 |
| LVEF | 62 ± 6 % | 64 ± 6 |
| RVSV | 45 ± 8 mL/m2 | 42 ± 7 |
| RVEDV | 86 ± 16 | 72 ± 13 |
| RVESV | 41 ± 11 | 31 ± 8 |
| RVEF | 53 ± 6 % | 58 ± 6 |

USED: ventricular rebuild (backlog 24). NOT YET USED: LV mass (the model has no wall
mass at all), female values, the age-stratified and per-ethnicity tables (backlog 25).
Trends: indexed LVEDV/LVESV/RVEDV/RVESV and LV mass all FALL with age in both sexes;
LVEF and RVEF RISE with age in females; RVEF rises with age in males, LVEF does not.
CAVEAT: Luu contrasts with UK Biobank (Petersen), which uses simplified contouring and
reports LVEDV ~9 mL/m2 LARGER — e.g. female LVEDV 74 ± 12 (Petersen) vs 65 ± 11 (Luu).
Treat 65-74 mL/m2 as the methodological spread, not a disagreement to resolve.
NO RIGHT ATRIAL DATA — the authors say so explicitly and promised a separate paper.

## Gao Y et al. 2022 — CMR biatrial reference values
Int J Cardiol 352:180-187. PMID 35124105, DOI 10.1016/j.ijcard.2022.01.071
n=408 healthy Chinese adults (220 M), age 44.4±12.1, BSA 1.72±0.18, BMI 23.3±2.7,
HR 65.6±8.8, SBP 114.9±13.5, DBP 70.8±9.8. Table 2, all subjects, mean ± SD:

| | absolute mL | indexed mL/m2 |
|---|---|---|
| LAVmax | 63.3 ± 14.2 | 36.9 ± 7.7 |
| LAVmin | 24.8 ± 7.7 | 14.4 ± 4.1 |
| LAVpac | 40.7 ± 11.1 | 23.7 ± 6.2 |
| RAVmax | 58.4 ± 17.1 | 33.9 ± 8.9 |
| RAVmin | 29.6 ± 10.8 | 17.1 ± 5.6 |
| RAVpac | 44.8 ± 14.7 | 26.0 ± 7.7 |

Phasic function: LAEF total 61.1±6.2 %, LATEV 38.5±8.6 mL, LAEF passive 35.9±8.3 %,
LAPEV 22.6±6.8 mL, LAEF booster 39.1±8.0 %, LAAEV 15.9±5.3 mL. RAEF total 49.7±9.2 %,
RATEV 28.8±9.3 mL, RAEF passive 23.6±9.4 %, RAPEV 13.6±6.2 mL, RAEF booster 34.0±10.0 %,
RAAEV 15.2±6.8 mL.
USED: atrial rebuild (backlog 23). NOT YET USED: Vpac, and the whole passive/booster
decomposition — the model has no separate conduit vs booster phases, but this is exactly
what a diastolic-dysfunction model would need. Age trends (Table 3, by decade 21-70):
LAVpac and RAVpac rise with age in both sexes; LAVmax/LAVmin/RAVmax/RAVmin rise with age
only in WOMEN; LAEF total, LAEF passive, RAEF total, RAEF passive all FALL with age while
LAEF BOOSTER RISES — the atrium compensating for stiffer ventricular filling, i.e. HFpEF
physiology (backlog 25).

---
---
---
## SEX SPLIT — the female/male ratios, indexed to BSA (backlog item 32)
Assembled 2026-08-27 from Luu 2022 Table 2 (PMID 34980185, n=3206) and Gao 2022 Table 2
(PMID 35124105, n=408). **These are ratios of values ALREADY INDEXED TO BSA**, so they are
what remains after body size is accounted for — the sex difference survives indexing, which
is the entire reason a sex input is needed at all.

| quantity | male | female | female/male |
|---|---|---|---|
| LVEDV mL/m2 | 74 ± 13 | 65 ± 11 | 0.878 |
| LVESV mL/m2 | 28 ± 7 | 23 ± 6 | 0.821 |
| LVSV mL/m2 | 46 ± 8 | 42 ± 7 | 0.913 |
| LVEF % | 62 ± 6 | 64 ± 6 | 1.032 |
| RVEDV mL/m2 | 86 ± 16 | 72 ± 13 | 0.837 |
| RVESV mL/m2 | 41 ± 11 | 31 ± 8 | 0.756 |
| RVSV mL/m2 | 45 ± 8 | 42 ± 7 | 0.933 |
| RVEF % | 53 ± 6 | 58 ± 6 | 1.094 |
| LV mass g/m2 | 61 ± 10 | 48 ± 8 | 0.787 |
| **LAVmax/BSA mL/m2** | 35.7 ± 7.5 | **38.4 ± 7.7** | **1.076** |
| LAVmin/BSA mL/m2 | 14.3 ± 3.8 | 14.5 ± 4.4 | 1.014 (p = 0.618, NS) |
| LAVpac/BSA mL/m2 | 23.0 ± 5.8 | 24.6 ± 6.6 | 1.070 |
| LAEF total % | 60.0 ± 6.2 | 62.5 ± 5.9 | 1.042 |
| LAEF passive % | 35.6 ± 8.4 | 36.3 ± 8.2 | 1.020 (p = 0.404, NS) |
| LAEF booster % | 37.6 ± 7.9 | 40.9 ± 7.6 | 1.088 |
| RAVmax/BSA mL/m2 | 34.9 ± 9.3 | 32.7 ± 8.2 | 0.937 |
| RAVmin/BSA mL/m2 | 18.5 ± 6.0 | 15.5 ± 4.6 | 0.838 |
| RAVpac/BSA mL/m2 | 27.3 ± 8.0 | 24.5 ± 6.9 | 0.897 |
| RAEF total % | 47.2 ± 8.4 | 52.6 ± 9.3 | 1.114 |
| RAEF passive % | 21.9 ± 8.4 | 25.6 ± 10.2 | 1.169 |
| RAEF booster % | 32.3 ± 9.1 | 36.0 ± 10.6 | 1.115 |
Gao's absolute (non-indexed) atrial volumes are all LARGER in men — LAVmax 65.2 vs 61.0 mL,
RAVmax 63.7 vs 52.2 — because men are bigger. Indexing reverses the LA and shrinks the RA
difference. Gao states this explicitly: after BSA normalisation LAVmax and LAVpac are
GREATER IN WOMEN while the RA measures stay greater in men.

**THE LEFT ATRIUM IS THE ONE THAT RUNS THE OTHER WAY.** Indexed to BSA the female LA is
LARGER (1.076) while LV, RV and RA are all smaller. Every ejection fraction is higher in
women. A single "female chambers are smaller" factor would be wrong, and wrong on the
chamber that is the wedge-pressure surrogate.

USED: `SEX_CHAMBER_FACTORS` in model/patient.py — LV, RV and RA volume factors, and all four
E_max factors. NOT USED and recorded as a gap: the LA volume factor. The model cannot apply
it — measured transmission of an assigned LA volume factor is NEGATIVE, because the
pulmonary veins, LA and LV are nearly continuous and LA volume is a share of one pooled
volume (items 23, 25a). NOT USED: LV mass (no wall mass in the model), and the passive /
booster split (no conduit and booster phases — item 25a).

## Luu 2022 TABLES 3 & 4 — the age- AND sex-stratified ventricular values (item 25)
J Cardiovasc Magn Reson 24(1):2. PMID 34980185, PMC8722350, DOI 10.1186/s12968-021-00819-z
**TABLES 3 AND 4 READ IN FULL 2026-08-27.** Same cohort as the Table 2 entry above (n=3206,
CVD and risk factors excluded, anatomically correct contouring with papillary muscle and
trabeculae counted as mass). PMC full text strips these tables — they are only in the PDF.
Mean +/- SD, indexed to BSA. Normal ranges (95 % prediction intervals) are in the source.

**MALES (n=1126)** — 35-44 (n=141) / 45-54 (n=408) / 55-64 (n=383) / 65-74 (n=194)
| variable | 35-44 | 45-54 | 55-64 | 65-74 |
|---|---|---|---|---|
| LVEF % | 61 ± 6 | 62 ± 6 | 62 ± 6 | 62 ± 6 |
| LVSV mL/m2 | 47 ± 8 | 46 ± 8 | 46 ± 8 | 43 ± 8 |
| LVEDV mL/m2 | 77 ± 13 | 75 ± 13 | 74 ± 13 | 69 ± 13 |
| LVESV mL/m2 | 30 ± 8 | 29 ± 7 | 28 ± 7 | 26 ± 7 |
| LV mass g/m2 | 61 ± 11 | 61 ± 10 | 62 ± 10 | 58 ± 9 |
| LV mass/volume g/mL | 0.81 ± 0.13 | 0.83 ± 0.15 | 0.85 ± 0.15 | 0.86 ± 0.20 |
| RVEF % | 51 ± 6 | 53 ± 6 | 53 ± 6 | 54 ± 6 |
| RVSV mL/m2 | 46 ± 9 | 46 ± 8 | 46 ± 8 | 43 ± 8 |
| RVEDV mL/m2 | 91 ± 18 | 88 ± 16 | 86 ± 17 | 80 ± 15 |
| RVESV mL/m2 | 45 ± 12 | 42 ± 10 | 41 ± 11 | 37 ± 10 |
| LA min mL/m2 | 19 ± 6 | 20 ± 6 | 22 ± 8 | 21 ± 8 |
| LA max mL/m2 | 36 ± 9 | 38 ± 10 | 40 ± 10 | 38 ± 11 |

**FEMALES (n=2080)** — 35-44 (n=228) / 45-54 (n=744) / 55-64 (n=795) / 65-74 (n=313)
| variable | 35-44 | 45-54 | 55-64 | 65-74 |
|---|---|---|---|---|
| LVEF % | 64 ± 5 | 64 ± 5 | 64 ± 6 | 65 ± 6 |
| LVSV mL/m2 | 45 ± 7 | 43 ± 7 | 41 ± 7 | 40 ± 6 |
| LVEDV mL/m2 | 70 ± 11 | 67 ± 10 | 64 ± 10 | 62 ± 9 |
| LVESV mL/m2 | 25 ± 6 | 24 ± 6 | 23 ± 6 | 21 ± 5 |
| LV mass g/m2 | 48 ± 7 | 47 ± 8 | 48 ± 7 | 46 ± 8 |
| LV mass/volume g/mL | 0.69 ± 0.11 | 0.72 ± 0.12 | 0.76 ± 0.14 | 0.76 ± 0.14 |
| RVEF % | 56 ± 6 | 58 ± 6 | 58 ± 7 | 59 ± 6 |
| RVSV mL/m2 | 44 ± 7 | 43 ± 7 | 41 ± 7 | 39 ± 6 |
| RVEDV mL/m2 | 79 ± 13 | 74 ± 13 | 71 ± 13 | 67 ± 11 |
| RVESV mL/m2 | 35 ± 8 | 32 ± 8 | 30 ± 8 | 28 ± 7 |
| LA min mL/m2 | 17 ± 5 | 18 ± 6 | 19 ± 6 | 21 ± 7 |
| LA max mL/m2 | 34 ± 8 | 37 ± 9 | 37 ± 9 | 38 ± 9 |

**TWO LABELLING ERRORS IN THE PUBLISHED TABLES. Read this before transcribing them again.**
1. Table 4 lists **two rows both labelled "RVESV"**. The first (44/43/41/39) is RVSV: it
   tracks female LVSV (45/43/41/40) almost exactly, as a stroke volume must, and mirrors the
   male RVSV row. The second (35/32/30/28) is the real RVESV. Corrected above.
2. The columns printed as **"LA SV"** and **"LA EF (%)"** do not mean what they say.
   "LA SV" (46-47 mL/m2 in men) equals LVSV, i.e. it is the VENTRICULAR stroke volume.
   "LA EF (%)" is numerically identical to (LA max - LA min): 36 - 19 = 17 for men 35-44,
   and the cell reads 17. So it is an LA stroke VOLUME in mL/m2, printed as a percentage.
   **Do not use Luu's "LA EF" as an ejection fraction.** A genuine LAEF from their own max
   and min is 17/36 = 47 %, which is the right order against Gao's LAEF total of ~60 %
   (different cohort, different method). Both columns are therefore omitted above.

**THE AGE AND SEX TRENDS, which is what item 25 needs.**
- Every indexed VOLUME falls with age in both sexes: LVEDV 77 -> 69 (men) and 70 -> 62
  (women); RVEDV 91 -> 80 and 79 -> 67. Stroke volumes fall with them.
- EJECTION FRACTIONS rise or hold: LVEF flat in men (61-62, p = 0.1985 in the paper) but
  rising in women (64 -> 65); RVEF rises in both (51 -> 54 men, 56 -> 59 women).
- MASS-TO-VOLUME RATIO rises with age in both (0.81 -> 0.86 men, 0.69 -> 0.76 women) —
  concentric remodelling, the chamber getting smaller faster than the wall thins.
- SEX is a larger effect than age for most of these. Male LVEDV exceeds female by ~10 mL/m2
  at every decade, and female LVEF exceeds male by 2-3 points at every decade. A model with
  one reference patient cannot represent either axis.
USED: nothing yet — items 25a/25b and the new sex item. NOT USED: LV mass (the model has no
wall mass), the per-ethnicity tables (S4-S6), and values indexed to height.

## Gao 2022 TABLE 3 — the age-stratified biatrial reference values (backlog item 25)
Int J Cardiol 352:180-187. PMID 35124105, DOI 10.1016/j.ijcard.2022.01.071
**TABLE 3 READ IN FULL 2026-08-27.** Same cohort as the Table 2 entry above: n=408 healthy
Chinese adults, CMR. Stratified by decade AND sex. Means +/- SD below; the source also gives
a 95 % CI for every cell and a p-for-trend per row, which are recorded here only where the
trend matters. Group sizes: men 32 / 65 / 67 / 35 / 21, women 28 / 47 / 49 / 31 / 33 across
21-30 / 31-40 / 41-50 / 51-60 / 61-70.

**INDEXED VOLUMES (mL/m2) — what the model would scale on.**
| | 21-30 | 31-40 | 41-50 | 51-60 | 61-70 | p trend |
|---|---|---|---|---|---|---|
| LAVmax/BSA, men | 34.8 ± 7.5 | 35.8 ± 6.9 | 35.8 ± 7.6 | 35.9 ± 9.3 | 36.1 ± 6.7 | 0.548 |
| LAVmax/BSA, women | 35.8 ± 6.1 | 38.5 ± 6.4 | 38.9 ± 6.6 | 37.0 ± 7.6 | 39.9 ± 9.3 | 0.104 |
| LAVmin/BSA, men | 13.8 ± 4.0 | 13.9 ± 3.5 | 14.2 ± 3.9 | 15.4 ± 4.4 | 14.8 ± 3.3 | 0.134 |
| LAVmin/BSA, women | 12.2 ± 2.7 | 14.1 ± 3.7 | 14.9 ± 3.6 | 14.4 ± 3.6 | 15.9 ± 4.9 | <0.001 |
| LAVpac/BSA, men | 21.0 ± 6.1 | 21.8 ± 4.8 | 23.1 ± 5.5 | 25.4 ± 6.8 | 25.8 ± 5.2 | <0.001 |
| LAVpac/BSA, women | 19.8 ± 5.5 | 23.5 ± 4.8 | 24.7 ± 5.1 | 24.9 ± 5.2 | 28.7 ± 7.6 | <0.001 |
| RAVmax/BSA, men | 30.9 ± 9.4 | 35.1 ± 7.5 | 35.1 ± 9.0 | 37.6 ± 12.4 | 34.9 ± 7.4 | 0.057 |
| RAVmax/BSA, women | 31.7 ± 7.1 | 31.2 ± 7.0 | 32.0 ± 8.9 | 33.1 ± 8.8 | 36.6 ± 8.4 | 0.012 |
| RAVmin/BSA, men | 15.2 ± 5.1 | 18.6 ± 5.3 | 18.7 ± 5.3 | 20.5 ± 8.1 | 19.1 ± 5.7 | 0.006 |
| RAVmin/BSA, women | 13.5 ± 3.6 | 13.6 ± 3.9 | 15.8 ± 4.5 | 17.1 ± 4.8 | 17.8 ± 4.7 | <0.001 |
| RAVpac/BSA, men | 22.3 ± 7.2 | 26.8 ± 6.3 | 27.8 ± 7.9 | 30.3 ± 10.2 | 29.6 ± 6.9 | <0.001 |
| RAVpac/BSA, women | 20.3 ± 5.1 | 21.9 ± 5.8 | 24.9 ± 7.0 | 26.0 ± 6.5 | 29.5 ± 6.7 | <0.001 |

**PHASIC FUNCTION (%) — the part that carries the physiology.**
| | 21-30 | 31-40 | 41-50 | 51-60 | 61-70 | p trend |
|---|---|---|---|---|---|---|
| LAEF total, men | 60.4 ± 6.2 | 61.1 ± 6.2 | 60.6 ± 5.3 | 57.1 ± 7.5 | 58.9 ± 5.4 | 0.056 |
| LAEF total, women | 65.9 ± 3.9 | 63.4 ± 6.9 | 61.9 ± 5.8 | 61.1 ± 5.2 | 60.3 ± 5.4 | <0.001 |
| LAEF passive, men | 39.9 ± 10.4 | 39.0 ± 6.9 | 35.6 ± 6.8 | 29.4 ± 6.0 | 28.5 ± 6.8 | <0.001 |
| LAEF passive, women | 45.3 ± 6.6 | 39.1 ± 5.3 | 36.5 ± 5.9 | 32.2 ± 7.8 | 28.1 ± 5.7 | <0.001 |
| **LAEF booster, men** | 33.3 ± 9.2 | 36.2 ± 7.8 | 38.7 ± 6.1 | 39.3 ± 8.9 | **42.3 ± 6.5** | <0.001 |
| **LAEF booster, women** | 37.2 ± 8.0 | 40.0 ± 8.8 | 40.1 ± 6.3 | 42.4 ± 7.5 | **44.9 ± 5.6** | <0.001 |
| RAEF total, men | 49.9 ± 9.1 | 47.4 ± 8.4 | 46.7 ± 7.6 | 45.7 ± 9.2 | 45.8 ± 7.6 | 0.049 |
| RAEF total, women | 57.0 ± 9.4 | 56.7 ± 8.1 | 50.0 ± 9.3 | 48.0 ± 8.4 | 51.2 ± 7.9 | <0.001 |
| RAEF passive, men | 27.1 ± 9.9 | 23.7 ± 7.5 | 20.9 ± 7.6 | 19.3 ± 7.7 | 15.6 ± 6.3 | <0.001 |
| RAEF passive, women | 35.7 ± 11.8 | 30.3 ± 8.4 | 23.0 ± 6.7 | 20.7 ± 6.2 | 18.7 ± 8.7 | <0.001 |
| RAEF booster, men | 31.2 ± 9.3 | 31.1 ± 9.2 | 32.7 ± 8.5 | 32.6 ± 10.3 | 35.8 ± 8.3 | 0.054 |
| RAEF booster, women | 32.8 ± 10.3 | 37.7 ± 9.9 | 34.9 ± 11.2 | 34.4 ± 9.1 | 39.4 ± 11.3 | 0.097 |

Absolute volumes and emptying volumes (LATEV, LAPEV, LAAEV, RATEV, RAAEV) by decade are in
the source and were read; recorded here only where the model could use them, since the
indexed values are what a BSA-scaled model needs. LAAEV men 13.1 -> 19.0 mL and women
11.6 -> 20.5 mL across the decades (both p<0.001) — the booster stroke itself grows.

**THE PHYSIOLOGY WORTH KEEPING.** Total emptying fraction falls with age while the BOOSTER
fraction RISES and the PASSIVE fraction falls — steeply, LAEF passive 39.9 -> 28.5 % in men
and 45.3 -> 28.1 % in women. That is the atrium compensating for stiffer ventricular filling
with a harder kick, which is the physiology of HFpEF appearing in a healthy ageing cohort.
A model that reproduced it would get diastolic dysfunction as a consequence of ageing rather
than as an invented disease model.
NOTE the model has NO separate conduit and booster phases — a single time-varying elastance
produces one emptying stroke. Reproducing the passive/booster split is a structural
prerequisite for using most of this table, and is the real scope of item 25.

## Figliozzi S et al. 2022 — 3D echo LA reference values (meta-analysis)
Int J Cardiovasc Imaging 38:1329-1340. PMID 34994882, DOI 10.1007/s10554-021-02520-9
15 studies, 4,226 healthy adults. Values read from the abstract, which states them:
LAVi max 25.18 mL/m2 (95% CI 23.10-27.26); LAVi min 11.10 (10.01-12.18);
LA-EF 55.94% (51.92-59.96).
NOTE the disagreement with Gao (36.9 vs 25.18 for LAVi max) is MODALITY: CMR reads
larger atrial volumes than 3D echo. Use 25-37 mL/m2 as the band; do not pick a winner.

## Abboud FM & Eckstein JW 1968 II — dog forelimb, arterial vs venous segments
J Clin Invest 47(1):10-19. PMID 16695932, PMC297143, DOI 10.1172/JCI105700
Perfused at CONSTANT flow 64-120 mL/min (mean 80 ± 3.0, n=14). d = change from baseline.

Table 1, norepinephrine, mean ± SE (mmHg):
| | 1 ug | 2 ug | 4 ug |
|---|---|---|---|
| d perfusion pressure, before | 66.1±6.3 | 82.5±7.7 | 89.2±12.4 |
| after 0.25 mg phenoxybenzamine | 56.8±6.0 | 68.9±6.9 | 69.3±11.5 |
| after 0.5 mg | 47.2±5.9 | 59.0±6.0 | 55.8±10.0 |
| d small vein pressure, before | 6.0±1.6 | 13.5±2.7 | 13.0±1.8 |
| after 0.25 mg | 3.7±1.5 | 5.3±1.4 | 6.3±1.8 |
| after 0.5 mg | 1.2±0.6 | 2.1±0.6 | 2.7±0.6 |

Table 2, nerve stimulation 3/6/12 cps: d PP before 76.7±8.5 / 90.0±8.1 / 97.3±9.5;
after 0.5 mg 38.8±6.0 / 44.8±7.7 / 45.5±9.6. d SvP before 7.5±2.1 / 10.3±1.9 / 14.1±2.3;
after 0.5 mg 1.7±0.8 / 2.2±0.7 / 2.8±0.9.
Table 4, paw flow: NE 41.0 -> 27.2 mL/min; nerve stim 38.4 -> 20.4.
Table 5, NE concentration reaching the veins, essentially unchanged by blockade:
0.12 / 0.20 / 0.21 / 0.35 ug before, 0.11 / 0.19 / 0.23 / 0.56 after.
USED: the 1.80x steeper venous dose-response (1 -> 2 ug: arterial x1.25, venous x2.25)
sets the postcapillary Hill shape (backlog 18). NOT YET USED: the phenoxybenzamine
columns quantify alpha-blockade selectivity (venous -84%, arterial -28%) — a ready-made
validation target if the model ever gets an alpha-blocker.

## Doorenbos CJ et al. 1991 — human forearm, NE / AngII / serotonin
Am J Hypertens 4(4 Pt 1):333-40. PMID 1829369, DOI 10.1093/ajh/4.4.333
14 male volunteers 20-29, intra-arterial infusion, no systemic effect. Constrictor-alone:
| | NE 1 ng/kg/min | AngII 0.5 | serotonin 10 |
|---|---|---|---|
| forearm blood flow | -29±6% (P<.05) | -54±5% (P<.01) | -25±11% (NS) |
| capillary filtration rate | no sig effect | NS rise | 0.18±0.02 -> 0.26±0.05 (P<.05) |
| venous pressure at cuff 40 | no sig effect | 31±1 -> 29±1 | 31±1 -> 22±4 (P<.001) |
| d forearm volume mL/100mL | 2.79±0.25 -> 2.51±0.28 | 2.84±0.46 -> 2.10±0.36 | 3.33±0.56 -> 1.36±0.22 |
| max venous outflow mL/100mL/min | 76±7 -> 70±6 (NS) | 79±15 -> 59±12 (P<.01) | 94±14 -> 28±7 (P<.001) |
Resting capillary filtration rate 0.14-0.22 mL/100 mL/min at cuff 40 mmHg.
USED: supports "do not raise Kf" (NE does not change filtration in man). NOT YET USED:
the serotonin arm is the only human demonstration of a mainly-VENOUS constrictor raising
capillary filtration; the resting filtration rates are a possible independent human Kf
anchor (needs a driving-pressure assumption and forearm->whole-body scaling).

## Widrich J & Shetty M — Physiology, Pulmonary Vascular Resistance
StatPearls, NCBI Bookshelf NBK554380. TERTIARY SOURCE (teaching reference), fine for
textbook constants, not for anything load-bearing.
PVR normal 0.25-1.6 mmHg*min/L (= 37-250 dyn*s*cm^-5). Mean PA pressure 15 mmHg.
Pulmonary venous pressure "equivalent to the pulmonary capillary wedge or left atrial
pressure", 5-6 mmHg. Cardiac output 5-6 L/min. Pulmonary hypertension: mean PA > 25 AND
PVR > 3.
USED: pulmonary tests (section 17), and the PV = wedge = LA identity that exposed the
phantom venoatrial valves.

## Lloyd-Donald et al. 2025 — CVP
DOI 10.1111/anae.16633. Normal supine awake CVP 2-3 mmHg.
USED: test_cvp_baseline_calibration.

## Heldt T et al. 2002 Table 3 — ZPFV and compliance (the ANCESTOR model, not truth)
J Appl Physiol 92:1239-1254. PMID 11842064, DOI 10.1152/japplphysiol.00241.2001
| compartment | ZPFV mL | C mL/mmHg |
|---|---|---|
| right ventricle | 50 (Estimate) | 1.2-20 |
| pulmonary arteries | 90 | 4.3 |
| pulmonary veins | 490 | 8.4 |
| left ventricle | 50 (Estimate) | 0.4-10 |
| systemic arteries | 715 | 2.0 |
| upper body veins | 650 | 8 (Estimate) |
| kidney | 150 (Estimate) | 15 (Estimate) |
| splanchnic | 1300 | 55 |
| lower limbs | 350 | 19 |
| abdominal veins | 250 | 25 |
| inferior vena cava | 75 | 2 |
| superior vena cava | 10 | 15 |
NOT A VALIDATION TARGET — see the "Heldt is not ground truth" rule in CLAUDE.md. Several
entries are marked "Estimate" in the paper itself. Used as a cross-check that showed our
pulmonary compliance is ~7.5x low while the systemic side is now the right order.

## Maspers M, Bjornberg J & Mellander S 1990 — cat skeletal muscle Pc vs tone
Acta Physiol Scand 140(1):73-83. PMID 2275407, DOI 10.1111/j.1748-1716.1990.tb08977.x
n=567. Control: Pc 16.7±0.3 mmHg at venous pressure 7, total resistance 19.1±0.3 PRU.
Graded metabolic dilatation to RT 1.7 PRU -> Pc up to 32 mmHg. Graded adrenergic
constriction to RT 100 PRU -> Pc down to 10 mmHg. Pc = 36.43 * RT^-0.27 (r = -0.79).
CAT data — ratios/shape only. NOT YET USED: the power law is a ready-made tone->Pc
relation if the model ever needs one.

## Kelly RP et al. 1992 — effective ARTERIAL elastance (not atrial)
Circulation 86(2):513-21. PMID 1638719, DOI 10.1161/01.cir.86.2.513
n=10 (4 young normotensive, 6 older hypertensive). Ea(PV) = 0.97*Ea(Z) + 0.17,
r2 = 0.98, SEE 0.09. Ea(PV) exceeded mean arterial resistance by up to 25% in older
hypertensives.
NOT YET USED: Ea = end-systolic pressure / stroke volume is directly computable from
this model and is currently UNVALIDATED. A ventriculo-arterial coupling test is a cheap
future win.

## Others noted but not usable for their original purpose
- Iwano H et al. 2020, Heart Vessels 35:1079-1086, PMID 32161994 — v waves on wedge and
  PA pressure, but 61 HEART FAILURE patients (LVEF 35±15%) and the subject is AUGMENTED
  v waves. Wrong population for a healthy reference.
- Espeland T et al. 2023, JACC Cardiovasc Imaging 17:111-124, PMID 37676209 — LV wall
  mechanical wave velocities, 63 healthy subjects: 2.2 and 2.6 m/s (inferolateral,
  anterolateral) vs 1.3 and 1.6 (inferoseptal, anteroseptal) at atrial kick. MYOCARDIAL
  tissue stiffness in m/s, not chamber compliance; this model has no wall mechanics.
- Quillen EW, Granger DN & Taylor AE 1977, Gastroenterology 73:1290-5, PMID 913970 —
  AVP in cat ileum RAISES the pre/post ratio Ra/Rv, LOWERS Pc and LOWERS Kf. Abstract
  only. This is the OPPOSITE sign to alpha-1 agonists and is why vasopressin's
  postcap_factor is deliberately left at 1.0.

---
## Pelosi P et al. 1995 — lung vs chest-wall elastance, WITH A NORMAL CONTROL GROUP
Am J Respir Crit Care Med 152(2):531-7. PMID 7633703, DOI 10.1164/ajrccm.152.2.7633703
Abstract only (states the numbers directly). Esophageal balloon + airway occlusion during
constant-flow inflation, mechanically ventilated. Three groups, measured at PEEP 0,
5, 10 (controls) and 0, 5, 10, 15 (patients). Mean ± SD at PEEP 0:

| group | n | Est,L (cmH2O/L) | Est,w (cmH2O/L) | Est,rs | **Est,w / Est,rs** |
|---|---|---|---|---|---|
| normal, anaesthetised-paralysed | 8 | 9.3 ± 1.7 | 5.6 ± 2.3 | 14.9 | **0.376** |
| moderate acute lung injury | 8 | 13.8 ± 3.3 | 9.9 ± 2.1 | 23.7 | 0.418 |
| ARDS | 8 | 23.7 ± 5.5 | 13.2 ± 5.4 | 36.9 | 0.358 |

Est,w/Est,rs IS the fraction of airway pressure transmitted to the pleural space, so this
is the pleural transmission fraction, measured in humans, in the model's own target
population (anaesthetised, paralysed, normal lungs). USED: `PLEURAL_TRANSMISSION` in
model/respiration.py, which previously carried an unsourced 0.5 (see RETRACTIONS.md R3).
Both Est,L and Est,w rise with injury severity, but their RATIO barely moves — 0.36-0.42
across all three groups. That is a useful robustness result: the transmission fraction is
close to 0.4 regardless of lung pathology, so it is not a knob that disease should swing.
NOT YET USED: the resistance partition (Rmax,L into airway Rmin,L and "additional" DR,L
from viscoelasticity/pendelluft), the PEEP-dependence of each elastance, and the EELV
measurements. The model has no airway mechanics at all, so none of it is reachable yet.

## Takata M, Wise RA & Robotham JL 1990 — abdominal vascular zone conditions
J Appl Physiol 69(6):1961-72. PMID 2076989, DOI 10.1152/jappl.1990.69.6.1961
Abstract only. n=12 dogs, open-chest IVC bypass. **DOG DATA — see CLAUDE.md on species.
Take the STRUCTURE and the RATIO, not the absolute numbers.**

The abdominal venous compartment behaves as either a capacitor (zone 3) or a collapsible
Starling resistor (zone 2), by analogy with pulmonary vascular zones. Raising abdominal
pressure Pab INCREASES IVC venous return when P_ivc(diaphragm) > Pab + Pc (zone 3) and
DECREASES it when P_ivc < Pab + Pc (zone 2).

| quantity | value |
|---|---|
| P_ivc − Pab separating increase from decrease in venous return | **1.00 ± 0.72 mmHg** (SE, n=6) |
| waterfall constant: P_ivc below which femoral venous pressure is independent of P_ivc | **0.96 ± 0.70 mmHg** (SE, n=6) |

The two agree, as the model predicts they should — Pc is a critical closing TRANSMURAL
pressure of about 1 mmHg. A closing pressure transfers across species far better than a
compliance or a time constant does.

## Takata M & Robotham JL 1992 — inspiratory diaphragmatic descent and IVC return
J Appl Physiol 72(2):597-607. PMID 1559938, DOI 10.1152/jappl.1992.72.2.597
Abstract only. Anaesthetised open-chest dogs, phrenic nerve stimulation, ultrasound flow
probes on thoracic and subhepatic abdominal IVC. Splits IVC flow into splanchnic and
non-splanchnic. **DOG DATA.** No numeric table in the abstract; the result is directional:

| volume state | effect of diaphragmatic descent on TOTAL IVC flow |
|---|---|
| hypervolaemic | INCREASES, by raising splanchnic IVC flow (non-splanchnic transiently falls) |
| hypovolaemic | initially increases, then DECREASES, by reducing non-splanchnic flow, with a pressure gradient across the diaphragm consistent with a waterfall |

This sign flip is the mechanism the model is missing, and it is the reason PPV
discriminates volume state at all: in a normovolaemic (zone 3) abdomen the inspiratory
rise in Pab AUGMENTS venous return and partly cancels the fall caused by the rise in
pleural pressure; in a hypovolaemic (zone 2) abdomen it IMPEDES it and adds to the fall.
A model with only the thoracic half of the mechanism gets a large PPV in BOTH states and
therefore cannot separate them. NOT YET IMPLEMENTED — backlog item 27, sibling of item 11
(Guyton waterfall at the thoracic inlet).
Companion review: Robotham & Takata 1995, J Sleep Res 4(S1):50-52,
DOI 10.1111/j.1365-2869.1995.tb00186.x — same concept applied to obstructive sleep apnoea
and to the pathogenesis of Kussmaul's sign.

## Pan C et al. 2016 — Ecw/Ers distribution in acute respiratory failure
Chin Med J 129(14):1652-7. PMID 27411451, DOI 10.4103/0366-6999.185855
Abstract only. n=24 ventilated ARF patients (71% pneumonia), VT 6 mL/kg, split at
Ecw/Ers = 30%: high group n=14 (>=30%), low group n=10 (<30%). Low group had HIGHER lung
elastance (20.0 ± 7.8 vs 11.6 ± 3.6 cmH2O/L, p<0.01), higher PEEP (9.0 ± 2.3 vs 5.7 ± 1.7)
and higher stress (7.0 ± 1.9 vs 4.9 ± 1.9). Airway-pressure stress index tracked
transpulmonary-pressure stress index in both (R2 0.85 low, 0.56 high).
Cross-check on Pelosi only: confirms Ecw/Ers ~0.3 is the middle of a respiratory-failure
population. Not used for a parameter.

## Cortes-Puentes GA et al. 2013 — abdomino-thoracic pressure coupling
Crit Care Med 41(8):1870-7. PMID 23863222, DOI 10.1097/CCM.0b013e31828a3bea
Abstract only. n=11 anaesthetised swine, air-regulated IAP 0-25 mmHg, PEEP 1 and 10.
**Above IAP 5 mmHg, plateau airway pressure rose linearly by ~50% of the applied IAP**,
with commensurate changes in esophageal pressure. End-expiratory transpulmonary pressure
went from -3.5 ± 0.4 cmH2O at PEEP 1 to +0.58 ± 1.2 at PEEP 10. FRC fell with IAP at both
PEEP levels without a matching change in end-expiratory esophageal pressure.
This is the ABDOMEN->THORAX coupling coefficient (~0.5). The model needs the reverse
direction (thorax->abdomen during a machine breath); this bounds it but does not give it.
SWINE DATA. NOT YET USED.

## Leads noted, not yet read
- D'Angelo E et al. 1992, J Appl Physiol 73(5):1736-42, PMID 1474045,
  DOI 10.1152/jappl.1992.73.5.1736 — 8 anaesthetised paralysed supine NORMAL humans,
  PEEP vs ZEEP, partitions Est,L / Est,w and lung + chest-wall viscoelastic constants.
  Same population as Pelosi's control arm; would give the PEEP-dependence of the
  transmission fraction and an independent check on 0.376. Abstract gives no absolutes.
- Chiumello D et al. 2016, Ann Intensive Care 6:13, PMID 26868503,
  DOI 10.1186/s13613-016-0112-1 — n=21 ventilated patients. dPes/dPaw occlusion ratio
  ~1; paralysis raised end-expiratory esophageal pressure by +2.47 cmH2O and the low
  balloon position by +2.26. Relevant to the ABSOLUTE resting pleural pressure the
  mechanical-ventilation branch currently lacks (it starts from 0, while the spontaneous
  branch starts from -2 cmH2O).

---
## Maas JJ et al. — mean systemic filling pressure and compliance, MEASURED IN HUMANS
Three studies from the same Leiden group, all in mechanically ventilated POSTOPERATIVE
CARDIAC SURGERY patients. Abstracts only; all state their numbers directly.
**COHORT CAVEAT: ventilated, post-cardiac-surgery, often volume-loaded and vasoactive-
supported. Not healthy awake supine subjects. The COMPLIANCE is a mechanical property and
should transfer better than the absolute Pmsf does.**

**Maas 2009**, Crit Care Med 37(3):912-8. PMID 19237896, DOI 10.1097/CCM.0b013e3181961481
**READ IN FULL 2026-08-26.** n=12 postoperative CABG/AVR, all on
beta-blockers, sedated with propofol (256 +/- 101 mg/hr) and sufentanil (11 +/- 4 ug/hr),
PEEP 5, VT 6-8 mL/kg, RR 12-14. Age 64 +/- 10, **weight 86 +/- 11 kg**, height 174 +/- 8 cm.
METHOD: four 12-s inspiratory holds at Pvent plateau 5, 15, 25, 35 cmH2O, 1 min apart, last
3 s used; linear fit of Pcv vs pulse-contour CO; pmsf = zero-flow intercept, Rvr = slope.
    Rvr = (pmsf - Pcv)/CO    Rsys = (Pa - Pcv)/CO    Csys = Vload/(pmsf_hyper - pmsf_base)
    Vs (stressed) = Csys x pmsf

Table 2, mean +/- SD (p vs baseline):
| variable | baseline | hypo (30 deg HUT) | p | hyper (+500 mL colloid) | p |
|---|---|---|---|---|---|
| Pa mmHg | 89.9 +/- 21.6 | 75.7 +/- 17.3 | 0.001 | 96.5 +/- 14.9 | 0.170 |
| Pcv mmHg | **6.72 +/- 2.26** | 4.02 +/- 2.12 | 0.001 | 9.67 +/- 2.63 | 0.007 |
| CO L/min | 5.82 +/- 1.44 | 4.76 +/- 1.30 | 0.001 | 6.83 +/- 1.36 | 0.002 |
| HR /min | 86.0 +/- 14.7 | 85.7 +/- 15.1 | 0.456 | 84.3 +/- 10.7 | 0.401 |
| **slope L/min/mmHg** | **-0.465 +/- 0.151** | -0.429 +/- 0.160 | 0.388 | -0.389 +/- 0.135 | 0.134 |
| pmsf mmHg | 18.76 +/- 4.53 | 14.54 +/- 2.99 | 0.005 | 29.07 +/- 5.23 | 0.001 |
| Pvr mmHg | 12.04 +/- 3.70 | 10.52 +/- 2.27 | 0.106 | | |

**THE SLOPE IS THE NUMBER THIS PROJECT NEEDED.** Rvr = 1/0.465 = 2.151 mmHg per L/min =
**0.129 mmHg.s/mL**, measured directly in humans with an intact circulation. Cross-checks
against their own data: CO = Pvr/Rvr = 12.04/0.129 = 5.60 L/min vs 5.82 measured.
**The slope is UNALTERED by volume state** (p = 0.388 and 0.134) — a structural fact worth
holding onto: resistance to venous return should be roughly volume-independent.

**Rvr/Rsys = 15 % at baseline**, 23 % with volume loading, 15 % with hypovolaemia. This
dimensionless ratio locates pmsf within the circulation ("in the range of the
capillary-venule pressures"). Per CLAUDE.md a ratio is the best kind of cross-cohort
target, and this is the single most useful number in the paper for us.

Csys **80 +/- 62 mL/mmHg (0.98 +/- 0.82 mL/mmHg/kg)** — note the enormous SD.
Stressed volume **1677 +/- 1643 mL**, reported in the Results as 12.5 +/- 12.1 mL/kg but in
the Discussion as 19.5 mL/kg (= 1677/86). INTERNAL INCONSISTENCY in the paper; 19.5 is the
ratio of means, 12.5 presumably the mean of per-patient ratios. Recorded, not resolved.
Hypovolaemia cost about 200 mL of stressed volume.

**CAVEATS THE AUTHORS THEMSELVES RAISE, and they matter more than the headline numbers:**
- Csys was measured **>20 minutes after volume loading**, where animal studies measure
  **30 seconds** after. They attribute their lower value partly to this. Previously reported
  Csys is **1.4-2.6 mL/mmHg/kg in dogs** and **1.5-2.4 in rats**.
- Quoting Rothe: "it is virtually impossible to measure the vascular capacitance
  characteristics ... in reflex-intact animals and humans ... because one cannot change
  blood volume and measure pmsf in <7-10 seconds, which is the maximal delay before reflex
  venoconstriction normally becomes evident, unless these reflexes are blocked."
  **So their Csys is NOT a passive compliance.** It is a 20-minute, reflex-intact,
  fluid-shift-inclusive chord.
- 500 mL colloid "can expand plasma volume by more than 500 mL".
- Propofol and sufentanil blunt sympathetic responsiveness; "these studies will need to be
  repeated in nonanesthetized subjects".
- Their technique may overestimate pmsf under hypervolaemia (squeezing blood out of the lung).

**OTHER pmsf VALUES THEY COLLATE** (useful, and none were in this ledger before):
| source | pmsf mmHg | method |
|---|---|---|
| Jellinek et al, n=10 humans | **10.2** | apnoea + ventricular fibrillation (true stop-flow) |
| Schipke et al, n=85 humans | **12** | same design |
| dogs | 7-12.5 | |
| rats | 7-9 | |
| pigs | 10-12 | |
| conscious calves, artificial heart | 20-30 | |
Both human stop-flow studies were "highly anesthetized nonvolume resuscitated subjects".
Maas notes his own higher value tracks his patients' raised Pcv: "if one assumes a similar
Rvr, this Pcv pressure difference would extrapolate to a pmsf of 12 mmHg for our subjects
if their Pcv was zero."

Magder & De Varennes: stressed volume **20.2 mL/kg**, measured by draining patients into
the pump reservoir at hypothermic circulatory arrest — the most direct measurement of
stressed volume there is.
Samar & Coleman: total circulatory stop gives an equal plateau pressure within 4-5 s, with
a SECOND rise after 10-12 s (rats) / 12-15 s (dogs) which is sympathetic reflex activation.

**Maas 2012a**, Anesth Analg 115(4):880-7. PMID 22763909, DOI 10.1213/ANE.0b013e31825fb01d
n=15, ten sequential 50-mL colloid boluses. Csys linear over the range:
| quantity | value |
|---|---|
| systemic vascular compliance Csys | **64.3 ± 32.7 mL/mmHg** |
| Csys per kg predicted body weight | **0.97 ± 0.49 mL/mmHg/kg** |
| stressed volume | **1265 ± 541 mL (28.5 ± 15 % of predicted blood volume)** |
Volume-responsive patients (>12% rise to 500 mL) had STEEP cardiac function curves, the
rest flat. Internally consistent: 1265/64.3 = 19.7 mmHg, matching the Pmsf above.

**Maas 2012b**, Intensive Care Med 38(9):1452-60. PMID 22584797, PMC3423572,
DOI 10.1007/s00134-012-2586-0
n=11, three methods compared across supine / 30 deg head-up / 500 mL colloid:
| method | value |
|---|---|
| Pmsf, inspiratory hold | **20.9 ± 5.6 mmHg** |
| Parm, arm stop-flow | 19.8 ± 5.7 |
| Pmsa, Guytonian model analog | 14.9 ± 4.0 |
Parm vs Pmsf bias -1.0 ± 3.08 mmHg (NS), COV 15 %, LOA -7.3 to 5.2. Pmsf vs Pmsa bias
-6.0 ± 3.1 (p<0.001) — **the model analog reads ~6 mmHg LOW against the measured value**,
which is worth remembering before trusting any modelled Pmsf, including ours.

**COMPARISON WITH THIS MODEL — REVISED 2026-08-26 after reading Maas 2009 in full.**
The earlier version of this block concluded the model's compliance was ~2x too high. That
was NOT like-for-like and the conclusion is withdrawn. Compared on matched timescales and
matched methods:

| quantity | model (70 kg) | best-matched human/animal measurement | verdict |
|---|---|---|---|
| Csys per kg | 1.76 mL/mmHg/kg | dogs 1.4-2.6, rats 1.5-2.4 (measured 30 s after loading) | **in range** |
| | | Maas 0.98 +/- 0.82 (>20 min, reflex-intact) | different quantity |
| MSFP | 10.15-10.44 mmHg | Jellinek 10.2 (n=10), Schipke 12 (n=85), human STOP-FLOW | **matches** |
| | | Maas 18.76 (12 s hold extrapolation, their Pcv 6.7 not ~0) | different method |
| stressed volume | 18.8 mL/kg | Magder 20.2 mL/kg, drained at circulatory arrest | **matches** |
| CVP | 5.6-6.0 mmHg | Maas measured Pcv 6.72 +/- 2.26 | **matches** |
| Rsys | 0.808 mmHg.s/mL | Maas 0.858 | **matches (0.94x)** |
| **Rvr** | **0.0399** | **Maas 0.129, measured as the VR curve slope** | **0.32x — TOO LOW** |
| **Rvr/Rsys** | **4.9 %** | **Maas 15 %** | **0.34x — TOO LOW** |

So four quantities match and one does not. The model's error is not capacitance at all:
**total systemic resistance is right but the model puts only ~5 % of it downstream of the
pmsf point where humans have ~15 %.** The venular/venous resistance is roughly three times
too low relative to the arteriolar. Rvr/Rsys is dimensionless, which per CLAUDE.md makes it
the most transferable target available. Backlog item 28 rewritten around it.

## Ferguson JJ et al. 1989 — RIGHT ATRIAL pressure-volume relations in humans
J Am Coll Cardiol 13(3):630-6. PMID 2918169, DOI 10.1016/0735-1097(89)90604-9
Figures 1, 2, 4 and Table 1 READ IN FULL 2026-08-26. n=16 at
cardiac catheterisation: 11 without an interatrial shunt, 5 with an ASD. RA volume by
multi-electrode IMPEDANCE catheter, continuous on-line pressure-volume data.

**THE CENTRAL LIMITATION, read off the axes: VOLUME IS REPORTED IN RELATIVE UNITS, NOT
MILLILITRES.** Figure 1's right-hand axis is "RIGHT ATRIAL RELATIVE VOLUME" (0-60) and
Figure 2's abscissa is "RELATIVE VOLUME" (30-60, with a break near the origin). So this
paper CANNOT give a chamber stiffness in mmHg/mL and cannot be used to derive or check
RA_EMIN. The V-loop slope reads about 0.20 mmHg per relative-volume unit, which resembles
the model's RA_EMIN of 0.20 mmHg/mL by pure coincidence of numbers — do not cite it as
agreement. Requested for exactly that derivation; it does not support it.

WHAT IT DOES GIVE — Figure 1, normal RA pressure waveform, one illustrative patient with
normal coronary arteries and no ASD, timed against ECG over ~750 ms:
| feature | value |
|---|---|
| a wave (peak, after P wave) | ~11 mmHg |
| x descent (trough, ~225 ms) | ~4.5 mmHg |
| v wave (~600 ms) | ~8.5 mmHg |
| **peak-to-trough swing** | **~6.5 mmHg** |
| approximate mean | ~7.5 mmHg |
USED: the SWING is the usable quantity — it constrains the RA_EMAX/RA_EMIN ratio, which is
a dimensionless ratio and so survives the relative-volume problem intact. Model swing was
2.98 mmHg before 2026-08-26, i.e. under half, agreeing with the independent finding that
model RAEF 39.0 % falls short of Gao's 49.7 %.
CAVEAT ON THE LEVEL: n=1 illustrative trace from a catheterisation patient, NOT a cohort
mean and NOT a healthy volunteer. It is a data point against `test_cvp_baseline_calibration`'s
2-4 mmHg band, not a refutation of it. Do not retarget that test on this figure alone.

Figure 2 — the RA pressure-volume loop is a FIGURE EIGHT: a counterclockwise A loop
(atrial contraction, spanning roughly pressure 5.3-10.5) and a clockwise V loop (passive
filling, roughly 6.7-9.0), meeting near the p wave at about 8.5 mmHg. Structural point the
model does reproduce in kind: the atrium is not a single-elastance chamber over the cycle.

Figure 3 — effect of RESPIRATION, patient without ASD, spontaneous breathing, INSP marks
~6 s apart (so ~10 breaths/min, slow and fairly deep). Stated in the caption:
**"With inspiration there is a decline in right atrial pressure and an increase in right
atrial volume. During expiration, right atrial pressure increases as right atrial volume
declines."** RA pressure and RA volume are ANTI-CORRELATED across the breath. Pressure
trace runs roughly 4-13 mmHg including the cardiac waves; the RESPIRATORY component of the
RA pressure swing is roughly **4-5 mmHg peak-to-peak**. Volume again in relative units.
USED: the DIRECTION, as `test_ra_fills_during_spontaneous_inspiration_ferguson1989` — a
calibration-independent guard on THORACIC_COMPARTMENTS, since the RA fills on inspiration
only because pleural pressure is applied to the atrium and not to the abdominal IVC.
NOT ASSERTABLE, and recorded rather than dropped: the pressure half of that sentence. The
model's reported `cvp` deliberately EXCLUDES respiratory ITP (defined as an end-expiratory
clinical reading), so no current output corresponds to a continuous catheter trace.
GAP THIS EXPOSES: measured on 2026-08-26, the model's respiratory swing in RA intraluminal
pressure is about **0.2 mmHg against Ferguson's 4-5**, and the volume swing is ~0.7 mL.
Direction correct, amplitude roughly 20x short. The cause is documented in
model/respiration.py itself — the spontaneous ITP swing is held to 1 cmH2O (0.74 mmHg)
deliberately, because the physiological limiter on venous return is not modelled and a
realistic swing floods the RA every cycle. Backlog item 30; it is the same missing
mechanism as item 27.

Figure 4 — Valsalva, patient without ASD. At peak Valsalva RA pressure RISES (toward the
20 mmHg reference line drawn on the figure) while BOTH relative RA volume AND RA stroke
volume FALL. Qualitative only, no table. USED: backlog item 29, the Valsalva test.

Table 1 — the five ASD patients (NOT the normals; the paper gives no equivalent table for
the 11 without a shunt):
| pt | age/sex | defect | RAP mmHg | PAP | Art P | Qp/Qs | Art sat % |
|---|---|---|---|---|---|---|---|
| 1 | 53F | primum | 13 | 67/25 | 107/70 | 5.9 | 95 |
| 2 | 62F | secundum | 6 | 26/12 | 144/70 | 1.4 | 92 |
| 3 | 41F | secundum | 2 | 20/8 | 128/91 | 1.5 | 94 |
| 4 | 27M | secundum | 6 | 22/8 | 108/65 | 1.3 | 96 |
| 5 | 59F | secundum (small R-to-L) | 5 | 65/25 | 130/70 | 2.2 | 91 |
RAP is the MEAN right atrial pressure. NOT USED: this is a shunt cohort, so it is not a
normal reference — but note mean RAP spans 2-13 mmHg in adults at catheterisation, which
is worth remembering whenever a single "normal CVP" figure is quoted narrowly.
NOT YET USED: the ASD pressure-volume findings (their loops resembled the non-shunt
patients at baseline, but mean RA volume did NOT change with respiration or Valsalva
despite similar pressure changes) — a ready-made target if the model ever gains a shunt.


---
## Rudski LG et al. 2010 — ASE right heart guidelines: RAP estimation from the IVC
J Am Soc Echocardiogr 23(7):685-713. PMID 20620859, DOI 10.1016/j.echo.2010.05.010
**READ IN FULL 2026-08-26.**
Endorsed by the EAE and the Canadian Society of Echocardiography.

Table 3 — estimation of RA pressure from IVC diameter and collapse:
| category | RAP point value | range | IVC diameter | collapse with sniff |
|---|---|---|---|---|
| **normal** | **3 mmHg** | **0-5** | <=2.1 cm | >50 % |
| intermediate | 8 | 5-10 | <=2.1 cm / >2.1 cm | <50 % / >50 % |
| high | 15 | 10-20 | >2.1 cm | <50 % |
Intermediate may be downgraded to 3 if no secondary indices of elevated RA pressure are
present, or upgraded to high if collapse is <35 % AND secondary indices are present.
Secondary indices of elevated RA pressure: restrictive right-sided filling, tricuspid
E/E' > 6, diastolic flow predominance in the hepatic veins (systolic filling fraction <55 %).

**WHAT THIS IS AND IS NOT.** These are values ASSIGNED from IVC appearance for the purpose
of computing systolic pulmonary artery pressure — a clinical estimation convention, not a
measured distribution of RAP in healthy people. The guideline itself lists as a
disadvantage that "IVC collapse does not accurately reflect RA pressure", and says collapse
"cannot be used to reliably estimate RA pressure" in ventilated patients (the IVC does not
collapse on a ventilator). It also notes the IVC may be dilated in normal young athletes
without elevated RA pressure.
Still, it is the ONLY normal-subject RAP reference in this ledger, and echo is the one
modality that can be applied to healthy awake volunteers — which was the gap item 31
recorded. USED: nothing yet; see the tension below.

**THE TENSION, recorded rather than resolved.** Every RAP number now in the ledger:
| source | value | population |
|---|---|---|
| Rudski 2010, echo convention | **3 (range 0-5)** | normal |
| Maas 2009, catheter | 6.72 +/- 2.26 | sedated, ventilated, PEEP 5, post-op |
| Ferguson 1989 Fig 1, catheter | ~7.5 mean | one cath-lab patient, no ASD |
| Ferguson 1989 Table 1, catheter | 2, 5, 6, 6, 13 | five ASD patients |
| Cecconi 1998 (PMID 9616849), catheter | 9.1 +/- 4.3, range 3-20 | 114 cardiac-disease patients |
The only NORMAL-population figure is the lowest one. The model's default patient breathes
spontaneously with reflexes intact, so Rudski's population is the right comparison, and
against it the model reads high: trough 5.7, mean ~6.4, against a normal range of 0-5.
`test_cvp_baseline_calibration` was widened 2-4 -> 2-8 earlier the same day, before this
was read. **The band has NOT been moved again** — moving it twice in one session, each
time in the direction that accommodates the model, is the exact failure mode this project
guards against. Flagged for a decision.

## Cecconi M et al. 1998 — echo estimation of mean RAP, validated invasively
G Ital Cardiol 28(4):357-64. PMID 9616849. Abstract only.
n=114 consecutive patients with various cardiac diseases (77 M, age 57 +/- 12), echo within
24 h of catheterisation (mean interval 6 +/- 3 h).
Mean RAP **9.1 +/- 4.3 mmHg, range 3-20**. Best correlates: IVC collapsibility index
r = -0.76; minimal inspiratory IVC diameter r = 0.72; tricuspid E deceleration time
r = -0.61. Best equation: mean RAP = 23.3 - 0.2*IVCCI - 0.026*DT (r = 0.80, R2 = 0.64).
IVCCI >45 % best predicts RAP <=8; IVCCI <35 % with DT <150 ms best predicts RAP >=15.
CARDIAC-DISEASE cohort, so not a normal reference — recorded because it is the invasive
validation behind the echo method, and it shows how wide real RAP spread is.
