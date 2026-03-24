# TestForge GUI v0.2 — 제품 사양서

**상태**: Draft
**작성자**: Alex (Product Manager)
**최종 수정**: 2026-03-23
**버전**: 0.2.0
**이해관계자**: 제품 오너 (LucaBlaq), 엔지니어링, QA

---

## 1. 문제 정의

### 핵심 문제

TestForge GUI v0.1은 QA 파이프라인의 각 단계(입력 → 분석 → 케이스 → 스크립트 → 실행 → 수동 QA → 보고서)를 나열만 할 뿐, **사용자가 각 단계를 이해하고, 조작하고, 다음 단계로 연결하는 데 필요한 정보와 인터랙션이 전무**하다.

### 제품 오너 원문 (10/100점)

> "QA 알바를 구해서 이거 쓰라고 하면 일반인이 쓸 수가 없다. 개발자인 나도 못 쓸 정도."

### 7대 결함 (제품 오너 지적)

| # | 결함 | 심각도 | 현재 상태 |
|---|------|--------|-----------|
| 1 | 입력 문서: 뷰어 없음, 다운로드 없음, Markdown 미렌더링 | CRITICAL | 파일 목록만 표시 |
| 2 | 분석: 리스트만 존재, 흐름도 없음, 요약 없음, 카테고리 설명 없음 | CRITICAL | 테이블 3개 나열 |
| 3 | 테스트 케이스: 편집/추가 불가, 긍정/부정 구분 없음 | CRITICAL | 읽기 전용 목록 |
| 4 | 스크립트: "75개 생성"만 표시, 케이스-스크립트 매핑 없음 | HIGH | 파일명+크기만 표시 |
| 5 | 실행: 이력 없음, 이전 실행 결과 미표시 | HIGH | 최신 1건만 표시 |
| 6 | 수동 QA: 이전 단계와 연결 없이 랜덤 등장 | HIGH | 독립 체크리스트 |
| 7 | 보고서: 비어 있음, 유용한 정보 없음, 이력 기반 보고서 없음 | CRITICAL | 빈 Markdown 출력 |

### 근본 원인

- **데이터 흐름 단절**: 각 탭이 독립된 페이지처럼 동작하며, 이전 단계의 산출물이 다음 단계에서 참조되지 않음
- **조작 불가**: 백엔드에 PUT API가 존재하나 프론트엔드에서 연결되지 않음 (분석 편집, 케이스 편집)
- **컨텍스트 부재**: 파이프라인 전체 진행 상황을 한눈에 볼 수 없음
- **렌더링 부재**: Markdown, 코드, 구조화된 데이터를 원시 텍스트로 출력

---

## 2. 목표 및 성공 지표

| 목표 | 지표 | 현재 | 목표 | 측정 기간 |
|------|------|------|------|-----------|
| 사용성 점수 개선 | 제품 오너 주관 평가 | 10/100 | 70/100 이상 | v0.2 출시 후 즉시 |
| QA 알바 독립 사용 | 가이드 없이 파이프라인 완주 가능 여부 | 불가능 | 가능 | v0.2 출시 후 1주 |
| 파이프라인 완주율 | 입력→보고서 전 과정 완료 비율 | 측정 불가 | 80%+ | v0.2 출시 후 2주 |
| 탭 간 이탈률 | 다음 단계로 진행하지 않고 이탈하는 비율 | 측정 불가 | 30% 이하 | v0.2 출시 후 2주 |

---

## 3. 비목표 (Non-Goals)

- v0.2에서 **멀티 유저/권한 관리**는 다루지 않음
- v0.2에서 **CI/CD 통합** (GitHub Actions, Jenkins 등)은 범위 밖
- v0.2에서 **실시간 SSE/WebSocket 스트리밍**은 범위 밖 (v0.3 예정)
- v0.2에서 **반응형 모바일 UI**는 최소한만 대응 (깨지지 않는 수준)
- v0.2에서 **ARIA 접근성** 전면 준수는 범위 밖

---

## 4. 사용자 페르소나

### Primary: 민지 — QA 담당자 (비개발자)

- **프로필**: QA 팀 주니어, 6개월 경력, 테스트 실행과 결과 보고가 주 업무
- **기술 수준**: GUI 도구 사용 가능, CLI/코드 경험 없음
- **목표**: 문서를 올리고, 생성된 테스트를 이해하고, 실행 결과를 보고서로 만들어 팀에 공유
- **페인 포인트**: "이 버튼 누르면 뭐가 되는 건지 모르겠어요", "어디까지 진행된 건지 안 보여요"

### Secondary: 재현 — 개발자 겸 QA 리드

- **프로필**: 풀스택 개발자, TestForge 도입 주도
- **기술 수준**: CLI, API 모두 사용 가능
- **목표**: LLM이 생성한 케이스를 검토/편집하고, 커버리지 갭을 파악하여 수동으로 보완
- **페인 포인트**: "편집이 안 되니까 결국 JSON 파일을 직접 열어서 고쳐야 해요"

---

## 5. 정보 아키텍처 — 전체 구조

```
+---------------------------------------------------------------+
| TestForge              [Project: my-webapp v]        [+ New]   |
+---------------------------------------------------------------+
| [my-webapp] 3 docs | 12 features | 24 cases | 75 scripts | 89%|  <- 컨텍스트 바 + 진행 스테퍼
+---------------------------------------------------------------+
| Overview | Inputs | Analysis | Cases | Scripts | Run | Manual | Report |
+---------------------------------------------------------------+
|                                                                |
|  [현재 탭 콘텐츠]                          [상세 패널 (슬라이드)]  |
|                                                                |
+---------------------------------------------------------------+
```

### 파이프라인 데이터 흐름

```
Inputs ──→ Analysis ──→ Cases ──→ Scripts ──→ Run ──→ Report
  │            │           │          │         │        │
  │            │           │          │         │        │
  │            │           ├──→ Manual QA ──────┘        │
  │            │           │                             │
  └── 문서 ────┘── 피처 ───┘── 케이스 ─── 스크립트 ── 결과 ── 보고서
```

**핵심 원칙**: 모든 탭은 이전 탭의 산출물을 참조하며, 다음 탭으로의 진행 CTA를 제공한다.

---

## 6. 탭별 상세 사양

---

### 6.0 Overview 탭 (신규)

#### 유저 스토리

> 민지(QA 담당자)로서, 프로젝트를 열면 전체 QA 파이프라인의 진행 상황을 한눈에 파악하고 싶다. 그래야 어디부터 작업해야 하는지 바로 알 수 있다.

#### 수락 기준

- [ ] 7단계 파이프라인 스테퍼(Inputs → Analysis → Cases → Scripts → Run → Manual → Report)가 수평으로 표시된다
- [ ] 각 단계는 상태 아이콘으로 구분된다: 완료(체크), 진행 가능(활성), 미도달(비활성)
- [ ] 각 단계 아이콘 아래에 요약 숫자가 표시된다 (예: "3 docs", "12 features", "24 cases")
- [ ] 현재 진행 가능한 다음 단계에 강조 CTA 버튼이 표시된다 (예: "Run Analysis →")
- [ ] 프로젝트 메타 정보 카드: 프로젝트명, 경로, LLM 프로바이더, 생성일, 마지막 활동일
- [ ] 스테퍼의 각 단계를 클릭하면 해당 탭으로 이동한다

#### 표시 정보

| 영역 | 데이터 | 소스 |
|------|--------|------|
| 파이프라인 스테퍼 | 각 단계 완료 여부 + 요약 수치 | 각 API GET 엔드포인트 |
| 프로젝트 메타 | 이름, 경로, 프로바이더, 모델 | `/api/config` + 프로젝트 설정 |
| 최근 활동 | 마지막 분석 시각, 마지막 실행 시각 | 파일 mtime |
| 커버리지 게이지 | 피처 커버리지 %, 룰 커버리지 % | `/api/projects/{path}/coverage` |

#### 인터랙션

| 액션 | 동작 |
|------|------|
| 스테퍼 단계 클릭 | 해당 탭으로 전환 |
| CTA 버튼 클릭 | 다음 미완료 단계 탭으로 이동 + 해당 동작 실행 |
| 프로젝트 설정 편집 | 프로바이더/모델 변경 모달 (v0.2 scope) |

#### 다른 탭과의 연결

- **입력**: Overview에서 "Start: Upload Documents →" CTA로 연결
- **보고서**: 커버리지 게이지 클릭 시 Report 탭으로 이동

---

### 6.1 Inputs 탭 (입력 문서)

#### 유저 스토리

> 민지(QA 담당자)로서, 업로드한 문서를 GUI에서 미리보기하고, Markdown은 렌더링된 형태로 읽고, 필요하면 다운로드하고 싶다. 그래야 분석에 올바른 문서가 들어갔는지 확인할 수 있다.

#### 수락 기준

- [ ] 드래그 앤 드롭 + 파일 선택 업로드가 작동한다
- [ ] 업로드된 파일 목록이 테이블로 표시된다: 아이콘, 파일명, 크기, 타입, 업로드 시각
- [ ] 파일명 클릭 시 상세 패널에 **문서 뷰어**가 열린다
  - Markdown (`.md`): 렌더링된 HTML로 표시 (제목, 목록, 코드 블록, 링크 지원)
  - 텍스트 (`.txt`): 고정폭 폰트로 표시
  - JSON/YAML: 구문 강조(syntax highlight)로 표시
  - 이미지 (`.png`, `.jpg`): 인라인 이미지로 표시
  - PDF/DOCX/PPTX/XLSX: "미리보기 불가, 다운로드하세요" 안내 + 다운로드 버튼
- [ ] 각 파일 행에 **다운로드 버튼**이 있다
- [ ] 각 파일 행에 **삭제 버튼**이 있고, 삭제 전 확인 다이얼로그가 표시된다
- [ ] 문서가 1개 이상 존재할 때 하단에 **"→ Run Analysis"** CTA 버튼이 표시된다
- [ ] 업로드 중 프로그레스 표시 (파일별)
- [ ] 지원 포맷 목록이 드롭존에 명시된다

#### 표시 정보

| 컬럼 | 데이터 |
|------|--------|
| 아이콘 | 파일 타입별 아이콘 (md, txt, pdf, docx, image, json, yaml) |
| 파일명 | `file.name` — 클릭 시 뷰어 오픈 |
| 타입 | `file.type` — 배지로 표시 |
| 크기 | `file.size` — formatBytes() |
| 액션 | 미리보기 / 다운로드 / 삭제 |

#### 인터랙션

| 액션 | 동작 |
|------|------|
| 파일 드래그 앤 드롭 | POST `/api/projects/{path}/inputs` 호출 → 테이블 갱신 |
| 파일명 클릭 | 상세 패널에 문서 뷰어 표시 (Markdown 렌더링 포함) |
| 다운로드 버튼 | 브라우저 파일 다운로드 실행 |
| 삭제 버튼 | 확인 다이얼로그 → DELETE `/api/inputs?project_path=...&filename=...` |
| "→ Run Analysis" CTA | Analysis 탭으로 전환 + 분석 실행 |

#### 다른 탭과의 연결

- **→ Analysis**: CTA 버튼으로 직접 연결. 분석 결과에 "소스 문서" 표시 시 Input 파일명 참조
- **← Overview**: Overview 스테퍼에서 문서 수 표시

#### 필요한 백엔드 변경

- [ ] `GET /api/projects/{path}/inputs/{filename}/content` — 파일 콘텐츠 반환 (text 계열) 또는 바이너리 스트림
- [ ] `GET /api/projects/{path}/inputs/{filename}/download` — 파일 다운로드 (Content-Disposition: attachment)

---

### 6.2 Analysis 탭 (분석 결과)

#### 유저 스토리

> 민지(QA 담당자)로서, 분석 결과를 단순 목록이 아니라 구조화된 요약과 함께 보고 싶다. 카테고리가 뭔지, 피처 간 관계가 어떤지 이해해야 다음 단계에서 적절한 테스트 케이스가 나왔는지 판단할 수 있다.

> 재현(QA 리드)으로서, 분석 결과의 피처/페르소나/비즈니스 룰을 직접 편집하고 싶다. LLM이 놓친 항목을 추가하거나, 잘못된 분류를 수정해야 한다.

#### 수락 기준

- [ ] **요약 카드 영역**: 분석 결과 상단에 통계 카드 표시
  - 총 피처 수, 총 페르소나 수, 총 비즈니스 룰 수, 총 스크린 수
  - 카테고리별 피처 분포 (카테고리명 + 개수, 막대 차트 또는 태그 그룹)
  - 우선순위별 피처 분포 (High / Medium / Low 비율)
- [ ] **카테고리 설명**: 각 카테고리명 옆에 툴팁 또는 배지로 해당 카테고리에 속한 피처 수 표시
- [ ] **피처 테이블**: ID, 이름, 카테고리, 우선순위, 소스 문서, 설명(truncated)
  - 행 클릭 시 상세 패널: 전체 설명, 태그 목록, 연관 스크린, 소스 문서명
  - 카테고리별 필터 드롭다운
  - 우선순위별 필터 드롭다운
  - 텍스트 검색 필터
- [ ] **페르소나 카드**: 각 페르소나를 카드 UI로 표시 (이름, 기술 수준, 목표, 페인 포인트)
  - 카드 클릭 시 상세 패널
- [ ] **비즈니스 룰 테이블**: ID, 이름, 조건, 기대 결과, 소스
  - 행 클릭 시 상세 패널
- [ ] **편집 기능** (인라인 편집):
  - 피처: 이름, 카테고리, 우선순위, 설명 편집 가능
  - 페르소나: 이름, 기술 수준, 목표, 페인 포인트 편집 가능
  - 비즈니스 룰: 이름, 조건, 기대 결과 편집 가능
  - "저장" 버튼 클릭 시 PUT `/api/projects/{path}/analysis` 호출
- [ ] **항목 추가/삭제**:
  - 각 섹션(피처, 페르소나, 비즈니스 룰)에 "+ 추가" 버튼
  - 각 행에 삭제 아이콘 (확인 다이얼로그)
- [ ] 분석 미실행 시 가드 메시지: "먼저 Inputs 탭에서 문서를 업로드하세요" + Inputs 탭 이동 링크
- [ ] 분석 완료 후 하단 CTA: **"→ Generate Test Cases"** (Cases 탭으로 이동 + 생성 실행)
- [ ] "Run Analysis" 버튼 클릭 시 로딩 스피너 + 진행 메시지 표시

#### 표시 정보

| 영역 | 데이터 | 소스 |
|------|--------|------|
| 통계 카드 | 피처/페르소나/룰/스크린 수 | `analysis.features.length` 등 |
| 카테고리 분포 | 카테고리별 피처 그룹핑 | `features.map(f => f.category)` |
| 우선순위 분포 | High/Med/Low 비율 | `features.map(f => f.priority)` |
| 피처 테이블 | id, name, category, priority, description, source | `analysis.features[]` |
| 페르소나 카드 | id, name, description, tech_level, goals, pain_points | `analysis.personas[]` |
| 룰 테이블 | id, name, condition, expected_behavior, source | `analysis.rules[]` |

#### 인터랙션

| 액션 | 동작 |
|------|------|
| "Run Analysis" 클릭 | POST → 로딩 → 결과 표시 |
| 피처 행 클릭 | 상세 패널 오픈 (읽기 모드) |
| 피처 행 "편집" 아이콘 | 상세 패널 오픈 (편집 모드) → 인라인 폼 |
| "저장" 클릭 | PUT `/api/projects/{path}/analysis` → toast 성공 |
| "+ 피처 추가" | 빈 폼으로 상세 패널 오픈 → 저장 시 목록에 추가 |
| 삭제 아이콘 | 확인 다이얼로그 → 목록에서 제거 → PUT으로 전체 저장 |
| 카테고리 필터 | 테이블 실시간 필터링 |
| "→ Generate Cases" CTA | Cases 탭 전환 + 생성 트리거 |

#### 다른 탭과의 연결

- **← Inputs**: 가드 메시지에서 Inputs 탭 링크. 피처의 `source` 필드가 Input 파일명 참조
- **→ Cases**: CTA 버튼으로 연결. 케이스의 `feature_id`가 분석 피처 ID 참조
- **→ Report**: 커버리지 계산 시 분석 피처/룰 ID 사용

---

### 6.3 Cases 탭 (테스트 케이스)

#### 유저 스토리

> 민지(QA 담당자)로서, 생성된 테스트 케이스를 긍정 테스트(정상 동작)와 부정 테스트(에러/엣지 케이스)로 구분해서 보고 싶다. 그래야 테스트 범위를 한눈에 파악할 수 있다.

> 재현(QA 리드)으로서, 생성된 테스트 케이스를 편집하고, 누락된 케이스를 수동으로 추가하고, 불필요한 케이스를 삭제하고 싶다. LLM 생성 결과를 그대로 쓸 수 없는 경우가 많다.

#### 수락 기준

- [ ] **요약 카드 영역**:
  - 총 케이스 수, 타입별(functional/usecase/checklist) 수, 긍정/부정/엣지 분류 수
  - 피처별 케이스 분포 (피처명 + 케이스 수)
  - 커버리지 상태: 케이스가 없는 피처 목록 (경고 아이콘)
- [ ] **테스트 케이스 테이블**:
  - 컬럼: ID, 제목, 타입, 분류(긍정/부정/엣지), 우선순위, 연관 피처, 상태
  - **분류(Nature) 컬럼**: 태그 기반 자동 분류
    - `tags`에 "negative"가 포함되면 → 부정 테스트 (빨간 배지)
    - `tags`에 "edge"가 포함되면 → 엣지 케이스 (노란 배지)
    - 그 외 → 긍정 테스트 (초록 배지)
  - 행 클릭 시 상세 패널: 전체 정보 (설명, 전제조건, 단계, 기대 결과, 태그, 연관 룰)
- [ ] **필터 & 정렬**:
  - 타입 필터 (all / functional / usecase / checklist)
  - 분류 필터 (all / positive / negative / edge)
  - 우선순위 필터 (all / high / medium / low)
  - 피처 필터 (드롭다운, 분석 결과의 피처 목록에서 채움)
  - 텍스트 검색
  - 컬럼 헤더 클릭 정렬
- [ ] **편집 기능**:
  - 행의 편집 아이콘 클릭 → 상세 패널에서 인라인 편집 (제목, 설명, 단계, 기대 결과, 우선순위, 태그)
  - 단계(steps) 편집: 순서 변경(드래그 or 위/아래 버튼), 추가, 삭제
  - "저장" 클릭 시 PUT `/api/projects/{path}/cases` 호출
- [ ] **케이스 추가**:
  - "+ Add Case" 버튼 → 빈 폼으로 상세 패널 오픈
  - 피처 선택 드롭다운 (분석 결과의 피처 목록)
  - 타입 선택 (functional / usecase / checklist)
  - ID 자동 생성 (TC-NNN 형식)
- [ ] **케이스 삭제**: 행 삭제 아이콘 → 확인 다이얼로그 → 목록에서 제거 → PUT 전체 저장
- [ ] **일괄 작업**:
  - 체크박스로 다중 선택
  - 일괄 삭제, 일괄 우선순위 변경, 일괄 태그 추가
- [ ] 분석 미실행 시 가드 메시지: "먼저 Analysis 탭에서 분석을 실행하세요" + Analysis 탭 링크
- [ ] 케이스 생성 완료 후 하단 CTA: **"→ Generate Scripts"** (Scripts 탭 이동)

#### 표시 정보

| 컬럼 | 데이터 | 소스 |
|------|--------|------|
| ID | `case.id` | cases.json |
| 제목 | `case.title \|\| case.name` | cases.json |
| 타입 | `case.type \|\| case.case_type` | cases.json — 배지(functional=파랑, usecase=보라, checklist=회색) |
| 분류 | tags 기반 자동 분류 | `case.tags` 파싱 — 배지(positive=초록, negative=빨강, edge=노랑) |
| 우선순위 | `case.priority` | cases.json — 배지(high=빨강, medium=노랑, low=파랑) |
| 피처 | `case.feature_id` → 피처 이름 조회 | cases.json + analysis.json |
| 상태 | `case.status` | cases.json — pending/approved/rejected |

#### 인터랙션

| 액션 | 동작 |
|------|------|
| "Generate Cases" 클릭 | POST → 타입 선택 드롭다운 값 전달 → 로딩 → 결과 표시 |
| 행 클릭 | 상세 패널 (읽기 모드) |
| 편집 아이콘 | 상세 패널 (편집 모드) |
| "+ Add Case" | 빈 폼으로 상세 패널 |
| 필터 변경 | 테이블 실시간 필터링 (클라이언트 사이드) |
| 체크박스 선택 | 일괄 작업 바 표시 |
| "→ Generate Scripts" CTA | Scripts 탭 전환 |

#### 다른 탭과의 연결

- **← Analysis**: 가드 메시지 링크. `feature_id` → 분석 피처 참조. 피처 컬럼에 피처 이름 표시
- **→ Scripts**: CTA 버튼. 스크립트가 케이스 ID 기반으로 생성됨
- **→ Manual QA**: 체크리스트 타입 케이스가 Manual QA 세션의 항목 소스
- **→ Report**: 커버리지 계산 시 케이스의 `feature_id`, `rule_ids` 참조

---

### 6.4 Scripts 탭 (테스트 스크립트)

#### 유저 스토리

> 재현(QA 리드)으로서, 생성된 75개 스크립트 각각이 어떤 테스트 케이스에 대응하는지 알고 싶다. 그리고 스크립트 코드를 미리보기로 확인하고 싶다. 그래야 자동화 테스트가 올바르게 작성되었는지 판단할 수 있다.

#### 수락 기준

- [ ] **요약 카드 영역**:
  - 총 스크립트 수, 총 파일 크기, 커버된 케이스 수 / 전체 케이스 수
  - 매핑 상태: 케이스 대비 스크립트 커버리지 비율
- [ ] **스크립트 테이블**:
  - 컬럼: 파일명, 크기, 연관 케이스 ID(들), 연관 피처
  - **연관 케이스 컬럼**: 파일명에서 케이스 ID 파싱 또는 매핑 데이터 활용
  - 연관 케이스 ID 클릭 시 → Cases 탭 해당 케이스 상세 패널 오픈
- [ ] **코드 미리보기**:
  - 파일명 클릭 시 상세 패널에 **코드 뷰어** 표시
  - Playwright/Python 코드 구문 강조 (최소한 `<pre><code>` + 기본 강조)
  - 줄 번호 표시
  - "복사" 버튼 (클립보드 복사)
- [ ] **케이스-스크립트 매핑 뷰** (토글 가능):
  - 좌측: 케이스 목록, 우측: 대응 스크립트
  - 매핑 없는 케이스는 경고 아이콘으로 표시
- [ ] 케이스 미생성 시 가드 메시지: "먼저 Cases 탭에서 테스트 케이스를 생성하세요" + Cases 탭 링크
- [ ] 스크립트 생성 완료 후 하단 CTA: **"→ Run Tests"** (Execution 탭 이동)

#### 표시 정보

| 컬럼 | 데이터 | 소스 |
|------|--------|------|
| 파일명 | 스크립트 파일 경로 | `/api/projects/{path}/scripts` 응답 |
| 크기 | 파일 크기 | 파일 시스템 |
| 연관 케이스 | 케이스 ID (파일명 파싱 or 매핑) | 파일명 규칙 기반 |
| 연관 피처 | 케이스의 feature_id → 피처 이름 | cases.json + analysis.json |

#### 인터랙션

| 액션 | 동작 |
|------|------|
| "Generate Scripts" 클릭 | POST → 로딩 → 결과 표시 |
| 파일명 클릭 | 상세 패널에 코드 뷰어 |
| 연관 케이스 ID 클릭 | Cases 탭 전환 + 해당 케이스 상세 패널 오픈 |
| "복사" 버튼 | 코드 클립보드 복사 |
| 매핑 뷰 토글 | 테이블 ↔ 매핑 뷰 전환 |
| "→ Run Tests" CTA | Execution 탭 전환 |

#### 다른 탭과의 연결

- **← Cases**: 가드 메시지 링크. 케이스 ID 기반 매핑 표시
- **→ Execution**: CTA 버튼. 실행 시 이 스크립트들이 실행됨

#### 필요한 백엔드 변경

- [ ] `GET /api/projects/{path}/scripts` — 스크립트 목록 (파일명, 크기, 생성 시각) 반환
- [ ] `GET /api/projects/{path}/scripts/{filename}/content` — 스크립트 소스 코드 반환

---

### 6.5 Execution 탭 (테스트 실행)

#### 유저 스토리

> 민지(QA 담당자)로서, 테스트를 실행하고 결과를 실시간으로 보고 싶다. 그리고 이전 실행 이력을 비교해서 "이번에 새로 실패한 건 뭔지" 파악하고 싶다.

#### 수락 기준

- [ ] **실행 이력 목록** (좌측 또는 상단):
  - 이전 실행 목록 표시: 실행 시각, 총 케이스, Pass/Fail 수, 소요 시간
  - 각 이력 클릭 시 해당 실행의 상세 결과 표시
  - 최신 실행이 기본 선택
- [ ] **실행 결과 상세** (현재 선택된 실행):
  - 요약 카드: Total, Passed (초록), Failed (빨강), Skipped (회색), 소요 시간
  - 프로그레스 바: Pass 비율 시각화
  - 결과 테이블: 케이스 ID, 케이스 제목, 상태 배지, 소요 시간(ms), 에러 메시지(truncated)
  - 행 클릭 시 상세 패널: 전체 stdout, stderr, return code, 스크린샷 (있으면)
- [ ] **실패 케이스 필터**: "실패만 보기" 토글 — 실패 케이스를 상단에 정렬하거나 필터링
- [ ] **실행 비교** (v0.2 MVP):
  - 현재 실행과 직전 실행의 diff 표시: 새로 실패한 케이스(빨간 NEW 배지), 새로 통과한 케이스(초록 FIX 배지)
- [ ] **실행 옵션**:
  - 태그 필터: 특정 태그의 케이스만 실행 (예: "smoke", "regression")
  - 병렬 실행 수 설정 (parallel 파라미터)
- [ ] 스크립트 미생성 시 가드 메시지: "먼저 Scripts 탭에서 스크립트를 생성하세요" + Scripts 탭 링크
- [ ] 실행 완료 후 하단 CTA: **"→ View Report"** (Report 탭 이동)

#### 표시 정보

| 영역 | 데이터 | 소스 |
|------|--------|------|
| 실행 이력 | 시각, total, passed, failed, duration | results.json 파일 목록 (타임스탬프) |
| 요약 카드 | total, passed, failed, skipped | `POST /run` 응답의 `summary` |
| 결과 테이블 | case_id, status, duration_ms, output, stderr, return_code | `POST /run` 응답의 `results[]` |
| 실행 비교 | 이전 실행 vs 현재 실행의 status diff | 두 결과 세트 클라이언트 사이드 비교 |

#### 인터랙션

| 액션 | 동작 |
|------|------|
| "Run Tests" 클릭 | POST `/api/projects/{path}/run` → 로딩 스피너 → 결과 표시 |
| 이력 항목 클릭 | 해당 실행의 결과 로드 |
| 결과 행 클릭 | 상세 패널 (stdout, stderr, 스크린샷) |
| "실패만 보기" 토글 | 결과 테이블 필터링 |
| 태그 입력 | 실행 대상 케이스 필터 |
| "→ View Report" CTA | Report 탭 전환 |

#### 다른 탭과의 연결

- **← Scripts**: 가드 메시지 링크. 실행 대상 스크립트 참조
- **→ Report**: CTA 버튼. 보고서가 실행 결과 기반으로 생성됨
- **← Cases**: 결과 테이블의 케이스 ID 클릭 → Cases 탭 해당 케이스 상세

#### 필요한 백엔드 변경

- [ ] `GET /api/projects/{path}/runs` — 실행 이력 목록 (results.json 파일들의 메타데이터)
- [ ] `GET /api/projects/{path}/runs/{run_id}` — 특정 실행의 상세 결과

---

### 6.6 Manual QA 탭 (수동 QA 체크리스트)

#### 유저 스토리

> 민지(QA 담당자)로서, 수동 QA 체크리스트가 어떤 테스트 케이스에서 파생되었는지 알고 싶다. 그리고 체크리스트 항목별로 Pass/Fail 판정과 메모를 남기면서, 전체 진행률을 실시간으로 보고 싶다.

#### 수락 기준

- [ ] **세션 이력**:
  - 이전 수동 QA 세션 목록 표시: 시작 시각, 완료 여부, 체크 항목 수 / 전체 수
  - 완료된 세션 클릭 시 읽기 전용으로 결과 표시
- [ ] **활성 세션 UI**:
  - 프로그레스 바: 체크한 항목 수 / 전체 항목 수
  - 숫자 표시: "12 / 24 항목 확인됨"
  - 각 항목 카드:
    - 항목 제목 + 설명
    - **출처 표시**: "from: TC-003 (로그인 실패 시 에러 메시지)" — 원본 케이스 참조
    - 단계 (steps) 표시 (있을 경우)
    - Pass / Fail / Skip 버튼 (3개)
    - 메모 입력 필드 (선택적)
    - 스크린샷/증빙 업로드 영역 (v0.2는 placeholder, v0.3에서 구현)
  - 상태별 필터: 전체 / 미완료 / Pass / Fail
- [ ] **케이스 연결**: 체크리스트 항목에 원본 테스트 케이스 ID 표시. 클릭 시 Cases 탭 해당 케이스 상세
- [ ] **세션 시작 시 안내**: "이 체크리스트는 [N]개의 테스트 케이스에서 생성되었습니다"
- [ ] "Finish Session" 클릭 시 완료 확인 다이얼로그: 미완료 항목 수 경고
- [ ] 세션 완료 후 하단 CTA: **"→ Generate Report"** (Report 탭 이동)

#### 표시 정보

| 영역 | 데이터 | 소스 |
|------|--------|------|
| 세션 이력 | session_id, 시작 시각, 상태, 체크 수/전체 수 | 파일 시스템 |
| 프로그레스 | checked / total | `manual/progress` API |
| 항목 카드 | item_id, title, description, steps, 출처 케이스 | `manual/start` 응답의 `items[]` |
| 판정 상태 | pass / fail / skip + note | `manual/check/{item_id}` 응답 |

#### 인터랙션

| 액션 | 동작 |
|------|------|
| "Start Session" 클릭 | POST `/manual/start` → 체크리스트 표시 |
| Pass/Fail/Skip 버튼 | PUT `/manual/check/{item_id}` → 프로그레스 업데이트 |
| 메모 입력 → 저장 | PUT 시 `note` 필드 포함 |
| 출처 케이스 ID 클릭 | Cases 탭 전환 + 상세 패널 오픈 |
| 이력 항목 클릭 | 해당 세션 결과 읽기 전용 표시 |
| "Finish Session" 클릭 | POST `/manual/finish` → 완료 처리 |
| "→ Generate Report" CTA | Report 탭 전환 |

#### 다른 탭과의 연결

- **← Cases**: 체크리스트 항목이 케이스에서 파생됨. 출처 케이스 ID로 양방향 참조
- **→ Report**: 수동 QA 결과가 보고서에 포함됨
- **← Execution**: 자동화 실행과 수동 QA를 합산한 전체 테스트 커버리지 표시

---

### 6.7 Report 탭 (보고서)

#### 유저 스토리

> 민지(QA 담당자)로서, 테스트 결과를 구조화된 보고서로 보고 팀에 공유하고 싶다. 보고서에는 요약, 커버리지, 실패 분석, 이력 추이가 포함되어야 한다. 빈 페이지가 아니라 실제로 유용한 정보가 있어야 한다.

#### 수락 기준

- [ ] **보고서 대시보드** (Report 탭 진입 시 기본 뷰):
  - **Executive Summary 카드**:
    - 전체 테스트 수, Pass/Fail/Skip 수 + 비율
    - 자동화 테스트 결과 + 수동 QA 결과 합산
    - 마지막 실행 시각
  - **커버리지 섹션**:
    - 피처 커버리지: N/M 피처 커버됨 (퍼센트 + 프로그레스 바)
    - 룰 커버리지: N/M 룰 커버됨 (퍼센트 + 프로그레스 바)
    - 미커버 피처/룰 목록 (경고 아이콘, 클릭 시 Analysis 탭 해당 항목)
  - **커버리지 매트릭스** (토글 가능):
    - 행: 피처, 열: 케이스, 셀: 존재 여부 (체크/빈칸)
    - 또는 행: 룰, 열: 케이스
  - **실패 분석 섹션**:
    - 실패한 테스트 케이스 목록 + 에러 메시지 요약
    - 실패 케이스 클릭 시 Execution 탭 해당 결과 상세
  - **이력 추이 섹션** (v0.2 기본):
    - 최근 5회 실행의 Pass/Fail 추이 (간단한 막대 차트 또는 텍스트 테이블)
    - 각 실행의 타임스탬프 + Pass 비율
- [ ] **보고서 내보내기**:
  - Markdown 형식 다운로드 버튼
  - HTML 형식 다운로드 버튼
  - Markdown 렌더링된 뷰 (현재 monospace → 렌더링된 HTML로 변경)
- [ ] **보고서 자동 생성**: 탭 진입 시 최신 데이터로 자동 생성 (수동 "Load" 불필요)
- [ ] 실행 결과 없을 시 가이드 메시지: "테스트를 먼저 실행하세요" + Execution 탭 링크
- [ ] 빈 보고서가 절대로 표시되지 않음 — 데이터가 부족하면 어떤 데이터가 필요한지 안내

#### 표시 정보

| 영역 | 데이터 | 소스 |
|------|--------|------|
| Executive Summary | total, passed, failed, skipped, pass_rate | `/api/projects/{path}/run` + `/manual/progress` |
| 커버리지 | feature_coverage_pct, rule_coverage_pct, uncovered lists | `/api/projects/{path}/coverage` |
| 커버리지 매트릭스 | feature_matrix, rule_matrix | `/api/projects/{path}/coverage` |
| 실패 분석 | 실패 케이스 목록 + 에러 메시지 | 실행 결과 |
| 이력 추이 | 최근 N회 실행의 pass/fail 수치 | `/api/projects/{path}/runs` |
| 렌더링된 보고서 | 전체 Markdown 보고서 | `/api/projects/{path}/report?fmt=markdown` |

#### 인터랙션

| 액션 | 동작 |
|------|------|
| 탭 진입 | 자동으로 최신 보고서 생성 + 커버리지 로드 |
| "Download Markdown" | 보고서 파일 다운로드 |
| "Download HTML" | HTML 보고서 다운로드 |
| 미커버 피처 클릭 | Analysis 탭 해당 피처 상세 |
| 실패 케이스 클릭 | Execution 탭 해당 결과 상세 |
| 이력 행 클릭 | Execution 탭 해당 실행 이력 |
| 매트릭스 토글 | 피처 매트릭스 ↔ 룰 매트릭스 전환 |

#### 다른 탭과의 연결

- **← Execution**: 실행 결과 데이터로 보고서 생성. 실패 케이스 클릭으로 양방향
- **← Manual QA**: 수동 QA 결과 합산
- **← Analysis**: 커버리지 계산에 피처/룰 사용. 미커버 항목 클릭으로 양방향
- **← Cases**: 커버리지 매트릭스에 케이스 ID 표시

---

## 7. 공통 UI 사양

### 7.1 컨텍스트 바 개선

현재 컨텍스트 바를 확장하여 파이프라인 진행 상태를 표시한다.

```
[my-webapp] 3 docs | 12 features | 24 cases | 75 scripts | Last run: 18/24 passed | 89% coverage
```

- 각 항목 클릭 시 해당 탭으로 이동
- 파이프라인 미도달 단계는 회색으로 표시 (예: 스크립트 미생성 시 "- scripts")

### 7.2 상세 패널 (Detail Panel)

기존 슬라이드 패널을 개선한다.

- **읽기 모드**: 현재와 동일, 필드별 표시
- **편집 모드**: 각 필드가 인라인 폼으로 전환
  - 텍스트 필드: `<input>` 또는 `<textarea>`
  - 선택 필드: `<select>` (우선순위, 카테고리, 타입 등)
  - 태그 필드: 태그 입력 + 배지 표시 (추가/삭제)
  - 목록 필드: 항목 추가/삭제/순서변경
- **읽기 → 편집 전환**: 패널 상단 "편집" 버튼
- **저장/취소**: 패널 하단 "저장" + "취소" 버튼
- **크기**: 패널 폭 최소 400px, 최대 화면 50%

### 7.3 Markdown 렌더링

모든 Markdown 콘텐츠에 적용한다.

- 기존 `simpleMarkdown()` 함수를 확장하거나 경량 라이브러리(marked.js 등) 도입
- 지원 요소: 제목(h1-h4), 목록(ul/ol), 코드 블록(```), 인라인 코드(`), 링크, 볼드/이탈릭, 테이블
- 보고서 탭: 전체 보고서 Markdown 렌더링
- 입력 탭: .md 파일 미리보기
- 분석 탭: 설명 필드 Markdown 렌더링

### 7.4 가드 메시지 개선

파이프라인 의존성을 명확히 안내한다.

| 탭 | 가드 조건 | 메시지 | 액션 |
|---|---------|--------|------|
| Analysis | inputs 0개 | "먼저 Inputs 탭에서 문서를 업로드하세요" | [Inputs 탭으로 이동] 버튼 |
| Cases | analysis 없음 | "먼저 Analysis 탭에서 분석을 실행하세요" | [Analysis 탭으로 이동] 버튼 |
| Scripts | cases 0개 | "먼저 Cases 탭에서 테스트 케이스를 생성하세요" | [Cases 탭으로 이동] 버튼 |
| Execution | scripts 0개 | "먼저 Scripts 탭에서 스크립트를 생성하세요" | [Scripts 탭으로 이동] 버튼 |
| Manual QA | cases 0개 | "먼저 Cases 탭에서 테스트 케이스를 생성하세요" | [Cases 탭으로 이동] 버튼 |
| Report | run 없음 | "테스트를 먼저 실행하세요" | [Execution 탭으로 이동] 버튼 |

### 7.5 로딩 & 에러 상태

- **로딩**: 각 API 호출 시 해당 영역에 스피너 + "분석 중..." / "생성 중..." / "실행 중..." 메시지
- **에러**: toast 알림 (빨간색, 6초 자동 닫기) + 해당 영역에 에러 메시지 표시
- **타임아웃**: LLM 호출은 최대 120초 (현재 30초 → 증가 필요). 타임아웃 시 재시도 안내

### 7.6 탭 간 네비게이션 헬퍼

- CTA 버튼: 각 탭 하단에 다음 단계 CTA (파란색 강조 버튼)
- 크로스 참조 링크: 피처 ID, 케이스 ID 등이 다른 탭에 표시될 때 클릭 가능한 링크
- 브라우저 뒤로가기: 탭 전환 시 URL hash 업데이트 (`#inputs`, `#analysis` 등)로 히스토리 지원

---

## 8. 탭 간 데이터 흐름 매트릭스

```
                 Inputs   Analysis   Cases   Scripts   Run   Manual   Report
Inputs             -        →src      -        -        -      -        -
Analysis          ←guard     -       →feat     -        -      -       →cov
Cases             -        ←feat      -      →case     -     →check   →cov
Scripts           -          -       ←case     -       →exec   -        -
Run               -          -        -       ←exec     -      -       →result
Manual            -          -       ←check    -        -      -       →result
Report            -        ←cov     ←cov       -      ←result ←result   -
```

**범례**:
- `→src`: 소스 문서 참조를 제공
- `→feat`: 피처 ID를 제공
- `→case`: 케이스 ID를 제공
- `→exec`: 실행 대상 스크립트를 제공
- `→check`: 체크리스트 항목을 제공
- `→cov`: 커버리지 데이터를 제공
- `→result`: 실행 결과를 제공
- `←guard`: 가드 의존성 (데이터 없으면 차단)

---

## 9. 필요한 백엔드 API 변경 요약

### 신규 API

| 엔드포인트 | 메서드 | 용도 |
|-----------|--------|------|
| `/api/projects/{path}/inputs/{filename}/content` | GET | 입력 파일 콘텐츠 반환 (텍스트/이미지) |
| `/api/projects/{path}/inputs/{filename}/download` | GET | 입력 파일 다운로드 |
| `/api/projects/{path}/scripts` | GET | 스크립트 목록 (파일명, 크기, 생성 시각) |
| `/api/projects/{path}/scripts/{filename}/content` | GET | 스크립트 소스 코드 반환 |
| `/api/projects/{path}/runs` | GET | 실행 이력 목록 |
| `/api/projects/{path}/runs/{run_id}` | GET | 특정 실행의 상세 결과 |
| `/api/projects/{path}/manual/sessions` | GET | 수동 QA 세션 이력 목록 |

### 기존 API 수정

| 엔드포인트 | 변경 내용 |
|-----------|-----------|
| `POST /api/projects/{path}/run` | 결과를 타임스탬프 기반 파일로 저장 (이력 보존) |
| `GET /api/projects/{path}/run` | `runs` 엔드포인트로 리팩터링하되, 하위 호환 유지 |

---

## 10. 구현 우선순위 (Phase 계획)

### Phase 1 — 기반 (1주)

**목표**: 파이프라인 흐름이 보이고, 기본 데이터가 표시되는 상태

| # | 항목 | 사이즈 | 7대 결함 대응 |
|---|------|--------|-------------|
| 1 | Overview 탭 + 파이프라인 스테퍼 | M | 전체 |
| 2 | 컨텍스트 바 확장 (파이프라인 상태) | S | 전체 |
| 3 | 가드 메시지 + 탭 이동 CTA 전체 적용 | S | 6, 7 |
| 4 | 탭 하단 CTA ("→ 다음 단계") 전체 적용 | S | 전체 |
| 5 | URL hash 기반 탭 라우팅 | XS | 전체 |

### Phase 2 — 핵심 뷰어 (1주)

**목표**: 각 탭에서 데이터를 제대로 볼 수 있는 상태

| # | 항목 | 사이즈 | 7대 결함 대응 |
|---|------|--------|-------------|
| 6 | Inputs 문서 뷰어 (Markdown 렌더링, 다운로드) | M | 1 |
| 7 | Analysis 요약 카드 + 카테고리 설명 + 필터 | M | 2 |
| 8 | Cases 분류 컬럼 (긍정/부정/엣지) + 필터 확장 | M | 3 |
| 9 | Scripts 코드 뷰어 + 케이스 매핑 | M | 4 |
| 10 | Report Markdown 렌더링 + Executive Summary 카드 | M | 7 |

### Phase 3 — 편집 & 이력 (1주)

**목표**: 사용자가 데이터를 조작하고, 이력을 비교할 수 있는 상태

| # | 항목 | 사이즈 | 7대 결함 대응 |
|---|------|--------|-------------|
| 11 | Analysis 인라인 편집 (피처/페르소나/룰 CRUD) | L | 2 |
| 12 | Cases 인라인 편집 + 수동 추가 + 삭제 | L | 3 |
| 13 | Execution 이력 목록 + 이전 실행 비교 | M | 5 |
| 14 | Manual QA 세션 이력 + 케이스 출처 표시 | M | 6 |
| 15 | Report 커버리지 매트릭스 + 실패 분석 + 이력 추이 | L | 7 |

### Phase 4 — 품질 & 연결 (1주)

**목표**: 탭 간 크로스 참조가 매끄럽고, UX 세부 사항이 마무리된 상태

| # | 항목 | 사이즈 | 7대 결함 대응 |
|---|------|--------|-------------|
| 16 | 크로스 참조 링크 (ID 클릭 → 해당 탭 이동) | M | 4, 6 |
| 17 | Cases 일괄 작업 (다중 선택, 일괄 삭제/태그) | M | 3 |
| 18 | Scripts 매핑 뷰 (케이스 ↔ 스크립트) | M | 4 |
| 19 | 로딩/에러 상태 전면 개선 | S | 전체 |
| 20 | API 타임아웃 120초 확장 | XS | 전체 |

---

## 11. 기술 고려사항

### 의존성

| 항목 | 현재 | v0.2 |
|------|------|------|
| Markdown 렌더링 | 자체 `simpleMarkdown()` (불완전) | marked.js CDN 도입 또는 자체 확장 |
| 코드 구문 강조 | 없음 | highlight.js CDN 도입 (선택적) |
| 차트 | 없음 | 텍스트 기반 테이블로 대체 (v0.2), Chart.js (v0.3) |
| 상태 관리 | 전역 변수 | 전역 변수 유지 (v0.2는 vanilla JS 유지) |

### 리스크

| 리스크 | 가능성 | 영향 | 완화 |
|--------|--------|------|------|
| LLM API 타임아웃 (분석/생성 시) | 높음 | 높음 | 타임아웃 120초 확장 + 재시도 버튼 |
| 대용량 프로젝트 성능 (100+ 케이스) | 중간 | 중간 | 페이지네이션 (20개 단위) + 가상 스크롤 (v0.3) |
| 동시 편집 충돌 | 낮음 | 중간 | 단일 사용자 가정 (v0.2), 낙관적 잠금 (v0.3) |

### 열린 질문

- [ ] Markdown 렌더링에 외부 라이브러리(marked.js) 도입할지, 자체 `simpleMarkdown()` 확장할지 — **권장: marked.js CDN**
- [ ] 실행 이력 보존 기간/개수 제한 — **권장: 최근 20회**
- [ ] 수동 QA 세션 이력 보존 — **권장: 전체 보존, UI는 최근 10회 표시**

---

## 12. 출시 계획

| 단계 | 일정 | 대상 | 성공 게이트 |
|------|------|------|-----------|
| Phase 1+2 완료 | +2주 | 내부 | 7대 결함 중 1,2,4,7 해소 확인 |
| Phase 3 완료 | +3주 | 내부 | 7대 결함 전체 해소, 제품 오너 재평가 50/100+ |
| Phase 4 완료 (v0.2 GA) | +4주 | 공개 | 제품 오너 재평가 70/100+, QA 알바 독립 사용 테스트 통과 |

### 롤백 기준

- v0.2 배포 후 기존 v0.1 기능이 정상 작동하지 않는 경우 v0.1로 롤백
- 백엔드 API 하위 호환성 깨지는 경우 즉시 수정

---

## 13. 부록

### A. 현재 백엔드 API 전체 목록 (v0.1)

```
GET    /api/health
GET    /api/config
GET    /api/projects?dir=...
POST   /api/projects
GET    /api/projects/{path}/inputs
POST   /api/projects/{path}/inputs          (파일 업로드)
DELETE /api/inputs?project_path=...&filename=...
GET    /api/projects/{path}/analysis
POST   /api/projects/{path}/analysis        (분석 실행)
PUT    /api/projects/{path}/analysis         (분석 편집)
GET    /api/projects/{path}/cases
POST   /api/projects/{path}/cases            (케이스 생성)
PUT    /api/projects/{path}/cases             (케이스 편집)
POST   /api/projects/{path}/scripts          (스크립트 생성)
POST   /api/projects/{path}/run              (테스트 실행)
GET    /api/projects/{path}/run              (최신 결과)
POST   /api/projects/{path}/manual/start
PUT    /api/projects/{path}/manual/check/{id}
GET    /api/projects/{path}/manual/progress
POST   /api/projects/{path}/manual/finish
GET    /api/projects/{path}/report?fmt=...
GET    /api/projects/{path}/coverage
```

### B. 데이터 모델 요약

```
Feature:       id, name, description, category, priority, screens[], tags[], source
Screen:        id, name, description, url_pattern, features[], elements[]
Persona:       id, name, description, goals[], pain_points[], tech_level
BusinessRule:  id, name, description, condition, expected_behavior, source
TestCase:      id, title, description, feature_id, priority, type, tags[],
               preconditions[], steps[{action, expected_result, input_data}],
               expected_result, rule_ids[], status
CoverageReport: total_features, covered_features, feature_coverage_pct,
                total_rules, covered_rules, rule_coverage_pct,
                feature_matrix{}, rule_matrix{}, uncovered_features[], uncovered_rules[]
TestCaseResult: id, name, status, duration_ms, error_message, screenshot_paths[], steps[], tags[]
ReportRun:     project, started_at, finished_at, environment{}, results[]
```

### C. 7대 결함 → 탭 매핑

| 결함 | 해소 탭 | Phase |
|------|---------|-------|
| 1. 입력 뷰어/다운로드/Markdown 미렌더링 | Inputs | Phase 2 (#6) |
| 2. 분석 흐름도/요약/카테고리 설명 없음 | Analysis | Phase 2 (#7) + Phase 3 (#11) |
| 3. 케이스 편집/추가/긍정-부정 구분 없음 | Cases | Phase 2 (#8) + Phase 3 (#12) |
| 4. 스크립트 상세/케이스 매핑 없음 | Scripts | Phase 2 (#9) + Phase 4 (#18) |
| 5. 실행 이력 없음 | Execution | Phase 3 (#13) |
| 6. 수동 QA 연결 없음 | Manual QA | Phase 3 (#14) |
| 7. 보고서 비어있음 | Report | Phase 2 (#10) + Phase 3 (#15) |
