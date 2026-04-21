"""Course generation API with async job progress and block-aware output."""
from __future__ import annotations

import asyncio
import json
import os
import uuid
from typing import Any, AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core import rag
from core.doc_gen import generate_docx
from core.llm import generate_slides_json
from core.slide_blocks import attach_blocks_to_slides_json
from core.teaching_spec import compile_teaching_spec
from core.compound_knowledge import get_knowledge_store

router = APIRouter()
OUTPUT_DIR = "outputs"

_jobs: dict[str, dict[str, Any]] = {}


class GenerateRequest(BaseModel):
    intent: dict
    file_ids: list[str] = []


@router.post("/generate")
def generate(req: GenerateRequest):
    """Synchronous generation endpoint for backward compatibility."""
    spec = compile_teaching_spec(req.intent)
    missing = spec.missing_preflight_labels()
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"生成前仍缺少必填信息：{'、'.join(missing)}",
        )
    effective_intent = spec.to_intent()

    # 检索复利知识
    knowledge_context = _retrieve_teaching_knowledge(effective_intent)
    if knowledge_context:
        effective_intent["knowledge_context"] = knowledge_context

    rag_chunks = _collect_rag(effective_intent)
    try:
        slides_json_raw = generate_slides_json(effective_intent, rag_chunks)
    except Exception as exc:
        raise HTTPException(500, f"课件内容生成失败: {exc}") from exc

    slides_json, block_summary = attach_blocks_to_slides_json(slides_json_raw)

    # 学习新模式
    learn_result = _learn_from_generation(effective_intent, slides_json)
    compound_factor = learn_result.get("compound_factor", 0.0) if learn_result else 0.0

    job_id = str(uuid.uuid4())[:8]
    docx_name = f"{job_id}_教案.docx"
    docx_path = os.path.join(OUTPUT_DIR, docx_name)
    try:
        generate_docx(effective_intent, rag_chunks, docx_path)
    except Exception as exc:
        raise HTTPException(500, f"Word 生成失败: {exc}") from exc

    page_count = len(slides_json.get("pages", []))
    return {
        "slides_json": slides_json,
        "docx": docx_name,
        "message": f"课件生成成功，共 {page_count} 页",
        "teaching_spec": spec.to_dict(),
        "block_summary": block_summary,
        "compound_factor": compound_factor,
    }


@router.post("/generate/start")
async def generate_start(req: GenerateRequest):
    """Start async generation and return job_id immediately."""
    spec = compile_teaching_spec(req.intent)
    missing = spec.missing_preflight_labels()
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"生成前仍缺少必填信息：{'、'.join(missing)}",
        )

    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "message": "准备中...",
        "slides_json": None,
        "docx": None,
        "teaching_spec": None,
        "block_summary": None,
        "error": None,
    }
    asyncio.create_task(_run_generate(job_id, req.intent))
    return {"job_id": job_id}


@router.get("/generate/{job_id}/stream")
async def generate_stream(job_id: str):
    """SSE progress stream endpoint for frontend EventSource."""
    if job_id not in _jobs:
        raise HTTPException(404, "job 不存在")

    async def event_gen() -> AsyncGenerator[str, None]:
        last_progress = -1
        timeout_seconds = 120
        elapsed = 0.0
        while elapsed < timeout_seconds:
            job = _jobs.get(job_id, {})
            progress = int(job.get("progress", 0))
            if progress != last_progress:
                last_progress = progress
                payload: dict[str, Any] = {
                    "progress": progress,
                    "message": job.get("message", ""),
                    "done": job.get("status") in ("done", "error"),
                }
                if job.get("status") == "done":
                    payload["slides_json"] = job.get("slides_json")
                    payload["docx"] = job.get("docx")
                    payload["teaching_spec"] = job.get("teaching_spec")
                    payload["block_summary"] = job.get("block_summary")
                    payload["compound_factor"] = job.get("compound_factor", 0.0)
                elif job.get("status") == "error":
                    payload["error"] = job.get("error")

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
    """Background generation worker for async flow."""

    def update(progress: int, message: str) -> None:
        if job_id in _jobs:
            _jobs[job_id]["progress"] = progress
            _jobs[job_id]["message"] = message
            _jobs[job_id]["status"] = "running"

    try:
        spec = compile_teaching_spec(intent)
        missing = spec.missing_preflight_labels()
        if missing:
            raise ValueError(f"生成前仍缺少必填信息：{'、'.join(missing)}")
        effective_intent = spec.to_intent()
        _jobs[job_id]["teaching_spec"] = spec.to_dict()

        update(5, "正在检索复利知识库...")
        knowledge_context = await asyncio.get_event_loop().run_in_executor(
            None, _retrieve_teaching_knowledge, effective_intent
        )
        if knowledge_context:
            effective_intent["knowledge_context"] = knowledge_context

        update(10, "正在检索知识库...")
        rag_chunks = await asyncio.get_event_loop().run_in_executor(
            None, _collect_rag, effective_intent
        )

        update(35, "正在生成课件内容...")
        slides_json_raw = await asyncio.get_event_loop().run_in_executor(
            None, generate_slides_json, effective_intent, rag_chunks
        )

        update(65, "正在归一化页面内容块...")
        slides_json, block_summary = await asyncio.get_event_loop().run_in_executor(
            None, attach_blocks_to_slides_json, slides_json_raw
        )

        update(75, "正在学习新教学模式...")
        learn_result = await asyncio.get_event_loop().run_in_executor(
            None, _learn_from_generation, effective_intent, slides_json
        )
        compound_factor = learn_result.get("compound_factor", 0.0) if learn_result else 0.0

        update(80, "正在生成 Word 教案...")
        docx_name = f"{job_id[:8]}_教案.docx"
        docx_path = os.path.join(OUTPUT_DIR, docx_name)
        await asyncio.get_event_loop().run_in_executor(
            None, generate_docx, effective_intent, rag_chunks, docx_path
        )

        update(100, "生成完成")
        _jobs[job_id]["status"] = "done"
        _jobs[job_id]["slides_json"] = slides_json
        _jobs[job_id]["docx"] = docx_name
        _jobs[job_id]["block_summary"] = block_summary
        _jobs[job_id]["compound_factor"] = compound_factor

    except Exception as exc:
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["error"] = str(exc)
        _jobs[job_id]["message"] = f"生成失败: {exc}"


def _collect_rag(intent: dict) -> list[str]:
    topic = intent.get("topic", "")
    key_points = intent.get("key_points", [])
    rag_chunks: list[str] = []
    for kp in key_points:
        results = rag.search(f"{topic} {kp}", top_k=2)
        rag_chunks.extend(results)
    # Keep order while removing duplicates.
    return list(dict.fromkeys(rag_chunks))


def _extract_teaching_patterns(intent: dict, slides_json: dict) -> str:
    """从生成的课件中提取教学模式"""
    topic = intent.get("topic", "")
    audience = intent.get("audience", "")
    style = intent.get("style", "")
    pages = slides_json.get("pages", [])

    # 统计页面类型分布
    type_counts = {}
    for page in pages:
        page_type = page.get("type", "content")
        type_counts[page_type] = type_counts.get(page_type, 0) + 1

    # 提取结构模式
    structure = " -> ".join([p.get("type", "content") for p in pages[:5]])

    pattern = f"""教学模式：
- 受众：{audience}
- 风格：{style}
- 页面结构：{structure}
- 类型分布：{type_counts}
- 总页数：{len(pages)}

适用场景：{topic}类课程
"""
    return pattern


def _learn_from_generation(intent: dict, slides_json: dict):
    """从生成结果中学习并存储到复利知识库"""
    try:
        kb = get_knowledge_store()
        topic = intent.get("topic", "")
        audience = intent.get("audience", "")
        style = intent.get("style", "")

        # 提取教学模式
        pattern = _extract_teaching_patterns(intent, slides_json)

        # 存储到知识库
        tags = [audience, style, "教学模式"]
        metadata = {
            "topic": topic,
            "page_count": len(slides_json.get("pages", [])),
            "generated_at": intent.get("generated_at", "")
        }

        result = kb.add_or_update(
            topic=f"{topic} - {audience}教学模式",
            content=pattern,
            tags=tags,
            metadata=metadata
        )

        return result
    except Exception as e:
        print(f"[Knowledge] Learning failed: {e}")
        return None


def _retrieve_teaching_knowledge(intent: dict) -> str:
    """检索相关教学模式知识"""
    try:
        kb = get_knowledge_store()
        topic = intent.get("topic", "")
        audience = intent.get("audience", "")

        # 检索相关知识
        results = kb.retrieve(f"{topic} {audience}", top_k=3)

        if not results:
            return ""

        # 构建知识提示
        knowledge_text = "\n\n【复利知识库 - 历史教学模式参考】\n"
        for i, entry in enumerate(results, 1):
            knowledge_text += f"\n{i}. {entry['topic']} (更新{entry['update_count']}次)\n"
            knowledge_text += f"{entry['content'][:300]}...\n"

        return knowledge_text
    except Exception as e:
        print(f"[Knowledge] Retrieval failed: {e}")
        return ""
