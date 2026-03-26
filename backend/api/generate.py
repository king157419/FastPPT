import os
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import rag
from core.llm import generate_slide_content
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

    # 为每个知识点：RAG检索 + Claude生成真实内容
    slide_contents = []
    for kp in key_points:
        rag_results = rag.search(f"{topic} {kp}", top_k=1)
        rag_ctx = rag_results[0] if rag_results else ""
        try:
            content = generate_slide_content(topic, kp, rag_ctx)
        except Exception:
            content = {
                "bullets": [
                    f"{kp}的基本概念与定义",
                    f"{kp}的核心原理与机制",
                    f"{kp}在实际场景中的应用",
                ],
                "tip": "结合实际案例讲解",
            }
        slide_contents.append({
            "key_point": kp,
            "bullets": content.get("bullets", []),
            "tip": content.get("tip", ""),
            "rag_ctx": rag_ctx,
        })

    job_id = str(uuid.uuid4())[:8]
    pptx_name = f"{job_id}_课件.pptx"
    docx_name = f"{job_id}_教案.docx"
    pptx_path = os.path.join(OUTPUT_DIR, pptx_name)
    docx_path = os.path.join(OUTPUT_DIR, docx_name)

    try:
        generate_pptx(intent, slide_contents, pptx_path)
    except Exception as e:
        raise HTTPException(500, f"PPT 生成失败：{e}")

    # doc_gen 仍使用 rag_chunks 列表（兼容）
    rag_chunks = [sc["rag_ctx"] for sc in slide_contents]
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
