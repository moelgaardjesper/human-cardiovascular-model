#!/usr/bin/env python3
"""Generate anatomical cardiovascular compartment diagram (PNG + SVG).

Outputs: compartment_diagram.png and compartment_diagram.svg in the repo root.
Run: python3 tools/generate_diagram.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Ellipse
from matplotlib.path import Path
import matplotlib.patheffects as pe
import numpy as np

# ── colours ──────────────────────────────────────────────────────────────────
ART   = '#b91c1c'    # arterial red
VEIN  = '#1d4ed8'    # venous blue
HEART = '#7c3aed'    # cardiac purple
LUNG  = '#0891b2'    # pulmonary teal
COR   = '#d97706'    # coronary amber

BG_UPPER  = '#fef2f2'   # head/upper — light red
BG_THORAX = '#eff6ff'   # thorax    — light blue
BG_ABD    = '#f0fdf4'   # abdomen   — light green
BG_LOWER  = '#fafaf9'   # lower     — off-white

LABEL_COL = '#111827'
REGION_LABEL_COL = '#6b7280'
ARROW_GRAY = '#374151'

# ── canvas ───────────────────────────────────────────────────────────────────
W, H = 11, 16          # inches
fig, ax = plt.subplots(figsize=(W, H))
ax.set_xlim(0, W); ax.set_ylim(0, H)
ax.set_aspect('equal'); ax.axis('off')
fig.patch.set_facecolor('white')

# ── anatomical region backgrounds ────────────────────────────────────────────
def region_bg(y0, y1, color, label, label_x=0.55):
    ax.fill_between([0.3, W - 0.3], [y0, y0], [y1, y1],
                    color=color, alpha=0.55, zorder=0)
    ax.text(label_x, (y0 + y1) / 2, label,
            ha='left', va='center', fontsize=7.5, color=REGION_LABEL_COL,
            fontstyle='italic', zorder=1)

region_bg(12.0, 15.4, BG_UPPER,  'Head &\nUpper\nBody',     0.38)
region_bg(7.6,  12.0, BG_THORAX, 'Thorax',                  0.38)
region_bg(4.2,   7.6, BG_ABD,    'Abdomen',                  0.38)
region_bg(0.4,   4.2, BG_LOWER,  'Lower\nExtremities',       0.38)

# ── helper: draw compartment box ─────────────────────────────────────────────
def box(cx, cy, label, color, w=1.65, h=0.52, fs=8.2, alpha=0.93):
    b = FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                        boxstyle='round,pad=0.07',
                        facecolor=color, edgecolor='white',
                        linewidth=1.8, alpha=alpha, zorder=3)
    ax.add_patch(b)
    ax.text(cx, cy, label, ha='center', va='center',
            fontsize=fs, color='white', fontweight='bold', zorder=4,
            multialignment='center')
    return (cx, cy)

# ── helper: arrow between two boxes ──────────────────────────────────────────
def arr(x1, y1, x2, y2, color=ARROW_GRAY, lw=1.4, rad=0.0, dashes=None):
    style = f'arc3,rad={rad}'
    props = dict(arrowstyle='-|>', color=color, lw=lw,
                 connectionstyle=style, mutation_scale=13)
    if dashes:
        props['linestyle'] = (0, dashes)
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=props, zorder=2)

# ── helper: straight line (for IVC / Aorta column) ───────────────────────────
def vline(x, y0, y1, color, lw=2.2, dashes=None):
    ls = '--' if dashes else '-'
    ax.plot([x, x], [y0, y1], color=color, lw=lw, ls=ls, zorder=2,
            solid_capstyle='round')

def hline(x0, x1, y, color, lw=2.2):
    ax.plot([x0, x1], [y, y], color=color, lw=lw, zorder=2,
            solid_capstyle='round')

def arrow_on_line(x, y, dx, dy, color, size=0.18):
    """Small arrowhead marker on a line segment."""
    ax.annotate('', xy=(x+dx, y+dy), xytext=(x-dx, y-dy),
                arrowprops=dict(arrowstyle='-|>', color=color,
                                lw=0, mutation_scale=11), zorder=2)

# ─────────────────────────────────────────────────────────────────────────────
# PLACE COMPARTMENTS
# Left column  (x≈2.3): veins
# Right column (x≈8.7): arteries
# Centre-left  (x≈4.1): right heart
# Centre-right (x≈6.9): left heart / aortic
# ─────────────────────────────────────────────────────────────────────────────

LX  = 2.3    # vein column x
RX  = 8.7    # artery column x
HLX = 4.1    # right-heart x
HRX = 6.9    # left-heart x
PLX = 3.1    # pulmonary-left x
PRX = 7.9    # pulmonary-right x
PCX = 5.5    # pulmonary-cap x

# ── Pulmonary circuit (thorax, top) ──────────────────────────────────────────
P_PA   = box(PLX,  11.35, 'Pulmonary\nArtery',      LUNG)
P_PCAP = box(PCX,  11.80, 'Pulmonary\nCapillaries', LUNG)
P_PV   = box(PRX,  11.35, 'Pulmonary\nVein',        LUNG)

# ── Right heart ──────────────────────────────────────────────────────────────
P_RA = box(HLX,  10.45, 'Right\nAtrium',  HEART)
P_RV = box(HLX,   9.45, 'Right\nVentricle', HEART, w=1.80)

# ── Left heart ───────────────────────────────────────────────────────────────
P_LA = box(HRX,  10.45, 'Left\nAtrium',   HEART)
P_LV = box(HRX,   9.45, 'Left\nVentricle', HEART, w=1.80)

# ── Aorta ────────────────────────────────────────────────────────────────────
P_AO  = box(RX,  8.90, 'Aorta',           ART)

# ── Coronary ─────────────────────────────────────────────────────────────────
P_COR = box(PCX,  8.65, 'Coronary',        COR, w=1.50)

# ── Upper body (thorax / head zone) ──────────────────────────────────────────
P_BC  = box(RX,  13.15, 'Brachio-\ncephalic',    ART)
P_UBA = box(RX,  12.15, 'Upper Body\nArtery',    ART)
P_UBV = box(LX,  12.15, 'Upper Body\nVein',      VEIN)
P_SVC = box(LX,  13.15, 'SVC',                   VEIN, w=1.30)

# ── Abdomen ──────────────────────────────────────────────────────────────────
P_AAO = box(RX,   6.90, 'Abdominal\nAorta',      ART)
P_RAR = box(RX,   5.90, 'Renal\nArtery',          ART)
P_RVN = box(LX,   5.90, 'Renal\nVein',            VEIN)
P_SPL = box(RX,   4.95, 'Splanchnic\nArtery',     ART)
P_SPV = box(LX,   4.95, 'Splanchnic\nVein',       VEIN)

# ── Lower extremities ────────────────────────────────────────────────────────
P_LBA = box(RX,   3.60, 'Lower Body\nArtery',     ART)
P_TV  = box(LX,   3.30, 'Thigh\nVein',            VEIN, w=1.40)
P_CV  = box(LX,   2.20, 'Calf\nVein',             VEIN, w=1.40)
P_FV  = box(LX,   1.10, 'Foot\nVein',             VEIN, w=1.40)

# ── IVC ──────────────────────────────────────────────────────────────────────
P_IVC = box(LX,   7.55, 'IVC',                    VEIN, w=1.30)

# ─────────────────────────────────────────────────────────────────────────────
# FLOW CONNECTIONS
# ─────────────────────────────────────────────────────────────────────────────

# ── Pulmonary circuit ─────────────────────────────────────────────────────────
arr(*P_RV, PLX, 11.10, LUNG, lw=1.6, rad=-0.25)   # RV → PA
arr(PLX, 11.62, PCX, 11.80, LUNG, lw=1.6)          # PA → PCAP
arr(PCX+0.83, 11.80, PRX-0.83, 11.62, LUNG, lw=1.6) # PCAP → PV
arr(PRX, 11.10, *P_LA, LUNG, lw=1.6, rad=-0.25)    # PV → LA

# ── Right heart circuit ───────────────────────────────────────────────────────
arr(*P_RA, *P_RV, HEART, lw=1.6)                    # RA → RV (tricuspid)
ax.text(HLX+0.1, 9.95, 'tricuspid', fontsize=6,
        color=HEART, ha='left', va='center', fontstyle='italic', zorder=5)

# ── Left heart circuit ────────────────────────────────────────────────────────
arr(*P_LA, *P_LV, HEART, lw=1.6)                    # LA → LV (mitral)
ax.text(HRX+0.1, 9.95, 'mitral', fontsize=6,
        color=HEART, ha='left', va='center', fontstyle='italic', zorder=5)

# LV → Aorta
arr(HRX, 9.19, RX, 9.15, ART, lw=1.8, rad=-0.2)
ax.text((HRX+RX)/2+0.1, 8.78, 'aortic valve', fontsize=6.0,
        color=ART, ha='center', va='center', fontstyle='italic', zorder=5)

# ── Pulmonic valve label near RV→PA ──────────────────────────────────────────
ax.text(HLX - 0.05, 10.90, 'pulmonic\nvalve', fontsize=5.8,
        color=LUNG, ha='center', va='center', fontstyle='italic', zorder=5)

# ── Arterial right column ────────────────────────────────────────────────────
# Upward trunk: AO → BC (brachiocephalic goes up from aortic arch)
vline(RX, 8.64, 13.42, ART)
arrow_on_line(RX, 10.85, 0, 0.18, ART)   # AO → UBA upward
arrow_on_line(RX, 12.65, 0, 0.18, ART)   # UBA → BC upward

# Downward trunk: AO → AAO → RAR → SPL → LBA
vline(RX, 3.86, 8.64, ART)
arrow_on_line(RX,  7.6,  0, -0.18, ART)  # AO → AAO downward
arrow_on_line(RX,  5.4,  0, -0.18, ART)  # AAO → RAR/SPL downward

# AO → Coronary (branch)
arr(RX - 0.83, 8.90, PCX + 0.75, 8.65, COR, lw=1.4, rad=0.2)

# ── Coronary back to RA ───────────────────────────────────────────────────────
arr(PCX - 0.75, 8.65, HLX + 0.9, 10.2, COR, lw=1.4, rad=0.25)
ax.text(4.15, 9.15, 'coronary\nsinus→RA', fontsize=5.8,
        color=COR, ha='center', va='center', fontstyle='italic', zorder=5)

# ── Upper body cap bed: UBA → UBV ────────────────────────────────────────────
arr(RX - 0.83, 12.15, LX + 0.83, 12.15, VEIN, lw=1.4)    # UBA → UBV (capillary)
ax.text(5.5, 12.38, 'cap bed', fontsize=6.0,
        color=VEIN, ha='center', va='bottom', fontstyle='italic', zorder=5)

# ── Venous left column ────────────────────────────────────────────────────────
# UBV → SVC (upper body veins drain upward into SVC junction)
vline(LX, 8.20, 13.42, VEIN)
arrow_on_line(LX, 12.65, 0, 0.18, VEIN)   # UBV → SVC upward
arrow_on_line(LX,  6.65, 0, -0.18, VEIN)  # abdominal veins to IVC

# ── SVC → RA (explicit arrow from SVC box downward to RA) ────────────────────
arr(LX + 0.65, 12.89, HLX - 0.90, 10.71, VEIN, lw=1.6, rad=0.15)
ax.text(2.82, 11.95, 'SVC → RA', fontsize=6.2,
        color=VEIN, ha='left', va='center', fontstyle='italic', zorder=5)

# ── Abdominal arteries: AAO branches ─────────────────────────────────────────
arr(RX - 0.83, 5.90, LX + 0.83, 5.90, VEIN, lw=1.3)  # RAR cap → RVN
ax.text(5.5, 6.12, 'renal\ncap', fontsize=5.8,
        color=VEIN, ha='center', va='bottom', fontstyle='italic', zorder=5)
# SPL → SPV
arr(RX - 0.83, 4.95, LX + 0.83, 4.95, VEIN, lw=1.3)  # SPL cap → SPV
ax.text(5.5, 5.17, 'splanchnic\ncap', fontsize=5.8,
        color=VEIN, ha='center', va='bottom', fontstyle='italic', zorder=5)

# RVN → IVC
arr(LX, 6.20, LX, 7.29, VEIN, lw=1.4)
# SPV → IVC
arr(LX + 0.65, 4.95, LX + 0.65, 7.29, VEIN, lw=1.4, rad=0.15)

# IVC → RA
arr(LX + 0.65, 7.81, HLX - 0.90, 10.20, VEIN, lw=1.6, rad=0.15)
ax.text(3.05, 9.05, 'IVC → RA', fontsize=6.2,
        color=VEIN, ha='left', va='center', fontstyle='italic', zorder=5)

# ── Lower extremity arteries ──────────────────────────────────────────────────
# LBA → venous cap beds
arr(RX - 0.83, 3.60, LX + 0.70, 3.30, VEIN, lw=1.3, rad=0.15)
ax.text(5.4, 3.75, 'cap bed', fontsize=5.8,
        color=VEIN, ha='center', va='bottom', fontstyle='italic', zorder=5)
arr(RX - 0.83, 3.60, LX + 0.70, 2.20, VEIN, lw=1.3, rad=0.25)
arr(RX - 0.83, 3.60, LX + 0.70, 1.10, VEIN, lw=1.3, rad=0.35)

# Venous ladder: FV → CV → TV (valved) ────────────────────────────────────────
arr(LX, 1.36, LX, 1.94, VEIN, lw=1.6)      # FV → CV
ax.text(LX - 0.18, 1.65, '▶', fontsize=7, color=VEIN, ha='right',
        va='center', rotation=90, zorder=5)
arr(LX, 2.46, LX, 3.04, VEIN, lw=1.6)      # CV → TV
ax.text(LX - 0.18, 2.75, '▶', fontsize=7, color=VEIN, ha='right',
        va='center', rotation=90, zorder=5)
arr(LX, 3.56, LX, 4.69, VEIN, lw=1.6)      # TV → IVC
ax.text(LX - 0.18, 4.05, '▶', fontsize=7, color=VEIN, ha='right',
        va='center', rotation=90, zorder=5)


# ─────────────────────────────────────────────────────────────────────────────
# ANNOTATIONS & TITLE
# ─────────────────────────────────────────────────────────────────────────────

# Valve note for venous valves
ax.text(LX - 0.55, 1.65, 'valved', fontsize=6.0, color=VEIN,
        ha='right', va='center', fontstyle='italic', rotation=90, zorder=5)

# Column headers
ax.text(LX,  15.1, 'VENOUS', ha='center', va='bottom',
        fontsize=9, color=VEIN, fontweight='bold', zorder=5)
ax.text(RX,  15.1, 'ARTERIAL', ha='center', va='bottom',
        fontsize=9, color=ART, fontweight='bold', zorder=5)
ax.text(PCX, 15.1, 'PULMONARY\n& HEART', ha='center', va='bottom',
        fontsize=9, color=HEART, fontweight='bold', zorder=5)

# Title
ax.text(W/2, 15.55, '23-Compartment Lumped-Parameter Cardiovascular Model',
        ha='center', va='bottom', fontsize=11, fontweight='bold',
        color=LABEL_COL, zorder=5)
ax.text(W/2, 15.25, 'Compartment flow diagram  ·  Arrows show direction of blood flow',
        ha='center', va='bottom', fontsize=8.0, color=REGION_LABEL_COL, zorder=5)

# Legend
leg_entries = [
    (ART,   'Systemic arterial'),
    (VEIN,  'Systemic venous'),
    (HEART, 'Cardiac chambers'),
    (LUNG,  'Pulmonary circuit'),
    (COR,   'Coronary'),
]
leg_x0, leg_y0 = 0.65, 0.30
cols = 3
for i, (col, lbl) in enumerate(leg_entries):
    bx = leg_x0 + (i % cols) * 3.45
    by = leg_y0 - (i // cols) * 0.50
    b = FancyBboxPatch((bx, by - 0.17), 0.32, 0.34,
                        boxstyle='round,pad=0.03',
                        facecolor=col, edgecolor='white', linewidth=1, zorder=5)
    ax.add_patch(b)
    ax.text(bx + 0.45, by, lbl, fontsize=7.8, va='center',
            color=LABEL_COL, zorder=5)

plt.tight_layout(pad=0.3)

out_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
png_path = os.path.join(out_dir, 'compartment_diagram.png')
svg_path = os.path.join(out_dir, 'compartment_diagram.svg')

plt.savefig(png_path, dpi=150, bbox_inches='tight', facecolor='white')
plt.savefig(svg_path, bbox_inches='tight', facecolor='white')
print(f'Saved: {png_path}')
print(f'Saved: {svg_path}')
plt.close()
