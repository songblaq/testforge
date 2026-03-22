/* TestForge Web GUI -- vanilla JS SPA */

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let currentProject = null;   // { name, path, ... }
let allCases = [];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
async function api(method, path, body) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  const data = await res.json();
  if (!res.ok) {
    const msg = data.detail || JSON.stringify(data);
    throw new Error(msg);
  }
  return data;
}

function toast(message, type) {
  type = type || "info";
  var container = document.getElementById("toast-container");
  var el = document.createElement("div");
  el.className = "toast toast-" + type;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(function() { el.remove(); }, 4000);
}

function esc(str) {
  var d = document.createElement("div");
  d.textContent = str || "";
  return d.innerHTML;
}

function priorityBadge(p) {
  var map = { high: "badge-red", medium: "badge-yellow", low: "badge-blue" };
  return '<span class="badge ' + (map[p] || "badge-dim") + '">' + esc(p || "medium") + "</span>";
}

function statusBadge(s) {
  var map = { passed: "badge-green", failed: "badge-red", skipped: "badge-dim", error: "badge-red" };
  return '<span class="badge ' + (map[s] || "badge-dim") + '">' + esc(s) + "</span>";
}

function selectProject(proj) {
  currentProject = proj;
  document.querySelectorAll(".project-card").forEach(function(el) {
    el.classList.toggle("selected", el.dataset.path === proj.path);
  });
  toast("Selected: " + proj.name, "info");
  // Reset analysis/cases/exec/report views
  loadAnalysisView();
  loadCasesView();
  document.getElementById("execution-status").style.display = "";
  document.getElementById("execution-summary").style.display = "none";
  document.getElementById("execution-table").style.display = "none";
  document.getElementById("report-status").style.display = "";
  document.getElementById("report-viewer").style.display = "none";
  document.getElementById("coverage-section").style.display = "none";
}

// ---------------------------------------------------------------------------
// Tabs
// ---------------------------------------------------------------------------
document.querySelectorAll(".tab-btn").forEach(function(btn) {
  btn.addEventListener("click", function() {
    document.querySelectorAll(".tab-btn").forEach(function(b) { b.classList.remove("active"); });
    document.querySelectorAll(".tab-panel").forEach(function(p) { p.classList.remove("active"); });
    btn.classList.add("active");
    document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
  });
});

// ---------------------------------------------------------------------------
// Dashboard -- Projects
// ---------------------------------------------------------------------------
async function loadProjects() {
  var dir = document.getElementById("scan-dir").value || ".";
  try {
    var data = await api("GET", "/api/projects?directory=" + encodeURIComponent(dir));
    renderProjects(data.projects || []);
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}

function renderProjects(projects) {
  var container = document.getElementById("project-list");
  if (!projects.length) {
    container.innerHTML = '<div class="empty-state"><h3>No projects found</h3><p>Create a new project or check the directory path.</p></div>';
    return;
  }
  container.innerHTML = projects.map(function(p) {
    var badges = [];
    if (p.has_analysis) badges.push('<span class="badge badge-green">Analyzed</span>');
    if (p.has_cases) badges.push('<span class="badge badge-blue">Cases</span>');
    if (p.has_report) badges.push('<span class="badge badge-yellow">Report</span>');
    if (!badges.length) badges.push('<span class="badge badge-dim">New</span>');

    return '<div class="card project-card" data-path="' + esc(p.path) + '" onclick=\'selectProject(' + JSON.stringify(p).replace(/'/g, "&#39;") + ')\'  style="cursor:pointer;margin:0;">' +
      '<div class="card-header"><h2>' + esc(p.name) + '</h2></div>' +
      '<div style="font-size:12px;color:var(--text-dim);margin-bottom:8px;">' + esc(p.path) + '</div>' +
      '<div style="display:flex;gap:6px;">' + badges.join("") + '</div>' +
      '</div>';
  }).join("");
}

function showCreateProject() {
  document.getElementById("create-modal").style.display = "flex";
}

function hideCreateProject() {
  document.getElementById("create-modal").style.display = "none";
}

async function createProject() {
  var name = document.getElementById("new-project-name").value.trim();
  if (!name) { toast("Project name is required", "error"); return; }
  var dir = document.getElementById("new-project-dir").value || ".";
  var provider = document.getElementById("new-project-provider").value;
  var model = document.getElementById("new-project-model").value.trim();

  try {
    await api("POST", "/api/projects", { name: name, directory: dir, provider: provider, model: model });
    hideCreateProject();
    toast("Project created: " + name, "success");
    document.getElementById("scan-dir").value = dir;
    loadProjects();
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}

// ---------------------------------------------------------------------------
// Analysis
// ---------------------------------------------------------------------------
async function loadAnalysisView() {
  if (!currentProject) return;
  try {
    var data = await api("GET", "/api/projects/" + encodeURIComponent(currentProject.path) + "/analysis");
    renderAnalysis(data.analysis);
  } catch (e) {
    document.getElementById("analysis-status").style.display = "";
    document.getElementById("analysis-status").innerHTML = '<h3>No analysis results</h3><p>Click "Run Analysis" to analyze input documents.</p>';
    document.getElementById("analysis-content").style.display = "none";
  }
}

function renderAnalysis(analysis) {
  document.getElementById("analysis-status").style.display = "none";
  document.getElementById("analysis-content").style.display = "";

  var ftbody = document.querySelector("#features-table tbody");
  ftbody.innerHTML = (analysis.features || []).map(function(f) {
    return "<tr><td>" + esc(f.id) + "</td><td>" + esc(f.name) + "</td><td>" + esc(f.category) + "</td><td>" + priorityBadge(f.priority) + "</td><td>" + esc(f.description) + "</td></tr>";
  }).join("");

  var ptbody = document.querySelector("#personas-table tbody");
  ptbody.innerHTML = (analysis.personas || []).map(function(p) {
    return "<tr><td>" + esc(p.id) + "</td><td>" + esc(p.name) + "</td><td>" + esc(p.tech_level) + "</td><td>" + esc(p.description) + "</td></tr>";
  }).join("");

  var rtbody = document.querySelector("#rules-table tbody");
  rtbody.innerHTML = (analysis.rules || []).map(function(r) {
    return "<tr><td>" + esc(r.id) + "</td><td>" + esc(r.name) + "</td><td>" + esc(r.condition) + "</td><td>" + esc(r.expected_behavior) + "</td></tr>";
  }).join("");
}

async function runAnalysis() {
  if (!currentProject) { toast("Select a project first", "error"); return; }
  var btn = document.getElementById("btn-analyze");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Analyzing...';
  try {
    await api("POST", "/api/projects/" + encodeURIComponent(currentProject.path) + "/analysis", { no_llm: true });
    toast("Analysis complete", "success");
    loadAnalysisView();
  } catch (e) {
    toast("Analysis error: " + e.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Run Analysis";
  }
}

// ---------------------------------------------------------------------------
// Cases
// ---------------------------------------------------------------------------
async function loadCasesView() {
  if (!currentProject) return;
  try {
    var data = await api("GET", "/api/projects/" + encodeURIComponent(currentProject.path) + "/cases");
    allCases = data.cases || [];
    renderCases(allCases);
  } catch (e) {
    allCases = [];
    document.getElementById("cases-status").style.display = "";
    document.getElementById("cases-status").innerHTML = '<h3>No test cases</h3><p>Generate test cases after running analysis.</p>';
    document.getElementById("cases-table").style.display = "none";
  }
}

function renderCases(cases) {
  if (!cases.length) {
    document.getElementById("cases-status").style.display = "";
    document.getElementById("cases-table").style.display = "none";
    return;
  }
  document.getElementById("cases-status").style.display = "none";
  document.getElementById("cases-table").style.display = "";

  var tbody = document.querySelector("#cases-table tbody");
  tbody.innerHTML = cases.map(function(c) {
    var type = c.type || c.case_type || "functional";
    var status = c.status || "pending";
    return "<tr>" +
      "<td>" + esc(c.id) + "</td>" +
      "<td>" + esc(c.title || c.name || "") + "</td>" +
      "<td><span class='badge badge-dim'>" + esc(type) + "</span></td>" +
      "<td>" + priorityBadge(c.priority) + "</td>" +
      "<td>" + esc(c.feature_id || "") + "</td>" +
      "<td>" + statusBadge(status) + "</td>" +
      "</tr>";
  }).join("");
}

function filterCases() {
  var q = document.getElementById("case-filter").value.toLowerCase();
  if (!q) { renderCases(allCases); return; }
  var filtered = allCases.filter(function(c) {
    return (c.id || "").toLowerCase().indexOf(q) >= 0 ||
           (c.title || c.name || "").toLowerCase().indexOf(q) >= 0 ||
           (c.feature_id || "").toLowerCase().indexOf(q) >= 0;
  });
  renderCases(filtered);
}

async function generateCases() {
  if (!currentProject) { toast("Select a project first", "error"); return; }
  var caseType = document.getElementById("case-type-select").value;
  try {
    var data = await api("POST", "/api/projects/" + encodeURIComponent(currentProject.path) + "/cases", { case_type: caseType });
    allCases = data.cases || [];
    renderCases(allCases);
    toast("Generated " + (data.count || 0) + " cases", "success");
  } catch (e) {
    toast("Generation error: " + e.message, "error");
  }
}

// ---------------------------------------------------------------------------
// Execution
// ---------------------------------------------------------------------------
async function runExecution() {
  if (!currentProject) { toast("Select a project first", "error"); return; }
  var btn = document.getElementById("btn-run");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Running...';
  try {
    var data = await api("POST", "/api/projects/" + encodeURIComponent(currentProject.path) + "/run", { tags: [], parallel: 1 });
    renderExecution(data);
    toast("Tests complete", "success");
  } catch (e) {
    toast("Execution error: " + e.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Run Tests";
  }
}

function renderExecution(data) {
  var summary = data.summary || {};
  var results = data.results || [];

  document.getElementById("execution-status").style.display = "none";
  document.getElementById("execution-summary").style.display = "";
  document.getElementById("execution-table").style.display = "";

  document.getElementById("exec-total").textContent = summary.total || results.length;
  document.getElementById("exec-passed").textContent = summary.passed || 0;
  document.getElementById("exec-failed").textContent = summary.failed || 0;

  var total = summary.total || results.length || 1;
  var pct = Math.round(((summary.passed || 0) / total) * 100);
  document.getElementById("exec-progress").style.width = pct + "%";

  var tbody = document.querySelector("#execution-table tbody");
  tbody.innerHTML = results.map(function(r) {
    return "<tr>" +
      "<td>" + esc(r.case_id || "") + "</td>" +
      "<td>" + statusBadge(r.status || "unknown") + "</td>" +
      "<td>" + (r.duration_ms ? r.duration_ms + "ms" : "-") + "</td>" +
      "<td style='max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>" + esc((r.output || "").substring(0, 200)) + "</td>" +
      "</tr>";
  }).join("");
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------
async function loadReport() {
  if (!currentProject) { toast("Select a project first", "error"); return; }
  var fmt = document.getElementById("report-fmt").value;
  try {
    var data = await api("GET", "/api/projects/" + encodeURIComponent(currentProject.path) + "/report?fmt=" + fmt);
    document.getElementById("report-status").style.display = "none";
    document.getElementById("report-viewer").style.display = "";
    document.getElementById("report-content").textContent = data.report || "Empty report";
    toast("Report generated", "success");
  } catch (e) {
    toast("Report error: " + e.message, "error");
  }

  // Also try loading coverage
  try {
    var cov = await api("GET", "/api/projects/" + encodeURIComponent(currentProject.path) + "/coverage");
    var c = cov.coverage;
    document.getElementById("coverage-section").style.display = "";
    document.getElementById("cov-features").textContent = Math.round(c.feature_coverage_pct) + "%";
    document.getElementById("cov-rules").textContent = Math.round(c.rule_coverage_pct) + "%";
  } catch (e) {
    // Coverage not available, that's ok
  }
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
(function init() {
  // Auto-check health
  api("GET", "/api/health").then(function(data) {
    console.log("TestForge API healthy:", data.version);
  }).catch(function() {
    toast("API not responding", "error");
  });
})();
