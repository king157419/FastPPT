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
    from_index: int | None = None
    to_index: int | None = None

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

    original_pages = _ensure_slide_ids(original_pages)
    revised_pages = _ensure_slide_ids_with_fallback(original_pages, revised_pages)
    original_pages = _normalize_unique_slide_ids(original_pages, "o")
    revised_pages = _normalize_unique_slide_ids(revised_pages, "r")

    target_index_set = {idx for idx in (page_indexes or []) if isinstance(idx, int) and idx > 0}
    target_slide_ids: list[str] = []
    operations: list[RevisionOperation] = []
    original_map = _index_by_slide_id(original_pages)
    revised_map = _index_by_slide_id(revised_pages)

    if target_index_set:
        allowed_ids: set[str] = set()
        for idx in target_index_set:
            zero_index = idx - 1
            if 0 <= zero_index < len(revised_pages):
                allowed_ids.add(str(revised_pages[zero_index].get("slide_id")))
            if 0 <= zero_index < len(original_pages):
                allowed_ids.add(str(original_pages[zero_index].get("slide_id")))
    else:
        allowed_ids = set(original_map.keys()) | set(revised_map.keys())

    # Deletions first so downstream application can re-index cleanly.
    deleted_ids = sorted([sid for sid in original_map.keys() if sid not in revised_map and sid in allowed_ids], key=lambda sid: original_map[sid][0], reverse=True)
    for slide_id in deleted_ids:
        original_index, original_page = original_map[slide_id]
        target_slide_ids.append(slide_id)
        operations.append(
            RevisionOperation(
                op="delete_slide",
                slide_id=slide_id,
                slide_index=original_index + 1,
                before=deepcopy(original_page),
                after={},
                from_index=original_index + 1,
                to_index=None,
            )
        )

    # Moves and replacements for existing slide ids.
    for slide_id in sorted([sid for sid in revised_map.keys() if sid in original_map and sid in allowed_ids], key=lambda sid: revised_map[sid][0]):
        revised_index, revised_page = revised_map[slide_id]
        original_index, original_page = original_map[slide_id]
        one_index = revised_index + 1

        if original_index != revised_index:
            target_slide_ids.append(slide_id)
            operations.append(
                RevisionOperation(
                    op="move_slide",
                    slide_id=slide_id,
                    slide_index=one_index,
                    before=deepcopy(original_page),
                    after=deepcopy(revised_page),
                    from_index=original_index + 1,
                    to_index=revised_index + 1,
                )
            )

        if original_page != revised_page:
            target_slide_ids.append(slide_id)
            operations.append(
                RevisionOperation(
                    op="replace_slide",
                    slide_id=slide_id,
                    slide_index=one_index,
                    before=deepcopy(original_page),
                    after=deepcopy(revised_page),
                    from_index=original_index + 1,
                    to_index=revised_index + 1,
                )
            )

    # Additions last.
    for slide_id in sorted([sid for sid in revised_map.keys() if sid not in original_map and sid in allowed_ids], key=lambda sid: revised_map[sid][0]):
        revised_index, revised_page = revised_map[slide_id]
        target_slide_ids.append(slide_id)
        operations.append(
            RevisionOperation(
                op="add_slide",
                slide_id=slide_id,
                slide_index=revised_index + 1,
                before={},
                after=deepcopy(revised_page),
                from_index=None,
                to_index=revised_index + 1,
            )
        )

    target_slide_ids = _dedupe_preserve_order(target_slide_ids)

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
        if op.op == "delete_slide":
            delete_index = _find_page_index(pages, op.slide_id)
            if delete_index is None:
                delete_index = op.slide_index - 1 if op.slide_index > 0 else None
            if delete_index is not None and 0 <= delete_index < len(pages):
                pages.pop(delete_index)
            continue

        if op.op == "move_slide":
            move_from = _find_page_index(pages, op.slide_id)
            if move_from is None:
                continue
            page_obj = pages.pop(move_from)
            target_index = (op.to_index or op.slide_index) - 1
            target_index = max(0, min(target_index, len(pages)))
            pages.insert(target_index, page_obj)
            continue

        if op.op == "add_slide":
            target_index = (op.to_index or op.slide_index) - 1
            target_index = max(0, min(target_index, len(pages)))
            pages.insert(target_index, deepcopy(op.after))
            continue

        # Default behavior for replace op and backward compatibility.
        replace_index = _find_page_index(pages, op.slide_id)
        if replace_index is None:
            replace_index = (op.to_index or op.slide_index) - 1
        if replace_index < 0:
            continue
        while replace_index >= len(pages):
            pages.append({})
        pages[replace_index] = deepcopy(op.after)

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


def _ensure_slide_ids(pages: list[Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, page in enumerate(pages, start=1):
        if not isinstance(page, dict):
            continue
        item = deepcopy(page)
        existing = str(item.get("slide_id") or "").strip()
        if not existing:
            item["slide_id"] = f"s{index:02d}"
        output.append(item)
    return output


def _ensure_slide_ids_with_fallback(
    original_pages: list[dict[str, Any]],
    revised_pages: list[Any],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, page in enumerate(revised_pages, start=1):
        if not isinstance(page, dict):
            continue
        item = deepcopy(page)
        existing = str(item.get("slide_id") or "").strip()
        if existing:
            output.append(item)
            continue

        if 0 <= index - 1 < len(original_pages):
            original_id = str(original_pages[index - 1].get("slide_id") or "").strip()
            if original_id:
                item["slide_id"] = original_id
                output.append(item)
                continue

        item["slide_id"] = f"r{index:02d}"
        output.append(item)
    return output


def _normalize_unique_slide_ids(pages: list[dict[str, Any]], prefix: str) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen_counts: dict[str, int] = {}
    for index, page in enumerate(pages, start=1):
        item = deepcopy(page)
        raw_id = str(item.get("slide_id") or "").strip()
        if not raw_id:
            raw_id = f"{prefix}{index:02d}"

        count = seen_counts.get(raw_id, 0)
        if count > 0:
            item["slide_id"] = f"{raw_id}__dup{count}"
        else:
            item["slide_id"] = raw_id
        seen_counts[raw_id] = count + 1
        normalized.append(item)
    return normalized


def _index_by_slide_id(pages: list[dict[str, Any]]) -> dict[str, tuple[int, dict[str, Any]]]:
    output: dict[str, tuple[int, dict[str, Any]]] = {}
    for index, page in enumerate(pages):
        slide_id = str(page.get("slide_id") or "").strip()
        if not slide_id:
            continue
        output[slide_id] = (index, page)
    return output


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def _find_page_index(pages: list[Any], slide_id: str) -> int | None:
    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            continue
        if str(page.get("slide_id") or "").strip() == slide_id:
            return index
    return None
