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
// Muscle pump preset
// ---------------------------------------------------------------------------
function applyPumpPreset(val) {
  document.getElementById("pump_pressure").value = val;
  document.getElementById("pump_pressure_v").textContent = val;
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
      gravity:              document.getElementById("gravity").value,
      tilt_start_deg:       parseFloat(document.getElementById("tilt_start").value),
      tilt_end_deg:         parseFloat(document.getElementById("tilt_end").value),
      tilt_onset_s:         parseFloat(document.getElementById("tilt_onset").value),
      tilt_duration_s:      parseFloat(document.getElementById("tilt_dur").value),
      muscle_pump_pressure: parseFloat(document.getElementById("pump_pressure").value),
      muscle_pump_freq_hz:  parseFloat(document.getElementById("pump_freq").value),
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
    const cppStatus = data.summary.cpp_mean < 50 ? ' ⚠ CPP LOW' : data.summary.cpp_mean < 60 ? ' ⚡ CPP marginal' : '';
    status.textContent =
      `Done — MAP ${data.summary.map_mean} · HR ${data.summary.hr_mean} · CO ${data.summary.co_mean} · CPP ${data.summary.cpp_mean} mmHg${cppStatus}`;
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

  // Perfusion metrics with colour thresholds
  const cppEl = document.getElementById("s_cpp");
  cppEl.textContent = s.cpp_mean;
  cppEl.style.color = s.cpp_mean < 50 ? "#f87171" : s.cpp_mean < 60 ? "#fbbf24" : "#34d399";

  const copEl = document.getElementById("s_cop");
  copEl.textContent = s.cop_mean;
  copEl.style.color = s.cop_mean < 30 ? "#f87171" : s.cop_mean < 40 ? "#fbbf24" : "#f472b6";

  const bkEl = document.getElementById("s_buckberg");
  bkEl.textContent = s.buckberg_mean;
  bkEl.style.color = s.buckberg_mean < 0.5 ? "#f87171" : s.buckberg_mean < 0.8 ? "#fbbf24" : "#fbbf24";
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

  // --- Cerebral perfusion pressure ---
  // Colour zones: green >60, amber 50-60, red <50
  const cppShapes = [
    { type:"rect", xref:"paper", yref:"y", x0:0, x1:1, y0:0,  y1:50,  fillcolor:"rgba(239,68,68,0.08)",  line:{width:0} },
    { type:"rect", xref:"paper", yref:"y", x0:0, x1:1, y0:50, y1:60,  fillcolor:"rgba(251,191,36,0.08)", line:{width:0} },
    { type:"line", xref:"paper", yref:"y", x0:0, x1:1, y0:50, y1:50,  line:{color:"#f87171", width:1, dash:"dot"} },
    { type:"line", xref:"paper", yref:"y", x0:0, x1:1, y0:60, y1:60,  line:{color:"#fbbf24", width:1, dash:"dot"} },
  ];
  Plotly.newPlot("chart_cpp", [
    { x: d.t, y: d.cpp, name: "CPP", line: { color: "#34d399", width: 2 } },
    ...(d.dbp ? [{ x: d.t, y: d.dbp, name: "DBP", line: { color: "#60a5fa", width: 1, dash: "dot" } }] : []),
  ], {
    ...LAYOUT_BASE,
    title: { text: "Cerebral Perfusion Pressure", font: { color: "#c7d2fe", size: 12 } },
    yaxis: { ...LAYOUT_BASE.yaxis, title: "mmHg", range: [0, 120] },
    shapes: cppShapes,
    annotations: [
      { xref:"paper", yref:"y", x:0.02, y:48,  text:"Ischaemia risk <50", showarrow:false, font:{color:"#f87171", size:9} },
      { xref:"paper", yref:"y", x:0.02, y:58,  text:"Marginal <60",        showarrow:false, font:{color:"#fbbf24", size:9} },
    ],
  }, cfg);

  // --- Coronary / Buckberg ---
  const bkShapes = [
    { type:"rect", xref:"paper", yref:"y2", x0:0, x1:1, y0:0,   y1:0.5, fillcolor:"rgba(239,68,68,0.08)",  line:{width:0} },
    { type:"rect", xref:"paper", yref:"y2", x0:0, x1:1, y0:0.5, y1:0.8, fillcolor:"rgba(251,191,36,0.08)", line:{width:0} },
    { type:"line", xref:"paper", yref:"y2", x0:0, x1:1, y0:0.5, y1:0.5, line:{color:"#f87171", width:1, dash:"dot"} },
    { type:"line", xref:"paper", yref:"y2", x0:0, x1:1, y0:0.8, y1:0.8, line:{color:"#fbbf24", width:1, dash:"dot"} },
  ];
  Plotly.newPlot("chart_buckberg", [
    { x: d.t, y: d.cop,      name: "CoPP",    line: { color: "#f472b6", width: 1.5 }, yaxis: "y"  },
    { x: d.t, y: d.buckberg, name: "Buckberg",line: { color: "#fbbf24", width: 2   }, yaxis: "y2" },
  ], {
    ...LAYOUT_BASE,
    title: { text: "Coronary Perfusion & Buckberg Index", font: { color: "#c7d2fe", size: 12 } },
    yaxis:  { ...LAYOUT_BASE.yaxis, title: "CoPP (mmHg)", range: [0, 100] },
    yaxis2: { title: "Buckberg", overlaying: "y", side: "right",
              gridcolor: "#1e2235", range: [0, 2] },
    shapes: bkShapes,
  }, cfg);
}
