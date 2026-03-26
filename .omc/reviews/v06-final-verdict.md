# TestForge v0.6 최종 판정

## 점수 변화

| 영역 | v0.5 | v0.6 | 변화 |
|------|------|------|------|
| 보안 | 4/10 | 7/10 | +3 |
| QA/에지케이스 | 6/10 | 7/10 | +1 |
| PM/문서 | 6/10 | 8/10 | +2 |
| 프론트엔드/접근성 | 6/10 | 8/10 | +2 |
| **평균** | **5.5** | **7.5** | **+2.0** |

## 보안 개선 상세 (4 → 7)
- Path traversal: manual.py session_id 정규식 + is_relative_to, projects.py directory/name 검증
- XSS: safeHref protocol-relative 차단, simpleMarkdown img alt 이스케이프, script/event 태그 제거
- SSRF/LFI: analysis inputs를 input_dir로 제한, url.py private IP 차단 + redirect 비활성화
- 잔여: list_projects 절대경로 허용 (localhost 맥락 수용), DNS rebinding (v0.7)

## QA/에지케이스 개선 (6 → 7)
- 클라이언트 폼 검증 추가 (빈 이름/제목 차단)
- 업로드 10MB 크기 제한 (413 반환)
- Cases pagination (50개 단위, 하위 호환)
- 보안 테스트 2개 추가 (업로드 제한, 경로 노출)

## PM/문서 개선 (6 → 8)
- pyproject.toml version 0.1.0 → 0.5.0, classifier Alpha → Beta
- README에 Web GUI 섹션 추가, CLI 명령 3개 추가 (web, research, coverage)
- CHANGELOG에 v0.3~v0.5 이력 추가, 부정확한 기능 주장 수정
- Ollama "coming" → "implemented" 반영

## 프론트엔드/접근성 개선 (6 → 8)
- 파이프라인 스테퍼: div → button (키보드 접근 가능)
- 모든 입력에 label 연결 (sr-only 포함)
- Create 모달 포커스 트랩 추가
- 에러 토스트 role="alert" + aria-live="assertive"
- 동적 영역 aria-live="polite"
- i18n: 중복 키 해결 (stepper.scripts_count), 338 keys x 3 languages 동기화
- 태블릿 반응형 (1024px), 테이블 가로 스크롤

## 테스트 결과
- API: 77/77 passed (test_web.py)
- CLI dogfood: 10/10 passed
- GUI dogfood: 28/28 passed
- 총: **284 passed, 4 skipped**

## Wave 실행 요약
| Wave | 에이전트 | 결과 |
|------|---------|------|
| 1 진단 | 8 | path-traversal 7건, XSS 6건, SSRF 3건, auth 29 endpoints, perf 5건, a11y 8건, docs 5/10, i18n 8/10 |
| 2 계획 | 3 | security-plan, ux-plan, docs-plan 작성 |
| 3 구현 | 6 | 경로순회 수정, XSS 수정, SSRF 방어, pagination, 접근성, 문서+버전 |
| 4 검증 | 5 | 보안 PASS, 테스트 PASS, 접근성 PASS, i18n PASS, 도그푸딩 PASS |
| 5 판정 | 1 | 이 문서 |

## 잔여 리스크 (v0.7 이월)
- 대량 케이스 가상 스크롤 (현재 pagination으로 완화)
- 멀티탭 동시 편집 충돌 감지 (ETag/If-Match)
- list_projects 절대경로 스캔 제한
- DNS rebinding 방어
- 인증/CSRF (localhost 단일 사용자 → 수용)
- CSP 헤더
- 스크립트/실행 이력 N+1 파일 I/O 최적화

## Gate 판정

> **v0.6 release: APPROVED**
>
> 평균 점수 5.5 → 7.5 (+2.0). 모든 Critical/High 보안 이슈 수정 완료.
> 284개 테스트 전체 통과. 문서 정합성 확보. 접근성 Level A 주요 위반 해소.
> 잔여 리스크는 localhost 단일 사용자 도구 맥락에서 수용 가능하며 v0.7에서 해결 예정.
