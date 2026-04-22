"""File upload endpoint supporting docs/images/videos with source-index registration."""
from __future__ import annotations

import os
import uuid

import aiofiles
from fastapi import APIRouter, File, HTTPException, UploadFile

from core import rag
from core import source_index
from core.parser import extract_chunks_with_metadata, extract_ppt_outline, extract_text

router = APIRouter()

DOC_EXTS = {".pdf", ".docx", ".doc", ".pptx", ".ppt", ".txt", ".md"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
ALLOWED_EXTS = DOC_EXTS | IMAGE_EXTS | VIDEO_EXTS
UPLOAD_DIR = "uploads"


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")

    file_id = str(uuid.uuid4())[:8]
    save_name = f"{file_id}{ext}"
    save_path = os.path.join(UPLOAD_DIR, save_name)

    async with aiofiles.open(save_path, "wb") as handle:
        content = await file.read()
        await handle.write(content)

    source_index.register_file(file_id=file_id, filename=file.filename or save_name, path=save_path, ext=ext)

    if ext in IMAGE_EXTS:
        return await _handle_image(file_id, save_path, file.filename or save_name)
    if ext in VIDEO_EXTS:
        return await _handle_video(file_id, save_path, file.filename or save_name)
    return await _handle_doc(file_id, save_path, file.filename or save_name, ext)


async def _handle_doc(file_id: str, save_path: str, filename: str, ext: str) -> dict:
    try:
        chunks = extract_chunks_with_metadata(save_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Document parse failed: {exc}") from exc

    if ext in {".pptx", ".ppt"}:
        try:
            outline = extract_ppt_outline(save_path)
            source_index.update_outline(file_id, outline)
        except Exception:
            # Keep upload successful even if outline extraction fails.
            pass

    source_index.add_chunks(file_id, chunks)
    rag.add_document(file_id, [item.get("text", "") for item in chunks])

    summary_text = ""
    try:
        summary_text = extract_text(save_path)
    except Exception:
        summary_text = ""

    summary = summary_text[:200].replace("\n", " ")
    if summary_text and len(summary_text) > 200:
        summary += "..."

    return {
        "file_id": file_id,
        "filename": filename,
        "summary": summary or "Uploaded successfully",
        "chunk_count": len(chunks),
        "type": "doc",
    }


async def _handle_image(file_id: str, save_path: str, filename: str) -> dict:
    import base64

    try:
        with open(save_path, "rb") as handle:
            image_base64 = base64.b64encode(handle.read()).decode()
        from core.llm import describe_image

        description = describe_image(image_base64)
    except Exception as exc:
        description = f"Image understanding failed: {exc}"

    chunks = [
        {
            "text": description,
            "metadata": {"page_or_slide": "image", "chunk_index": 0},
        }
    ] if description else []

    source_index.add_chunks(file_id, chunks)
    rag.add_document(file_id, [item["text"] for item in chunks])

    return {
        "file_id": file_id,
        "filename": filename,
        "summary": description[:200],
        "chunk_count": len(chunks),
        "type": "image",
    }


async def _handle_video(file_id: str, save_path: str, filename: str) -> dict:
    from core.video_parser import build_rag_chunks, parse_video

    try:
        result = parse_video(save_path, output_dir=UPLOAD_DIR)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Video parse failed: {exc}") from exc

    rag_chunks = build_rag_chunks(result)
    structured = [
        {
            "text": text,
            "metadata": {"page_or_slide": "video", "chunk_index": idx},
        }
        for idx, text in enumerate(rag_chunks)
    ]
    source_index.add_chunks(file_id, structured)
    rag.add_document(file_id, rag_chunks)

    frame_count = len(result.frames)
    summary = f"Video {result.duration:.0f}s, extracted {frame_count} frames"
    if result.subtitle_text:
        summary += f", subtitle chars {len(result.subtitle_text)}"
    if result.error:
        summary += f" ({result.error})"

    frames_info = [
        {
            "id": frame.id,
            "timestamp": frame.timestamp,
            "description": frame.description,
            "save_path": frame.save_path,
        }
        for frame in result.frames
    ]

    return {
        "file_id": file_id,
        "filename": filename,
        "summary": summary,
        "chunk_count": len(rag_chunks),
        "type": "video",
        "frames": frames_info,
    }
