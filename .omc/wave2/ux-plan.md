# TestForge v0.6 — UX / Performance / A11y / i18n fix plan

Source diagnostics: `.omc/wave1/performance.json`, `.omc/wave1/accessibility.json`, `.omc/wave1/i18n-completeness.json`.

---

## Priority overview

| Priority | Theme | Items |
|----------|--------|--------|
| **P0** | Accessibility (Level A blockers) | Pipeline stepper keyboard; project dropdown keyboard |
| **P1** | Performance + A11y (major) | Cases API pagination + UI; label associations; CRUD `for`/`id`; create-modal focus trap; toast errors |
| **P2** | A11y polish + live regions | `aria-live` regions; select-all / logo; toast contrast (AA) |
| **P3** | i18n hygiene | `stepper.scripts` duplicate key; dead-key cleanup |

---

## P0 — Critical accessibility

### 1. Pipeline stepper: keyboard + semantics

**Files:** `src/testforge/web/static/app.js` (`renderPipelineStepper`), `src/testforge/web/static/style.css` (`.pipeline-step`)

**Problem:** Steps are `<div class="pipeline-step">` with click-only delegation (`document` click → `.pipeline-step`). No focus, no Enter/Space.

**Exact change (recommended: `<button type="button">` per step):**

HTML is built in `renderPipelineStepper` (~lines 1076–1083). Replace the outer wrapper:

```javascript
// Before (conceptually):
'<div class="pipeline-step ' + stateClass + '" data-tab="' + tab + '">' + ... + '</div>'

// After:
'<button type="button" class="pipeline-step ' + stateClass + '" data-tab="' + tab + '" aria-current="' + (isActive ? 'step' : 'false') + '">' +
  '<span class="pipeline-step-connector" aria-hidden="true"></span>' +
  '<span class="pipeline-step-icon" aria-hidden="true">' + icon + '</span>' +
  '<span class="pipeline-step-label">' + esc(stageLabels[stage.stage] || stage.stage) + '</span>' +
  '<span class="pipeline-step-count">' + esc(countText) + '</span>' +
  '<span class="pipeline-step-status">' + esc(statusText) + '</span>' +
'</button>'
```

**CSS** (`style.css`): reset native button chrome so layout matches current design:

```css
.pipeline-step {
  /* existing flex/visual rules */
  appearance: none;
  border: none;
  background: transparent;
  font: inherit;
  text-align: inherit;
  cursor: pointer;
  width: 100%; /* or keep flex child behavior per layout */
}
.pipeline-step:focus-visible {
  outline: 2px solid var(--accent, #4a90d9);
  outline-offset: 2px;
}
```

**Delegation:** Existing `e.target.closest(".pipeline-step")` continues to work for `<button class="pipeline-step">`.

**Optional:** Set `aria-label` on each button to combine stage name + status, e.g. `Inputs, done` / `Analysis, ready`, using existing `stageLabels` + `statusText`.

---

### 2. Project dropdown list: keyboard activation

**Files:** `src/testforge/web/static/app.js` (`renderProjectDropdown`), `src/testforge/web/static/style.css` (`.dropdown-item`)

**Problem:** Items are `<div class="dropdown-item">` — not in tab order, no keyboard activation.

**Exact change:** In `renderProjectDropdown`, replace `document.createElement("div")` with `document.createElement("button")`:

```javascript
var item = document.createElement("button");
item.type = "button";
item.className = "dropdown-item";
item.dataset.index = i;
item.innerHTML = '...'; // same innerHTML as today
```

Add CSS so buttons match current row layout:

```css
button.dropdown-item {
  display: block;
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  font: inherit;
  cursor: pointer;
  /* padding to match previous .dropdown-item */
}
button.dropdown-item:focus-visible {
  outline: 2px solid var(--accent, #4a90d9);
  outline-offset: -2px;
}
```

Click delegation on `#project-dropdown-list` unchanged. For full combobox pattern (`aria-activedescendant`), defer to v0.7 unless timeboxed.

---

## P1 — Performance + major accessibility

### 3. Cases: backend `?page` / `per_page` + frontend pagination (backward compatible)

**Backend file:** `src/testforge/web/routers/cases.py`

**Exact change:** Extend `get_cases` with optional query params using FastAPI `Query`:

```python
from typing import Optional
from fastapi import Query

@router.get("/{project_path:path}/cases")
async def get_cases(
    project_path: str,
    page: Optional[int] = Query(default=None, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
):
    from testforge.core.project import load_cases

    p = resolve_project(project_path)  # same as existing handlers; import from testforge.web.deps if needed
    cases = load_cases(p)
    if not cases:
        return {"cases": [], "count": 0, "total": 0}

    total = len(cases)
    if page is None:
        return {"cases": cases, "count": total, "total": total}

    start = (page - 1) * per_page
    page_cases = cases[start : start + per_page]
    return {
        "cases": page_cases,
        "count": len(page_cases),
        "total": total,
        "page": page,
        "per_page": per_page,
    }
```

**Contract:**

- **No `page` query** → same as today: full `cases` array, `count == total`.
- **With `page`** → sliced body; always include `total` (and `page`, `per_page`) so the UI can build pager.

**Tests:** `tests/test_web.py` — add cases:

- `GET .../cases` without query → unchanged shape for existing tests.
- `GET .../cases?page=1&per_page=2` → `len(cases) <= 2`, `total` matches full save.

**Frontend files:** `src/testforge/web/static/index.html`, `src/testforge/web/static/app.js`

**HTML:** Inside `#cases-content`, below the cases table container, add a pager bar (ids suggested):

```html
<nav id="cases-pagination" class="cases-pagination" style="display:none;" aria-label="Cases pages">
  <button type="button" id="cases-page-prev" class="btn btn-secondary btn-sm">Previous</button>
  <span id="cases-page-status"></span>
  <button type="button" id="cases-page-next" class="btn btn-secondary btn-sm">Next</button>
</nav>
```

Add i18n keys e.g. `cases.page_status` = `Page {page} of {total_pages} ({total} cases)` in `i18n.js` (en/ko/vi).

**JS state (top of `app.js` near `allCases`):**

```javascript
var casesPage = 1;
var casesPerPage = 50;
var casesTotal = 0;
```

**`loadCases()`:** When opening the Cases tab with no active client filters, request:

```javascript
var url = "/api/projects/" + encodePath(currentProject.path) + "/cases?page=" + casesPage + "&per_page=" + casesPerPage;
var data = await api("GET", url);
allCases = data.cases || [];
casesTotal = data.total != null ? data.total : (data.count || 0);
renderCases(allCases);
updateCasesPaginationUI();
```

**Filter interaction (preserve current filter UX):** If `#case-filter` is non-empty or `#case-type-select` / `#case-tag-select` is not `"all"`, fetch **without** `page` so `allCases` holds the full list and existing `filterCases()` behavior stays correct:

```javascript
function casesFiltersActive() {
  var q = (document.getElementById("case-filter") || {}).value || "";
  var t = document.getElementById("case-type-select").value;
  var g = document.getElementById("case-tag-select").value;
  return q.trim() !== "" || t !== "all" || g !== "all";
}

// In loadCases, branch URL on casesFiltersActive()
```

When user **clears** all filters, reset `casesPage = 1` and switch back to paginated `GET`.

**`generateCases` / export:** After POST generation, response still includes full `cases`; set `casesPage = 1`, then either reload paginated or full list per `casesFiltersActive()`. Export must use full dataset: `GET .../cases` **without** `page` (or use in-memory `allCases` only if known complete).

**`updateCasesPaginationUI()`:** Show/hide `#cases-pagination`, disable prev/next at bounds, set `cases-page-status` from `casesPage`, `casesPerPage`, `casesTotal`.

---

### 4. Label associations (`for` / `id`) — static HTML + LLM card

**File:** `src/testforge/web/static/index.html`

| Control | Change |
|---------|--------|
| `#lang-select` | Wrap header-right in a row or add `<label class="visually-hidden" for="lang-select" data-i18n="settings.language">Language</label>` (add key in `i18n.js`) |
| `#scan-dir` | `<label for="scan-dir" data-i18n="projects.dir_label">Directory</label>` before input |
| `#project-search` | `<label for="project-search" class="visually-hidden" data-i18n="projects.search">Search projects</label>` |
| `#case-type-select` | `<label for="case-type-select" data-i18n="cases.filter_type">Case type</label>` |
| `#case-tag-select` | `<label for="case-tag-select" data-i18n="cases.filter_tag">Tag</label>` |
| `#case-filter` | `<label for="case-filter" class="visually-hidden" data-i18n="cases.filter">Filter cases</label>` |
| `#case-gen-mode` | `<label for="case-gen-mode" data-i18n="gen.mode">Mode</label>` |
| `#script-gen-mode` | `<label for="script-gen-mode" data-i18n="gen.mode">Mode</label>` |
| `#report-fmt` | `<label for="report-fmt" data-i18n="report.format">Format</label>` |

**LLM config card** (lines 134–145): replace bare `<label>` with:

```html
<label for="llm-provider-select" data-i18n="llm.provider">Provider</label>
<select id="llm-provider-select">...</select>
<label for="llm-model-input" data-i18n="llm.model">Model</label>
<input type="text" id="llm-model-input" placeholder="(default)">
```

Use `.visually-hidden` in CSS if not present:

```css
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0,0,0,0);
  white-space: nowrap;
  border: 0;
}
```

---

### 5. CRUD modal: `label for` matching field `id`

**File:** `src/testforge/web/static/app.js` — function `buildCrudForm` (~2624+)

**Pattern:** Every `<label>...</label>` must be `<label for="crud-...">`.

**Exact replacements (examples):**

```javascript
// feature / shared fields
'<div class="form-group"><label for="crud-name">' + esc(t("form.name")) + '</label><input id="crud-name" ...></div>'
'<div class="form-group"><label for="crud-description">' + esc(t("form.description")) + '</label><textarea id="crud-description">...'
'<div class="form-group"><label for="crud-category">' + ...
'<label for="crud-priority">' ...
'<label for="crud-source">' ...
'<label for="crud-tags">' ...
// persona
'<label for="crud-tech-level">' ...
'<label for="crud-goals">' ...
'<label for="crud-pain-points">' ...
// rule
'<label for="crud-condition">' ...
'<label for="crud-expected-behavior">' ...
// case
'<label for="crud-title">' ...
'<label for="crud-type">' ...
'<label for="crud-feature-id">' ...
'<label for="crud-preconditions">' ...
'<label for="crud-steps">' ...
'<label for="crud-expected-result">' ...
// script
'<label for="crud-code">' + esc(t("detail.code")) + '</label><textarea id="crud-code" ...>'
```

---

### 6. Create modal: focus trap + restore focus

**Files:** `src/testforge/web/static/app.js`

**Problem:** `#create-modal` does not call `_trapFocus`; tab escapes behind overlay.

**State:**

```javascript
var _createModalPreviousFocus = null;
```

**`showCreateModal`:**

```javascript
function showCreateModal() {
  _createModalPreviousFocus = document.activeElement;
  var overlay = document.getElementById("create-modal");
  overlay.style.display = "flex";
  document.getElementById("new-project-name").value = "";
  document.getElementById("create-model").value = "";
  _trapFocus(overlay);
  document.getElementById("new-project-name").focus();
}
```

**`hideCreateModal`:** Mirror `hideCrudModal`:

```javascript
function hideCreateModal() {
  var overlay = document.getElementById("create-modal");
  if (overlay._trapHandler) overlay.removeEventListener("keydown", overlay._trapHandler);
  overlay.style.display = "none";
  if (_createModalPreviousFocus && typeof _createModalPreviousFocus.focus === "function") {
    _createModalPreviousFocus.focus();
  }
  _createModalPreviousFocus = null;
}
```

Note: `_trapFocus` already focuses `first` focusable; if you want name field first, ensure DOM order puts `#new-project-name` before other focusables or call `focus()` after `_trapFocus` as above.

---

### 7. Toast: `role="alert"` / assertive for errors

**File:** `src/testforge/web/static/app.js` — `toast()` (~64–73)

**Exact change:**

```javascript
function toast(message, type) {
  type = type || "info";
  var container = document.getElementById("toast-container");
  var el = document.createElement("div");
  el.className = "toast toast-" + type;
  el.textContent = message;
  if (type === "error") {
    el.setAttribute("role", "alert");
    el.setAttribute("aria-live", "assertive");
  } else {
    el.setAttribute("role", "status");
    el.setAttribute("aria-live", "polite");
  }
  container.appendChild(el);
  var delay = type === "error" ? 6000 : 4000;
  setTimeout(function() { el.remove(); }, delay);
}
```

**Optional:** Remove duplicate politeness from parent `#toast-container` or set container to `aria-live="off"` and let each toast own live region behavior (avoids double announcements — pick one strategy in implementation).

---

## P2 — `aria-live` + remaining audit items

### 8. `aria-live` for dynamic content areas

**Principle:** Polite regions for non-critical updates; assertive only for urgent (often covered by error toasts).

**Suggested regions (add in `index.html`, update in `app.js` when content changes):**

| Region | Element | `aria-live` | Updated by |
|--------|---------|---------------|------------|
| Pipeline stepper | `#pipeline-stepper` | `aria-live="polite"` | After `renderPipelineStepper` innerHTML |
| Cases table | `#cases-table` or wrap `<tbody>` | `aria-live="polite"` | After `renderCases` sets `tbody.innerHTML` |
| Run history | `#runs-table` parent or `tbody` | `aria-live="polite"` | After run list render |
| Manual checklist | `#manual-items` | `aria-live="polite"` | After manual items built |
| LLM status bar | `#llm-status-bar` | `aria-live="polite"` | Already text-only updates |

**Example:**

```html
<div id="pipeline-stepper" class="pipeline-stepper" aria-live="polite" aria-busy="false"></div>
```

Toggle `aria-busy="true"` during `loadOverview` fetch if desired.

---

### 9. Other items from `accessibility.json` (recommended same release)

- **`#case-select-all`** (`index.html` ~275): add `aria-label` using i18n, e.g. `data-i18n-aria-label="cases.select_all"` or `aria-label` bound via `applyTranslations` pattern used elsewhere.
- **`h1.logo`**: add inner `<button type="button" class="logo-btn">TestForge</button>` or `tabindex="0"` + `role="link"` + keydown to call same handler as click to return to project list — match existing “click logo” behavior in `app.js` if present (search `logo`).
- **Toast contrast (WCAG 1.4.3 AA)** (`style.css` `.toast-success`, `.toast-error`): darken backgrounds or use dark text on light fills until ratio ≥ 4.5:1 for normal text.

---

## P3 — i18n

### 10. `stepper.scripts` duplicate object key (JavaScript)

**File:** `src/testforge/web/static/i18n.js`

**Problem:** In each locale object, `"stepper.scripts"` appears twice; the second wins at runtime. Labels use the count template string.

**Exact fix:** Keep the stage **title** as `stepper.scripts` (`"Scripts"`). Rename the **count** string to `stepper.scripts_count` (mirror `stepper.cases` / `stepper.cases_count`).

**In `app.js` `getStageCount`:**

```javascript
if (stage.stage === "scripts") return t("stepper.scripts_count", {n: stage.count});
```

**In `i18n.js` (en, ko, vi):** Remove duplicate key; ensure:

```text
"stepper.scripts": "Scripts",
"stepper.scripts_count": "{n} scripts",
```

(and Korean / Vietnamese equivalents).

---

### 11. Dead keys (40) — cleanup consideration

These keys are present in locale objects but **not** referenced by `t("...")` in `app.js` or `data-i18n` in `index.html` per the auditor. **Do not delete blindly** — some may be intended for future UI or dynamic composition. Use this list for grep verification before removal.

1. `app.title`
2. `common.analyzing`
3. `common.error`
4. `common.generating`
5. `common.retry`
6. `common.running`
7. `common.selected`
8. `crud.cancel`
9. `detail.close`
10. `detail.content`
11. `detail.step.action`
12. `exec.failed_only`
13. `exec.no_runs`
14. `exec.run_again`
15. `exec.run_id`
16. `gen.mode_desc`
17. `gen.mode_title`
18. `gen.new_version`
19. `gen.overwrite_warning`
20. `inputs.empty`
21. `inputs.empty.desc`
22. `mapping.authoritative`
23. `mapping.heuristic`
24. `mapping.manual`
25. `nav.goto_report`
26. `nav.goto_run`
27. `overview.next`
28. `report.exec_summary`
29. `report.last_run`
30. `report.no_reports`
31. `report.report_id`
32. `report.view`
33. `report.view_report`
34. `scripts.copied`
35. `scripts.copy`
36. `scripts.count`
37. `th.environment`
38. `th.mapping`
39. `th.mapping_source`
40. `th.started`

**Process:** For each key, `rg 'key'` across `src/testforge/web/static/`; if unused, remove from all three locale blocks in `i18n.js` in one commit.

---

## Deferred (from performance diagnostic, not in v0.6 UX scope)

- `execution.list_runs` / large run JSON reads
- `scripts.list_scripts` full-file reads and payload size
- Virtualizing tables, `esc()` hot-path optimization, debounced `filterCases`

Track as v0.7+ backend/FE performance epic.

---

## Verification checklist

- [ ] Keyboard: Tab through pipeline steps; Enter/Space switches tab.
- [ ] Keyboard: Tab through project dropdown items; Enter selects.
- [ ] Cases: `GET /cases` unchanged without `?page=`; with `?page=1&per_page=50` returns slice + `total`.
- [ ] Screen reader: case type / tag / filter / LLM fields announce labels.
- [ ] Create project: Tab cycles within modal only; focus returns to “New Project” on close.
- [ ] Error toast announced assertively.
- [ ] i18n: only one `stepper.scripts` per locale; counts use `stepper.scripts_count`.
