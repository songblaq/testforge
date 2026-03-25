"""FastAPI application factory -- registers routers and serves static files."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from testforge import __version__

STATIC_DIR = Path(__file__).parent / "static"


def create_app() -> FastAPI:
    """Build the FastAPI app with all routers and static serving."""
    app = FastAPI(
        title="TestForge",
        version=__version__,
        description="TestForge Web GUI -- manage projects, cases, and reports.",
    )

    # --- API routers ---
    from testforge.web.routers.projects import router as projects_router
    from testforge.web.routers.analysis import router as analysis_router
    from testforge.web.routers.cases import router as cases_router
    from testforge.web.routers.execution import router as execution_router
    from testforge.web.routers.reports import router as reports_router
    from testforge.web.routers.manual import router as manual_router
    from testforge.web.routers.scripts import router as scripts_router
    from testforge.web.routers.inputs import router as inputs_router
    from testforge.web.routers.inputs import delete_router as inputs_delete_router
    from testforge.web.routers.translate import router as translate_router

    app.include_router(analysis_router)
    app.include_router(cases_router)
    app.include_router(execution_router)
    app.include_router(reports_router)
    app.include_router(manual_router)
    app.include_router(scripts_router)
    app.include_router(inputs_router)
    app.include_router(inputs_delete_router)
    app.include_router(projects_router)
    app.include_router(translate_router)

    # --- Health + Config endpoints ---
    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": __version__}

    @app.get("/api/config")
    async def config():
        return {"version": __version__}

    # --- Error handlers ---
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc), "type": "validation_error"},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        import logging
        logging.getLogger("testforge.web").exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "type": "server_error"},
        )

    # --- Static files ---
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

        @app.get("/")
        async def index():
            index_path = STATIC_DIR / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))
            return {"message": "TestForge Web GUI -- static files not found"}

    return app
