"""FastAPI routes related to BCF operations."""
from __future__ import annotations

import base64
import logging
import os
import tempfile
import zipfile
from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from starlette.background import BackgroundTask

from app.bcf import merger, reader

router = APIRouter(prefix="/bcf", tags=["bcf"])

logger = logging.getLogger(__name__)


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


def _detect_bcf_type(upload: UploadFile, temp_path: str) -> str:
    filename = (upload.filename or "").lower()
    if zipfile.is_zipfile(temp_path):
        return ".bcfzip"
    if filename.endswith(".bcf"):
        return ".bcf"
    if filename.endswith(".bcfzip"):
        return ".bcfzip"
    return "unknown"


def _serialise_snapshot(topic: Dict[str, Any]) -> str | None:
    data = topic.get("snapshotData")
    if isinstance(data, (bytes, bytearray, memoryview)):
        encoded = base64.b64encode(bytes(data)).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    snapshot = topic.get("snapshot")
    if isinstance(snapshot, str) and snapshot.strip():
        return snapshot.strip()
    return None


def _normalise_topics(raw_topics: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    normalised: list[Dict[str, Any]] = []
    for topic in raw_topics:
        if not isinstance(topic, dict):
            continue

        comments: list[Dict[str, str]] = []
        for comment in topic.get("comments", []):
            if not isinstance(comment, dict):
                continue
            comment_entry: Dict[str, str] = {
                "author": str(comment.get("author") or ""),
                "date": str(
                    comment.get("date") or comment.get("createdAt") or ""
                ),
                "text": str(comment.get("text") or comment.get("comment") or ""),
            }
            if comment.get("guid"):
                comment_entry["guid"] = str(comment.get("guid"))
            comments.append(comment_entry)

        viewpoints: list[str] = []
        for viewpoint in topic.get("viewpoints", []):
            if isinstance(viewpoint, str) and viewpoint.strip():
                viewpoints.append(viewpoint.strip())
            elif isinstance(viewpoint, dict):
                for key in ("viewpoint", "snapshot", "guid", "index"):
                    value = viewpoint.get(key)
                    if isinstance(value, str) and value.strip():
                        viewpoints.append(value.strip())
                        break

        normalised.append(
            {
                "guid": str(topic.get("guid") or ""),
                "title": str(topic.get("title") or ""),
                "status": str(topic.get("status") or ""),
                "priority": str(topic.get("priority") or ""),
                "author": str(topic.get("author") or ""),
                "createdAt": str(topic.get("createdAt") or ""),
                "comments": comments,
                "viewpoints": viewpoints,
                "snapshot": _serialise_snapshot(topic),
            }
        )

    return normalised


@router.post("/inspect")
async def inspect_bcf(file: UploadFile = File(...)) -> dict:
    logger.info("Received request: POST /bcf/inspect")
    if file is None:
        raise HTTPException(status_code=400, detail="Aucun fichier fourni.")

    temp_path = ""
    project_meta: Dict[str, Any] = {}
    response_topics: list[Dict[str, Any]] = []
    try:
        temp_path = await _save_upload_to_temp(file)
        logger.info(
            "Uploaded file '%s' stored at '%s'", file.filename, temp_path
        )
        detected_type = _detect_bcf_type(file, temp_path)
        logger.info("Detected BCF type for '%s': %s", file.filename, detected_type)
        project_meta, topics = reader.read_bcf(temp_path)
        response_topics = _normalise_topics(topics)
        if not response_topics:
            raise HTTPException(
                status_code=400,
                detail="Aucune donnée d'issue n'a pu être extraite du fichier fourni.",
            )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive programming
        logger.exception("Failed to parse BCF file '%s'", file.filename)
        return JSONResponse(status_code=400, content={"detail": str(exc)})
    finally:
        _cleanup_file(temp_path)
        await file.close()

    return {"project": project_meta, "topics": response_topics}


@router.post("/merge")
async def merge_bcfs(files: list[UploadFile] = File(...)) -> FileResponse:
    logger.info("Received request: POST /bcf/merge")
    if not files:
        raise HTTPException(status_code=400, detail="Aucun fichier fourni.")

    temp_paths: list[str] = []
    merged_path = ""
    try:
        for upload in files:
            temp_paths.append(await _save_upload_to_temp(upload))
            temp_path = temp_paths[-1]
            logger.info(
                "Uploaded file '%s' stored at '%s'", upload.filename, temp_path
            )
            detected_type = _detect_bcf_type(upload, temp_path)
            logger.info(
                "Detected BCF type for '%s': %s", upload.filename, detected_type
            )

        merged_path = merger.merge_bcfs(temp_paths)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive programming
        logger.exception("Failed to merge BCF files")
        return JSONResponse(status_code=400, content={"detail": str(exc)})
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
