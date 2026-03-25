# TestForge v0.3 Final — Cursor Batch Prompt

> **지시**: 서브에이전트를 병렬로 호출해서 작업하라. 각 Phase 안에서 독립적인 작업은 반드시 병렬 실행할 것.
> **Runtime**: Cursor (1 request = 1 consume, 토큰 무관)
> **목표**: PM 70+/100, UX 80+/100 달성. 비개발자 QA 담당자가 GUI만으로 전체 파이프라인을 독립 수행 가능하게.

---

## 이미 완료된 작업 — 절대 건드리지 말 것

다음 파일/기능은 이미 구현되어 47개 테스트가 통과하는 상태임. 기존 동작을 깨뜨리면 안 됨.

### 백엔드 (절대 삭제/재구현 금지)
- `src/testforge/web/routers/cases.py` — 단건 CRUD (POST/PUT/DELETE /cases/item), 벌크삭제, 매핑 기반 스크립트 조회
- `src/testforge/web/routers/analysis.py` — Feature/Persona/Rule 개별 CRUD (POST/PUT/DELETE)
- `src/testforge/web/routers/scripts.py` — 전체 코드 GET, PUT 수정, DELETE, 매핑 관리 (GET/POST/DELETE /mappings)
- `src/testforge/web/routers/execution.py` — 이뮤터블 run_id, GET /runs, GET /runs/{run_id}
- `src/testforge/web/routers/reports.py` — 이뮤터블 report_id, GET /reports, GET /reports/{report_id}
- `src/testforge/web/routers/translate.py` — 다국어 정책 stub (501), GET /translate/status
- `src/testforge/web/routers/projects.py` — GET/PUT /config, GET /config/test (LLM 연결 확인)
- `src/testforge/web/deps.py` — load_mappings/save_mappings
- `src/testforge/execution/runner.py` — pytest 통합, script_name/runner 필드
- `src/testforge/llm/agent.py` — detect_agent_runtime()
- `src/testforge/input/code.py` — AST 기반 코드 파서

### 프론트엔드 (기존 동작 유지 필수)
- `app.js` CRUD 모달 시스템 (showCrudModal/saveCrudModal/hideCrudModal) — 전 엔티티 CRUD 작동 중
- `app.js` 드릴다운 네비게이션 (goto-script, goto-case)
- `app.js` 실행 이력 (loadRunHistory), 보고서 이력 (loadReportHistory)
- `app.js` 재생성 확인 대화상자 (mode=regenerate)
- `app.js` LLM 설정 패널 (loadLlmConfig, saveLlmConfig, testLlmConnection)
- `app.js` LLM 설정 배너 (llm-setup-banner 시스템)
- `index.html` CRUD 모달, 확인 다이얼로그, LLM 설정 카드, LLM 설정 배너 구조

### 테스트 (47개 전부 통과 상태 유지 필수)
- `tests/test_web.py` — 47개 테스트. `.venv/bin/python -m pytest tests/test_web.py`로 확인.

---

## Phase 1: 테스트 보강 + i18n 완성 (병렬)

### Task A: 신규 엔드포인트 테스트 추가 (tests/test_web.py)
**파일**: `tests/test_web.py`

현재 47개 테스트가 존재하나 다음 엔드포인트에 대한 테스트가 없음. 추가할 것:

```
1. GET  /api/projects/{p}/config               — LLM 설정 읽기
2. PUT  /api/projects/{p}/config               — LLM 설정 저장
3. PUT  /api/projects/{p}/config (잘못된 provider) — 400 에러 검증
4. GET  /api/projects/{p}/config/test          — LLM 연결 테스트 (anthropic, key 없을 때 warning)
5. POST /api/projects/{p}/translate            — 501 반환 확인
6. GET  /api/projects/{p}/translate/status     — 상태 반환 확인
7. POST /api/projects/{p}/mappings             — 매핑 추가
8. POST /api/projects/{p}/mappings (중복)       — 409 에러 검증
9. DELETE /api/projects/{p}/mappings?...       — 매핑 삭제
10. GET /api/projects/{p}/reports/{bad_id}     — 404 반환 확인
11. PUT /api/projects/{p}/cases/item/{bad_id}  — 404 반환 확인
12. GET /api/projects/{p}/scripts/bad_name     — 404 반환 확인
13. PUT /api/projects/{p}/scripts/{name}       — 코드 수정 후 내용 확인
14. DELETE /api/projects/{p}/scripts/{name}    — 삭제 후 목록 확인
15. POST /api/projects/{p}/analysis/features   — 새 feature 추가 후 조회
16. DELETE /api/projects/{p}/analysis/features/{id} — 삭제 후 조회
17. POST /api/projects/{p}/analysis/personas   — 새 persona 추가 후 조회
18. POST /api/projects/{p}/analysis/rules      — 새 rule 추가 후 조회
```

기존 `web_client`와 `sample_project` fixture를 재사용할 것.
테스트 함수 명명: `test_<router>_<action>` 패턴 (예: `test_config_get`, `test_translate_stub_501`).
**검증**: `.venv/bin/python -m pytest tests/test_web.py -v` → 전체 통과.

### Task B: Vietnamese i18n 완성 (src/testforge/web/static/i18n.js)
**파일**: `src/testforge/web/static/i18n.js`

Vietnamese (vi) 섹션에 다음 키들이 누락됨. 영어 키를 기준으로 모두 추가:

```
누락 키 카테고리 (영어 키 기준으로 대응되는 vi 번역 추가):
- exec.history, exec.run_again, exec.failed_only
- th.run_id, th.date, th.started, th.environment
- report.history, report.download, report.view
- crud.add_case, crud.confirm_regenerate, crud.selected, crud.bulk_delete
- crud.save, crud.add, crud.edit, crud.delete, crud.confirm, crud.confirm_delete
- nav.goto_case, nav.goto_script
- form.steps, form.steps_hint (이번 세션에서 추가했으나 확인 필요)
- llm.config_title, llm.provider, llm.model, llm.save, llm.saved, llm.test, llm.testing
- llm.setup_title, llm.setup_desc
- detail.mapped_scripts, detail.mapped_case
- mapping.authoritative, mapping.heuristic, mapping.manual
- gen.regenerate, gen.overwrite_warning
```

**검증 방법**:
1. 영어(en) 섹션의 모든 키를 추출
2. 한국어(ko) 섹션의 모든 키를 추출
3. Vietnamese(vi) 섹션의 모든 키를 추출
4. `en ∪ ko` 에서 `vi`에 없는 키 = 누락 → 모두 베트남어로 번역하여 추가
5. 최종 상태: 3개 언어 키 수 동일 (±5 이내)

### Task C: 한국어 i18n 키 감사 및 중복 제거 (src/testforge/web/static/i18n.js)
**파일**: `src/testforge/web/static/i18n.js`

한국어(ko) 섹션이 영어보다 키가 ~2.7배 많다는 감사 결과가 있음.
- 영어에 없는 ko 전용 키 → 영어/베트남어에도 추가 (진짜 유용한 키인 경우)
- 중복 키 → 나중 것만 유지 (JavaScript 객체 특성상 나중 키가 덮어씀)
- 오타/잘못된 키 → 삭제

---

## Phase 2: UX 폴리시 + 사용자 여정 완성 (병렬)

### Task D: Overview 탭 대시보드 강화 (app.js + index.html)
**파일**: `src/testforge/web/static/app.js`, `src/testforge/web/static/index.html`

현재 Overview 탭에 파이프라인 스테퍼와 Quick Stats만 있음. QA 매니저 관점에서 부족.

추가할 것:
1. **최근 실행 요약 카드** — 마지막 실행의 pass/fail/total, 날짜, run_id 요약 (GET /runs에서 첫 번째 항목)
2. **커버리지 게이지** — GET /coverage에서 feature_coverage_pct, rule_coverage_pct를 간단한 프로그레스 바로 표시
3. **다음 행동 안내** — "문서가 없습니다 → Inputs 탭으로 이동" 같은 맥락적 안내 (이미 overview-next-cta가 있으나 내용 보강)

파이프라인 스테퍼 기존 동작은 절대 건드리지 말 것. 새 카드를 `overview-stats-card` 아래에 추가.

### Task E: Execution 탭 실패 상세 개선 (app.js)
**파일**: `src/testforge/web/static/app.js`

현재 상태:
- 테이블에서 output 200자 잘림 (line ~1797) — 이건 그대로 둘 것 (의도된 UX)
- 상세 패널에 full output/stderr 표시됨 — 좋음

추가할 것:
1. 상세 패널에서 `stderr`가 비어있지 않으면 **빨간색 배경 박스**로 강조 (`.stderr-box { background: var(--danger-bg); border-left: 3px solid var(--danger); padding: 12px; }`)
2. `returncode`가 0이 아닌 경우 `return_code` 배지 (빨간)
3. `script_name` 필드가 있으면 표시 + 클릭 시 Scripts 탭 드릴다운
4. `duration` 필드를 사람이 읽기 쉽게 포맷 (1234ms → "1.2s", 65432ms → "1m 5s")

CSS 추가 위치: `src/testforge/web/static/style.css` 끝

### Task F: Manual QA 탭 세션 이력 (app.js + manual.py)
**파일**: `src/testforge/web/static/app.js`, `src/testforge/web/routers/manual.py`

현재 Manual QA는 단일 세션만 지원 (이전 세션 이력 없음).

추가할 것:
1. **백엔드**: GET /api/projects/{p}/manual/sessions — 저장된 세션 목록 반환
   - 세션 파일 위치: `{project}/output/manual_session_*.json`
   - 각 세션: `{ session_id, started_at, finished_at, total, passed, failed, items }`
2. **백엔드**: POST /api/projects/{p}/manual/finish에서 세션 저장 시 고유 session_id 부여
3. **프론트엔드**: Manual QA 탭 상단에 "이전 세션" 드롭다운/목록
4. **프론트엔드**: 세션 선택 시 해당 세션 결과 읽기 전용 표시

### Task G: 케이스 내보내기 (app.js + cases.py 또는 프론트엔드 전용)
**파일**: `src/testforge/web/static/app.js`

현재 케이스 내보내기 기능 없음. 프론트엔드 전용으로 구현 (새 API 불필요):

1. "Export" 버튼을 Cases 탭 헤더에 추가 (`btn-export-cases`)
2. 클릭 시: 현재 `allCases` 데이터를 JSON Blob으로 변환 → 브라우저 다운로드 트리거
3. 파일명: `{project_name}_cases_{YYYYMMDD}.json`

i18n 키: `cases.export` (en: "Export JSON", ko: "JSON 내보내기", vi: "Xuất JSON")

---

## Phase 3: 문서화 + Hive 동기화 (순차)

### Task H: v0.3 구현 요약 문서 업데이트
**파일**: `docs/plans/2026-03-24-v03-implementation-summary.md` (이미 존재, 업데이트)

내용:
1. 구현 완료 항목 전체 목록 (TASK-001~021)
2. 아키텍처 변경 사항 (매핑 저장소, 이뮤터블 이력, 번역 정책)
3. API 엔드포인트 목록 (40개) — 메서드/경로/설명
4. 잔여 작업 (v0.4 예정): 실제 LLM 번역, 리포트 PDF 내보내기, 커버리지 시각화

### Task I: AgentHive 태스크 상태 동기화
**파일**: `~/.agenthive/projects/Users--user--_--workspace--nts-ai/testforge/tasks/*/task.yaml`

모든 TASK-001~021의 task.yaml에서 `status: backlog` → `status: done`으로 변경.
BACKLOG.md도 실제 상태 반영하여 정리.

### Task J: 전체 테스트 실행 및 검증
**명령**: `.venv/bin/python -m pytest tests/ -v --tb=short`

모든 테스트 통과 확인. 실패 시 수정.

---

## 최종 산출물 체크리스트

작업 완료 후 반드시 하나씩 확인:

- [ ] `.venv/bin/python -m pytest tests/test_web.py -v` → 기존 47 + 신규 18 = 65+ 테스트 전체 통과
- [ ] i18n: `en`, `ko`, `vi` 3개 언어 키 수 차이 ±5 이내
- [ ] Overview 탭: 최근 실행 요약 + 커버리지 게이지 표시
- [ ] Execution 탭 상세: stderr 빨간 박스, returncode 배지, script_name 드릴다운, duration 포맷
- [ ] Manual QA: 세션 이력 목록 + 이전 세션 조회 가능
- [ ] Cases 탭: Export JSON 버튼 동작
- [ ] docs/plans/ 업데이트됨
- [ ] AgentHive TASK-001~021 모두 status: done
- [ ] git commit 완료 (메시지: `feat: v0.3 final — tests, i18n, UX polish, session history`)

---

## 참조 파일 경로

| 파일 | 역할 | 줄 수 |
|------|------|-------|
| `src/testforge/web/static/app.js` | 프론트엔드 SPA | ~2,904 |
| `src/testforge/web/static/index.html` | HTML 구조 | ~462 |
| `src/testforge/web/static/i18n.js` | 번역 | ~1,164 |
| `src/testforge/web/static/style.css` | 스타일 | ~1,596 |
| `src/testforge/web/routers/*.py` | API 라우터 (8개) | ~1,500 합계 |
| `src/testforge/web/deps.py` | 공유 유틸 | 36 |
| `src/testforge/execution/runner.py` | 테스트 러너 | ~320 |
| `tests/test_web.py` | API 테스트 | ~613 |

## Khala 공지

작업 완료 후 다음 명령으로 플라자에 공지:
```bash
~/.aria/bin/aria khala publish "plaza/announcements" \
  "[TestForge v0.3 Final] cursor-agent 배치 완료. 65+개 테스트, i18n 3언어 완성, UX 폴리시, 세션 이력. 커밋: {hash}"
```
