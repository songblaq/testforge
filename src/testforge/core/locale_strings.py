"""Centralized locale string maps for skeleton/fallback generation."""
from __future__ import annotations

from typing import Any

SKELETON_STRINGS: dict[str, dict[str, str]] = {
    "ko": {
        # Functional case skeletons
        "verify_feature": "{feature} 검증",
        "validate_feature": "{feature} 기능이 명세대로 동작하는지 확인: {description}",
        "system_accessible": "시스템에 접근 가능",
        "user_authenticated": "사용자가 인증됨",
        "navigate_to": "{feature} 기능으로 이동",
        "feature_displayed": "기능이 표시됨",
        "perform_primary": "주요 동작 수행",
        "expected_observed": "예상 동작이 관찰됨",
        "verify_result": "결과 확인",
        "result_matches": "결과가 명세와 일치",
        "functions_correctly": "{feature} 기능이 명세대로 정상 동작",

        # Use case skeletons
        "view_list": "{feature} 목록 보기",
        "view_detail": "{feature} 상세 보기",
        "edit_item": "{feature} 항목 편집",
        "delete_item": "{feature} 항목 삭제",
        "list_displayed": "목록/테이블이 항목들과 함께 표시되는지 확인",
        "item_shows_info": "각 항목이 주요 정보(ID, 이름, 상태)를 표시하는지 확인",
        "detail_shows_all": "상세 보기에 모든 필드가 표시되는지 확인 (요약뿐 아니라)",
        "back_navigation": "목록으로 돌아가는 네비게이션 확인",
        "updated_reflected": "수정된 데이터가 목록 및 상세 보기에 반영되는지 확인",
        "default_state": "시스템이 기본 상태",
        "has_existing_data": "{feature}에 기존 데이터가 존재",
        "navigate_section": "{feature} 섹션으로 이동",
        "select_item": "목록에서 항목 선택",
        "verify_detail_fields": "상세 정보의 모든 필드 확인",
        "click_edit": "편집 버튼 클릭",
        "modify_fields": "필드 값 수정",
        "save_changes": "변경사항 저장",
        "click_delete": "삭제 버튼 클릭",
        "confirm_delete": "삭제 확인",
        "item_removed": "항목이 목록에서 제거되었는지 확인",

        # Checklist skeletons
        "manual_check": "수동 점검: {feature}",
        "verify_manually": "{feature} 수동 검증: {description}",
        "navigate_area": "{feature} 영역으로 이동",
        "verify_ui": "모든 UI 요소가 올바르게 표시되는지 확인",
        "perform_action": "주요 동작을 수행하고 결과 관찰",
        "check_error_handling": "잘못된 입력으로 오류 처리 확인",
        "behaves_as_documented": "{feature} 기능이 문서대로 동작",

        # Script skeletons
        "todo_implement": "# TODO: 단계 동작 구현",
        "step_n": "단계 {n}",

        # Report headers
        "report_title": "TestForge 보고서",
        "summary": "요약",
        "coverage": "커버리지",
        "execution_info": "실행 정보",
        "test_results": "테스트 결과",
        "passed": "통과",
        "failed": "실패",
        "skipped": "건너뜀",
        "error": "오류",
        "total_tests": "전체 테스트",
        "pass_rate": "통과율",
        "duration": "실행 시간",
        "no_results": "테스트 결과가 없습니다.",
        "generated_by": "TestForge로 생성됨",
        "screenshots": "스크린샷",

        # Use case skeletons (generic)
        "uc_primary_workflow": "{persona} -- 주요 워크플로우",
        "uc_e2e_scenario": "{persona}의 엔드투엔드 시나리오",
        "uc_navigate_app": "{persona}로서 애플리케이션에 접속",
        "uc_interact_feature": "{feature} 기능과 상호작용",
        "uc_verify_final": "최종 상태가 기대와 일치하는지 확인",
        "uc_all_success": "모든 상호작용이 성공적으로 완료",
        "uc_crud_validation": "{feature} CRUD 흐름 검증",

        # Report coverage labels
        "features_covered": "기능 커버리지",
        "rules_covered": "규칙 커버리지",
        "uncovered_features": "미커버 기능",
        "uncovered_rules": "미커버 규칙",
        "evidence_gallery": "증거 갤러리",
        "status_passed": "통과",
        "status_failed": "실패",
        "status_skipped": "건너뜀",

        # TUI manual defaults
        "tui_init": "프로젝트 초기화 가능 여부 확인",
        "tui_analysis": "분석이 오류 없이 실행되는지 확인",
        "tui_cases_gen": "테스트 케이스가 생성되는지 확인",
        "tui_run": "테스트가 실행되고 결과가 반환되는지 확인",
        "tui_report": "보고서가 생성되는지 확인",
    },
    "en": {
        "verify_feature": "Verify {feature}",
        "validate_feature": "Validate that {feature} works as described: {description}",
        "system_accessible": "System is accessible",
        "user_authenticated": "User is authenticated",
        "navigate_to": "Navigate to {feature} feature",
        "feature_displayed": "Feature is displayed",
        "perform_primary": "Perform primary action",
        "expected_observed": "Expected behavior observed",
        "verify_result": "Verify result",
        "result_matches": "Result matches specification",
        "functions_correctly": "{feature} functions correctly as specified",

        "view_list": "View {feature} list",
        "view_detail": "View {feature} detail",
        "edit_item": "Edit {feature} item",
        "delete_item": "Delete {feature} item",
        "list_displayed": "Verify list/table is displayed with items",
        "item_shows_info": "Verify each item shows key information (ID, name, status)",
        "detail_shows_all": "Verify detail view shows ALL fields (not just summary)",
        "back_navigation": "Verify back/close navigation to return to list",
        "updated_reflected": "Verify updated data is reflected in list and detail views",
        "default_state": "System is in default state",
        "has_existing_data": "{feature} has existing data",
        "navigate_section": "Navigate to {feature} section",
        "select_item": "Select an item from the list",
        "verify_detail_fields": "Verify all detail fields",
        "click_edit": "Click edit button",
        "modify_fields": "Modify field values",
        "save_changes": "Save changes",
        "click_delete": "Click delete button",
        "confirm_delete": "Confirm deletion",
        "item_removed": "Verify item is removed from the list",

        "manual_check": "Manual check: {feature}",
        "verify_manually": "Verify {feature} manually: {description}",
        "navigate_area": "Navigate to the {feature} area",
        "verify_ui": "Verify all UI elements are displayed correctly",
        "perform_action": "Perform the primary action and observe results",
        "check_error_handling": "Check error handling with invalid input",
        "behaves_as_documented": "{feature} behaves as documented",

        "todo_implement": "# TODO: implement step action",
        "step_n": "Step {n}",

        "report_title": "TestForge Report",
        "summary": "Summary",
        "coverage": "Coverage",
        "execution_info": "Execution Info",
        "test_results": "Test Results",
        "passed": "Passed",
        "failed": "Failed",
        "skipped": "Skipped",
        "error": "Error",
        "total_tests": "Total Tests",
        "pass_rate": "Pass Rate",
        "duration": "Duration",
        "no_results": "No test results available.",
        "generated_by": "Generated by TestForge",
        "screenshots": "Screenshots",

        "uc_primary_workflow": "{persona} -- primary workflow",
        "uc_e2e_scenario": "End-to-end scenario for {persona}",
        "uc_navigate_app": "As {persona}, navigate to the application",
        "uc_interact_feature": "Interact with {feature}",
        "uc_verify_final": "Verify final state matches expectations",
        "uc_all_success": "All interactions complete successfully",
        "uc_crud_validation": "CRUD flow validation for {feature}",

        "features_covered": "Features Covered",
        "rules_covered": "Rules Covered",
        "uncovered_features": "Uncovered Features",
        "uncovered_rules": "Uncovered Rules",
        "evidence_gallery": "Evidence Gallery",
        "status_passed": "PASSED",
        "status_failed": "FAILED",
        "status_skipped": "SKIPPED",

        "tui_init": "Verify project can be initialized",
        "tui_analysis": "Verify analysis runs without errors",
        "tui_cases_gen": "Verify test cases are generated",
        "tui_run": "Verify tests run and results are returned",
        "tui_report": "Verify report is generated",
    },
}


def s(key: str, locale: str = "ko", **kwargs: Any) -> str:
    """Get a locale-aware skeleton string with parameter substitution.

    Falls back: locale -> en -> key.
    """
    primary = (locale or "ko").strip().split("-", 1)[0].lower()
    strings = SKELETON_STRINGS.get(primary, SKELETON_STRINGS.get("en", {}))
    template = strings.get(key, SKELETON_STRINGS["en"].get(key, key))
    try:
        return template.format(**kwargs) if kwargs else template
    except (KeyError, IndexError):
        return template
