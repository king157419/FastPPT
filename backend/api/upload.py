import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
import aiofiles

from core.parser import extract_text, chunk_text
from core import rag

router = APIRouter()

ALLOWED_EXTS = {".pdf", ".docx", ".doc", ".pptx", ".ppt", ".txt", ".md"}
UPLOAD_DIR = "uploads"


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(400, f"不支持的文件类型：{ext}，支持：{', '.join(ALLOWED_EXTS)}")

    file_id = str(uuid.uuid4())[:8]
    save_name = f"{file_id}{ext}"
    save_path = os.path.join(UPLOAD_DIR, save_name)

    async with aiofiles.open(save_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # 解析文本
    try:
        text = extract_text(save_path)
    except Exception as e:
        raise HTTPException(500, f"文件解析失败：{e}")

    if not text.strip():
        return {
            "file_id": file_id,
            "filename": file.filename,
            "summary": "文件内容为空或无法提取文本",
            "chunk_count": 0,
        }

    # 分块并加入 RAG 索引
    chunks = chunk_text(text)
    rag.add_document(file_id, chunks)

    summary = text[:200].replace("\n", " ") + ("..." if len(text) > 200 else "")
    return {
        "file_id": file_id,
        "filename": file.filename,
        "summary": summary,
        "chunk_count": len(chunks),
    }
