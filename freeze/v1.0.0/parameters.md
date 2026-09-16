# Frozen parameter set

Introspected from the modules at the freeze commit — not a transcribed list.
A parameter added to the model appears here without anyone editing this tool.


## The 23 compartments

Fields are every field of the `Compartment` dataclass, in declaration order.

| idx | name | compliance | resistance | unstressed_volume | height_m | init_volume | p_stiffen | drain_resistance |
|---|---|---|---|---|---|---|---|---|
| 0 | aorta | 0.8 | 0.05 | 100 | 0.05 | 165 | — | 0.05 |
| 1 | brachiocephalic | 0.19 | 0.05 | 30 | 0.15 | 45 | — | 0.05 |
| 2 | upper_body_art | 0.4 | 0.1 | 50 | 0.25 | 81 | — | 0.1 |
| 3 | upper_body_vein | 12 | 3.75 | 764 | 0.05 | 850 | — | 0.1 |
| 4 | svc | 8 | 0.05 | 70 | 0.05 | 123 | — | 0.04 |
| 5 | abdominal_aorta | 0.4 | 0.05 | 60 | -0.1 | 91 | — | 0.05 |
| 6 | renal_art | 0.08 | 0.1 | 20 | -0.1 | 26 | — | 0.1 |
| 7 | renal_vein | 7.2 | 4.5 | 60 | -0.1 | 135 | — | 0.2 |
| 8 | splanchnic_art | 0.19 | 0.1 | 50 | -0.15 | 65 | — | 0.1 |
| 9 | splanchnic_vein | 52 | 3.6 | 542 | -0.08 | 1064 | — | 0.14 |
| 10 | lower_body_art | 0.56 | 0.3 | 80 | -0.5 | 123 | — | 0.3 |
| 11 | thigh_vein | 3.2 | 9.033 | 381 | -0.2 | 420 | 12 | 0.6 |
| 12 | calf_vein | 4.8 | 6.95 | 508 | -0.55 | 568 | 11 | 0.1 |
| 13 | foot_vein | 4 | 9.263 | 254 | -0.85 | 298 | 8 | 0.14 |
| 14 | ivc | 12 | 0.04 | 120 | -0.15 | 197 | — | 0.04 |
| 15 | right_atrium | 0.35 | 0.01 | 16 | 0 | 33 | — | 0.01 |
| 16 | right_ventricle | 0.1 | 0.01 | 38 | 0 | 160 | — | 0.01 |
| 17 | pulmonary_art | 6 | 0.01 | 100 | 0 | 179 | — | 0.01 |
| 18 | pulmonary_cap | 2.5 | 0.06 | 80 | 0 | 105 | — | 0.06 |
| 19 | pulmonary_vein | 4 | 0.02 | 160 | 0 | 197 | — | 0.02 |
| 20 | left_atrium | 0.2 | 0.01 | 15 | 0 | 38 | — | 0.01 |
| 21 | left_ventricle | 0.08 | 0.01 | 10 | 0 | 138 | — | 0.01 |
| 22 | coronary | 0.1 | 15 | 20 | 0.05 | 21 | — | 15 |

Total initial volume **5122.0 mL**, of which **3528.0 mL** unstressed (68.9 %) and **1594.0 mL** stressed (31.1 %).


## Model constants, by module

A constant that first appears in an earlier module and is imported by a later one is marked *re-export*. The model holds ONE definition; the label tells you which module owns it.


### `model.heart`

| constant | value |
|---|---|
| `ATRIAL_PR_INTERVAL_S` | 0.16 |
| `LA_EMAX` | 0.45 |
| `LA_EMIN` | 0.19 |
| `LV_EMAX` | 3 |
| `LV_EMIN` | 0.055 |
| `RA_EMAX` | 0.45 |
| `RA_EMIN` | 0.2 |
| `RV_EMAX` | 0.72 |
| `RV_EMIN` | 0.04 |

### `model.baroreflex`

| constant | value |
|---|---|
| `CP_HR_GAIN_BPM_PER_MMHG` | 3.8 |
| `CP_HR_REFERENCE_CVP_MMHG` | 4.7 |
| `CP_HR_RESERVE_BPM` | 40 |
| `CVP_SETPOINT` | 3 |
| `HR_REFLEX_GAIN_BPM` | 30 |
| `HR_REFLEX_SCALE_MMHG` | 35 |
| `MAP_SETPOINT` | 93 |
| `PP_SETPOINT` | 40 |
| `REFERENCE_CO_LPM` | 5 |
| `REFERENCE_CVP_MMHG` | 5 |
| `REFERENCE_MAP_MMHG` | 93 |
| `_HR_VAGAL_FRACTION` | 0.45 |
| `_TAU_PARA` | 1.5 |
| `_TAU_SYMP_FAST` | 2 |
| `_TAU_SYMP_HR` | 5 |
| `_TAU_SYMP_SLOW` | 20 |

### `model.respiration`

| constant | value |
|---|---|
| `ABDOMINAL_TRANSMISSION` | 0.21 |
| `PLEURAL_TRANSMISSION` | 0.376 |
| `SPONTANEOUS_ITP_BASELINE_CMH2O` | -2 |
| `SPONTANEOUS_ITP_SWING_CMH2O` | -3.5 |
| `_CMHG_TO_MMHG` | 0.735 |

### `model.gravity`

| constant | value |
|---|---|
| `BLOOD_DENSITY` | 1060 |
| `MMHG_PER_PA` | 0.00750064 |

### `model.circulation`

| constant | value |
|---|---|
| `ABDOMINAL_TRANSMISSION` | 0.21 *(re-export from `model.respiration`)* |
| `AORTIC_R` | 0.01 |
| `LA_EMAX` | 0.45 *(re-export from `model.heart`)* |
| `LA_EMIN` | 0.19 *(re-export from `model.heart`)* |
| `LV_EMAX` | 3 *(re-export from `model.heart`)* |
| `LV_EMIN` | 0.055 *(re-export from `model.heart`)* |
| `MITRAL_R` | 0.01 |
| `PULMONIC_R` | 0.01 |
| `RA_EMAX` | 0.45 *(re-export from `model.heart`)* |
| `RA_EMIN` | 0.2 *(re-export from `model.heart`)* |
| `RV_EMAX` | 0.72 *(re-export from `model.heart`)* |
| `RV_EMIN` | 0.04 *(re-export from `model.heart`)* |
| `TRICUSPID_R` | 0.01 |
| `VALVE_DP_REG` | 0.1 |
| `_ABDOMINAL_IDX` | (5, 6, 7, 8, 9, 14) |
| `_ARREST_PHASE` | 0.9 |
| `_THORACIC_IDX` | (0, 1, 4, 22, 15, 16, 17, 18, 19, 20, 21) |

### `model.slow_dynamics`

| constant | value |
|---|---|
| `ADH_MAX_SVR_FRACTION` | 0.13 |
| `CAPILLARY_BEDS` | (('upper_body_art', 'upper_body_vein', 0.3), ('renal_art', 'renal_vein', 0.15), ('splanchnic_art', 'splanchnic_vein', 0.35), ('lower_body_art', 'thigh_vein', 0.2)) |
| `CAPILLARY_PRESSURE_FRACTION` | 0.2 |
| `EC50_ADH_MMHG` | 22 |
| `EC50_RAAS_MMHG` | 15 |
| `HAEMATOCRIT` | 0.45 |
| `HILL_N_NEUROHUMORAL` | 2 |
| `INTERSTITIAL_C_LOOSE` | 2000 |
| `INTERSTITIAL_C_STIFF` | 150 |
| `INTERSTITIAL_P_REST_MMHG` | -7 |
| `KF_TOTAL` | 0.111667 |
| `KF_TOTAL_ML_PER_MIN_MMHG` | 6.7 |
| `K_RELAX` | 0.428571 |
| `PLASMA_PROTEIN_G_PER_L` | 70 |
| `RAAS_MAX_SVR_FRACTION` | 0.15 |
| `RELAX_FRACTION` | 0.3 |
| `SETTLE_S` | 60 |
| `SIGMA_PROTEIN` | 0.9 |
| `SLOW_DT` | 0.1 |
| `TAU_ADH_S` | 600 |
| `TAU_LYMPH` | 3600 |
| `TAU_MAP_FILTER_S` | 10 |
| `TAU_PRESSURE_FILTER_S` | 5 |
| `TAU_RAAS_S` | 300 |
| `TAU_STRESS_RELAX` | 250 |
| `_V_TO_ATMOSPHERIC` | 1050 |

### `model.aging`

| constant | value |
|---|---|
| `ALHOGBANI_ACC` | ((32.0, 15.0), (47.5, 28.0), (65.0, 38.0)) |
| `FRANKLIN_PP_REFERENCE_MMHG` | 51.5 |
| `FRANKLIN_PP_SLOPE_MALE_NORMOTENSIVE` | 0.68 |
| `GAO_LAEF_BOOSTER_MEN` | ((25.5, 33.3), (35.5, 36.2), (45.5, 38.7), (55.5, 39.3), (65.5, 42.3)) |
| `GAO_LAEF_PASSIVE_MEN` | ((25.5, 39.9), (35.5, 39.0), (45.5, 35.6), (55.5, 29.4), (65.5, 28.5)) |
| `LUU_LVEDV_MEN` | ((39.5, 77.0), (49.5, 75.0), (59.5, 74.0), (69.5, 69.0)) |
| `LUU_LVEF_MEN` | ((39.5, 61.0), (49.5, 62.0), (59.5, 62.0), (69.5, 62.0)) |
| `LUU_LVESV_MEN` | ((39.5, 30.0), (49.5, 29.0), (59.5, 28.0), (69.5, 26.0)) |
| `LUU_RVEDV_MEN` | ((39.5, 91.0), (49.5, 88.0), (59.5, 86.0), (69.5, 80.0)) |
| `LUU_RVEF_MEN` | ((39.5, 51.0), (49.5, 53.0), (59.5, 53.0), (69.5, 54.0)) |
| `LUU_RVESV_MEN` | ((39.5, 45.0), (49.5, 42.0), (59.5, 41.0), (69.5, 37.0)) |
| `NORRE_A_VELOCITY_MEN` | ((30.0, 0.5), (50.0, 0.61), (68.0, 0.73)) |
| `NORRE_DECEL_TIME_MEN` | ((30.0, 179.8), (50.0, 186.6), (68.0, 217.5)) |
| `NORRE_EA_MEN` | ((30.0, 1.69), (50.0, 1.22), (68.0, 0.96)) |
| `NORRE_E_VELOCITY_MEN` | ((30.0, 0.79), (50.0, 0.72), (68.0, 0.67)) |
| `REFERENCE_AGE_YEARS` | 55 |
| `TANAKA_ARTERIAL_COMPLIANCE_SEDENTARY` | ((28.0, 1.0), (50.0, 0.55), (64.0, 0.55)) |

### `model.patient`

| constant | value |
|---|---|
| `BSA_REF` | 1.84466 |
| `BV_REF` | 5000 |
| `REFERENCE_AGE_YEARS` | 55 *(re-export from `model.aging`)* |
| `REFERENCE_CO_LPM` | 5 *(re-export from `model.baroreflex`)* |
| `REFERENCE_CVP_MMHG` | 5 *(re-export from `model.baroreflex`)* |
| `REFERENCE_MAP_MMHG` | 93 *(re-export from `model.baroreflex`)* |
| `REF_HEIGHT_CM` | 175 |
| `REF_WEIGHT_KG` | 70 |

### `model.perfusion`

| constant | value |
|---|---|
| `BLOOD_DENSITY` | 1060 *(re-export from `model.gravity`)* |
| `H_BRAIN_M` | 0.25 |
| `ICP_BASE` | 10 |
| `ICP_SLOPE` | 0.07 |
| `MMHG_PER_PA` | 0.00750064 *(re-export from `model.gravity`)* |

### `model.pharmacology`

| constant | value |
|---|---|
| `ALPHA1_POSTCAP_EC50` | 0.2 |
| `ALPHA1_POSTCAP_EMAX` | 2.6 |
| `ALPHA1_POSTCAP_HILL` | 1.6 |

### `model.compartments`

| constant | value |
|---|---|
| `AORTIC_R` | 0.01 *(re-export from `model.circulation`)* |
| `CAVOATRIAL_R` | 0.04 |
| `GORLIN_CONST` | 44.3 |
| `MITRAL_R` | 0.01 *(re-export from `model.circulation`)* |
| `PULMONIC_R` | 0.01 *(re-export from `model.circulation`)* |
| `TRICUSPID_R` | 0.01 *(re-export from `model.circulation`)* |
| `VALVE_DP_REG` | 0.1 *(re-export from `model.circulation`)* |
| `VALVE_R` | 0.01 |
| `VENOATRIAL_R` | 0.02 |
| `VENOUS_COMPLIANCE_SCALE` | 0.8 |
| `VENOUS_DRAINAGE_SCALE` | 2 |
