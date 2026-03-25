"""Content translation endpoints.

# Multilingual Content Policy
# ============================================================
# TestForge v0.3 adopts the SOURCE + TRANSLATION JOB model:
#
#   1. Source artifact (e.g. cases.json, analysis.json) stores content in the
#      language the LLM generated it — typically Korean or English, depending
#      on the prompt language.
#
#   2. Translated versions are stored alongside as:
#      cases_ko.json, cases_en.json, cases_vi.json
#      (and similarly for analysis_ko.json etc.)
#
#   3. The UI language toggle NEVER overwrites existing source content.
#      It switches UI chrome only. Data content stays as-is unless
#      the operator explicitly requests a translation job.
#
#   4. Translation jobs are explicit, auditable, and reversible.
#      The original source artifact is never mutated by a translation job.
#
#   5. If a translated version already exists and was human-edited, the API
#      returns 409 CONFLICT with a "human_edited" flag — the caller must
#      explicitly pass force=true to overwrite.
#
# Current state: Translation jobs are stubbed (HTTP 501 Not Implemented).
# The policy contract above is in effect: no silent overwrites, ever.
# Full LLM-backed translation is deferred to v0.4.
# ============================================================
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from testforge.web.deps import resolve_project

router = APIRouter(prefix="/api/projects", tags=["translate"])

SUPPORTED_LANGS = ("ko", "en", "vi")


class TranslateRequest(BaseModel):
    target_lang: str
    entity_type: str  # "cases" | "analysis" | "all"
    force: bool = False  # overwrite even if human-edited version exists


@router.post("/{project_path:path}/translate")
async def request_translation(project_path: str, body: TranslateRequest):
    """Request translation of project content to target language.

    Policy:
    - Source artifact is never overwritten.
    - Translated version is saved as {entity}_{lang}.json.
    - If a human-edited translated version already exists, returns 409
      unless force=True is supplied.

    Current status: Stub — returns 501 Not Implemented.
    Full LLM-backed translation is planned for v0.4.
    """
    p = resolve_project(project_path)

    if body.target_lang not in SUPPORTED_LANGS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language '{body.target_lang}'. Supported: {SUPPORTED_LANGS}",
        )

    if body.entity_type not in ("cases", "analysis", "all"):
        raise HTTPException(
            status_code=400,
            detail="entity_type must be 'cases', 'analysis', or 'all'",
        )

    # Stub: check if translated version already exists to return correct status
    translated_paths = []
    if body.entity_type in ("cases", "all"):
        cases_translated = p / "cases" / f"cases_{body.target_lang}.json"
        translated_paths.append(("cases", cases_translated))
    if body.entity_type in ("analysis", "all"):
        analysis_translated = p / "analysis" / f"analysis_{body.target_lang}.json"
        translated_paths.append(("analysis", analysis_translated))

    existing = [(etype, str(path)) for etype, path in translated_paths if path.exists()]

    if existing and not body.force:
        return {
            "status": "conflict",
            "message": "Translated versions already exist. Pass force=true to overwrite.",
            "existing": existing,
            "human_edited": True,
        }

    # Policy contract response — full LLM translation deferred to v0.4
    raise HTTPException(
        status_code=501,
        detail={
            "message": "LLM-backed content translation is not yet implemented (planned for v0.4).",
            "policy": {
                "model": "source_plus_translation_job",
                "source_language": "preserved — never overwritten",
                "translation_storage": "{entity}_{lang}.json",
                "supported_languages": SUPPORTED_LANGS,
                "ui_language": "independent from content language",
            },
            "workaround": (
                "To translate content now: export the source artifact, "
                "translate externally, and re-import via the PUT endpoint."
            ),
        },
    )


@router.get("/{project_path:path}/translate/status")
async def get_translation_status(project_path: str):
    """Return translation status for all entities and supported languages."""
    p = resolve_project(project_path)

    status = {}
    for lang in SUPPORTED_LANGS:
        status[lang] = {
            "cases": (p / "cases" / f"cases_{lang}.json").exists(),
            "analysis": (p / "analysis" / f"analysis_{lang}.json").exists(),
        }

    return {
        "translation_policy": "source_plus_translation_job",
        "supported_languages": SUPPORTED_LANGS,
        "source_note": "Source artifacts (cases.json, analysis.json) are never overwritten by translation jobs.",
        "status": status,
    }
