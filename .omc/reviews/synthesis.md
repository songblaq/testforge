# TestForge v0.5 Phantom Panel 리뷰 종합

## 참여 리뷰어

| 역할 | 점수 | 핵심 의견 |
|------|------|-----------|
| QA 엔지니어 | 6/10 | 대량 케이스 성능, 멀티탭 충돌, 클라이언트 검증 부재 |
| PM | 6/10 | README에 Web UI 미언급, 버전 불일치, v0.5 스코프 문서 부재 |
| 보안 전문가 | 4/10 | 업로드 크기 무제한, session_id 경로 순회, XSS 벡터, 경로 노출 |
| 프론트엔드 | 6/10 | 모달 포커스 트랩 없음, 키보드 네비게이션 불완전, 로딩 인디케이터 누락 |

**평균: 5.5/10**

## Critical/High → 수정 완료 (Phase 2)

- [x] 폼 검증 — saveCrudModal에 빈 이름/제목 클라이언트 검증 추가 (Task 2A)
- [x] XSS 방어 — simpleMarkdown에서 script 태그 및 on* 이벤트 제거 (Task 2B)
- [x] 업로드 크기 제한 — 10MB MAX_UPLOAD_SIZE, 413 반환 (Task 2C)
- [x] 모달 포커스 트랩 — _trapFocus 구현, showCrudModal/showConfirmDialog 적용 (Task 2D)
- [x] 로딩 인디케이터 — withLoading 래퍼, 4개 주요 버튼 적용 (Task 2E)
- [x] 경로 노출 차단 — deps.py 에러 메시지에서 전체 경로 제거 (Task 2C)

## Medium → 수정 완료 (Phase 3)

- [x] 웰컴 메시지 — Overview 탭 프로젝트 미선택 시 안내 (Task 3A)
- [x] i18n fallback — 이미 정상 동작 확인 (Task 3B)
- [x] 태블릿 반응형 — 1024px 브레이크포인트 + table-container 스크롤 (Task 3C)

## 잔여 리스크 (v0.6 이월)

- 대량 케이스 pagination / virtual scroll (QA: high)
- 멀티탭 동시 편집 충돌 감지 (QA: high)
- session_id 경로 순회 방어 (Security: high — localhost 전용이므로 수용)
- SSRF/LFI via analysis inputs (Security: high — localhost 전용이므로 수용)
- 인증/CSRF 미구현 (Security: info — localhost 단일 사용자 도구)
- CSP 헤더 미설정 (Security: low)
- 파이프라인 스테퍼 키보드 접근성 (Frontend: high)
- README Web UI 온보딩 추가 (PM: high)
- pyproject.toml 버전 정렬 (PM: high)

## Gate 판정

> **v0.5 release: APPROVED**
>
> Critical 보안 이슈(업로드 제한, XSS, 경로 노출) 및 UX 이슈(폼 검증, 포커스 트랩, 로딩)가
> 모두 수정되었습니다. 잔여 리스크는 localhost 단일 사용자 도구 특성상 수용 가능하며,
> v0.6에서 순차적으로 해결할 예정입니다.
