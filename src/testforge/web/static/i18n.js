/* TestForge i18n -- lightweight translation system */

var translations = {
  en: {
    // Header
    "app.title": "TestForge",
    "project.select": "Select project...",
    "project.new": "+ New Project",

    // Context bar
    "ctx.docs": "{n} docs",
    "ctx.features": "{n} features",
    "ctx.cases": "{n} cases",
    "ctx.pipeline": "{n}/6 stages",

    // Tabs
    "tab.overview": "Overview",
    "tab.inputs": "Inputs",
    "tab.analysis": "Analysis",
    "tab.cases": "Cases",
    "tab.scripts": "Scripts",
    "tab.execution": "Execution",
    "tab.manual": "Manual QA",
    "tab.report": "Report",

    // Overview tab
    "overview.title": "Pipeline Overview",
    "overview.quickstats": "Quick Stats",
    "overview.next": "Next Step",
    "overview.all_done": "All pipeline stages complete!",

    // LLM config panel
    "llm.config_title": "LLM Configuration",
    "llm.provider": "Provider",
    "llm.model": "Model",
    "llm.save": "Save",
    "llm.saved": "LLM configuration saved",
    "llm.test": "Test Connection",
    "llm.testing": "Testing connection...",

    // Pipeline stepper
    "stepper.inputs": "Inputs",
    "stepper.analysis": "Analysis",
    "stepper.cases": "Cases",
    "stepper.scripts": "Scripts",
    "stepper.execution": "Execution",
    "stepper.report": "Report",
    "stepper.done": "Done",
    "stepper.ready": "Ready",
    "stepper.waiting": "Waiting",
    "stepper.docs": "{n} docs",
    "stepper.features": "{n} features",
    "stepper.cases_count": "{n} cases",
    "stepper.scripts": "{n} scripts",
    "stepper.runs": "{n} runs",
    "stepper.no_data": "-",

    // Inputs tab
    "inputs.title": "Input Documents",
    "inputs.upload": "+ Upload",
    "inputs.drop": "Drop files here or click Upload",
    "inputs.formats": "Supports: .md, .txt, .pdf, .docx, .pptx, .xlsx, .yaml, .json, images",
    "inputs.analyze": "\u2192 Run Analysis with these documents",
    "inputs.empty": "No input files",
    "inputs.empty.desc": "Upload documents to start the QA pipeline.",
    "inputs.download": "Download",
    "inputs.preview_unavailable": "Preview not available for this file type. Please download.",
    "inputs.confirm_delete": "Delete \"{name}\"? This cannot be undone.",

    // Analysis tab
    "analysis.title": "Analysis Results",
    "analysis.run": "Run Analysis",
    "analysis.guard": "Upload documents in the Inputs tab first before running analysis.",
    "analysis.empty": "No analysis results",
    "analysis.empty.desc": "Run analysis to extract features, personas, and business rules from your documents.",
    "analysis.features": "Features",
    "analysis.personas": "Personas",
    "analysis.rules": "Business Rules",
    "analysis.summary.features": "Features",
    "analysis.summary.personas": "Personas",
    "analysis.summary.rules": "Rules",
    "analysis.summary.high": "High: {n}",
    "analysis.summary.medium": "Med: {n}",
    "analysis.summary.low": "Low: {n}",

    // Cases tab
    "cases.title": "Test Cases",
    "cases.generate": "Generate Cases",
    "cases.guard": "Run analysis first in the Analysis tab before generating test cases.",
    "cases.empty": "No test cases",
    "cases.empty.desc": "Generate test cases after running analysis.",
    "cases.filter": "Filter cases...",
    "cases.all": "All Types",
    "cases.functional": "Functional",
    "cases.usecase": "Use Case",
    "cases.checklist": "Checklist",
    "cases.crud": "CRUD",
    "cases.all_tags": "All Tags",
    "cases.positive": "Positive",
    "cases.negative": "Negative",
    "cases.edge": "Edge",
    "cases.smoke": "Smoke",
    "cases.regression": "Regression",

    // Scripts tab
    "scripts.title": "Test Scripts",
    "scripts.generate": "Generate Scripts",
    "scripts.guard": "Generate test cases first in the Cases tab before generating scripts.",
    "scripts.empty": "No scripts generated",
    "scripts.empty.desc": "Generate Playwright test scripts from your test cases.",
    "scripts.summary.total": "Scripts",
    "scripts.summary.lines": "Total Lines",
    "scripts.summary.size": "Total Size",
    "scripts.copy": "Copy",
    "scripts.copied": "Copied!",

    // Execution tab
    "exec.title": "Test Execution",
    "exec.run": "Run Tests",
    "exec.guard": "Generate scripts first in the Scripts tab before running tests.",
    "exec.empty": "No test runs yet",
    "exec.empty.desc": "Execute test scripts and see results here.",
    "exec.total": "Total",
    "exec.passed": "Passed",
    "exec.failed": "Failed",

    // Manual QA tab
    "manual.title": "Manual QA Checklist",
    "manual.guard": "Generate test cases or run analysis first before starting a manual QA session.",
    "manual.start": "Start Session",
    "manual.finish": "Finish Session",
    "manual.empty": "No active session",
    "manual.empty.desc": "Start a manual QA session to work through the checklist.",
    "manual.items": "{checked} / {total} items checked",
    "manual.pass": "Pass",
    "manual.fail": "Fail",
    "manual.note": "Notes...",

    // Report tab
    "report.title": "Test Report",
    "report.load": "Load Report",
    "report.empty": "No report loaded",
    "report.empty.desc": "Generate a report after running tests.",
    "report.coverage": "Coverage",
    "report.feature_cov": "Feature Coverage",
    "report.rule_cov": "Rule Coverage",
    "report.download": "Download",
    "report.guard": "Run tests first in the Execution tab before viewing the report.",
    "report.exec_summary": "Executive Summary",
    "report.total_cases": "Total Cases",
    "report.pass_rate": "Pass Rate",
    "report.last_run": "Last Run",

    // Guard CTA buttons
    "guard.goto_inputs": "Go to Inputs \u2192",
    "guard.goto_analysis": "Go to Analysis \u2192",
    "guard.goto_cases": "Go to Cases \u2192",
    "guard.goto_scripts": "Go to Scripts \u2192",
    "guard.goto_execution": "Go to Execution \u2192",

    // Tab bottom CTA
    "cta.next_analysis": "\u2192 Next: Run Analysis",
    "cta.next_cases": "\u2192 Next: Generate Cases",
    "cta.next_scripts": "\u2192 Next: Generate Scripts",
    "cta.next_execution": "\u2192 Next: Run Tests",
    "cta.next_report": "\u2192 Next: View Report",
    "cta.done_inputs": "Documents uploaded.",
    "cta.done_analysis": "Analysis complete.",
    "cta.done_cases": "Cases generated.",
    "cta.done_scripts": "Scripts generated.",
    "cta.done_execution": "Tests complete.",
    "cta.done_manual": "Session complete.",

    // Modal
    "modal.title": "New Project",
    "modal.name": "Project Name",
    "modal.dir": "Directory",
    "modal.provider": "LLM Provider",
    "modal.model": "Model (optional)",
    "modal.cancel": "Cancel",
    "modal.create": "Create",

    // Project list
    "projects.title": "Projects",
    "projects.scan": "Scan",
    "projects.empty": "No projects found",
    "projects.empty.desc": "Create a new project or check the directory path.",
    "projects.open": "Open",
    "projects.docs": "{n} docs",
    "projects.failed": "Failed to load projects",
    "projects.retry": "Retry",
    "projects.none": "No projects",

    // Table headers
    "th.id": "ID",
    "th.name": "Name",
    "th.type": "Type",
    "th.tag": "Tag",
    "th.category": "Category",
    "th.priority": "Priority",
    "th.description": "Description",
    "th.tech_level": "Tech Level",
    "th.condition": "Condition",
    "th.expected": "Expected",
    "th.title": "Title",
    "th.feature": "Feature",
    "th.status": "Status",
    "th.file": "File",
    "th.size": "Size",
    "th.lines": "Lines",
    "th.case_id": "Case",
    "th.actions": "Actions",
    "th.case": "Case",
    "th.duration": "Duration",
    "th.output": "Output",

    // Badges
    "badge.analyzed": "Analyzed",
    "badge.cases": "Cases",
    "badge.scripts": "Scripts",
    "badge.report": "Report",
    "badge.new": "New",

    // Common
    "common.analyzing": "Analyzing...",
    "common.generating": "Generating...",
    "common.running": "Running...",
    "common.loading": "Loading...",
    "common.starting": "Starting...",
    "common.error": "Error",
    "common.success": "Success",
    "common.delete": "Delete",
    "common.retry": "Retry",
    "common.selected": "Selected: {name}",

    // Toast messages
    "toast.opened": "Opened: {name}",
    "toast.deleted": "Deleted: {name}",
    "toast.upload_error": "Upload error ({name}): {msg}",
    "toast.uploaded": "Uploaded {n} file(s)",
    "toast.analysis_complete": "Analysis complete",
    "toast.analysis_error": "Analysis error: {msg}",
    "toast.generated_cases": "Generated {n} cases",
    "toast.generation_error": "Generation error: {msg}",
    "toast.generated_scripts": "Generated {n} script(s)",
    "toast.script_error": "Script generation error: {msg}",
    "toast.tests_complete": "Tests complete",
    "toast.execution_error": "Execution error: {msg}",
    "toast.manual_started": "Manual QA session started",
    "toast.manual_start_error": "Error starting session: {msg}",
    "toast.manual_finished": "Manual QA session finished. Report: {path}",
    "toast.manual_finish_error": "Error finishing session: {msg}",
    "toast.manual_check_error": "Error checking item: {msg}",
    "toast.report_loaded": "Report loaded",
    "toast.report_error": "Report error: {msg}",
    "toast.project_created": "Project created: {name}",
    "toast.project_error": "Error: {msg}",
    "toast.load_error": "Error loading projects: {msg}",
    "toast.delete_error": "Delete error: {msg}",
    "toast.select_project": "Select a project first",
    "toast.name_required": "Project name is required",
    "toast.timeout": "Request timed out after 30s",
    "toast.network_error": "Network error: {msg}",
    "toast.invalid_json": "Invalid JSON response (status {status})",

    // Detail panel
    "detail.close": "Close",
    "detail.preconditions": "Preconditions",
    "detail.steps": "Steps",
    "detail.step.action": "Action",
    "detail.step.expected": "Expected Result",
    "detail.step.input": "Input Data",
    "detail.expected": "Expected Result",
    "detail.tags": "Tags",
    "detail.rules": "Rule IDs",
    "detail.output": "Output",
    "detail.stderr": "Stderr",
    "detail.returncode": "Return Code",
    "detail.note": "Note",
    "detail.source": "Source",
    "detail.screens": "Screens",
    "detail.goals": "Goals",
    "detail.pain_points": "Pain Points",
    "detail.condition": "Condition",
    "detail.expected_behavior": "Expected Behavior",
    "detail.filename": "Filename",
    "detail.filesize": "Size",
    "detail.filetype": "Type",
    "detail.case_id": "Case ID",
    "detail.duration": "Duration",
    "detail.feature_id": "Feature ID",
    "detail.status": "Status",
    "detail.code": "Code",
    "detail.content": "Content",
    "detail.mapped_scripts": "Mapped Scripts",
    "detail.mapped_case": "Mapped Case",

    // CRUD
    "crud.add": "+ Add",
    "crud.add_case": "+ Add Case",
    "crud.edit": "Edit",
    "crud.delete": "Delete",
    "crud.save": "Save",
    "crud.cancel": "Cancel",
    "crud.confirm": "Confirm",
    "crud.confirm_delete": "Delete",
    "crud.confirm_delete_msg": "Are you sure you want to delete \"{name}\"? This cannot be undone.",
    "crud.confirm_regenerate": "This will overwrite existing data. Continue?",
    "crud.selected": "selected",
    "crud.bulk_delete": "Delete Selected",
    "crud.no_selection": "No items selected",

    // Generate/Regenerate
    "gen.generate": "Generate",
    "gen.regenerate": "Regenerate (overwrite)",
    "gen.new_version": "New Version",
    "gen.mode_title": "Generation Mode",
    "gen.mode_desc": "Choose how to handle existing data:",

    // Run history
    "exec.history": "Run History",
    "exec.run_id": "Run ID",
    "exec.no_runs": "No previous runs",
    "exec.view_run": "View",

    // Report history
    "report.history": "Report History",
    "report.report_id": "Report ID",
    "report.no_reports": "No previous reports",
    "report.view_report": "View",

    // Table headers (new)
    "th.run_id": "Run ID",
    "th.date": "Date",
    "th.total": "Total",
    "th.passed": "Passed",
    "th.failed": "Failed",
    "th.report_id": "Report ID",
    "th.format": "Format",
    "th.mapping": "Mapping",
    "th.mapping_source": "Source",

    // Drill-down
    "nav.goto_script": "Go to Script →",
    "nav.goto_case": "Go to Case →",
    "nav.goto_run": "Go to Run →",
    "nav.goto_report": "Go to Report →",

    // Form labels
    "form.title": "Title",
    "form.name": "Name",
    "form.description": "Description",
    "form.category": "Category",
    "form.priority": "Priority",
    "form.type": "Type",
    "form.tags": "Tags (comma separated)",
    "form.feature_id": "Feature ID",
    "form.preconditions": "Preconditions (one per line)",
    "form.expected_result": "Expected Result",
    "form.condition": "Condition",
    "form.expected_behavior": "Expected Behavior",
    "form.source": "Source",
    "form.tech_level": "Tech Level",
    "form.goals": "Goals (one per line)",
    "form.pain_points": "Pain Points (one per line)",
    "form.steps": "Steps",
    "form.steps_hint": "action | expected result, one per line",

    // Misc
    "scripts.count": "{n} script(s) generated",
    "coverage.pct": "{n}% coverage",
    "report.saved": "saved"
  },
  ko: {
    // Header
    "app.title": "TestForge",
    "project.select": "\ud504\ub85c\uc81d\ud2b8 \uc120\ud0dd...",
    "project.new": "+ \uc0c8 \ud504\ub85c\uc81d\ud2b8",

    // Context bar
    "ctx.docs": "{n}\uac1c \ubb38\uc11c",
    "ctx.features": "{n}\uac1c \uae30\ub2a5",
    "ctx.cases": "{n}\uac1c \ucf00\uc774\uc2a4",
    "ctx.pipeline": "{n}/6 \ub2e8\uacc4",

    // Tabs
    "tab.overview": "\uac1c\uc694",
    "tab.inputs": "\uc785\ub825 \ubb38\uc11c",
    "tab.analysis": "\ubd84\uc11d",
    "tab.cases": "\ud14c\uc2a4\ud2b8 \ucf00\uc774\uc2a4",
    "tab.scripts": "\uc2a4\ud06c\ub9bd\ud2b8",
    "tab.execution": "\uc2e4\ud589",
    "tab.manual": "\uc218\ub3d9 QA",
    "tab.report": "\ubcf4\uace0\uc11c",

    // Overview tab
    "overview.title": "\ud30c\uc774\ud504\ub77c\uc778 \uac1c\uc694",
    "overview.quickstats": "\ube60\ub978 \ud1b5\uacc4",
    "overview.next": "\ub2e4\uc74c \ub2e8\uacc4",
    "overview.all_done": "\ubaa8\ub4e0 \ud30c\uc774\ud504\ub77c\uc778 \ub2e8\uacc4 \uc644\ub8cc!",

    // LLM config panel
    "llm.config_title": "LLM \uc124\uc815",
    "llm.provider": "\ud504\ub85c\ubc14\uc774\ub354",
    "llm.model": "\ubaa8\ub378",
    "llm.save": "\uc800\uc7a5",
    "llm.saved": "LLM \uc124\uc815\uc774 \uc800\uc7a5\ub418\uc5c8\uc2b5\ub2c8\ub2e4",
    "llm.test": "\uc5f0\uacb0 \ud14c\uc2a4\ud2b8",
    "llm.testing": "\uc5f0\uacb0 \ud14c\uc2a4\ud2b8 \uc911...",

    // Pipeline stepper
    "stepper.inputs": "\uc785\ub825",
    "stepper.analysis": "\ubd84\uc11d",
    "stepper.cases": "\ucf00\uc774\uc2a4",
    "stepper.scripts": "\uc2a4\ud06c\ub9bd\ud2b8",
    "stepper.execution": "\uc2e4\ud589",
    "stepper.report": "\ubcf4\uace0\uc11c",
    "stepper.done": "\uc644\ub8cc",
    "stepper.ready": "\uc900\ube44\ub428",
    "stepper.waiting": "\ub300\uae30",
    "stepper.docs": "{n}\uac1c \ubb38\uc11c",
    "stepper.features": "{n}\uac1c \uae30\ub2a5",
    "stepper.cases_count": "{n}\uac1c \ucf00\uc774\uc2a4",
    "stepper.scripts": "{n}\uac1c \uc2a4\ud06c\ub9bd\ud2b8",
    "stepper.runs": "{n}\ud68c \uc2e4\ud589",
    "stepper.no_data": "-",

    // Inputs tab
    "inputs.title": "\uc785\ub825 \ubb38\uc11c",
    "inputs.upload": "+ \uc5c5\ub85c\ub4dc",
    "inputs.drop": "\ud30c\uc77c\uc744 \uc5ec\uae30\uc5d0 \ub4dc\ub798\uadf8\ud558\uac70\ub098 \uc5c5\ub85c\ub4dc\ub97c \ud074\ub9ad\ud558\uc138\uc694",
    "inputs.formats": "\uc9c0\uc6d0 \ud615\uc2dd: .md, .txt, .pdf, .docx, .pptx, .xlsx, .yaml, .json, \uc774\ubbf8\uc9c0",
    "inputs.analyze": "\u2192 \uc774 \ubb38\uc11c\ub85c \ubd84\uc11d \uc2e4\ud589",
    "inputs.empty": "\uc785\ub825 \ud30c\uc77c \uc5c6\uc74c",
    "inputs.empty.desc": "QA \ud30c\uc774\ud504\ub77c\uc778\uc744 \uc2dc\uc791\ud558\ub824\uba74 \ubb38\uc11c\ub97c \uc5c5\ub85c\ub4dc\ud558\uc138\uc694.",
    "inputs.download": "\ub2e4\uc6b4\ub85c\ub4dc",
    "inputs.preview_unavailable": "\uc774 \ud30c\uc77c \uc720\ud615\uc740 \ubbf8\ub9ac\ubcf4\uae30\uac00 \uc9c0\uc6d0\ub418\uc9c0 \uc54a\uc2b5\ub2c8\ub2e4. \ub2e4\uc6b4\ub85c\ub4dc\ud574 \uc8fc\uc138\uc694.",
    "inputs.confirm_delete": "\"{name}\" \ud30c\uc77c\uc744 \uc0ad\uc81c\ud558\uc2dc\uaca0\uc2b5\ub2c8\uae4c? \uc774 \uc791\uc5c5\uc740 \ub418\ub3cc\ub9b4 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4.",

    // Analysis tab
    "analysis.title": "\ubd84\uc11d \uacb0\uacfc",
    "analysis.run": "\ubd84\uc11d \uc2e4\ud589",
    "analysis.guard": "\ubd84\uc11d \uc804\uc5d0 \uc785\ub825 \ud0ed\uc5d0\uc11c \ubb38\uc11c\ub97c \uba3c\uc800 \uc5c5\ub85c\ub4dc\ud558\uc138\uc694.",
    "analysis.empty": "\ubd84\uc11d \uacb0\uacfc \uc5c6\uc74c",
    "analysis.empty.desc": "\ubd84\uc11d\uc744 \uc2e4\ud589\ud558\uc5ec \uae30\ub2a5, \ud398\ub974\uc18c\ub098, \ube44\uc988\ub2c8\uc2a4 \uaddc\uce59\uc744 \ucd94\ucd9c\ud558\uc138\uc694.",
    "analysis.features": "\uae30\ub2a5",
    "analysis.personas": "\ud398\ub974\uc18c\ub098",
    "analysis.rules": "\ube44\uc988\ub2c8\uc2a4 \uaddc\uce59",
    "analysis.summary.features": "\uae30\ub2a5",
    "analysis.summary.personas": "\ud398\ub974\uc18c\ub098",
    "analysis.summary.rules": "\uaddc\uce59",
    "analysis.summary.high": "\ub192\uc74c: {n}",
    "analysis.summary.medium": "\uc911\uac04: {n}",
    "analysis.summary.low": "\ub0ae\uc74c: {n}",

    // Cases tab
    "cases.title": "\ud14c\uc2a4\ud2b8 \ucf00\uc774\uc2a4",
    "cases.generate": "\ucf00\uc774\uc2a4 \uc0dd\uc131",
    "cases.guard": "\ud14c\uc2a4\ud2b8 \ucf00\uc774\uc2a4 \uc0dd\uc131 \uc804\uc5d0 \uba3c\uc800 \ubd84\uc11d\uc744 \uc2e4\ud589\ud558\uc138\uc694.",
    "cases.empty": "\ud14c\uc2a4\ud2b8 \ucf00\uc774\uc2a4 \uc5c6\uc74c",
    "cases.empty.desc": "\ubd84\uc11d \ud6c4 \ud14c\uc2a4\ud2b8 \ucf00\uc774\uc2a4\ub97c \uc0dd\uc131\ud558\uc138\uc694.",
    "cases.filter": "\ucf00\uc774\uc2a4 \uac80\uc0c9...",
    "cases.all": "\uc804\uccb4",
    "cases.functional": "\uae30\ub2a5 \ud14c\uc2a4\ud2b8",
    "cases.usecase": "\uc720\uc2a4\ucf00\uc774\uc2a4",
    "cases.checklist": "\uccb4\ud06c\ub9ac\uc2a4\ud2b8",
    "cases.crud": "CRUD",
    "cases.all_tags": "\uc804\uccb4 \ud0dc\uadf8",
    "cases.positive": "\uae0d\uc815",
    "cases.negative": "\ubd80\uc815",
    "cases.edge": "\uc5e3\uc9c0",
    "cases.smoke": "\uc2a4\ubaa8\ud06c",
    "cases.regression": "\ud68c\uadc0",

    // Scripts tab
    "scripts.title": "\ud14c\uc2a4\ud2b8 \uc2a4\ud06c\ub9bd\ud2b8",
    "scripts.generate": "\uc2a4\ud06c\ub9bd\ud2b8 \uc0dd\uc131",
    "scripts.guard": "\uc2a4\ud06c\ub9bd\ud2b8 \uc0dd\uc131 \uc804\uc5d0 \uba3c\uc800 \ud14c\uc2a4\ud2b8 \ucf00\uc774\uc2a4\ub97c \uc0dd\uc131\ud558\uc138\uc694.",
    "scripts.empty": "\uc0dd\uc131\ub41c \uc2a4\ud06c\ub9bd\ud2b8 \uc5c6\uc74c",
    "scripts.empty.desc": "\ud14c\uc2a4\ud2b8 \ucf00\uc774\uc2a4\ub85c\ubd80\ud130 Playwright \uc2a4\ud06c\ub9bd\ud2b8\ub97c \uc0dd\uc131\ud558\uc138\uc694.",
    "scripts.summary.total": "\uc2a4\ud06c\ub9bd\ud2b8",
    "scripts.summary.lines": "\ucd1d \uc904 \uc218",
    "scripts.summary.size": "\ucd1d \ud06c\uae30",
    "scripts.copy": "\ubcf5\uc0ac",
    "scripts.copied": "\ubcf5\uc0ac\ub428!",

    // Execution tab
    "exec.title": "\ud14c\uc2a4\ud2b8 \uc2e4\ud589",
    "exec.run": "\ud14c\uc2a4\ud2b8 \uc2e4\ud589",
    "exec.guard": "\ud14c\uc2a4\ud2b8 \uc2e4\ud589 \uc804\uc5d0 \uba3c\uc800 \uc2a4\ud06c\ub9bd\ud2b8\ub97c \uc0dd\uc131\ud558\uc138\uc694.",
    "exec.empty": "\uc2e4\ud589 \uae30\ub85d \uc5c6\uc74c",
    "exec.empty.desc": "\ud14c\uc2a4\ud2b8 \uc2a4\ud06c\ub9bd\ud2b8\ub97c \uc2e4\ud589\ud558\uace0 \uacb0\uacfc\ub97c \ud655\uc778\ud558\uc138\uc694.",
    "exec.total": "\uc804\uccb4",
    "exec.passed": "\ud1b5\uacfc",
    "exec.failed": "\uc2e4\ud328",

    // Manual QA tab
    "manual.title": "\uc218\ub3d9 QA \uccb4\ud06c\ub9ac\uc2a4\ud2b8",
    "manual.guard": "\uc218\ub3d9 QA \uc138\uc158\uc744 \uc2dc\uc791\ud558\ub824\uba74 \uba3c\uc800 \ud14c\uc2a4\ud2b8 \ucf00\uc774\uc2a4\ub97c \uc0dd\uc131\ud558\uac70\ub098 \ubd84\uc11d\uc744 \uc2e4\ud589\ud558\uc138\uc694.",
    "manual.start": "\uc138\uc158 \uc2dc\uc791",
    "manual.finish": "\uc138\uc158 \uc644\ub8cc",
    "manual.empty": "\ud65c\uc131 \uc138\uc158 \uc5c6\uc74c",
    "manual.empty.desc": "\uc218\ub3d9 QA \uc138\uc158\uc744 \uc2dc\uc791\ud558\uc5ec \uccb4\ud06c\ub9ac\uc2a4\ud2b8\ub97c \uc9c4\ud589\ud558\uc138\uc694.",
    "manual.items": "{checked} / {total}\uac1c \ud56d\ubaa9 \ud655\uc778\ub428",
    "manual.pass": "\ud1b5\uacfc",
    "manual.fail": "\uc2e4\ud328",
    "manual.note": "\uba54\ubaa8 \ucd94\uac00...",

    // Report tab
    "report.title": "\ud14c\uc2a4\ud2b8 \ubcf4\uace0\uc11c",
    "report.load": "\ubcf4\uace0\uc11c \ub85c\ub4dc",
    "report.empty": "\ub85c\ub4dc\ub41c \ubcf4\uace0\uc11c \uc5c6\uc74c",
    "report.empty.desc": "\ud14c\uc2a4\ud2b8 \uc2e4\ud589 \ud6c4 \ubcf4\uace0\uc11c\ub97c \uc0dd\uc131\ud558\uc138\uc694.",
    "report.coverage": "\ucee4\ubc84\ub9ac\uc9c0",
    "report.feature_cov": "\uae30\ub2a5 \ucee4\ubc84\ub9ac\uc9c0",
    "report.rule_cov": "\uaddc\uce59 \ucee4\ubc84\ub9ac\uc9c0",
    "report.download": "\ub2e4\uc6b4\ub85c\ub4dc",
    "report.guard": "\ubcf4\uace0\uc11c\ub97c \ubcf4\ub824\uba74 \uba3c\uc800 \uc2e4\ud589 \ud0ed\uc5d0\uc11c \ud14c\uc2a4\ud2b8\ub97c \uc2e4\ud589\ud558\uc138\uc694.",
    "report.exec_summary": "\uc694\uc57d",
    "report.total_cases": "\uc804\uccb4 \ucf00\uc774\uc2a4",
    "report.pass_rate": "\ud1b5\uacfc\uc728",
    "report.last_run": "\ub9c8\uc9c0\ub9c9 \uc2e4\ud589",

    // Guard CTA buttons
    "guard.goto_inputs": "\uc785\ub825 \ud0ed\uc73c\ub85c \uc774\ub3d9 \u2192",
    "guard.goto_analysis": "\ubd84\uc11d \ud0ed\uc73c\ub85c \uc774\ub3d9 \u2192",
    "guard.goto_cases": "\ucf00\uc774\uc2a4 \ud0ed\uc73c\ub85c \uc774\ub3d9 \u2192",
    "guard.goto_scripts": "\uc2a4\ud06c\ub9bd\ud2b8 \ud0ed\uc73c\ub85c \uc774\ub3d9 \u2192",
    "guard.goto_execution": "\uc2e4\ud589 \ud0ed\uc73c\ub85c \uc774\ub3d9 \u2192",

    // Tab bottom CTA
    "cta.next_analysis": "\u2192 \ub2e4\uc74c: \ubd84\uc11d \uc2e4\ud589",
    "cta.next_cases": "\u2192 \ub2e4\uc74c: \ucf00\uc774\uc2a4 \uc0dd\uc131",
    "cta.next_scripts": "\u2192 \ub2e4\uc74c: \uc2a4\ud06c\ub9bd\ud2b8 \uc0dd\uc131",
    "cta.next_execution": "\u2192 \ub2e4\uc74c: \ud14c\uc2a4\ud2b8 \uc2e4\ud589",
    "cta.next_report": "\u2192 \ub2e4\uc74c: \ubcf4\uace0\uc11c \ubcf4\uae30",
    "cta.done_inputs": "\ubb38\uc11c \uc5c5\ub85c\ub4dc \uc644\ub8cc.",
    "cta.done_analysis": "\ubd84\uc11d \uc644\ub8cc.",
    "cta.done_cases": "\ucf00\uc774\uc2a4 \uc0dd\uc131 \uc644\ub8cc.",
    "cta.done_scripts": "\uc2a4\ud06c\ub9bd\ud2b8 \uc0dd\uc131 \uc644\ub8cc.",
    "cta.done_execution": "\ud14c\uc2a4\ud2b8 \uc2e4\ud589 \uc644\ub8cc.",
    "cta.done_manual": "\uc138\uc158 \uc644\ub8cc.",

    // Modal
    "modal.title": "\uc0c8 \ud504\ub85c\uc81d\ud2b8",
    "modal.name": "\ud504\ub85c\uc81d\ud2b8 \uc774\ub984",
    "modal.dir": "\ub514\ub809\ud1a0\ub9ac",
    "modal.provider": "LLM \uc81c\uacf5\uc790",
    "modal.model": "\ubaa8\ub378 (\uc120\ud0dd\uc0ac\ud56d)",
    "modal.cancel": "\ucde8\uc18c",
    "modal.create": "\uc0dd\uc131",

    // Project list
    "projects.title": "\ud504\ub85c\uc81d\ud2b8",
    "projects.scan": "\uc2a4\uce94",
    "projects.empty": "\ud504\ub85c\uc81d\ud2b8\ub97c \ucc3e\uc744 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4",
    "projects.empty.desc": "\uc0c8 \ud504\ub85c\uc81d\ud2b8\ub97c \ub9cc\ub4e4\uac70\ub098 \ub514\ub809\ud1a0\ub9ac \uacbd\ub85c\ub97c \ud655\uc778\ud558\uc138\uc694.",
    "projects.open": "\uc5f4\uae30",
    "projects.docs": "{n}\uac1c \ubb38\uc11c",
    "projects.failed": "\ud504\ub85c\uc81d\ud2b8 \ub85c\ub4dc \uc2e4\ud328",
    "projects.retry": "\uc7ac\uc2dc\ub3c4",
    "projects.none": "\ud504\ub85c\uc81d\ud2b8 \uc5c6\uc74c",

    // Table headers
    "th.id": "ID",
    "th.name": "\uc774\ub984",
    "th.type": "\uc720\ud615",
    "th.tag": "\ud0dc\uadf8",
    "th.category": "\uce74\ud14c\uace0\ub9ac",
    "th.priority": "\uc6b0\uc120\uc21c\uc704",
    "th.description": "\uc124\uba85",
    "th.tech_level": "\uae30\uc220 \uc218\uc900",
    "th.condition": "\uc870\uac74",
    "th.expected": "\uae30\ub300 \ub3d9\uc791",
    "th.title": "\uc81c\ubaa9",
    "th.feature": "\uae30\ub2a5",
    "th.status": "\uc0c1\ud0dc",
    "th.file": "\ud30c\uc77c",
    "th.size": "\ud06c\uae30",
    "th.lines": "\uc904 \uc218",
    "th.case_id": "\ucf00\uc774\uc2a4",
    "th.actions": "\uc791\uc5c5",
    "th.case": "\ucf00\uc774\uc2a4",
    "th.duration": "\uc18c\uc694\uc2dc\uac04",
    "th.output": "\ucd9c\ub825",

    // Badges
    "badge.analyzed": "\ubd84\uc11d \uc644\ub8cc",
    "badge.cases": "\ucf00\uc774\uc2a4",
    "badge.scripts": "\uc2a4\ud06c\ub9bd\ud2b8",
    "badge.report": "\ubcf4\uace0\uc11c",
    "badge.new": "\uc0c8\ub85c\uc6b4",

    // Common
    "common.analyzing": "\ubd84\uc11d \uc911...",
    "common.generating": "\uc0dd\uc131 \uc911...",
    "common.running": "\uc2e4\ud589 \uc911...",
    "common.loading": "\ub85c\ub529 \uc911...",
    "common.starting": "\uc2dc\uc791 \uc911...",
    "common.error": "\uc624\ub958",
    "common.success": "\uc131\uacf5",
    "common.delete": "\uc0ad\uc81c",
    "common.retry": "\uc7ac\uc2dc\ub3c4",
    "common.selected": "{name} \uc120\ud0dd\ub428",

    // Toast messages
    "toast.opened": "{name} \uc5f4\ub9bc",
    "toast.deleted": "{name} \uc0ad\uc81c\ub428",
    "toast.upload_error": "\uc5c5\ub85c\ub4dc \uc624\ub958 ({name}): {msg}",
    "toast.uploaded": "{n}\uac1c \ud30c\uc77c \uc5c5\ub85c\ub4dc \uc644\ub8cc",
    "toast.analysis_complete": "\ubd84\uc11d \uc644\ub8cc",
    "toast.analysis_error": "\ubd84\uc11d \uc624\ub958: {msg}",
    "toast.generated_cases": "{n}\uac1c \ucf00\uc774\uc2a4 \uc0dd\uc131\ub428",
    "toast.generation_error": "\uc0dd\uc131 \uc624\ub958: {msg}",
    "toast.generated_scripts": "{n}\uac1c \uc2a4\ud06c\ub9bd\ud2b8 \uc0dd\uc131\ub428",
    "toast.script_error": "\uc2a4\ud06c\ub9bd\ud2b8 \uc0dd\uc131 \uc624\ub958: {msg}",
    "toast.tests_complete": "\ud14c\uc2a4\ud2b8 \uc644\ub8cc",
    "toast.execution_error": "\uc2e4\ud589 \uc624\ub958: {msg}",
    "toast.manual_started": "\uc218\ub3d9 QA \uc138\uc158 \uc2dc\uc791\ub428",
    "toast.manual_start_error": "\uc138\uc158 \uc2dc\uc791 \uc624\ub958: {msg}",
    "toast.manual_finished": "\uc218\ub3d9 QA \uc138\uc158 \uc644\ub8cc. \ubcf4\uace0\uc11c: {path}",
    "toast.manual_finish_error": "\uc138\uc158 \uc885\ub8cc \uc624\ub958: {msg}",
    "toast.manual_check_error": "\ud56d\ubaa9 \ud655\uc778 \uc624\ub958: {msg}",
    "toast.report_loaded": "\ubcf4\uace0\uc11c \ub85c\ub4dc\ub428",
    "toast.report_error": "\ubcf4\uace0\uc11c \uc624\ub958: {msg}",
    "toast.project_created": "\ud504\ub85c\uc81d\ud2b8 \uc0dd\uc131\ub428: {name}",
    "toast.project_error": "\uc624\ub958: {msg}",
    "toast.load_error": "\ud504\ub85c\uc81d\ud2b8 \ub85c\ub4dc \uc624\ub958: {msg}",
    "toast.delete_error": "\uc0ad\uc81c \uc624\ub958: {msg}",
    "toast.select_project": "\uba3c\uc800 \ud504\ub85c\uc81d\ud2b8\ub97c \uc120\ud0dd\ud558\uc138\uc694",
    "toast.name_required": "\ud504\ub85c\uc81d\ud2b8 \uc774\ub984\uc740 \ud544\uc218\uc785\ub2c8\ub2e4",
    "toast.timeout": "30\ucd08 \ud6c4 \uc694\uccad \uc2dc\uac04 \ucd08\uacfc",
    "toast.network_error": "\ub124\ud2b8\uc6cc\ud06c \uc624\ub958: {msg}",
    "toast.invalid_json": "\uc798\ubabb\ub41c JSON \uc751\ub2f5 (\uc0c1\ud0dc {status})",

    // Detail panel
    "detail.close": "\ub2eb\uae30",
    "detail.preconditions": "\uc0ac\uc804 \uc870\uac74",
    "detail.steps": "\ub2e8\uacc4",
    "detail.step.action": "\uc561\uc158",
    "detail.step.expected": "\uae30\ub300 \uacb0\uacfc",
    "detail.step.input": "\uc785\ub825 \ub370\uc774\ud130",
    "detail.expected": "\uae30\ub300 \uacb0\uacfc",
    "detail.tags": "\ud0dc\uadf8",
    "detail.rules": "\uad00\ub828 \uaddc\uce59",
    "detail.output": "\ucd9c\ub825",
    "detail.stderr": "\ud45c\uc900 \uc624\ub958",
    "detail.returncode": "\uc885\ub8cc \ucf54\ub4dc",
    "detail.note": "\uba54\ubaa8",
    "detail.source": "\ucd9c\ucc98",
    "detail.screens": "\ud654\uba74",
    "detail.goals": "\ubaa9\ud45c",
    "detail.pain_points": "\ubd88\ud3b8 \uc0ac\ud56d",
    "detail.condition": "\uc870\uac74",
    "detail.expected_behavior": "\uae30\ub300 \ub3d9\uc791",
    "detail.filename": "\ud30c\uc77c\uba85",
    "detail.filesize": "\ud06c\uae30",
    "detail.filetype": "\uc720\ud615",
    "detail.case_id": "\ucf00\uc774\uc2a4 ID",
    "detail.duration": "\uc18c\uc694\uc2dc\uac04",
    "detail.feature_id": "\uae30\ub2a5 ID",
    "detail.status": "\uc0c1\ud0dc",
    "detail.code": "\ucf54\ub4dc",
    "detail.content": "\ub0b4\uc6a9",
    "detail.mapped_scripts": "\ub9e4\ud551\ub41c \uc2a4\ud06c\ub9bd\ud2b8",
    "detail.mapped_case": "\ub9e4\ud551\ub41c \ucf00\uc774\uc2a4",

    // CRUD
    "crud.add": "+ \ucd94\uac00",
    "crud.add_case": "+ \ucf00\uc774\uc2a4 \ucd94\uac00",
    "crud.edit": "\ud3b8\uc9d1",
    "crud.delete": "\uc0ad\uc81c",
    "crud.save": "\uc800\uc7a5",
    "crud.cancel": "\ucde8\uc18c",
    "crud.confirm": "\ud655\uc778",
    "crud.confirm_delete": "\uc0ad\uc81c",
    "crud.confirm_delete_msg": "\"{name}\"\uc744(\ub97c) \uc0ad\uc81c\ud558\uc2dc\uaca0\uc2b5\ub2c8\uae4c? \uc774 \uc791\uc5c5\uc740 \ub418\ub3cc\ub9b4 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4.",
    "crud.confirm_regenerate": "\uae30\uc874 \ub370\uc774\ud130\ub97c \ub36e\uc5b4\uc501\ub2c8\ub2e4. \uacc4\uc18d\ud558\uc2dc\uaca0\uc2b5\ub2c8\uae4c?",
    "crud.selected": "\uac1c \uc120\ud0dd\ub428",
    "crud.bulk_delete": "\uc120\ud0dd \uc0ad\uc81c",
    "crud.no_selection": "\uc120\ud0dd\ub41c \ud56d\ubaa9\uc774 \uc5c6\uc2b5\ub2c8\ub2e4",

    // \uc0dd\uc131/\uc7ac\uc0dd\uc131
    "gen.generate": "\uc0dd\uc131",
    "gen.regenerate": "\uc7ac\uc0dd\uc131 (\ub36e\uc5b4\uc4f0\uae30)",
    "gen.new_version": "\uc0c8 \ubc84\uc804 \uc0dd\uc131",
    "gen.mode_title": "\uc0dd\uc131 \ubaa8\ub4dc",
    "gen.mode_desc": "\uae30\uc874 \ub370\uc774\ud130 \ucc98\ub9ac \ubc29\ubc95\uc744 \uc120\ud0dd\ud558\uc138\uc694:",

    // \uc2e4\ud589 \uc774\ub825
    "exec.history": "\uc2e4\ud589 \uc774\ub825",
    "exec.run_id": "\uc2e4\ud589 ID",
    "exec.no_runs": "\uc774\uc804 \uc2e4\ud589 \uae30\ub85d \uc5c6\uc74c",
    "exec.view_run": "\ubcf4\uae30",

    // \ubcf4\uace0\uc11c \uc774\ub825
    "report.history": "\ubcf4\uace0\uc11c \uc774\ub825",
    "report.report_id": "\ubcf4\uace0\uc11c ID",
    "report.no_reports": "\uc774\uc804 \ubcf4\uace0\uc11c \uc5c6\uc74c",
    "report.view_report": "\ubcf4\uae30",

    // \ud14c\uc774\ube14 \ud5e4\ub354 (\uc2e0\uaddc)
    "th.run_id": "\uc2e4\ud589 ID",
    "th.date": "\ub0a0\uc9dc",
    "th.total": "\uc804\uccb4",
    "th.passed": "\ud1b5\uacfc",
    "th.failed": "\uc2e4\ud328",
    "th.report_id": "\ubcf4\uace0\uc11c ID",
    "th.format": "\ud615\uc2dd",
    "th.mapping": "\ub9e4\ud551",
    "th.mapping_source": "\ucd9c\ucc98",

    // \ub4dc\ub9b4\ub2e4\uc6b4
    "nav.goto_script": "\uc2a4\ud06c\ub9bd\ud2b8\ub85c \uc774\ub3d9 \u2192",
    "nav.goto_case": "\ucf00\uc774\uc2a4\ub85c \uc774\ub3d9 \u2192",
    "nav.goto_run": "\uc2e4\ud589\uc73c\ub85c \uc774\ub3d9 \u2192",
    "nav.goto_report": "\ubcf4\uace0\uc11c\ub85c \uc774\ub3d9 \u2192",

    // \ud3fc \ub808\uc774\ube14
    "form.title": "\uc81c\ubaa9",
    "form.name": "\uc774\ub984",
    "form.description": "\uc124\uba85",
    "form.category": "\uce74\ud14c\uace0\ub9ac",
    "form.priority": "\uc6b0\uc120\uc21c\uc704",
    "form.type": "\uc720\ud615",
    "form.tags": "\ud0dc\uadf8 (\uc27c\ud45c\ub85c \uad6c\ubd84)",
    "form.feature_id": "\uae30\ub2a5 ID",
    "form.preconditions": "\uc0ac\uc804 \uc870\uac74 (\uc904 \ub2e8\uc704)",
    "form.expected_result": "\uae30\ub300 \uacb0\uacfc",
    "form.condition": "\uc870\uac74",
    "form.expected_behavior": "\uae30\ub300 \ub3d9\uc791",
    "form.source": "\ucd9c\ucc98",
    "form.tech_level": "\uae30\uc220 \uc218\uc900",
    "form.goals": "\ubaa9\ud45c (\uc904 \ub2e8\uc704)",
    "form.pain_points": "\ubd88\ud3b8 \uc0ac\ud56d (\uc904 \ub2e8\uc704)",
    "form.steps": "\ud14c\uc2a4\ud2b8 \ub2e8\uacc4",
    "form.steps_hint": "\uc791\uc5c5 | \uae30\ub300 \uacb0\uacfc, \ud55c \uc904\uc5d0 \ud558\ub098\uc529",

    // Misc
    "scripts.count": "{n}\uac1c \uc2a4\ud06c\ub9bd\ud2b8 \uc0dd\uc131\ub428",
    "coverage.pct": "{n}% \ucee4\ubc84\ub9ac\uc9c0",
    "report.saved": "\uc800\uc7a5\ub428"
  },
  vi: {
    // Header
    "app.title": "TestForge",
    "project.select": "Ch\u1ECDn d\u1EF1 \u00E1n...",
    "project.new": "+ D\u1EF1 \u00E1n m\u1EDBi",

    // Context bar
    "ctx.docs": "{n} t\u00E0i li\u1EC7u",
    "ctx.features": "{n} t\u00EDnh n\u0103ng",
    "ctx.cases": "{n} tr\u01B0\u1EDDng h\u1EE3p",
    "ctx.pipeline": "{n}/6 giai \u0111o\u1EA1n",

    // Tabs
    "tab.overview": "T\u1ED5ng quan",
    "tab.inputs": "T\u00E0i li\u1EC7u",
    "tab.analysis": "Ph\u00E2n t\u00EDch",
    "tab.cases": "Tr\u01B0\u1EDDng h\u1EE3p",
    "tab.scripts": "K\u1ECBch b\u1EA3n",
    "tab.execution": "Th\u1EF1c thi",
    "tab.manual": "QA th\u1EE7 c\u00F4ng",
    "tab.report": "B\u00E1o c\u00E1o",

    // Overview tab
    "overview.title": "T\u1ED5ng quan quy tr\u00ECnh",
    "overview.quickstats": "Th\u1ED1ng k\u00EA nhanh",
    "overview.next": "B\u01B0\u1EDBc ti\u1EBFp theo",
    "overview.all_done": "T\u1EA5t c\u1EA3 giai \u0111o\u1EA1n \u0111\u00E3 ho\u00E0n th\u00E0nh!",

    // LLM config panel
    "llm.config_title": "C\u1EA5u h\u00ECnh LLM",
    "llm.provider": "Nh\u00E0 cung c\u1EA5p",
    "llm.model": "M\u00F4 h\u00ECnh",
    "llm.save": "L\u01B0u",
    "llm.saved": "\u0110\u00E3 l\u01B0u c\u1EA5u h\u00ECnh LLM",
    "llm.test": "Ki\u1EC3m tra k\u1EBFt n\u1ED1i",
    "llm.testing": "\u0110ang ki\u1EC3m tra...",

    // Pipeline stepper
    "stepper.inputs": "T\u00E0i li\u1EC7u",
    "stepper.analysis": "Ph\u00E2n t\u00EDch",
    "stepper.cases": "Tr\u01B0\u1EDDng h\u1EE3p",
    "stepper.scripts": "K\u1ECBch b\u1EA3n",
    "stepper.execution": "Th\u1EF1c thi",
    "stepper.report": "B\u00E1o c\u00E1o",
    "stepper.done": "Ho\u00E0n th\u00E0nh",
    "stepper.ready": "S\u1EB5n s\u00E0ng",
    "stepper.waiting": "Ch\u1EDD",
    "stepper.docs": "{n} t\u00E0i li\u1EC7u",
    "stepper.features": "{n} t\u00EDnh n\u0103ng",
    "stepper.cases_count": "{n} tr\u01B0\u1EDDng h\u1EE3p",
    "stepper.scripts": "{n} k\u1ECBch b\u1EA3n",
    "stepper.runs": "{n} l\u1EA7n ch\u1EA1y",
    "stepper.no_data": "-",

    // Inputs tab
    "inputs.title": "T\u00E0i li\u1EC7u \u0111\u1EA7u v\u00E0o",
    "inputs.upload": "+ T\u1EA3i l\u00EAn",
    "inputs.drop": "K\u00E9o th\u1EA3 t\u1EC7p v\u00E0o \u0111\u00E2y ho\u1EB7c nh\u1EA5n T\u1EA3i l\u00EAn",
    "inputs.formats": "H\u1ED7 tr\u1EE3: .md, .txt, .pdf, .docx, .pptx, .xlsx, .yaml, .json, h\u00ECnh \u1EA3nh",
    "inputs.analyze": "\u2192 Ch\u1EA1y ph\u00E2n t\u00EDch v\u1EDBi c\u00E1c t\u00E0i li\u1EC7u n\u00E0y",
    "inputs.empty": "Ch\u01B0a c\u00F3 t\u1EC7p \u0111\u1EA7u v\u00E0o",
    "inputs.empty.desc": "T\u1EA3i l\u00EAn t\u00E0i li\u1EC7u \u0111\u1EC3 b\u1EAFt \u0111\u1EA7u quy tr\u00ECnh QA.",
    "inputs.download": "T\u1EA3i xu\u1ED1ng",
    "inputs.preview_unavailable": "Kh\u00F4ng h\u1ED7 tr\u1EE3 xem tr\u01B0\u1EDBc lo\u1EA1i t\u1EC7p n\u00E0y. Vui l\u00F2ng t\u1EA3i xu\u1ED1ng.",
    "inputs.confirm_delete": "X\u00F3a \"{name}\"? Thao t\u00E1c n\u00E0y kh\u00F4ng th\u1EC3 ho\u00E0n t\u00E1c.",

    // Analysis tab
    "analysis.title": "K\u1EBFt qu\u1EA3 ph\u00E2n t\u00EDch",
    "analysis.run": "Ch\u1EA1y ph\u00E2n t\u00EDch",
    "analysis.guard": "Vui l\u00F2ng t\u1EA3i l\u00EAn t\u00E0i li\u1EC7u trong tab T\u00E0i li\u1EC7u tr\u01B0\u1EDBc khi ch\u1EA1y ph\u00E2n t\u00EDch.",
    "analysis.empty": "Ch\u01B0a c\u00F3 k\u1EBFt qu\u1EA3 ph\u00E2n t\u00EDch",
    "analysis.empty.desc": "Ch\u1EA1y ph\u00E2n t\u00EDch \u0111\u1EC3 tr\u00EDch xu\u1EA5t t\u00EDnh n\u0103ng, persona v\u00E0 quy t\u1EAFc nghi\u1EC7p v\u1EE5.",
    "analysis.features": "T\u00EDnh n\u0103ng",
    "analysis.personas": "Persona",
    "analysis.rules": "Quy t\u1EAFc nghi\u1EC7p v\u1EE5",
    "analysis.summary.features": "T\u00EDnh n\u0103ng",
    "analysis.summary.personas": "Persona",
    "analysis.summary.rules": "Quy t\u1EAFc",
    "analysis.summary.high": "Cao: {n}",
    "analysis.summary.medium": "TB: {n}",
    "analysis.summary.low": "Th\u1EA5p: {n}",

    // Cases tab
    "cases.title": "Tr\u01B0\u1EDDng h\u1EE3p ki\u1EC3m th\u1EED",
    "cases.generate": "T\u1EA1o tr\u01B0\u1EDDng h\u1EE3p",
    "cases.guard": "Vui l\u00F2ng ch\u1EA1y ph\u00E2n t\u00EDch trong tab Ph\u00E2n t\u00EDch tr\u01B0\u1EDBc khi t\u1EA1o tr\u01B0\u1EDDng h\u1EE3p ki\u1EC3m th\u1EED.",
    "cases.empty": "Ch\u01B0a c\u00F3 tr\u01B0\u1EDDng h\u1EE3p ki\u1EC3m th\u1EED",
    "cases.empty.desc": "T\u1EA1o tr\u01B0\u1EDDng h\u1EE3p ki\u1EC3m th\u1EED sau khi ch\u1EA1y ph\u00E2n t\u00EDch.",
    "cases.filter": "L\u1ECDc tr\u01B0\u1EDDng h\u1EE3p...",
    "cases.all": "T\u1EA5t c\u1EA3",
    "cases.functional": "Ch\u1EE9c n\u0103ng",
    "cases.usecase": "Use Case",
    "cases.checklist": "Danh s\u00E1ch ki\u1EC3m tra",
    "cases.crud": "CRUD",
    "cases.all_tags": "T\u1EA5t c\u1EA3 nh\u00E3n",
    "cases.positive": "T\u00EDch c\u1EF1c",
    "cases.negative": "Ti\u00EAu c\u1EF1c",
    "cases.edge": "Bi\u00EAn",
    "cases.smoke": "Smoke",
    "cases.regression": "H\u1ED3i quy",

    // Scripts tab
    "scripts.title": "K\u1ECBch b\u1EA3n ki\u1EC3m th\u1EED",
    "scripts.generate": "T\u1EA1o k\u1ECBch b\u1EA3n",
    "scripts.guard": "Vui l\u00F2ng t\u1EA1o tr\u01B0\u1EDDng h\u1EE3p ki\u1EC3m th\u1EED trong tab Tr\u01B0\u1EDDng h\u1EE3p tr\u01B0\u1EDBc khi t\u1EA1o k\u1ECBch b\u1EA3n.",
    "scripts.empty": "Ch\u01B0a c\u00F3 k\u1ECBch b\u1EA3n",
    "scripts.empty.desc": "T\u1EA1o k\u1ECBch b\u1EA3n Playwright t\u1EEB c\u00E1c tr\u01B0\u1EDDng h\u1EE3p ki\u1EC3m th\u1EED.",
    "scripts.summary.total": "K\u1ECBch b\u1EA3n",
    "scripts.summary.lines": "T\u1ED5ng s\u1ED1 d\u00F2ng",
    "scripts.summary.size": "T\u1ED5ng dung l\u01B0\u1EE3ng",
    "scripts.copy": "Sao ch\u00E9p",
    "scripts.copied": "\u0110\u00E3 sao ch\u00E9p!",

    // Execution tab
    "exec.title": "Th\u1EF1c thi ki\u1EC3m th\u1EED",
    "exec.run": "Ch\u1EA1y ki\u1EC3m th\u1EED",
    "exec.guard": "Vui l\u00F2ng t\u1EA1o k\u1ECBch b\u1EA3n trong tab K\u1ECBch b\u1EA3n tr\u01B0\u1EDBc khi ch\u1EA1y ki\u1EC3m th\u1EED.",
    "exec.empty": "Ch\u01B0a c\u00F3 l\u1EA7n ch\u1EA1y n\u00E0o",
    "exec.empty.desc": "Th\u1EF1c thi k\u1ECBch b\u1EA3n ki\u1EC3m th\u1EED v\u00E0 xem k\u1EBFt qu\u1EA3 t\u1EA1i \u0111\u00E2y.",
    "exec.total": "T\u1ED5ng",
    "exec.passed": "\u0110\u1EA1t",
    "exec.failed": "Kh\u00F4ng \u0111\u1EA1t",

    // Manual QA tab
    "manual.title": "Danh s\u00E1ch ki\u1EC3m tra QA th\u1EE7 c\u00F4ng",
    "manual.guard": "Vui l\u00F2ng t\u1EA1o tr\u01B0\u1EDDng h\u1EE3p ki\u1EC3m th\u1EED ho\u1EB7c ch\u1EA1y ph\u00E2n t\u00EDch tr\u01B0\u1EDBc khi b\u1EAFt \u0111\u1EA7u phi\u00EAn QA th\u1EE7 c\u00F4ng.",
    "manual.start": "B\u1EAFt \u0111\u1EA7u phi\u00EAn",
    "manual.finish": "K\u1EBFt th\u00FAc phi\u00EAn",
    "manual.empty": "Ch\u01B0a c\u00F3 phi\u00EAn n\u00E0o",
    "manual.empty.desc": "B\u1EAFt \u0111\u1EA7u phi\u00EAn QA th\u1EE7 c\u00F4ng \u0111\u1EC3 th\u1EF1c hi\u1EC7n danh s\u00E1ch ki\u1EC3m tra.",
    "manual.items": "{checked} / {total} m\u1EE5c \u0111\u00E3 ki\u1EC3m tra",
    "manual.pass": "\u0110\u1EA1t",
    "manual.fail": "Kh\u00F4ng \u0111\u1EA1t",
    "manual.note": "Ghi ch\u00FA...",

    // Report tab
    "report.title": "B\u00E1o c\u00E1o ki\u1EC3m th\u1EED",
    "report.load": "T\u1EA3i b\u00E1o c\u00E1o",
    "report.empty": "Ch\u01B0a c\u00F3 b\u00E1o c\u00E1o",
    "report.empty.desc": "T\u1EA1o b\u00E1o c\u00E1o sau khi ch\u1EA1y ki\u1EC3m th\u1EED.",
    "report.coverage": "\u0110\u1ED9 bao ph\u1EE7",
    "report.feature_cov": "\u0110\u1ED9 bao ph\u1EE7 t\u00EDnh n\u0103ng",
    "report.rule_cov": "\u0110\u1ED9 bao ph\u1EE7 quy t\u1EAFc",
    "report.download": "T\u1EA3i xu\u1ED1ng",
    "report.guard": "Vui l\u00F2ng ch\u1EA1y ki\u1EC3m th\u1EED trong tab Th\u1EF1c thi tr\u01B0\u1EDBc khi xem b\u00E1o c\u00E1o.",
    "report.exec_summary": "T\u00F3m t\u1EAFt",
    "report.total_cases": "T\u1ED5ng tr\u01B0\u1EDDng h\u1EE3p",
    "report.pass_rate": "T\u1EF7 l\u1EC7 \u0111\u1EA1t",
    "report.last_run": "L\u1EA7n ch\u1EA1y cu\u1ED1i",

    // Guard CTA buttons
    "guard.goto_inputs": "\u0110i \u0111\u1EBFn T\u00E0i li\u1EC7u \u2192",
    "guard.goto_analysis": "\u0110i \u0111\u1EBFn Ph\u00E2n t\u00EDch \u2192",
    "guard.goto_cases": "\u0110i \u0111\u1EBFn Tr\u01B0\u1EDDng h\u1EE3p \u2192",
    "guard.goto_scripts": "\u0110i \u0111\u1EBFn K\u1ECBch b\u1EA3n \u2192",
    "guard.goto_execution": "\u0110i \u0111\u1EBFn Th\u1EF1c thi \u2192",

    // Tab bottom CTA
    "cta.next_analysis": "\u2192 Ti\u1EBFp: Ch\u1EA1y ph\u00E2n t\u00EDch",
    "cta.next_cases": "\u2192 Ti\u1EBFp: T\u1EA1o tr\u01B0\u1EDDng h\u1EE3p",
    "cta.next_scripts": "\u2192 Ti\u1EBFp: T\u1EA1o k\u1ECBch b\u1EA3n",
    "cta.next_execution": "\u2192 Ti\u1EBFp: Ch\u1EA1y ki\u1EC3m th\u1EED",
    "cta.next_report": "\u2192 Ti\u1EBFp: Xem b\u00E1o c\u00E1o",
    "cta.done_inputs": "\u0110\u00E3 t\u1EA3i l\u00EAn t\u00E0i li\u1EC7u.",
    "cta.done_analysis": "Ph\u00E2n t\u00EDch ho\u00E0n t\u1EA5t.",
    "cta.done_cases": "\u0110\u00E3 t\u1EA1o tr\u01B0\u1EDDng h\u1EE3p.",
    "cta.done_scripts": "\u0110\u00E3 t\u1EA1o k\u1ECBch b\u1EA3n.",
    "cta.done_execution": "Ki\u1EC3m th\u1EED ho\u00E0n t\u1EA5t.",
    "cta.done_manual": "Phi\u00EAn ho\u00E0n t\u1EA5t.",

    // Modal
    "modal.title": "D\u1EF1 \u00E1n m\u1EDBi",
    "modal.name": "T\u00EAn d\u1EF1 \u00E1n",
    "modal.dir": "Th\u01B0 m\u1EE5c",
    "modal.provider": "Nh\u00E0 cung c\u1EA5p LLM",
    "modal.model": "M\u00F4 h\u00ECnh (t\u00F9y ch\u1ECDn)",
    "modal.cancel": "H\u1EE7y",
    "modal.create": "T\u1EA1o",

    // Project list
    "projects.title": "D\u1EF1 \u00E1n",
    "projects.scan": "Qu\u00E9t",
    "projects.empty": "Kh\u00F4ng t\u00ECm th\u1EA5y d\u1EF1 \u00E1n",
    "projects.empty.desc": "T\u1EA1o d\u1EF1 \u00E1n m\u1EDBi ho\u1EB7c ki\u1EC3m tra \u0111\u01B0\u1EDDng d\u1EABn th\u01B0 m\u1EE5c.",
    "projects.open": "M\u1EDF",
    "projects.docs": "{n} t\u00E0i li\u1EC7u",
    "projects.failed": "T\u1EA3i d\u1EF1 \u00E1n th\u1EA5t b\u1EA1i",
    "projects.retry": "Th\u1EED l\u1EA1i",
    "projects.none": "Kh\u00F4ng c\u00F3 d\u1EF1 \u00E1n",

    // Table headers
    "th.id": "ID",
    "th.name": "T\u00EAn",
    "th.type": "Lo\u1EA1i",
    "th.tag": "Nh\u00E3n",
    "th.category": "Danh m\u1EE5c",
    "th.priority": "\u0110\u1ED9 \u01B0u ti\u00EAn",
    "th.description": "M\u00F4 t\u1EA3",
    "th.tech_level": "Tr\u00ECnh \u0111\u1ED9 k\u1EF9 thu\u1EADt",
    "th.condition": "\u0110i\u1EC1u ki\u1EC7n",
    "th.expected": "K\u1EBFt qu\u1EA3 mong \u0111\u1EE3i",
    "th.title": "Ti\u00EAu \u0111\u1EC1",
    "th.feature": "T\u00EDnh n\u0103ng",
    "th.status": "Tr\u1EA1ng th\u00E1i",
    "th.file": "T\u1EC7p",
    "th.size": "Dung l\u01B0\u1EE3ng",
    "th.lines": "S\u1ED1 d\u00F2ng",
    "th.case_id": "Tr\u01B0\u1EDDng h\u1EE3p",
    "th.actions": "Thao t\u00E1c",
    "th.case": "Tr\u01B0\u1EDDng h\u1EE3p",
    "th.duration": "Th\u1EDDi gian",
    "th.output": "K\u1EBFt xu\u1EA5t",

    // Badges
    "badge.analyzed": "\u0110\u00E3 ph\u00E2n t\u00EDch",
    "badge.cases": "Tr\u01B0\u1EDDng h\u1EE3p",
    "badge.scripts": "K\u1ECBch b\u1EA3n",
    "badge.report": "B\u00E1o c\u00E1o",
    "badge.new": "M\u1EDBi",

    // Common
    "common.analyzing": "\u0110ang ph\u00E2n t\u00EDch...",
    "common.generating": "\u0110ang t\u1EA1o...",
    "common.running": "\u0110ang ch\u1EA1y...",
    "common.loading": "\u0110ang t\u1EA3i...",
    "common.starting": "\u0110ang kh\u1EDFi \u0111\u1ED9ng...",
    "common.error": "L\u1ED7i",
    "common.success": "Th\u00E0nh c\u00F4ng",
    "common.delete": "X\u00F3a",
    "common.retry": "Th\u1EED l\u1EA1i",
    "common.selected": "\u0110\u00E3 ch\u1ECDn: {name}",

    // Toast messages
    "toast.opened": "\u0110\u00E3 m\u1EDF: {name}",
    "toast.deleted": "\u0110\u00E3 x\u00F3a: {name}",
    "toast.upload_error": "L\u1ED7i t\u1EA3i l\u00EAn ({name}): {msg}",
    "toast.uploaded": "\u0110\u00E3 t\u1EA3i l\u00EAn {n} t\u1EC7p",
    "toast.analysis_complete": "Ph\u00E2n t\u00EDch ho\u00E0n t\u1EA5t",
    "toast.analysis_error": "L\u1ED7i ph\u00E2n t\u00EDch: {msg}",
    "toast.generated_cases": "\u0110\u00E3 t\u1EA1o {n} tr\u01B0\u1EDDng h\u1EE3p",
    "toast.generation_error": "L\u1ED7i t\u1EA1o: {msg}",
    "toast.generated_scripts": "\u0110\u00E3 t\u1EA1o {n} k\u1ECBch b\u1EA3n",
    "toast.script_error": "L\u1ED7i t\u1EA1o k\u1ECBch b\u1EA3n: {msg}",
    "toast.tests_complete": "Ki\u1EC3m th\u1EED ho\u00E0n t\u1EA5t",
    "toast.execution_error": "L\u1ED7i th\u1EF1c thi: {msg}",
    "toast.manual_started": "\u0110\u00E3 b\u1EAFt \u0111\u1EA7u phi\u00EAn QA th\u1EE7 c\u00F4ng",
    "toast.manual_start_error": "L\u1ED7i kh\u1EDFi \u0111\u1ED9ng phi\u00EAn: {msg}",
    "toast.manual_finished": "Phi\u00EAn QA th\u1EE7 c\u00F4ng ho\u00E0n t\u1EA5t. B\u00E1o c\u00E1o: {path}",
    "toast.manual_finish_error": "L\u1ED7i k\u1EBFt th\u00FAc phi\u00EAn: {msg}",
    "toast.manual_check_error": "L\u1ED7i ki\u1EC3m tra m\u1EE5c: {msg}",
    "toast.report_loaded": "\u0110\u00E3 t\u1EA3i b\u00E1o c\u00E1o",
    "toast.report_error": "L\u1ED7i b\u00E1o c\u00E1o: {msg}",
    "toast.project_created": "\u0110\u00E3 t\u1EA1o d\u1EF1 \u00E1n: {name}",
    "toast.project_error": "L\u1ED7i: {msg}",
    "toast.load_error": "L\u1ED7i t\u1EA3i d\u1EF1 \u00E1n: {msg}",
    "toast.delete_error": "L\u1ED7i x\u00F3a: {msg}",
    "toast.select_project": "Vui l\u00F2ng ch\u1ECDn d\u1EF1 \u00E1n tr\u01B0\u1EDBc",
    "toast.name_required": "T\u00EAn d\u1EF1 \u00E1n l\u00E0 b\u1EAFt bu\u1ED9c",
    "toast.timeout": "Y\u00EAu c\u1EA7u h\u1EBFt th\u1EDDi gian ch\u1EDD sau 30 gi\u00E2y",
    "toast.network_error": "L\u1ED7i m\u1EA1ng: {msg}",
    "toast.invalid_json": "Ph\u1EA3n h\u1ED3i JSON kh\u00F4ng h\u1EE3p l\u1EC7 (tr\u1EA1ng th\u00E1i {status})",

    // Detail panel
    "detail.close": "\u0110\u00F3ng",
    "detail.preconditions": "\u0110i\u1EC1u ki\u1EC7n ti\u00EAn quy\u1EBFt",
    "detail.steps": "C\u00E1c b\u01B0\u1EDBc",
    "detail.step.action": "H\u00E0nh \u0111\u1ED9ng",
    "detail.step.expected": "K\u1EBFt qu\u1EA3 mong \u0111\u1EE3i",
    "detail.step.input": "D\u1EEF li\u1EC7u \u0111\u1EA7u v\u00E0o",
    "detail.expected": "K\u1EBFt qu\u1EA3 mong \u0111\u1EE3i",
    "detail.tags": "Nh\u00E3n",
    "detail.rules": "Quy t\u1EAFc li\u00EAn quan",
    "detail.output": "K\u1EBFt xu\u1EA5t",
    "detail.stderr": "L\u1ED7i chu\u1EA9n",
    "detail.returncode": "M\u00E3 tr\u1EA3 v\u1EC1",
    "detail.note": "Ghi ch\u00FA",
    "detail.source": "Ngu\u1ED3n",
    "detail.screens": "M\u00E0n h\u00ECnh",
    "detail.goals": "M\u1EE5c ti\u00EAu",
    "detail.pain_points": "\u0110i\u1EC3m kh\u00F3 kh\u0103n",
    "detail.condition": "\u0110i\u1EC1u ki\u1EC7n",
    "detail.expected_behavior": "H\u00E0nh vi mong \u0111\u1EE3i",
    "detail.filename": "T\u00EAn t\u1EC7p",
    "detail.filesize": "Dung l\u01B0\u1EE3ng",
    "detail.filetype": "Lo\u1EA1i t\u1EC7p",
    "detail.case_id": "ID tr\u01B0\u1EDDng h\u1EE3p",
    "detail.duration": "Th\u1EDDi gian",
    "detail.feature_id": "ID t\u00EDnh n\u0103ng",
    "detail.status": "Tr\u1EA1ng th\u00E1i",
    "detail.code": "M\u00E3 ngu\u1ED3n",
    "detail.content": "N\u1ED9i dung",
    "detail.mapped_scripts": "K\u1ECBch b\u1EA3n li\u00EAn k\u1EBFt",
    "detail.mapped_case": "Tr\u01B0\u1EDDng h\u1EE3p li\u00EAn k\u1EBFt",

    // CRUD
    "crud.add": "+ Th\u00EAm",
    "crud.add_case": "+ Th\u00EAm tr\u01B0\u1EDDng h\u1EE3p",
    "crud.edit": "S\u1EEDa",
    "crud.delete": "X\u00F3a",
    "crud.save": "L\u01B0u",
    "crud.cancel": "H\u1EE7y",
    "crud.confirm": "X\u00E1c nh\u1EADn",
    "crud.confirm_delete": "X\u00F3a",
    "crud.confirm_delete_msg": "B\u1EA1n c\u00F3 ch\u1EAFc mu\u1ED1n x\u00F3a \"{name}\"? Thao t\u00E1c n\u00E0y kh\u00F4ng th\u1EC3 ho\u00E0n t\u00E1c.",
    "crud.confirm_regenerate": "D\u1EEF li\u1EC7u hi\u1EC7n t\u1EA1i s\u1EBD b\u1ECB ghi \u0111\u00E8. Ti\u1EBFp t\u1EE5c?",
    "crud.selected": "\u0111\u00E3 ch\u1ECDn",
    "crud.bulk_delete": "X\u00F3a \u0111\u00E3 ch\u1ECDn",
    "crud.no_selection": "Ch\u01B0a ch\u1ECDn m\u1EE5c n\u00E0o",

    "gen.generate": "T\u1EA1o",
    "gen.regenerate": "T\u1EA1o l\u1EA1i (ghi \u0111\u00E8)",
    "gen.new_version": "Phi\u00EAn b\u1EA3n m\u1EDBi",
    "gen.mode_title": "Ch\u1EBF \u0111\u1ED9 t\u1EA1o",
    "gen.mode_desc": "Ch\u1ECDn c\u00E1ch x\u1EED l\u00FD d\u1EEF li\u1EC7u hi\u1EC7n c\u00F3:",

    "exec.history": "L\u1ECBch s\u1EED ch\u1EA1y",
    "exec.run_id": "ID l\u1EA7n ch\u1EA1y",
    "exec.no_runs": "Ch\u01B0a c\u00F3 l\u1EA7n ch\u1EA1y n\u00E0o",
    "exec.view_run": "Xem",

    "report.history": "L\u1ECBch s\u1EED b\u00E1o c\u00E1o",
    "report.report_id": "ID b\u00E1o c\u00E1o",
    "report.no_reports": "Ch\u01B0a c\u00F3 b\u00E1o c\u00E1o n\u00E0o",
    "report.view_report": "Xem",

    "th.run_id": "ID l\u1EA7n ch\u1EA1y",
    "th.date": "Ng\u00E0y",
    "th.total": "T\u1ED5ng",
    "th.passed": "\u0110\u1EA1t",
    "th.failed": "Kh\u00F4ng \u0111\u1EA1t",
    "th.report_id": "ID b\u00E1o c\u00E1o",
    "th.format": "\u0110\u1ECBnh d\u1EA1ng",
    "th.mapping": "\u00C1nh x\u1EA1",
    "th.mapping_source": "Ngu\u1ED3n",

    "nav.goto_script": "\u0110i \u0111\u1EBFn k\u1ECBch b\u1EA3n \u2192",
    "nav.goto_case": "\u0110i \u0111\u1EBFn tr\u01B0\u1EDDng h\u1EE3p \u2192",
    "nav.goto_run": "\u0110i \u0111\u1EBFn l\u1EA7n ch\u1EA1y \u2192",
    "nav.goto_report": "\u0110i \u0111\u1EBFn b\u00E1o c\u00E1o \u2192",

    "form.title": "Ti\u00EAu \u0111\u1EC1",
    "form.name": "T\u00EAn",
    "form.description": "M\u00F4 t\u1EA3",
    "form.category": "Danh m\u1EE5c",
    "form.priority": "\u0110\u1ED9 \u01B0u ti\u00EAn",
    "form.type": "Lo\u1EA1i",
    "form.tags": "Nh\u00E3n (ph\u00E2n c\u00E1ch b\u1EB1ng d\u1EA5u ph\u1EA9y)",
    "form.feature_id": "ID t\u00EDnh n\u0103ng",
    "form.preconditions": "\u0110i\u1EC1u ki\u1EC7n ti\u00EAn quy\u1EBFt (m\u1ED7i d\u00F2ng m\u1ED9t)",
    "form.expected_result": "K\u1EBFt qu\u1EA3 mong \u0111\u1EE3i",
    "form.condition": "\u0110i\u1EC1u ki\u1EC7n",
    "form.expected_behavior": "H\u00E0nh vi mong \u0111\u1EE3i",
    "form.source": "Ngu\u1ED3n",
    "form.tech_level": "Tr\u00ECnh \u0111\u1ED9 k\u1EF9 thu\u1EADt",
    "form.goals": "M\u1EE5c ti\u00EAu (m\u1ED7i d\u00F2ng m\u1ED9t)",
    "form.pain_points": "\u0110i\u1EC3m kh\u00F3 kh\u0103n (m\u1ED7i d\u00F2ng m\u1ED9t)",
    "form.steps": "C\u00E1c b\u01B0\u1EDBc ki\u1EC3m th\u1EED",
    "form.steps_hint": "h\u00E0nh \u0111\u1ED9ng | k\u1EBFt qu\u1EA3 mong \u0111\u1EE3i, m\u1ED7i d\u00F2ng m\u1ED9t b\u01B0\u1EDBc",

    // Misc
    "scripts.count": "\u0110\u00E3 t\u1EA1o {n} k\u1ECBch b\u1EA3n",
    "coverage.pct": "\u0110\u1ED9 bao ph\u1EE7 {n}%",
    "report.saved": "\u0111\u00E3 l\u01B0u"
  }
};

function getLang() {
  try {
    var stored = localStorage.getItem("testforge-lang");
    if (stored && translations[stored]) return stored;
  } catch (e) { /* localStorage unavailable */ }
  // Detect from browser
  var nav = (typeof navigator !== "undefined" && navigator.language) || "en";
  var prefix = nav.split("-")[0].toLowerCase();
  if (translations[prefix]) return prefix;
  return "ko";
}

function setLang(lang) {
  if (!translations[lang]) lang = "en";
  try {
    localStorage.setItem("testforge-lang", lang);
  } catch (e) { /* localStorage unavailable */ }
  document.documentElement.lang = lang;
}

function t(key, params) {
  var lang = getLang();
  var text = (translations[lang] && translations[lang][key]) || translations.en[key] || key;
  if (params) {
    var keys = Object.keys(params);
    for (var i = 0; i < keys.length; i++) {
      text = text.replace("{" + keys[i] + "}", params[keys[i]]);
    }
  }
  return text;
}

function applyTranslations() {
  var elems = document.querySelectorAll("[data-i18n]");
  for (var i = 0; i < elems.length; i++) {
    var key = elems[i].getAttribute("data-i18n");
    if (key) {
      elems[i].textContent = t(key);
    }
  }
  // Also handle data-i18n-placeholder
  var placeholders = document.querySelectorAll("[data-i18n-placeholder]");
  for (var j = 0; j < placeholders.length; j++) {
    var pkey = placeholders[j].getAttribute("data-i18n-placeholder");
    if (pkey) {
      placeholders[j].placeholder = t(pkey);
    }
  }
}
