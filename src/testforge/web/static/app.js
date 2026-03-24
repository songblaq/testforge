/* TestForge Web GUI -- vanilla JS SPA (redesigned) */

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
var currentProject = null;
var allProjects = [];
var allCases = [];
var manualSession = null;
var _pipelineData = null;
var _lastReportContent = null;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
async function api(method, path, body) {
  var controller = new AbortController();
  var timeoutId = setTimeout(function() { controller.abort(); }, 30000);
  var opts = { method: method, headers: {}, signal: controller.signal };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  var res;
  try {
    res = await fetch(path, opts);
  } catch (err) {
    if (err.name === "AbortError") throw new Error(t("toast.timeout"));
    throw new Error(t("toast.network_error", {msg: err.message}));
  } finally {
    clearTimeout(timeoutId);
  }
  var data;
  try {
    data = await res.json();
  } catch (err) {
    throw new Error(t("toast.invalid_json", {status: res.status}));
  }
  if (!res.ok) {
    var msg = data.detail || JSON.stringify(data);
    throw new Error(msg);
  }
  return data;
}

function encodePath(p) {
  return p.split("/").map(function(s) { return encodeURIComponent(s); }).join("/");
}

function toast(message, type) {
  type = type || "info";
  var container = document.getElementById("toast-container");
  var el = document.createElement("div");
  el.className = "toast toast-" + type;
  el.textContent = message;
  container.appendChild(el);
  var delay = type === "error" ? 6000 : 4000;
  setTimeout(function() { el.remove(); }, delay);
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
  var map = { passed: "badge-green", failed: "badge-red", skipped: "badge-dim", error: "badge-red", pass: "badge-green", fail: "badge-red", pending: "badge-dim" };
  return '<span class="badge ' + (map[s] || "badge-dim") + '">' + esc(s) + "</span>";
}

function tagBadge(tags) {
  if (!tags || !tags.length) return '<span class="badge badge-green">' + esc(t("cases.positive")) + '</span>';
  for (var i = 0; i < tags.length; i++) {
    if (tags[i] === "negative") return '<span class="badge badge-red">' + esc(t("cases.negative")) + '</span>';
    if (tags[i] === "edge") return '<span class="badge badge-yellow">' + esc(t("cases.edge")) + '</span>';
  }
  return '<span class="badge badge-green">' + esc(t("cases.positive")) + '</span>';
}

function classifyTag(tags) {
  if (!tags || !tags.length) return "positive";
  for (var i = 0; i < tags.length; i++) {
    if (tags[i] === "negative") return "negative";
    if (tags[i] === "edge") return "edge";
  }
  return "positive";
}

function formatBytes(bytes) {
  if (bytes === 0) return "0 B";
  var units = ["B", "KB", "MB", "GB"];
  var i = Math.floor(Math.log(bytes) / Math.log(1024));
  if (i >= units.length) i = units.length - 1;
  return (bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1) + " " + units[i];
}

function simpleMarkdown(text) {
  if (!text) return "";
  var lines = text.split("\n");
  var html = [];
  var inCode = false;
  var inList = false;
  var inTable = false;
  var tableRows = [];

  for (var i = 0; i < lines.length; i++) {
    var line = lines[i];

    // Code blocks
    if (line.trim().indexOf("```") === 0) {
      if (inCode) {
        html.push("</code></pre>");
        inCode = false;
      } else {
        if (inList) { html.push("</ul>"); inList = false; }
        if (inTable) { html.push(renderMarkdownTable(tableRows)); inTable = false; tableRows = []; }
        html.push("<pre><code>");
        inCode = true;
      }
      continue;
    }
    if (inCode) {
      html.push(esc(line) + "\n");
      continue;
    }

    // Table rows (lines with |)
    if (line.trim().indexOf("|") === 0 && line.trim().lastIndexOf("|") > 0) {
      if (inList) { html.push("</ul>"); inList = false; }
      // Check if separator row
      if (/^\|[\s\-:|]+\|$/.test(line.trim())) {
        inTable = true;
        continue;
      }
      if (!inTable) inTable = true;
      tableRows.push(line);
      continue;
    } else if (inTable) {
      html.push(renderMarkdownTable(tableRows));
      inTable = false;
      tableRows = [];
    }

    // Close list if not a list item
    if (inList && line.trim() !== "" && line.trim().charAt(0) !== "-" && line.trim().charAt(0) !== "*") {
      html.push("</ul>");
      inList = false;
    }

    // Empty line
    if (line.trim() === "") {
      if (inList) { html.push("</ul>"); inList = false; }
      continue;
    }

    // Headings
    if (line.indexOf("#### ") === 0) { html.push("<h4>" + inlineFormat(esc(line.substring(5))) + "</h4>"); continue; }
    if (line.indexOf("### ") === 0) { html.push("<h3>" + inlineFormat(esc(line.substring(4))) + "</h3>"); continue; }
    if (line.indexOf("## ") === 0) { html.push("<h2>" + inlineFormat(esc(line.substring(3))) + "</h2>"); continue; }
    if (line.indexOf("# ") === 0) { html.push("<h1>" + inlineFormat(esc(line.substring(2))) + "</h1>"); continue; }

    // Horizontal rule
    if (/^---+$/.test(line.trim())) { html.push("<hr>"); continue; }

    // List items
    if (line.trim().charAt(0) === "-" || line.trim().charAt(0) === "*") {
      if (!inList) { html.push("<ul>"); inList = true; }
      var content = esc(line.trim().substring(1).trim());
      content = inlineFormat(content);
      html.push("<li>" + content + "</li>");
      continue;
    }

    // Paragraph
    var pContent = inlineFormat(esc(line));
    html.push("<p>" + pContent + "</p>");
  }

  if (inCode) html.push("</code></pre>");
  if (inList) html.push("</ul>");
  if (inTable) html.push(renderMarkdownTable(tableRows));
  return html.join("\n");
}

function renderMarkdownTable(rows) {
  if (!rows.length) return "";
  var html = '<table>';
  for (var i = 0; i < rows.length; i++) {
    var cells = rows[i].split("|").filter(function(c) { return c.trim() !== ""; });
    var tag = i === 0 ? "th" : "td";
    html += "<tr>";
    for (var j = 0; j < cells.length; j++) {
      html += "<" + tag + ">" + inlineFormat(esc(cells[j].trim())) + "</" + tag + ">";
    }
    html += "</tr>";
  }
  html += "</table>";
  return html;
}

function safeHref(url) {
  if (/^(https?:|mailto:|\/|#|\.)/i.test(url)) return url;
  return '#';
}

function inlineFormat(text) {
  // Bold: **text**
  text = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  // Italic: *text*
  text = text.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  // Inline code: `text`
  text = text.replace(/`([^`]+)`/g, "<code>$1</code>");
  // Links: [text](url)
  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, function(_, text, url) {
    return '<a href="' + safeHref(url) + '" target="_blank" rel="noopener">' + text + '</a>';
  });
  // Images: ![alt](url)
  text = text.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, function(_, alt, url) {
    return '<img src="' + safeHref(url) + '" alt="' + alt + '">';
  });
  return text;
}

// ---------------------------------------------------------------------------
// Detail Panel
// ---------------------------------------------------------------------------
function openDetailPanel(title, bodyHtml) {
  var panel = document.getElementById("detail-panel");
  document.getElementById("detail-title").textContent = title;
  document.getElementById("detail-body").innerHTML = bodyHtml;
  panel.classList.add("open");
}

function closeDetailPanel() {
  var panel = document.getElementById("detail-panel");
  panel.classList.remove("open");
}

function detailField(label, value) {
  return '<div class="detail-field"><div class="detail-field-label">' + esc(label) + '</div><div class="detail-field-value">' + (value || "-") + '</div></div>';
}

function detailTagList(items) {
  if (!items || !items.length) return "-";
  return '<div class="detail-tags">' + items.map(function(item) { return '<span class="badge badge-dim">' + esc(item) + '</span>'; }).join("") + '</div>';
}

// -- Analysis tab details --

function showFeatureDetail(feature) {
  var html =
    detailField(t("th.id"), esc(feature.id)) +
    detailField(t("th.name"), esc(feature.name)) +
    detailField(t("th.category"), esc(feature.category || "")) +
    detailField(t("th.priority"), priorityBadge(feature.priority)) +
    detailField(t("th.description"), esc(feature.description)) +
    detailField(t("detail.tags"), detailTagList(feature.tags)) +
    detailField(t("detail.screens"), feature.screens && feature.screens.length ? esc(feature.screens.join(", ")) : "-") +
    detailField(t("detail.source"), esc(feature.source || ""));
  openDetailPanel(feature.name, html);
}

function showPersonaDetail(persona) {
  var html =
    detailField(t("th.id"), esc(persona.id)) +
    detailField(t("th.name"), esc(persona.name)) +
    detailField(t("th.tech_level"), esc(persona.tech_level || "intermediate")) +
    detailField(t("th.description"), esc(persona.description)) +
    detailField(t("detail.goals"), persona.goals && persona.goals.length ?
      '<ul>' + persona.goals.map(function(g) { return '<li>' + esc(g) + '</li>'; }).join("") + '</ul>' : "-") +
    detailField(t("detail.pain_points"), persona.pain_points && persona.pain_points.length ?
      '<ul>' + persona.pain_points.map(function(p) { return '<li>' + esc(p) + '</li>'; }).join("") + '</ul>' : "-");
  openDetailPanel(persona.name, html);
}

function showRuleDetail(rule) {
  var html =
    detailField(t("th.id"), esc(rule.id)) +
    detailField(t("th.name"), esc(rule.name)) +
    detailField(t("th.description"), esc(rule.description)) +
    detailField(t("detail.condition"), esc(rule.condition || "")) +
    detailField(t("detail.expected_behavior"), esc(rule.expected_behavior || "")) +
    detailField(t("detail.source"), esc(rule.source || ""));
  openDetailPanel(rule.name, html);
}

// -- Cases tab detail --

function showCaseDetail(c) {
  var type = c.type || c.case_type || "functional";
  var status = c.status || "pending";
  var html =
    detailField(t("th.id"), esc(c.id)) +
    detailField(t("th.title"), esc(c.title || c.name || "")) +
    detailField(t("th.description"), esc(c.description || "")) +
    detailField(t("detail.feature_id"), esc(c.feature_id || "")) +
    detailField(t("th.priority"), priorityBadge(c.priority)) +
    detailField(t("th.type"), '<span class="badge badge-dim">' + esc(type) + '</span>') +
    detailField(t("detail.status"), statusBadge(status));

  // Preconditions
  if (c.preconditions && c.preconditions.length) {
    html += detailField(t("detail.preconditions"),
      '<ul>' + c.preconditions.map(function(p) { return '<li>' + esc(p) + '</li>'; }).join("") + '</ul>');
  }

  // Steps
  if (c.steps && c.steps.length) {
    var stepsHtml = '<ol class="detail-steps">';
    for (var i = 0; i < c.steps.length; i++) {
      var s = c.steps[i];
      if (typeof s === "string") {
        stepsHtml += '<li>' + esc(s) + '</li>';
      } else {
        stepsHtml += '<li><strong>' + esc(s.action || s.step || "") + '</strong>';
        if (s.expected_result) stepsHtml += '<br><em>' + esc(t("detail.step.expected")) + ':</em> ' + esc(s.expected_result);
        if (s.input_data) stepsHtml += '<br><em>' + esc(t("detail.step.input")) + ':</em> ' + esc(s.input_data);
        stepsHtml += '</li>';
      }
    }
    stepsHtml += '</ol>';
    html += detailField(t("detail.steps"), stepsHtml);
  }

  // Expected result
  if (c.expected_result) {
    html += detailField(t("detail.expected"), esc(c.expected_result));
  }

  // Tags
  html += detailField(t("detail.tags"), detailTagList(c.tags));

  // Rule IDs
  if (c.rule_ids && c.rule_ids.length) {
    html += detailField(t("detail.rules"), detailTagList(c.rule_ids));
  }

  openDetailPanel(c.title || c.name || c.id, html);

  // Load mapped scripts asynchronously
  if (currentProject && c.id) {
    api("GET", "/api/projects/" + encodePath(currentProject.path) + "/cases/" + encodeURIComponent(c.id) + "/scripts")
      .then(function(data) {
        if (data.scripts && data.scripts.length > 0) {
          var scriptHtml = '<div class="detail-field"><div class="detail-field-label">' + esc(t("detail.mapped_scripts")) + '</div><div class="detail-field-value">';
          scriptHtml += data.scripts.map(function(s) {
            return '<div class="mapped-item">' + esc(s.name) + ' <span class="badge badge-dim">' + s.lines + ' lines</span></div>';
          }).join("");
          scriptHtml += '</div></div>';
          var body = document.getElementById("detail-body");
          if (body) body.innerHTML += scriptHtml;
        }
      }).catch(function() { /* ignore mapping errors */ });
  }
}

// -- Scripts tab detail --

function showScriptDetail(script) {
  var html =
    detailField(t("detail.filename"), esc(script.name || script.file || "")) +
    detailField(t("detail.filesize"), script.size !== undefined ? formatBytes(script.size) : "-") +
    detailField(t("th.lines"), script.lines !== undefined ? String(script.lines) : "-") +
    detailField(t("detail.case_id"), esc(script.case_id || "-"));

  // Code viewer
  if (script.preview) {
    var codeLines = esc(script.preview).split("\n").map(function(line) {
      return '<span class="code-line">' + line + '</span>';
    }).join("\n");
    html += detailField(t("detail.code"),
      '<div class="code-viewer"><pre>' + codeLines + '</pre></div>');
  }

  // Mapped case link
  if (script.case_id && script.case_id !== "-") {
    html += '<div class="detail-field"><div class="detail-field-label">' + esc(t("detail.mapped_case")) + '</div><div class="detail-field-value"><button class="btn btn-sm btn-secondary" data-action="goto-tab" data-tab="cases">' + esc(script.case_id) + ' \u2192</button></div></div>';
  }

  openDetailPanel(script.name || script.file || "Script", html);
}

// -- Execution tab detail --

function showExecutionDetail(result) {
  var html =
    detailField(t("detail.case_id"), esc(result.case_id || "")) +
    detailField(t("detail.status"), statusBadge(result.status || "unknown")) +
    detailField(t("detail.duration"), result.duration_ms ? result.duration_ms + "ms" : "-") +
    detailField(t("detail.output"), result.output ? '<pre>' + esc(result.output) + '</pre>' : "-") +
    detailField(t("detail.stderr"), result.stderr ? '<pre>' + esc(result.stderr) + '</pre>' : "-") +
    detailField(t("detail.returncode"), result.return_code !== undefined ? esc(String(result.return_code)) : "-");
  openDetailPanel(result.case_id || "Result", html);
}

// -- Manual QA tab detail --

function showManualItemDetail(item, result) {
  var itemId = item.id || item.item_id || "";
  var status = result ? result.status : "pending";
  var html =
    detailField(t("th.id"), esc(itemId)) +
    detailField(t("th.description"), esc(item.description || "")) +
    detailField(t("detail.status"), statusBadge(status)) +
    detailField(t("detail.note"), result && result.note ? esc(result.note) : "-");
  if (item.steps) {
    html += detailField(t("detail.steps"), esc(item.steps));
  }
  openDetailPanel(item.title || item.name || itemId, html);
}

// -- Inputs tab detail (enhanced with document viewer) --

function showInputDetail(file) {
  var html =
    detailField(t("detail.filename"), esc(file.name)) +
    detailField(t("detail.filetype"), '<span class="badge badge-dim">' + esc(file.type) + '</span>') +
    detailField(t("detail.filesize"), formatBytes(file.size));

  // Download button
  if (currentProject) {
    html += '<div style="margin-bottom:16px;"><button class="btn btn-secondary btn-sm" id="detail-download-btn">' + esc(t("inputs.download")) + '</button></div>';
  }

  // Content viewer placeholder
  html += '<div id="detail-doc-viewer"></div>';

  openDetailPanel(file.name, html);

  // Bind download
  var dlBtn = document.getElementById("detail-download-btn");
  if (dlBtn) {
    dlBtn.addEventListener("click", function() {
      downloadInputFile(file.name);
    });
  }

  // Load content
  loadInputContent(file);
}

async function loadInputContent(file) {
  if (!currentProject) return;
  var viewer = document.getElementById("detail-doc-viewer");
  if (!viewer) return;

  var ext = (file.type || "").toLowerCase();
  var previewTypes = ["md", "txt", "json", "yaml", "yml", "png", "jpg", "jpeg"];
  if (previewTypes.indexOf(ext) < 0) {
    viewer.innerHTML = '<p style="color:var(--text-dim);">' + esc(t("inputs.preview_unavailable")) + '</p>';
    return;
  }

  try {
    var url = "/api/projects/" + encodePath(currentProject.path) + "/inputs/" + encodeURIComponent(file.name);
    var res = await fetch(url);
    if (!res.ok) throw new Error("Failed to load");

    if (ext === "png" || ext === "jpg" || ext === "jpeg") {
      var blob = await res.blob();
      if (viewer._objectUrl) URL.revokeObjectURL(viewer._objectUrl);
      var imgUrl = URL.createObjectURL(blob);
      viewer._objectUrl = imgUrl;
      viewer.innerHTML = '<div class="doc-viewer-image"><img src="' + imgUrl + '" alt="' + esc(file.name) + '"></div>';
    } else {
      var text = await res.text();
      if (ext === "md") {
        viewer.innerHTML = '<div class="doc-viewer">' + simpleMarkdown(text) + '</div>';
      } else {
        viewer.innerHTML = '<div class="doc-viewer"><pre class="doc-viewer-text">' + esc(text) + '</pre></div>';
      }
    }
  } catch (e) {
    viewer.innerHTML = '<p style="color:var(--text-dim);">' + esc(t("inputs.preview_unavailable")) + '</p>';
  }
}

function downloadInputFile(filename) {
  if (!currentProject) return;
  var url = "/api/projects/" + encodePath(currentProject.path) + "/inputs/" + encodeURIComponent(filename);
  var a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// ---------------------------------------------------------------------------
// Language Select
// ---------------------------------------------------------------------------
function updateLangSelect() {
  var sel = document.getElementById("lang-select");
  if (!sel) return;
  sel.value = getLang();
}

// ---------------------------------------------------------------------------
// Project Management
// ---------------------------------------------------------------------------
async function loadProjects() {
  var dir = document.getElementById("scan-dir").value || ".";
  try {
    var cfg = await api("GET", "/api/config");
    if (cfg.cwd && !document.getElementById("scan-dir").value) {
      document.getElementById("scan-dir").value = cfg.cwd;
      dir = cfg.cwd;
    }
  } catch (e) { /* ignore */ }

  try {
    var data = await api("GET", "/api/projects?directory=" + encodeURIComponent(dir));
    allProjects = data.projects || [];
    renderProjectGrid(allProjects);
    renderProjectDropdown(allProjects);
  } catch (e) {
    toast(t("toast.load_error", {msg: e.message}), "error");
    var container = document.getElementById("project-grid");
    container.innerHTML =
      '<div class="empty-state">' +
        '<h3>' + esc(t("projects.failed")) + '</h3>' +
        '<p>' + esc(e.message) + '</p>' +
        '<button class="btn btn-primary" id="btn-retry-load">' + esc(t("projects.retry")) + '</button>' +
      '</div>';
    var retryBtn = document.getElementById("btn-retry-load");
    if (retryBtn) {
      retryBtn.addEventListener("click", function() { loadProjects(); });
    }
  }
}

function renderProjectGrid(projects) {
  var container = document.getElementById("project-grid");
  if (!projects.length) {
    container.innerHTML = '<div class="empty-state"><h3>' + esc(t("projects.empty")) + '</h3><p>' + esc(t("projects.empty.desc")) + '</p></div>';
    return;
  }

  container.innerHTML = "";
  for (var i = 0; i < projects.length; i++) {
    var p = projects[i];
    var card = document.createElement("div");
    card.className = "project-card";
    card.dataset.index = i;

    var badges = [];
    if (p.has_analysis) badges.push('<span class="badge badge-green">' + esc(t("badge.analyzed")) + '</span>');
    if (p.has_cases) badges.push('<span class="badge badge-blue">' + esc(t("badge.cases")) + '</span>');
    if (p.has_scripts) badges.push('<span class="badge badge-yellow">' + esc(t("badge.scripts")) + '</span>');
    if (p.has_report) badges.push('<span class="badge badge-yellow">' + esc(t("badge.report")) + '</span>');
    if (!badges.length) badges.push('<span class="badge badge-dim">' + esc(t("badge.new")) + '</span>');

    var meta = "";
    if (p.input_count !== undefined) meta += '<span class="badge badge-dim">' + esc(t("projects.docs", {n: p.input_count})) + '</span>';

    card.innerHTML =
      '<div class="project-card-name">' + esc(p.name) + '</div>' +
      '<div class="project-card-path">' + esc(p.path) + '</div>' +
      '<div class="project-card-meta">' + badges.join("") + meta + '</div>' +
      '<div class="project-card-footer"><button class="btn btn-primary btn-sm" data-action="open" data-index="' + i + '">' + esc(t("projects.open")) + '</button></div>';

    container.appendChild(card);
  }

  // Attach event listener via delegation (only once)
  if (!container._clickBound) {
    container._clickBound = true;
    container.addEventListener("click", function(e) {
      var btn = e.target.closest("[data-action='open']");
      if (btn) {
        var idx = parseInt(btn.dataset.index, 10);
        if (allProjects[idx]) selectProject(allProjects[idx]);
      }
    });
  }
}

function renderProjectDropdown(projects) {
  var list = document.getElementById("project-dropdown-list");
  list.innerHTML = "";

  if (!projects.length) {
    list.innerHTML = '<div style="padding:12px;color:var(--text-dim);font-size:13px;text-align:center;">' + esc(t("projects.none")) + '</div>';
    return;
  }

  for (var i = 0; i < projects.length; i++) {
    var item = document.createElement("div");
    item.className = "dropdown-item";
    item.dataset.index = i;
    item.innerHTML =
      '<span class="dropdown-item-name">' + esc(projects[i].name) + '</span>' +
      '<span class="dropdown-item-path">' + esc(projects[i].path) + '</span>';
    list.appendChild(item);
  }

  if (!list._clickBound) {
    list._clickBound = true;
    list.addEventListener("click", function(e) {
      var item = e.target.closest(".dropdown-item");
      if (item) {
        var idx = parseInt(item.dataset.index, 10);
        if (allProjects[idx]) {
          selectProject(allProjects[idx]);
          closeDropdown();
        }
      }
    });
  }

  // Search filter (only register once)
  var searchEl = document.getElementById("project-search");
  if (!searchEl._inputBound) {
    searchEl._inputBound = true;
    searchEl.addEventListener("input", function() {
      var q = this.value.toLowerCase();
      var items = list.querySelectorAll(".dropdown-item");
      for (var i = 0; i < items.length; i++) {
        var name = (allProjects[parseInt(items[i].dataset.index, 10)] || {}).name || "";
        items[i].style.display = name.toLowerCase().indexOf(q) >= 0 ? "" : "none";
      }
    });
  }
}

function selectProject(proj) {
  currentProject = proj;
  allCases = [];
  manualSession = null;
  _pipelineData = null;

  // Update header
  document.getElementById("selected-project-name").textContent = proj.name;

  // Show context bar + tab bar, hide project list
  document.getElementById("context-bar").style.display = "";
  document.getElementById("tab-bar").style.display = "";
  document.getElementById("project-list-view").style.display = "none";

  // Update context bar immediately
  document.getElementById("ctx-name").textContent = proj.name;
  document.getElementById("ctx-inputs").textContent = t("ctx.docs", {n: proj.input_count || 0});
  document.getElementById("ctx-features").textContent = t("ctx.features", {n: "-"});
  document.getElementById("ctx-cases").textContent = t("ctx.cases", {n: "-"});
  document.getElementById("ctx-coverage").textContent = "-";
  document.getElementById("ctx-pipeline").textContent = t("ctx.pipeline", {n: "-"});

  // Mark active in dropdown
  var items = document.querySelectorAll("#project-dropdown-list .dropdown-item");
  for (var i = 0; i < items.length; i++) {
    items[i].classList.toggle("active", allProjects[parseInt(items[i].dataset.index, 10)] === proj);
  }

  // Reset all tab panels
  resetAllTabs();

  // Switch to overview tab (or from hash)
  var hashTab = location.hash.replace("#", "") || "overview";
  switchTab(hashTab);

  // Async context bar update
  updateContextBar();

  toast(t("toast.opened", {name: proj.name}), "info");
}

function deselectProject() {
  currentProject = null;
  allCases = [];
  manualSession = null;
  _pipelineData = null;

  document.getElementById("selected-project-name").textContent = t("project.select");
  document.getElementById("context-bar").style.display = "none";
  document.getElementById("tab-bar").style.display = "none";
  document.getElementById("project-list-view").style.display = "";

  // Hide all tab panels
  document.querySelectorAll(".tab-panel").forEach(function(p) { p.classList.remove("active"); });

  loadProjects();
}

async function updateContextBar() {
  if (!currentProject) return;
  try {
    var data = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/info");
    var info = data.project;
    Object.assign(currentProject, info);
    document.getElementById("ctx-name").textContent = info.name;
    document.getElementById("ctx-inputs").textContent = t("ctx.docs", {n: info.input_count || 0});
  } catch (e) { /* ignore */ }

  // Try to get analysis feature count
  try {
    var analysis = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/analysis");
    var a = analysis.analysis || {};
    var featureCount = (a.features || []).length;
    document.getElementById("ctx-features").textContent = t("ctx.features", {n: featureCount});
  } catch (e) {
    document.getElementById("ctx-features").textContent = t("ctx.features", {n: 0});
  }

  // Try to get case count
  try {
    var cases = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/cases");
    var caseCount = (cases.cases || []).length;
    document.getElementById("ctx-cases").textContent = t("ctx.cases", {n: caseCount});
  } catch (e) {
    document.getElementById("ctx-cases").textContent = t("ctx.cases", {n: 0});
  }

  // Try to get coverage
  try {
    var cov = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/coverage");
    var c = cov.coverage;
    document.getElementById("ctx-coverage").textContent = t("coverage.pct", {n: Math.round(c.feature_coverage_pct)});
  } catch (e) {
    document.getElementById("ctx-coverage").textContent = "-";
  }

  // Pipeline stages count
  try {
    var overview = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/overview");
    _pipelineData = overview;
    var pipeline = overview.pipeline || [];
    var doneCount = 0;
    for (var i = 0; i < pipeline.length; i++) {
      if (pipeline[i].status === "done") doneCount++;
    }
    document.getElementById("ctx-pipeline").textContent = t("ctx.pipeline", {n: doneCount});
  } catch (e) {
    document.getElementById("ctx-pipeline").textContent = t("ctx.pipeline", {n: 0});
  }
}

function resetAllTabs() {
  // Clear inputs table
  var itbody = document.querySelector("#inputs-table tbody");
  if (itbody) itbody.innerHTML = "";
  document.getElementById("inputs-table").style.display = "none";
  document.getElementById("inputs-action").style.display = "none";

  // Analysis
  document.getElementById("analysis-guard").style.display = "none";
  document.getElementById("analysis-empty").style.display = "";
  document.getElementById("analysis-content").style.display = "none";

  // Cases
  document.getElementById("cases-guard").style.display = "none";
  document.getElementById("cases-empty").style.display = "";
  document.getElementById("cases-content").style.display = "none";

  // Scripts
  document.getElementById("scripts-guard").style.display = "none";
  document.getElementById("scripts-empty").style.display = "";
  document.getElementById("scripts-content").style.display = "none";

  // Execution
  document.getElementById("execution-guard").style.display = "none";
  document.getElementById("execution-empty").style.display = "";
  document.getElementById("execution-summary").style.display = "none";

  // Manual
  document.getElementById("manual-empty").style.display = "";
  document.getElementById("manual-content").style.display = "none";
  document.getElementById("btn-manual-finish").style.display = "none";

  // Report
  document.getElementById("report-guard").style.display = "none";
  document.getElementById("report-empty").style.display = "";
  document.getElementById("report-content").style.display = "none";
  document.getElementById("coverage-section").style.display = "none";
  document.getElementById("report-executive-summary").style.display = "none";

  // Hide all bottom CTAs
  document.querySelectorAll(".tab-bottom-cta").forEach(function(el) { el.style.display = "none"; });
}

// ---------------------------------------------------------------------------
// Dropdown
// ---------------------------------------------------------------------------
function toggleDropdown() {
  var dd = document.getElementById("project-dropdown");
  if (dd.style.display === "none") {
    dd.style.display = "";
    document.getElementById("project-search").value = "";
    document.getElementById("project-search").focus();
  } else {
    closeDropdown();
  }
}

function closeDropdown() {
  document.getElementById("project-dropdown").style.display = "none";
}

// Close dropdown when clicking outside
document.addEventListener("click", function(e) {
  var selector = document.getElementById("project-selector");
  if (!selector.contains(e.target)) {
    closeDropdown();
  }
});

// ---------------------------------------------------------------------------
// Tab Switching + URL Hash Routing
// ---------------------------------------------------------------------------
function switchTab(tabName) {
  // Close detail panel when switching tabs
  closeDetailPanel();

  // Update URL hash
  if (location.hash !== "#" + tabName) {
    history.replaceState(null, "", "#" + tabName);
  }

  // Update tab buttons
  document.querySelectorAll(".tab-btn").forEach(function(b) {
    b.classList.toggle("active", b.dataset.tab === tabName);
  });

  // Update panels
  document.querySelectorAll(".tab-panel").forEach(function(p) { p.classList.remove("active"); });
  var panel = document.getElementById("tab-" + tabName);
  if (panel) panel.classList.add("active");

  // Load data for the tab
  switch (tabName) {
    case "overview": loadOverview(); break;
    case "inputs": loadInputs(); break;
    case "analysis": loadAnalysis(); break;
    case "cases": loadCases(); break;
    case "scripts": loadScripts(); break;
    case "execution": loadExecution(); break;
    case "manual": loadManual(); break;
    case "report": loadReport(); break;
  }
}

// Hash change listener
window.addEventListener("hashchange", function() {
  if (currentProject) {
    var tab = location.hash.replace("#", "") || "overview";
    switchTab(tab);
  }
});

// ---------------------------------------------------------------------------
// OVERVIEW TAB
// ---------------------------------------------------------------------------
async function loadOverview() {
  if (!currentProject) return;

  try {
    var data = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/overview");
    _pipelineData = data;
    renderPipelineStepper(data);
    renderOverviewStats(data);
  } catch (e) {
    document.getElementById("pipeline-stepper").innerHTML = '<p style="color:var(--text-dim);text-align:center;">' + esc(e.message) + '</p>';
  }
}

function renderPipelineStepper(data) {
  var pipeline = data.pipeline || [];
  var container = document.getElementById("pipeline-stepper");

  var stageLabels = {
    inputs: t("stepper.inputs"),
    analysis: t("stepper.analysis"),
    cases: t("stepper.cases"),
    scripts: t("stepper.scripts"),
    execution: t("stepper.execution"),
    report: t("stepper.report")
  };

  var stageIcons = {
    inputs: "1",
    analysis: "2",
    cases: "3",
    scripts: "4",
    execution: "5",
    report: "6"
  };

  var tabMap = {
    inputs: "inputs",
    analysis: "analysis",
    cases: "cases",
    scripts: "scripts",
    execution: "execution",
    report: "report"
  };

  var html = "";
  var foundNext = false;

  for (var i = 0; i < pipeline.length; i++) {
    var stage = pipeline[i];
    var isDone = stage.status === "done";
    var isActive = false;

    if (!isDone && !foundNext) {
      isActive = true;
      foundNext = true;
    }

    var stateClass = isDone ? "done" : (isActive ? "active" : "");
    var icon = isDone ? "\u2713" : stageIcons[stage.stage] || String(i + 1);
    var statusText = isDone ? t("stepper.done") : (isActive ? t("stepper.ready") : t("stepper.waiting"));
    var countText = getStageCount(stage);

    html +=
      '<div class="pipeline-step ' + stateClass + '" data-tab="' + (tabMap[stage.stage] || stage.stage) + '">' +
        '<div class="pipeline-step-connector"></div>' +
        '<div class="pipeline-step-icon">' + icon + '</div>' +
        '<div class="pipeline-step-label">' + esc(stageLabels[stage.stage] || stage.stage) + '</div>' +
        '<div class="pipeline-step-count">' + esc(countText) + '</div>' +
        '<div class="pipeline-step-status">' + esc(statusText) + '</div>' +
      '</div>';
  }

  container.innerHTML = html;

  // Show next action CTA
  var ctaContainer = document.getElementById("overview-next-cta");
  if (!foundNext) {
    // All done
    ctaContainer.style.display = "";
    ctaContainer.innerHTML = '<p style="color:var(--green);font-size:14px;">' + esc(t("overview.all_done")) + '</p>';
  } else {
    // Find first non-done stage
    for (var j = 0; j < pipeline.length; j++) {
      if (pipeline[j].status !== "done") {
        var nextTab = tabMap[pipeline[j].stage] || pipeline[j].stage;
        var nextLabel = stageLabels[pipeline[j].stage] || pipeline[j].stage;
        ctaContainer.style.display = "";
        ctaContainer.innerHTML = '<button class="btn btn-accent" data-action="goto-tab" data-tab="' + nextTab + '">\u2192 ' + esc(nextLabel) + '</button>';
        break;
      }
    }
  }
}

function getStageCount(stage) {
  if (stage.count !== undefined) {
    if (stage.stage === "inputs") return t("stepper.docs", {n: stage.count});
    if (stage.stage === "scripts") return t("stepper.scripts", {n: stage.count});
    return String(stage.count);
  }
  if (stage.summary) {
    if (stage.stage === "analysis") {
      return t("stepper.features", {n: stage.summary.features || 0});
    }
    if (stage.stage === "cases") {
      return t("stepper.cases", {n: stage.summary.total || 0});
    }
    if (stage.stage === "execution") {
      var total = stage.summary.total || 0;
      if (total > 0) return t("stepper.runs", {n: total});
    }
  }
  return t("stepper.no_data");
}

function renderOverviewStats(data) {
  var pipeline = data.pipeline || [];
  var statsContainer = document.getElementById("overview-stats");
  var statsCard = document.getElementById("overview-stats-card");

  var cards = [];
  for (var i = 0; i < pipeline.length; i++) {
    var stage = pipeline[i];
    var value = "-";
    var label = "";

    if (stage.stage === "inputs") {
      value = stage.count !== undefined ? String(stage.count) : "-";
      label = t("stepper.inputs");
    } else if (stage.stage === "analysis" && stage.summary) {
      value = String(stage.summary.features || 0);
      label = t("stepper.features", {n: ""}).replace(/\s*$/, "");
    } else if (stage.stage === "cases" && stage.summary) {
      value = String(stage.summary.total || 0);
      label = t("stepper.cases", {n: ""}).replace(/\s*$/, "");
    } else if (stage.stage === "scripts") {
      value = stage.count !== undefined ? String(stage.count) : "-";
      label = t("stepper.scripts", {n: ""}).replace(/\s*$/, "");
    } else if (stage.stage === "execution" && stage.summary && stage.summary.total) {
      value = String(stage.summary.passed || 0) + "/" + String(stage.summary.total || 0);
      label = t("exec.passed");
    } else {
      continue;
    }

    cards.push(
      '<div class="stat-card">' +
        '<div class="stat-value">' + esc(value) + '</div>' +
        '<div class="stat-label">' + esc(label) + '</div>' +
      '</div>'
    );
  }

  if (cards.length > 0) {
    statsCard.style.display = "";
    statsContainer.innerHTML = cards.join("");
  } else {
    statsCard.style.display = "none";
  }
}

// ---------------------------------------------------------------------------
// Tab Bottom CTA helper
// ---------------------------------------------------------------------------
function showTabBottomCta(tabName, doneText, nextText, nextTab) {
  var ctaEl = document.getElementById(tabName + "-next-cta");
  if (!ctaEl) return;
  ctaEl.style.display = "";
  ctaEl.innerHTML =
    '<span class="cta-done-text">\u2713 ' + esc(doneText) + '</span>' +
    '<button class="btn btn-accent btn-sm" data-action="goto-tab" data-tab="' + nextTab + '">' + esc(nextText) + '</button>';
}

// ---------------------------------------------------------------------------
// INPUTS TAB
// ---------------------------------------------------------------------------
async function loadInputs() {
  if (!currentProject) return;
  try {
    var data = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/inputs");
    var files = data.files || [];
    renderInputs(files);
  } catch (e) {
    renderInputs([]);
  }
}

var _renderedInputFiles = [];

function renderInputs(files) {
  _renderedInputFiles = files;
  var table = document.getElementById("inputs-table");
  var tbody = table.querySelector("tbody");
  var action = document.getElementById("inputs-action");

  if (!files.length) {
    table.style.display = "none";
    action.style.display = "none";
    document.getElementById("inputs-next-cta").style.display = "none";
    return;
  }

  table.style.display = "";
  action.style.display = "";

  tbody.innerHTML = "";
  for (var i = 0; i < files.length; i++) {
    var f = files[i];
    var tr = document.createElement("tr");
    tr.className = "clickable-row";
    tr.dataset.detailIndex = i;
    tr.innerHTML =
      "<td><span class='badge badge-dim'>" + esc(f.type) + "</span></td>" +
      "<td>" + esc(f.name) + "</td>" +
      "<td>" + formatBytes(f.size) + "</td>" +
      '<td>' +
        '<button class="btn btn-secondary btn-sm" data-action="download-input" data-name="' + esc(f.name) + '" style="margin-right:4px;">' + esc(t("inputs.download")) + '</button>' +
        '<button class="btn btn-danger btn-sm" data-action="delete-input" data-name="' + esc(f.name) + '">' + esc(t("common.delete")) + '</button>' +
      '</td>';
    tbody.appendChild(tr);
  }

  // Show bottom CTA
  showTabBottomCta("inputs", t("cta.done_inputs"), t("cta.next_analysis"), "analysis");

  // Delegation for buttons and row clicks (only once)
  if (!tbody._clickBound) {
    tbody._clickBound = true;
    tbody.addEventListener("click", function(e) {
      var dlBtn = e.target.closest("[data-action='download-input']");
      if (dlBtn) {
        downloadInputFile(dlBtn.dataset.name);
        return;
      }
      var delBtn = e.target.closest("[data-action='delete-input']");
      if (delBtn) {
        handleInputDelete(e);
        return;
      }
      var row = e.target.closest("tr.clickable-row");
      if (row) {
        var idx = parseInt(row.dataset.detailIndex, 10);
        var item = _renderedInputFiles[idx];
        if (item) showInputDetail(item);
      }
    });
  }
}

function handleInputDelete(e) {
  var btn = e.target.closest("[data-action='delete-input']");
  if (!btn) return;
  var name = btn.dataset.name;
  deleteInput(name);
}

async function deleteInput(filename) {
  if (!currentProject) return;
  if (!confirm(t("inputs.confirm_delete", {name: filename}))) return;
  try {
    await api("DELETE", "/api/inputs?project_path=" + encodeURIComponent(currentProject.path) + "&filename=" + encodeURIComponent(filename));
    toast(t("toast.deleted", {name: filename}), "success");
    loadInputs();
    updateContextBar();
  } catch (e) {
    toast(t("toast.delete_error", {msg: e.message}), "error");
  }
}

async function uploadFiles(fileList) {
  if (!currentProject || !fileList || !fileList.length) return;

  var uploaded = 0;
  var errors = 0;

  for (var i = 0; i < fileList.length; i++) {
    var formData = new FormData();
    formData.append("file", fileList[i]);
    try {
      var res = await fetch("/api/projects/" + encodePath(currentProject.path) + "/inputs", {
        method: "POST",
        body: formData
      });
      if (!res.ok) {
        var errData = await res.json().catch(function() { return {}; });
        throw new Error(errData.detail || "Upload failed");
      }
      uploaded++;
    } catch (e) {
      errors++;
      toast(t("toast.upload_error", {name: fileList[i].name, msg: e.message}), "error");
    }
  }

  if (uploaded > 0) {
    toast(t("toast.uploaded", {n: uploaded}), "success");
    loadInputs();
    updateContextBar();
  }

  document.getElementById("file-upload").value = "";
}

// ---------------------------------------------------------------------------
// ANALYSIS TAB
// ---------------------------------------------------------------------------
async function loadAnalysis() {
  if (!currentProject) return;

  // Guard: check if inputs exist
  if (currentProject.input_count === 0) {
    document.getElementById("analysis-guard").style.display = "";
    document.getElementById("analysis-empty").style.display = "none";
    document.getElementById("analysis-content").style.display = "none";
    document.getElementById("btn-analyze").disabled = true;
    document.getElementById("analysis-next-cta").style.display = "none";
    return;
  }

  document.getElementById("analysis-guard").style.display = "none";
  document.getElementById("btn-analyze").disabled = false;

  try {
    var data = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/analysis");
    renderAnalysis(data.analysis);
  } catch (e) {
    document.getElementById("analysis-empty").style.display = "";
    document.getElementById("analysis-content").style.display = "none";
    document.getElementById("analysis-next-cta").style.display = "none";
  }
}

var _analysisData = null;

function renderAnalysis(analysis) {
  _analysisData = analysis;
  if (!analysis || (!analysis.features && !analysis.personas && !analysis.rules)) {
    document.getElementById("analysis-empty").style.display = "";
    document.getElementById("analysis-content").style.display = "none";
    document.getElementById("analysis-next-cta").style.display = "none";
    return;
  }

  document.getElementById("analysis-empty").style.display = "none";
  document.getElementById("analysis-content").style.display = "";

  var features = analysis.features || [];
  var personas = analysis.personas || [];
  var rules = analysis.rules || [];

  // Summary cards (#7)
  var summaryHtml = '';
  var highCount = 0, medCount = 0, lowCount = 0;
  var catMap = {};
  for (var fi = 0; fi < features.length; fi++) {
    var pri = (features[fi].priority || "medium").toLowerCase();
    if (pri === "high") highCount++;
    else if (pri === "low") lowCount++;
    else medCount++;
    var cat = features[fi].category || "Uncategorized";
    catMap[cat] = (catMap[cat] || 0) + 1;
  }

  summaryHtml +=
    '<div class="stat-card"><div class="stat-value">' + features.length + '</div><div class="stat-label">' + esc(t("analysis.summary.features")) + '</div>' +
    '<div class="stat-sub">' + esc(t("analysis.summary.high", {n: highCount})) + ' / ' + esc(t("analysis.summary.medium", {n: medCount})) + ' / ' + esc(t("analysis.summary.low", {n: lowCount})) + '</div></div>';
  summaryHtml +=
    '<div class="stat-card"><div class="stat-value">' + personas.length + '</div><div class="stat-label">' + esc(t("analysis.summary.personas")) + '</div></div>';
  summaryHtml +=
    '<div class="stat-card"><div class="stat-value">' + rules.length + '</div><div class="stat-label">' + esc(t("analysis.summary.rules")) + '</div></div>';

  document.getElementById("analysis-summary-cards").innerHTML = summaryHtml;

  // Features table
  var ftbody = document.querySelector("#features-table tbody");
  ftbody.innerHTML = features.map(function(f, i) {
    var catBadge = '<span class="badge badge-dim" title="' + esc(f.category || "") + '">' + esc(f.category || "") + '</span>';
    return '<tr class="clickable-row" data-detail-type="feature" data-detail-index="' + i + '"><td>' + esc(f.id) + "</td><td>" + esc(f.name) + "</td><td>" + catBadge + "</td><td>" + priorityBadge(f.priority) + "</td><td>" + esc((f.description || "").substring(0, 80)) + "</td></tr>";
  }).join("");

  if (!ftbody._clickBound) {
    ftbody._clickBound = true;
    ftbody.addEventListener("click", function(e) {
      var row = e.target.closest("tr.clickable-row");
      if (row && _analysisData) {
        var idx = parseInt(row.dataset.detailIndex, 10);
        var item = (_analysisData.features || [])[idx];
        if (item) showFeatureDetail(item);
      }
    });
  }

  // Personas table
  var ptbody = document.querySelector("#personas-table tbody");
  ptbody.innerHTML = personas.map(function(p, i) {
    return '<tr class="clickable-row" data-detail-type="persona" data-detail-index="' + i + '"><td>' + esc(p.id) + "</td><td>" + esc(p.name) + "</td><td>" + esc(p.tech_level) + "</td><td>" + esc(p.description) + "</td></tr>";
  }).join("");

  if (!ptbody._clickBound) {
    ptbody._clickBound = true;
    ptbody.addEventListener("click", function(e) {
      var row = e.target.closest("tr.clickable-row");
      if (row && _analysisData) {
        var idx = parseInt(row.dataset.detailIndex, 10);
        var item = (_analysisData.personas || [])[idx];
        if (item) showPersonaDetail(item);
      }
    });
  }

  // Rules table
  var rtbody = document.querySelector("#rules-table tbody");
  rtbody.innerHTML = rules.map(function(r, i) {
    return '<tr class="clickable-row" data-detail-type="rule" data-detail-index="' + i + '"><td>' + esc(r.id) + "</td><td>" + esc(r.name) + "</td><td>" + esc(r.condition) + "</td><td>" + esc(r.expected_behavior) + "</td></tr>";
  }).join("");

  if (!rtbody._clickBound) {
    rtbody._clickBound = true;
    rtbody.addEventListener("click", function(e) {
      var row = e.target.closest("tr.clickable-row");
      if (row && _analysisData) {
        var idx = parseInt(row.dataset.detailIndex, 10);
        var item = (_analysisData.rules || [])[idx];
        if (item) showRuleDetail(item);
      }
    });
  }

  // Bottom CTA
  showTabBottomCta("analysis", t("cta.done_analysis"), t("cta.next_cases"), "cases");
}

async function runAnalysis() {
  if (!currentProject) { toast(t("toast.select_project"), "error"); return; }
  var btn = document.getElementById("btn-analyze");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> ' + esc(t("common.analyzing"));
  try {
    await api("POST", "/api/projects/" + encodePath(currentProject.path) + "/analysis", {});
    toast(t("toast.analysis_complete"), "success");
    try {
      var info = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/info");
      Object.assign(currentProject, info.project);
    } catch (e) { /* ignore */ }
    loadAnalysis();
    updateContextBar();
  } catch (e) {
    toast(t("toast.analysis_error", {msg: e.message}), "error");
  } finally {
    btn.disabled = false;
    btn.textContent = t("analysis.run");
  }
}

// ---------------------------------------------------------------------------
// CASES TAB
// ---------------------------------------------------------------------------
async function loadCases() {
  if (!currentProject) return;

  if (!currentProject.has_analysis) {
    document.getElementById("cases-guard").style.display = "";
    document.getElementById("cases-empty").style.display = "none";
    document.getElementById("cases-content").style.display = "none";
    document.getElementById("btn-generate").disabled = true;
    document.getElementById("cases-next-cta").style.display = "none";
    return;
  }

  document.getElementById("cases-guard").style.display = "none";
  document.getElementById("btn-generate").disabled = false;

  try {
    var data = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/cases");
    allCases = data.cases || [];
    renderCases(allCases);
  } catch (e) {
    allCases = [];
    document.getElementById("cases-empty").style.display = "";
    document.getElementById("cases-content").style.display = "none";
    document.getElementById("cases-next-cta").style.display = "none";
  }
}

var _renderedCases = [];

function renderCases(cases) {
  _renderedCases = cases;
  if (!cases.length) {
    document.getElementById("cases-empty").style.display = "";
    document.getElementById("cases-content").style.display = "none";
    document.getElementById("cases-next-cta").style.display = "none";
    return;
  }

  document.getElementById("cases-empty").style.display = "none";
  document.getElementById("cases-content").style.display = "";

  var tbody = document.querySelector("#cases-table tbody");
  tbody.innerHTML = cases.map(function(c, i) {
    var type = c.type || c.case_type || "functional";
    var status = c.status || "pending";
    return '<tr class="clickable-row" data-detail-index="' + i + '">' +
      "<td>" + esc(c.id) + "</td>" +
      "<td>" + esc(c.title || c.name || "") + "</td>" +
      "<td><span class='badge badge-dim'>" + esc(type) + "</span></td>" +
      "<td>" + tagBadge(c.tags) + "</td>" +
      "<td>" + priorityBadge(c.priority) + "</td>" +
      "<td>" + esc(c.feature_id || "") + "</td>" +
      "<td>" + statusBadge(status) + "</td>" +
      "</tr>";
  }).join("");

  if (!tbody._clickBound) {
    tbody._clickBound = true;
    tbody.addEventListener("click", function(e) {
      var row = e.target.closest("tr.clickable-row");
      if (row) {
        var idx = parseInt(row.dataset.detailIndex, 10);
        var item = _renderedCases[idx];
        if (item) showCaseDetail(item);
      }
    });
  }

  // Bottom CTA
  showTabBottomCta("cases", t("cta.done_cases"), t("cta.next_scripts"), "scripts");
}

function filterCases() {
  var q = document.getElementById("case-filter").value.toLowerCase();
  var typeVal = document.getElementById("case-type-select").value;
  var tagVal = document.getElementById("case-tag-select").value;

  var filtered = allCases.filter(function(c) {
    // Text filter
    if (q) {
      var match = (c.id || "").toLowerCase().indexOf(q) >= 0 ||
             (c.title || c.name || "").toLowerCase().indexOf(q) >= 0 ||
             (c.feature_id || "").toLowerCase().indexOf(q) >= 0 ||
             (c.description || "").toLowerCase().indexOf(q) >= 0;
      if (!match) return false;
    }
    // Type filter
    if (typeVal !== "all") {
      var caseType = c.type || c.case_type || "functional";
      if (caseType !== typeVal) return false;
    }
    // Tag filter
    if (tagVal !== "all") {
      var cTag = classifyTag(c.tags);
      if (tagVal === "positive" && cTag !== "positive") return false;
      if (tagVal === "negative" && cTag !== "negative") return false;
      if (tagVal === "edge" && cTag !== "edge") return false;
      if (tagVal === "smoke" && (!c.tags || c.tags.indexOf("smoke") < 0)) return false;
      if (tagVal === "regression" && (!c.tags || c.tags.indexOf("regression") < 0)) return false;
    }
    return true;
  });
  renderCases(filtered);
}

async function generateCases() {
  if (!currentProject) { toast(t("toast.select_project"), "error"); return; }
  var caseType = document.getElementById("case-type-select").value;
  var btn = document.getElementById("btn-generate");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> ' + esc(t("common.generating"));
  try {
    var data = await api("POST", "/api/projects/" + encodePath(currentProject.path) + "/cases", { case_type: caseType });
    allCases = data.cases || [];
    renderCases(allCases);
    toast(t("toast.generated_cases", {n: data.count || 0}), "success");
    try {
      var info = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/info");
      Object.assign(currentProject, info.project);
    } catch (e) { /* ignore */ }
    updateContextBar();
  } catch (e) {
    toast(t("toast.generation_error", {msg: e.message}), "error");
  } finally {
    btn.disabled = false;
    btn.textContent = t("cases.generate");
  }
}

// ---------------------------------------------------------------------------
// SCRIPTS TAB
// ---------------------------------------------------------------------------
var _renderedScripts = [];

async function loadScripts() {
  if (!currentProject) return;

  if (!currentProject.has_cases) {
    document.getElementById("scripts-guard").style.display = "";
    document.getElementById("scripts-empty").style.display = "none";
    document.getElementById("scripts-content").style.display = "none";
    document.getElementById("btn-gen-scripts").disabled = true;
    document.getElementById("scripts-next-cta").style.display = "none";
    return;
  }

  document.getElementById("scripts-guard").style.display = "none";
  document.getElementById("btn-gen-scripts").disabled = false;

  try {
    var data = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/scripts");
    var scripts = data.scripts || [];
    _renderedScripts = scripts;

    if (scripts.length === 0) {
      document.getElementById("scripts-empty").style.display = "";
      document.getElementById("scripts-content").style.display = "none";
      document.getElementById("scripts-next-cta").style.display = "none";
      return;
    }

    document.getElementById("scripts-empty").style.display = "none";
    document.getElementById("scripts-content").style.display = "";

    // Summary cards (#9)
    var totalLines = 0;
    var totalSize = 0;
    for (var i = 0; i < scripts.length; i++) {
      totalLines += scripts[i].lines || 0;
      totalSize += scripts[i].size || 0;
    }

    document.getElementById("scripts-summary-cards").innerHTML =
      '<div class="stat-card"><div class="stat-value">' + scripts.length + '</div><div class="stat-label">' + esc(t("scripts.summary.total")) + '</div></div>' +
      '<div class="stat-card"><div class="stat-value">' + totalLines + '</div><div class="stat-label">' + esc(t("scripts.summary.lines")) + '</div></div>' +
      '<div class="stat-card"><div class="stat-value">' + formatBytes(totalSize) + '</div><div class="stat-label">' + esc(t("scripts.summary.size")) + '</div></div>';

    var tbody = document.querySelector("#scripts-table tbody");
    tbody.innerHTML = scripts.map(function(s, i) {
      return '<tr class="clickable-row" data-detail-index="' + i + '">' +
        '<td>' + esc(s.name || "") + '</td>' +
        '<td>' + (s.lines || "-") + '</td>' +
        '<td>' + esc(s.case_id || "-") + '</td>' +
        '<td>' + (s.size !== undefined ? formatBytes(s.size) : "-") + '</td>' +
        '</tr>';
    }).join("");

    if (!tbody._clickBound) {
      tbody._clickBound = true;
      tbody.addEventListener("click", function(e) {
        var row = e.target.closest("tr.clickable-row");
        if (row) {
          var idx = parseInt(row.dataset.detailIndex, 10);
          var item = _renderedScripts[idx];
          if (item) showScriptDetail(item);
        }
      });
    }

    // Bottom CTA
    showTabBottomCta("scripts", t("cta.done_scripts"), t("cta.next_execution"), "execution");
  } catch (e) {
    document.getElementById("scripts-empty").style.display = "";
    document.getElementById("scripts-content").style.display = "none";
    document.getElementById("scripts-next-cta").style.display = "none";
  }
}

async function generateScripts() {
  if (!currentProject) { toast(t("toast.select_project"), "error"); return; }
  var btn = document.getElementById("btn-gen-scripts");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> ' + esc(t("common.generating"));
  try {
    var data = await api("POST", "/api/projects/" + encodePath(currentProject.path) + "/scripts", { force: false });
    var scripts = data.scripts || [];
    _renderedScripts = scripts;
    toast(t("toast.generated_scripts", {n: scripts.length}), "success");
    try {
      var info = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/info");
      Object.assign(currentProject, info.project);
    } catch (e) { /* ignore */ }
    loadScripts();
  } catch (e) {
    toast(t("toast.script_error", {msg: e.message}), "error");
  } finally {
    btn.disabled = false;
    btn.textContent = t("scripts.generate");
  }
}

// ---------------------------------------------------------------------------
// EXECUTION TAB
// ---------------------------------------------------------------------------
async function loadExecution() {
  if (!currentProject) return;

  if (!currentProject.has_scripts) {
    document.getElementById("execution-guard").style.display = "";
    document.getElementById("execution-empty").style.display = "none";
    document.getElementById("execution-summary").style.display = "none";
    document.getElementById("btn-run").disabled = true;
    document.getElementById("execution-next-cta").style.display = "none";
    return;
  }

  document.getElementById("execution-guard").style.display = "none";
  document.getElementById("btn-run").disabled = false;

  try {
    var data = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/run");
    if (data.run && data.run.total > 0) {
      document.getElementById("execution-empty").style.display = "none";
      document.getElementById("execution-summary").style.display = "";
      document.getElementById("exec-total").textContent = data.run.total || 0;
      document.getElementById("exec-passed").textContent = data.run.passed || 0;
      document.getElementById("exec-failed").textContent = data.run.failed || 0;
      var total = data.run.total || 1;
      var pct = Math.round(((data.run.passed || 0) / total) * 100);
      document.getElementById("exec-progress").style.width = pct + "%";
      if (data.run.results) {
        _renderedExecResults = data.run.results;
        var tbody = document.querySelector("#execution-table tbody");
        tbody.innerHTML = data.run.results.map(function(r, i) {
          return '<tr class="clickable-row" data-detail-index="' + i + '">' +
            '<td>' + esc(r.case_id || "") + '</td>' +
            '<td>' + statusBadge(r.status || "unknown") + '</td>' +
            '<td>' + (r.duration_ms ? r.duration_ms + "ms" : "-") + '</td>' +
            '<td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + esc((r.output || "").substring(0, 200)) + '</td>' +
            '</tr>';
        }).join("");
      }
      showTabBottomCta("execution", t("cta.done_execution"), t("cta.next_report"), "report");
    } else {
      document.getElementById("execution-empty").style.display = "";
      document.getElementById("execution-summary").style.display = "none";
      document.getElementById("execution-next-cta").style.display = "none";
    }
  } catch (e) {
    document.getElementById("execution-empty").style.display = "";
    document.getElementById("execution-summary").style.display = "none";
    document.getElementById("execution-next-cta").style.display = "none";
  }
}

async function runExecution() {
  if (!currentProject) { toast(t("toast.select_project"), "error"); return; }
  var btn = document.getElementById("btn-run");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> ' + esc(t("common.running"));
  try {
    var data = await api("POST", "/api/projects/" + encodePath(currentProject.path) + "/run", { tags: [], parallel: 1 });
    renderExecution(data);
    toast(t("toast.tests_complete"), "success");
  } catch (e) {
    toast(t("toast.execution_error", {msg: e.message}), "error");
  } finally {
    btn.disabled = false;
    btn.textContent = t("exec.run");
  }
}

var _renderedExecResults = [];

function renderExecution(data) {
  var summary = data.summary || {};
  var results = data.results || [];
  _renderedExecResults = results;

  document.getElementById("execution-empty").style.display = "none";
  document.getElementById("execution-summary").style.display = "";

  document.getElementById("exec-total").textContent = summary.total || results.length;
  document.getElementById("exec-passed").textContent = summary.passed || 0;
  document.getElementById("exec-failed").textContent = summary.failed || 0;

  var total = summary.total || results.length || 1;
  var pct = Math.round(((summary.passed || 0) / total) * 100);
  document.getElementById("exec-progress").style.width = pct + "%";

  var tbody = document.querySelector("#execution-table tbody");
  tbody.innerHTML = results.map(function(r, i) {
    return '<tr class="clickable-row" data-detail-index="' + i + '">' +
      "<td>" + esc(r.case_id || "") + "</td>" +
      "<td>" + statusBadge(r.status || "unknown") + "</td>" +
      "<td>" + (r.duration_ms ? r.duration_ms + "ms" : "-") + "</td>" +
      "<td style='max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>" + esc((r.output || "").substring(0, 200)) + "</td>" +
      "</tr>";
  }).join("");

  if (!tbody._clickBound) {
    tbody._clickBound = true;
    tbody.addEventListener("click", function(e) {
      var row = e.target.closest("tr.clickable-row");
      if (row) {
        var idx = parseInt(row.dataset.detailIndex, 10);
        var item = _renderedExecResults[idx];
        if (item) showExecutionDetail(item);
      }
    });
  }

  showTabBottomCta("execution", t("cta.done_execution"), t("cta.next_report"), "report");
}

// ---------------------------------------------------------------------------
// MANUAL QA TAB
// ---------------------------------------------------------------------------
async function loadManual() {
  if (!currentProject) return;

  if (!currentProject.has_cases && !currentProject.has_analysis) {
    document.getElementById("manual-guard").style.display = "";
    document.getElementById("manual-empty").style.display = "none";
    document.getElementById("manual-content").style.display = "none";
    document.getElementById("btn-manual-start").disabled = true;
    return;
  }
  document.getElementById("manual-guard").style.display = "none";
  document.getElementById("btn-manual-start").disabled = false;

  try {
    var data = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/manual/progress");
    var progress = data.progress;
    if (progress) {
      manualSession = progress;
      document.getElementById("manual-empty").style.display = "none";
      document.getElementById("manual-content").style.display = "";
      document.getElementById("btn-manual-finish").style.display = "";
      renderManualItems(progress.items || [], progress.results || {});
      updateManualProgress(progress);
    } else {
      showManualEmpty();
    }
  } catch (e) {
    showManualEmpty();
  }
}

function showManualEmpty() {
  manualSession = null;
  document.getElementById("manual-empty").style.display = "";
  document.getElementById("manual-content").style.display = "none";
  document.getElementById("btn-manual-finish").style.display = "none";
  document.getElementById("manual-next-cta").style.display = "none";
}

async function startManualSession() {
  if (!currentProject) { toast(t("toast.select_project"), "error"); return; }
  var btn = document.getElementById("btn-manual-start");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> ' + esc(t("common.starting"));
  try {
    var data = await api("POST", "/api/projects/" + encodePath(currentProject.path) + "/manual/start");
    manualSession = data;
    document.getElementById("manual-empty").style.display = "none";
    document.getElementById("manual-content").style.display = "";
    document.getElementById("btn-manual-finish").style.display = "";
    renderManualItems(data.items || [], {});
    document.getElementById("manual-total").textContent = data.item_count || 0;
    document.getElementById("manual-checked").textContent = "0";
    document.getElementById("manual-progress").style.width = "0%";
    updateManualStatsText(0, data.item_count || 0);
    toast(t("toast.manual_started"), "success");
  } catch (e) {
    toast(t("toast.manual_start_error", {msg: e.message}), "error");
  } finally {
    btn.disabled = false;
    btn.textContent = t("manual.start");
  }
}

var _renderedManualItems = [];
var _renderedManualResults = {};

function renderManualItems(items, results) {
  _renderedManualItems = items;
  _renderedManualResults = results;
  var container = document.getElementById("manual-items");
  container.innerHTML = "";

  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    var itemId = item.id || item.item_id || ("item-" + i);
    var result = results[itemId] || null;

    var div = document.createElement("div");
    div.className = "manual-item";
    if (result) {
      div.classList.add(result.status === "pass" ? "checked-pass" : "checked-fail");
    }
    div.dataset.itemId = itemId;
    div.dataset.detailIndex = i;

    div.innerHTML =
      '<div class="manual-item-header" style="cursor:pointer;" data-action="manual-detail" data-detail-index="' + i + '">' +
        '<div>' +
          '<div class="manual-item-title">' + esc(item.title || item.name || itemId) + '</div>' +
          '<div class="manual-item-id">' + esc(itemId) + '</div>' +
        '</div>' +
      '</div>' +
      (item.description ? '<div class="manual-item-desc">' + esc(item.description) + '</div>' : '') +
      (item.steps ? '<div class="manual-item-desc">' + esc(item.steps) + '</div>' : '') +
      '<div class="manual-item-actions">' +
        '<input type="text" class="manual-note" data-item-id="' + esc(itemId) + '" placeholder="' + esc(t("manual.note")) + '" value="' + esc(result ? result.note || "" : "") + '">' +
        '<button class="btn-pass' + (result && result.status === "pass" ? " active" : "") + '" data-action="manual-pass" data-item-id="' + esc(itemId) + '">' + esc(t("manual.pass")) + '</button>' +
        '<button class="btn-fail' + (result && result.status === "fail" ? " active" : "") + '" data-action="manual-fail" data-item-id="' + esc(itemId) + '">' + esc(t("manual.fail")) + '</button>' +
      '</div>';

    container.appendChild(div);
  }

  if (!container._clickBound) {
    container._clickBound = true;
    container.addEventListener("click", function(e) {
      var passBtn = e.target.closest("[data-action='manual-pass']");
      var failBtn = e.target.closest("[data-action='manual-fail']");
      var detailBtn = e.target.closest("[data-action='manual-detail']");
      if (passBtn) {
        var id = passBtn.dataset.itemId;
        var note = container.querySelector("input[data-item-id='" + id + "']");
        checkManualItem(id, "pass", note ? note.value : "");
      } else if (failBtn) {
        var id2 = failBtn.dataset.itemId;
        var note2 = container.querySelector("input[data-item-id='" + id2 + "']");
        checkManualItem(id2, "fail", note2 ? note2.value : "");
      } else if (detailBtn) {
        var idx = parseInt(detailBtn.dataset.detailIndex, 10);
        var item = _renderedManualItems[idx];
        if (item) {
          var itemId = item.id || item.item_id || ("item-" + idx);
          var result = _renderedManualResults[itemId] || null;
          showManualItemDetail(item, result);
        }
      }
    });
  }
}

async function checkManualItem(itemId, status, note) {
  if (!currentProject) return;
  try {
    var data = await api("PUT", "/api/projects/" + encodePath(currentProject.path) + "/manual/check/" + encodeURIComponent(itemId), { status: status, note: note || "" });

    var itemDiv = document.querySelector(".manual-item[data-item-id='" + itemId + "']");
    if (itemDiv) {
      itemDiv.classList.remove("checked-pass", "checked-fail");
      itemDiv.classList.add(status === "pass" ? "checked-pass" : "checked-fail");
      var passBtn = itemDiv.querySelector("[data-action='manual-pass']");
      var failBtn = itemDiv.querySelector("[data-action='manual-fail']");
      if (passBtn) passBtn.classList.toggle("active", status === "pass");
      if (failBtn) failBtn.classList.toggle("active", status === "fail");
    }

    document.getElementById("manual-checked").textContent = data.checked || 0;
    document.getElementById("manual-total").textContent = data.total || 0;
    updateManualStatsText(data.checked || 0, data.total || 0);
    var pct = data.total > 0 ? Math.round((data.checked / data.total) * 100) : 0;
    document.getElementById("manual-progress").style.width = pct + "%";
  } catch (e) {
    toast(t("toast.manual_check_error", {msg: e.message}), "error");
  }
}

function updateManualStatsText(checked, total) {
  var el = document.getElementById("manual-stats-text");
  if (el) {
    el.textContent = t("manual.items", {checked: checked, total: total});
  }
}

function updateManualProgress(progress) {
  var checked = 0;
  var total = (progress.items || []).length;
  var results = progress.results || {};
  for (var key in results) {
    if (results.hasOwnProperty(key)) checked++;
  }
  document.getElementById("manual-checked").textContent = checked;
  document.getElementById("manual-total").textContent = total;
  updateManualStatsText(checked, total);
  var pct = total > 0 ? Math.round((checked / total) * 100) : 0;
  document.getElementById("manual-progress").style.width = pct + "%";
}

async function finishManualSession() {
  if (!currentProject) return;
  try {
    var data = await api("POST", "/api/projects/" + encodePath(currentProject.path) + "/manual/finish");
    toast(t("toast.manual_finished", {path: data.report_path || t("report.saved")}), "success");
    showManualEmpty();
    manualSession = null;
    showTabBottomCta("manual", t("cta.done_manual"), t("cta.next_report"), "report");
  } catch (e) {
    toast(t("toast.manual_finish_error", {msg: e.message}), "error");
  }
}

// ---------------------------------------------------------------------------
// REPORT TAB
// ---------------------------------------------------------------------------
async function loadReport() {
  if (!currentProject) { toast(t("toast.select_project"), "error"); return; }
  var fmt = document.getElementById("report-fmt").value;
  var btn = document.getElementById("btn-load-report");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> ' + esc(t("common.loading"));
  try {
    var data = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/report?fmt=" + fmt);
    _lastReportContent = { content: data.report || "", fmt: fmt };
    document.getElementById("report-empty").style.display = "none";
    document.getElementById("report-guard").style.display = "none";
    document.getElementById("report-content").style.display = "";
    document.getElementById("btn-download-report").style.display = "";

    var viewer = document.getElementById("report-viewer");
    if (fmt === "html") {
      viewer.textContent = data.report || "Empty report";
    } else {
      viewer.innerHTML = simpleMarkdown(data.report || "Empty report");
    }
    toast(t("toast.report_loaded"), "success");
  } catch (e) {
    toast(t("toast.report_error", {msg: e.message}), "error");
  } finally {
    btn.disabled = false;
    btn.textContent = t("report.load");
  }

  // Load coverage
  loadCoverage();
  // Load executive summary
  loadExecutiveSummary();
}

async function loadCoverage() {
  if (!currentProject) return;
  try {
    var cov = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/coverage");
    var c = cov.coverage;
    document.getElementById("coverage-section").style.display = "";
    document.getElementById("cov-features").textContent = Math.round(c.feature_coverage_pct) + "%";
    document.getElementById("cov-rules").textContent = Math.round(c.rule_coverage_pct) + "%";
  } catch (e) {
    // Coverage not available
  }
}

async function loadExecutiveSummary() {
  if (!currentProject) return;
  var summaryEl = document.getElementById("report-executive-summary");
  try {
    var runData = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/run");
    if (runData.run && runData.run.total > 0) {
      var run = runData.run;
      var passRate = run.total > 0 ? Math.round((run.passed / run.total) * 100) : 0;
      summaryEl.style.display = "";
      summaryEl.innerHTML =
        '<div class="stat-card"><div class="stat-value">' + (run.total || 0) + '</div><div class="stat-label">' + esc(t("report.total_cases")) + '</div></div>' +
        '<div class="stat-card stat-pass"><div class="stat-value">' + (run.passed || 0) + '</div><div class="stat-label">' + esc(t("exec.passed")) + '</div></div>' +
        '<div class="stat-card stat-fail"><div class="stat-value">' + (run.failed || 0) + '</div><div class="stat-label">' + esc(t("exec.failed")) + '</div></div>' +
        '<div class="stat-card"><div class="stat-value">' + passRate + '%</div><div class="stat-label">' + esc(t("report.pass_rate")) + '</div></div>';
    }
  } catch (e) {
    summaryEl.style.display = "none";
  }
}

function downloadReport() {
  if (!_lastReportContent) return;
  var ext = _lastReportContent.fmt === "html" ? ".html" : ".md";
  var mime = _lastReportContent.fmt === "html" ? "text/html" : "text/markdown";
  var blob = new Blob([_lastReportContent.content], { type: mime });
  var url = URL.createObjectURL(blob);
  var a = document.createElement("a");
  a.href = url;
  a.download = "testforge-report" + ext;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ---------------------------------------------------------------------------
// Create Project Modal
// ---------------------------------------------------------------------------
function showCreateModal() {
  document.getElementById("create-modal").style.display = "flex";
  document.getElementById("new-project-name").value = "";
  document.getElementById("new-project-model").value = "";
  document.getElementById("new-project-name").focus();
}

function hideCreateModal() {
  document.getElementById("create-modal").style.display = "none";
}

async function createProject() {
  var name = document.getElementById("new-project-name").value.trim();
  if (!name) { toast(t("toast.name_required"), "error"); return; }
  var dir = document.getElementById("new-project-dir").value || ".";
  var provider = document.getElementById("new-project-provider").value;
  var model = document.getElementById("new-project-model").value.trim();

  try {
    await api("POST", "/api/projects", { name: name, directory: dir, provider: provider, model: model });
    hideCreateModal();
    toast(t("toast.project_created", {name: name}), "success");
    document.getElementById("scan-dir").value = dir;
    loadProjects();
  } catch (e) {
    toast(t("toast.project_error", {msg: e.message}), "error");
  }
}

// ---------------------------------------------------------------------------
// Global CTA delegation (guard buttons, pipeline steps, tab bottom CTAs)
// ---------------------------------------------------------------------------
document.addEventListener("click", function(e) {
  // Guard CTA buttons
  var guardBtn = e.target.closest(".guard-cta-btn");
  if (guardBtn && guardBtn.dataset.guardTab) {
    switchTab(guardBtn.dataset.guardTab);
    return;
  }

  // Pipeline step clicks
  var step = e.target.closest(".pipeline-step");
  if (step && step.dataset.tab) {
    switchTab(step.dataset.tab);
    return;
  }

  // Tab bottom CTA and overview CTA buttons
  var ctaBtn = e.target.closest("[data-action='goto-tab']");
  if (ctaBtn && ctaBtn.dataset.tab) {
    switchTab(ctaBtn.dataset.tab);
    return;
  }

  // Context bar clickable stats
  var ctxStat = e.target.closest(".ctx-clickable");
  if (ctxStat && ctxStat.dataset.tab && currentProject) {
    switchTab(ctxStat.dataset.tab);
    return;
  }
});

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
(function init() {
  // Apply i18n translations on load
  applyTranslations();
  updateLangSelect();

  // Language select
  document.getElementById("lang-select").addEventListener("change", function() {
    setLang(this.value);
    applyTranslations();
    updateLangSelect();
    if (currentProject) {
      var activeTab = document.querySelector(".tab-btn.active");
      if (activeTab) switchTab(activeTab.dataset.tab);
      updateContextBar();
    } else {
      renderProjectGrid(allProjects);
    }
  });

  // Event listeners (NO inline handlers)
  document.getElementById("btn-new-project").addEventListener("click", showCreateModal);
  document.getElementById("btn-scan").addEventListener("click", function() { loadProjects(); });
  document.getElementById("modal-close").addEventListener("click", hideCreateModal);
  document.getElementById("modal-cancel").addEventListener("click", hideCreateModal);
  document.getElementById("modal-create").addEventListener("click", createProject);
  document.getElementById("project-dropdown-btn").addEventListener("click", toggleDropdown);
  document.getElementById("btn-analyze").addEventListener("click", runAnalysis);
  document.getElementById("btn-generate").addEventListener("click", generateCases);
  document.getElementById("btn-gen-scripts").addEventListener("click", generateScripts);
  document.getElementById("btn-run").addEventListener("click", runExecution);
  document.getElementById("btn-load-report").addEventListener("click", loadReport);
  document.getElementById("btn-download-report").addEventListener("click", downloadReport);
  document.getElementById("btn-manual-start").addEventListener("click", startManualSession);
  document.getElementById("btn-manual-finish").addEventListener("click", finishManualSession);
  document.getElementById("btn-run-analysis-from-inputs").addEventListener("click", function() {
    switchTab("analysis");
    runAnalysis();
  });
  document.getElementById("case-filter").addEventListener("input", filterCases);
  document.getElementById("case-type-select").addEventListener("change", filterCases);
  document.getElementById("case-tag-select").addEventListener("change", filterCases);
  document.getElementById("file-upload").addEventListener("change", function(e) {
    uploadFiles(e.target.files);
  });

  // Drop zone
  var dz = document.getElementById("drop-zone");
  dz.addEventListener("dragover", function(e) {
    e.preventDefault();
    dz.classList.add("drag-over");
  });
  dz.addEventListener("dragleave", function() {
    dz.classList.remove("drag-over");
  });
  dz.addEventListener("drop", function(e) {
    e.preventDefault();
    dz.classList.remove("drag-over");
    uploadFiles(e.dataTransfer.files);
  });

  // Tab switching
  document.querySelectorAll(".tab-btn").forEach(function(btn) {
    btn.addEventListener("click", function() {
      switchTab(btn.dataset.tab);
    });
  });

  // Detail panel close button
  document.getElementById("detail-close").addEventListener("click", closeDetailPanel);

  // ESC to close modal and detail panel
  document.addEventListener("keydown", function(e) {
    if (e.key === "Escape") {
      closeDetailPanel();
      hideCreateModal();
    }
  });

  // Modal overlay click to close
  document.getElementById("create-modal").addEventListener("click", function(e) {
    if (e.target === this) hideCreateModal();
  });

  // Logo click returns to project list
  document.querySelector(".logo").addEventListener("click", function() {
    if (currentProject) deselectProject();
  });

  // Load projects on init
  loadProjects();
})();
