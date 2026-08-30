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

---
# WANTED — sources the model needs and I could not retrieve (2026-08-28)

Ranked by what they unblock. Each says what NUMBER is needed, not just a topic, because a
paper that does not contain the number is worse than no paper (see RETRACTIONS R2 and R3).

## 1. Thorax-to-abdomen pressure transmission during positive-pressure ventilation
**Unblocks item 27, which is the most clinically dangerous open gap** — the model flags a
normovolaemic patient as fluid-responsive (PPV 24.7 % against Michard's < 13 %).
NEEDED: the ratio of the RESPIRATORY SWING in abdominal pressure to that in pleural
pressure, during mechanical ventilation, in humans. In practice that means a study
recording OESOPHAGEAL and GASTRIC (or bladder) pressure SIMULTANEOUSLY in ventilated
patients, reporting both swings or their ratio.
**THE REQUEST MUST SAY "PASSIVE" — my first version did not, and that cost a paper.**
Akoumianaki 2024 (below) has exactly the pairing I asked for, 76 patients with simultaneous
oesophageal and gastric pressure, and it still cannot answer the question, because every
patient has spontaneous breathing activity. Its ΔPgas is the patient's own EXPIRATORY MUSCLE
contraction, not pressure transmitted from the thorax. What is needed is a PARALYSED or
fully passive patient on controlled ventilation, where the only thing moving the abdomen is
the diaphragm being pushed down by the ventilator.
WHAT I HAVE, all reverse-direction or static:
  Shaji (2026-08-29) — HUMANS, n=42: driving pressure +0.72 cmH2O per unit IAP. The best
    bound available, and it moved the swine 0.50 to a human 0.72.
  Cortes-Puentes 2013 (PMID 23863222) — swine, plateau airway pressure +~50 % of applied IAP.
  Sindi 2014 — n=43 PARALYSED patients: the STATIC Pabd-Pes correlation is weak (0.79
    univariate, collapsing to 0.10 and non-significant once BMI is included). A static
    coupling term is not supported; the swing is a different quantity and was not measurable
    in that study because every patient got the same insufflation pressure.
**ANSWERED AND CLOSED 2026-08-30. ITEM 27 IS NO LONGER BLOCKED ON A SOURCE.**
Both papers were obtained and read in full: **Heijnen 2016** (PMID 26732769) for the tidal
swing in humans, and **van den Berg, Jansen & Pinsky 2002** (PMID 11842062,
DOI 10.1152/japplphysiol.00487.2001) for the mechanism and endpoint in 42 sedated and
PARALYSED humans. Full entries in the ledger body. Working coefficient: **~0.21 of the
PLEURAL swing** for thorax -> abdomen in a tidal, normovolaemic setting, with van den Berg's
dPabd/dPra of 0.73 as evidence the mechanism can hold cardiac output flat when the abdomen
is full.

**WHAT WOULD STILL IMPROVE IT, in priority order — none blocking:**
  1. **The volume-dependence of dPabd/dPra.** van den Berg measured it in deliberately
     hypervolaemic patients and says so. Nobody has measured how it weakens as volume falls,
     and that is precisely the discrimination PPV depends on. This is now the most valuable
     unmeasured quantity for item 27.
  2. **Verzilli** (n=30 ARDS: 30 % transmission at normal IAP, 57 % at IAP >= 12 mmHg) and
     **Gattinoni 1998** (10 % pulmonary vs 14 % extrapulmonary ARDS), both cited by Heijnen,
     to fill in the spread and test whether the method really explains it.
  3. A tidal-swing measurement in PARALYSED normovolaemic patients would settle Heijnen vs
     van den Berg outright.

**Original request, kept for the record:**
Heijnen 2016, PMID 26732769, DOI 10.1177/0885066615625180, J Intensive Care Med
32(3):218-222, "Low Transmission of Airway Pressures to the Abdomen in Mechanically
Ventilated Patients With or Without Acute Respiratory Failure and Intra-Abdominal
Hypertension". n=18 ventilated patients, intravesical pressure at 5-second inspiratory and
expiratory holds, transmission reported as **~8 %**. Full entry with all numbers is in the
body of this ledger.
**NEEDED NOW: the FULL TEXT, to answer exactly two questions.** Not in PMC; likely paywalled.
  (a) Is the 8 % referenced to AIRWAY pressure (as the title says) or PLEURAL pressure (as
      the abstract says)? Pleural-referenced it becomes ~21 %. The model needs pleural.
  (b) Were the patients paralysed or merely sedated? Akoumianaki failed this test.
Secondary want: the same measurement with an OESOPHAGEAL balloon rather than a bladder
catheter, which would remove question (a) entirely.
Takata's zone conditions (PMID 2076989) give the STRUCTURE and a ~1 mmHg closing pressure,
but in dogs.
DO NOT let me pick a coefficient without this. One chosen to land PPV under 13 % would be
tuning to the endpoint.

**ON THE EXPECTED SIGN — I WROTE THIS TWICE ON 2026-08-30 AND THE SECOND READING STANDS.**
First reading, from Heijnen's 8 % plus Diaz's piglets: the abdominal swing is small and
raising abdominal pressure raises PPV, so item 27 probably cannot bring PPV down.
Second reading, after finding van den Berg 2002 an hour later: **that was too pessimistic,
and it was built on the weaker evidence.** van den Berg raises airway pressure to 20 cmH2O
in 42 PARALYSED humans and finds cardiac output and RV end-diastolic volume UNCHANGED,
because 73 % of the rise in right atrial pressure is matched by a rise in abdominal
pressure. That is item 27's hypothesis confirmed at the endpoint, in the right species and
the right passive state, measuring the thing we actually care about rather than a
transmission coefficient.
Why the first reading was weak: Diaz is piglets under sustained tonic IAH, not a tidal
swing, and its finding that PPV rises with IAH is about a pathological abdomen, not a
normal one. Heijnen's 8 % is airway-referenced (~21 % pleural) and disagrees with van den
Berg by five-fold for reasons not yet resolved.
**Current position: item 27 remains the right mechanism and MAY well bring PPV down. Build
it because it is correct; do not tune the coefficient to land under 13 %.** The two
candidate coefficients differ five-fold, so settling Heijnen vs van den Berg comes first.

## 2. The FIRST 24-72 HOURS of head-down bed rest
**Unblocks the bed-rest arm of item 33** — long-duration runs need a gradeable target.
NEEDED: plasma volume, central venous pressure and stroke volume against time over the
first one to three days of -6 deg head-down tilt. Hourly or twice-daily sampling.
WHAT I HAVE: Spaak 2004 (PMID 15501923, DOI 10.1152/japplphysiol.01332.2003) — 120 days of
-6 deg HDT, n=6, with upright resting SV -24 +/- 9 % at day 60, supine exercise SV -5 +/- 8 %
at day 60 and -18 +/- 4 % at day 113, HR +18 +/- 4 % at day 60, MAP unchanged. Good paper,
WRONG TIMESCALE — its earliest timepoint is day 60 and we need hours to days. Recorded
anyway; it would be the target if the model ever runs for months.
The one bed-rest paper already in the validation log (PMID 15838970) was EXCLUDED as a
deconditioning confound. For a multi-day ADAPTATION test, deconditioning is the phenomenon
rather than the confound, so that exclusion may be worth revisiting.

## 3. Baroreflex resetting time course in humans
**Unblocks Phase 4 of slow_dynamics**, which is planned but has NO sourced target at all.
NEEDED: how fast the baroreflex operating point shifts toward a sustained new pressure —
a time constant, or a percentage reset at stated times over minutes to days.
This also matters for the long runs: the model's reflex does NOT reset, so a multi-hour run
currently holds sustained reflex activation where a real one adapts.

## 4. Right atrial pressure in HEALTHY AWAKE supine adults
**Unblocks item 31.** Searched 2026-08-26 and 2026-08-28, not found, and possibly does not
exist — you do not catheterise healthy volunteers.
NEEDED: a measured distribution, not an assigned value. Rudski 2010's normal RAP of 3 mmHg
(range 0-5) is ASSIGNED from IVC appearance to compute pulmonary pressures; the guideline
itself says IVC collapse does not reliably reflect RA pressure. Every other RAP number in
this ledger is from sedated, ventilated or catheter-lab subjects.
A healthy-volunteer study with central access for another reason would do it.

## 5. Noradrenaline's chronotropic and right-ventricular effects
**Would firm up two unsourced numbers in pharmacology.py.** The chronotropic ceiling is set
at +10 % and the RV inotropic effect at 0.7 of the LV effect. Both are modelling choices
with no source. The 0.7 is flagged as such in the test, and the sign error it replaced cost
the noradrenaline validation test (see validation_log.md 2026-08-28).
NEEDED: dose-response for heart rate and for RV contractility, in humans, over the clinical
range 0.01-0.5 mcg/kg/min.

## Sindi A et al. 2014 — oesophageal vs abdominal pressure, PARALYSED patients
Respir Care 59(4):491-496. **READ 2026-08-29.** n=43, elective laparoscopic surgery,
intubated AND PARALYSED — the passive condition item 27 requires. Age 53.2 +/- 14.6,
BMI 33.7 +/- 10.5 (range 13.7-60.5), PEEP 5-7 cmH2O in 19 patients and 0 in the rest.
Recorded Pes 9.5 +/- 4.7 cmH2O.

| relationship (baseline, before insufflation) | coefficient (95 % CI) | R2 | p |
|---|---|---|---|
| Pabd -> Pes, univariate | **0.79 (0.36-1.21)** | 0.24 | 0.001 |
| BMI -> Pes, univariate | 0.29 (0.19-0.40) | 0.41 | <0.001 |
| Pabd -> Pes, MULTIVARIABLE | **0.10 (-0.46 to 0.65)** | | **0.73 (NS)** |
| BMI -> Pes, multivariable | 0.27 (0.11-0.43) | 0.40 | 0.001 |

**THE STATIC COUPLING IS WEAK AND BMI CONFOUNDS IT.** The univariate Pabd-Pes correlation
of 0.79 collapses to 0.10 and loses significance once BMI is in the model, while BMI stays
highly significant. Their conclusion is that abdominal pressure has "limited value" as a
surrogate for oesophageal pressure. So a naive static coupling of the form
Pabd = k * Ppleural is NOT supported.
**IT STILL DOES NOT GIVE ITEM 27'S COEFFICIENT, and the reason is specific:** item 27 needs
the coupling of the RESPIRATORY SWING, not of the static baseline, and those are different
quantities — a static offset can couple weakly while the tidal swing transmits well. Sindi
tried to measure the change: "Due to unexpected uniformity of abdominal inflation pressures
(generally 20.4 cmH2O) during surgery, data were not amenable to assessment of correlation
between CHANGES in abdominal and esophageal pressures after inflation." Every patient got
the same insufflation pressure, so there was no variation to regress against.
**WHAT THE MODEL CAN USE TODAY — the BMI row, not the abdominal one.** The model has no
BMI channel at all: height and weight collapse to BSA, and BSA scales everything, so body
shape does nothing (backlog item 34). The 0.27 cmH2O per BMI unit is a directly usable
static offset on intrathoracic pressure: BMI 20 -> 30 is +1.98 mmHg, which is larger than
the model's whole spontaneous ITP swing of 0.74 mmHg. Fumagalli 2019 fixes the structure —
obese patients have NORMAL chest-wall elastance and HIGH pleural pressure — so this belongs
as an offset on the ITP level, not as a change to PLEURAL_TRANSMISSION (0.376, Pelosi 1995).
Anchor caveat: the cohort mean BMI is 33.7 and the patients are paralysed, so the slope is
measured in obesity and should not be extrapolated down to BMI 18, and R^2 0.40 means it is
a population trend rather than a per-patient prediction.

## Heijnen BGADH et al. 2016 — THORAX -> ABDOMEN transmission, the number item 27 asked for
J Intensive Care Med 32(3):218-222. PMID 26732769, DOI 10.1177/0885066615625180.
Found 2026-08-30 by PubMed search. **FULL TEXT READ 2026-08-30** (Jesper supplied the PDF;
copy in `docs/papers/heijnen_2016_thorax_abdomen_transmission.pdf`). This is the study design
WANTED item 1 specified. n=18 mechanically ventilated patients: 9 within 3 h of uncomplicated
cardiac surgery, 9 within 12 h of acute respiratory failure (lung injury score > 1.5; 6 of 9
had ARDS). Supine. Intravesical pressure via Foley manometer, measured three times at
3-minute intervals and averaged (reproducibility 1.8 %), at the end of 5-second inspiratory
and expiratory HOLD manoeuvres. Patients after abdominal trauma or surgery were excluded.

**THE DENOMINATOR IS AIRWAY PRESSURE. THE TITLE WAS RIGHT AND THE ABSTRACT WAS LOOSE.**
Methods, verbatim: the transmission index is "the ratio of a change in abdominal pressure
(end-inspiratory IAP minus end-expiratory IAP) to the change in intrathoracic pressure,
**that is, Pplat minus PEEP**". Plateau minus PEEP is AIRWAY DRIVING PRESSURE, not pleural
pressure. So the 8 % is per unit AIRWAY pressure and must be converted before use.

| | Group 1 (cardiac surgery, n=9) | Group 2 (ARF, n=9) | P |
|---|---|---|---|
| End-inspiratory plateau pressure, cmH2O | 16.9 (1.8) | 29.1 (6.3) | <.001 |
| PEEP, cmH2O | 6.0 (1.3) | 12.9 (6.4) | .35 |
| End-inspiratory IAP, cmH2O | 12.7 (3.3) | 14.3 (3.9) | 1.0 |
| End-expiratory IAP, cmH2O | 11.7 (3.4) | 13.2 (3.9) | 1.0 |
| "Total" IAP over the cycle, cmH2O | 12.0 (3.4) | 13.5 (3.9) | 1.0 |
| **Transmission index, % of AIRWAY** | **8.9 (5.0)** | **7.1 (7.9)** | .35 |
| "True" IAP, cmH2O | 11.1 (3.4) | 12.3 (4.1) | 1.0 |
| Tidal volume, mL/kg | 7.5 (1.4) | 5.7 (1.4) | .35 |
| Total respiratory compliance, mL/cmH2O | 52.0 (7.2) | 28.8 (8.6) | .003 |
| Lung injury score | 0.72 (0.34) | 1.99 (0.74) | <.001 |
| Age, years | 66.3 (8.5) | 60.6 (10.0) | 1.0 |
| **Body mass index, kg/m2** | **26.4 (3.2)** | **26.9 (3.7)** | 1.0 |

By IAP stratum (Table 3): IAP >= 12 mmHg (n=5) TI 8.7 (4.1); IAP < 12 mmHg (n=13) TI 7.7
(4.8), P = 1.0. Transmission does NOT depend on baseline IAP, respiratory compliance, or
ventilator settings across the range studied.

**CONVERSION TO THE PLEURAL REFERENCE THE MODEL NEEDS**, using Pelosi's 0.376
(dPpl = 0.376 * dPaw, already in `respiration.py`):
| Group | dPaw | dIAP | TI vs airway | dPpl | **TI vs PLEURAL** |
|---|---|---|---|---|---|
| 1 | 10.9 | 1.0 | 9.2 % | 4.10 | **24.4 %** |
| 2 | 16.2 | 1.1 | 6.8 % | 6.09 | **18.1 %** |
| pooled | | | ~8 % | | **~21 %** |
**USE ~0.21 FOR THORAX -> ABDOMEN, NOT 0.08.** The model's ITP is already a pleural
pressure, so feeding it the airway-referenced 8 % would understate the coupling by 2.6x.

**CAVEAT — SEDATED, NOT PARALYSED.** "Patients were ventilated in a pressure-controlled
mode under sedation and analgesia with propofol or midazolam and fentanyl". No neuromuscular
blockade is reported. This is much closer to passive than Akoumianaki (pressure-controlled
mode, 5-second holds that an actively breathing patient would disturb, and group 1 within
3 h of cardiac surgery), but spontaneous effort is not formally excluded. Treat 0.21 as the
best available human estimate with that qualification attached, not as a measured passive
value.

**THE SDs ARE LARGE RELATIVE TO THE MEANS: 8.9 (5.0) and 7.1 (7.9).** Group 2's interval
includes zero. n=18 total. This is a "proof-of-principle study" by the authors' own
description. The coefficient is small AND noisy; do not present it as precise.

**THE LITERATURE ON THIS RANGES FROM 0 % TO 57 %, AND THE METHOD EXPLAINS THE SPREAD.**
Values Heijnen tabulates from prior work, all AIRWAY-referenced:
| Source | Value | Preparation |
|---|---|---|
| Sussman 1991, n=15 post-laparotomy | PEEP to 15 cmH2O did not affect IAP | humans |
| Jakob 2010 | PEEP to 10 cmH2O not transmitted | pigs |
| Gattinoni 1998 | ~10 % (pulmonary ARDS, n=12), 14 % (extrapulmonary, n=9) | humans |
| Verzilli, n=30 ARDS | 30 % (normal IAP), **57 %** (IAP >= 12 mmHg) | humans |
| Heijnen 2016 | ~8 % | humans |
Heijnen's explanation, and it decides which number this model should use: earlier authors
**stepped PEEP up** and measured the resulting IAP change, whereas Heijnen used
**end-inspiratory holds at unchanged ventilator settings**. A sustained PEEP step and a
within-breath tidal swing are different perturbations. **The model needs the within-breath
swing, so Heijnen's method is the correct one for item 27** — Verzilli's 57 % answers a
different question. Heijnen notes transmission "may be linear in the range studied" but did
not vary settings to confirm it.

**THE ASYMMETRY IS THE REAL FINDING, and it is physiologically sensible.**
Transmission is NOT reciprocal, and the two directions must be separate coefficients:
| Direction | Value | Source |
|---|---|---|
| abdomen -> thorax | ~50 % | Regli 2019 review; Cortes-Puentes swine |
| abdomen -> thorax | 72 % (driving pressure per unit IAP) | Shaji, humans, n=42 |
| thorax -> abdomen | ~8 % of airway, or ~21 % of pleural | Heijnen, humans, n=18 |
Why: raising abdominal pressure pushes the diaphragm up into a COMPRESSIBLE lung, so much
of it arrives. Raising thoracic pressure pushes the diaphragm down onto a nearly
incompressible fluid-filled abdomen with a COMPLIANT wall, which simply displaces outward,
so little pressure builds. Never model this with one shared coefficient.

## van den Berg PCM, Jansen JRC, Pinsky MR 2002 — ITEM 27'S MECHANISM, MEASURED DIRECTLY
J Appl Physiol 92(3):1223-1231. PMID 11842062, DOI 10.1152/japplphysiol.00487.2001.
Found 2026-08-30 from Heijnen's reference 10. **This is the closest study to item 27 that
exists, and it is in SEDATED AND PARALYSED humans.** Their stated hypothesis is item 27
verbatim: "PEEP-induced diaphragmatic descent increases abdominal pressure... we
hypothesized that an increase in Paw induced by PEEP would minimally alter venous return
because the associated increase in Pra would be partially offset by a concomitant increase
in Pabd."

n=42 patients in ICU after coronary artery bypass surgery, haemodynamically stable and
fluid-resuscitated. Airway pressure raised progressively in 2-4 cmH2O steps from 0 to
20 cmH2O in sequential **25-second inspiratory-hold manoeuvres**. RV cardiac output and RV
ejection fraction by thermodilution at 5 s into each hold; RV end-diastolic and stroke
volume derived; Pra from the pulmonary artery catheter; Pabd estimated as bladder pressure.

**FULL TEXT READ 2026-08-30** (Jesper supplied the PDF; copy in
`docs/papers/van_den_berg_2002_positive_pressure_venous_return.pdf`).

| Quantity | Value | Note |
|---|---|---|
| **dPabd / dPra** | **0.73 +/- 0.36** | "not significantly different from unity"; both in mmHg, so UNIT-CLEAN |
| dPra / dPaw | 0.32 +/- 0.2 | mean of per-subject regression slopes |
| **dPabd / dPaw** | **0.20 +/- 0.1** | DIRECTLY MEASURED, not chained |
| dCOtd / dPra | 0.05 +/- 0.15 L/min/mmHg | not significantly different from 0 |
| RV end-diastolic volume at 20 cmH2O | **+18.3 +/- 24 %** | "slight but significant" INCREASE |
| Heart rate, maximal change 0 -> 20 cmH2O | -4.9 +/- 9 % | |
| Pra at 0 Paw -> at maximal Paw | 8.12 +/- 3.4 -> 15.42 +/- 3.0 mmHg | |
| Paw range achieved | 0 -> 19.01 +/- 2.7 cmH2O | |
| Maximal inflated volume | 1750 mL (range 1250-2250), 16 mL/kg | limited by thorax drain |
| Total compliance (lung + thorax) | 85 mL/cmH2O (62-112) = 1.1 mL/kg/cmH2O | NORMAL |
| Tricuspid insufficiency, Paw-dependent | NONE, by TEE at 0 and 20 cmH2O and by Pra waveform in all 42 | |

**CORRECTION TO MY OWN ENTRY OF AN HOUR EARLIER.** From the abstract I chained
dPabd/dPaw = 0.32 / 0.73 = 0.44 and recorded that. **The paper measures it directly as
0.20 +/- 0.1.** The chain was invalid: all three figures are means of PER-SUBJECT ratios,
and the mean of a ratio is not the ratio of means (0.20/0.32 = 0.63, not the 0.73 they
report, and the authors do not remark on it). **Use 0.20. This is the fifth
derived-versus-measured slip in this project — always prefer the number the paper actually
measured.**

**UNITS ARE MIXED AND IT MATTERS.** Table 1 reports Pra and Pabd in mmHg; Paw is in cmH2O.
Checking against the raw endpoints: dPra = 7.30 mmHg for dPaw = 19.01 cmH2O gives 0.384 in
mixed units and 0.522 if Paw is converted first. The reported 0.32 is far closer to the
mixed-unit value, so **the ratios against Paw are almost certainly mmHg per cmH2O**. In
consistent units they become dPra/dPaw = 0.44 and **dPabd/dPaw = 0.27**. This is an
inference from internal consistency, not a statement in the paper — treat it as such.
**dPabd/dPra = 0.73 is immune to all of this** (both quantities in mmHg), which is one more
reason to prefer it.

**THE HEADLINE RESULT IS THE ENDPOINT ITSELF, NOT A COEFFICIENT.** Raising airway pressure
to 20 cmH2O raised Pra from 8.1 to 15.4 mmHg and yet cardiac output did not change, and RV
end-diastolic volume rose slightly. The authors attribute this to "an in-phase-associated
pressurization of the abdominal compartment associated with compression of the liver and
squeezing of the lungs". **For this model the usable statement is: 70 % or more of any rise
in right atrial pressure is matched by a rise in abdominal pressure, so the gradient for
venous return is nearly preserved.** That is item 27's mechanism, quantified, in paralysed
humans, measured at the endpoint we care about.

**THE LIMITATION THAT MATTERS MOST FOR OUR PPV PROBLEM — READ BEFORE BUILDING ITEM 27.**
The authors state it themselves: "We measured COtd in fluid-filled, **probably
hypervolemic**, patients", and they chose that deliberately ("To maximize any potential
effect of Pabd on Pms"). **The mechanism was measured in the condition most favourable to
it.** A full splanchnic reservoir is what makes diaphragmatic descent able to sustain venous
return; a hypovolaemic abdomen has much less blood to squeeze. Our PPV target is the
NORMOVOLAEMIC patient, so 0.73 is very likely an UPPER bound for our case, and the
volume-dependence of this mechanism is itself unmeasured here. Do not assume it transfers
to the normovolaemic model unchanged.

Two further mechanisms the authors raise, neither quantified, both plausible additions
later: hepatic compression by the descending diaphragm augmenting hepatic venous outflow
(Matuschak), and a fall in resistance to venous return from redistribution of drainage away
from the portal circuit. They also note that in almost none of their patients could an
estimate of Pms be made from the data using Guyton's model.

**RECONCILED WITH HEIJNEN — NOW ~3x APART, NOT 5x, AND THE REASONS ARE IDENTIFIABLE.**
Heijnen 0.08 (dimensionless: he converts bladder mmHg to cmH2O explicitly) versus van den
Berg 0.20 mixed-unit = ~0.27 dimensionless.
  - **Perturbation size and duration.** van den Berg drives Paw to ~19 cmH2O and holds 25 s
    with 1750 mL inflated; Heijnen uses 5 s holds at unchanged tidal settings
    (dPaw 11-16 cmH2O). A large sustained inflation recruits diaphragmatic descent that a
    tidal breath does not.
  - **Fluid state.** van den Berg's patients are deliberately volume-loaded; Heijnen's are
    not. A full abdomen transmits better than a slack one.
  - **Paralysis.** van den Berg's are paralysed, Heijnen's only sedated. Residual
    diaphragmatic tone opposes descent and would lower apparent transmission.
DO NOT average them. **For a TIDAL swing in a normovolaemic patient — which is the PPV
question — Heijnen's preparation is the closer match and 0.08 airway / ~0.21 pleural is the
more defensible starting point. van den Berg's 0.73 dPabd/dPra is the better evidence that
the MECHANISM is real and that it can hold cardiac output flat.** Those two statements are
compatible: the mechanism is genuine, and its magnitude in our target condition is at the
low end.

### van den Berg Table 1 — baseline apnoeic haemodynamics, n=42 post-CABG, mean +/- SD
Directly useful as a human reference set, and note these are VENTILATED POST-OPERATIVE
patients, not healthy awake adults (so this does NOT settle item 31).
| Quantity | Value |
|---|---|
| Mean arterial pressure | 75 +/- 15 mmHg |
| Mean pulmonary arterial pressure | 21 +/- 5 mmHg |
| **Right atrial pressure** | **9 +/- 4 mmHg** |
| **Abdominal pressure (bladder)** | **9 +/- 6 mmHg** |
| Cardiac output (thermodilution) | 5.74 +/- 1.52 L/min |
| **RV ejection fraction** | **0.41 +/- 0.09** |
| Cardiac index | 2.93 +/- 0.70 L/min/m2 |
| Stroke volume index | 36 +/- 10 mL/m2 |
| **RV end-diastolic volume index** | **88 +/- 21 mL/m2** |
| **RV end-systolic volume index** | **51 +/- 18 mL/m2** |
| Pulmonary arterial occlusion pressure | 10 +/- 1 mmHg |
Age 59 yr (range 40-74), weight 78 kg (range 52-110). Anaesthetised with high-dose fentanyl
(50 ug/kg), some on dopamine < 5 ug/kg/min and nitroglycerine.
**RVEF 0.41 is LOW against healthy values and RV EDVI 88 is high — these are post-CABG
hearts, so use this table for the ABDOMINAL and Pra numbers and treat the RV volumes as a
diseased-cohort cross-check, not a normal target.** Baseline Pabd of 9 +/- 6 mmHg in supine
ventilated patients is a directly usable resting value.

## Loring SH et al. 2009 — simultaneous oesophageal, gastric and bladder pressure
J Appl Physiol 108(3):515-522. PMID 20019160, DOI 10.1152/japplphysiol.00835.2009.
n=48 acute lung injury patients. The best available STATIC three-way comparison. Abstract
only; PMC full text is empty.

| Quantity | Mean +/- SD (cmH2O) |
|---|---|
| End-expiratory oesophageal pressure Pes | 18.6 +/- 4.7 |
| End-expiratory gastric pressure Pga | 18.4 +/- 5.6 |
| End-expiratory bladder pressure Pblad | 19.3 +/- 7.8 |
| Transpulmonary pressure, end exhalation | -2.8 +/- 4.9 |
| Transpulmonary pressure, end inflation | 8.3 +/- 6.2 |

Pes correlates with Pga (p=0.0004) and Pblad (p=0.0104), and is UNRELATED to chest wall
compliance. Pes-Pga differences match expected gravitational gradients.
**NOTE THE STATIC LEVELS ARE NEARLY EQUAL (18.6 / 18.4 / 19.3) WHILE THE SWING TRANSMITS AT
~8 %.** That pairing is the cleanest evidence that the static offset and the tidal swing are
different quantities — the same point Sindi forced, now with all three pressures at once.
NEGATIVE end-expiratory transpulmonary pressure in ALI is also worth remembering: it means
airway closure at end exhalation is normal in these patients, not an artefact.

## Regli A, Pelosi P, Malbrain MLNG 2019 — review, ventilation in intra-abdominal hypertension
Ann Intensive Care 9(1):52. PMID 31025221, DOI 10.1186/s13613-019-0522-y. Open access.
Review, not primary data. Quoted for one line: **"Abdominal-thoracic pressure transmission
is around 50 %."** Consistent with Cortes-Puentes' swine 50 % and brackets Shaji's human
72 %. Also: IAH is present on admission in 1 in 4 to 1 in 3 ICU patients, and half develop
it within the first ICU week. IAH is defined as IAP > 12 mmHg.

## Diaz F et al. 2015 — PPV and SVV under intra-abdominal hypertension, by tidal volume
BMC Anesthesiol 15:127. PMID 26395001, DOI 10.1186/s12871-015-0105-x. Open access.
12 anaesthetised, mechanically ventilated PIGLETS. Hypovolaemia excluded first with two
fluid boluses. IAH induced by intraperitoneal colloid until respiratory system compliance
halved. **SPECIES: pig — see the animal-vs-human rule; use the RATIOS, not the absolutes.**

| VT (mL/kg) | PPV baseline | PPV during IAH | SVV baseline | SVV during IAH |
|---|---|---|---|---|
| 6  | 3 % (2-4.25)   | 6 % (4.75-7)      | 3 % (3-4)   | 5 % (4-6.25)   |
| 12 | 5 % (4-6)      | 13.5 % (10.25-15.5) | 5 % (4-6)   | 11 % (8.75-17) |
| 18 | 7 % (5.5-8.5)  | 24 % (13.5-30.25) | 5 % (4-7.5) | 15 % (8.75-19.5) |

**TWO RESULTS THAT BEAR DIRECTLY ON ITEM 27.**
  1. Raising abdominal pressure RAISES PPV, and the rise is bigger at bigger tidal volume.
     PPV also rises steeply with VT alone at baseline (3 -> 5 -> 7 %).
  2. Under IAH, NEITHER PPV NOR SVV could identify the fluid responders at any tidal volume,
     even though a third of the animals responded. The authors' conclusion is that these
     indices depend on intrathoracic AND intra-abdominal pressure as well as volaemia.

## Valenza F et al. 2004 — negative extra-abdominal pressure, PARALYSED pigs
Intensive Care Med 31(1):105-111. PMID 15517159, DOI 10.1007/s00134-004-2483-2.
8 sedated and PARALYSED pigs (19.6 +/- 3.4 kg), with airway, oesophageal, gastric and
central venous pressure recorded SIMULTANEOUSLY. Right passive state and right
instrumentation; wrong species and the intervention is applied around the abdomen.

| Quantity | Value |
|---|---|
| NEXAP applied | -20 cmH2O |
| Gastric pressure fall | 1.97 +/- 2.26 mmHg |
| Oesophageal pressure fall | 1.21 +/- 0.67 mmHg |
| Implied abdomen -> thorax ratio | 1.21 / 1.97 = **0.61** |
| Intrathoracic blood volume | 358 +/- 47 -> 314 +/- 47 mL (-44 mL, -12.3 %) |
| ITBV fall vs CVP fall | R^2 = 0.820 |
| Chest wall elastance during IAH | 0.067 +/- 0.023 -> 0.056 +/- 0.021 cmH2O/mL |
| Peritoneal pressure when raised | 24.7 +/- 5.5 mmHg |

The 0.61 sits between Cortes-Puentes' 0.50 and Shaji's 0.72, from a third species and a
third method, which is mild support for the abdomen -> thorax direction being roughly
one-half to three-quarters. The ITBV-CVP coupling (44 mL of thoracic blood per ~2 mmHg of
abdominal pressure change, R^2 0.82) is a separate and directly model-relevant number: it
is a measured volume shift for a measured pressure change in a passive preparation.
USED: as a CAUTION against a static coupling term. Not for a coefficient.

## Shaji U et al. — intra-abdominal pressure and ventilatory mechanics, HUMANS
J Anaesthesiol Clin Pharmacol. **READ 2026-08-29.** n=42, laparoscopic cholecystectomy,
prospective cohort. Timepoints T1-T3 at identical ventilator settings across rising IAP,
then PEEP raised to 8 (T4) and 11 cmH2O (T5) at IAP 14 mmHg.

| relationship | value | r | p |
|---|---|---|---|
| **driving pressure per unit IAP** | **+0.72 cmH2O** | 0.73 | <0.001 |
| mechanical power per unit IAP | +0.19 | 0.71 | <0.001 |
Effect sizes 0.89 and 0.90. Airway resistance rose and respiratory compliance fell from
T1 to T3, both reversing at T4-T5. Raising PEEP from 5 to 11 increased mechanical power
while driving pressure fell.

**THIS IS THE BEST HUMAN NUMBER YET FOR THE ABDOMEN-TO-THORAX DIRECTION.** At constant
tidal volume, a driving-pressure rise of 0.72 per unit IAP means the chest wall absorbs
~72 % of the added abdominal pressure. It upgrades Cortes-Puentes 2013 (PMID 23863222),
which gave ~50 % in SWINE, to a human value: **0.72 vs 0.50, same direction, humans stiffer.**
STILL THE REVERSE DIRECTION. Item 27 needs THORAX -> ABDOMEN (the ventilator raises pleural
pressure, the diaphragm descends, the abdomen follows), and this is ABDOMEN -> THORAX
(insufflation pushes the diaphragm up). The two are not guaranteed symmetric — they put
different compliances in series — so this BOUNDS the coefficient rather than supplying it.
USED: not yet. It is the tightest bound available and should be quoted whenever item 27's
coefficient is finally chosen.

## Akoumianaki E et al. 2024 — gastric pressure and active expiration
Anesthesiology 141:541-53. **READ 2026-08-29. Does NOT answer item 27 — see why.**
n=76 invasively ventilated patients on ASSISTED ventilation with spontaneous breathing
activity, retrospective, with simultaneous oesophageal (Peso) and gastric (Pgas) pressure.
58 of the 76 showed active expiration, defined as ΔPgas >= 1.0 cmH2O during expiratory flow
without a corresponding change in diaphragmatic pressure.

| quantity | value (median, IQR) |
|---|---|
| ΔPgas, active-expiration subgroup (n=58) | **3.4 cmH2O (2.4-5.3)** |
| ΔPeso, whole cohort | 10.0 cmH2O (7.4-13.7) |
| ΔPeso, active vs passive expiration groups | 10.7 (8.2-14.6) vs 8.4 (5.8-12.0), p<0.05 |
| ΔPdi | 8.4 cmH2O (5.4-11.2) |
| tidal volume | 468 (417-545) vs 497 (443-615) mL |
| duration of active-expiration recordings | 27.2 min (17.9-48.3) |
Among the 58, active expiration produced distortions mimicking ineffective efforts,
autotriggering and multiple triggering; prolonged cycles with biphasic inspiratory flow
raised mechanical inflation time by 54 % (44-70) and tidal volume by 25 % (8-35).

**WHY IT DOES NOT GIVE ITEM 27'S COEFFICIENT.** The paper's own definitions:
ΔPeso is the "inspiratory DECREASE in esophageal pressure" and ΔPgas the "expiratory
INCREASE in gastric pressure". They are different PHASES of the breath and both are
generated by the PATIENT'S OWN MUSCLES. Their ratio is expiratory effort over inspiratory
effort, not thorax-to-abdomen transmission. Item 27 needs a passive patient in whom the
ventilator raises pleural pressure and the abdomen follows; here the abdomen leads.
USED: nothing. Recorded because the numbers are worth having if the model ever represents
expiratory muscle activity, and because it sharpened the WANTED request above.


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

## Atrial contribution to LV filling — the target 25a actually needs (2026-08-31)

Found by PubMed search while scoping the mitral / pulmonary-venous coupling. **This is the
quantity that maps onto Gao's passive/booster split, and the ledger had nothing on it.**

### Alhogbani T, Strohm O, Friedrich MG 2012 — CMR, the primary target
J Magn Reson Imaging 37(4):860-864. PMID 23097384, DOI 10.1002/jmri.23881.
n=120 normal subjects, 50 % female, steady-state free precession CMR volumetry, short-axis
and rotational long-axis views. **Atrial contraction contribution (ACC) = LV filling volume
from left atrial contraction, divided by LV stroke volume.**

| Age band | ACC (% of LV stroke volume) |
|---|---|
| < 40 years | **15 +/- 5 %** |
| 40-55 years | **28 +/- 8 %** |
| > 55 years | **38 +/- 5 %** |

Overall range 10-40 %, strongly age-dependent. Their age-adjusted rule: ACC % divided by
age gives 0.4-0.7 at any age in normals — so at the model's reference age of 55 that is
**22-38.5 %**.
**SAME MODALITY AS GAO (CMR), and a VOLUME fraction, so it is directly comparable to the
model** — unlike E/A, which is a ratio of peak VELOCITIES and does not translate cleanly
into volumes.

### Faggiano P et al. 1989 — Doppler, normal controls, volume fractions of filling
J Hum Hypertens 3(3):149-156. PMID 2769673. n=25 age-matched normal subjects (control arm
of a hypertension study), transmitral blood flow by Doppler.

| Quantity | Normal controls |
|---|---|
| Peak E velocity | 0.62 +/- 0.1 m/s |
| Peak A velocity | 0.49 +/- 0.1 m/s |
| **E/A ratio (derived)** | **~1.27** |
| **E area, % of total diastolic area** | **56 +/- 5 %** |
| **A area, % of total diastolic area** | **26 +/- 5 %** |
| Deceleration half-time | 80 +/- 12 ms |

E area + A area = 82 %, so **diastasis accounts for the remaining ~18 %** of filling. That
three-way split — 56 % early, 26 % atrial, 18 % diastasis — is the shape the model should
reproduce. Their hypertensive arms are recorded for completeness: E area falls to 48 +/- 5
(no LVH) and 43 +/- 6 (LVH), A area rises to 41 +/- 4 and 47 +/- 7, DHT lengthens 80 -> 90
-> 105 ms. NOT USED as a target — the model has no hypertensive phenotype — but it is the
direction diastolic dysfunction moves, and item 25b will want it.

### Mohan JC et al. 1994 — Doppler, young controls
Indian Heart J 46(3):129-132. PMID 7821932. n=15 matched controls (control arm of a mitral
valvuloplasty study, so YOUNG). Atrial contribution **12.5 +/- 3.3 %** of total filling
volume. Consistent with Alhogbani's < 40 band of 15 +/- 5 %.
Also useful as a bound on the MITRAL RESISTANCE question: in severe mitral stenosis
(valve area 0.78 +/- 0.12 cm2) the atrial contribution FELL to 8 +/- 2.8 %, and rose back
to 12.5 +/- 3.8 % after valvuloplasty opened the valve to 1.72 +/- 0.4 cm2. So raising
mitral resistance LOWERS the atrial contribution — which is the opposite of what the model
needs, and is direct evidence that mitral resistance is the WRONG LEVER for the model's
low booster fraction.

### THE THREE SOURCES AGREE, AND THEY SETTLE THE AGE GRADIENT
| Age | ACC | Source |
|---|---|---|
| young (< 40) | 12.5-15 % | Mohan, Alhogbani |
| 40-55 | 26-28 % | Alhogbani, Faggiano |
| > 55 | 38 % | Alhogbani |
Three independent cohorts and two modalities. This is a firmer target than most numbers in
this ledger, and it is exactly the quantity item 25b (age) will need later — the atrial
contribution roughly TRIPLES from young adult to elderly, which is the same physiology as
Gao's LAEF booster rising with age while passive falls.

**MODEL COMPARISON, AND THE UNIT TRAP.** The model's LA booster EF is 14.3 %, but that is
(VpreA - Vmin)/VpreA — a fraction of ATRIAL volume. ACC is a fraction of LV STROKE VOLUME.
They are different denominators and must not be compared directly. The model's booster moves
5.8 mL against a stroke volume of ~86 mL, so its ACC is of order 7 %, against a target of
22-38.5 % at the reference age of 55. **Measure ACC properly from mitral flow before using
this — do not compare the two fractions as if they were the same quantity.**

### Caballero L et al. 2015 — NORRE, the definitive reference ranges
Eur Heart J Cardiovasc Imaging 16(9):1031-1041. PMID 25896355, DOI 10.1093/ehjci/jev083.
n=449 healthy volunteers (198 men, 251 women), mean age 45.8 +/- 13.7, EACVI-approved
acquisition protocol. Age- and sex-stratified Doppler reference ranges.
ABSTRACT ONLY so far. It states the trends — E wave and e' higher in the young and falling
with age, E/e' rising with age, most diastolic parameters similar between sexes — but the
per-decade E and A tables are in the paper, not the abstract.
**WANTED: the NORRE Doppler tables**, which would give sex- and decade-stratified E and A
for the male reference this project validates on. Companion paper for 3D LV volumes is
Bernard 2017, PMID 28329230, DOI 10.1093/ehjci/jew284 (LV EDV upper limit 97 mL/m2 in men,
ESV 42, EF lower limit 50 %) — worth having for item 25b alongside Luu.

## Caballero L et al. 2015 — NORRE Doppler reference ranges, FULL TEXT READ 2026-08-31
Eur Heart J Cardiovasc Imaging 16(9):1031-1041. PMID 25896355, DOI 10.1093/ehjci/jev083.
PDF supplied by Jesper; copy in `docs/papers/caballero_2015_norre_doppler_reference_ranges.pdf`.
n=449 healthy volunteers (198 men, 251 women), mean age 45.8 +/- 13.7, EACVI-approved
acquisition and measurement protocol, 22 collaborating institutions.
**This project validates on MALE patients — the male columns are the ones to use.**

### Table 3 — transmitral Doppler by age and sex (male columns)
| Parameter | 20-40 y | 40-60 y | >= 60 y | age correlation (men) |
|---|---|---|---|---|
| E wave velocity (m/s) | 0.79 +/- 0.14 | 0.72 +/- 0.16 | 0.67 +/- 0.15 | r = -0.31, p < 0.001 |
| A wave velocity (m/s) | 0.50 +/- 0.13 | 0.61 +/- 0.15 | 0.73 +/- 0.16 | r = +0.49, p < 0.001 |
| **E/A ratio** | **1.69 +/- 0.52** | **1.22 +/- 0.31** | **0.96 +/- 0.27** | r = -0.61, p < 0.001 |
| E deceleration time (ms) | 179.8 +/- 46.4 | 186.6 +/- 52.8 | 217.5 +/- 69.7 | r = +0.23, p = 0.001 |
Whole cohort, both sexes: E 0.76 +/- 0.17, A 0.60 +/- 0.17, E/A 1.37 +/- 0.51
(95 % CI 0.64-2.74), DT 188.0 +/- 49.4 ms. A wave, DT and E/A show no sex difference;
E wave is higher in women (0.79 vs 0.74, p = 0.002).
**The model's reference age is 55, so the target band is the male 40-60 column: E/A 1.22.**

### Tissue Doppler, and the number that matters for filling pressure
Whole cohort: septal e' 10.3 +/- 3.0, lateral e' 13.5 +/- 4.0, average e' 11.9 +/- 3.1 cm/s.
e' falls steeply with age (septal 12.1 -> 9.8 -> 7.6 cm/s across the three bands).
| E/e' | whole cohort |
|---|---|
| Septal | 7.9 +/- 2.4 |
| Lateral | 6.1 +/- 2.1 |
| Average septal + lateral | 6.8 +/- 2.1 |
| **Average of five sites** | **6.6 +/- 2.0** |
No sex difference at any site.

### Table 4 — proportions exceeding thresholds (NOT means)
LA volume > 34 mL/m2 in 15.1 % of the healthy global cohort and > 37 mL/m2 in 8.9 %
(single-plane area-length, four-chamber); by other methods 9.1-20.7 % and 5.4-12.6 %.
sPAP > 36 mmHg in 1/294 (0.3 %); sPAP > 45 mmHg in 0/294.

### CROSS-CHECKS AGAINST WHAT THE LEDGER ALREADY HELD
1. **E/A agrees with Faggiano.** NORRE male 40-60 gives 1.22 +/- 0.31; Faggiano's normal
   controls give E 0.62 / A 0.49 = ~1.27. Independent cohorts, 26 years apart.
2. **The AGE DIRECTION agrees with Gao and Alhogbani, which is the important one.** A wave
   rises (0.50 -> 0.61 -> 0.73 m/s) while E falls, so E/A drops 1.69 -> 1.22 -> 0.96. That
   is the same physiology as Gao's LAEF booster RISING and LAEF passive FALLING with age,
   and as Alhogbani's atrial contribution tripling from 15 % to 38 %. **Four independent
   sources, three modalities, one consistent story: the ageing atrium takes over more of
   ventricular filling.** This is now the best-supported age trend in the ledger and it is
   what item 25b will be built on.
3. **LA volume: NORRE aligns with the ECHO sources, not the CMR one.** Only 15.1 % of
   healthy subjects exceed 34 mL/m2, so the normal echo LA volume sits well below that —
   consistent with Figliozzi's 3D echo 25.18 mL/m2 and NOT with Gao's CMR 36.9 +/- 7.7.
   This is a THIRD source confirming the modality split already flagged under item 23.
   **The model's LAVmax of 50.5 mL/m2 is above the threshold that only 9 % of healthy
   people exceed, by either modality.**
4. **sPAP.** Essentially no healthy subject exceeds 36 mmHg systolic. Not a direct
   constraint on the model's MEAN PA of 20.60, but it is consistent with the mean PA
   ceiling of 20 the pulmonary test asserts.

### THE PCWP TARGET IN `test_pulmonary_pressures_are_physiological` IS TOO LOW
The test's 5-6 mmHg wedge figure comes from [P1] StatPearls, which the test file itself
flags as tertiary with the note that "anything load-bearing should be traced to a primary
measurement". It is load-bearing, and it is at the bottom of the usual clinical range.
Applying Nagueh's relation (PCWP = 1.24 * E/e' + 1.9) to NORRE's measured values in 449
healthy volunteers:
| E/e' | implied PCWP |
|---|---|
| septal 7.9 | 11.7 mmHg |
| average 6.6 | 10.1 mmHg |
Standard clinical normal PCWP is **6-12 mmHg**, not 5-6. **So the model's 12.4 mmHg is
mildly high — at or just above the upper limit — NOT "more than double" as recorded earlier
on 2026-08-31 while scoping the coupling.** That earlier statement was wrong and is
withdrawn. The PCWP discrepancy is a weak signal for the mitral coupling work, not a strong
one; LAVmax (50.5 vs a 34-37 ceiling) and the atrial contribution (~7 % vs 22-38.5 %) are
the strong ones.
