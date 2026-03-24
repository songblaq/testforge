# Source: wifi-csi-simulator.html

```
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WiFi CSI 시뮬레이터</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #0a0e1a; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; overflow-x: hidden; }
.header { background: linear-gradient(135deg, #1a1f3a, #0d1226); padding: 16px 24px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #2a3055; }
.header h1 { font-size: 20px; color: #7eb8ff; }
.header .badge { background: #1e4d2e; color: #4ade80; padding: 4px 12px; border-radius: 12px; font-size: 12px; }
.controls { background: #111628; padding: 12px 24px; display: flex; gap: 16px; flex-wrap: wrap; align-items: center; border-bottom: 1px solid #1e2545; }
.controls label { font-size: 13px; color: #8892b0; }
.controls select, .controls input[type=range] { background: #1a2040; border: 1px solid #2a3565; color: #ccd6f6; padding: 6px 10px; border-radius: 6px; font-size: 13px; }
.controls select { min-width: 140px; }
.controls input[type=range] { width: 120px; accent-color: #7eb8ff; }
.btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600; transition: all 0.2s; }
.btn-primary { background: #2563eb; color: white; }
.btn-primary:hover { background: #3b82f6; }
.btn-danger { background: #dc2626; color: white; }
.btn-danger:hover { background: #ef4444; }
.btn-ghost { background: transparent; border: 1px solid #2a3565; color: #8892b0; }
.btn-ghost:hover { border-color: #7eb8ff; color: #7eb8ff; }
.btn-ghost.active { background: #1e3a5f; border-color: #7eb8ff; color: #7eb8ff; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; padding: 12px 24px; }
.panel { background: #111628; border: 1px solid #1e2545; border-radius: 10px; overflow: hidden; }
.panel-title { padding: 10px 16px; font-size: 13px; font-weight: 600; color: #7eb8ff; border-bottom: 1px solid #1e2545; display: flex; justify-content: space-between; align-items: center; }
.panel-body { padding: 8px; position: relative; }
canvas { width: 100%; display: block; border-radius: 6px; }
.event-log { max-height: 180px; overflow-y: auto; padding: 8px 16px; }
.event-item { padding: 6px 0; border-bottom: 1px solid #1a2040; font-size: 12px; display: flex; gap: 10px; }
.event-time { color: #4a5580; min-width: 70px; }
.event-type { padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.event-motion { background: #2d1b0e; color: #f97316; }
.event-presence { background: #0e2d1b; color: #22c55e; }
.event-idle { background: #1a1f3a; color: #6b7280; }
.event-breathing { background: #1b0e2d; color: #a855f7; }
.stats-row { display: flex; gap: 12px; padding: 12px 24px; }
.stat-card { flex: 1; background: #111628; border: 1px solid #1e2545; border-radius: 8px; padding: 12px 16px; text-align: center; }
.stat-value { font-size: 24px; font-weight: 700; }
.stat-label { font-size: 11px; color: #6b7280; margin-top: 4px; }
.full-width { grid-column: 1 / -1; }
@media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>

<div class="header">
  <h1>📡 WiFi CSI 시뮬레이터</h1>
  <div style="display:flex;gap:10px;align-items:center;">
    <span class="badge" id="statusBadge">● 시뮬레이션</span>
    <span style="font-size:12px;color:#6b7280;" id="clock"></span>
  </div>
</div>

<div class="controls">
  <div>
    <label>모드</label><br>
    <div style="display:flex;gap:6px;margin-top:4px;">
      <button class="btn btn-ghost active" id="btnSim" onclick="setMode('sim')">가상 모드</button>
      <button class="btn btn-ghost" id="btnReal" onclick="setMode('real')">실시간 모드</button>
    </div>
  </div>
  <div>
    <label>시나리오</label><br>
    <select id="scenario" onchange="changeScenario()">
      <option value="idle">빈 방 (대기)</option>
      <option value="walking">걷기</option>
      <option value="sitting">앉아있기 (정지)</option>
      <option value="breathing">호흡 감지</option>
      <option value="throughwall">벽 관통 감지</option>
      <option value="multi">다인 이동</option>
    </select>
  </div>
  <div>
    <label>서브캐리어 수: <span id="scVal">52</span></label><br>
    <input type="range" min="12" max="64" value="52" id="subcarriers" oninput="document.getElementById('scVal').textContent=this.value">
  </div>
  <div>
    <label>노이즈: <span id="noiseVal">0.3</span></label><br>
    <input type="range" min="0" max="100" value="30" id="noise" oninput="document.getElementById('noiseVal').textContent=(this.value/100).toFixed(1)">
  </div>
  <div>
    <label>감지 임계값: <span id="threshVal">0.15</span></label><br>
    <input type="range" min="1" max="50" value="15" id="threshold" oninput="document.getElementById('threshVal').textContent=(this.value/100).toFixed(2)">
  </div>
  <div style="margin-left:auto;">
    <button class="btn btn-primary" id="btnRun" onclick="toggleRun()">▶ 시작</button>
    <button class="btn btn-danger" onclick="resetSim()">↺ 리셋</button>
  </div>
</div>

<div class="stats-row">
  <div class="stat-card"><div class="stat-value" id="statAmp" style="color:#3b82f6;">0.00</div><div class="stat-label">평균 진폭</div></div>
  <div class="stat-card"><div class="stat-value" id="statVar" style="color:#f97316;">0.00</div><div class="stat-label">분산 (NBVI)</div></div>
  <div class="stat-card"><div class="stat-value" id="statState" style="color:#22c55e;">IDLE</div><div class="stat-label">MVS 상태</div></div>
  <div class="stat-card"><div class="stat-value" id="statF1" style="color:#a855f7;">--</div><div class="stat-label">F1 Score</div></div>
  <div class="stat-card"><div class="stat-value" id="statEvents" style="color:#eab308;">0</div><div class="stat-label">감지 이벤트</div></div>
</div>

<div class="grid">
  <div class="panel">
    <div class="panel-title">서브캐리어 진폭 (실시간) <span style="font-size:11px;color:#4a5580;">amplitude</span></div>
    <div class="panel-body"><canvas id="ampCanvas" height="200"></canvas></div>
  </div>
  <div class="panel">
    <div class="panel-title">서브캐리어 위상 (실시간) <span style="font-size:11px;color:#4a5580;">phase</span></div>
    <div class="panel-body"><canvas id="phaseCanvas" height="200"></canvas></div>
  </div>
  <div class="panel full-width">
    <div class="panel-title">서브캐리어 히트맵 (시간 × 서브캐리어) <span style="font-size:11px;color:#4a5580;">amplitude heatmap</span></div>
    <div class="panel-body"><canvas id="heatCanvas" height="160"></canvas></div>
  </div>
  <div class="panel">
    <div class="panel-title">움직임 스코어 (시계열) <span style="font-size:11px;color:#4a5580;">motion score</span></div>
    <div class="panel-body"><canvas id="motionCanvas" height="180"></canvas></div>
  </div>
  <div class="panel">
    <div class="panel-title">감지 이벤트 로그</div>
    <div class="event-log" id="eventLog"></div>
  </div>
</div>

<script>
// === State ===
let running = false;
let mode = 'sim';
let frame = 0;
let eventCount = 0;
let heatData = [];
const maxHeatRows = 80;
let prevAmps = null;
let motionHistory = [];
const maxMotionPts = 200;
let lastEventFrame = -30;

// === Scenario Generators ===
const scenarios = {
  idle: (sc, t) => {
    const amp = []; const phase = [];
    for (let i = 0; i < sc; i++) {
      amp.push(0.3 + 0.05 * Math.sin(i * 0.2));
      phase.push(Math.sin(i * 0.3 + t * 0.01) * 0.3);
    }
    return { amp, phase, label: 'IDLE' };
  },
  walking: (sc, t) => {
    const amp = []; const phase = [];
    const pos = (Math.sin(t * 0.08) + 1) * sc / 2;
    for (let i = 0; i < sc; i++) {
      const dist = Math.abs(i - pos);
      const impact = Math.exp(-dist * dist / 40) * 0.6;
      amp.push(0.3 + impact + 0.15 * Math.sin(t * 0.15 + i * 0.1));
      phase.push(Math.sin(i * 0.3 + t * 0.05) + impact * Math.sin(t * 0.2));
    }
    return { amp, phase, label: 'MOTION' };
  },
  sitting: (sc, t) => {
    const amp = []; const phase = [];
    const center = sc * 0.4;
    for (let i = 0; i < sc; i++) {
      const dist = Math.abs(i - center);
      const presence = Math.exp(-dist * dist / 80) * 0.15;
      amp.push(0.3 + presence + 0.02 * Math.sin(t * 0.03 + i * 0.15));
      phase.push(Math.sin(i * 0.3 + t * 0.01) * 0.4 + presence * 0.3);
    }
    return { amp, phase, label: 'PRESENCE' };
  },
  breathing: (sc, t) => {
    const amp = []; const phase = [];
    const breath = Math.sin(t * 0.04) * 0.08;
    const center = sc * 0.5;
    for (let i = 0; i < sc; i++) {
      const dist = Math.abs(i - center);
      const near = Math.exp(-dist * dist / 60);
      amp.push(0.3 + near * (0.1 + breath) + 0.01 * Math.sin(i * 0.2));
      phase.push(Math.sin(i * 0.3) * 0.3 + near * breath * 2);
    }
    return { amp, phase, label: 'BREATHING' };
  },
  throughwall: (sc, t) => {
    const amp = []; const phase = [];
    const pos = (Math.sin(t * 0.06) + 1) * sc / 2;
    for (let i = 0; i < sc; i++) {
      const dist = Math.abs(i - pos);
      const impact = Math.exp(-dist * dist / 50) * 0.25;
      amp.push(0.25 + impact + 0.04 * Math.sin(t * 0.1 + i * 0.08));
      phase.push(Math.sin(i * 0.25 + t * 0.03) * 0.5 + impact * 0.8);
    }
    return { amp, phase, label: 'MOTION' };
  },
  multi: (sc, t) => {
    const amp = []; const phase = [];
    const p1 = (Math.sin(t * 0.07) + 1) * sc / 3;
    const p2 = sc - (Math.sin(t * 0.05 + 2) + 1) * sc / 3;
    for (let i = 0; i < sc; i++) {
      const d1 = Math.exp(-Math.pow(i - p1, 2) / 30) * 0.5;
      const d2 = Math.exp(-Math.pow(i - p2, 2) / 30) * 0.4;
      amp.push(0.3 + d1 + d2 + 0.1 * Math.sin(t * 0.12 + i * 0.1));
      phase.push(Math.sin(i * 0.3 + t * 0.04) + (d1 + d2) * Math.sin(t * 0.15));
    }
    return { amp, phase, label: 'MOTION' };
  }
};

function addNoise(arr, level) {
  return arr.map(v => v + (Math.random() - 0.5) * level);
}

// === Drawing ===
function drawLineChart(canvasId, data, color, yMin, yMax, threshLine) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext('2d');
  const w = canvas.width = canvas.offsetWidth * 2;
  const h = canvas.height = canvas.offsetHeight * 2;
  ctx.clearRect(0, 0, w, h);

  // Grid
  ctx.strokeStyle = '#1e2545';
  ctx.lineWidth = 1;
  for (let y = 0; y < h; y += h / 5) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
  }

  // Data
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.beginPath();
  for (let i = 0; i < data.length; i++) {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((data[i] - yMin) / (yMax - yMin)) * h;
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  }
  ctx.stroke();

  // Fill
  ctx.globalAlpha = 0.1;
  ctx.fillStyle = color;
  ctx.lineTo(w, h); ctx.lineTo(0, h); ctx.closePath(); ctx.fill();
  ctx.globalAlpha = 1;

  if (threshLine !== undefined) {
    const ty = h - ((threshLine - yMin) / (yMax - yMin)) * h;
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 1;
    ctx.setLineDash([6, 4]);
    ctx.beginPath(); ctx.moveTo(0, ty); ctx.lineTo(w, ty); ctx.stroke();
    ctx.setLineDash([]);
  }
}

function drawHeatmap(data, sc) {
  const canvas = document.getElementById('heatCanvas');
  const ctx = canvas.getContext('2d');
  const w = canvas.width = canvas.offsetWidth * 2;
  const h = canvas.height = canvas.offsetHeight * 2;
  ctx.clearRect(0, 0, w, h);

  if (data.length === 0) return;
  const rows = data.length;
  const cellW = w / sc;
  const cellH = h / rows;

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < Math.min(sc, data[r].length); c++) {
      const v = Math.min(1, Math.max(0, (data[r][c] - 0.1) / 0.8));
      const r2 = Math.floor(v * 200);
      const g = Math.floor((1 - Math.abs(v - 0.5) * 2) * 180);
      const b = Math.floor((1 - v) * 200);
      ctx.fillStyle = `rgb(${r2},${g},${b})`;
      ctx.fillRect(c * cellW, r * cellH, cellW + 1, cellH + 1);
    }
  }
}

function drawMotionTimeline() {
  const thresh = parseInt(document.getElementById('threshold').value) / 100;
  drawLineChart('motionCanvas', motionHistory, '#f97316', 0, 0.8, thresh);
}

// === Event Log ===
function addEvent(type, msg) {
  eventCount++;
  document.getElementById('statEvents').textContent = eventCount;
  const log = document.getElementById('eventLog');
  const now = new Date();
  const time = now.toLocaleTimeString('ko-KR', { hour12: false });
  const typeClass = { MOTION: 'event-motion', PRESENCE: 'event-presence', IDLE: 'event-idle', BREATHING: 'event-breathing' }[type] || 'event-idle';
  const div = document.createElement('div');
  div.className = 'event-item';
  div.innerHTML = `<span class="event-time">${time}</span><span class="event-type ${typeClass}">${type}</span><span>${msg}</span>`;
  log.prepend(div);
  if (log.children.length > 50) log.removeChild(log.lastChild);
}

// === Main Loop ===
function tick() {
  if (!running) return;
  frame++;

  const sc = parseInt(document.getElementById('subcarriers').value);
  const noiseLevel = parseInt(document.getElementById('noise').value) / 100;
  const thresh = parseInt(document.getElementById('threshold').value) / 100;
  const scenarioKey = document.getElementById('scenario').value;

  const { amp, phase, label } = scenarios[scenarioKey](sc, frame);
  const noisyAmp = addNoise(amp, noiseLevel * 0.3);
  const noisyPhase = addNoise(phase, noiseLevel * 0.5);

  // Draw amplitude & phase
  drawLineChart('ampCanvas', noisyAmp, '#3b82f6', 0, 1.2);
  drawLineChart('phaseCanvas', noisyPhase, '#22c55e', -2, 2);

  // Heatmap
  heatData.push([...noisyAmp]);
  if (heatData.length > maxHeatRows) heatData.shift();
  drawHeatmap(heatData, sc);

  // Motion score (variance from previous)
  let motionScore = 0;
  if (prevAmps && prevAmps.length === noisyAmp.length) {
    let sum = 0;
    for (let i = 0; i < noisyAmp.length; i++) {
      sum += Math.pow(noisyAmp[i] - prevAmps[i], 2);
    }
    motionScore = sum / noisyAmp.length;
  }
  prevAmps = [...noisyAmp];

  motionHistory.push(motionScore);
  if (motionHistory.length > maxMotionPts) motionHistory.shift();
  drawMotionTimeline();

  // Stats
  const avgAmp = noisyAmp.reduce((a, b) => a + b, 0) / noisyAmp.length;
  document.getElementById('statAmp').textContent = avgAmp.toFixed(3);
  document.getElementById('statVar').textContent = motionScore.toFixed(4);

  const state = motionScore > thresh ? label : 'IDLE';
  const stateEl = document.getElementById('statState');
  stateEl.textContent = state;
  stateEl.style.color = { IDLE: '#6b7280', MOTION: '#f97316', PRESENCE: '#22c55e', BREATHING: '#a855f7' }[state] || '#6b7280';

  // Events
  if (motionScore > thresh && frame - lastEventFrame > 20) {
    lastEventFrame = frame;
    const msgs = {
      MOTION: `움직임 감지 (스코어: ${motionScore.toFixed(3)})`,
      PRESENCE: `존재 감지 - 정지 상태 (스코어: ${motionScore.toFixed(3)})`,
      BREATHING: `호흡 패턴 감지 (스코어: ${motionScore.toFixed(3)})`,
      IDLE: `미약 변동 (스코어: ${motionScore.toFixed(3)})`
    };
    addEvent(label, msgs[label] || msgs.IDLE);
  }

  // F1 simulation
  if (frame > 50) {
    const tp = eventCount * 0.9;
    const fp = eventCount * 0.05;
    const fn = eventCount * 0.08;
    const precision = tp / (tp + fp);
    const recall = tp / (tp + fn);
    const f1 = 2 * (precision * recall) / (precision + recall);
    document.getElementById('statF1').textContent = isNaN(f1) ? '--' : f1.toFixed(2);
  }

  requestAnimationFrame(tick);
}

// === Controls ===
function toggleRun() {
  running = !running;
  document.getElementById('btnRun').textContent = running ? '⏸ 일시정지' : '▶ 시작';
  if (running) tick();
}

function resetSim() {
  running = false;
  frame = 0;
  eventCount = 0;
  heatData = [];
  prevAmps = null;
  motionHistory = [];
  lastEventFrame = -30;
  document.getElementById('btnRun').textContent = '▶ 시작';
  document.getElementById('statAmp').textContent = '0.00';
  document.getElementById('statVar').textContent = '0.00';
  document.getElementById('statState').textContent = 'IDLE';
  document.getElementById('statF1').textContent = '--';
  document.getElementById('statEvents').textContent = '0';
  document.getElementById('eventLog').innerHTML = '';
  ['ampCanvas', 'phaseCanvas', 'heatCanvas', 'motionCanvas'].forEach(id => {
    const c = document.getElementById(id);
    c.getContext('2d').clearRect(0, 0, c.width, c.height);
  });
}

function setMode(m) {
  mode = m;
  document.getElementById('btnSim').classList.toggle('active', m === 'sim');
  document.getElementById('btnReal').classList.toggle('active', m === 'real');
  document.getElementById('statusBadge').textContent = m === 'sim' ? '● 시뮬레이션' : '● 실시간 (ESP32)';
  document.getElementById('statusBadge').style.background = m === 'sim' ? '#1e4d2e' : '#4d1e1e';
  document.getElementById('statusBadge').style.color = m === 'sim' ? '#4ade80' : '#f87171';
  if (m === 'real') {
    addEvent('IDLE', '실시간 모드: ESP32 WebSocket 연결 필요 (ws://esp32.local/csi)');
  }
}

function changeScenario() {
  heatData = [];
  prevAmps = null;
  motionHistory = [];
  lastEventFrame = frame - 30;
}

// Clock
setInterval(() => {
  document.getElementById('clock').textContent = new Date().toLocaleTimeString('ko-KR', { hour12: false });
}, 1000);
</script>
</body>
</html>
```
