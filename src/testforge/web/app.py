"""FastAPI application factory -- registers routers and serves static files."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from testforge import __version__

STATIC_DIR = Path(__file__).parent / "static"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "connect-src 'self'; "
            "img-src 'self' data:; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response


def create_app() -> FastAPI:
    """Build the FastAPI app with all routers and static serving."""
    disable_docs = os.environ.get("TESTFORGE_DISABLE_DOCS", "").lower() in ("1", "true", "yes")
    app = FastAPI(
        title="TestForge",
        version=__version__,
        description="TestForge Web GUI -- manage projects, cases, and reports.",
        docs_url=None if disable_docs else "/docs",
        redoc_url=None if disable_docs else "/redoc",
        openapi_url=None if disable_docs else "/openapi.json",
    )

    import secrets as _secrets

    TESTFORGE_TOKEN = os.environ.get("TESTFORGE_TOKEN", "")

    _PUBLIC_PATHS = {"/api/health", "/api/config", "/", "/static"}

    @app.middleware("http")
    async def check_auth(request, call_next):
        if not TESTFORGE_TOKEN:
            return await call_next(request)

        path = request.url.path
        is_safe_read = request.method == "GET" and any(
            path == p or path.startswith(p + "/") for p in _PUBLIC_PATHS
        )
        if is_safe_read:
            return await call_next(request)

        is_mutating = request.method in ("POST", "PUT", "DELETE", "PATCH")
        if is_mutating:
            token = request.headers.get("X-TestForge-Token", "")
            if len(token) != len(TESTFORGE_TOKEN) or not _secrets.compare_digest(token, TESTFORGE_TOKEN):
                from starlette.responses import JSONResponse
                return JSONResponse({"detail": "Unauthorized"}, status_code=401)

        return await call_next(request)

    # --- API routers ---
    from testforge.web.routers.projects import router as projects_router
    from testforge.web.routers.analysis import router as analysis_router
    from testforge.web.routers.cases import router as cases_router
    from testforge.web.routers.execution import router as execution_router
    from testforge.web.routers.execution import engines_router
    from testforge.web.routers.reports import router as reports_router
    from testforge.web.routers.manual import router as manual_router
    from testforge.web.routers.scripts import router as scripts_router
    from testforge.web.routers.inputs import router as inputs_router
    from testforge.web.routers.inputs import delete_router as inputs_delete_router
    from testforge.web.routers.translate import router as translate_router

    app.include_router(analysis_router)
    app.include_router(cases_router)
    app.include_router(execution_router)
    app.include_router(engines_router)
    app.include_router(reports_router)
    app.include_router(manual_router)
    app.include_router(scripts_router)
    app.include_router(inputs_router)
    app.include_router(inputs_delete_router)
    app.include_router(projects_router)
    app.include_router(translate_router)

    app.add_middleware(SecurityHeadersMiddleware)

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
        safe_errors = []
        for err in exc.errors():
            safe_errors.append({
                "loc": err.get("loc", []),
                "msg": err.get("msg", "Validation error"),
                "type": err.get("type", ""),
            })
        return JSONResponse(
            status_code=422,
            content={"detail": safe_errors, "type": "validation_error"},
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
