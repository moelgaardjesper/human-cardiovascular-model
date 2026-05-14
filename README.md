# Vascular Model Simulator

A 21-compartment lumped-parameter cardiovascular simulator for clinical and research use. Predicts blood pressure dynamics, cardiac output, and fluid shifts during intraoperative and physiological interventions — from simple inputs (MAP + BMI) up to full intracardiac monitoring.

## Use cases

- **Intraoperative posture changes** — Trendelenburg (−30° to +30°), reverse Trendelenburg, passive leg raising
- **Vasopressor titration** — norepinephrine, phenylephrine, vasopressin, epinephrine
- **Gravitational environments** — Earth, Mars, Moon, microgravity
- **Fluid responsiveness assessment** — predicts SV/CO response to preload manipulation

> **Microgravity and postoperative recovery share the same physiology.** Both eliminate orthostatic gravitational stress, causing fluid redistribution toward the thorax, altered baroreflex dynamics, and reduced lower-limb vascular tone. The model captures both contexts via the same gravity parameter.

## Quick start

```bash
pip install -r requirements.txt
python3 -m api.app        # opens at http://localhost:5000
pytest tests/             # run smoke tests
```

## Architecture

```
model/
  compartments.py   21-compartment parameter set (Compartment dataclass, IDX)
  heart.py          Time-varying elastance (Suga-Sagawa), Starling curve
  gravity.py        Hydrostatic correction: ρgh·sin(α) per compartment
  baroreflex.py     4-step ABR+CPR (arterial + cardiopulmonary reflex)
  pharmacology.py   Hill-equation PD: NE, phenylephrine, vasopressin, epi
  patient.py        Allometric scaling (BSA/Mosteller), 3-tier calibration
  circulation.py    ODE system, SimParams, run_simulation() entry point

api/
  app.py            Flask factory, serves frontend/
  routes.py         POST /api/simulate, GET /api/defaults, POST /api/estimate

frontend/
  index.html        Single-page UI (Plotly.js — no build step)
  js/main.js        Form collection, fetch, waveform rendering
```

### Patient input tiers

| Tier | Inputs | What gets estimated |
|------|--------|---------------------|
| 1 — Minimal | MAP, BMI/height/weight | All parameters via population scaling |
| 2 — Intermediate | + cardiac output, ABI | Arterial resistance, peripheral disease index |
| 3 — Advanced | + CVP, PCWP, mean PAP | Full intracardiac calibration |

## Validation

Tested against published clinical data retrieved via PubMed:

| Scenario | Reference | Result |
|----------|-----------|--------|
| Supine resting (MAP, HR, SV, CO) | [DOI: 10.14814/phy2.15216](https://doi.org/10.14814/phy2.15216) | PASS |
| 20° HDT — normovolemic (SV/CO stable) | [DOI: 10.14814/phy2.15216](https://doi.org/10.14814/phy2.15216) | PASS |
| 6° HDT vs upright (MAP↓, HR↓) | [DOI: 10.1038/s41598-019-39360-6](https://doi.org/10.1038/s41598-019-39360-6) | PASS |
| −30° Trendelenburg (CVP↑, MAP↑) | Clinical expectation | PASS |
| Microgravity CVP > upright CVP | Clinical expectation | PASS |

Run the validation suite: `python3 tests/stress_test_literature.py`

### Known limitations

- **Extreme upright posture (>60°):** The lumped lower-body venous compartment cannot represent the distributed hydrostatic column at 90° standing. Baroreflex compensation is underestimated. Model is validated for −30° to +45°.
- **Starling plateau:** Implemented as a hard cap above EDV = 130 mL. The linear ESV–EDV relationship still allows a small SV increase above the cap. A sigmoid Starling curve would better represent normovolemic plateau behaviour.

## References

**Model basis:**

- Heldt T, Shim EB, Kamm RD, Mark RG. *Computational modeling of cardiovascular response to orthostatic stress.* J Appl Physiol. 2002;92(3):1239–1254. — foundational 21-compartment lumped-parameter model
- PMC9363491 — Mohammadyari et al. *Cardiovascular model for orthostatic stress / Mars mission planning.* Sci Rep 2022. — 21-compartment implementation with hydrostatic tilt and baroreflex; primary basis for this model's parameter set and compartment topology

**Validation data (retrieved via PubMed):**

- Sørensen et al. [DOI: 10.14814/phy2.15216](https://doi.org/10.14814/phy2.15216) (PMID: 35854636) — HDT vs PLR in healthy volunteers; Starling plateau validation
- Verdini et al. [DOI: 10.1038/s41598-019-39360-6](https://doi.org/10.1038/s41598-019-39360-6) (PMID: 30808948) — cardiovascular responses to leg muscle loading during HDT; tilt direction validation

**Related work:**

- [DOI: 10.1038/s41598-022-18831-3](https://doi.org/10.1038/s41598-022-18831-3) — VoM-PhyS: 3D multiscale vascular heat/flow framework
- VaMpy (JORS): [https://openresearchsoftware.metajnl.com/articles/10.5334/jors.159](https://openresearchsoftware.metajnl.com/articles/10.5334/jors.159) — 1D arterial wave propagation model
