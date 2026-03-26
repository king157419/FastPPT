"""文件上传：支持 PDF/Word/PPT/TXT/图片/视频"""
import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
import aiofiles

from core.parser import extract_text, chunk_text
from core import rag

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
        raise HTTPException(400, f"不支持的文件类型：{ext}")

    file_id = str(uuid.uuid4())[:8]
    save_name = f"{file_id}{ext}"
    save_path = os.path.join(UPLOAD_DIR, save_name)

    async with aiofiles.open(save_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    if ext in IMAGE_EXTS:
        return await _handle_image(file_id, save_path, file.filename)
    elif ext in VIDEO_EXTS:
        return await _handle_video(file_id, save_path, file.filename)
    else:
        return await _handle_doc(file_id, save_path, file.filename)


async def _handle_doc(file_id: str, save_path: str, filename: str) -> dict:
    try:
        text = extract_text(save_path)
    except Exception as e:
        raise HTTPException(500, f"文件解析失败：{e}")

    if not text.strip():
        return {"file_id": file_id, "filename": filename,
                "summary": "文件内容为空或无法提取文本", "chunk_count": 0, "type": "doc"}

    chunks = chunk_text(text)
    rag.add_document(file_id, chunks)
    summary = text[:200].replace("\n", " ") + ("..." if len(text) > 200 else "")
    return {"file_id": file_id, "filename": filename,
            "summary": summary, "chunk_count": len(chunks), "type": "doc"}


async def _handle_image(file_id: str, save_path: str, filename: str) -> dict:
    import base64
    try:
        with open(save_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        from core.llm import describe_image
        description = describe_image(img_b64)
    except Exception as e:
        description = f"图片理解失败：{e}"

    chunks = chunk_text(description) if description else []
    if chunks:
        rag.add_document(file_id, chunks)

    return {"file_id": file_id, "filename": filename,
            "summary": description[:200], "chunk_count": len(chunks), "type": "image"}


async def _handle_video(file_id: str, save_path: str, filename: str) -> dict:
    from core.video_parser import parse_video, build_rag_chunks
    try:
        result = parse_video(save_path, output_dir=UPLOAD_DIR)
    except Exception as e:
        raise HTTPException(500, f"视频解析失败：{e}")

    chunks = build_rag_chunks(result)
    if chunks:
        rag.add_document(file_id, chunks)

    frame_count = len(result.frames)
    summary = f"视频时长 {result.duration:.0f}s，提取 {frame_count} 帧"
    if result.subtitle_text:
        summary += f"，字幕 {len(result.subtitle_text)} 字"
    if result.error:
        summary += f"（{result.error}）"

    # 返回帧截图路径列表（供前端预览或作为PPT配图）
    frames_info = [
        {"id": f.id, "timestamp": f.timestamp,
         "description": f.description, "save_path": f.save_path}
        for f in result.frames
    ]
    return {"file_id": file_id, "filename": filename,
            "summary": summary, "chunk_count": len(chunks),
            "type": "video", "frames": frames_info}
