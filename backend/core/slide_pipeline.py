"""Pipeline primitives for TeachingSpec -> SlidePlan -> SlideDraft -> RevisionPatch."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Callable

from core.teaching_spec import TeachingSpec


@dataclass
class SlidePlanItem:
    slide_id: str
    title: str
    slide_type: str
    objective: str
    key_point: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SlideDraft:
    slide_id: str
    slide_type: str
    title: str
    content: dict[str, Any]
    evidence: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RevisionOperation:
    op: str
    slide_id: str
    slide_index: int
    before: dict[str, Any]
    after: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RevisionPatch:
    patch_id: str
    instruction: str
    target_slide_ids: list[str]
    operations: list[RevisionOperation]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["operations"] = [item.to_dict() for item in self.operations]
        return data


def _plan_item(slide_index: int, title: str, slide_type: str, objective: str, key_point: str = "") -> SlidePlanItem:
    return SlidePlanItem(
        slide_id=f"s{slide_index:02d}",
        title=title,
        slide_type=slide_type,
        objective=objective,
        key_point=key_point,
    )


def build_slide_plan(spec: TeachingSpec, intent: dict[str, Any]) -> list[SlidePlanItem]:
    """Build a deterministic slide plan from teaching spec and mode-A hints."""
    key_points = [item for item in spec.key_points if item]
    reference_outline = [str(item).strip() for item in (intent.get("reference_outline") or []) if str(item).strip()]
    ordered_points = reference_outline[:10] if intent.get("preserve_structure") and reference_outline else key_points[:10]
    if not ordered_points:
        ordered_points = ["核心概念", "关键原理", "课堂应用"]

    plan: list[SlidePlanItem] = []
    plan.append(_plan_item(1, spec.topic, "cover", f"面向{spec.audience}的课程导入"))
    plan.append(_plan_item(2, "课程导航", "agenda", "明确本节课结构与学习路线"))

    next_index = 3
    for kp in ordered_points:
        plan.append(
            _plan_item(
                next_index,
                kp,
                "content",
                f"解释“{kp}”并围绕重点难点展开",
                key_point=kp,
            )
        )
        next_index += 1

    plan.append(_plan_item(next_index, "课堂小结", "summary", spec.teaching_goal))
    return plan


def _inject_plan_into_intent(intent: dict[str, Any], slide_plan: list[SlidePlanItem]) -> dict[str, Any]:
    enriched = deepcopy(intent)
    enriched["slide_plan"] = [item.to_dict() for item in slide_plan]
    enriched["pipeline_version"] = "slide-pipeline.v1"
    return enriched


def _resolve_slide_id(page: dict[str, Any], index: int, slide_plan: list[SlidePlanItem]) -> str:
    existing = str(page.get("slide_id") or "").strip()
    if existing:
        return existing
    if 0 <= index < len(slide_plan):
        return slide_plan[index].slide_id
    return f"s{index + 1:02d}"


def generate_slide_drafts(
    spec: TeachingSpec,
    intent: dict[str, Any],
    rag_chunks: list[str],
    slide_plan: list[SlidePlanItem],
    generator: Callable[[dict[str, Any], list[str]], dict[str, Any]],
) -> tuple[dict[str, Any], list[SlideDraft]]:
    """Generate slides_json and map pages into SlideDraft objects."""
    enriched_intent = _inject_plan_into_intent(intent, slide_plan)
    slides_json = deepcopy(generator(enriched_intent, rag_chunks) or {})
    pages = slides_json.get("pages")
    if not isinstance(pages, list):
        pages = []
        slides_json["pages"] = pages

    drafts: list[SlideDraft] = []
    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            continue
        slide_id = _resolve_slide_id(page, index, slide_plan)
        page["slide_id"] = slide_id

        # Keep plan context on each page for downstream revise and export.
        if 0 <= index < len(slide_plan):
            page.setdefault(
                "plan",
                {
                    "objective": slide_plan[index].objective,
                    "key_point": slide_plan[index].key_point,
                    "slide_type": slide_plan[index].slide_type,
                },
            )

        content = {
            "title": page.get("title", ""),
            "bullets": page.get("bullets") or page.get("takeaways") or [],
            "tip": page.get("tip", ""),
        }
        evidence = page.get("evidence")
        if not isinstance(evidence, list):
            evidence = []
        drafts.append(
            SlideDraft(
                slide_id=slide_id,
                slide_type=str(page.get("type") or "content"),
                title=str(page.get("title") or ""),
                content=content,
                evidence=evidence,
            )
        )

    meta = slides_json.get("meta")
    if not isinstance(meta, dict):
        meta = {}
    meta["pipeline"] = {
        "version": "slide-pipeline.v1",
        "stage": "SlideDraft",
        "teaching_spec": spec.to_dict(),
        "plan_size": len(slide_plan),
        "draft_size": len(drafts),
    }
    slides_json["meta"] = meta
    return slides_json, drafts


def build_revision_patch(
    original_slides_json: dict[str, Any],
    revised_slides_json: dict[str, Any],
    instruction: str,
    page_indexes: list[int] | None = None,
) -> RevisionPatch:
    original_pages = original_slides_json.get("pages")
    revised_pages = revised_slides_json.get("pages")
    if not isinstance(original_pages, list):
        original_pages = []
    if not isinstance(revised_pages, list):
        revised_pages = []

    target_index_set = {idx for idx in (page_indexes or []) if isinstance(idx, int) and idx > 0}
    target_slide_ids: list[str] = []
    operations: list[RevisionOperation] = []

    total = max(len(original_pages), len(revised_pages))
    for zero_index in range(total):
        original_page = original_pages[zero_index] if zero_index < len(original_pages) and isinstance(original_pages[zero_index], dict) else {}
        revised_page = revised_pages[zero_index] if zero_index < len(revised_pages) and isinstance(revised_pages[zero_index], dict) else {}
        one_index = zero_index + 1
        if target_index_set and one_index not in target_index_set:
            continue
        if original_page == revised_page:
            continue

        slide_id = str(revised_page.get("slide_id") or original_page.get("slide_id") or f"s{one_index:02d}")
        target_slide_ids.append(slide_id)
        operations.append(
            RevisionOperation(
                op="replace_slide",
                slide_id=slide_id,
                slide_index=one_index,
                before=deepcopy(original_page),
                after=deepcopy(revised_page),
            )
        )

    raw = json.dumps(
        {
            "instruction": instruction,
            "target_slide_ids": target_slide_ids,
            "operations": [item.to_dict() for item in operations],
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    patch_id = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return RevisionPatch(
        patch_id=f"rp-{patch_id}",
        instruction=instruction,
        target_slide_ids=target_slide_ids,
        operations=operations,
    )


def apply_revision_patch(slides_json: dict[str, Any], patch: RevisionPatch) -> dict[str, Any]:
    data = deepcopy(slides_json or {})
    pages = data.get("pages")
    if not isinstance(pages, list):
        pages = []
        data["pages"] = pages

    for op in patch.operations:
        target_zero = op.slide_index - 1
        if target_zero < 0:
            continue
        while target_zero >= len(pages):
            pages.append({})
        pages[target_zero] = deepcopy(op.after)

    meta = data.get("meta")
    if not isinstance(meta, dict):
        meta = {}
    revisions = meta.get("revisions")
    if not isinstance(revisions, list):
        revisions = []
    revisions.append(
        {
            "patch_id": patch.patch_id,
            "instruction": patch.instruction,
            "target_slide_ids": list(patch.target_slide_ids),
            "operation_count": len(patch.operations),
        }
    )
    meta["revisions"] = revisions
    meta["pipeline"] = {
        "version": "slide-pipeline.v1",
        "stage": "RevisionPatch",
        "last_patch_id": patch.patch_id,
    }
    data["meta"] = meta
    return data

