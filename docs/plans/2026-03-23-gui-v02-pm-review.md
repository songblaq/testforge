# TestForge GUI v0.2 -- PM 리뷰 보고서

**리뷰어**: Alex (Product Manager)
**일자**: 2026-03-23
**대상**: Phase 1+2 구현물 vs 제품 사양서 v0.2.0
**파일**: `index.html`, `app.js`, `style.css`, `i18n.js`

---

## 요약 판정

| 구분 | 점수 |
|------|------|
| v0.1 제품 오너 평가 (원점) | 10/100 |
| Phase 1+2 사양 대비 구현률 | **약 62%** |
| 업데이트된 제품 점수 (PM 추정) | **48/100** |

Phase 1(기반) 항목은 대부분 잘 구현되었다. Phase 2(핵심 뷰어)는 기본 골격은 있으나, 사양서가 요구하는 깊이의 절반 수준에 그친다. "데이터가 보이긴 하는데, 사양서가 요구하는 수준의 조작과 정보 밀도에는 못 미치는 상태"로 요약된다.

---

## Phase 1+2 항목별 상세 평가 (10개)

---

### 항목 1. Overview 탭 + 파이프라인 스테퍼

**사양 요구사항**:
- 7단계 파이프라인 스테퍼 수평 표시 (Inputs -> Analysis -> Cases -> Scripts -> Run -> Manual -> Report)
- 각 단계 상태 아이콘 (완료/활성/비활성)
- 각 단계 아래 요약 숫자
- 다음 단계 강조 CTA 버튼
- 프로젝트 메타 정보 카드 (프로젝트명, 경로, LLM 프로바이더, 생성일, 마지막 활동일)
- 스테퍼 각 단계 클릭 시 해당 탭 이동

**구현 상태**:

| 수락 기준 | 충족 여부 | 근거 |
|-----------|----------|------|
| 파이프라인 스테퍼 수평 표시 | O | `renderPipelineStepper()` 함수, `.pipeline-stepper` flex 레이아웃 |
| 상태 아이콘 구분 (done/active/waiting) | O | `stateClass` 로직 + CSS `.pipeline-step.done`, `.active` |
| 요약 숫자 표시 | O | `getStageCount()` 함수 |
| 다음 단계 CTA 버튼 | O | `overview-next-cta` div + goto-tab 액션 |
| 프로젝트 메타 정보 카드 | **X** | **누락** -- 사양서 요구: 프로젝트명, 경로, LLM 프로바이더, 생성일, 마지막 활동일. Quick Stats 카드만 있고 메타 정보 카드는 없음 |
| 스테퍼 클릭 시 탭 이동 | O | 글로벌 이벤트 위임: `.pipeline-step[data-tab]` 클릭 처리 |
| 6단계 vs 7단계 | **PARTIAL** | 사양서는 7단계(Manual 포함), 구현은 6단계(Manual 없음) -- `stageLabels`에 Manual 없음 |

**판정**: **PARTIAL -- 75%**
핵심 스테퍼 UI와 CTA는 잘 구현됨. 프로젝트 메타 정보 카드 누락과 Manual 단계 미포함이 갭.

---

### 항목 2. 컨텍스트 바 확장

**사양 요구사항**:
- `[my-webapp] 3 docs | 12 features | 24 cases | 75 scripts | Last run: 18/24 passed | 89% coverage`
- 각 항목 클릭 시 해당 탭으로 이동
- 미도달 단계는 회색 표시

**구현 상태**:

| 수락 기준 | 충족 여부 | 근거 |
|-----------|----------|------|
| 프로젝트명 + 파이프라인 단계 수 | O | `ctx-name`, `ctx-pipeline` |
| 문서 수, 피처 수, 케이스 수 | O | `ctx-inputs`, `ctx-features`, `ctx-cases` |
| 스크립트 수 | **X** | **누락** -- 사양서 요구: scripts 수 표시. HTML에 해당 요소 없음 |
| Last run 결과 | **X** | **누락** -- 사양서 요구: "Last run: 18/24 passed" 표시. 미구현 |
| 커버리지 퍼센트 | O | `ctx-coverage` |
| 각 항목 클릭 시 탭 이동 | O | `ctx-clickable` 클래스 + `data-tab` + 글로벌 이벤트 위임 |
| 미도달 단계 회색 표시 | **PARTIAL** | API 호출 실패 시 "0"이나 "-"로 표시되나, 명시적 회색 비활성 스타일은 없음 |

**판정**: **PARTIAL -- 60%**
기본 구조는 있으나 사양서의 모든 정보 항목을 표시하지 않음.

---

### 항목 3. 가드 메시지 + 탭 이동 CTA

**사양 요구사항**:
- 6개 탭 (Analysis, Cases, Scripts, Execution, Manual QA, Report)에 의존성 가드 메시지
- 각 가드 메시지에 이전 탭으로 이동하는 CTA 버튼

**구현 상태**:

| 탭 | 가드 메시지 | 이동 CTA | 충족 |
|----|-----------|---------|------|
| Analysis | O (`analysis-guard` + "Upload documents...") | O (`guard-cta-btn` -> inputs) | O |
| Cases | O (`cases-guard` + "Run analysis first...") | O (`guard-cta-btn` -> analysis) | O |
| Scripts | O (`scripts-guard` + "Generate test cases first...") | O (`guard-cta-btn` -> cases) | O |
| Execution | O (`execution-guard` + "Generate scripts first...") | O (`guard-cta-btn` -> scripts) | O |
| Manual QA | **X** | **X** | **X** -- 사양서 요구: cases 0개일 때 가드. 구현에 가드 없음 |
| Report | O (`report-guard` + "Run tests first...") | O (`guard-cta-btn` -> execution) | O |

**판정**: **PASS -- 83%**
6개 중 5개 탭에 가드 구현 완료. Manual QA만 누락.

---

### 항목 4. 탭 하단 CTA ("-> 다음 단계")

**사양 요구사항**:
- 각 탭 하단에 다음 단계로의 CTA 버튼 (초록색 강조)
- 완료 상태 텍스트 + 다음 단계 버튼

**구현 상태**:

| 탭 | 하단 CTA | 충족 |
|----|---------|------|
| Inputs | O (`inputs-next-cta` -> "Next: Run Analysis") | O |
| Analysis | O (`analysis-next-cta` -> "Next: Generate Cases") | O |
| Cases | O (`cases-next-cta` -> "Next: Generate Scripts") | O |
| Scripts | O (`scripts-next-cta` -> "Next: Run Tests") | O |
| Execution | O (`execution-next-cta` -> "Next: View Report") | O |
| Manual QA | **PARTIAL** -- 세션 완료 후에만 표시 | O (finishManualSession 후 표시) |

`showTabBottomCta()` 헬퍼 함수가 일관된 UI로 처리. `.tab-bottom-cta` CSS 스타일 완비.

**판정**: **PASS -- 95%**
거의 완벽. i18n 키도 모두 준비됨.

---

### 항목 5. URL hash 기반 탭 라우팅

**사양 요구사항**:
- 탭 전환 시 URL hash 업데이트 (`#inputs`, `#analysis` 등)
- 브라우저 뒤로가기/앞으로가기 지원
- 새로고침 시 현재 탭 유지

**구현 상태**:

| 수락 기준 | 충족 여부 | 근거 |
|-----------|----------|------|
| URL hash 업데이트 | O | `switchTab()` 내 `history.replaceState(null, "", "#" + tabName)` |
| hashchange 이벤트 리스닝 | O | `window.addEventListener("hashchange", ...)` |
| 프로젝트 선택 시 hash 복원 | O | `selectProject()` 내 `location.hash.replace("#", "") \|\| "overview"` |

**주의사항**: `history.replaceState`를 사용하므로 뒤로가기 히스토리가 쌓이지 않는다. `history.pushState`가 더 사양 의도에 맞겠으나, 기능 자체는 동작한다.

**판정**: **PASS -- 90%**
replaceState vs pushState 차이만 있을 뿐, 핵심 요구사항 충족.

---

### 항목 6. Inputs 문서 뷰어

**사양 요구사항**:
- 드래그 앤 드롭 + 파일 선택 업로드
- 파일 목록 테이블 (아이콘, 파일명, 크기, 타입, 업로드 시각)
- 파일명 클릭 시 문서 뷰어 (Markdown 렌더링, 텍스트, JSON/YAML, 이미지, 미지원 포맷 안내)
- 각 파일 다운로드 버튼
- 각 파일 삭제 버튼 (확인 다이얼로그)
- 하단 "-> Run Analysis" CTA
- 업로드 프로그레스 표시

**구현 상태**:

| 수락 기준 | 충족 여부 | 근거 |
|-----------|----------|------|
| 드래그 앤 드롭 업로드 | O | `drop-zone` + dragover/dragleave/drop 이벤트 |
| 파일 선택 업로드 | O | `file-upload` input[type=file] |
| 파일 목록 테이블 | **PARTIAL** | Type, Name, Size, Actions 있으나 **업로드 시각 컬럼 누락** |
| 파일명 클릭 시 문서 뷰어 | O | `showInputDetail()` -> `loadInputContent()` |
| Markdown 렌더링 | O | `simpleMarkdown()` 함수로 렌더링 |
| 텍스트 파일 표시 | O | `<pre class="doc-viewer-text">` |
| JSON/YAML 구문 강조 | **PARTIAL** | 고정폭 `<pre>` 표시만 함, **구문 강조(syntax highlight) 미구현** |
| 이미지 인라인 표시 | O | blob URL 생성 + `<img>` |
| 미지원 포맷 안내 | O | `inputs.preview_unavailable` 메시지 |
| 다운로드 버튼 | O | `downloadInputFile()` + 테이블 행 내 버튼 + 상세 패널 내 버튼 |
| 삭제 버튼 | **PARTIAL** | 삭제 기능 있으나 **확인 다이얼로그(confirm) 없이 즉시 삭제** |
| 하단 CTA | O | `btn-run-analysis-from-inputs` |
| 업로드 프로그레스 | **X** | **누락** -- 파일별 프로그레스 표시 없음 |
| 지원 포맷 드롭존 명시 | O | `drop-hint` 텍스트 |

**판정**: **PARTIAL -- 72%**
문서 뷰어의 핵심 기능(Markdown 렌더링, 다운로드, 미리보기)은 구현됨. 삭제 확인 다이얼로그와 업로드 프로그레스가 빠짐.

---

### 항목 7. Analysis 요약 카드

**사양 요구사항**:
- 요약 카드: 총 피처/페르소나/룰/스크린 수
- 카테고리별 피처 분포 (카테고리명 + 개수, 막대 차트 또는 태그 그룹)
- 우선순위별 분포 (High/Medium/Low 비율)
- 카테고리 설명 (카테고리명 옆에 툴팁/배지로 피처 수)
- 피처 테이블 행 클릭 시 상세 패널
- 카테고리별/우선순위별 필터 드롭다운
- 텍스트 검색 필터
- 편집 기능 (Phase 3이므로 이번 평가 제외)

**구현 상태**:

| 수락 기준 | 충족 여부 | 근거 |
|-----------|----------|------|
| 통계 카드 (피처/페르소나/룰) | O | `analysis-summary-cards` + stat-card 3개 |
| 스크린 수 카드 | **X** | **누락** |
| 카테고리별 분포 | **PARTIAL** | `catMap` 계산은 하지만 **UI에 표시하지 않음** -- 카테고리 분포 시각화 누락 |
| 우선순위별 분포 | O | High/Med/Low 카운트가 피처 카드 하단 `stat-sub`에 표시 |
| 카테고리 설명/배지 | **PARTIAL** | 테이블에 카테고리 배지는 있으나 **피처 수 표시 없음** |
| 피처 행 클릭 -> 상세 패널 | O | `showFeatureDetail()` |
| 페르소나 행 클릭 -> 상세 패널 | O | `showPersonaDetail()` |
| 룰 행 클릭 -> 상세 패널 | O | `showRuleDetail()` |
| 카테고리별 필터 | **X** | **누락** -- HTML에 필터 드롭다운 없음 |
| 우선순위별 필터 | **X** | **누락** |
| 텍스트 검색 필터 | **X** | **누락** |

**판정**: **PARTIAL -- 50%**
요약 카드와 행 클릭 상세는 구현됨. 필터링 UI 전면 누락이 가장 큰 갭. 카테고리 분포 시각화도 계산만 하고 렌더링하지 않음.

---

### 항목 8. Cases 분류 컬럼 + 필터 확장

**사양 요구사항**:
- 테이블에 분류(Nature) 컬럼: positive(초록)/negative(빨강)/edge(노랑) 배지
- 타입 필터 (all/functional/usecase/checklist)
- 분류 필터 (all/positive/negative/edge)
- 우선순위 필터
- 피처 필터
- 텍스트 검색
- 컬럼 헤더 클릭 정렬
- 행 클릭 시 상세 패널

**구현 상태**:

| 수락 기준 | 충족 여부 | 근거 |
|-----------|----------|------|
| 분류(Tag) 컬럼 배지 표시 | O | `tagBadge(c.tags)` -- positive=초록, negative=빨강, edge=노랑 |
| 타입 필터 | O | `case-type-select` (all/functional/usecase/checklist/crud) |
| 분류(Tag) 필터 | O | `case-tag-select` (all/positive/negative/edge/smoke/regression) |
| 우선순위 필터 | **X** | **누락** -- HTML에 우선순위 필터 select 없음 |
| 피처 필터 | **X** | **누락** -- 분석 결과의 피처 목록에서 채우는 드롭다운 없음 |
| 텍스트 검색 | O | `case-filter` input + `filterCases()` |
| 컬럼 헤더 클릭 정렬 | **X** | **누락** -- 정렬 로직 없음 |
| 행 클릭 -> 상세 패널 | O | `showCaseDetail()` -- preconditions, steps, expected_result, tags, rule_ids 모두 표시 |
| 요약 카드 영역 | **X** | **누락** -- 사양서 요구: 총 케이스 수, 타입별 수, 긍정/부정 분류 수, 미커버 피처 경고 |

**판정**: **PARTIAL -- 55%**
핵심 분류 컬럼과 기본 필터(타입/태그/텍스트)는 구현됨. 우선순위/피처 필터, 정렬, 요약 카드 누락.

---

### 항목 9. Scripts 코드 뷰어

**사양 요구사항**:
- 요약 카드: 총 스크립트 수, 총 파일 크기, 커버된 케이스 수/전체 케이스 수
- 스크립트 테이블: 파일명, 크기, 연관 케이스 ID, 연관 피처
- 파일명 클릭 시 코드 뷰어 (구문 강조, 줄 번호, 복사 버튼)
- 케이스-스크립트 매핑 뷰 (토글)

**구현 상태**:

| 수락 기준 | 충족 여부 | 근거 |
|-----------|----------|------|
| 요약 카드 (총 수, 줄 수, 크기) | O | `scripts-summary-cards` -- 3개 stat-card |
| 커버된 케이스 수 표시 | **X** | **누락** -- 전체 케이스 대비 커버 비율 미표시 |
| 테이블: 파일명 | O | `s.name` |
| 테이블: 크기 | O | `formatBytes(s.size)` |
| 테이블: 연관 케이스 ID | O | `s.case_id` 컬럼 |
| 테이블: 연관 피처 | **X** | **누락** -- 피처명 조회/표시 없음 |
| 코드 뷰어 (상세 패널) | **PARTIAL** | `showScriptDetail()` -- `script.preview`가 있으면 `<pre>` 표시. 그러나 **preview 데이터가 API에서 오는지 불확실** |
| 구문 강조 | **X** | **누락** -- `<pre>` 일반 텍스트만 |
| 줄 번호 | **PARTIAL** | `.code-line` span은 있으나 실제 줄 번호 렌더링 코드 없음 |
| 복사 버튼 | **X** | **누락** -- i18n에 `scripts.copy`, `scripts.copied` 키는 있으나 UI 미구현 |
| 매핑 뷰 (토글) | **X** | **누락** -- 케이스-스크립트 양방향 매핑 뷰 없음 |

**판정**: **PARTIAL -- 40%**
테이블과 요약 카드 기본 구조는 있으나, 코드 뷰어의 핵심(구문 강조, 줄 번호, 복사)과 매핑 뷰가 모두 누락.

---

### 항목 10. Report 개선

**사양 요구사항**:
- Executive Summary 카드 (전체 테스트 수, Pass/Fail/Skip, 비율, 마지막 실행 시각)
- 커버리지 섹션 (피처/룰 커버리지 + 프로그레스 바 + 미커버 목록)
- 커버리지 매트릭스 (피처 x 케이스)
- 실패 분석 섹션
- 이력 추이 (최근 5회)
- Markdown 렌더링된 뷰
- 보고서 다운로드 (Markdown/HTML)
- 탭 진입 시 자동 생성
- 빈 보고서 절대 미표시

**구현 상태**:

| 수락 기준 | 충족 여부 | 근거 |
|-----------|----------|------|
| Executive Summary 카드 | O | `loadExecutiveSummary()` -- total, passed, failed, pass_rate |
| 마지막 실행 시각 | **X** | **누락** -- i18n에 `report.last_run` 키는 있으나 표시 로직 없음 |
| 커버리지 섹션 | **PARTIAL** | `loadCoverage()` -- 피처/룰 퍼센트 표시. **프로그레스 바 없음, 미커버 목록 없음** |
| 커버리지 매트릭스 | **X** | **누락** |
| 실패 분석 섹션 | **X** | **누락** |
| 이력 추이 | **X** | **누락** |
| Markdown 렌더링된 뷰 | O | `simpleMarkdown()` 사용하여 렌더링 |
| HTML 형식 표시 | **PARTIAL** | HTML은 `textContent`로 표시 (렌더링 아닌 원시 텍스트) |
| 다운로드 | O | `downloadReport()` -- Blob 생성 -> 다운로드 |
| 탭 진입 시 자동 생성 | **X** | **사양 위반** -- 수동 "Load Report" 클릭 필요. `switchTab("report")`에서 auto-load 안 함 |
| 빈 보고서 미표시 | **PARTIAL** | 가드 메시지는 있으나, 부분 데이터 시 빈 보고서 렌더링 가능 |

**판정**: **PARTIAL -- 35%**
Executive Summary와 기본 커버리지 수치, Markdown 렌더링은 있으나, 사양서가 요구하는 보고서의 핵심 가치(실패 분석, 이력 추이, 매트릭스, 자동 생성)가 전부 누락.

---

## Phase 1+2 종합 점수표

| # | 항목 | 판정 | 점수 |
|---|------|------|------|
| 1 | Overview + 파이프라인 스테퍼 | PARTIAL | 75% |
| 2 | 컨텍스트 바 확장 | PARTIAL | 60% |
| 3 | 가드 메시지 + 탭 이동 CTA | PASS | 83% |
| 4 | 탭 하단 CTA | PASS | 95% |
| 5 | URL hash 라우팅 | PASS | 90% |
| 6 | Inputs 문서 뷰어 | PARTIAL | 72% |
| 7 | Analysis 요약 카드 | PARTIAL | 50% |
| 8 | Cases 분류 + 필터 | PARTIAL | 55% |
| 9 | Scripts 코드 뷰어 | PARTIAL | 40% |
| 10 | Report 개선 | PARTIAL | 35% |
| | **평균** | | **65.5%** |

Phase 1 (항목 1-5) 평균: **80.6%** -- 양호
Phase 2 (항목 6-10) 평균: **50.4%** -- 미흡

---

## 7대 결함 재평가

### 결함 1: 입력 문서 뷰어/다운로드 없음

**판정: RESOLVED**

- 파일명 클릭 시 상세 패널에 문서 뷰어 열림
- Markdown 렌더링 (`simpleMarkdown()`)
- 텍스트 파일 고정폭 표시
- 이미지 인라인 표시
- 다운로드 버튼 (테이블 행 + 상세 패널)
- 미지원 포맷 안내 메시지

근거: `showInputDetail()` + `loadInputContent()` + `downloadInputFile()` 모두 구현. 핵심 페인 포인트 해소됨.

---

### 결함 2: 분석 흐름도/요약 없음

**판정: PARTIALLY RESOLVED**

해결된 부분:
- 요약 카드 3개 (피처 수 + 우선순위 분포, 페르소나 수, 룰 수)
- 피처/페르소나/룰 테이블 + 행 클릭 상세 패널
- 카테고리 배지 표시

미해결 부분:
- 카테고리별 피처 분포 시각화 (계산만 하고 렌더링 안 함)
- 카테고리/우선순위/텍스트 필터 전면 누락
- 편집 기능 (Phase 3 범위이므로 감점하지 않음)
- 흐름도는 사양서에서 Phase 2 범위가 아니므로 제외

---

### 결함 3: 케이스 편집/추가 불가, 성공/실패 구분 없음

**판정: PARTIALLY RESOLVED**

해결된 부분:
- 긍정/부정/엣지 분류 배지 (초록/빨강/노랑)
- 타입별 필터 (functional/usecase/checklist/crud)
- 태그별 필터 (positive/negative/edge/smoke/regression)
- 텍스트 검색
- 행 클릭 시 전체 상세 (steps, preconditions, expected_result, tags)

미해결 부분:
- 편집 기능 (Phase 3 범위)
- 추가/삭제 기능 (Phase 3 범위)
- 우선순위/피처 필터, 정렬 누락
- 요약 카드 누락

편집/추가는 Phase 3 범위이므로 현 단계에서는 "분류 구분"이 핵심. 이 부분은 잘 구현됨.

---

### 결함 4: 스크립트 상세/매핑 없음

**판정: PARTIALLY RESOLVED**

해결된 부분:
- 스크립트 테이블 (파일명, 줄 수, 케이스 ID, 크기)
- 요약 카드 (총 수, 줄 수, 크기)
- 행 클릭 시 상세 패널 (파일명, 크기, 줄 수, 케이스 ID)

미해결 부분:
- 코드 미리보기가 `script.preview` 의존적 (API가 preview를 제공하지 않으면 빈 상태)
- 구문 강조 미구현
- 줄 번호 미구현
- 복사 버튼 미구현 (i18n 키만 준비)
- 케이스-스크립트 매핑 뷰 미구현
- 연관 피처 컬럼 미구현

"75개 생성" 한 줄만 표시되던 v0.1 대비 크게 개선되었으나, 사양서의 "코드 뷰어" 비전에는 못 미침.

---

### 결함 5: 실행 이력 없음

**판정: UNRESOLVED**

- 실행 이력 목록 UI 없음 -- 최신 1건만 표시하는 구조 그대로
- `GET /api/projects/{path}/runs` API 미호출
- 이전 실행과의 비교(diff) 기능 없음
- 실패만 보기 토글 없음

`loadExecution()`은 `GET /run` (단수)만 호출하고 최신 결과만 렌더링. Phase 3 범위(항목 13)이므로 Phase 1+2에서는 기대하지 않으나, 7대 결함 기준으로는 미해결.

---

### 결함 6: 수동 QA 연결 없음

**판정: PARTIALLY RESOLVED**

해결된 부분:
- 세션 시작/종료 워크플로우
- Pass/Fail 버튼 + 메모 입력
- 실시간 프로그레스 바 + 숫자 표시
- 항목 상세 패널

미해결 부분:
- 체크리스트 항목의 **출처 테스트 케이스 참조 표시** 없음 (사양서: "from: TC-003 (로그인 실패 시 에러 메시지)")
- 세션 이력 없음 (Phase 3 범위)
- 가드 메시지 없음 (cases 미생성 시)
- 케이스 ID 클릭 시 Cases 탭 이동 없음

v0.1의 "독립 체크리스트" 대비 Pass/Fail 판정과 프로그레스가 추가되어 개선됨. 그러나 "이전 단계와의 연결"이라는 핵심 결함은 부분적으로만 해소.

---

### 결함 7: 보고서 비어있음

**판정: PARTIALLY RESOLVED**

해결된 부분:
- Executive Summary 카드 (total, passed, failed, pass_rate)
- 커버리지 퍼센트 (피처/룰)
- Markdown 렌더링된 보고서 뷰
- 보고서 다운로드 (Markdown/HTML)

미해결 부분:
- 탭 진입 시 자동 생성 안 됨 (수동 "Load Report" 필요)
- 커버리지 프로그레스 바, 미커버 목록 없음
- 커버리지 매트릭스 없음
- 실패 분석 섹션 없음
- 이력 추이 없음
- 빈 보고서 방지 로직 불완전

v0.1의 "빈 Markdown 출력" 대비 Executive Summary와 커버리지 수치가 추가되어 확실히 개선됨. 그러나 사양서가 요구하는 "유용한 보고서"의 절반 수준.

---

## 7대 결함 점수표

| # | 결함 | 판정 | 비고 |
|---|------|------|------|
| 1 | 입력 문서 뷰어/다운로드 없음 | **RESOLVED** | 문서 뷰어 + 다운로드 완비 |
| 2 | 분석 흐름도/요약 없음 | **PARTIALLY RESOLVED** | 요약 카드 O, 필터/분포 시각화 X |
| 3 | 케이스 편집/추가 불가, 성공/실패 구분 없음 | **PARTIALLY RESOLVED** | 분류 구분 O, 편집은 Phase 3 |
| 4 | 스크립트 상세/매핑 없음 | **PARTIALLY RESOLVED** | 테이블 O, 코드 뷰어/매핑 X |
| 5 | 실행 이력 없음 | **UNRESOLVED** | Phase 3 범위 |
| 6 | 수동 QA 연결 없음 | **PARTIALLY RESOLVED** | Pass/Fail O, 출처 연결 X |
| 7 | 보고서 비어있음 | **PARTIALLY RESOLVED** | Executive Summary O, 심층 분석 X |

**RESOLVED**: 1/7
**PARTIALLY RESOLVED**: 5/7
**UNRESOLVED**: 1/7

---

## 업데이트된 점수: 48/100

### 산정 근거

| 영역 | v0.1 점수 | v0.2 점수 | 근거 |
|------|----------|----------|------|
| 전체 파이프라인 가시성 | 0 | 9/12 | 스테퍼 + 컨텍스트 바 + 가드 + CTA. 메타 정보 카드 누락 |
| 입력 문서 | 1 | 9/12 | 뷰어 + 렌더링 + 다운로드. 프로그레스/확인다이얼로그 누락 |
| 분석 결과 | 2 | 6/12 | 요약 카드 + 상세 패널. 필터/분포 시각화 전면 누락 |
| 테스트 케이스 | 1 | 7/12 | 분류 배지 + 필터 3종. 정렬/우선순위필터/요약카드 누락 |
| 스크립트 | 1 | 4/12 | 테이블 + 기본 상세. 코드뷰어/매핑 핵심 기능 누락 |
| 실행 | 2 | 3/12 | 최신 결과 표시만. 이력/비교/필터 전면 누락 |
| 수동 QA | 1 | 5/12 | Pass/Fail + 프로그레스. 출처 연결/가드 누락 |
| 보고서 | 0 | 5/16 | Executive Summary + 커버리지 수치. 심층 분석/자동생성 누락 |
| **합계** | **8 (->10)** | **48/100** | |

---

## PM 권장 사항

### 즉시 수정 (Quick Wins -- 예상 각 30분 이내)

1. **Report 자동 로드**: `switchTab("report")` 시 `loadReport()` 호출 추가. 사양서 명시 사항이며 사용자 경험 임팩트 큼
2. **삭제 확인 다이얼로그**: `deleteInput()`에 `confirm()` 추가
3. **Manual QA 가드 메시지**: `has_cases` 체크 + 가드 메시지 표시
4. **replaceState -> pushState**: 뒤로가기 히스토리 지원
5. **컨텍스트 바 스크립트 수**: `ctx-scripts` 요소 추가 + `updateContextBar()`에서 scripts 수 표시

### Phase 2 보강 (현재 구현 보완 -- 각 1-2시간)

6. **Analysis 필터**: 카테고리/우선순위 드롭다운 + 텍스트 검색 추가
7. **카테고리 분포 시각화**: `catMap` 데이터를 태그 그룹 UI로 렌더링
8. **Scripts 복사 버튼**: 상세 패널에 clipboard 복사 기능 추가 (i18n 키 이미 준비됨)
9. **Cases 요약 카드**: 총 수 + 타입별 + 분류별 카운트 stat-card 추가
10. **Overview 프로젝트 메타 카드**: 프로젝트명, 경로, 프로바이더, 모델 표시

### Phase 2 -> Phase 3 경계 확인

사양서 Phase 2에 포함되어 있으나 현재 미구현이고, Phase 3로 밀어도 제품 오너 평가에 큰 영향을 주지 않는 항목:

- Scripts 매핑 뷰 (토글) -- Phase 4로 이동 권장
- Analysis 카테고리 설명 툴팁 -- 있으면 좋지만 필수 아님

### Phase 3 진입 전 필수 조건

Phase 3 (편집 & 이력)에 들어가기 전에, Phase 2의 **핵심 누락 3가지**를 반드시 보강해야 한다:

1. Analysis 필터 (사용자가 100개 피처에서 원하는 것을 찾을 수 없으면 편집도 의미 없음)
2. Report 자동 생성 + 실패 분석 섹션 (보고서가 "빈 보고서"에서 "수동 로드 보고서"로 바뀌었을 뿐 근본 불만 미해소)
3. Scripts 코드 미리보기 실제 동작 확인 (API가 preview 데이터를 제공하는지 확인 필요)

---

## 결론

v0.2 Phase 1+2 구현은 v0.1 대비 **확실한 진전**이다. 파이프라인 흐름의 가시성(스테퍼, 가드, CTA)이 잡혔고, 입력 문서 뷰어는 사양 요구사항을 거의 충족한다. 그러나 Phase 2의 "핵심 뷰어" 5개 항목 중 4개(Analysis, Cases, Scripts, Report)가 50% 수준에 머물러 있어, "데이터가 보이긴 하는데 활용할 수 없는" 상태에서 완전히 벗어나지 못했다.

현재 점수 48/100은 사양서의 Phase 1+2 완료 성공 게이트("7대 결함 중 1,2,4,7 해소 확인")를 **미달**하는 수준이다. 결함 1만 RESOLVED이고, 2/4/7은 PARTIALLY RESOLVED이다.

Quick Wins 5개를 적용하면 약 55/100까지 올라갈 수 있고, Phase 2 보강 5개까지 적용하면 Phase 1+2 성공 게이트(결함 1,2,4,7 해소)에 도달할 수 있을 것으로 판단한다.
