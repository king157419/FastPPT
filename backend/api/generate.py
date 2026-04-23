"""Thin generate API router delegating orchestration to service layer."""
from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services import generate_service

router = APIRouter()
OUTPUT_DIR = generate_service.OUTPUT_DIR
_jobs = generate_service._jobs

# Backward-compatible monkeypatch hooks used by existing tests.
_collect_rag = generate_service._collect_rag
_collect_rag_and_evidence = generate_service._collect_rag_and_evidence
_apply_reference_outline_context = generate_service._apply_reference_outline_context
_retrieve_teaching_knowledge = generate_service._retrieve_teaching_knowledge
_learn_from_generation = generate_service._learn_from_generation
generate_slides_json = generate_service.generate_slides_json
generate_slide_drafts = generate_service.generate_slide_drafts
revise_slides_json = generate_service.revise_slides_json
generate_pptx_from_slides_json = generate_service.generate_pptx_from_slides_json
generate_docx = generate_service.generate_docx


class GenerateRequest(BaseModel):
    intent: dict
    file_ids: list[str] = []


class ReviseRequest(BaseModel):
    intent: dict = {}
    slides_json: dict
    instruction: str
    page_indexes: list[int] = []


def _sync_service_config() -> None:
    generate_service._jobs = _jobs
    generate_service.OUTPUT_DIR = OUTPUT_DIR
    generate_service._collect_rag = _collect_rag
    generate_service._collect_rag_and_evidence = _collect_rag_and_evidence
    generate_service._apply_reference_outline_context = _apply_reference_outline_context
    generate_service._retrieve_teaching_knowledge = _retrieve_teaching_knowledge
    generate_service._learn_from_generation = _learn_from_generation
    generate_service.generate_slides_json = generate_slides_json
    generate_service.generate_slide_drafts = generate_slide_drafts
    generate_service.revise_slides_json = revise_slides_json
    generate_service.generate_pptx_from_slides_json = generate_pptx_from_slides_json
    generate_service.generate_docx = generate_docx


async def _run_generate(job_id: str, intent: dict, file_ids: list[str]) -> None:
    _sync_service_config()
    await generate_service.run_generate_job(job_id, intent, file_ids)


@router.post("/generate")
def generate(req: GenerateRequest):
    _sync_service_config()
    try:
        return generate_service.generate_courseware(req.intent, req.file_ids)
    except generate_service.ServiceValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}") from exc


@router.post("/generate/start")
async def generate_start(req: GenerateRequest):
    _sync_service_config()
    try:
        job_id = generate_service.create_generate_job(req.intent, req.file_ids)
    except generate_service.ServiceValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    asyncio.create_task(_run_generate(job_id, req.intent, req.file_ids))
    return {"job_id": job_id}


@router.get("/generate/{job_id}/stream")
async def generate_stream(job_id: str):
    if generate_service.get_job(job_id) is None:
        raise HTTPException(status_code=404, detail="job not found")

    async def event_gen() -> AsyncGenerator[str, None]:
        last_progress = -1
        elapsed = 0.0
        timeout_seconds = 120
        while elapsed < timeout_seconds:
            job = generate_service.get_job(job_id) or {}
            progress = int(job.get("progress", 0))
            if progress != last_progress:
                last_progress = progress
                payload: dict[str, Any] = {
                    "progress": progress,
                    "message": job.get("message", ""),
                    "done": job.get("status") in {"done", "error"},
                }
                if job.get("status") == "done":
                    payload.update(
                        {
                            "slides_json": job.get("slides_json"),
                            "pptx": job.get("pptx"),
                            "docx": job.get("docx"),
                            "teaching_spec": job.get("teaching_spec"),
                            "slide_plan": job.get("slide_plan"),
                            "slide_drafts": job.get("slide_drafts"),
                            "block_summary": job.get("block_summary"),
                            "compound_factor": job.get("compound_factor", 0.0),
                            "mode_a": job.get("mode_a", {}),
                        }
                    )
                elif job.get("status") == "error":
                    payload["error"] = job.get("error")

                yield f"data: {json.dumps(payload, ensure_ascii=False)}\\n\\n"
                if payload["done"]:
                    break

            await asyncio.sleep(0.5)
            elapsed += 0.5

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/generate/revise")
def revise(req: ReviseRequest):
    _sync_service_config()
    try:
        return generate_service.revise_courseware(
            intent=req.intent or {},
            slides_json=req.slides_json,
            instruction=req.instruction,
            page_indexes=req.page_indexes,
        )
    except generate_service.ServiceValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Revision failed: {exc}") from exc
