"""Thin upload API router delegating orchestration to service layer."""
from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from services import upload_service

router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        return await upload_service.save_and_index_upload(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}") from exc
