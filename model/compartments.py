"""
Vascular compartment definitions for the lumped-parameter cardiovascular model.

Based on the 21-compartment structure from:
  Heldt T et al. (2002) J Appl Physiol 92:1239-1254
  PMC9363491 — cardiovascular model for orthostatic stress / spaceflight
"""

from dataclasses import dataclass, field


@dataclass
class Compartment:
    """
    One lumped vascular compartment.

    Parameters
    ----------
    name : str
    compliance : float
        mL/mmHg — relates stressed volume to pressure
    resistance : float
        mmHg·s/mL — outflow resistance to the next compartment
    unstressed_volume : float
        mL — volume at zero transmural pressure
    height_m : float
        metres above heart level (negative = below heart).
        Used to compute the hydrostatic pressure column when tilted.
    init_volume : float
        mL — initial volume for ODE state vector (defaults to unstressed_volume)
    """

    name: str
    compliance: float       # mL/mmHg
    resistance: float       # mmHg·s/mL  (outflow to next compartment)
    unstressed_volume: float  # mL
    height_m: float = 0.0   # metres from heart level
    init_volume: float = field(default=None)

    def __post_init__(self):
        if self.init_volume is None:
            self.init_volume = self.unstressed_volume

    def pressure(self, volume: float) -> float:
        """Transmural pressure from stressed volume (mmHg)."""
        return (volume - self.unstressed_volume) / self.compliance


# ---------------------------------------------------------------------------
# Cardiac valve resistance (mmHg·s/mL).
# Must satisfy: VALVE_R * C_min > dt for Euler stability.
# With C_min = 0.05 and dt = 0.001 s → VALVE_R > 0.02.
# ---------------------------------------------------------------------------
# VALVE_R must satisfy: VALVE_R * C_aorta > dt for Euler stability at dt=0.001 s.
# With C_aorta=0.50 → need VALVE_R > 0.002 s. Using 0.08 limits peak valve flow
# to ~500 mL/s (physiological) and keeps LV-aortic ΔP ≈ 40 mmHg during ejection.
VALVE_R = 0.08


# ---------------------------------------------------------------------------
# Baseline 21-compartment parameter set
# Compartment order (indices 0-20) matches circulation.py state vector.
#
# Parameter values from Heldt 2002 Table 1 and PMC9363491 Supplementary.
# Heights measured from heart centroid in supine (horizontal) reference:
#   positive = head-ward, negative = foot-ward.
# ---------------------------------------------------------------------------

def default_compartments() -> list[Compartment]:
    """
    Return the 21 baseline compartments in canonical index order.

    Parameters calibrated to reproduce resting haemodynamics:
      MAP ≈ 90 mmHg, CO ≈ 5 L/min, CVP ≈ 5 mmHg, HR = 70 bpm
      SVR_target = (MAP-CVP)/CO = 1.02 mmHg·s/mL
      Total arterial C ≈ 1.5 mL/mmHg → Windkessel τ = C·SVR ≈ 1.5 s
        → DBP ≈ SBP·exp(-T_dia/τ) ≈ 120·exp(-0.57/1.5) = 82 mmHg ✓

    init_volume gives physiological resting pressure in each compartment:
      Arterial: P₀ ≈ 90 mmHg  → V_init = V0 + P₀·C
      Venous:   P₀ ≈ 8 mmHg   → V_init = V0 + P₀·C
      Cardiac (elastance model): V_init = V0 + P₀/E_min
    """
    return [
        # idx  name                    C(mL/mmHg)  R(mmHg·s/mL)   V0(mL)  h(m)   init_vol(mL)
        # ---- Systemic arterial (large compliant vessels + arterioles) ----
        Compartment("aorta",               0.50, 0.05,  100,  0.05,  145),  # 0  P0=90
        Compartment("brachiocephalic",     0.12, 0.05,   30,  0.15,   41),  # 1  P0=91
        Compartment("upper_body_art",      0.25, 3.80,   50,  0.25,   72),  # 2  P0=88 (arterioles)
        Compartment("upper_body_vein",     1.30, 0.15,  300,  0.20,  309),  # 3  P0≈7
        Compartment("svc",                 0.40, 0.05,   70,  0.15,   72),  # 4  P0=5
        Compartment("abdominal_aorta",     0.25, 0.05,   60, -0.10,   82),  # 5  P0=88
        Compartment("renal_art",           0.05, 4.60,   20, -0.10,   24),  # 6  P0=80 (arterioles)
        Compartment("renal_vein",          0.35, 0.25,   60, -0.10,   63),  # 7  P0≈9
        Compartment("splanchnic_art",      0.12, 3.70,   50, -0.15,   60),  # 8  P0=83 (arterioles)
        Compartment("splanchnic_vein",     3.50, 0.18,  700, -0.15,  728),  # 9  P0=8
        Compartment("lower_body_art",      0.35, 2.80,   80, -0.50,  111),  # 10 P0=89 (arterioles)
        Compartment("lower_body_vein",     4.00, 0.30,  900, -0.45,  940),  # 11 P0=10
        Compartment("ivc",                 0.60, 0.04,  120, -0.15,  123),  # 12 P0=5
        # ---- Cardiac chambers (elastance model; R = valve resistance) ----
        Compartment("right_atrium",        0.35, VALVE_R,  60,  0.0,  131),  # 13 EDV fills to ~5 mmHg
        Compartment("right_ventricle",     0.10, VALVE_R,  80,  0.0,  180),  # 14 EDV≈180 mL
        # ---- Pulmonary (PVR ≈ 0.08 mmHg·s/mL) ----
        Compartment("pulmonary_art",       0.40, 0.03,  100,  0.0,  106),  # 15 P0=15
        Compartment("pulmonary_cap",       0.50, 0.06,   80,  0.0,   85),  # 16 P0=10
        Compartment("pulmonary_vein",      0.80, 0.02,  160,  0.0,  168),  # 17 P0=10
        # ---- Left heart ----
        Compartment("left_atrium",         0.20, VALVE_R,  45,  0.0,  145),  # 18 EDP≈9
        Compartment("left_ventricle",      0.08, VALVE_R,  60,  0.0,  160),  # 19 EDV≈160
        # ---- Coronary ----
        Compartment("coronary",            0.10, 15.0,   20,  0.05,   21),  # 20 flow≈0.3 L/min
    ]


# Compartment index constants for readable cross-references
IDX = {c.name: i for i, c in enumerate(default_compartments())}
