/* main.js — Human Cardiovascular Model */

// ═══════════════════════════════════════════════════
// Tilt control
// ═══════════════════════════════════════════════════

function onTiltMove(val) {
  val = parseInt(val, 10);
  let label = val === 0 ? '0° — Supine'
            : val < 0  ? `${val}° — Head-down`
                        : `+${val}° — Head-up`;
  document.getElementById('tilt_val_lbl').textContent = label;
  document.getElementById('s_tilt').textContent = val + '°';
  updateAvatar({ tilt: val });
  liveUpdate();
}

// ═══════════════════════════════════════════════════
// Pump preset
// ═══════════════════════════════════════════════════

function applyPumpPreset(val) {
  // Store internal pump pressure (used in buildPayload / liveUpdate)
  window._pumpPressure = parseFloat(val);
  liveUpdate();
}
window._pumpPressure = 0;

function clearDrugs() {
  ['drug_propofol','drug_norepi','drug_phenyl','drug_vaso','drug_epi'].forEach(id => {
    document.getElementById(id).value = 0;
  });
  liveUpdate();
}

// ═══════════════════════════════════════════════════
// Analysis run overlay
// ═══════════════════════════════════════════════════

function showRunPanel() { document.getElementById('runOverlay').style.display = 'flex'; }
function hideRunPanel() { document.getElementById('runOverlay').style.display = 'none'; }

// ═══════════════════════════════════════════════════
// Build payload (shared by run + live)
// ═══════════════════════════════════════════════════

function optFloat(id) {
  const v = parseFloat(document.getElementById(id).value);
  return isNaN(v) ? null : v;
}

function buildPatient() {
  return {
    height_cm: parseFloat(document.getElementById('height_cm').value),
    weight_kg: parseFloat(document.getElementById('weight_kg').value),
    map_mmhg:  optFloat('map_mmhg'),
    hr_bpm:    parseFloat(document.getElementById('hr_bpm').value),
  };
}

function buildScenario() {
  const drugs = {};
  const prop   = optFloat('drug_propofol'); if (prop)   drugs.propofol       = prop;
  const norepi = optFloat('drug_norepi');   if (norepi) drugs.norepinephrine = norepi;
  const phenyl = optFloat('drug_phenyl');   if (phenyl) drugs.phenylephrine  = phenyl;
  const vaso   = optFloat('drug_vaso');     if (vaso)   drugs.vasopressin    = vaso;
  const epi    = optFloat('drug_epi');      if (epi)    drugs.epinephrine    = epi;

  return {
    gravity:              document.getElementById('gravity').value,
    tilt_start_deg:       parseFloat(document.getElementById('tilt_current').value),
    tilt_end_deg:         parseFloat(document.getElementById('tilt_current').value),
    tilt_onset_s:         0,
    tilt_duration_s:      5,
    muscle_pump_pressure: window._pumpPressure || 0,
    muscle_pump_freq_hz:  0.5,
    drugs,
  };
}

// ═══════════════════════════════════════════════════
// One-shot analysis run
// ═══════════════════════════════════════════════════

async function runSim() {
  hideRunPanel();
  const status = document.getElementById('statusBar');
  status.textContent = 'Running analysis…';

  try {
    const res = await fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        patient:    buildPatient(),
        scenario:   buildScenario(),
        simulation: {
          duration_s:         parseFloat(document.getElementById('duration_s').value),
          baroreflex_enabled: document.getElementById('baroreflex').checked,
        },
      }),
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    renderStaticCharts(data);
    updateVitals(data.summary);
    const s = data.summary;
    status.textContent = `Analysis done — MAP ${s.map_mean} mmHg · HR ${s.hr_mean} bpm · CO ${s.co_mean} L/min · CPP ${s.cpp_mean} mmHg`;
  } catch (e) {
    status.textContent = `Error: ${e.message}`;
    console.error(e);
  }
}

// ═══════════════════════════════════════════════════
// Static chart rendering (one-shot run)
// ═══════════════════════════════════════════════════

const BASE = {
  paper_bgcolor: '#0b0e17',
  plot_bgcolor:  '#0b0e17',
  font:   { color: '#6b7280', size: 10 },
  margin: { l: 44, r: 10, t: 28, b: 28 },
  xaxis:  { gridcolor: '#1f2937', title: 'Time (s)', color: '#6b7280' },
  yaxis:  { gridcolor: '#1f2937', color: '#6b7280' },
};
const CFG = { responsive: true, displayModeBar: false };

const C = {
  ap: '#818cf8', map: '#60a5fa', dbp: '#4f46e5',
  co: '#10b981', sv: '#a78bfa',
  cvp: '#f59e0b', la: '#f472b6',
  hr: '#fbbf24',
  cpp_ok: '#10b981', cpp_warn: '#f59e0b', cpp_bad: '#ef4444',
  cop: '#f472b6', buck: '#fbbf24',
};

function renderStaticCharts(d) {
  Plotly.newPlot('chart_ap', [
    { x: d.t, y: d.aortic_p, name: 'Aortic P', line: { color: C.ap, width: 1.5 } },
    { x: d.t, y: d.map,      name: 'MAP',       line: { color: C.map, width: 2, dash: 'dot' } },
    { x: d.t, y: d.dbp,      name: 'DBP',       line: { color: C.dbp, width: 1, dash: 'dot' } },
  ], { ...BASE, title: { text: 'Arterial Pressure', font: { color: '#c7d2fe', size: 11 } },
       yaxis: { ...BASE.yaxis, title: 'mmHg' } }, CFG);

  Plotly.newPlot('chart_co', [
    { x: d.t, y: d.co, name: 'CO',  line: { color: C.co, width: 2 }, yaxis: 'y' },
    { x: d.t, y: d.sv, name: 'SV',  line: { color: C.sv, width: 1.5 }, yaxis: 'y2' },
  ], { ...BASE, title: { text: 'Cardiac Output & SV', font: { color: '#c7d2fe', size: 11 } },
       yaxis:  { ...BASE.yaxis, title: 'CO (L/min)' },
       yaxis2: { title: 'SV (mL)', overlaying: 'y', side: 'right', gridcolor: '#1f2937', color: '#6b7280' } }, CFG);

  Plotly.newPlot('chart_cvp', [
    { x: d.t, y: d.cvp,         name: 'CVP',  line: { color: C.cvp, width: 2 } },
    { x: d.t, y: d.la_pressure, name: 'PCWP', line: { color: C.la,  width: 1.5 } },
  ], { ...BASE, title: { text: 'Filling Pressures', font: { color: '#c7d2fe', size: 11 } },
       yaxis: { ...BASE.yaxis, title: 'mmHg' } }, CFG);

  const cppCol = (d.summary?.cpp_mean || 70) < 50 ? C.cpp_bad
               : (d.summary?.cpp_mean || 70) < 60 ? C.cpp_warn : C.cpp_ok;
  Plotly.newPlot('chart_cpp', [
    { x: d.t, y: d.cpp, name: 'CPP', line: { color: cppCol, width: 2 } },
  ], { ...BASE,
       title: { text: 'Cerebral Perfusion Pressure', font: { color: '#c7d2fe', size: 11 } },
       yaxis: { ...BASE.yaxis, title: 'mmHg', range: [0, 120] },
       shapes: cppZones() }, CFG);

  Plotly.newPlot('chart_buckberg', [
    { x: d.t, y: d.cop,      name: 'CoPP',    line: { color: C.cop, width: 1.5 }, yaxis: 'y' },
    { x: d.t, y: d.buckberg, name: 'Buckberg', line: { color: C.buck, width: 2 }, yaxis: 'y2' },
  ], { ...BASE,
       title: { text: 'Coronary / Buckberg', font: { color: '#c7d2fe', size: 11 } },
       yaxis:  { ...BASE.yaxis, title: 'CoPP (mmHg)', range: [0, 100] },
       yaxis2: { title: 'Buckberg', overlaying: 'y', side: 'right', range: [0, 2], gridcolor: '#1f2937', color: '#6b7280' },
       shapes: buckZones() }, CFG);
}

function cppZones() {
  return [
    { type:'rect', xref:'paper', yref:'y', x0:0, x1:1, y0:0,  y1:50,  fillcolor:'rgba(239,68,68,.07)',  line:{width:0} },
    { type:'rect', xref:'paper', yref:'y', x0:0, x1:1, y0:50, y1:60,  fillcolor:'rgba(245,158,11,.07)', line:{width:0} },
    { type:'line', xref:'paper', yref:'y', x0:0, x1:1, y0:50, y1:50,  line:{color:'#ef4444',width:1,dash:'dot'} },
    { type:'line', xref:'paper', yref:'y', x0:0, x1:1, y0:60, y1:60,  line:{color:'#f59e0b',width:1,dash:'dot'} },
  ];
}
function buckZones() {
  return [
    { type:'rect', xref:'paper', yref:'y2', x0:0, x1:1, y0:0,   y1:0.5, fillcolor:'rgba(239,68,68,.07)',  line:{width:0} },
    { type:'rect', xref:'paper', yref:'y2', x0:0, x1:1, y0:0.5, y1:0.8, fillcolor:'rgba(245,158,11,.07)', line:{width:0} },
    { type:'line', xref:'paper', yref:'y2', x0:0, x1:1, y0:0.5, y1:0.5, line:{color:'#ef4444',width:1,dash:'dot'} },
    { type:'line', xref:'paper', yref:'y2', x0:0, x1:1, y0:0.8, y1:0.8, line:{color:'#f59e0b',width:1,dash:'dot'} },
  ];
}

// ═══════════════════════════════════════════════════
// Patient avatar
// ═══════════════════════════════════════════════════

function updateAvatar(s) {
  const tilt = s.tilt ?? 0;

  // Tilt body around hip (100, 45); positive SVG rotation = head dips
  const body = document.getElementById('av-body');
  if (body) body.setAttribute('transform', `rotate(${-tilt}, 100, 45)`);

  // Head: CPP traffic-light
  const cpp  = s.cpp ?? null;
  const head = document.getElementById('av-head');
  if (head && cpp != null) {
    head.setAttribute('fill',
      cpp < 50 ? '#ef4444' : cpp < 60 ? '#f59e0b' : '#10b981');
  }

  // Torso: Buckberg traffic-light (subtle dark tint)
  const bk    = s.buckberg ?? null;
  const torso = document.getElementById('av-torso');
  if (torso && bk != null) {
    torso.setAttribute('fill',
      bk < 0.5 ? '#3b0f0f' : bk < 0.8 ? '#291a06' : '#1f2937');
  }

  // Legs: venous pooling proxy — opacity rises when head-up
  const legs = document.getElementById('av-legs');
  if (legs) {
    const pool = Math.max(0, Math.min(1, tilt / 45));
    legs.setAttribute('opacity', (0.3 + pool * 0.55).toFixed(2));
  }

  // Heart rate: speed up animation duration
  const hr    = s.hr ?? null;
  const heart = document.getElementById('av-heart');
  if (heart && hr != null) {
    heart.style.animationDuration = (60 / Math.max(30, hr)).toFixed(2) + 's';
  }
}

// ═══════════════════════════════════════════════════
// Vitals update (shared by live + static summary)
// ═══════════════════════════════════════════════════

function updateVitals(s) {
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val ?? '—';
  };
  set('s_hr',       s.hr_mean  ?? s.hr);
  set('s_map',      s.map_mean ?? s.map);
  set('s_bp',       `${s.sbp_mean ?? s.sbp ?? '—'}/${s.dbp_mean ?? s.dbp ?? '—'}`);
  set('s_co',       s.co_mean  ?? s.co);
  set('s_sv',       s.sv_mean  ?? s.sv);
  set('s_cvp',      s.cvp_mean ?? s.cvp);
  set('s_tilt',     (s.tilt != null ? s.tilt + '°' : null));

  const cpp = s.cpp_mean ?? s.cpp;
  const cop = s.cop_mean ?? s.cop;
  const bk  = s.buckberg_mean ?? s.buckberg;
  set('s_cpp',      cpp);
  set('s_cop',      cop);
  set('s_buckberg', bk);

  // Color-code CPP vital
  const cppEl = document.getElementById('v_cpp');
  const cppV  = document.getElementById('s_cpp');
  if (cpp != null) {
    cppEl.className = 'vital ' + (cpp < 50 ? 'red' : cpp < 60 ? 'amber' : 'green');
    cppV.style.color = cpp < 50 ? 'var(--red)' : cpp < 60 ? 'var(--amber)' : 'var(--green)';
  }

  // Color-code Buckberg
  const bkEl = document.getElementById('v_buckberg');
  const bkV  = document.getElementById('s_buckberg');
  if (bk != null) {
    bkEl.className = 'vital ' + (bk < 0.5 ? 'red' : bk < 0.8 ? 'amber' : '');
    bkV.style.color = bk < 0.5 ? 'var(--red)' : bk < 0.8 ? 'var(--amber)' : '#fbbf24';
  }

  updateAvatar(s);
}

// ═══════════════════════════════════════════════════
// Live mode
// ═══════════════════════════════════════════════════

let _liveActive  = false;
let _pollTimer   = null;
const LIVE_WIN   = 15;    // seconds of rolling window shown
const MAX_PTS    = 150;   // maxpoints passed to extendTraces (15 s × 10 Hz)

const _CHART_IDS = ['chart_ap','chart_co','chart_cvp','chart_cpp','chart_buckberg'];

// No _ld buffer arrays needed — Plotly.extendTraces manages data internally.
// extendTraces appends exactly one point and trims to maxpoints in O(1),
// eliminating the accumulation that caused the 15/60-second freeze.

let _lastExtend  = 0;    // wall-clock time of last extendTraces call
let _titleTick   = 0;    // counter for throttled title/axis updates

function _initLiveCharts() {
  const cfg = { responsive: true, displayModeBar: false };
  Plotly.newPlot('chart_ap', [
    { x:[], y:[], name:'Aortic P', line:{ color:C.ap,      width:1.5 } },
    { x:[], y:[], name:'SBP',      line:{ color:'#f472b6', width:1, dash:'dot' } },
    { x:[], y:[], name:'DBP',      line:{ color:C.dbp,     width:1, dash:'dot' } },
  ], { ...BASE, title:{ text:'Arterial Pressure', font:{color:'#c7d2fe',size:11} },
       yaxis:{ ...BASE.yaxis, title:'mmHg', range:[20,180] } }, cfg);

  Plotly.newPlot('chart_co', [
    { x:[], y:[], name:'CO', line:{ color:C.co, width:2 } },
  ], { ...BASE, title:{ text:'Cardiac Output', font:{color:'#c7d2fe',size:11} },
       yaxis:{ ...BASE.yaxis, title:'L/min', range:[0,12] } }, cfg);

  Plotly.newPlot('chart_cvp', [
    { x:[], y:[], name:'CVP', line:{ color:C.cvp, width:2 } },
  ], { ...BASE, title:{ text:'CVP', font:{color:'#c7d2fe',size:11} },
       yaxis:{ ...BASE.yaxis, title:'mmHg', range:[0,20] } }, cfg);

  Plotly.newPlot('chart_cpp', [
    { x:[], y:[], name:'CPP', line:{ color:C.cpp_ok, width:2 } },
  ], { ...BASE, title:{ text:'Cerebral Perfusion Pressure', font:{color:'#c7d2fe',size:11} },
       yaxis:{ ...BASE.yaxis, title:'mmHg', range:[0,120] }, shapes:cppZones() }, cfg);

  Plotly.newPlot('chart_buckberg', [
    { x:[], y:[], name:'CoPP',    line:{ color:C.cop,  width:1.5 }, yaxis:'y'  },
    { x:[], y:[], name:'Buckberg',line:{ color:C.buck, width:2   }, yaxis:'y2' },
  ], { ...BASE, title:{ text:'Coronary / Buckberg', font:{color:'#c7d2fe',size:11} },
       yaxis:  { ...BASE.yaxis, title:'CoPP (mmHg)', range:[0,100] },
       yaxis2: { title:'Buckberg', overlaying:'y', side:'right', range:[0,2],
                 gridcolor:'#1f2937', color:'#6b7280' },
       shapes: buckZones() }, cfg);
}

function _ext(id, update, indices) {
  try { Plotly.extendTraces(id, update, indices, MAX_PTS); } catch(e) {
    console.warn(`extendTraces ${id}:`, e.message);
  }
}

function _onLivePoint(s) {
  // 1. Vitals bar + avatar — lightweight, always runs
  updateVitals(s);
  updateAvatar(s);
  const tl = s.tilt ?? 0;
  document.getElementById('tilt_val_lbl').textContent =
    tl === 0 ? '0° — Supine' : tl < 0 ? `${tl}° — Head-down` : `+${tl}° — Head-up`;
  document.getElementById('s_tilt').textContent = tl + '°';

  // 2. Append one data point to each chart — O(1), no accumulation
  const now = Date.now();
  if (now - _lastExtend < 100) return;   // cap at 10 Hz chart updates
  _lastExtend = now;

  const t  = [[s.t]];
  _ext('chart_ap',        { x:[t,t,t], y:[[s.aortic_p??s.map],[s.sbp??s.map],[s.dbp??s.map]] }, [0,1,2]);
  _ext('chart_co',        { x:[t],     y:[[s.co]]                                             }, [0]    );
  _ext('chart_cvp',       { x:[t],     y:[[s.cvp]]                                            }, [0]    );
  _ext('chart_cpp',       { x:[t],     y:[[s.cpp]]                                            }, [0]    );
  _ext('chart_buckberg',  { x:[t,t],   y:[[s.cop],[s.buckberg]]                               }, [0,1]  );

  // 3. Scroll x-axis and refresh titles every second
  _titleTick++;
  if (_titleTick % 10 === 0) {
    const xr = { 'xaxis.range': [s.t - LIVE_WIN, s.t + 0.5] };
    const cppCol = (s.cpp||70)<50 ? C.cpp_bad : (s.cpp||70)<60 ? C.cpp_warn : C.cpp_ok;
    const bkCol  = (s.buckberg||1)<0.5 ? C.cpp_bad : C.cpp_warn;
    try { Plotly.relayout('chart_ap',       { ...xr, 'title.text':`BP  ${s.sbp}/${s.dbp} mmHg` }); } catch {}
    try { Plotly.relayout('chart_co',       { ...xr, 'title.text':`CO  ${s.co} L/min` });          } catch {}
    try { Plotly.relayout('chart_cvp',      { ...xr, 'title.text':`CVP  ${s.cvp} mmHg` });         } catch {}
    try { Plotly.relayout('chart_cpp',      { ...xr, 'title.text':`CPP  ${s.cpp} mmHg`,
                                              'data[0].line.color': cppCol });                      } catch {}
    try { Plotly.relayout('chart_buckberg', { ...xr, 'title.text':`CoPP ${s.cop}  Buckberg ${s.buckberg}`,
                                              'data[1].line.color': bkCol });                       } catch {}
  }
}

async function toggleLive() {
  if (_liveActive) {
    // Stop
    _liveActive = false;
    if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
    await fetch('/api/live/stop', { method: 'POST' });

    document.getElementById('liveBtn').className = 'btn-live start';
    document.getElementById('liveBtn').textContent = '⬤ Start Live Monitor';
    document.getElementById('liveBadge').classList.remove('active');
    document.getElementById('liveBadgeText').textContent = 'READY';
    document.getElementById('statusBar').textContent = 'Live monitor stopped.';
    return;
  }

  // Start
  _liveActive = true;
  _lastExtend = 0; _titleTick = 0;

  // Start server session
  await fetch('/api/live/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ patient: buildPatient(), scenario: buildScenario() }),
  });

  _initLiveCharts();

  // Poll /api/live/state at 10 Hz — simple, reliable, no SSE buffering issues.
  // SSE was being buffered by werkzeug's dev server (delivered in ~30-second
  // batches instead of immediately), causing the apparent 30-second freeze.
  _pollTimer = setInterval(async () => {
    if (!_liveActive) return;
    try {
      const res = await fetch('/api/live/state');
      if (!res.ok) return;
      const s = await res.json();
      if (s.ready && typeof s.t === 'number') _onLivePoint(s);
    } catch {}
  }, 100);  // 10 Hz

  document.getElementById('liveBtn').className = 'btn-live stop';
  document.getElementById('liveBtn').textContent = '⬛ Stop Live Monitor';
  document.getElementById('liveBadge').classList.add('active');
  document.getElementById('liveBadgeText').textContent = 'LIVE';
  document.getElementById('statusBar').textContent =
    'Live monitor running — adjust posture or vasopressors and watch the response.';
}

// ═══════════════════════════════════════════════════
// Live parameter update (called by controls in live mode)
// ═══════════════════════════════════════════════════

function liveUpdate() {
  if (!_liveActive) return;
  const drugs = {};
  const prop   = optFloat('drug_propofol'); if (prop)   drugs.propofol       = prop;
  const norepi = optFloat('drug_norepi');   if (norepi) drugs.norepinephrine = norepi;
  const phenyl = optFloat('drug_phenyl');   if (phenyl) drugs.phenylephrine  = phenyl;
  const vaso   = optFloat('drug_vaso');     if (vaso)   drugs.vasopressin    = vaso;
  const epi    = optFloat('drug_epi');      if (epi)    drugs.epinephrine    = epi;

  fetch('/api/live/params', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario: {
      tilt_deg:             parseFloat(document.getElementById('tilt_current').value),
      gravity:              document.getElementById('gravity').value,
      muscle_pump_pressure: window._pumpPressure || 0,
      muscle_pump_freq_hz:  0.5,
      drugs:     Object.keys(drugs).length ? drugs : undefined,
      drugs_reset: !Object.keys(drugs).length,
    }}),
  }).catch(console.error);
}
