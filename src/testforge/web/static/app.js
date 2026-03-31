/* TestForge Web GUI -- vanilla JS SPA (redesigned) */

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
var currentProject = null;
var allProjects = [];
var allCases = [];
var casesPage = 1;
var casesPerPage = 50;
var casesTotal = 0;
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

async function withLoading(buttonId, asyncFn) {
  var btn = document.getElementById(buttonId);
  if (!btn) return asyncFn();
  var original = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> ' + btn.textContent.trim();
  try {
    return await asyncFn();
  } finally {
    btn.disabled = false;
    btn.innerHTML = original;
  }
}

function toast(message, type) {
  type = type || "info";
  var container = document.getElementById("toast-container");
  var el = document.createElement("div");
  el.className = "toast toast-" + type;
  el.textContent = message;
  if (type === "error") {
    el.setAttribute("role", "alert");
    el.setAttribute("aria-live", "assertive");
  }
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

function formatDuration(ms) {
  if (ms == null) return "-";
  if (ms < 1000) return ms + "ms";
  if (ms < 60000) return (ms / 1000).toFixed(1) + "s";
  var m = Math.floor(ms / 60000);
  var s = Math.round((ms % 60000) / 1000);
  return m + "m " + s + "s";
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
  var out = html.join("\n");
  out = out.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, "");
  out = out.replace(/on\w+\s*=\s*["'][^"']*["']/gi, "");
  return out;
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
  if (!url) return "";
  url = url.trim();
  if (url.startsWith("//")) return "";  // block protocol-relative
  if (url.startsWith("http://") || url.startsWith("https://") || url.startsWith("mailto:") || url.startsWith("/") || url.startsWith("#") || url.startsWith(".")) return url;
  return "";
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
    return '<img src="' + safeHref(url) + '" alt="' + esc(alt) + '">';
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
  var closeBtn = document.getElementById("detail-close");
  if (closeBtn) closeBtn.focus();
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

  // Load mapped scripts asynchronously with drill-down links
  if (currentProject && c.id) {
    api("GET", "/api/projects/" + encodePath(currentProject.path) + "/cases/" + encodeURIComponent(c.id) + "/scripts")
      .then(function(data) {
        if (data.scripts && data.scripts.length > 0) {
          var scriptHtml = '<div class="detail-field"><div class="detail-field-label">' + esc(t("detail.mapped_scripts")) + '</div><div class="detail-field-value"><div class="detail-drill-links">';
          scriptHtml += data.scripts.map(function(s) {
            var srcClass = s.mapping_source === "authoritative" ? "authoritative" : "heuristic";
            return '<button class="drill-link" data-action="goto-script" data-script-name="' + esc(s.name) + '">' + esc(s.name) + ' <span class="mapping-badge ' + srcClass + '">' + esc(s.mapping_source) + '</span></button>';
          }).join("");
          scriptHtml += '</div></div></div>';
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

  // Mapped cases with drill-down
  var mappedCases = script.mapped_cases || [];
  if (mappedCases.length > 0) {
    html += '<div class="detail-field"><div class="detail-field-label">' + esc(t("detail.mapped_case")) + '</div><div class="detail-field-value"><div class="detail-drill-links">';
    html += mappedCases.map(function(m) {
      var srcClass = m.source === "authoritative" || m.source === "generated" ? "authoritative" : (m.source === "manual" ? "manual" : "heuristic");
      return '<button class="drill-link" data-action="goto-case" data-case-id="' + esc(m.case_id) + '">' + esc(m.case_id) + ' <span class="mapping-badge ' + srcClass + '">' + esc(m.source) + '</span></button>';
    }).join("");
    html += '</div></div></div>';
  } else if (script.case_id && script.case_id !== "-") {
    html += '<div class="detail-field"><div class="detail-field-label">' + esc(t("detail.mapped_case")) + '</div><div class="detail-field-value"><button class="drill-link" data-action="goto-case" data-case-id="' + esc(script.case_id) + '">' + esc(script.case_id) + ' ' + esc(t("nav.goto_case")) + '</button></div></div>';
  }

  // Edit button
  html += '<div style="margin-top:12px;"><button class="btn btn-secondary btn-sm" data-action="edit-current-script">' + esc(t("crud.edit")) + '</button></div>';

  openDetailPanel(script.name || script.file || "Script", html);
}

// -- Execution tab detail --

function showExecutionDetail(result) {
  var rc = result.returncode !== undefined ? result.returncode : result.return_code;
  var durMs = result.duration_ms != null ? result.duration_ms : result.duration;
  var html =
    detailField(t("detail.case_id"), esc(result.case_id || "")) +
    detailField(t("detail.status"), statusBadge(result.status || "unknown")) +
    detailField(t("detail.duration"), formatDuration(durMs)) +
    detailField(t("detail.output"), result.output ? '<pre>' + esc(result.output) + '</pre>' : "-");
  if (result.stderr) {
    html += '<div class="stderr-box"><strong>' + esc(t("detail.stderr")) + ':</strong><pre>' + esc(result.stderr) + "</pre></div>";
  } else {
    html += detailField(t("detail.stderr"), "-");
  }
  var returncodeVal = "-";
  if (rc !== undefined && rc !== null) {
    returncodeVal = rc !== 0
      ? '<span class="badge badge-danger">exit ' + esc(String(rc)) + "</span>"
      : esc(String(rc));
  }
  html += detailField(t("detail.returncode"), returncodeVal);
  if (result.script_name) {
    html += detailField(
      t("detail.filename"),
      esc(result.script_name) +
        ' <a href="#" class="goto-script" data-script="' +
        esc(result.script_name) +
        '">' +
        esc(t("nav.goto_script")) +
        "</a>"
    );
  }
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
  casesPage = 1;
  casesTotal = 0;
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
  casesPage = 1;
  casesTotal = 0;
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
  var isOpen;
  if (dd.style.display === "none") {
    dd.style.display = "";
    document.getElementById("project-search").value = "";
    document.getElementById("project-search").focus();
    isOpen = true;
  } else {
    closeDropdown();
    isOpen = false;
  }
  var btn = document.getElementById("project-dropdown-btn");
  if (btn) btn.setAttribute("aria-expanded", isOpen ? "true" : "false");
}

function closeDropdown() {
  document.getElementById("project-dropdown").style.display = "none";
  var btn = document.getElementById("project-dropdown-btn");
  if (btn) btn.setAttribute("aria-expanded", "false");
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
    var on = b.dataset.tab === tabName;
    b.classList.toggle("active", on);
    b.setAttribute("aria-selected", on ? "true" : "false");
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
    case "report":
      loadReportHistory();
      loadCoverage();
      syncReportGenerateHint();
      break;
  }
}

function syncReportGenerateHint() {
  var emptyEl = document.getElementById("report-empty");
  if (!emptyEl || emptyEl.style.display === "none") return;
  var hint = document.getElementById("report-click-to-generate");
  if (!hint) {
    hint = document.createElement("p");
    hint.id = "report-click-to-generate";
    emptyEl.appendChild(hint);
  }
  hint.textContent = t("report.click_to_generate");
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
  if (!currentProject) {
    document.getElementById("pipeline-stepper").innerHTML =
      '<div class="welcome-state"><h2>' + esc(t("welcome.title")) + '</h2>' +
      '<p>' + esc(t("welcome.desc")) + '</p>' +
      '<button class="btn btn-primary" onclick="document.getElementById(\'btn-new-project\').click()">' + esc(t("welcome.create")) + '</button></div>';
    return;
  }

  var overviewData = null;
  try {
    var data = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/overview");
    overviewData = data;
    _pipelineData = data;
    renderPipelineStepper(data);
    renderOverviewStats(data);
  } catch (e) {
    document.getElementById("pipeline-stepper").innerHTML = '<p style="color:var(--text-dim);text-align:center;">' + esc(e.message) + '</p>';
  }
  await loadLlmConfig();
  if (overviewData) await checkLLMSetup(overviewData);
}

async function checkLLMSetup(overview) {
  if (!currentProject || !overview) return;
  try {
    var pipeline = overview.pipeline || [];
    var analysisStage = null;
    for (var i = 0; i < pipeline.length; i++) {
      if (pipeline[i].stage === "analysis") {
        analysisStage = pipeline[i];
        break;
      }
    }
    var ban = document.getElementById("llm-setup-banner");
    if (ban) {
      ban.style.display = (analysisStage && analysisStage.status === "empty") ? "" : "none";
    }
  } catch (e) {
    /* ignore */
  }
}

async function loadLlmConfig() {
  if (!currentProject) return;
  var card = document.getElementById("llm-config-card");
  if (!card) return;
  card.style.display = "";
  try {
    var data = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/config");
    var cfg = data.config || {};
    var sel = document.getElementById("llm-provider-select");
    var inp = document.getElementById("llm-model-input");
    if (sel) sel.value = cfg.llm_provider || "anthropic";
    if (inp) inp.value = cfg.llm_model || "";
    var banProv = document.getElementById("llm-provider");
    var banModel = document.getElementById("llm-model");
    if (banProv) banProv.value = cfg.llm_provider || "anthropic";
    if (banModel) banModel.value = cfg.llm_model || "";
  } catch (e) {
    /* ignore — card still visible for setting */
  }
}

async function saveLlmConfig() {
  if (!currentProject) return;
  var provider = document.getElementById("llm-provider-select").value;
  var model = document.getElementById("llm-model-input").value.trim();
  try {
    await api("PUT", "/api/projects/" + encodePath(currentProject.path) + "/config", {
      llm_provider: provider,
      llm_model: model,
    });
    var banProv = document.getElementById("llm-provider");
    var banModel = document.getElementById("llm-model");
    if (banProv) banProv.value = provider;
    if (banModel) banModel.value = model;
    toast(t("llm.saved"), "success");
  } catch (e) {
    toast(e.message, "error");
  }
}

async function testLlmConnection() {
  if (!currentProject) return;
  var bar = document.getElementById("llm-status-bar");
  if (bar) { bar.style.display = ""; bar.textContent = t("llm.testing"); }
  try {
    var data = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/config/test");
    var icon = data.status === "connected" || data.status === "configured" ? "✓" : data.status === "warning" ? "⚠" : "✗";
    var color = data.status === "connected" || data.status === "configured" ? "var(--success)" : data.status === "warning" ? "#f0a500" : "var(--danger)";
    if (bar) { bar.style.display = ""; bar.style.color = color; bar.textContent = icon + " " + data.message; }
  } catch (e) {
    if (bar) { bar.style.display = ""; bar.style.color = "var(--danger)"; bar.textContent = "✗ " + e.message; }
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
      '<button type="button" class="pipeline-step ' + stateClass + '" data-tab="' + (tabMap[stage.stage] || stage.stage) + '">' +
        '<span class="pipeline-step-connector" aria-hidden="true"></span>' +
        '<span class="pipeline-step-icon" aria-hidden="true">' + icon + '</span>' +
        '<span class="pipeline-step-label">' + esc(stageLabels[stage.stage] || stage.stage) + '</span>' +
        '<span class="pipeline-step-count">' + esc(countText) + '</span>' +
        '<span class="pipeline-step-status">' + esc(statusText) + '</span>' +
      '</button>';
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
    if (stage.stage === "scripts") return t("stepper.scripts_count", {n: stage.count});
    return String(stage.count);
  }
  if (stage.summary) {
    if (stage.stage === "analysis") {
      return t("stepper.features", {n: stage.summary.features || 0});
    }
    if (stage.stage === "cases") {
      return t("stepper.cases_count", {n: stage.summary.total || 0});
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
      label = t("stepper.cases_count", {n: ""}).replace(/\s*$/, "");
    } else if (stage.stage === "scripts") {
      value = stage.count !== undefined ? String(stage.count) : "-";
      label = t("stepper.scripts");
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
    if (e.message && !e.message.includes("404")) toast(e.message, "error");
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

async function addUrlInput() {
  if (!currentProject) { toast(t("toast.select_project"), "error"); return; }
  var urlEl = document.getElementById("url-input");
  var url = (urlEl.value || "").trim();
  if (!url) return;
  try {
    await api("POST", "/api/projects/" + encodePath(currentProject.path) + "/inputs/url", { url: url });
    toast(t("toast.url_added", { url: url }), "success");
    urlEl.value = "";
    loadInputs();
    updateContextBar();
  } catch (e) {
    toast(t("toast.url_error", { msg: e.message }), "error");
  }
}

async function addRepoInput() {
  if (!currentProject) { toast(t("toast.select_project"), "error"); return; }
  var repoEl = document.getElementById("repo-input");
  var repo = (repoEl.value || "").trim();
  if (!repo) return;
  try {
    await api("POST", "/api/projects/" + encodePath(currentProject.path) + "/inputs/repo", { repo: repo });
    toast(t("toast.repo_added", { repo: repo }), "success");
    repoEl.value = "";
    loadInputs();
    updateContextBar();
  } catch (e) {
    toast(t("toast.repo_error", { msg: e.message }), "error");
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
    if (e.message && !e.message.includes("404")) toast(e.message, "error");
  }
}

var _analysisData = null;

function renderAnalysis(analysis) {
  _analysisData = analysis;
  var isEmpty = !analysis ||
    ((!analysis.features || analysis.features.length === 0) &&
     (!analysis.personas || analysis.personas.length === 0) &&
     (!analysis.rules || analysis.rules.length === 0));
  if (isEmpty) {
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
    return '<tr class="clickable-row" data-detail-type="feature" data-detail-index="' + i + '"><td>' + esc(f.id) + "</td><td>" + esc(f.name) + "</td><td>" + catBadge + "</td><td>" + priorityBadge(f.priority) + "</td><td>" + esc((f.description || "").substring(0, 80)) + '</td><td class="row-actions"><button class="btn-icon" data-action="edit-feature" data-detail-index="' + i + '" aria-label="Edit">&#9998;</button><button class="btn-icon btn-icon-danger" data-action="delete-feature" data-entity-id="' + esc(f.id) + '" aria-label="Delete">&#128465;</button></td></tr>';
  }).join("");

  if (!ftbody._clickBound) {
    ftbody._clickBound = true;
    ftbody.addEventListener("click", function(e) {
      var editBtn = e.target.closest("[data-action='edit-feature']");
      if (editBtn && _analysisData) {
        var idx = parseInt(editBtn.dataset.detailIndex, 10);
        var item = (_analysisData.features || [])[idx];
        if (item) showCrudModal("feature", item);
        return;
      }
      var delBtn = e.target.closest("[data-action='delete-feature']");
      if (delBtn) {
        deleteAnalysisEntity("features", delBtn.dataset.entityId);
        return;
      }
      var row = e.target.closest("tr.clickable-row");
      if (row && _analysisData) {
        var idx2 = parseInt(row.dataset.detailIndex, 10);
        var item2 = (_analysisData.features || [])[idx2];
        if (item2) showFeatureDetail(item2);
      }
    });
  }

  // Personas table
  var ptbody = document.querySelector("#personas-table tbody");
  ptbody.innerHTML = personas.map(function(p, i) {
    return '<tr class="clickable-row" data-detail-type="persona" data-detail-index="' + i + '"><td>' + esc(p.id) + "</td><td>" + esc(p.name) + "</td><td>" + esc(p.tech_level) + "</td><td>" + esc(p.description) + '</td><td class="row-actions"><button class="btn-icon" data-action="edit-persona" data-detail-index="' + i + '" aria-label="Edit">&#9998;</button><button class="btn-icon btn-icon-danger" data-action="delete-persona" data-entity-id="' + esc(p.id) + '" aria-label="Delete">&#128465;</button></td></tr>';
  }).join("");

  if (!ptbody._clickBound) {
    ptbody._clickBound = true;
    ptbody.addEventListener("click", function(e) {
      var editBtn = e.target.closest("[data-action='edit-persona']");
      if (editBtn && _analysisData) {
        var idx = parseInt(editBtn.dataset.detailIndex, 10);
        var item = (_analysisData.personas || [])[idx];
        if (item) showCrudModal("persona", item);
        return;
      }
      var delBtn = e.target.closest("[data-action='delete-persona']");
      if (delBtn) {
        deleteAnalysisEntity("personas", delBtn.dataset.entityId);
        return;
      }
      var row = e.target.closest("tr.clickable-row");
      if (row && _analysisData) {
        var idx2 = parseInt(row.dataset.detailIndex, 10);
        var item2 = (_analysisData.personas || [])[idx2];
        if (item2) showPersonaDetail(item2);
      }
    });
  }

  // Rules table
  var rtbody = document.querySelector("#rules-table tbody");
  rtbody.innerHTML = rules.map(function(r, i) {
    return '<tr class="clickable-row" data-detail-type="rule" data-detail-index="' + i + '"><td>' + esc(r.id) + "</td><td>" + esc(r.name) + "</td><td>" + esc(r.condition) + "</td><td>" + esc(r.expected_behavior) + '</td><td class="row-actions"><button class="btn-icon" data-action="edit-rule" data-detail-index="' + i + '" aria-label="Edit">&#9998;</button><button class="btn-icon btn-icon-danger" data-action="delete-rule" data-entity-id="' + esc(r.id) + '" aria-label="Delete">&#128465;</button></td></tr>';
  }).join("");

  if (!rtbody._clickBound) {
    rtbody._clickBound = true;
    rtbody.addEventListener("click", function(e) {
      var editBtn = e.target.closest("[data-action='edit-rule']");
      if (editBtn && _analysisData) {
        var idx = parseInt(editBtn.dataset.detailIndex, 10);
        var item = (_analysisData.rules || [])[idx];
        if (item) showCrudModal("rule", item);
        return;
      }
      var delBtn = e.target.closest("[data-action='delete-rule']");
      if (delBtn) {
        deleteAnalysisEntity("rules", delBtn.dataset.entityId);
        return;
      }
      var row = e.target.closest("tr.clickable-row");
      if (row && _analysisData) {
        var idx2 = parseInt(row.dataset.detailIndex, 10);
        var item2 = (_analysisData.rules || [])[idx2];
        if (item2) showRuleDetail(item2);
      }
    });
  }

  // Bottom CTA
  showTabBottomCta("analysis", t("cta.done_analysis"), t("cta.next_cases"), "cases");
}

async function runAnalysis() {
  if (!currentProject) { toast(t("toast.select_project"), "error"); return; }
  return withLoading("btn-analyze", async function() {
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
    }
  });
}

// ---------------------------------------------------------------------------
// CASES TAB
// ---------------------------------------------------------------------------
function updateCasesExportVisibility() {
  var exportBtn = document.getElementById("btn-export-cases");
  if (exportBtn) {
    exportBtn.style.display = casesTotal > 0 || (allCases && allCases.length > 0) ? "" : "none";
  }
}

function isCasesFilterActive() {
  var filterInput = document.getElementById("case-filter");
  var q = (filterInput && filterInput.value || "").trim().toLowerCase();
  var typeVal = document.getElementById("case-type-select").value;
  var tagVal = document.getElementById("case-tag-select").value;
  return !!(q || typeVal !== "all" || tagVal !== "all");
}

function applyCasesFiltersToList(list) {
  var filterInput = document.getElementById("case-filter");
  var q = (filterInput && filterInput.value || "").trim().toLowerCase();
  var typeVal = document.getElementById("case-type-select").value;
  var tagVal = document.getElementById("case-tag-select").value;

  return list.filter(function(c) {
    if (q) {
      var match = (c.id || "").toLowerCase().indexOf(q) >= 0 ||
             (c.title || c.name || "").toLowerCase().indexOf(q) >= 0 ||
             (c.feature_id || "").toLowerCase().indexOf(q) >= 0 ||
             (c.description || "").toLowerCase().indexOf(q) >= 0;
      if (!match) return false;
    }
    if (typeVal !== "all") {
      var caseType = c.type || c.case_type || "functional";
      if (caseType !== typeVal) return false;
    }
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
}

function renderCasesPager() {
  var pager = document.getElementById("cases-pager");
  if (!pager) return;
  if (isCasesFilterActive() || casesTotal <= casesPerPage) {
    pager.innerHTML = "";
    return;
  }
  var totalPages = Math.ceil(casesTotal / casesPerPage);
  pager.innerHTML = '<button type="button" class="btn btn-sm" ' + (casesPage <= 1 ? "disabled" : "") +
    ' onclick="casesPage--; loadCases();">&laquo; ' + esc(t("pager.prev")) + "</button>" +
    " <span>" + casesPage + " / " + totalPages + "</span> " +
    '<button type="button" class="btn btn-sm" ' + (casesPage >= totalPages ? "disabled" : "") +
    ' onclick="casesPage++; loadCases();">' + esc(t("pager.next")) + " &raquo;</button>";
}

async function loadCases() {
  if (!currentProject) return;

  if (!currentProject.has_analysis) {
    document.getElementById("cases-guard").style.display = "";
    document.getElementById("cases-empty").style.display = "none";
    document.getElementById("cases-content").style.display = "none";
    document.getElementById("btn-generate").disabled = true;
    document.getElementById("cases-next-cta").style.display = "none";
    casesTotal = 0;
    var pgGuard = document.getElementById("cases-pager");
    if (pgGuard) pgGuard.innerHTML = "";
    updateCasesExportVisibility();
    return;
  }

  document.getElementById("cases-guard").style.display = "none";
  document.getElementById("btn-generate").disabled = false;

  try {
    var base = "/api/projects/" + encodePath(currentProject.path) + "/cases";
    var data;
    if (isCasesFilterActive()) {
      data = await api("GET", base);
      allCases = data.cases || [];
      casesTotal = data.count != null ? data.count : allCases.length;
      renderCases(applyCasesFiltersToList(allCases));
    } else {
      var qs = "?page=" + encodeURIComponent(casesPage) + "&per_page=" + encodeURIComponent(casesPerPage);
      data = await api("GET", base + qs);
      allCases = data.cases || [];
      casesTotal = data.total != null ? data.total : allCases.length;
      var totalPages = Math.max(1, Math.ceil(casesTotal / casesPerPage) || 1);
      if (casesPage > totalPages && casesTotal > 0) {
        casesPage = totalPages;
        return loadCases();
      }
      renderCases(allCases);
    }
    updateCasesExportVisibility();
  } catch (e) {
    allCases = [];
    casesTotal = 0;
    document.getElementById("cases-empty").style.display = "";
    document.getElementById("cases-content").style.display = "none";
    document.getElementById("cases-next-cta").style.display = "none";
    var pgErr = document.getElementById("cases-pager");
    if (pgErr) pgErr.innerHTML = "";
    updateCasesExportVisibility();
  }
}

var _renderedCases = [];

function renderCases(cases) {
  _renderedCases = cases;
  updateCasesExportVisibility();
  if (!cases.length) {
    document.getElementById("cases-empty").style.display = "";
    document.getElementById("cases-content").style.display = "none";
    document.getElementById("cases-next-cta").style.display = "none";
    renderCasesPager();
    return;
  }

  document.getElementById("cases-empty").style.display = "none";
  document.getElementById("cases-content").style.display = "";

  var tbody = document.querySelector("#cases-table tbody");
  tbody.innerHTML = cases.map(function(c, i) {
    var type = c.type || c.case_type || "functional";
    var status = c.status || "pending";
    return '<tr class="clickable-row" data-detail-index="' + i + '">' +
      '<td><input type="checkbox" class="case-checkbox" data-case-id="' + esc(c.id) + '" onclick="event.stopPropagation(); updateBulkActions();"></td>' +
      "<td>" + esc(c.id) + "</td>" +
      "<td>" + esc(c.title || c.name || "") + "</td>" +
      "<td><span class='badge badge-dim'>" + esc(type) + "</span></td>" +
      "<td>" + tagBadge(c.tags) + "</td>" +
      "<td>" + priorityBadge(c.priority) + "</td>" +
      "<td>" + esc(c.feature_id || "") + "</td>" +
      "<td>" + statusBadge(status) + "</td>" +
      '<td class="row-actions">' +
        '<button class="btn-icon" data-action="edit-case" data-detail-index="' + i + '" title="' + esc(t("crud.edit")) + '" aria-label="Edit">&#9998;</button>' +
        '<button class="btn-icon btn-icon-danger" data-action="delete-case" data-case-id="' + esc(c.id) + '" title="' + esc(t("crud.delete")) + '" aria-label="Delete">&#128465;</button>' +
      '</td>' +
      "</tr>";
  }).join("");

  if (!tbody._clickBound) {
    tbody._clickBound = true;
    tbody.addEventListener("click", function(e) {
      var editBtn = e.target.closest("[data-action='edit-case']");
      if (editBtn) {
        var idx = parseInt(editBtn.dataset.detailIndex, 10);
        var item = _renderedCases[idx];
        if (item) showCrudModal("case", item);
        return;
      }
      var delBtn = e.target.closest("[data-action='delete-case']");
      if (delBtn) {
        deleteCase(delBtn.dataset.caseId);
        return;
      }
      var row = e.target.closest("tr.clickable-row");
      if (row && !e.target.closest("input")) {
        var idx2 = parseInt(row.dataset.detailIndex, 10);
        var item2 = _renderedCases[idx2];
        if (item2) showCaseDetail(item2);
      }
    });
  }

  // Reset bulk actions
  var selectAll = document.getElementById("case-select-all");
  if (selectAll) selectAll.checked = false;
  var bulkBar = document.getElementById("cases-bulk-actions");
  if (bulkBar) bulkBar.style.display = "none";

  // Bottom CTA
  showTabBottomCta("cases", t("cta.done_cases"), t("cta.next_scripts"), "scripts");
  renderCasesPager();
}

async function filterCases() {
  if (!currentProject) return;
  if (!isCasesFilterActive()) {
    casesPage = 1;
    await loadCases();
    return;
  }
  try {
    if (casesTotal > 0 && allCases.length < casesTotal) {
      var data = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/cases");
      allCases = data.cases || [];
      casesTotal = data.count != null ? data.count : allCases.length;
    }
    var filtered = applyCasesFiltersToList(allCases);
    renderCases(filtered);
  } catch (e) {
    toast(e.message, "error");
  }
}

async function generateCases() {
  if (!currentProject) { toast(t("toast.select_project"), "error"); return; }
  var caseType = document.getElementById("case-type-select").value;
  var mode = document.getElementById("case-gen-mode") ? document.getElementById("case-gen-mode").value : "generate";
  if (mode === "regenerate") {
    var confirmed = await new Promise(function(resolve) {
      showConfirmDialog(
        t("crud.confirm_regenerate") || "Regenerate will replace existing cases. Continue?",
        function() { resolve(true); },
        function() { resolve(false); },
        t("gen.regenerate") || "Regenerate"
      );
    });
    if (!confirmed) return;
  }
  return withLoading("btn-generate", async function() {
    try {
      var data = await api("POST", "/api/projects/" + encodePath(currentProject.path) + "/cases", { case_type: caseType, mode: mode });
      casesPage = 1;
      await loadCases();
      toast(t("toast.generated_cases", {n: data.count || 0}), "success");
      try {
        var info = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/info");
        Object.assign(currentProject, info.project);
      } catch (e) { /* ignore */ }
      updateContextBar();
    } catch (e) {
      toast(t("toast.generation_error", {msg: e.message}), "error");
    }
  });
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
      var mappedCases = s.mapped_cases || [];
      var caseDisplay = mappedCases.length > 0 ?
        mappedCases.map(function(m) {
          var srcClass = m.source === "authoritative" || m.source === "generated" ? "authoritative" : (m.source === "manual" ? "manual" : "heuristic");
          return '<span class="mapping-badge ' + srcClass + '">' + esc(m.case_id) + '</span>';
        }).join(" ") :
        '<span class="badge badge-dim">' + esc(s.case_id || "-") + '</span>';
      return '<tr class="clickable-row" data-detail-index="' + i + '">' +
        '<td>' + esc(s.name || "") + '</td>' +
        '<td>' + (s.lines || "-") + '</td>' +
        '<td>' + caseDisplay + '</td>' +
        '<td>' + (s.size !== undefined ? formatBytes(s.size) : "-") + '</td>' +
        '<td class="row-actions">' +
          '<button class="btn-icon" data-action="edit-script" data-detail-index="' + i + '" title="' + esc(t("crud.edit")) + '" aria-label="Edit">&#9998;</button>' +
          '<button class="btn-icon btn-icon-danger" data-action="delete-script" data-script-name="' + esc(s.name) + '" title="' + esc(t("crud.delete")) + '" aria-label="Delete">&#128465;</button>' +
        '</td>' +
        '</tr>';
    }).join("");

    if (!tbody._clickBound) {
      tbody._clickBound = true;
      tbody.addEventListener("click", function(e) {
        var editBtn = e.target.closest("[data-action='edit-script']");
        if (editBtn) {
          var idx = parseInt(editBtn.dataset.detailIndex, 10);
          var item = _renderedScripts[idx];
          if (item) editScript(item);
          return;
        }
        var delBtn = e.target.closest("[data-action='delete-script']");
        if (delBtn) {
          deleteScript(delBtn.dataset.scriptName);
          return;
        }
        var row = e.target.closest("tr.clickable-row");
        if (row) {
          var idx2 = parseInt(row.dataset.detailIndex, 10);
          var item2 = _renderedScripts[idx2];
          if (item2) showScriptDetail(item2);
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
  var mode = document.getElementById("script-gen-mode") ? document.getElementById("script-gen-mode").value : "generate";
  if (mode === "regenerate") {
    var confirmed = await new Promise(function(resolve) {
      showConfirmDialog(
        t("crud.confirm_regenerate") || "Regenerate will replace existing scripts. Continue?",
        function() { resolve(true); },
        function() { resolve(false); },
        t("gen.regenerate") || "Regenerate"
      );
    });
    if (!confirmed) return;
  }
  return withLoading("btn-gen-scripts", async function() {
    try {
      var data = await api("POST", "/api/projects/" + encodePath(currentProject.path) + "/scripts", { force: false, mode: mode });
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
    }
  });
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
    loadRunHistory();
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

  // Load run history
  loadRunHistory();
}

async function runExecution() {
  if (!currentProject) { toast(t("toast.select_project"), "error"); return; }
  return withLoading("btn-run", async function() {
    try {
      var data = await api("POST", "/api/projects/" + encodePath(currentProject.path) + "/run", { tags: [], parallel: 1 });
      renderExecution(data);
      toast(t("toast.tests_complete"), "success");
    } catch (e) {
      toast(t("toast.execution_error", {msg: e.message}), "error");
    }
  });
}

var _renderedExecResults = [];

function renderExecution(data) {
  var run = data.run || data;
  var summary = run.summary || {};
  if (!summary.total && run.total != null) {
    summary = { total: run.total, passed: run.passed || 0, failed: run.failed || 0 };
  }
  var results = run.results || [];
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

  loadRunHistory();
}

// ---------------------------------------------------------------------------
// MANUAL QA TAB
// ---------------------------------------------------------------------------
async function loadManualSessions() {
  if (!currentProject) return;
  try {
    var data = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/manual/sessions");
    var sessions = data.sessions || [];
    var container = document.getElementById("manual-sessions");
    if (!container) return;
    if (sessions.length === 0) {
      container.style.display = "none";
      return;
    }
    container.style.display = "";
    container.innerHTML = "<h4>" + esc(t("manual.history")) + "</h4>" +
      '<table class="data-table"><thead><tr>' +
      "<th>" + esc(t("th.date")) + "</th>" +
      "<th>" + esc(t("th.total")) + "</th>" +
      "<th>" + esc(t("th.passed")) + "</th>" +
      "<th>" + esc(t("th.failed")) + "</th>" +
      "</tr></thead><tbody>" +
      sessions.map(function(s) {
        return "<tr><td>" + (s.started_at ? new Date(s.started_at).toLocaleDateString() : "-") + "</td>" +
          "<td>" + esc(String(s.total)) + "</td>" +
          '<td class="text-success">' + esc(String(s.passed)) + "</td>" +
          '<td class="text-danger">' + esc(String(s.failed)) + "</td></tr>";
      }).join("") +
      "</tbody></table>";
  } catch (e) {
    // ignore
  }
}

async function loadManual() {
  if (!currentProject) return;

  await loadManualSessions();

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
    var data = await api("POST", "/api/projects/" + encodePath(currentProject.path) + "/report?fmt=" + fmt);
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
  // Load report history
  loadReportHistory();
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
  var overlay = document.getElementById("create-modal");
  overlay.style.display = "flex";
  document.getElementById("new-project-name").value = "";
  document.getElementById("create-model").value = "";
  _trapFocus(overlay);
  document.getElementById("new-project-name").focus();
}

function hideCreateModal() {
  var overlay = document.getElementById("create-modal");
  if (overlay._trapHandler) overlay.removeEventListener("keydown", overlay._trapHandler);
  overlay.style.display = "none";
}

async function createProject() {
  var name = document.getElementById("new-project-name").value.trim();
  if (!name) { toast(t("toast.name_required"), "error"); return; }
  var dir = document.getElementById("new-project-dir").value || ".";
  var provider = document.getElementById("create-provider").value;
  var model = document.getElementById("create-model").value.trim();

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

  // Drill-down: goto script
  var gotoScript = e.target.closest("[data-action='goto-script']");
  if (gotoScript && gotoScript.dataset.scriptName) {
    closeDetailPanel();
    navigateToScript(gotoScript.dataset.scriptName);
    return;
  }

  var gotoScriptLink = e.target.closest("a.goto-script");
  if (gotoScriptLink && gotoScriptLink.dataset.script) {
    e.preventDefault();
    closeDetailPanel();
    navigateToScript(gotoScriptLink.dataset.script);
    return;
  }

  // Drill-down: goto case
  var gotoCase = e.target.closest("[data-action='goto-case']");
  if (gotoCase && gotoCase.dataset.caseId) {
    closeDetailPanel();
    navigateToCase(gotoCase.dataset.caseId);
    return;
  }

  // Edit script from detail panel
  var editScriptBtn = e.target.closest("[data-action='edit-current-script']");
  if (editScriptBtn) {
    var panel = document.getElementById("detail-panel");
    var titleEl = document.getElementById("detail-title");
    if (titleEl && panel.classList.contains("open")) {
      var scriptName = titleEl.textContent;
      for (var si = 0; si < _renderedScripts.length; si++) {
        if (_renderedScripts[si].name === scriptName) {
          editScript(_renderedScripts[si]);
          return;
        }
      }
    }
    return;
  }
});

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
(function init() {
  document.documentElement.lang = getLang();
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
  document.getElementById("btn-export-cases")?.addEventListener("click", async function() {
    if (!currentProject) return;
    var toExport = allCases;
    try {
      if (casesTotal > 0 && (!allCases || allCases.length < casesTotal)) {
        var full = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/cases");
        toExport = full.cases || [];
      }
    } catch (e) {
      toast(e.message, "error");
      return;
    }
    if (!toExport || toExport.length === 0) return;
    var projectName = currentProject && currentProject.path ? currentProject.path.split("/").pop() : "testforge";
    var date = new Date().toISOString().slice(0, 10).replace(/-/g, "");
    var filename = projectName + "_cases_" + date + ".json";
    var blob = new Blob([JSON.stringify(toExport, null, 2)], { type: "application/json" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast(t("cases.export") + ": " + filename, "success");
  });
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

  document.getElementById("btn-add-url").addEventListener("click", addUrlInput);
  document.getElementById("btn-add-repo").addEventListener("click", addRepoInput);

  document.getElementById("url-input").addEventListener("keydown", function(e) {
    if (e.key === "Enter") addUrlInput();
  });
  document.getElementById("repo-input").addEventListener("keydown", function(e) {
    if (e.key === "Enter") addRepoInput();
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

  // LLM config
  var saveLlmBtn = document.getElementById("btn-save-llm-config");
  if (saveLlmBtn) saveLlmBtn.addEventListener("click", saveLlmConfig);
  var testLlmBtn = document.getElementById("btn-test-llm");
  if (testLlmBtn) testLlmBtn.addEventListener("click", testLlmConnection);

  var llmTestBanner = document.getElementById("llm-test-btn");
  if (llmTestBanner) {
    llmTestBanner.addEventListener("click", async function() {
      if (!currentProject) return;
      var statusEl = document.getElementById("llm-status");
      if (!statusEl) return;
      statusEl.textContent = t("llm.testing") || "Testing...";
      statusEl.className = "llm-status";
      try {
        var testData = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/config/test");
        statusEl.textContent = testData.status + ": " + testData.message;
        statusEl.className = "llm-status llm-" + testData.status;
      } catch (err) {
        statusEl.textContent = "Error: " + err.message;
        statusEl.className = "llm-status llm-error";
      }
    });
  }
  var llmSaveBanner = document.getElementById("llm-save-btn");
  if (llmSaveBanner) {
    llmSaveBanner.addEventListener("click", async function() {
      if (!currentProject) return;
      var provider = document.getElementById("llm-provider").value;
      var model = document.getElementById("llm-model").value;
      try {
        await api("PUT", "/api/projects/" + encodePath(currentProject.path) + "/config", {
          llm_provider: provider,
          llm_model: model,
        });
        var sel = document.getElementById("llm-provider-select");
        var inp = document.getElementById("llm-model-input");
        if (sel) sel.value = provider;
        if (inp) inp.value = model;
        toast(t("llm.saved") || "LLM configuration saved", "success");
      } catch (err) {
        toast(err.message, "error");
      }
    });
  }

  // Tab switching
  document.querySelectorAll(".tab-btn").forEach(function(btn) {
    btn.addEventListener("click", function() {
      switchTab(btn.dataset.tab);
    });
  });

  // Detail panel close button
  document.getElementById("detail-close").addEventListener("click", closeDetailPanel);

  // ESC: topmost overlay first (confirm > CRUD > detail + create project modal)
  document.addEventListener("keydown", function(e) {
    if (e.key !== "Escape") return;
    var confirmDlg = document.getElementById("confirm-dialog");
    var crudDlg = document.getElementById("crud-modal");
    if (confirmDlg && confirmDlg.style.display === "flex") {
      hideConfirmDialog();
    } else if (crudDlg && crudDlg.style.display === "flex") {
      hideCrudModal();
    } else {
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

  // CRUD buttons
  var addFeatureBtn = document.getElementById("btn-add-feature");
  if (addFeatureBtn) addFeatureBtn.addEventListener("click", function() { showCrudModal("feature"); });
  var addPersonaBtn = document.getElementById("btn-add-persona");
  if (addPersonaBtn) addPersonaBtn.addEventListener("click", function() { showCrudModal("persona"); });
  var addRuleBtn = document.getElementById("btn-add-rule");
  if (addRuleBtn) addRuleBtn.addEventListener("click", function() { showCrudModal("rule"); });
  var addCaseBtn = document.getElementById("btn-add-case");
  if (addCaseBtn) addCaseBtn.addEventListener("click", function() { showCrudModal("case"); });

  // CRUD modal
  var crudClose = document.getElementById("crud-modal-close");
  if (crudClose) crudClose.addEventListener("click", hideCrudModal);
  var crudCancel = document.getElementById("crud-modal-cancel");
  if (crudCancel) crudCancel.addEventListener("click", hideCrudModal);
  var crudSave = document.getElementById("crud-modal-save");
  if (crudSave) crudSave.addEventListener("click", saveCrudModal);
  var crudOverlay = document.getElementById("crud-modal");
  if (crudOverlay) crudOverlay.addEventListener("click", function(e) { if (e.target === this) hideCrudModal(); });

  // Confirm dialog
  var confirmCancel = document.getElementById("confirm-cancel");
  if (confirmCancel) confirmCancel.addEventListener("click", hideConfirmDialog);
  var confirmOverlay = document.getElementById("confirm-dialog");
  if (confirmOverlay) confirmOverlay.addEventListener("click", function(e) { if (e.target === this) hideConfirmDialog(); });

  // Bulk delete
  var bulkDeleteBtn = document.getElementById("btn-bulk-delete-cases");
  if (bulkDeleteBtn) bulkDeleteBtn.addEventListener("click", bulkDeleteCases);

  // Select all checkbox
  var selectAllCb = document.getElementById("case-select-all");
  if (selectAllCb) selectAllCb.addEventListener("change", function() {
    var cbs = document.querySelectorAll(".case-checkbox");
    for (var i = 0; i < cbs.length; i++) cbs[i].checked = this.checked;
    updateBulkActions();
  });

  // Load projects on init
  loadProjects();
})();

// ---------------------------------------------------------------------------
// Script Edit Helper
// ---------------------------------------------------------------------------
async function editScript(script) {
  if (!currentProject) return;
  try {
    var data = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/scripts/" + encodeURIComponent(script.name));
    showCrudModal("script", { name: script.name, content: data.content });
  } catch (e) {
    showCrudModal("script", { name: script.name, content: script.preview || "" });
  }
}

// ---------------------------------------------------------------------------
// CRUD Modal System
// ---------------------------------------------------------------------------
var _crudContext = null;

function _trapFocus(modal) {
  if (modal._trapHandler) {
    modal.removeEventListener("keydown", modal._trapHandler);
  }
  var focusable = modal.querySelectorAll('input, textarea, select, button:not([disabled]), [tabindex]:not([tabindex="-1"])');
  if (focusable.length === 0) return;
  var first = focusable[0];
  var last = focusable[focusable.length - 1];
  first.focus();
  modal._trapHandler = function(e) {
    if (e.key === "Tab") {
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  };
  modal.addEventListener("keydown", modal._trapHandler);
}

function showCrudModal(entityType, existingData) {
  _crudContext = { type: entityType, data: existingData || null };
  var modal = document.getElementById("crud-modal");
  var title = document.getElementById("crud-modal-title");
  var body = document.getElementById("crud-modal-body");

  var isEdit = !!existingData;
  var titleMap = { feature: t("analysis.features"), persona: t("analysis.personas"), rule: t("analysis.rules"), case: t("cases.title"), script: t("scripts.title") };
  title.textContent = (isEdit ? t("crud.edit") : t("crud.add")) + " " + (titleMap[entityType] || entityType);

  body.innerHTML = buildCrudForm(entityType, existingData);
  modal.style.display = "flex";
  _trapFocus(modal);
}

function hideCrudModal() {
  var modal = document.getElementById("crud-modal");
  if (modal._trapHandler) modal.removeEventListener("keydown", modal._trapHandler);
  modal.style.display = "none";
  _crudContext = null;
}

function buildCrudForm(type, data) {
  data = data || {};
  if (type === "feature") {
    return '<div class="form-group"><label>' + esc(t("form.name")) + '</label><input id="crud-name" value="' + esc(data.name || "") + '"></div>' +
      '<div class="form-group"><label>' + esc(t("form.description")) + '</label><textarea id="crud-description">' + esc(data.description || "") + '</textarea></div>' +
      '<div class="form-row"><div class="form-group"><label>' + esc(t("form.category")) + '</label><input id="crud-category" value="' + esc(data.category || "") + '"></div>' +
      '<div class="form-group"><label>' + esc(t("form.priority")) + '</label><select id="crud-priority"><option value="high"' + (data.priority === "high" ? " selected" : "") + '>' + esc(t("analysis.summary.high", {n:""})) + '</option><option value="medium"' + (data.priority === "medium" || !data.priority ? " selected" : "") + '>' + esc(t("analysis.summary.medium", {n:""})) + '</option><option value="low"' + (data.priority === "low" ? " selected" : "") + '>' + esc(t("analysis.summary.low", {n:""})) + '</option></select></div></div>' +
      '<div class="form-group"><label>' + esc(t("form.source")) + '</label><input id="crud-source" value="' + esc(data.source || "") + '"></div>' +
      '<div class="form-group"><label>' + esc(t("form.tags")) + '</label><input id="crud-tags" value="' + esc((data.tags || []).join(", ")) + '"></div>';
  }
  if (type === "persona") {
    return '<div class="form-group"><label>' + esc(t("form.name")) + '</label><input id="crud-name" value="' + esc(data.name || "") + '"></div>' +
      '<div class="form-group"><label>' + esc(t("form.description")) + '</label><textarea id="crud-description">' + esc(data.description || "") + '</textarea></div>' +
      '<div class="form-group"><label>' + esc(t("form.tech_level")) + '</label><select id="crud-tech-level"><option value="beginner"' + (data.tech_level === "beginner" ? " selected" : "") + '>Beginner</option><option value="intermediate"' + (data.tech_level === "intermediate" || !data.tech_level ? " selected" : "") + '>Intermediate</option><option value="advanced"' + (data.tech_level === "advanced" ? " selected" : "") + '>Advanced</option></select></div>' +
      '<div class="form-group"><label>' + esc(t("form.goals")) + '</label><textarea id="crud-goals">' + esc((data.goals || []).join("\n")) + '</textarea></div>' +
      '<div class="form-group"><label>' + esc(t("form.pain_points")) + '</label><textarea id="crud-pain-points">' + esc((data.pain_points || []).join("\n")) + '</textarea></div>';
  }
  if (type === "rule") {
    return '<div class="form-group"><label>' + esc(t("form.name")) + '</label><input id="crud-name" value="' + esc(data.name || "") + '"></div>' +
      '<div class="form-group"><label>' + esc(t("form.description")) + '</label><textarea id="crud-description">' + esc(data.description || "") + '</textarea></div>' +
      '<div class="form-group"><label>' + esc(t("form.condition")) + '</label><input id="crud-condition" value="' + esc(data.condition || "") + '"></div>' +
      '<div class="form-group"><label>' + esc(t("form.expected_behavior")) + '</label><input id="crud-expected-behavior" value="' + esc(data.expected_behavior || "") + '"></div>' +
      '<div class="form-group"><label>' + esc(t("form.source")) + '</label><input id="crud-source" value="' + esc(data.source || "") + '"></div>';
  }
  if (type === "case") {
    return '<div class="form-group"><label>' + esc(t("form.title")) + '</label><input id="crud-title" value="' + esc(data.title || "") + '"></div>' +
      '<div class="form-group"><label>' + esc(t("form.description")) + '</label><textarea id="crud-description">' + esc(data.description || "") + '</textarea></div>' +
      '<div class="form-row"><div class="form-group"><label>' + esc(t("form.type")) + '</label><select id="crud-type"><option value="functional"' + (data.type === "functional" || !data.type ? " selected" : "") + '>' + esc(t("cases.functional")) + '</option><option value="usecase"' + (data.type === "usecase" ? " selected" : "") + '>' + esc(t("cases.usecase")) + '</option><option value="checklist"' + (data.type === "checklist" ? " selected" : "") + '>' + esc(t("cases.checklist")) + '</option></select></div>' +
      '<div class="form-group"><label>' + esc(t("form.priority")) + '</label><select id="crud-priority"><option value="high"' + (data.priority === "high" ? " selected" : "") + '>High</option><option value="medium"' + (data.priority === "medium" || !data.priority ? " selected" : "") + '>Medium</option><option value="low"' + (data.priority === "low" ? " selected" : "") + '>Low</option></select></div></div>' +
      '<div class="form-group"><label>' + esc(t("form.feature_id")) + '</label><input id="crud-feature-id" value="' + esc(data.feature_id || "") + '"></div>' +
      '<div class="form-group"><label>' + esc(t("form.tags")) + '</label><input id="crud-tags" value="' + esc((data.tags || []).join(", ")) + '"></div>' +
      '<div class="form-group"><label>' + esc(t("form.preconditions")) + '</label><textarea id="crud-preconditions">' + esc((data.preconditions || []).join("\n")) + '</textarea></div>' +
      '<div class="form-group"><label>' + esc(t("form.steps")) + ' <small style="color:var(--text-muted)">(' + esc(t("form.steps_hint")) + ')</small></label><textarea id="crud-steps" rows="5">' + esc((data.steps || []).map(function(s) { return typeof s === "string" ? s : (s.action || "") + (s.expected_result ? " | " + s.expected_result : ""); }).join("\n")) + '</textarea></div>' +
      '<div class="form-group"><label>' + esc(t("form.expected_result")) + '</label><textarea id="crud-expected-result">' + esc(data.expected_result || "") + '</textarea></div>';
  }
  if (type === "script") {
    return '<div class="form-group"><label>' + esc(t("detail.code")) + '</label><textarea id="crud-code" class="code-editor">' + esc(data.content || data.preview || "") + '</textarea></div>';
  }
  return "";
}

async function saveCrudModal() {
  if (!_crudContext || !currentProject) return;
  var type = _crudContext.type;
  var isEdit = !!_crudContext.data;
  var basePath = "/api/projects/" + encodePath(currentProject.path);

  // Client-side validation
  var errors = [];
  if (type === "feature" || type === "persona" || type === "rule") {
    var nameEl = document.getElementById("crud-name");
    if (nameEl && !nameEl.value.trim()) errors.push(t("validation.name_required"));
  }
  if (type === "case") {
    var titleEl = document.getElementById("crud-title");
    if (titleEl && !titleEl.value.trim()) errors.push(t("validation.title_required"));
  }
  if (errors.length > 0) {
    toast(errors.join(", "), "error");
    return;
  }

  try {
    if (type === "feature") {
      var payload = {
        name: document.getElementById("crud-name").value,
        description: document.getElementById("crud-description").value,
        category: document.getElementById("crud-category").value,
        priority: document.getElementById("crud-priority").value,
        source: document.getElementById("crud-source").value,
        tags: document.getElementById("crud-tags").value.split(",").map(function(s) { return s.trim(); }).filter(Boolean)
      };
      if (isEdit) {
        await api("PUT", basePath + "/analysis/features/" + encodeURIComponent(_crudContext.data.id), payload);
      } else {
        await api("POST", basePath + "/analysis/features", payload);
      }
      toast(t("common.success"), "success");
      hideCrudModal();
      loadAnalysis();
    } else if (type === "persona") {
      var payload = {
        name: document.getElementById("crud-name").value,
        description: document.getElementById("crud-description").value,
        tech_level: document.getElementById("crud-tech-level").value,
        goals: document.getElementById("crud-goals").value.split("\n").filter(Boolean),
        pain_points: document.getElementById("crud-pain-points").value.split("\n").filter(Boolean)
      };
      if (isEdit) {
        await api("PUT", basePath + "/analysis/personas/" + encodeURIComponent(_crudContext.data.id), payload);
      } else {
        await api("POST", basePath + "/analysis/personas", payload);
      }
      toast(t("common.success"), "success");
      hideCrudModal();
      loadAnalysis();
    } else if (type === "rule") {
      var payload = {
        name: document.getElementById("crud-name").value,
        description: document.getElementById("crud-description").value,
        condition: document.getElementById("crud-condition").value,
        expected_behavior: document.getElementById("crud-expected-behavior").value,
        source: document.getElementById("crud-source").value
      };
      if (isEdit) {
        await api("PUT", basePath + "/analysis/rules/" + encodeURIComponent(_crudContext.data.id), payload);
      } else {
        await api("POST", basePath + "/analysis/rules", payload);
      }
      toast(t("common.success"), "success");
      hideCrudModal();
      loadAnalysis();
    } else if (type === "case") {
      var payload = {
        title: document.getElementById("crud-title").value,
        description: document.getElementById("crud-description").value,
        type: document.getElementById("crud-type").value,
        priority: document.getElementById("crud-priority").value,
        feature_id: document.getElementById("crud-feature-id").value,
        tags: document.getElementById("crud-tags").value.split(",").map(function(s) { return s.trim(); }).filter(Boolean),
        preconditions: document.getElementById("crud-preconditions").value.split("\n").filter(Boolean),
        steps: document.getElementById("crud-steps").value.split("\n").filter(Boolean).map(function(line, idx) {
          var parts = line.split("|");
          return { order: idx + 1, action: parts[0].trim(), expected_result: (parts[1] || "").trim() };
        }),
        expected_result: document.getElementById("crud-expected-result").value
      };
      if (isEdit) {
        await api("PUT", basePath + "/cases/item/" + encodeURIComponent(_crudContext.data.id), payload);
      } else {
        await api("POST", basePath + "/cases/item", payload);
      }
      toast(t("common.success"), "success");
      hideCrudModal();
      loadCases();
      updateContextBar();
    } else if (type === "script") {
      var content = document.getElementById("crud-code").value;
      await api("PUT", basePath + "/scripts/" + encodeURIComponent(_crudContext.data.name), { content: content });
      toast(t("common.success"), "success");
      hideCrudModal();
      loadScripts();
    }
  } catch (e) {
    toast(e.message, "error");
  }
}

// ---------------------------------------------------------------------------
// Confirm Dialog
// ---------------------------------------------------------------------------
var _confirmCallback = null;
var _confirmCancelCallback = null;

function showConfirmDialog(message, onOk, onCancel, okLabel) {
  var dlg = document.getElementById("confirm-dialog");
  document.getElementById("confirm-message").textContent = message;
  dlg.style.display = "flex";
  _confirmCallback = onOk;
  _confirmCancelCallback = onCancel || null;
  var okBtn = document.getElementById("confirm-ok");
  okBtn.textContent = okLabel || t("crud.confirm_delete") || "Delete";
  okBtn.onclick = function() {
    dlg.style.display = "none";
    var cb = _confirmCallback;
    _confirmCallback = null;
    _confirmCancelCallback = null;
    if (cb) cb();
  };
  _trapFocus(dlg);
}

function hideConfirmDialog() {
  var dlg = document.getElementById("confirm-dialog");
  if (dlg._trapHandler) dlg.removeEventListener("keydown", dlg._trapHandler);
  if (dlg.style.display !== "flex") return;
  dlg.style.display = "none";
  var cancelCb = _confirmCancelCallback;
  _confirmCallback = null;
  _confirmCancelCallback = null;
  if (cancelCb) cancelCb();
}

// ---------------------------------------------------------------------------
// Entity Delete Helpers
// ---------------------------------------------------------------------------
async function deleteAnalysisEntity(type, id) {
  if (!currentProject) return;
  showConfirmDialog(t("crud.confirm_delete_msg", { name: id }), async function() {
    try {
      await api("DELETE", "/api/projects/" + encodePath(currentProject.path) + "/analysis/" + type + "/" + encodeURIComponent(id));
      toast(t("toast.deleted", { name: id }), "success");
      loadAnalysis();
      updateContextBar();
    } catch (e) {
      toast(e.message, "error");
    }
  });
}

async function deleteCase(caseId) {
  if (!currentProject) return;
  showConfirmDialog(t("crud.confirm_delete_msg", { name: caseId }), async function() {
    try {
      await api("DELETE", "/api/projects/" + encodePath(currentProject.path) + "/cases/item/" + encodeURIComponent(caseId));
      toast(t("toast.deleted", { name: caseId }), "success");
      loadCases();
      updateContextBar();
    } catch (e) {
      toast(e.message, "error");
    }
  });
}

async function deleteScript(scriptName) {
  if (!currentProject) return;
  showConfirmDialog(t("crud.confirm_delete_msg", { name: scriptName }), async function() {
    try {
      await api("DELETE", "/api/projects/" + encodePath(currentProject.path) + "/scripts/" + encodeURIComponent(scriptName));
      toast(t("toast.deleted", { name: scriptName }), "success");
      loadScripts();
    } catch (e) {
      toast(e.message, "error");
    }
  });
}

// ---------------------------------------------------------------------------
// Bulk Actions
// ---------------------------------------------------------------------------
function updateBulkActions() {
  var cbs = document.querySelectorAll(".case-checkbox:checked");
  var bar = document.getElementById("cases-bulk-actions");
  var countEl = document.getElementById("cases-selected-count");
  if (bar) {
    bar.style.display = cbs.length > 0 ? "" : "none";
    if (countEl) countEl.textContent = cbs.length;
  }
}

async function bulkDeleteCases() {
  var cbs = document.querySelectorAll(".case-checkbox:checked");
  if (!cbs.length) { toast(t("crud.no_selection"), "error"); return; }
  var ids = [];
  for (var i = 0; i < cbs.length; i++) ids.push(cbs[i].dataset.caseId);

  showConfirmDialog(t("crud.confirm_delete_msg", { name: ids.length + " items" }), async function() {
    try {
      await api("POST", "/api/projects/" + encodePath(currentProject.path) + "/cases/bulk-delete", { case_ids: ids });
      toast(t("toast.deleted", { name: ids.length + " cases" }), "success");
      loadCases();
      updateContextBar();
    } catch (e) {
      toast(e.message, "error");
    }
  });
}

// ---------------------------------------------------------------------------
// Enhanced Drill-Down Navigation
// ---------------------------------------------------------------------------
function navigateToScript(scriptName) {
  switchTab("scripts");
  setTimeout(function() {
    for (var i = 0; i < _renderedScripts.length; i++) {
      if (_renderedScripts[i].name === scriptName) {
        showScriptDetail(_renderedScripts[i]);
        return;
      }
    }
  }, 300);
}

function navigateToCase(caseId) {
  switchTab("cases");
  setTimeout(function() {
    for (var i = 0; i < _renderedCases.length; i++) {
      if (_renderedCases[i].id === caseId) {
        showCaseDetail(_renderedCases[i]);
        return;
      }
    }
  }, 300);
}

// ---------------------------------------------------------------------------
// Run History
// ---------------------------------------------------------------------------
async function loadRunHistory() {
  if (!currentProject) return;
  var historyEl = document.getElementById("run-history");
  if (!historyEl) return;
  try {
    var data = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/runs");
    var runs = data.runs || [];
    if (runs.length === 0) {
      historyEl.style.display = "none";
      return;
    }
    historyEl.style.display = "";
    var tbody = document.querySelector("#runs-table tbody");
    tbody.innerHTML = runs.map(function(r) {
      var s = r.summary || {};
      var date = r.started_at ? new Date(r.started_at).toLocaleString() : "-";
      return '<tr class="clickable-row" data-run-id="' + esc(r.run_id || "") + '">' +
        '<td><code>' + esc((r.run_id || "").substring(0, 20)) + '</code></td>' +
        '<td>' + esc(date) + '</td>' +
        '<td>' + (s.total || 0) + '</td>' +
        '<td>' + statusBadge("passed") + ' ' + (s.passed || 0) + '</td>' +
        '<td>' + statusBadge("failed") + ' ' + (s.failed || 0) + '</td>' +
        '</tr>';
    }).join("");

    if (!tbody._histClickBound) {
      tbody._histClickBound = true;
      tbody.addEventListener("click", function(e) {
        var row = e.target.closest("tr.clickable-row");
        if (row && row.dataset.runId) {
          loadRunDetail(row.dataset.runId);
        }
      });
    }
  } catch (e) {
    historyEl.style.display = "none";
  }
}

async function loadRunDetail(runId) {
  if (!currentProject) return;
  try {
    var data = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/runs/" + encodeURIComponent(runId));
    var run = data.run || {};
    var results = run.results || [];
    _renderedExecResults = results;

    document.getElementById("execution-empty").style.display = "none";
    document.getElementById("execution-summary").style.display = "";

    var s = run.summary || {};
    document.getElementById("exec-total").textContent = s.total || results.length;
    document.getElementById("exec-passed").textContent = s.passed || 0;
    document.getElementById("exec-failed").textContent = s.failed || 0;

    var total = s.total || results.length || 1;
    var pct = Math.round(((s.passed || 0) / total) * 100);
    document.getElementById("exec-progress").style.width = pct + "%";

    var tbody = document.querySelector("#execution-table tbody");
    tbody.innerHTML = results.map(function(r, i) {
      return '<tr class="clickable-row" data-detail-index="' + i + '">' +
        '<td>' + esc(r.case_id || "") + '</td>' +
        '<td>' + statusBadge(r.status || "unknown") + '</td>' +
        '<td>' + (r.duration_ms ? r.duration_ms + "ms" : "-") + '</td>' +
        '<td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + esc((r.output || r.error_message || "").substring(0, 200)) + '</td>' +
        '</tr>';
    }).join("");
  } catch (e) {
    toast(e.message, "error");
  }
}

// ---------------------------------------------------------------------------
// Report History
// ---------------------------------------------------------------------------
async function loadReportHistory() {
  if (!currentProject) return;
  var historyEl = document.getElementById("report-history");
  if (!historyEl) return;
  try {
    var data = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/reports");
    var reports = data.reports || [];
    if (reports.length === 0) {
      historyEl.style.display = "none";
      return;
    }
    historyEl.style.display = "";
    var tbody = document.querySelector("#reports-history-table tbody");
    tbody.innerHTML = reports.map(function(r) {
      var date = r.created_at ? new Date(r.created_at).toLocaleString() : "-";
      return '<tr>' +
        '<td><code>' + esc((r.report_id || "").substring(0, 20)) + '</code></td>' +
        '<td>' + esc(date) + '</td>' +
        '<td><span class="badge badge-dim">' + esc(r.format || "-") + '</span></td>' +
        '<td><button class="btn btn-secondary btn-sm" data-action="view-report" data-report-id="' + esc(r.report_id || "") + '">' + esc(t("exec.view_run")) + '</button></td>' +
        '</tr>';
    }).join("");

    if (!tbody._reportClickBound) {
      tbody._reportClickBound = true;
      tbody.addEventListener("click", function(e) {
        var btn = e.target.closest("[data-action='view-report']");
        if (btn && btn.dataset.reportId) {
          loadReportById(btn.dataset.reportId);
        }
      });
    }
  } catch (e) {
    historyEl.style.display = "none";
  }
}

async function loadReportById(reportId) {
  if (!currentProject) return;
  try {
    var data = await api("GET", "/api/projects/" + encodePath(currentProject.path) + "/reports/" + encodeURIComponent(reportId));
    var content = data.report || "";
    var meta = data.meta || {};

    document.getElementById("report-empty").style.display = "none";
    document.getElementById("report-guard").style.display = "none";
    document.getElementById("report-content").style.display = "";

    var viewer = document.getElementById("report-viewer");
    if (meta.format === "html") {
      viewer.textContent = content;
    } else {
      viewer.innerHTML = simpleMarkdown(content);
    }
    toast(t("toast.report_loaded") + " (" + reportId.substring(0, 15) + ")", "success");
  } catch (e) {
    toast(e.message, "error");
  }
}
