"""课件生成接口：异步 jobId + SSE 进度推送"""
import os
import uuid
import asyncio
import json
from typing import AsyncGenerator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core import rag
from core.llm import generate_slides_json
from core.doc_gen import generate_docx

router = APIRouter()
OUTPUT_DIR = "outputs"

# 内存 job 存储
_jobs: dict[str, dict] = {}


class GenerateRequest(BaseModel):
    intent: dict
    file_ids: list[str] = []


@router.post("/generate")
def generate(req: GenerateRequest):
    """同步生成（保持原有接口兼容性）"""
    intent = req.intent
    rag_chunks = _collect_rag(intent)
    try:
        slides_json = generate_slides_json(intent, rag_chunks)
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(500, f"课件内容生成失败：{e}")

    job_id = str(uuid.uuid4())[:8]
    docx_name = f"{job_id}_教案.docx"
    docx_path = os.path.join(OUTPUT_DIR, docx_name)
    try:
        generate_docx(intent, rag_chunks, docx_path)
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(500, f"Word 生成失败：{e}")

    page_count = len(slides_json.get("pages", []))
    return {
        "slides_json": slides_json,
        "docx": docx_name,
        "message": f"课件生成成功！共 {page_count} 页",
    }


@router.post("/generate/start")
async def generate_start(req: GenerateRequest):
    """启动异步生成，立即返回 job_id"""
    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {"status": "pending", "progress": 0, "message": "准备中...",
                     "slides_json": None, "docx": None, "error": None}
    asyncio.create_task(_run_generate(job_id, req.intent))
    return {"job_id": job_id}


@router.get("/generate/{job_id}/stream")
async def generate_stream(job_id: str):
    """SSE 进度流，前端 EventSource 订阅"""
    if job_id not in _jobs:
        from fastapi import HTTPException
        raise HTTPException(404, "job 不存在")

    async def event_gen() -> AsyncGenerator[str, None]:
        last_progress = -1
        timeout = 120  # 最多等120s
        elapsed = 0
        while elapsed < timeout:
            job = _jobs.get(job_id, {})
            progress = job.get("progress", 0)
            if progress != last_progress:
                last_progress = progress
                payload = {
                    "progress": progress,
                    "message": job.get("message", ""),
                    "done": job.get("status") in ("done", "error"),
                }
                if job.get("status") == "done":
                    payload["slides_json"] = job["slides_json"]
                    payload["docx"] = job["docx"]
                elif job.get("status") == "error":
                    payload["error"] = job["error"]
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                if payload["done"]:
                    break
            await asyncio.sleep(0.5)
            elapsed += 0.5

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _run_generate(job_id: str, intent: dict):
    """后台异步生成任务"""
    def update(progress: int, message: str):
        if job_id in _jobs:
            _jobs[job_id]["progress"] = progress
            _jobs[job_id]["message"] = message
            _jobs[job_id]["status"] = "running"

    try:
        update(10, "正在检索知识库...")
        rag_chunks = await asyncio.get_event_loop().run_in_executor(
            None, _collect_rag, intent
        )

        update(30, "正在生成课件大纲...")
        slides_json = await asyncio.get_event_loop().run_in_executor(
            None, generate_slides_json, intent, rag_chunks
        )

        update(70, "正在生成 Word 教案...")
        job_short = job_id[:8]
        docx_name = f"{job_short}_教案.docx"
        docx_path = os.path.join(OUTPUT_DIR, docx_name)
        await asyncio.get_event_loop().run_in_executor(
            None, generate_docx, intent, rag_chunks, docx_path
        )

        update(100, "生成完成！")
        _jobs[job_id]["status"] = "done"
        _jobs[job_id]["slides_json"] = slides_json
        _jobs[job_id]["docx"] = docx_name

    except Exception as e:
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["error"] = str(e)
        _jobs[job_id]["message"] = f"生成失败：{e}"


def _collect_rag(intent: dict) -> list[str]:
    topic = intent.get("topic", "")
    key_points = intent.get("key_points", [])
    rag_chunks = []
    for kp in key_points:
        results = rag.search(f"{topic} {kp}", top_k=2)
        rag_chunks.extend(results)
    return list(dict.fromkeys(rag_chunks))  # 去重保序
