"""Generation and revise orchestration service."""
from __future__ import annotations

import asyncio
import json
import os
import uuid
from functools import partial
from typing import Any

from core import rag
from core import source_index
from core.compound_knowledge import get_knowledge_store
from core.doc_gen import generate_docx
from core.llm import generate_slides_json, revise_slides_json
from core.ppt_gen import generate_pptx_from_slides_json
from core.slide_blocks import attach_blocks_to_slides_json
from core.slide_pipeline import (
    apply_revision_patch,
    build_revision_patch,
    build_slide_plan,
    generate_slide_drafts,
)
from core.teaching_spec import compile_teaching_spec


OUTPUT_DIR = "outputs"
_jobs: dict[str, dict[str, Any]] = {}


class ServiceValidationError(ValueError):
    """Raised when request payload is semantically invalid."""


def create_generate_job(intent: dict, file_ids: list[str]) -> str:
    spec = compile_teaching_spec(intent)
    missing = spec.missing_preflight_labels()
    if missing:
        raise ServiceValidationError(f"Missing required fields: {', '.join(missing)}")

    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "message": "Preparing...",
        "slides_json": None,
        "pptx": None,
        "docx": None,
        "teaching_spec": None,
        "slide_plan": None,
        "slide_drafts": None,
        "block_summary": None,
        "compound_factor": 0.0,
        "mode_a": {"enabled": False, "outline_size": 0, "source_file": ""},
        "error": None,
    }
    return job_id


def get_job(job_id: str) -> dict[str, Any] | None:
    return _jobs.get(job_id)


def generate_courseware(intent: dict, file_ids: list[str]) -> dict[str, Any]:
    spec = compile_teaching_spec(intent)
    missing = spec.missing_preflight_labels()
    if missing:
        raise ServiceValidationError(f"Missing required fields: {', '.join(missing)}")

    effective_intent = spec.to_intent()
    mode_a_info = _apply_reference_outline_context(effective_intent, file_ids)

    knowledge_context = _retrieve_teaching_knowledge(effective_intent)
    if knowledge_context:
        effective_intent["knowledge_context"] = knowledge_context

    rag_bundle = _collect_rag_and_evidence(effective_intent, file_ids)
    rag_chunks = rag_bundle["chunks"]
    slide_plan = build_slide_plan(spec, effective_intent)

    slides_json_raw, slide_drafts = generate_slide_drafts(
        spec=spec,
        intent=effective_intent,
        rag_chunks=rag_chunks,
        slide_plan=slide_plan,
        generator=generate_slides_json,
    )

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

    generate_pptx_from_slides_json(effective_intent, slides_json, pptx_path)
    generate_docx(
        effective_intent,
        rag_chunks,
        docx_path,
        evidence_entries=rag_bundle["general_evidence"],
    )

    return {
        "slides_json": slides_json,
        "pptx": pptx_name,
        "docx": docx_name,
        "message": f"Generation succeeded, total {len(slides_json.get('pages', []))} pages",
        "teaching_spec": spec.to_dict(),
        "slide_plan": [item.to_dict() for item in slide_plan],
        "slide_drafts": [item.to_dict() for item in slide_drafts],
        "block_summary": block_summary,
        "compound_factor": compound_factor,
        "mode_a": mode_a_info,
    }


async def run_generate_job(job_id: str, intent: dict, file_ids: list[str]) -> None:
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
            raise ServiceValidationError(f"Missing required fields: {', '.join(missing)}")

        effective_intent = spec.to_intent()
        _jobs[job_id]["teaching_spec"] = spec.to_dict()

        loop = asyncio.get_event_loop()

        update(5, "Resolving reference structure...")
        mode_a_info = await loop.run_in_executor(None, _apply_reference_outline_context, effective_intent, file_ids)
        _jobs[job_id]["mode_a"] = mode_a_info
        slide_plan = build_slide_plan(spec, effective_intent)
        _jobs[job_id]["slide_plan"] = [item.to_dict() for item in slide_plan]

        update(10, "Retrieving compound knowledge...")
        knowledge_context = await loop.run_in_executor(None, _retrieve_teaching_knowledge, effective_intent)
        if knowledge_context:
            effective_intent["knowledge_context"] = knowledge_context

        update(20, "Collecting retrieval context...")
        rag_bundle = await loop.run_in_executor(None, _collect_rag_and_evidence, effective_intent, file_ids)

        update(40, "Generating slide JSON...")
        draft_fn = partial(
            generate_slide_drafts,
            spec=spec,
            intent=effective_intent,
            rag_chunks=rag_bundle["chunks"],
            slide_plan=slide_plan,
            generator=generate_slides_json,
        )
        slides_json_raw, slide_drafts = await loop.run_in_executor(None, draft_fn)
        _jobs[job_id]["slide_drafts"] = [item.to_dict() for item in slide_drafts]

        update(55, "Attaching source evidence...")
        attach_fn = partial(
            _attach_page_evidence,
            slides_json_raw,
            effective_intent,
            rag_bundle["evidence_by_key_point"],
            rag_bundle["general_evidence"],
        )
        slides_with_evidence = await loop.run_in_executor(None, attach_fn)

        update(65, "Normalizing block schema...")
        slides_json, block_summary = await loop.run_in_executor(None, attach_blocks_to_slides_json, slides_with_evidence)

        update(75, "Learning from output pattern...")
        learn_result = await loop.run_in_executor(None, _learn_from_generation, effective_intent, slides_json)
        compound_factor = learn_result.get("compound_factor", 0.0) if learn_result else 0.0

        update(85, "Exporting PPT and DOC...")
        pptx_name = f"{job_id}_courseware.pptx"
        pptx_path = os.path.join(OUTPUT_DIR, pptx_name)
        docx_name = f"{job_id}_lesson_plan.docx"
        docx_path = os.path.join(OUTPUT_DIR, docx_name)

        await loop.run_in_executor(None, generate_pptx_from_slides_json, effective_intent, slides_json, pptx_path)
        docx_fn = partial(
            generate_docx,
            effective_intent,
            rag_bundle["chunks"],
            docx_path,
            evidence_entries=rag_bundle["general_evidence"],
        )
        await loop.run_in_executor(None, docx_fn)

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


def revise_courseware(
    intent: dict,
    slides_json: dict,
    instruction: str,
    page_indexes: list[int] | None = None,
) -> dict[str, Any]:
    text = (instruction or "").strip()
    if not text:
        raise ServiceValidationError("instruction cannot be empty")

    spec = compile_teaching_spec(intent or {})
    effective_intent = spec.to_intent()

    revised = revise_slides_json(
        original_slides_json=slides_json,
        instruction=text,
        intent=effective_intent,
        page_indexes=page_indexes or [],
    )
    revision_patch = build_revision_patch(
        original_slides_json=slides_json,
        revised_slides_json=revised,
        instruction=text,
        page_indexes=page_indexes or [],
    )
    patched = apply_revision_patch(slides_json, revision_patch)
    revised, block_summary = attach_blocks_to_slides_json(patched)

    job_id = str(uuid.uuid4())[:8]
    pptx_name = f"{job_id}_revised_courseware.pptx"
    pptx_path = os.path.join(OUTPUT_DIR, pptx_name)
    generate_pptx_from_slides_json(effective_intent, revised, pptx_path)

    return {
        "slides_json": revised,
        "pptx": pptx_name,
        "message": "Revision completed and exported",
        "teaching_spec": spec.to_dict(),
        "revision_patch": revision_patch.to_dict(),
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
        "Teaching pattern summary:\n"
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
