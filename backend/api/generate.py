"""Course generation API with async job progress, Mode A support, and evidence attachment."""
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
from core import source_index
from core.compound_knowledge import get_knowledge_store
from core.doc_gen import generate_docx
from core.llm import generate_slides_json, revise_slides_json
from core.ppt_gen import generate_pptx_from_slides_json
from core.slide_blocks import attach_blocks_to_slides_json
from core.teaching_spec import compile_teaching_spec

router = APIRouter()
OUTPUT_DIR = "outputs"

_jobs: dict[str, dict[str, Any]] = {}


class GenerateRequest(BaseModel):
    intent: dict
    file_ids: list[str] = []


class ReviseRequest(BaseModel):
    intent: dict = {}
    slides_json: dict
    instruction: str
    page_indexes: list[int] = []


@router.post("/generate")
def generate(req: GenerateRequest):
    spec = compile_teaching_spec(req.intent)
    missing = spec.missing_preflight_labels()
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing required fields: {', '.join(missing)}")

    effective_intent = spec.to_intent()
    mode_a_info = _apply_reference_outline_context(effective_intent, req.file_ids)

    knowledge_context = _retrieve_teaching_knowledge(effective_intent)
    if knowledge_context:
        effective_intent["knowledge_context"] = knowledge_context

    rag_bundle = _collect_rag_and_evidence(effective_intent, req.file_ids)
    rag_chunks = rag_bundle["chunks"]

    try:
        slides_json_raw = generate_slides_json(effective_intent, rag_chunks)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Slide generation failed: {exc}") from exc

    slides_with_evidence = _attach_page_evidence(
        slides_json_raw,
        effective_intent,
        rag_bundle["evidence_by_key_point"],
        rag_bundle["general_evidence"],
    )
    slides_json, block_summary = attach_blocks_to_slides_json(slides_with_evidence)

    learn_result = _learn_from_generation(effective_intent, slides_json)
    compound_factor = learn_result.get("compound_factor", 0.0) if learn_result else 0.0

    job_id = str(uuid.uuid4())[:8]
    pptx_name = f"{job_id}_courseware.pptx"
    pptx_path = os.path.join(OUTPUT_DIR, pptx_name)
    docx_name = f"{job_id}_lesson_plan.docx"
    docx_path = os.path.join(OUTPUT_DIR, docx_name)

    try:
        generate_pptx_from_slides_json(effective_intent, slides_json, pptx_path)
        generate_docx(effective_intent, rag_chunks, docx_path, evidence_entries=rag_bundle["general_evidence"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"File export failed: {exc}") from exc

    return {
        "slides_json": slides_json,
        "pptx": pptx_name,
        "docx": docx_name,
        "message": f"Generation succeeded, total {len(slides_json.get('pages', []))} pages",
        "teaching_spec": spec.to_dict(),
        "block_summary": block_summary,
        "compound_factor": compound_factor,
        "mode_a": mode_a_info,
    }


@router.post("/generate/start")
async def generate_start(req: GenerateRequest):
    spec = compile_teaching_spec(req.intent)
    missing = spec.missing_preflight_labels()
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing required fields: {', '.join(missing)}")

    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "message": "Preparing...",
        "slides_json": None,
        "pptx": None,
        "docx": None,
        "teaching_spec": None,
        "block_summary": None,
        "compound_factor": 0.0,
        "mode_a": {"enabled": False, "outline_size": 0, "source_file": ""},
        "error": None,
    }

    asyncio.create_task(_run_generate(job_id, req.intent, req.file_ids))
    return {"job_id": job_id}


@router.get("/generate/{job_id}/stream")
async def generate_stream(job_id: str):
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="job not found")

    async def event_gen() -> AsyncGenerator[str, None]:
        last_progress = -1
        elapsed = 0.0
        timeout_seconds = 120
        while elapsed < timeout_seconds:
            job = _jobs.get(job_id, {})
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
                            "block_summary": job.get("block_summary"),
                            "compound_factor": job.get("compound_factor", 0.0),
                            "mode_a": job.get("mode_a", {}),
                        }
                    )
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


async def _run_generate(job_id: str, intent: dict, file_ids: list[str]):
    def update(progress: int, message: str) -> None:
        if job_id not in _jobs:
            return
        _jobs[job_id]["status"] = "running"
        _jobs[job_id]["progress"] = progress
        _jobs[job_id]["message"] = message

    try:
        spec = compile_teaching_spec(intent)
        missing = spec.missing_preflight_labels()
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        effective_intent = spec.to_intent()
        _jobs[job_id]["teaching_spec"] = spec.to_dict()

        update(5, "Resolving reference structure...")
        mode_a_info = await asyncio.get_event_loop().run_in_executor(
            None, _apply_reference_outline_context, effective_intent, file_ids
        )
        _jobs[job_id]["mode_a"] = mode_a_info

        update(10, "Retrieving compound knowledge...")
        knowledge_context = await asyncio.get_event_loop().run_in_executor(
            None, _retrieve_teaching_knowledge, effective_intent
        )
        if knowledge_context:
            effective_intent["knowledge_context"] = knowledge_context

        update(20, "Collecting retrieval context...")
        rag_bundle = await asyncio.get_event_loop().run_in_executor(
            None, _collect_rag_and_evidence, effective_intent, file_ids
        )

        update(40, "Generating slide JSON...")
        slides_json_raw = await asyncio.get_event_loop().run_in_executor(
            None, generate_slides_json, effective_intent, rag_bundle["chunks"]
        )

        update(55, "Attaching source evidence...")
        slides_with_evidence = await asyncio.get_event_loop().run_in_executor(
            None,
            _attach_page_evidence,
            slides_json_raw,
            effective_intent,
            rag_bundle["evidence_by_key_point"],
            rag_bundle["general_evidence"],
        )

        update(65, "Normalizing block schema...")
        slides_json, block_summary = await asyncio.get_event_loop().run_in_executor(
            None, attach_blocks_to_slides_json, slides_with_evidence
        )

        update(75, "Learning from output pattern...")
        learn_result = await asyncio.get_event_loop().run_in_executor(
            None, _learn_from_generation, effective_intent, slides_json
        )
        compound_factor = learn_result.get("compound_factor", 0.0) if learn_result else 0.0

        update(85, "Exporting PPT and DOC...")
        pptx_name = f"{job_id}_courseware.pptx"
        pptx_path = os.path.join(OUTPUT_DIR, pptx_name)
        docx_name = f"{job_id}_lesson_plan.docx"
        docx_path = os.path.join(OUTPUT_DIR, docx_name)

        await asyncio.get_event_loop().run_in_executor(
            None, generate_pptx_from_slides_json, effective_intent, slides_json, pptx_path
        )
        await asyncio.get_event_loop().run_in_executor(
            None, generate_docx, effective_intent, rag_bundle["chunks"], docx_path, rag_bundle["general_evidence"]
        )

        update(100, "Done")
        _jobs[job_id].update(
            {
                "status": "done",
                "slides_json": slides_json,
                "pptx": pptx_name,
                "docx": docx_name,
                "block_summary": block_summary,
                "compound_factor": compound_factor,
            }
        )

    except Exception as exc:
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["message"] = f"Generation failed: {exc}"
        _jobs[job_id]["error"] = str(exc)


@router.post("/generate/revise")
def revise(req: ReviseRequest):
    instruction = (req.instruction or "").strip()
    if not instruction:
        raise HTTPException(status_code=400, detail="instruction cannot be empty")

    spec = compile_teaching_spec(req.intent or {})
    effective_intent = spec.to_intent()

    revised = revise_slides_json(
        original_slides_json=req.slides_json,
        instruction=instruction,
        intent=effective_intent,
        page_indexes=req.page_indexes,
    )
    revised, block_summary = attach_blocks_to_slides_json(revised)

    job_id = str(uuid.uuid4())[:8]
    pptx_name = f"{job_id}_revised_courseware.pptx"
    pptx_path = os.path.join(OUTPUT_DIR, pptx_name)
    try:
        generate_pptx_from_slides_json(effective_intent, revised, pptx_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Revised PPT export failed: {exc}") from exc

    return {
        "slides_json": revised,
        "pptx": pptx_name,
        "message": "Revision completed and exported",
        "teaching_spec": spec.to_dict(),
        "block_summary": block_summary,
    }


def _apply_reference_outline_context(intent: dict, file_ids: list[str]) -> dict[str, Any]:
    outline, source_meta = source_index.choose_reference_outline(file_ids)
    if not outline:
        return {"enabled": False, "outline_size": 0, "source_file": ""}

    intent["preserve_structure"] = True
    intent["reference_outline"] = outline
    if source_meta and source_meta.get("file_name"):
        intent["reference_source"] = source_meta["file_name"]

    return {
        "enabled": True,
        "outline_size": len(outline),
        "source_file": source_meta.get("file_name", "") if source_meta else "",
    }


def _collect_rag(intent: dict) -> list[str]:
    topic = intent.get("topic", "")
    key_points = intent.get("key_points", [])
    rag_chunks: list[str] = []
    for kp in key_points:
        results = rag.search(f"{topic} {kp}", top_k=2)
        rag_chunks.extend(results)
    return list(dict.fromkeys(rag_chunks))


def _collect_rag_and_evidence(intent: dict, file_ids: list[str]) -> dict[str, Any]:
    topic = intent.get("topic", "")
    key_points = intent.get("key_points", []) or []

    rag_chunks = _collect_rag(intent)

    evidence_by_key_point: dict[str, list[dict[str, Any]]] = {}
    general_evidence: list[dict[str, Any]] = []

    queries = key_points or [topic]
    for query_item in queries:
        query = f"{topic} {query_item}".strip()
        source_hits = source_index.search_chunks(query=query, top_k=5, file_ids=file_ids)
        normalized_hits = [_normalize_evidence(hit) for hit in source_hits]
        evidence_by_key_point[str(query_item)] = _dedupe_evidence(normalized_hits)[:3]
        general_evidence.extend(normalized_hits)

    general_evidence = _dedupe_evidence(general_evidence)[:8]

    return {
        "chunks": rag_chunks,
        "evidence_by_key_point": evidence_by_key_point,
        "general_evidence": general_evidence,
    }


def _normalize_evidence(hit: dict[str, Any]) -> dict[str, Any]:
    return {
        "file_id": str(hit.get("file_id", "")),
        "file_name": str(hit.get("file_name", "")),
        "page_or_slide": str(hit.get("page_or_slide", "")),
        "chunk_index": int(hit.get("chunk_index", 0) or 0),
        "score": float(hit.get("score", 0.0) or 0.0),
        "snippet": str(hit.get("snippet", hit.get("text", ""))),
    }


def _dedupe_evidence(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, int, str]] = set()
    output: list[dict[str, Any]] = []
    for item in items:
        key = (
            item.get("file_id", ""),
            item.get("page_or_slide", ""),
            int(item.get("chunk_index", 0) or 0),
            item.get("snippet", "")[:80],
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def _attach_page_evidence(
    slides_json: dict,
    intent: dict,
    evidence_by_key_point: dict[str, list[dict[str, Any]]],
    general_evidence: list[dict[str, Any]],
) -> dict:
    if not isinstance(slides_json, dict):
        return slides_json

    pages = slides_json.get("pages")
    if not isinstance(pages, list):
        return slides_json

    key_points = [str(item) for item in (intent.get("key_points") or []) if str(item).strip()]

    for page in pages:
        if not isinstance(page, dict):
            continue

        title = str(page.get("title", ""))
        matched_key = ""
        for kp in key_points:
            if kp and (kp in title or title in kp):
                matched_key = kp
                break

        evidence = evidence_by_key_point.get(matched_key) if matched_key else None
        if not evidence:
            evidence = general_evidence

        page["evidence"] = evidence[:3] if isinstance(evidence, list) else []

    meta = slides_json.get("meta")
    if not isinstance(meta, dict):
        meta = {}
    meta["source_evidence_count"] = len(general_evidence)
    slides_json["meta"] = meta
    return slides_json


def _extract_teaching_patterns(intent: dict, slides_json: dict) -> str:
    topic = intent.get("topic", "")
    audience = intent.get("audience", "")
    style = intent.get("style", "")
    pages = slides_json.get("pages", [])

    type_counts: dict[str, int] = {}
    for page in pages:
        page_type = page.get("type", "content")
        type_counts[page_type] = type_counts.get(page_type, 0) + 1

    structure = " -> ".join([p.get("type", "content") for p in pages[:5]])

    return (
        "鏁欏妯″紡:\n"
        f"- audience: {audience}\n"
        f"- style: {style}\n"
        f"- structure: {structure}\n"
        f"- type_distribution: {type_counts}\n"
        f"- page_count: {len(pages)}\n\n"
        f"suitable_scene: {topic}"
    )


def _learn_from_generation(intent: dict, slides_json: dict):
    try:
        kb = get_knowledge_store()
        topic = intent.get("topic", "")
        audience = intent.get("audience", "")
        style = intent.get("style", "")

        pattern = _extract_teaching_patterns(intent, slides_json)

        tags = [audience, style, "teaching-pattern"]
        metadata = {
            "topic": topic,
            "page_count": len(slides_json.get("pages", [])),
            "generated_at": intent.get("generated_at", ""),
        }

        return kb.add_or_update(
            topic=f"{topic} - {audience} teaching-pattern",
            content=pattern,
            tags=tags,
            metadata=metadata,
        )
    except Exception as exc:
        print(f"[Knowledge] learning failed: {exc}")
        return None


def _retrieve_teaching_knowledge(intent: dict) -> str:
    try:
        kb = get_knowledge_store()
        topic = intent.get("topic", "")
        audience = intent.get("audience", "")

        results = kb.retrieve(f"{topic} {audience}", top_k=3)
        if not results:
            return ""

        chunks = ["\n\n[Compound knowledge context]"]
        for idx, entry in enumerate(results, start=1):
            chunks.append(
                f"\n{idx}. {entry['topic']} (updated {entry['update_count']} times)\n"
                f"{entry['content'][:300]}..."
            )
        return "".join(chunks)
    except Exception as exc:
        print(f"[Knowledge] retrieval failed: {exc}")
        return ""
