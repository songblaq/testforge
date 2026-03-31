"""Input file management endpoints."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from pydantic import BaseModel

from testforge.web.deps import resolve_project
from testforge.core.config import load_config

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

# Two routers to avoid Starlette greedy-path-param routing conflicts:
#   - router: GET/POST  on /api/projects/{project_path:path}/inputs
#   - delete_router: DELETE on /api/inputs  (project_path as query param)
router = APIRouter(prefix="/api/projects", tags=["inputs"])
delete_router = APIRouter(prefix="/api/inputs", tags=["inputs"])


@router.get("/{project_path:path}/inputs")
async def list_inputs(project_path: str):
    """List input files in the project."""
    p = resolve_project(project_path)
    config = load_config(p)
    input_dir = p / config.input_dir
    if not input_dir.exists():
        return {"files": [], "count": 0}

    files = []
    for f in sorted(input_dir.iterdir()):
        if f.is_file() and not f.name.startswith("."):
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
                "type": f.suffix.lstrip(".") or "unknown",
            })
    return {"files": files, "count": len(files)}


@router.post("/{project_path:path}/inputs")
async def upload_input(project_path: str, file: UploadFile = File(...)):
    """Upload an input file to the project."""
    p = resolve_project(project_path)
    config = load_config(p)
    input_dir = p / config.input_dir
    input_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    safe_name = Path(file.filename).name
    if not safe_name or safe_name.startswith("."):
        raise HTTPException(status_code=400, detail="Invalid filename")

    dest = input_dir / safe_name
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")
    with open(dest, "wb") as out:
        out.write(contents)

    return {
        "name": safe_name,
        "size": dest.stat().st_size,
        "type": dest.suffix.lstrip(".") or "unknown",
    }


@router.get("/{project_path:path}/inputs/{filename}")
async def get_input_content(project_path: str, filename: str):
    """Get input file content for preview/download."""
    from fastapi.responses import Response
    p = resolve_project(project_path)
    config = load_config(p)
    safe_name = Path(filename).name
    target = p / config.input_dir / safe_name
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    content = target.read_bytes()
    ext = target.suffix.lower()
    content_types = {
        '.md': 'text/markdown', '.txt': 'text/plain', '.json': 'application/json',
        '.yaml': 'text/yaml', '.yml': 'text/yaml',
        '.pdf': 'application/pdf', '.png': 'image/png', '.jpg': 'image/jpeg',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }
    ct = content_types.get(ext, 'application/octet-stream')

    return Response(content=content, media_type=ct, headers={
        "Content-Disposition": f'inline; filename="{safe_name}"'
    })


class URLInput(BaseModel):
    url: str


class RepoInput(BaseModel):
    repo: str


@router.post("/{project_path:path}/inputs/url")
async def add_url_input(project_path: str, body: URLInput):
    """Fetch URL content and save as an input document."""
    from testforge.input.url import parse_url
    from urllib.parse import urlparse

    p = resolve_project(project_path)
    config = load_config(p)
    input_dir = p / config.input_dir
    input_dir.mkdir(parents=True, exist_ok=True)

    result = parse_url(body.url)

    # Generate safe filename from URL
    parsed = urlparse(body.url)
    safe_name = (parsed.netloc + parsed.path).replace("/", "_").strip("_")[:80]
    filename = f"url_{safe_name}.md"

    # Save content
    content = f"# {body.url}\n\n{result.get('text', '')}"
    (input_dir / filename).write_text(content)

    size = len(content.encode())
    return {"name": filename, "size": size, "type": "url"}


@router.post("/{project_path:path}/inputs/repo")
async def add_repo_input(project_path: str, body: RepoInput):
    """Clone repository and save analysis as input document."""
    from testforge.input.repository import parse_repository

    p = resolve_project(project_path)
    config = load_config(p)
    input_dir = p / config.input_dir
    input_dir.mkdir(parents=True, exist_ok=True)

    result = parse_repository(body.repo)

    # Generate safe filename
    safe_name = body.repo.replace("/", "_").replace(":", "_").strip("_")[:80]
    filename = f"repo_{safe_name}.md"

    content = result.get("text", "")
    (input_dir / filename).write_text(content)

    size = len(content.encode())
    return {"name": filename, "size": size, "type": "repository"}


@delete_router.delete("")
async def delete_input(
    project_path: str = Query(..., description="Project path"),
    filename: str = Query(..., description="Filename to delete"),
):
    """Delete an input file. Pass project_path and filename as query params."""
    p = resolve_project(project_path)
    config = load_config(p)

    # Sanitize - prevent path traversal in filename
    safe_name = Path(filename).name
    target = p / config.input_dir / safe_name

    if not target.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    target.unlink()
    return {"deleted": safe_name}
