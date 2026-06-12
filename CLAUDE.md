# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A 23-compartment lumped-parameter cardiovascular simulator for clinical use.  
Models blood pressure dynamics, cardiac output, and fluid shifts under:
- Intraoperative posture changes (Trendelenburg, reverse Trendelenburg)
- Vasopressor administration (norepinephrine, phenylephrine, vasopressin, epinephrine)
- Reduced gravity (Mars, Moon, microgravity)

Inputs scale from minimal (MAP + BMI) to full intracardiac monitoring (CO, CVP, PCWP, PAP).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/

# Run a single test
pytest tests/test_circulation.py::test_resting_baseline -v

# Start the web server (opens at http://localhost:5000)
python -m api.app
```

## Architecture

```
model/
  compartments.py   23 compartments (index 0-22), Compartment dataclass, IDX dict
  heart.py          Time-varying elastance (Suga-Sagawa), Frank-Starling scaling
  gravity.py        Hydrostatic pressure correction: ρgh·sin(α); smooth tilt profile
  baroreflex.py     BaroreflexController — 4-step ABR+CPR, impulse response convolution
  pharmacology.py   Hill-equation PD for NE, phenylephrine, vasopressin, epinephrine
  patient.py        Allometric parameter scaling (BSA/Mosteller), 3-tier calibration
  circulation.py    ODE system (_odes), SimParams, run_simulation() — main entry point

api/
  app.py            Flask factory, serves frontend/
  routes.py         POST /api/simulate, GET /api/defaults, POST /api/estimate

frontend/
  index.html        Single-page UI (Plotly.js, no build step)
  js/main.js        Form collection, fetch, chart rendering
```

### Key data flow

1. `build_patient_params()` in `patient.py` scales compartments from clinical inputs.
2. Caller fills a `SimParams` and passes it to `run_simulation()`.
3. `run_simulation()` steps the ODE with Euler integration (dt = 1 ms), updating the `BaroreflexController` every step.
4. Results (time-series pressures, flows, HR) are returned as a dict and serialised to JSON by the Flask route.

### Compartment index order

See `IDX` dict in `compartments.py`. Cardiac chambers: RA=15, RV=16, LA=20, LV=21.  
State vector `V[0..22]` stores volumes in mL. Pressures are derived at every step — not stored in the state.

### Adding a new intervention

1. Add a PD function to `pharmacology.py` returning the standard `{svr_factor, hr_factor, ...}` dict.
2. Register it in `combined_drug_factors()`.
3. Add a UI input in `frontend/index.html` and wire it in `buildPayload()` in `js/main.js`.

## References

- PMC9363491 — primary model basis (21-compartment orthostatic stress model, Heldt-based; expanded to 23 compartments here)  
- Heldt T et al. (2002) J Appl Physiol 92:1239-1254 — foundational lumped-parameter model  
- DOI 10.1038/s41598-022-18831-3 — VoM-PhyS: 3D multiscale blood-flow and heat transfer  
- VaMpy (JORS): https://openresearchsoftware.metajnl.com/articles/10.5334/jors.159 — 1D arterial wave model
