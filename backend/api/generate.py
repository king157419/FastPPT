import os
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import rag
from core.ppt_gen import generate_pptx
from core.doc_gen import generate_docx

router = APIRouter()

OUTPUT_DIR = "outputs"


class GenerateRequest(BaseModel):
    intent: dict
    file_ids: list[str] = []


@router.post("/generate")
def generate(req: GenerateRequest):
    intent = req.intent
    topic = intent.get("topic", "未知主题")
    key_points = intent.get("key_points", [])

    # RAG 检索：为每个知识点检索相关段落
    rag_chunks = []
    for kp in key_points:
        results = rag.search(f"{topic} {kp}", top_k=1)
        rag_chunks.append(results[0] if results else "")

    job_id = str(uuid.uuid4())[:8]
    pptx_name = f"{job_id}_课件.pptx"
    docx_name = f"{job_id}_教案.docx"
    pptx_path = os.path.join(OUTPUT_DIR, pptx_name)
    docx_path = os.path.join(OUTPUT_DIR, docx_name)

    try:
        generate_pptx(intent, rag_chunks, pptx_path)
    except Exception as e:
        raise HTTPException(500, f"PPT 生成失败：{e}")

    try:
        generate_docx(intent, rag_chunks, docx_path)
    except Exception as e:
        raise HTTPException(500, f"Word 生成失败：{e}")

    return {
        "job_id": job_id,
        "pptx": pptx_name,
        "docx": docx_name,
        "message": f"课件生成成功！共 {len(key_points) + 3} 页 PPT + Word 教案",
    }
