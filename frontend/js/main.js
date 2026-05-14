/* main.js — UI logic and API calls for the vascular model simulator */

// ---------------------------------------------------------------------------
// Tier tabs
// ---------------------------------------------------------------------------
let currentTier = 1;

function setTier(n) {
  currentTier = n;
  [1, 2, 3].forEach(k => {
    document.getElementById(`tier${k}`).classList.toggle("visible", k <= n);
    document.querySelectorAll(".tier-tabs button")[k - 1].classList.toggle("active", k <= n);
  });
}

// ---------------------------------------------------------------------------
// Collect form values
// ---------------------------------------------------------------------------
function optFloat(id) {
  const v = parseFloat(document.getElementById(id).value);
  return isNaN(v) ? null : v;
}

function buildPayload() {
  const drugs = {};
  const norepi = optFloat("drug_norepi"); if (norepi) drugs.norepinephrine = norepi;
  const phenyl = optFloat("drug_phenyl"); if (phenyl) drugs.phenylephrine  = phenyl;
  const vaso   = optFloat("drug_vaso");   if (vaso)   drugs.vasopressin    = vaso;
  const epi    = optFloat("drug_epi");    if (epi)    drugs.epinephrine    = epi;

  return {
    patient: {
      height_cm:           parseFloat(document.getElementById("height_cm").value),
      weight_kg:           parseFloat(document.getElementById("weight_kg").value),
      map_mmhg:            optFloat("map_mmhg"),
      hr_bpm:              parseFloat(document.getElementById("hr_bpm").value),
      cardiac_output_lpm:  currentTier >= 2 ? optFloat("co_lpm")      : null,
      abi:                 currentTier >= 2 ? optFloat("abi")          : null,
      cvp_mmhg:            currentTier >= 3 ? optFloat("cvp_mmhg")    : null,
      pcwp_mmhg:           currentTier >= 3 ? optFloat("pcwp_mmhg")   : null,
      pap_mean_mmhg:       currentTier >= 3 ? optFloat("pap_mean_mmhg") : null,
    },
    scenario: {
      gravity:       document.getElementById("gravity").value,
      tilt_start_deg: parseFloat(document.getElementById("tilt_start").value),
      tilt_end_deg:   parseFloat(document.getElementById("tilt_end").value),
      tilt_onset_s:   parseFloat(document.getElementById("tilt_onset").value),
      tilt_duration_s: parseFloat(document.getElementById("tilt_dur").value),
      drugs,
    },
    simulation: {
      duration_s:         parseFloat(document.getElementById("duration_s").value),
      baroreflex_enabled: document.getElementById("baroreflex").checked,
    },
  };
}

// ---------------------------------------------------------------------------
// Run simulation
// ---------------------------------------------------------------------------
async function runSim() {
  const btn = document.getElementById("runBtn");
  const status = document.getElementById("statusBar");
  btn.disabled = true;
  btn.textContent = "Running…";
  status.textContent = "Sending request…";

  try {
    const res = await fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildPayload()),
    });

    if (!res.ok) {
      const err = await res.text();
      throw new Error(err);
    }

    const data = await res.json();
    renderCharts(data);
    updateSummary(data.summary);
    status.textContent =
      `Done — MAP ${data.summary.map_mean} mmHg · HR ${data.summary.hr_mean} bpm · CO ${data.summary.co_mean} L/min`;
  } catch (e) {
    status.textContent = `Error: ${e.message}`;
    console.error(e);
  } finally {
    btn.disabled = false;
    btn.textContent = "Run Simulation";
  }
}

// ---------------------------------------------------------------------------
// Update summary metrics
// ---------------------------------------------------------------------------
function updateSummary(s) {
  document.getElementById("s_map").textContent  = s.map_mean;
  document.getElementById("s_hr").textContent   = s.hr_mean;
  document.getElementById("s_co").textContent   = s.co_mean;
  document.getElementById("s_cvp").textContent  = s.cvp_mean;
  document.getElementById("s_sv").textContent   = s.sv_mean;
}

// ---------------------------------------------------------------------------
// Render Plotly charts
// ---------------------------------------------------------------------------
const LAYOUT_BASE = {
  paper_bgcolor: "#13161f",
  plot_bgcolor:  "#0f1117",
  font:   { color: "#94a3b8", size: 11 },
  margin: { l: 48, r: 12, t: 32, b: 36 },
  xaxis:  { gridcolor: "#1e2235", title: "Time (s)" },
  yaxis:  { gridcolor: "#1e2235" },
};

const LINE_COLORS = {
  ap:    "#818cf8",
  map:   "#60a5fa",
  co:    "#34d399",
  cvp:   "#fb923c",
  la:    "#f472b6",
  hr:    "#facc15",
  sv:    "#a78bfa",
};

function renderCharts(d) {
  const cfg = { responsive: true, displayModeBar: false };

  // --- Arterial pressure ---
  Plotly.newPlot("chart_ap", [
    { x: d.t, y: d.aortic_p, name: "Aortic P", line: { color: LINE_COLORS.ap, width: 1.5 } },
    { x: d.t, y: d.map,      name: "MAP",       line: { color: LINE_COLORS.map, width: 2, dash: "dot" } },
  ], {
    ...LAYOUT_BASE,
    title: { text: "Arterial Pressure", font: { color: "#c7d2fe", size: 12 } },
    yaxis: { ...LAYOUT_BASE.yaxis, title: "mmHg" },
  }, cfg);

  // --- Cardiac output ---
  Plotly.newPlot("chart_co", [
    { x: d.t, y: d.co, name: "CO",  line: { color: LINE_COLORS.co, width: 1.5 }, yaxis: "y" },
    { x: d.t, y: d.sv, name: "SV",  line: { color: LINE_COLORS.sv, width: 1.5 }, yaxis: "y2" },
  ], {
    ...LAYOUT_BASE,
    title: { text: "Cardiac Output & Stroke Volume", font: { color: "#c7d2fe", size: 12 } },
    yaxis:  { ...LAYOUT_BASE.yaxis, title: "CO (L/min)" },
    yaxis2: { title: "SV (mL)", overlaying: "y", side: "right", gridcolor: "#1e2235" },
  }, cfg);

  // --- Filling pressures ---
  Plotly.newPlot("chart_cvp", [
    { x: d.t, y: d.cvp,         name: "CVP / RAP",  line: { color: LINE_COLORS.cvp, width: 1.5 } },
    { x: d.t, y: d.la_pressure, name: "LAP / PCWP", line: { color: LINE_COLORS.la,  width: 1.5 } },
  ], {
    ...LAYOUT_BASE,
    title: { text: "Filling Pressures", font: { color: "#c7d2fe", size: 12 } },
    yaxis: { ...LAYOUT_BASE.yaxis, title: "mmHg" },
  }, cfg);

  // --- Heart rate ---
  Plotly.newPlot("chart_hr", [
    { x: d.t, y: d.hr, name: "HR", line: { color: LINE_COLORS.hr, width: 2 } },
  ], {
    ...LAYOUT_BASE,
    title: { text: "Heart Rate", font: { color: "#c7d2fe", size: 12 } },
    yaxis: { ...LAYOUT_BASE.yaxis, title: "bpm" },
  }, cfg);
}
