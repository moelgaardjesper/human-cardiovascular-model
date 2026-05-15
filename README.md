# Cardiovascular System Simulator

> An open-source, lumped-parameter model of human cardiovascular physiology for intraoperative and physiological research use.

---

## Overview

This simulator predicts haemodynamic responses to clinical interventions in real time. It is designed for intraoperative use — where understanding how a patient's cardiovascular system responds to posture, vasopressors, or altered gravity can guide clinical decision-making. Inputs scale from the minimal (blood pressure + BMI) to full intracardiac monitoring, so the model works with whatever data is available at the bedside.

The model is a **work in progress**. Validation has been iterative: after each implementation step, outputs were compared to published physiological measurements, and parameters were adjusted accordingly. Known limitations are documented openly (see [Limitations](#limitations)).

---

## Clinical Use Cases

| Scenario | What the model predicts |
|---|---|
| **Trendelenburg (head-down tilt)** | CVP rise, MAP response, preload change |
| **Reverse Trendelenburg** | Venous pooling, orthostatic compensation |
| **Vasopressor titration** | MAP, CO, and SVR response to NE / phenylephrine / vasopressin |
| **Intraoperative hypotension** | Fluid responsiveness, haemodynamic reserve |
| **Postoperative bed-rest / recovery** | Cardiovascular adaptation to supine position |

Microgravity scenarios are included not because space medicine is a primary target, but because **the physiology of microgravity and postoperative bed-rest are cardiovascular analogues**: both eliminate orthostatic gravitational stress, redistribute central blood volume, and alter baroreflex dynamics. Including these scenarios strengthens the coherence of the vascular model across the full gravitational range.

---

## Quick Start

```bash
git clone https://github.com/moelgaardjesper/vascular-model.git
cd vascular-model
pip install -r requirements.txt

# Start the web interface
python3 -m api.app
# → open http://localhost:5000
```

### Run tests

```bash
# Smoke tests
pytest tests/

# Literature validation suite
python3 tests/stress_test_literature.py
```

---

## Interface

A browser-based single-page interface (no build step required):

**Patient panel** — height, weight, MAP, HR; optional cardiac output, ABI, CVP, PCWP, PAP

**Scenario panel** — tilt angle slider (−30° to +30°), vasopressor selection and dose, gravity environment

**Output panel** — live arterial pressure waveform, cardiac output, CVP, heart rate

---

## Architecture

```
model/
  compartments.py   23-compartment parameter set; lower body veins split into
                    foot / calf / thigh to model distributed hydrostatic column
  heart.py          Time-varying elastance (Suga-Sagawa); Frank-Starling plateau
  gravity.py        ΔP = ρgh·sin(α) per compartment; smooth tilt transitions
  baroreflex.py     4-step arterial + cardiopulmonary reflex (Heldt 2002)
  pharmacology.py   Hill-equation PD: NE, phenylephrine, vasopressin, epi
  patient.py        3-tier parameter scaling from sparse clinical inputs
  circulation.py    ODE system (Euler, dt = 1 ms); run_simulation() entry point

api/               Flask REST API (synchronous; < 1 s per 60 s simulation)
frontend/          Plain HTML + Plotly.js; no build step
tests/             Smoke tests + 5-scenario literature validation suite
```

### Patient input tiers

| Tier | Required inputs | What is estimated |
|---|---|---|
| **1 — Minimal** | MAP, height, weight | All parameters via allometric scaling (Mosteller BSA) |
| **2 — Intermediate** | + Cardiac output, ABI | Arterial resistance, peripheral disease index |
| **3 — Advanced** | + CVP, PCWP, mean PAP | Full intracardiac calibration |

---

## Scientific Basis

The model is built on established lumped-parameter cardiovascular modelling literature. All references below were retrieved via PubMed or PMC.

### Foundational model

- **Heldt T, Shim EB, Kamm RD, Mark RG** (2002). Computational modeling of cardiovascular response to orthostatic stress. *J Appl Physiol* 92:1239–1254.
  The foundational 21-compartment model and baroreflex structure this simulator is based on.

- **PMC9363491** — Mohammadyari et al. Cardiovascular model for orthostatic stress and Mars mission planning. *Sci Rep* 2022.
  Primary source for compartment parameter values, hydrostatic tilt implementation, and spaceflight adaptation data. DOI: [10.1038/s41598-022-25731-5](https://doi.org/10.1038/s41598-022-25731-5)

### Validation data

Outputs were validated against the following published physiological measurements. After each comparison, model parameters were revised to better match the literature.

- **Sørensen et al.** (2022). To identify normovolemia in humans: the stroke volume response to passive leg raising vs head-down tilt. *Physiol Rep* PMID: 35854636. DOI: [10.14814/phy2.15216](https://doi.org/10.14814/phy2.15216)
  *Used for:* supine resting haemodynamics (MAP, HR, SV, CO); 20° HDT response in normovolemic subjects.

- **Verdini et al.** (2019). Cardiovascular responses to leg muscle loading during head-down tilt at rest and after dynamic exercises. *Sci Rep* PMID: 30808948. DOI: [10.1038/s41598-019-39360-6](https://doi.org/10.1038/s41598-019-39360-6)
  *Used for:* HDT vs upright directional haemodynamic comparisons; effect of leg muscle loading.

- **Sibbald WJ et al.** (1979). The Trendelenburg position: hemodynamic effects in hypotensive and normotensive patients. *Crit Care Med* PMID: 467083.
  *Used for:* Trendelenburg response validation in normotensive patients (MAP, CO, SVR).

### Venous physiology

- **Sjöstrand T** (1953). Volume and distribution of blood and their significance in regulating the circulation. *Physiol Rev* 33:202–228. PMID: 13055444. DOI: [10.1152/physrev.1953.33.2.202](https://doi.org/10.1152/physrev.1953.33.2.202)
  *Used for:* calibration target of ~640 mL venous pooling in lower extremities on standing; motivated the 3-compartment lower body venous split (foot / calf / thigh).

- **Blomqvist CG, Stone HL** (1983/2011). Cardiovascular adjustments to gravitational stress. *Comprehensive Physiology* 1025–1063.
  Comprehensive review of orthostatic cardiovascular physiology; informed the hydrostatic indifference concept and compartment height assignments.

- **Hinghofer-Szalkay H** (2011). Gravity, the hydrostatic indifference concept and the cardiovascular system. *Eur J Appl Physiol* 111:163–174.
  *Used for:* hydrostatic indifference point positioning and baroreflex sensor placement rationale.

### Related modelling work

- DOI: [10.1038/s41598-022-18831-3](https://doi.org/10.1038/s41598-022-18831-3) — VoM-PhyS: 3D multiscale vascular blood-flow and heat-transfer framework.
- [VaMpy](https://openresearchsoftware.metajnl.com/articles/10.5334/jors.159) — 1D arterial wave propagation model (JORS).

---

## Validation Summary

The model has been validated against published human physiological data across five scenarios:

| Scenario | Reference | Status |
|---|---|---|
| Supine resting (MAP, HR, SV, CO) | [10.14814/phy2.15216](https://doi.org/10.14814/phy2.15216) | ✓ PASS |
| 20° HDT — directional response | [10.14814/phy2.15216](https://doi.org/10.14814/phy2.15216) | ✓ PASS |
| 6° HDT vs 20° upright (HR direction) | [10.1038/s41598-019-39360-6](https://doi.org/10.1038/s41598-019-39360-6) | ✓ PASS |
| −30° Trendelenburg (CVP↑, MAP maintained) | Clinical expectation / Sibbald 1979 | ✓ PASS |
| Microgravity CVP > upright CVP | Clinical expectation | ✓ PASS |

Run `python3 tests/stress_test_literature.py` to reproduce.

---

## Limitations

This model is a work in progress. The following limitations are known and documented for transparency:

### Venous muscle pump not implemented
The most significant current limitation. In a standing, conscious patient, calf muscle contractions act as a peripheral heart — compressing the deep leg veins and returning 200–400 mL of blood to the central circulation per minute. Without this, the model underestimates venous return in the upright position:

- Sjöstrand (1953) measured **640 mL** of lower-extremity venous pooling on standing in healthy conscious subjects.
- The current model produces **~220 mL** pooling at 90° (without muscle pump).
- For sedated/anesthetised patients in the validated clinical range (−30° to +30°), this is acceptable; the muscle pump is inactive under anaesthesia.
- **Future work:** implement a periodic calf compression model driven by heart rate or respiratory rate.

### Validated tilt range: −30° to +30°
At angles above ~35°, the lumped lower-body venous compartments cannot fully represent the distributed hydrostatic column without an active venous return mechanism. Simulations at steep upright angles (>35°) will show appropriate haemodynamic stress but will overestimate the degree of cardiovascular collapse compared to a conscious patient with intact muscle pump and vasomotor reflexes.

### Starling plateau approximation
The Frank-Starling plateau is implemented as a hard cap on E_max above EDV = 130 mL. In a fully normovolemic supine patient, 20° HDT should cause minimal SV change (as shown by Sørensen et al.). The model correctly shows the MAP direction (↑), but overestimates the SV/CO increase when the patient input MAP is below the baroreflex setpoint, because patient.py interprets this as mild hypovolemia.

### Single-compartment splanchnic and upper-body veins
Like the lower body, these could benefit from distributed height modelling for large tilt angles. Currently modelled as single lumped compartments.

### No respiratory-cardiovascular coupling
Intrathoracic pressure swings with breathing are not modelled. SVV (stroke volume variation) as a dynamic fluid responsiveness marker therefore cannot be computed.

---

## Iterative Development

This model did not emerge complete. Development has been openly iterative:

1. **Initial implementation** — 21-compartment ODE at rest; validated against normal resting haemodynamics.
2. **Hydrostatic sign correction** — the initial tilt implementation had inverted hydrostatic signs; corrected after comparing Trendelenburg response to Sibbald 1979 data.
3. **Frank-Starling plateau** — initial linear Starling relationship caused a 34% SV increase with 20° HDT in normovolemic subjects; plateau cap added after comparison with Sørensen 2022.
4. **3-compartment venous split** — single lower body vein compartment could only pool 73 mL at 90° upright; split into foot/calf/thigh after comparison with Sjöstrand 1953 (640 mL target); improved to ~220 mL.
5. **Initial condition calibration** — init_volumes were initially set at P = 8–10 mmHg; analytical calculation of steady-state venous pressures (~12–14 mmHg) required to prevent a large initial transient that drained central circulation.

Each iteration is documented in the git history.

---

## Contributing

Contributions are welcome — particularly:

- **Venous muscle pump model** (calf compression, valves, respiratory coupling)
- **Additional vasopressor pharmacology** (dobutamine, milrinone)
- **Expanded validation scenarios** (prone positioning, sitting, post-induction hypotension)
- **Parameter fitting from patient monitor data** (improve `patient.py` Tier 3)

Please open an issue before starting a large change.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Citation

If you use this model in research or clinical development, please cite:

```
Moelgaard J et al. Cardiovascular System Simulator (open source).
GitHub: https://github.com/moelgaardjesper/vascular-model
Based on: Heldt T et al. (2002) J Appl Physiol 92:1239-1254
          PMC9363491 — Mohammadyari et al., Sci Rep 2022
```
