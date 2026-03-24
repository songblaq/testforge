# TestForge v0.3 — 구현 요약

**날짜:** 2026-03-24
**버전:** v0.3.0
**상태:** 구현 완료

## 변경 요약

### P0: 전 엔티티 CRUD (완료)

#### 백엔드 API 추가/변경

| 엔티티 | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Feature | `POST .../analysis/features` | `GET .../analysis` | `PUT .../analysis/features/{id}` | `DELETE .../analysis/features/{id}` |
| Persona | `POST .../analysis/personas` | `GET .../analysis` | `PUT .../analysis/personas/{id}` | `DELETE .../analysis/personas/{id}` |
| Rule | `POST .../analysis/rules` | `GET .../analysis` | `PUT .../analysis/rules/{id}` | `DELETE .../analysis/rules/{id}` |
| Case | `POST .../cases/item` | `GET .../cases` | `PUT .../cases/item/{id}` | `DELETE .../cases/item/{id}` |
| Script | (generate) | `GET .../scripts/{name}` | `PUT .../scripts/{name}` | `DELETE .../scripts/{name}` |

#### 프론트엔드 UI
- 모든 Analysis 테이블(Feature/Persona/Rule)에 **+ 추가** 버튼 + 행별 **편집/삭제** 아이콘
- Cases 테이블에 **+ 케이스 추가** 버튼 + 행별 **편집/삭제** + **체크박스 벌크 삭제**
- Scripts 테이블에 행별 **편집/삭제** 아이콘
- 공유 CRUD 모달 (폼 기반 생성/편집)
- 확인 다이얼로그 (삭제 전 확인)

### P0: 생성/재생성 시맨틱 분리 (완료)

- `POST .../cases`에 `mode` 파라미터 추가: `generate` | `regenerate` | `new_version`
- `regenerate` 모드 시 기존 데이터를 `cases_backup.json`으로 백업 후 덮어쓰기
- `POST .../scripts`에도 `mode` 파라미터 추가

### P0: 권위적 다대다 매핑 모델 (완료)

- `.testforge/mappings.json`에 권위적 매핑 저장
- 매핑 API: `GET/POST/DELETE .../mappings`
- 스크립트 생성 시 자동 매핑 생성 (`_auto_create_mappings`)
- 매핑 출처 표시: `authoritative` | `generated` | `manual` | `heuristic`
- 스크립트 삭제 시 관련 매핑 자동 정리
- UI에서 매핑 출처별 색상 배지 표시

### P0: 실행 상세 + 실패 추적 (완료)

- 실행 결과에 `stderr`, `return_code`, `output`, `duration_ms` 포함
- 상세 패널에서 전체 에러 메시지, 표준 오류, 종료 코드 표시
- 이뮤터블 실행 기록: `run_{run_id}.json` 파일로 저장

### P0: 이뮤터블 보고서 이력 (완료)

- 보고서 생성 시 `output/reports/report_{report_id}.md|html` + `.meta.json` 저장
- 보고서 이력 API: `GET .../reports` (목록), `GET .../reports/{id}` (상세)
- UI에서 보고서 이력 테이블 표시 + 과거 보고서 조회

### P0: 이뮤터블 실행 이력 (완료)

- `run_id` = 타임스탬프 + UUID 해시
- `output/run_{run_id}.json`으로 각 실행 기록 보존
- 실행 이력 API: `GET .../runs` (목록), `GET .../runs/{id}` (상세)
- UI에서 실행 이력 테이블 + 과거 실행 결과 조회

### P1: 양방향 드릴다운 네비게이션 (완료)

- Case 상세 → 매핑된 Script 클릭 → Script 상세로 직접 이동
- Script 상세 → 매핑된 Case 클릭 → Case 상세로 직접 이동
- 매핑 출처(authoritative/heuristic/manual) 배지 표시
- 탭 전환만이 아닌 **직접 엔티티 이동** 구현

### P1: 다국어 콘텐츠 정책 (정의됨)

**선택된 정책: 소스 아티팩트 + 번역 작업 워크플로우**

- UI 언어 전환: 한국어(기본) / 베트남어 / 영어 — 기존 동작 유지
- 생성된 콘텐츠(분석 결과, 케이스 등)는 **생성 시 언어로 저장**
- 언어 전환 시 기존 사람이 편집한 콘텐츠를 **자동으로 덮어쓰지 않음**
- 향후 번역 작업: LLM 기반 번역 API 추가 예정 (Phase 4)

### P2: UX 개선 (완료)

- 69개 신규 i18n 키 × 3개 언어 (한/영/베) 추가
- CRUD 관련 CSS 스타일 (~170줄)
- 벌크 액션 바, 매핑 배지, 드릴다운 링크, 코드 에디터 스타일

## 수용 기준 체크리스트

| 기준 | 상태 |
|------|------|
| 사용자가 케이스를 수동으로 관리 가능 | ✅ |
| 사용자가 스크립트를 수동으로 관리 가능 | ✅ |
| 케이스 상세에서 연결된 스크립트 직접 접근 | ✅ |
| 스크립트 상세에서 연결된 케이스 직접 접근 | ✅ |
| 다대다 매핑이 명시적이고 신뢰할 수 있음 | ✅ |
| 한/영/베 UI 동작 정의 및 구현 | ✅ |
| 실행 ID와 보고서 ID가 명시적 | ✅ |
| 이뮤터블 실행별 보고서 이력 존재 | ✅ |
| 실패 원인과 증거가 사용자에게 의미 있게 표시 | ✅ |

## 남은 작업 (Phase 4)

1. **콘텐츠 번역 API** — LLM 기반 분석 결과/케이스 번역
2. **커버리지 매트릭스 시각화** — Feature × Case 매트릭스 뷰
3. **실행 비교** — 두 실행 결과 비교 뷰
4. **보고서 차트** — 시각적 보고서 (pass rate 추이 등)
5. **알림/공유** — 보고서 URL 공유, 이메일 알림

## 기술 변경 사항

### 변경된 파일
- `src/testforge/web/routers/analysis.py` — Feature/Persona/Rule 개별 CRUD 추가
- `src/testforge/web/routers/cases.py` — 전면 재작성 (개별 CRUD, 벌크 삭제, 재생성 모드)
- `src/testforge/web/routers/scripts.py` — 전면 재작성 (CRUD, 매핑 API, 자동 매핑)
- `src/testforge/web/routers/execution.py` — 전면 재작성 (이뮤터블 실행 이력)
- `src/testforge/web/routers/reports.py` — 전면 재작성 (이뮤터블 보고서 이력)
- `src/testforge/web/static/index.html` — CRUD 버튼, 모달, 이력 테이블 추가
- `src/testforge/web/static/app.js` — CRUD 로직, 드릴다운, 이력 로딩 (~400줄 추가)
- `src/testforge/web/static/i18n.js` — 69키 × 3언어 추가
- `src/testforge/web/static/style.css` — CRUD UI 스타일 (~170줄 추가)

### 신규 데이터 파일
- `.testforge/mappings.json` — 권위적 케이스↔스크립트 매핑
- `output/run_{run_id}.json` — 이뮤터블 실행 기록
- `output/reports/report_{report_id}.md|html` — 이뮤터블 보고서
- `output/reports/report_{report_id}.meta.json` — 보고서 메타데이터
- `cases/cases_backup.json` — 재생성 시 백업

### 테스트 결과
- 기존 23개 웹 테스트 모두 통과
- FastAPI 앱 57개 라우트 정상 로드
