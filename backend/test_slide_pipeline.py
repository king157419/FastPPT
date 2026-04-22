"""Tests for TeachingSpec -> SlidePlan -> SlideDraft -> RevisionPatch pipeline."""
from __future__ import annotations

from core.slide_pipeline import (
    apply_revision_patch,
    build_revision_patch,
    build_slide_plan,
    generate_slide_drafts,
)
from core.teaching_spec import compile_teaching_spec


def test_build_slide_plan_uses_key_points_and_cover_summary():
    spec = compile_teaching_spec(
        {
            "topic": "函数单调性",
            "teaching_goal": "理解概念并会判断",
            "audience": "高一",
            "difficulty_focus": "定义域与区间判断",
            "key_points": ["定义", "判定方法", "例题讲解"],
        }
    )
    intent = spec.to_intent()
    plan = build_slide_plan(spec, intent)

    assert plan[0].slide_type == "cover"
    assert plan[1].slide_type == "agenda"
    assert plan[-1].slide_type == "summary"
    assert any(item.title == "定义" for item in plan)


def test_generate_slide_drafts_adds_slide_ids_and_pipeline_meta():
    spec = compile_teaching_spec(
        {
            "topic": "函数单调性",
            "teaching_goal": "理解概念并会判断",
            "audience": "高一",
            "difficulty_focus": "定义域与区间判断",
            "key_points": ["定义", "判定方法"],
        }
    )
    intent = spec.to_intent()
    plan = build_slide_plan(spec, intent)

    def fake_generator(_intent, _rag):
        return {
            "theme": {"primary": "#0f172a", "accent": "#60a5fa", "text": "#f8fafc"},
            "pages": [
                {"type": "cover", "title": "函数单调性", "subtitle": "高一 | 45分钟"},
                {"type": "content", "title": "定义", "bullets": ["a", "b"]},
                {"type": "summary", "title": "课堂小结", "takeaways": ["x"]},
            ],
        }

    slides_json, drafts = generate_slide_drafts(spec, intent, [], plan, fake_generator)
    assert len(drafts) == 3
    assert slides_json["pages"][0]["slide_id"] == "s01"
    assert slides_json["meta"]["pipeline"]["stage"] == "SlideDraft"


def test_revision_patch_replace_selected_page_only():
    original = {
        "pages": [
            {"slide_id": "s01", "type": "cover", "title": "原封面"},
            {"slide_id": "s02", "type": "content", "title": "原第二页", "bullets": ["a"]},
        ]
    }
    revised = {
        "pages": [
            {"slide_id": "s01", "type": "cover", "title": "原封面"},
            {"slide_id": "s02", "type": "content", "title": "新第二页", "bullets": ["a", "b"]},
        ]
    }
    patch = build_revision_patch(original, revised, "第2页补充要点", [2])
    assert patch.target_slide_ids == ["s02"]
    assert len(patch.operations) == 1

    patched = apply_revision_patch(original, patch)
    assert patched["pages"][1]["title"] == "新第二页"
    assert patched["meta"]["pipeline"]["stage"] == "RevisionPatch"

