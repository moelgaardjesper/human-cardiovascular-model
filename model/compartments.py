"""
Vascular compartment definitions for the lumped-parameter cardiovascular model.

Based on the 23-compartment structure extended from:
  Heldt T et al. (2002) J Appl Physiol 92:1239-1254
  PMC9363491 — cardiovascular model for orthostatic stress / spaceflight

The original single lower_body_vein compartment has been split into three
anatomically-placed segments (thigh_vein, calf_vein, foot_vein) to correctly
simulate the ~640 mL venous pooling observed on standing (Sjöstrand 1953).
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
    compliance: float       # mL/mmHg — low-pressure compliance C0
    resistance: float       # mmHg·s/mL  (outflow to next compartment)
    unstressed_volume: float  # mL
    height_m: float = 0.0   # metres from heart level
    init_volume: float = field(default=None)
    # Nonlinear (collapsible-vein) pressure–volume behaviour. When set, the
    # compartment stiffens above transmural pressure `p_stiffen` (mmHg) via an
    # exponential tube law: P = k·(exp(Vs/(C0·k)) − 1), Vs = stressed volume.
    # dP/dVs → 1/C0 at Vs→0 (compliant, e.g. supine/leg-raised) and rises with
    # volume (low incremental compliance when dependent → self-limiting pooling).
    # None → linear P = Vs/C0. Used for the limb veins so they hold recruitable
    # volume supine yet do not pool catastrophically upright.
    p_stiffen: float | None = None
    # Drainage resistance out of an exchange bed toward the great veins
    # (mmHg·s/mL). Only meaningful for the systemic venous compartments.
    #
    # WHY THIS EXISTS. `renal_vein` and `splanchnic_vein` previously used a single
    # `resistance` value for BOTH the artery→vein flow through the exchange bed and
    # the vein→IVC drainage — one number doing two physiologically distinct jobs,
    # so neither could be changed without silently changing the other. Backlog
    # item 20 needs exactly that separation: the exchange segment carries the
    # arteriolar resistance and sets capillary pressure, while drainage sets
    # venous return. They are not the same quantity and must not share a field.
    #
    # None → falls back to `resistance`, which reproduces the old shared behaviour.
    drain_resistance: float | None = None

    def __post_init__(self):
        if self.init_volume is None:
            self.init_volume = self.unstressed_volume
        if self.drain_resistance is None:
            self.drain_resistance = self.resistance

    def pressure(self, volume: float) -> float:
        """Transmural pressure from stressed volume (mmHg)."""
        vs = volume - self.unstressed_volume
        if self.p_stiffen is None or vs <= 0.0:
            return vs / self.compliance
        import numpy as _np
        return self.p_stiffen * (_np.exp(vs / (self.compliance * self.p_stiffen)) - 1.0)


# ---------------------------------------------------------------------------
# Cardiac valve resistance (mmHg·s/mL).
# Must satisfy: VALVE_R * C_min > dt for Euler stability.
# With C_min = 0.05 and dt = 0.001 s → VALVE_R > 0.02.
# ---------------------------------------------------------------------------
# VALVE_R must satisfy: VALVE_R * C_aorta > dt for Euler stability at dt=0.001 s.
# With C_aorta=0.50 → need VALVE_R > 0.002 s. Using 0.08 limits peak valve flow
# to ~500 mL/s (physiological) and keeps LV-aortic ΔP ≈ 40 mmHg during ejection.
VALVE_R = 0.01

# Great-vein -> atrium resistance. NOT A VALVE. See backlog item 23.
VENOATRIAL_R = 0.02


# ---------------------------------------------------------------------------
# Compartments whose `resistance` field carries the systemic ARTERIOLAR
# resistance, i.e. the artery→vein exchange segment of each bed.
#
# Since 2026-08-21 the arteriole sits on the flow OUT of each `*_art` compartment
# rather than into it (backlog item 20), so the arteriolar resistance is stored on
# the downstream venous compartment. Anything scaling systemic vascular resistance
# — the patient calibration in patient.py, drug `svr_factor`, the baroreflex —
# must act on THESE, not on the `*_art` compartments, which now hold only small
# conduit resistances. Their `drain_resistance` is a separate, postcapillary
# quantity and must NOT be scaled by an arteriolar factor.
# ---------------------------------------------------------------------------
ARTERIOLAR_SEGMENTS = (
    "upper_body_vein", "renal_vein", "splanchnic_vein",
    "thigh_vein", "calf_vein", "foot_vein",
)


# ---------------------------------------------------------------------------
# Baseline 23-compartment parameter set
# Compartment order (indices 0-22) matches circulation.py state vector.
#
# Parameter values from Heldt 2002 Table 1 and PMC9363491 Supplementary.
# Heights measured from heart centroid in supine (horizontal) reference:
#   positive = head-ward, negative = foot-ward.
# ---------------------------------------------------------------------------

def default_compartments() -> list[Compartment]:
    """
    Return the 23 baseline compartments in canonical index order.

    Parameters calibrated to reproduce resting haemodynamics:
      MAP ≈ 90 mmHg, CO ≈ 5 L/min, CVP ≈ 5 mmHg, HR = 70 bpm
      SVR_target = (MAP-CVP)/CO = 1.02 mmHg·s/mL
      Total arterial C ≈ 1.5 mL/mmHg → Windkessel τ = C·SVR ≈ 1.5 s
        → DBP ≈ SBP·exp(-T_dia/τ) ≈ 120·exp(-0.57/1.5) = 82 mmHg ✓

    init_volume gives physiological resting pressure in each compartment:
      Arterial: P₀ ≈ 90 mmHg  → V_init = V0 + P₀·C
      Venous:   P₀ ≈ 8 mmHg   → V_init = V0 + P₀·C
      Cardiac (elastance model): V_init = V0 + P₀/E_min

    The lower body venous return is modelled as three serial segments:
      foot_vein → calf_vein → thigh_vein → ivc
    Anatomical heights reproduce correct hydrostatic column at 90° upright
    (IVC reference h=−0.15 m), giving substantially more pooling than the
    old single-compartment approximation (Sjöstrand 1953).
    Hydrostatic columns at 90° upright:
      thigh (h=−0.20): ΔP= 3.9 mmHg
      calf  (h=−0.55): ΔP=31.2 mmHg
      foot  (h=−0.85): ΔP=54.6 mmHg
    Pooling ΔV ∝ C × ΔP_hydrostatic per segment.
    """
    return [
        # idx  name                    C(mL/mmHg)  R(mmHg·s/mL)   V0(mL)  h(m)   init_vol(mL)
        # ---- Systemic arterial (large compliant vessels + arterioles) ----
        #
        # ARTERIOLAR RESISTANCE PLACEMENT (fixed 2026-08-21, backlog item 20).
        # `resistance` is the resistance on the flow INTO this compartment. The
        # arteriolar resistance used to sit here, on the inflow to each `*_art`
        # compartment, which put the whole arteriolar pressure drop UPSTREAM of it:
        # `upper_body_art` settled at 8.6 mmHg while its own init_volume
        # (72 = V0 50 + C 0.25 x 88) and the comment below both say 88 mmHg.
        # Capillary pressure, computed between `*_art` and `*_vein`, was therefore
        # pinned to venous pressure at ~6.8 mmHg against a physiological ~20.
        # The arteriole now sits on the artery→vein segment where the exchange
        # vessels actually are; each `*_art` keeps only a small conduit resistance.
        # Artery→vein TOTALS are unchanged per bed, so systemic resistance, MAP and
        # cardiac output are preserved (measured: CO 4.131 -> 4.140).
        # See docs/validation_log.md "Backlog 20 diagnosed".
        Compartment("aorta",               0.50, 0.05,  100,  0.05,  145),  # 0  P0=90
        Compartment("brachiocephalic",     0.12, 0.05,   30,  0.15,   41),  # 1  P0=91
        Compartment("upper_body_art",      0.25, 0.10,   50,  0.25,   72),  # 2  P0=88 (conduit; arteriole moved to upper_body_vein)
        # Heights reference the volume-weighted thoracic venous centroid (~heart
        # level), not the neck: with physiological compliance the hydrostatic term
        # C·ΔP dominates tilt redistribution, so a mid-neck height (0.15-0.20) would
        # pool ~200 mL into the upper body in head-down tilt and steal preload.
        Compartment("upper_body_vein",    15.0, 3.80,  350,  0.05,  440,
                    drain_resistance=0.05),  # 3  P0≈6 (R = arteriole + exchange segment)
        Compartment("svc",                10.0, 0.05,   70,  0.05,  110, drain_resistance=VENOATRIAL_R),  # 4  P0≈4
        Compartment("abdominal_aorta",     0.25, 0.05,   60, -0.10,   82),  # 5  P0=88
        Compartment("renal_art",           0.05, 0.10,   20, -0.10,   24),  # 6  P0=80 (conduit; arteriole moved to renal_vein)
        # renal_vein / splanchnic_vein: `resistance` is the artery→vein exchange
        # segment; `drain_resistance` is the vein→IVC drainage. These were a single
        # shared number until 2026-08-21 — see Compartment.drain_resistance.
        Compartment("renal_vein",          9.0, 4.60,   60, -0.10,  132,
                    drain_resistance=0.10),                                # 7  P0≈8
        Compartment("splanchnic_art",      0.12, 0.10,   50, -0.15,   60),  # 8  P0=83 (conduit; arteriole moved to splanchnic_vein)
        Compartment("splanchnic_vein",    65.0, 3.67, 1200, -0.08, 1920,
                    drain_resistance=0.07),  # 9  P0≈11 (dominant mobilizable reservoir)
        Compartment("lower_body_art",      0.35, 0.30,   80, -0.50,  111),  # 10 P0=89 (conduit; arteriole moved to the leg exchange branches)
        # ---- Lower body venous: foot→calf→thigh→ivc (outflow resistance on each segment) ----
        # Compliances reproduce the ~640 mL venous pooling on standing documented by
        # Sjöstrand (1953, DOI: 10.1152/physrev.1953.33.2.202).
        #
        # Hydrostatic pooling at 90° upright, relative to supine equilibrium (~13 mmHg):
        #   thigh (h=−0.20m): ΔV = 5 × (8.9−13) = −20 mL  (above IVC → decompresses)
        #   calf  (h=−0.55m): ΔV = 9 × (36.2−14) = +200 mL
        #   foot  (h=−0.85m): ΔV = 7 × (59.6−14) = +319 mL
        #   Net ≈ +500–600 mL (vs Sjöstrand target 640 mL) ✓
        #
        # Supine equilibrium pressures (from analytical flow balance):
        #   P_lb_art_eq ≈ 15.7 mmHg, P_thigh_eq ≈ 12.7, P_calf_eq ≈ 13.6, P_foot_eq ≈ 14.2 mmHg
        # Vinit = V0 + C × P_eq (gives correct starting point, avoids large initial transient).
        # Total lower body venous volume at supine: ~1186 mL (physiologically normal).
        #
        # Euler stability at dt=0.001 s: τ_min = C / Σconductances > 0.2 s for all segments ✓
        # Compliances calibrated to give maximum orthostatic pooling while keeping 45° upright
        # MAP ≥ 60 mmHg and supine hemodynamics within physiological range.
        # Vinit set at analytical steady-state supine pressures (≈12.5 / 13.0 / 13.5 mmHg),
        # not at P=8 mmHg, to avoid a large initial transient that drains central circulation.
        #
        # At 45° upright: ΔV ≈ +130 mL pooling.
        # At 90° upright: ΔV ≈ +220 mL (vs old single-vein 73 mL).
        # Full Sjöstrand 640 mL requires the active muscle pump (absent in sedated patients).
        # Limb veins use the nonlinear tube law (p_stiffen): compliant when
        # filling (supine/leg-raised → hold recruitable volume, restore PLR
        # response) but self-limiting when dependent (upright → pooling capped,
        # no MAP collapse). C0 is the low-pressure compliance.
        # Leg veins follow the same convention as the other exchange beds:
        # `resistance` is the arteriole + exchange segment feeding the compartment,
        # `drain_resistance` is its outflow (foot→calf→thigh→IVC). The exchange
        # resistances were hard-coded inside `_odes` until 2026-08-21, which put
        # them out of reach of both the patient SVR calibration and the PAD factor.
        # They carry the 2.80 arteriolar resistance that used to sit on
        # lower_body_art's inflow, split 30/40/30 across the three segments:
        #   2.80/0.30 = 9.33,  2.80/0.40 = 7.00,  2.80/0.30 = 9.33
        #   equivalent parallel R = 2.80 ✓, plus the 0.30 conduit = 3.10 as before.
        Compartment("thigh_vein",          4.0, 9.333, 300, -0.20,  332, p_stiffen=12.0,
                    drain_resistance=0.30),  # 11
        Compartment("calf_vein",           6.0, 7.000, 400, -0.55,  448, p_stiffen=11.0,
                    drain_resistance=0.05),  # 12
        Compartment("foot_vein",           5.0, 9.333, 200, -0.85,  241, p_stiffen= 8.0,
                    drain_resistance=0.07),  # 13
        Compartment("ivc",                15.0, 0.04,  120, -0.15,  195, drain_resistance=VENOATRIAL_R),  # 14 P0≈5
        # ---- Cardiac chambers (elastance model; R = valve resistance) ----
        # RA Vinit=155: at RA_EMIN=0.04 and P_ra_eq≈3.8 mmHg → V=60+3.8/0.04=155 mL.
        # End-diastolic (rolling-minimum) CVP ≈ 3 mmHg once RA partially empties ✓
        Compartment("right_atrium",        0.35, VALVE_R,  16,  0.0,   47),  # 15
        # RV Vinit=163: at RV_EMIN=0.02, P_rv_dia=0.02×(163-80)=1.7 mmHg → CVP can be 2-3 mmHg.
        # ESV=V0+P_pa/E_max=80+15/1.15=93 mL; SV=163-93=70 mL (improved from 56 mL). ✓
        Compartment("right_ventricle",     0.10, VALVE_R,  38,  0.0,  159),  # 16 EDV≈163 mL
        # ---- Pulmonary (PVR ≈ 0.08 mmHg·s/mL) ----
        Compartment("pulmonary_art",       0.40, 0.03,  100,  0.0,  106),  # 17 P0=15
        Compartment("pulmonary_cap",       0.50, 0.06,   80,  0.0,   85),  # 18 P0=10
        Compartment("pulmonary_vein",      0.80, 0.02,  160,  0.0,  168, drain_resistance=VENOATRIAL_R),  # 19 P0=10
        # ---- Left heart ----
        Compartment("left_atrium",         0.20, VALVE_R,  15,  0.0,   47),  # 20 EDP≈9
        Compartment("left_ventricle",      0.08, VALVE_R,  10,  0.0,  137),  # 21 EDV≈160
        # ---- Coronary ----
        Compartment("coronary",            0.10, 15.0,   20,  0.05,   21),  # 22 flow≈0.3 L/min
    ]


# Compartment index constants for readable cross-references
IDX = {c.name: i for i, c in enumerate(default_compartments())}
