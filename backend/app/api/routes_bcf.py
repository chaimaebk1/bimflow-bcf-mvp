"""FastAPI routes related to BCF operations."""
from __future__ import annotations

import os
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.bcf import merger, reader

router = APIRouter(prefix="/bcf", tags=["bcf"])


async def _save_upload_to_temp(upload: UploadFile) -> str:
    suffix = os.path.splitext(upload.filename or "")[1] or ".bcfzip"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        await upload.seek(0)
        contents = await upload.read()
        tmp.write(contents)
        return tmp.name


def _cleanup_file(path: str) -> None:
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


@router.post("/inspect")
async def inspect_bcf(file: UploadFile = File(...)) -> dict:
    if file is None:
        raise HTTPException(status_code=400, detail="Aucun fichier fourni.")

    temp_path = ""
    try:
        temp_path = await _save_upload_to_temp(file)
        project_meta, topics = reader.read_bcf(temp_path)
    except Exception as exc:  # pragma: no cover - defensive programming
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        _cleanup_file(temp_path)
        await file.close()

    return {"project": project_meta, "topics": topics}


@router.post("/merge")
async def merge_bcfs(files: list[UploadFile] = File(...)) -> FileResponse:
    if not files:
        raise HTTPException(status_code=400, detail="Aucun fichier fourni.")

    temp_paths: list[str] = []
    merged_path = ""
    try:
        for upload in files:
            temp_paths.append(await _save_upload_to_temp(upload))

        merged_path = merger.merge_bcfs(temp_paths)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive programming
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        for upload in files:
            await upload.close()
        for path in temp_paths:
            if path != merged_path:
                _cleanup_file(path)

    background = BackgroundTask(_cleanup_file, merged_path)
    return FileResponse(
        merged_path,
        filename="merged.bcfzip",
        media_type="application/octet-stream",
        background=background,
    )
