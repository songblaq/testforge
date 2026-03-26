# TestForge v0.5 — 클린업 + 보안/UX 경화 + Phantom Panel 리뷰

> **지시**: 서브에이전트를 병렬로 호출해서 작업하라. Phase 내 독립 작업은 반드시 병렬. Phase 간은 순차.
> **Runtime**: Cursor (1 request = 1 consume)
> **핵심 원칙**: "첫 설치 사용자가 깨끗한 상태에서 시작하고, 보안 허점 없이, 비개발자도 직관적으로 사용 가능해야 한다."

---

## 이미 완료된 작업 — 절대 건드리지 말 것

### 백엔드 (수정 금지)
- `src/testforge/web/routers/*.py` 8개 라우터의 기존 엔드포인트 로직
- `src/testforge/web/deps.py`, `src/testforge/core/project.py`, `src/testforge/core/config.py`
- `src/testforge/llm/agent.py`, `src/testforge/input/code.py`
- `src/testforge/execution/runner.py`의 pytest 통합 및 conftest 자동 생성

### 프론트엔드 (기존 동작 유지 필수)
- CRUD 모달 시스템, 드릴다운 네비게이션, 실행/보고서 이력
- LLM 설정 패널 (배너+카드 이중 시스템)
- 재생성 확인 대화상자

### 테스트 (282 passed, 4 skipped 유지 필수)
```bash
.venv/bin/python -m pytest tests/ -q --tb=line
# 반드시 282+ passed 유지
```

---

## Phase 0: 레포 클린업 — 도그푸딩 데이터 제거 (순차)

### Task 0A: git에서 도그푸딩 프로젝트 제거

이 3개 디렉토리는 실존하지 않는 외부 프로젝트의 도그푸딩 데이터. git에서 제거하고 .gitignore에 추가.

```bash
# 1. git에서 제거 (로컬 파일은 유지)
git rm -r --cached "AgentHive QA/"
git rm -r --cached "Health Device QA/"
git rm -r --cached "TestForge Self-Test/"
git rm --cached testforge.yaml

# 2. .gitignore에 추가 (기존 내용 유지, 아래 섹션 추가)
```

**`.gitignore` 수정** — 파일 끝에 다음 블록 추가:
```gitignore
# Dogfooding project data (user-generated, not part of source)
AgentHive QA/
Health Device QA/
TestForge Self-Test/
testforge.yaml
scripts/
```

기존 `.gitignore`의 `TestForge Self-Test/` 줄이 이미 있으면 중복 제거.

**검증**: `git status`에서 삭제 확인, `git ls-files "AgentHive QA"` → 빈 결과.

### Task 0B: .omc/ 정리

`.omc/` 디렉토리에서 더 이상 필요 없는 파일 제거:
- `progress.txt` — 2026-03-22 Ralph 이터레이션 메모 (구 데이터)
- `project-memory.json` — 구 경로(lucablaq) 참조 (무효)
- `sessions/*.json` — 빈 세션 데이터
- `state/*.jsonl` — 빈 에이전트 리플레이

**유지할 파일**:
- `cursor-batch-v03-final.md` — v0.3 배치 기록
- `cursor-batch-v04-dogfooding.md` — v0.4 배치 기록
- `cursor-batch-v05-hardening.md` — 이 파일 (현재 실행 중)
- `prd.json` — 이력 (해가 없음)

```bash
rm -f .omc/progress.txt .omc/project-memory.json
rm -rf .omc/sessions/ .omc/state/
```

---

## Phase 1: Phantom Panel 사전 리뷰 (병렬 4개)

Cursor 서브에이전트 4개가 각각 다른 Phantom 역할(QA, PM, Security, Frontend)로 현재 코드를 리뷰.
각 리뷰 결과를 `.omc/reviews/` 디렉토리에 JSON으로 저장. 리뷰 결과가 Phase 2의 수정 우선순위를 결정.

### Task 1A: QA 엔지니어 Phantom 리뷰

**역할**: 경력 6년차 QA 엔지니어. 에지 케이스, 실패 시나리오, 테스트 커버리지 관점.

**리뷰 대상**: `src/testforge/web/static/app.js` 전체, `tests/test_web.py`, `tests/selftest/`

**리뷰 포인트**:
1. 사용자가 예상치 못한 입력(빈 문자열, 특수문자, 초장문)을 넣으면?
2. 동시에 두 탭에서 같은 케이스를 편집하면?
3. 실행 중 브라우저를 닫으면?
4. 1000개 케이스를 로드하면 성능은?
5. 각 CRUD 작업의 404/409/500 에러 핸들링이 사용자 친화적인지?

**출력**: `.omc/reviews/phantom-qa.json` (Phantom 출력 형식)
```json
{
  "archetype_id": "qa-engineer",
  "archetype_name": "QA 엔지니어",
  "category": "dev",
  "findings": [ ... ],
  "overall_impression": "...",
  "score": { "value": 0, "scale": 10, "criteria": "에지 케이스 커버리지 + 에러 핸들링" }
}
```

### Task 1B: PM Phantom 리뷰

**역할**: 경력 8년차 PM. 스코프, 리스크, MVP, 점진적 출시 관점.

**리뷰 대상**: `README.md`, `docs/plans/`, `pyproject.toml`, 전체 기능 목록

**리뷰 포인트**:
1. README가 약속하는 것 vs 실제 구현된 것의 괴리
2. v0.5로 릴리스 가능한 MVP 범위는 어디까지?
3. 오버엔지니어링된 부분 (있으면)
4. 문서화와 인수인계 상태
5. 사용자 온보딩 경로가 명확한지 (첫 실행 → 프로젝트 생성 → 분석 → ...)

**출력**: `.omc/reviews/phantom-pm.json`

### Task 1C: 보안 전문가 Phantom 리뷰

**역할**: 경력 10년차 보안 전문가. OWASP Top 10, 입력 검증, XSS.

**리뷰 대상**: 전체 `src/testforge/web/` (routers + static)

**리뷰 포인트**:
1. path traversal — `deps.py` resolve_project 외에 미보호 경로?
2. XSS — `app.js`의 `esc()` 미사용 지점, `innerHTML` 직접 사용
3. 파일 업로드 — 크기 제한, MIME 검증, 악성 파일 차단
4. toast()에 API 에러 메시지 unescaped 전달 (`e.message` 직접 사용)
5. `simpleMarkdown()` 함수의 HTML 인젝션 가능성
6. API 응답의 민감 정보 노출 (전체 파일 경로 등)

**출력**: `.omc/reviews/phantom-security.json`

### Task 1D: 프론트엔드 개발자 Phantom 리뷰

**역할**: 경력 5년차 프론트엔드 개발자. UX, 접근성, 반응형, 성능.

**리뷰 대상**: `index.html`, `app.js`, `style.css`, `i18n.js`

**리뷰 포인트**:
1. 모달 포커스 트랩 구현 여부
2. aria-label 일관성
3. 키보드 네비게이션 (Tab, Escape, Enter)
4. 모바일 반응형 (media query 상태)
5. 로딩 인디케이터 누락 지점
6. 빈 상태(empty state) 메시지의 친절도
7. 대량 데이터 시 성능 (pagination/virtual scroll)

**출력**: `.omc/reviews/phantom-frontend.json`

---

## Phase 2: Critical/High 이슈 수정 (병렬 5개)

Phase 1 리뷰 결과와 사전 감사 결과를 종합하여 Critical/High 이슈를 수정.

### Task 2A: 클라이언트 사이드 폼 검증 추가

**파일**: `src/testforge/web/static/app.js`

`saveCrudModal()` 함수 상단에 검증 로직 추가:

```javascript
// saveCrudModal() 함수 시작부:
async function saveCrudModal() {
  if (!_crudContext || !currentProject) return;
  var type = _crudContext.type;

  // --- Client-side validation ---
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
  // --- End validation ---

  // ... existing saveCrudModal logic continues unchanged
}
```

i18n 키 추가 (3언어):
```
"validation.name_required": "Name is required" / "이름은 필수입니다" / "Tên là bắt buộc"
"validation.title_required": "Title is required" / "제목은 필수입니다" / "Tiêu đề là bắt buộc"
```

### Task 2B: XSS 방어 강화

**파일**: `src/testforge/web/static/app.js`

1. **toast()의 에러 메시지 이스케이프**: toast 함수에서 message를 항상 이스케이프:
```javascript
function toast(message, type) {
  type = type || "info";
  var container = document.getElementById("toast-container");
  var el = document.createElement("div");
  el.className = "toast toast-" + type;
  el.textContent = message;  // textContent는 이미 안전 — 확인만
  container.appendChild(el);
  var delay = type === "error" ? 6000 : 4000;
  setTimeout(function() { el.remove(); }, delay);
}
```
→ `textContent`를 사용하고 있으므로 이미 안전. **확인 후 변경 불필요면 건드리지 말 것.**

2. **simpleMarkdown()의 HTML 인젝션 방지**: markdown 파서에서 `<script>` 태그 제거:
```javascript
// simpleMarkdown 함수 끝에 추가:
html = html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
html = html.replace(/on\w+\s*=\s*["'][^"']*["']/gi, '');
```

3. **API 에러 메시지의 경로 정보 제거**: `src/testforge/web/routers/projects.py`의 에러 응답에서 절대 경로 노출 방지:
```python
# resolve_project의 404 에러에서 full path 대신 project name만:
raise HTTPException(status_code=404, detail=f"Project not found: {Path(project_path).name}")
```
→ 이건 `deps.py`에 있음. **deps.py의 에러 메시지에서 전체 경로를 프로젝트 이름만으로 교체**.

### Task 2C: 파일 업로드 크기 제한

**파일**: `src/testforge/web/routers/inputs.py`

업로드 엔드포인트에 크기 제한 추가:

```python
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("/{project_path:path}/inputs")
async def upload_input(project_path: str, file: UploadFile):
    # ... existing resolve_project ...

    # Size check
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")
    await file.seek(0)  # reset for subsequent reads

    # ... rest of existing logic, but use 'contents' instead of re-reading
```

### Task 2D: 모달 포커스 트랩 + ESC 핸들링

**파일**: `src/testforge/web/static/app.js`

```javascript
// showCrudModal 함수 끝에 추가:
function showCrudModal(entityType, existingData) {
  // ... existing code ...
  modal.style.display = "flex";

  // Focus trap
  _trapFocus(modal);
}

function _trapFocus(modal) {
  var focusable = modal.querySelectorAll('input, textarea, select, button, [tabindex]:not([tabindex="-1"])');
  if (focusable.length === 0) return;
  var first = focusable[0];
  var last = focusable[focusable.length - 1];
  first.focus();
  modal.addEventListener("keydown", function _trap(e) {
    if (e.key === "Tab") {
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  });
  modal._trapHandler = function(e) {
    if (e.key === "Tab") {
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  };
  modal.addEventListener("keydown", modal._trapHandler);
}

// hideCrudModal에서 정리:
function hideCrudModal() {
  var modal = document.getElementById("crud-modal");
  if (modal._trapHandler) modal.removeEventListener("keydown", modal._trapHandler);
  modal.style.display = "none";
  _crudContext = null;
}
```

### Task 2E: 로딩 인디케이터 일관성

**파일**: `src/testforge/web/static/app.js`

현재 일부 버튼만 로딩 중 disabled 처리. 모든 생성/실행 버튼에 일관되게 적용:

```javascript
// 범용 로딩 래퍼 함수 추가:
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
```

그리고 다음 함수들에서 `withLoading` 적용:
- `runAnalysis()` → `withLoading("btn-analyze", async function() { ... })`
- `generateCases()` → `withLoading("btn-gen-cases", ...)`
- `generateScripts()` → `withLoading("btn-gen-scripts", ...)`
- `runTests()` → `withLoading("btn-run-tests", ...)`
- `loadReport()` / report 생성 → 해당 버튼

**CSS** (`style.css`에 추가):
```css
.spinner {
  display: inline-block;
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
button:disabled { opacity: 0.6; cursor: not-allowed; }
```
→ **spinner 클래스가 이미 정의되어 있으면 중복 추가하지 말 것. 먼저 확인.**

---

## Phase 3: Medium 이슈 수정 + 빈 상태 메시지 개선 (병렬 3개)

### Task 3A: 빈 상태 메시지 + 첫 실행 웰컴

**파일**: `src/testforge/web/static/app.js`, `src/testforge/web/static/index.html`

1. **Overview 탭 — 프로젝트 미선택 시 웰컴 메시지**:
Overview 탭의 `loadOverview()` 시작부에서 `currentProject`가 null이면:
```javascript
if (!currentProject) {
  document.getElementById("pipeline-stepper").innerHTML =
    '<div class="welcome-state"><h2>' + esc(t("welcome.title")) + '</h2>' +
    '<p>' + esc(t("welcome.desc")) + '</p>' +
    '<button class="btn btn-primary" onclick="switchTab(\'projects\')">' + esc(t("welcome.create")) + '</button></div>';
  return;
}
```

2. **Scripts 탭 가드 메시지 강화**: 현재 "Generate test cases first"만 표시. 왜 필요한지 설명 추가.

i18n 키 (3언어):
```
"welcome.title": "Welcome to TestForge" / "TestForge에 오신 것을 환영합니다" / "Chào mừng đến TestForge"
"welcome.desc": "Select or create a project to begin your QA workflow." / "프로젝트를 선택하거나 생성하여 QA 워크플로우를 시작하세요." / "Chọn hoặc tạo dự án để bắt đầu."
"welcome.create": "Create Project" / "프로젝트 만들기" / "Tạo dự án"
```

### Task 3B: i18n fallback + 키 누락 방지

**파일**: `src/testforge/web/static/i18n.js`

`t()` 함수에 fallback 추가:
```javascript
function t(key, params) {
  var lang = currentLang || "ko";
  var str = (translations[lang] && translations[lang][key])
    || (translations["en"] && translations["en"][key])  // fallback to English
    || key;  // fallback to key itself (never "undefined")
  if (params) {
    Object.keys(params).forEach(function(k) {
      str = str.replace("{" + k + "}", params[k]);
    });
  }
  return str;
}
```
→ **기존 `t()` 함수를 찾아서 이 로직으로 교체. 기존 동작이 이미 이렇게 되어 있으면 건드리지 말 것.**

### Task 3C: 모바일 반응형 개선

**파일**: `src/testforge/web/static/style.css`

기존 `@media (max-width: 768px)` 블록 외에 태블릿 대응 추가:

```css
/* Tablet */
@media (max-width: 1024px) {
  .form-row { flex-direction: column; }
  .stats-row { flex-wrap: wrap; }
  .stats-row .stat-card { min-width: 140px; }
  .data-table { font-size: 13px; }
  .detail-panel { width: 50vw; min-width: 320px; }
}

/* Table horizontal scroll */
.table-container { overflow-x: auto; -webkit-overflow-scrolling: touch; }
```

`index.html`에서 모든 `<table class="data-table">` 부모 div에 `class="table-container"` 추가.
→ **이미 table-container가 있으면 건드리지 말 것.**

---

## Phase 4: 테스트 보강 + Phantom 리뷰 반영 (병렬 2개)

### Task 4A: Phase 2/3 수정사항 테스트 추가

**파일**: `tests/test_web.py`

```python
def test_upload_size_limit(web_client, sample_project):
    """File upload rejects files over 10MB."""
    huge = b"x" * (11 * 1024 * 1024)
    r = web_client.post(
        f"/api/projects/{sample_project}/inputs",
        files={"file": ("huge.bin", huge, "application/octet-stream")},
    )
    assert r.status_code == 413

def test_error_message_no_full_path(web_client):
    """Error messages should not expose full filesystem paths."""
    r = web_client.get("/api/projects/nonexistent-project/info")
    assert r.status_code in (400, 404)
    detail = r.json().get("detail", "")
    assert "/Users/" not in detail
    assert "/home/" not in detail
```

### Task 4B: Phantom 리뷰 결과 종합 문서

**파일**: `.omc/reviews/synthesis.md` (신규)

Phase 1의 4개 Phantom 리뷰 결과를 종합:
1. 각 리뷰어의 score (x/10)
2. Critical findings 목록 → Phase 2에서 수정된 것 / 안 된 것
3. 잔여 리스크 목록 (v0.6으로 이월)
4. 전체 리뷰 통과 여부 판정

형식:
```markdown
# TestForge v0.5 Phantom Panel 리뷰 종합

## 참여 리뷰어
| 역할 | 점수 | 핵심 의견 |
|------|------|-----------|
| QA 엔지니어 | ?/10 | ... |
| PM | ?/10 | ... |
| 보안 전문가 | ?/10 | ... |
| 프론트엔드 | ?/10 | ... |

## Critical → 수정 완료
- [ ] 폼 검증 (Task 2A)
- [ ] XSS 방어 (Task 2B)
- [ ] 업로드 크기 제한 (Task 2C)
- [ ] 모달 포커스 트랩 (Task 2D)

## 잔여 리스크 (v0.6)
- 대량 케이스 pagination
- CORS 미설정
- IE 11 미지원 (수용)
- 에러 트래킹 미도입

## Gate 판정
> v0.5 release: APPROVED / BLOCKED
```

---

## Phase 5: 최종 검증 + 커밋 (순차)

### Task 5A: 전체 테스트 실행

```bash
.venv/bin/python -m pytest tests/ -v --tb=short -q
```
모든 테스트 통과 확인. 실패 시 수정 (테스트 삭제 금지).

### Task 5B: git 커밋 + Khala 공지

```bash
# 도그푸딩 데이터 제거 커밋 (별도)
git add .gitignore
git commit -m "chore: remove dogfooding project data from git tracking

Remove AgentHive QA/, Health Device QA/, TestForge Self-Test/, testforge.yaml
from git. These are user-generated dogfooding data, not source code.
New users get a clean install with no pre-existing projects."

# v0.5 경화 커밋
git add -A
git commit -m "feat: v0.5 hardening — security, validation, a11y, Phantom Panel review

Phase 0: Repo cleanup — dogfooding data removed from git tracking
Phase 1: 4-persona Phantom Panel review (QA/PM/Security/Frontend)
Phase 2: Critical fixes — form validation, XSS defense, upload limit, focus trap, loading states
Phase 3: Medium fixes — welcome state, i18n fallback, mobile responsive
Phase 4: Tests for new security/validation behaviors + review synthesis

Co-Authored-By: Cursor Agent <noreply@cursor.com>"

# Khala 공지
~/.aria/bin/aria khala publish "plaza/announcements" \
  "[TestForge v0.5 경화 완료] Phantom Panel 4인 리뷰(QA/PM/Security/Frontend) + Critical/High 전수 수정. 도그푸딩 데이터 git 제거. 보안: XSS 방어+업로드 10MB+경로 노출 차단. UX: 폼 검증+포커스 트랩+로딩+웰컴. commit: $(git rev-parse --short HEAD)"
```

---

## 최종 산출물 체크리스트

- [ ] `git ls-files "AgentHive QA"` → 빈 결과 (git에서 제거됨)
- [ ] `git ls-files "Health Device QA"` → 빈 결과
- [ ] `git ls-files "TestForge Self-Test"` → 빈 결과
- [ ] `git ls-files testforge.yaml` → 빈 결과
- [ ] `.omc/reviews/phantom-qa.json` 존재 + score 기록
- [ ] `.omc/reviews/phantom-pm.json` 존재 + score 기록
- [ ] `.omc/reviews/phantom-security.json` 존재 + score 기록
- [ ] `.omc/reviews/phantom-frontend.json` 존재 + score 기록
- [ ] `.omc/reviews/synthesis.md` 존재 + gate 판정 기록
- [ ] CRUD 모달에서 빈 이름/제목 제출 시 에러 토스트 (서버 호출 안 함)
- [ ] `simpleMarkdown()`에서 `<script>` 태그 제거됨
- [ ] 업로드 10MB 초과 시 413 반환
- [ ] 에러 메시지에 `/Users/...` 절대 경로 미노출
- [ ] 모달 열릴 때 첫 input에 포커스 + Tab 순환
- [ ] 생성/실행 버튼 클릭 시 disabled + spinner 표시
- [ ] Overview 탭 프로젝트 미선택 시 웰컴 메시지
- [ ] `t("nonexistent.key")` → "nonexistent.key" 반환 (undefined 아님)
- [ ] `.venv/bin/python -m pytest tests/ -q` → 전체 통과
- [ ] git commit 2개 (클린업 + 경화) 완료
- [ ] Khala 공지 완료

---

## 참조 파일 경로

| 파일 | 작업 |
|------|------|
| `.gitignore` | 도그푸딩 경로 추가 |
| `src/testforge/web/static/app.js` | 폼 검증, 포커스 트랩, 로딩 래퍼, 웰컴 |
| `src/testforge/web/static/i18n.js` | validation/welcome 키 + t() fallback |
| `src/testforge/web/static/index.html` | table-container 래퍼 |
| `src/testforge/web/static/style.css` | 태블릿 반응형, spinner 확인 |
| `src/testforge/web/routers/inputs.py` | 업로드 크기 제한 |
| `src/testforge/web/deps.py` | 에러 메시지 경로 노출 제거 |
| `tests/test_web.py` | 보안 테스트 추가 |
| `.omc/reviews/*.json` | Phantom 리뷰 결과 |
| `.omc/reviews/synthesis.md` | 리뷰 종합 + gate 판정 |
