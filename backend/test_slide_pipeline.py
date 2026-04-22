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


def test_revision_patch_detects_add_delete_move_with_slide_id_priority():
    original = {
        "pages": [
            {"slide_id": "s01", "type": "cover", "title": "封面"},
            {"slide_id": "s02", "type": "content", "title": "原第二页"},
            {"slide_id": "s03", "type": "content", "title": "原第三页"},
        ]
    }
    revised = {
        "pages": [
            {"slide_id": "s03", "type": "content", "title": "原第三页"},  # move to first
            {"slide_id": "s01", "type": "cover", "title": "封面（更新）"},   # move + replace
            {"slide_id": "s04", "type": "content", "title": "新增页"},      # add
        ]
    }

    patch = build_revision_patch(original, revised, "结构调整")
    op_types = [op.op for op in patch.operations]
    assert "delete_slide" in op_types
    assert "move_slide" in op_types
    assert "add_slide" in op_types
    assert "replace_slide" in op_types

    patched = apply_revision_patch(original, patch)
    assert [page["slide_id"] for page in patched["pages"]] == ["s03", "s01", "s04"]
    assert patched["pages"][1]["title"] == "封面（更新）"


def test_revision_patch_page_indexes_keeps_delete_operation():
    original = {
        "pages": [
            {"slide_id": "s01", "type": "content", "title": "第一页"},
            {"slide_id": "s02", "type": "content", "title": "第二页"},
            {"slide_id": "s03", "type": "content", "title": "第三页"},
        ]
    }
    revised = {
        "pages": [
            {"slide_id": "s01", "type": "content", "title": "第一页"},
            {"slide_id": "s03", "type": "content", "title": "第三页"},
        ]
    }

    patch = build_revision_patch(original, revised, "删除第2页", [2])
    assert any(op.op == "delete_slide" and op.slide_id == "s02" for op in patch.operations)

    patched = apply_revision_patch(original, patch)
    assert [page["slide_id"] for page in patched["pages"]] == ["s01", "s03"]


def test_revision_patch_handles_duplicate_slide_ids_safely():
    original = {
        "pages": [
            {"slide_id": "dup", "type": "content", "title": "A"},
            {"slide_id": "dup", "type": "content", "title": "B"},
        ]
    }
    revised = {
        "pages": [
            {"slide_id": "dup", "type": "content", "title": "A-更新"},
            {"slide_id": "dup", "type": "content", "title": "B"},
            {"slide_id": "dup", "type": "content", "title": "C-新增"},
        ]
    }

    patch = build_revision_patch(original, revised, "处理重复ID")
    # Should not collapse operations due to duplicated raw slide_id values.
    assert len(patch.operations) >= 2
    assert len(set(patch.target_slide_ids)) == len(patch.target_slide_ids)

    patched = apply_revision_patch(original, patch)
    assert len(patched["pages"]) == 3
