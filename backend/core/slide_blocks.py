"""Slide block registry and normalization helpers."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any

BLOCK_SCHEMA_VERSION = "slide-blocks.v1"


def _block(
    block_type: str,
    payload: dict[str, Any],
    *,
    layout_slot: str = "body",
    render_strategy: str = "default",
    validation_rules: list[str] | None = None,
    anchors: list[str] | None = None,
    style_hints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "type": block_type,
        "payload": payload,
        "anchors": anchors or [],
        "layoutHints": {"slot": layout_slot},
        "styleHints": style_hints or {},
        "renderStrategy": render_strategy,
        "validationRules": validation_rules or ["non_empty_payload"],
    }


def _build_cover_blocks(page: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _block("TextBlock", {"text": page.get("title", ""), "role": "title"}, layout_slot="hero"),
        _block("TextBlock", {"text": page.get("subtitle", ""), "role": "subtitle"}, layout_slot="hero"),
    ]


def _build_agenda_blocks(page: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _block("TextBlock", {"text": page.get("title", "目录"), "role": "title"}, layout_slot="header"),
        _block(
            "BulletBlock",
            {"items": page.get("items") or page.get("points") or []},
            render_strategy="agenda-list",
        ),
    ]


def _build_content_blocks(page: dict[str, Any]) -> list[dict[str, Any]]:
    blocks = [
        _block("TextBlock", {"text": page.get("title", ""), "role": "title"}, layout_slot="header"),
        _block("BulletBlock", {"items": page.get("bullets") or []}, render_strategy="numbered-bullets"),
    ]
    tip = page.get("tip")
    if tip:
        blocks.append(_block("TextBlock", {"text": tip, "role": "teaching_tip"}, layout_slot="footer"))
    return blocks


def _build_code_blocks(page: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _block("TextBlock", {"text": page.get("title", ""), "role": "title"}, layout_slot="header"),
        _block(
            "CodeBlock",
            {
                "language": page.get("language", "text"),
                "code": page.get("code", ""),
                "explanation": page.get("explanation", ""),
            },
            render_strategy="code-panel",
            validation_rules=["non_empty_payload", "max_lines_soft_limit"],
        ),
    ]


def _build_formula_blocks(page: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _block("TextBlock", {"text": page.get("title", ""), "role": "title"}, layout_slot="header"),
        _block(
            "FormulaBlock",
            {
                "formulas": page.get("formulas") or [],
                "explanation": page.get("explanation", ""),
            },
            render_strategy="formula-first",
            validation_rules=["non_empty_payload", "latex_or_fallback"],
        ),
    ]


def _build_example_blocks(page: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _block("TextBlock", {"text": page.get("title", ""), "role": "title"}, layout_slot="header"),
        _block(
            "CaseBlock",
            {
                "problem": page.get("problem", ""),
                "steps": page.get("steps") or [],
                "answer": page.get("answer", ""),
            },
            render_strategy="case-panel",
        ),
    ]


def _build_two_column_blocks(page: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _block("TextBlock", {"text": page.get("title", ""), "role": "title"}, layout_slot="header"),
        _block(
            "TableBlock",
            {
                "left": page.get("left") or {},
                "right": page.get("right") or {},
            },
            render_strategy="two-column",
        ),
    ]


def _build_image_blocks(page: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _block("TextBlock", {"text": page.get("title", ""), "role": "title"}, layout_slot="header"),
        _block(
            "ImageBlock",
            {
                "image_base64": page.get("image_base64"),
                "image_url": page.get("image_url"),
                "caption": page.get("caption", ""),
            },
            render_strategy="contain",
            validation_rules=["image_source_exists"],
        ),
    ]


def _build_quote_blocks(page: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _block(
            "TextBlock",
            {"text": page.get("text", ""), "role": "quote"},
            layout_slot="center",
            render_strategy="quote",
        )
    ]


def _build_summary_blocks(page: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _block("TextBlock", {"text": page.get("title", "总结"), "role": "title"}, layout_slot="header"),
        _block("BulletBlock", {"items": page.get("takeaways") or []}, render_strategy="checklist"),
    ]


def _build_animation_blocks(page: dict[str, Any]) -> list[dict[str, Any]]:
    template = page.get("template", "")
    if template == "flowchart":
        return [
            _block("TextBlock", {"text": page.get("title", ""), "role": "title"}, layout_slot="header"),
            _block(
                "FlowchartBlock",
                {"template": template, "template_data": page.get("template_data") or {}},
                render_strategy="iframe-template",
            ),
        ]
    return [
        _block("TextBlock", {"text": page.get("title", ""), "role": "title"}, layout_slot="header"),
        _block(
            "TextBlock",
            {"text": f"[互动动画:{template}]"},
            render_strategy="placeholder",
        ),
    ]


_PAGE_BUILDERS = {
    "cover": _build_cover_blocks,
    "agenda": _build_agenda_blocks,
    "content": _build_content_blocks,
    "code": _build_code_blocks,
    "formula": _build_formula_blocks,
    "example": _build_example_blocks,
    "two_column": _build_two_column_blocks,
    "image": _build_image_blocks,
    "quote": _build_quote_blocks,
    "summary": _build_summary_blocks,
    "animation": _build_animation_blocks,
}


def build_page_blocks(page: dict[str, Any], page_index: int) -> list[dict[str, Any]]:
    page_type = page.get("type", "content")
    builder = _PAGE_BUILDERS.get(page_type, _build_content_blocks)
    blocks = builder(page)
    for idx, item in enumerate(blocks, start=1):
        item["id"] = f"p{page_index:02d}-b{idx:02d}"
    return blocks


def attach_blocks_to_slides_json(slides_json: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    """Attach normalized block list to each page while keeping old shape intact."""
    data: dict[str, Any] = deepcopy(slides_json or {})
    pages = data.get("pages")
    if not isinstance(pages, list):
        data["pages"] = []
        summary = {"total_pages": 0, "total_blocks": 0, "block_counts": {}}
        data["meta"] = {
            "block_schema_version": BLOCK_SCHEMA_VERSION,
            "block_summary": summary,
        }
        return data, summary

    counter: Counter[str] = Counter()
    for page_index, page in enumerate(pages, start=1):
        if not isinstance(page, dict):
            continue
        blocks = build_page_blocks(page, page_index)
        page["blocks"] = blocks
        for item in blocks:
            counter[item["type"]] += 1

    summary = {
        "total_pages": len(pages),
        "total_blocks": sum(counter.values()),
        "block_counts": dict(counter),
    }

    meta = data.get("meta", {})
    if not isinstance(meta, dict):
        meta = {}
    meta["block_schema_version"] = BLOCK_SCHEMA_VERSION
    meta["block_summary"] = summary
    data["meta"] = meta

    return data, summary

