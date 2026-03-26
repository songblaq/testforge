# TestForge v0.6 — Agent Swarm 경화

> **지시**: 이 배치는 5개 Wave로 구성된 에이전트 스웜 패턴이다.
> Wave 내 모든 에이전트는 반드시 서브에이전트로 **병렬 실행**한다.
> Wave 간은 순차 (이전 Wave 완료 후 다음 Wave 시작).
> 각 에이전트의 출력은 지정된 파일에 JSON/Markdown으로 저장한다.
> **Runtime**: Cursor (1 request)

---

## 절대 수정 금지

- 기존 284개 테스트 전부 통과 상태 유지
- 기존 라우터 엔드포인트의 URL/메서드/응답 스키마 변경 금지
- CRUD 모달, 드릴다운, 실행이력, 보고서이력의 기존 동작 유지
- `.venv/bin/python -m pytest tests/ -q` → 284+ passed 상태 유지 필수

---

## Wave 1: 진단 에이전트 8개 (병렬)

각 에이전트는 좁은 범위를 깊게 조사하고 결과를 `.omc/wave1/` 에 저장.

### Agent 1-1: Path Traversal 헌터
**범위**: 전체 `src/testforge/web/routers/*.py` + `deps.py`
**임무**: 모든 엔드포인트에서 사용자 입력이 파일 경로에 들어가는 곳을 전수 조사.
- `resolve_project`를 거치지 않고 직접 Path()를 만드는 곳
- query parameter에서 받은 값으로 파일을 읽거나 쓰는 곳
- session_id, script_name, filename, run_id 등 사용자 입력이 경로 구성에 쓰이는 모든 곳

**출력**: `.omc/wave1/path-traversal.json`
```json
{
  "agent": "path-traversal-hunter",
  "findings": [
    { "file": "...", "line": 0, "param": "...", "risk": "high|medium|low", "detail": "...", "fix": "..." }
  ],
  "safe_count": 0,
  "unsafe_count": 0
}
```

### Agent 1-2: XSS 벡터 헌터
**범위**: `app.js` 전체 (2900+ lines)
**임무**: `innerHTML`을 사용하는 모든 지점에서 `esc()` 누락을 탐지.
- `innerHTML =` 또는 `+= ` 로 HTML을 구성하는 모든 곳
- 각 지점에서 사용자 제어 데이터가 `esc()` 없이 들어가는지
- `simpleMarkdown()` 출력이 어디에 삽입되는지
- `detailField()` 두 번째 인자가 raw HTML인 곳
- `safeHref()` 가 `//evil.com` 같은 protocol-relative URL을 허용하는지

**출력**: `.omc/wave1/xss-vectors.json`

### Agent 1-3: SSRF/LFI 분석기
**범위**: `src/testforge/analysis/analyzer.py`, `src/testforge/input/parser.py`, `src/testforge/input/*.py`
**임무**: analysis 엔드포인트의 `inputs` 파라미터가 임의 파일/URL을 읽을 수 있는지 검증.
- `body.inputs`에 `/etc/passwd`나 `file:///` 를 넣으면?
- URL 입력 시 내부 네트워크(127.0.0.1, 169.254.x.x)에 접근 가능한지?
- `input_dir` 바깥의 파일을 참조할 수 있는지?

**출력**: `.omc/wave1/ssrf-lfi.json`

### Agent 1-4: 인증/접근제어 감사관
**범위**: `src/testforge/web/app.py`, 모든 라우터
**임무**: 인증 없이 접근 가능한 위험 엔드포인트 목록 작성.
- DELETE 엔드포인트 (프로젝트 삭제, 케이스 삭제 등) — 인증 없이 호출 가능?
- PUT /scripts/{name} — 코드 수정 가능 = RCE 경로?
- POST /run — 임의 스크립트 실행 가능?
- localhost binding 여부 확인 (cli.py의 web 명령 기본 host)
- 현실적 위협 평가: "localhost 도구"라는 맥락에서의 실제 리스크 레벨

**출력**: `.omc/wave1/auth-audit.json`

### Agent 1-5: 성능 프로파일러
**범위**: `app.js` 렌더링 함수들, 라우터의 파일 I/O
**임무**: 대량 데이터에서 병목이 되는 지점 식별.
- `renderCases()` — 1000개 케이스를 `.map().join()` 으로 한번에 렌더링. DOM 블로킹?
- `renderScripts()` — 스크립트마다 `read_text()` 호출. 100개면?
- `list_scripts` 라우터 — 모든 스크립트 파일을 순차 읽기. N+1?
- `loadRunHistory()` — 모든 run 파일을 순차 파싱?

**출력**: `.omc/wave1/performance.json` (각 병목에 예상 임팩트와 수정 제안)

### Agent 1-6: 접근성 감사관
**범위**: `index.html`, `app.js`, `style.css`
**임무**: WCAG 2.1 Level A 위반 전수 조사.
- 모든 `<button>` 에 aria-label 또는 visible text 있는지
- 모든 `<input>/<select>/<textarea>` 에 연결된 `<label>` 있는지
- 색상 대비 비율 (CSS 변수에서 계산)
- 키보드 네비게이션: Tab 순서가 논리적인지
- 스크린리더: 동적 콘텐츠 변경 시 `aria-live` 사용하는지
- 파이프라인 스테퍼가 키보드로 조작 가능한지

**출력**: `.omc/wave1/accessibility.json`

### Agent 1-7: README/문서 정합성 검사관
**범위**: `README.md`, `pyproject.toml`, `CHANGELOG.md`, `docs/`
**임무**: 문서가 코드 현실과 일치하는지 검증.
- pyproject.toml version vs README의 버전 언급
- README의 기능 목록 vs 실제 구현 상태 (체크리스트)
- CLI --help 텍스트와 README 일치 여부
- Web GUI가 README에서 제대로 소개되는지
- Getting Started 가이드가 실제 작동하는 명령인지

**출력**: `.omc/wave1/docs-accuracy.json`

### Agent 1-8: i18n 완전성 검사관
**범위**: `i18n.js`, `app.js`, `index.html`
**임무**: 3개 언어 간 키 동기화 + 코드에서 사용되는 키가 i18n에 정의돼 있는지.
- app.js에서 `t("...")` 호출 → 해당 키가 en/ko/vi 모두에 있는지
- index.html의 `data-i18n="..."` → 해당 키가 3언어 모두에 있는지
- 3언어 키 수 정확히 세기
- 번역 품질은 평가하지 않음 (키 존재 여부만)

**출력**: `.omc/wave1/i18n-completeness.json`

---

## Wave 2: 계획 에이전트 3개 (병렬)

Wave 1의 8개 진단 결과를 읽고, 수정 계획을 수립.

### Agent 2-1: 보안 수정 계획자
**입력**: `.omc/wave1/path-traversal.json`, `xss-vectors.json`, `ssrf-lfi.json`, `auth-audit.json`
**임무**: 4개 보안 진단을 종합하여 우선순위 수정 계획 작성.
- 각 finding을 "즉시 수정" / "localhost 맥락에서 수용" / "v0.7 이월"로 분류
- "즉시 수정" 항목에 대해 정확한 파일, 라인, 수정 코드 제시
- 수정 간 의존성 명시 (A를 먼저 고쳐야 B가 가능)

**출력**: `.omc/wave2/security-plan.md`

### Agent 2-2: UX/성능 수정 계획자
**입력**: `.omc/wave1/performance.json`, `accessibility.json`, `i18n-completeness.json`
**임무**: 성능, 접근성, i18n 진단을 종합하여 수정 계획 작성.
- 케이스 pagination 구현 전략 (프론트엔드 only vs 백엔드 API)
- 접근성 수정 우선순위 (Level A 위반 먼저)
- i18n 누락 키 추가 목록

**출력**: `.omc/wave2/ux-plan.md`

### Agent 2-3: 문서/릴리스 계획자
**입력**: `.omc/wave1/docs-accuracy.json`, `pyproject.toml`
**임무**: 문서 정합성 수정 + 버전 정렬 + 릴리스 준비.
- README 수정 사항 목록 (줄 번호 + 수정 내용)
- pyproject.toml version → 0.5.0으로 업데이트
- CHANGELOG.md에 v0.5 섹션 추가 내용

**출력**: `.omc/wave2/docs-plan.md`

---

## Wave 3: 구현 에이전트 6개 (병렬)

Wave 2 계획에 따라 실제 코드를 수정.

### Agent 3-1: 경로 순회 수정자
**입력**: `.omc/wave2/security-plan.md` 중 path traversal 섹션
**수정 대상**: 계획서에 명시된 파일/라인
**필수 패턴**: 모든 사용자 입력 경로에 대해:
```python
# 검증 패턴
if ".." in name or "/" in name:
    raise HTTPException(status_code=400, detail="Invalid name")
resolved = (base_dir / name).resolve()
if not resolved.is_relative_to(base_dir.resolve()):
    raise HTTPException(status_code=403, detail="Access denied")
```
**특히**: manual.py의 session_id, list_projects의 directory parameter

### Agent 3-2: XSS 정밀 수정자
**입력**: `.omc/wave2/security-plan.md` 중 XSS 섹션
**수정 대상**: app.js
- `safeHref()`: protocol-relative URL (`//`) 차단 추가
- `simpleMarkdown()`: img alt 속성 이스케이프
- `detailField()` 사용처 중 raw HTML이 필요없는 곳 → `esc()` 추가

### Agent 3-3: SSRF/LFI 방어자
**입력**: `.omc/wave2/security-plan.md` 중 SSRF 섹션
**수정 대상**: `analysis.py`, `input/parser.py`
- `body.inputs` 경로를 `project_dir / config.input_dir` 아래로 제한
- URL 입력 시 private IP 대역(127.x, 10.x, 172.16-31.x, 192.168.x, 169.254.x) 차단

### Agent 3-4: 케이스 Pagination 구현자
**입력**: `.omc/wave2/ux-plan.md` 중 성능 섹션
**수정 대상**: `app.js`, `src/testforge/web/routers/cases.py`

백엔드:
- GET /cases에 `?page=1&per_page=50` query parameter 추가
- 기존 동작 유지 (page 미지정 시 전체 반환 = 하위 호환)

프론트엔드:
- 50개 초과 시 페이지네이션 UI (이전/다음 버튼)
- 50개 이하면 기존과 동일 (변화 없음)

### Agent 3-5: 접근성 수정자
**입력**: `.omc/wave2/ux-plan.md` 중 접근성 섹션
**수정 대상**: `index.html`, `app.js`, `style.css`
- 파이프라인 스테퍼에 `role="tablist"` + 키보드 화살표 네비게이션
- 동적 콘텐츠 영역에 `aria-live="polite"`
- toast에 `role="alert"`
- 모든 아이콘 버튼의 aria-label 일관성 점검

### Agent 3-6: 문서 + 버전 수정자
**입력**: `.omc/wave2/docs-plan.md`
**수정 대상**: `README.md`, `pyproject.toml`, `CHANGELOG.md`
- pyproject.toml: `version = "0.5.0"`
- README: Web GUI 섹션 추가, 기능 목록 현실 반영
- CHANGELOG: v0.3~v0.5 이력 추가

---

## Wave 4: 검증 에이전트 5개 (병렬)

Wave 3 수정 후 각 영역을 독립 검증.

### Agent 4-1: 보안 재검증자
Wave 1과 동일한 관점으로 수정된 코드를 재검사.
- path traversal: 수정된 모든 엔드포인트에 공격 페이로드 대입 검증
- XSS: `safeHref("//evil.com")`, `simpleMarkdown("<img onerror=alert(1)>")` 시뮬레이션
- SSRF: 수정된 분석 엔드포인트에 `file:///etc/passwd`, `http://127.0.0.1` 시뮬레이션
**출력**: `.omc/wave4/security-recheck.json` (finding 0개 = pass)

### Agent 4-2: 테스트 실행자
```bash
.venv/bin/python -m pytest tests/ -v --tb=short -q
```
모든 기존 테스트 + 신규 테스트 통과 확인.
**실패 시**: 실패 원인을 분석하고 코드 수정 (테스트 삭제 금지).
**출력**: `.omc/wave4/test-results.txt`

### Agent 4-3: 접근성 재검증자
Wave 1과 동일한 WCAG 관점으로 수정된 HTML/JS 재검사.
**출력**: `.omc/wave4/a11y-recheck.json`

### Agent 4-4: i18n 재검증자
수정 후 3언어 키 수 동기화 재확인.
**출력**: `.omc/wave4/i18n-recheck.json` (en=X, ko=X, vi=X, 누락=0)

### Agent 4-5: 회귀 테스트 실행자
도그푸딩 테스트 스위트 별도 실행:
```bash
.venv/bin/python -m pytest tests/selftest/ -v --tb=short -q
```
**출력**: `.omc/wave4/dogfood-results.txt`

---

## Wave 5: 종합 판정 + 커밋 (순차, 에이전트 1개)

### Agent 5-1: 최종 종합 판정관

**입력**: `.omc/wave4/` 전체 + `.omc/wave2/` 계획 대비 실행 결과
**임무**:
1. Wave 4 검증 결과를 종합하여 각 영역 점수 재산정 (x/10)
2. v0.5 Phantom Panel 점수 대비 개선 폭 측정
3. 잔여 리스크 최종 목록 (v0.7 이월 사항)
4. Gate 판정: APPROVED / CONDITIONAL / BLOCKED

**출력**: `.omc/reviews/v06-final-verdict.md`

```markdown
# TestForge v0.6 최종 판정

## 점수 변화
| 영역 | v0.5 | v0.6 | 변화 |
|------|------|------|------|
| 보안 | 4/10 | ?/10 | +? |
| QA/에지케이스 | 6/10 | ?/10 | +? |
| PM/문서 | 6/10 | ?/10 | +? |
| 프론트엔드/접근성 | 6/10 | ?/10 | +? |
| **평균** | **5.5** | **?** | **+?** |

## 테스트 결과
- API: ?/? passed
- CLI dogfood: ?/? passed
- GUI dogfood: ?/? passed
- 총: ?/? passed, ? skipped

## Gate 판정
> v0.6 release: ???
```

**커밋** (APPROVED인 경우만):
```bash
git add -A
git commit -m "feat: v0.6 swarm hardening — security, pagination, a11y, docs

Wave 1: 8-agent diagnostic sweep (path traversal, XSS, SSRF, auth, perf, a11y, docs, i18n)
Wave 2: 3-agent planning synthesis
Wave 3: 6-agent parallel implementation (security fixes, pagination, a11y, docs)
Wave 4: 5-agent independent verification
Wave 5: Final verdict — score improvement from 5.5 to X/10

Co-Authored-By: Cursor Agent <noreply@cursor.com>"

~/.aria/bin/aria khala publish "plaza/announcements" \
  "[TestForge v0.6 Swarm 완료] 8진단→3계획→6구현→5검증→1판정. 보안: 4→?/10. 총 테스트: ?개. commit: $(git rev-parse --short HEAD)"
```

**BLOCKED인 경우**: 커밋하지 않고 `.omc/reviews/v06-final-verdict.md`에 블로커 목록 기록.

---

## 에이전트 수 요약

| Wave | 역할 | 에이전트 수 | 실행 |
|------|------|------------|------|
| **1** | 진단 | **8** | 병렬 |
| **2** | 계획 | **3** | 병렬 |
| **3** | 구현 | **6** | 병렬 |
| **4** | 검증 | **5** | 병렬 |
| **5** | 판정 | **1** | 순차 |
| **합계** | | **23** | |

---

## 최종 체크리스트

- [ ] `.omc/wave1/` 에 8개 진단 JSON 존재
- [ ] `.omc/wave2/` 에 3개 계획 MD 존재
- [ ] `.omc/wave4/` 에 5개 검증 결과 존재
- [ ] `.omc/reviews/v06-final-verdict.md` 존재 + gate 판정
- [ ] 보안 점수 4/10 → 7+/10 개선
- [ ] 전체 평균 5.5/10 → 7+/10 개선
- [ ] `.venv/bin/python -m pytest tests/ -q` → 전체 통과
- [ ] pagination: 50개 초과 케이스 시 페이지네이션 동작
- [ ] pyproject.toml version = "0.5.0"
- [ ] README에 Web GUI 섹션 존재
- [ ] git commit 완료 (APPROVED 시)
- [ ] Khala 공지 완료
