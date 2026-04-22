"""Regression tests for generation/revision API contracts."""
from __future__ import annotations

import asyncio
from pathlib import Path

from api import generate as generate_api


def _write_dummy_file(path: str, content: bytes) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return str(p)


def test_generate_returns_pptx_and_docx(monkeypatch, tmp_path):
    monkeypatch.setattr(generate_api, "OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(generate_api, "_collect_rag", lambda _intent: [])
    monkeypatch.setattr(generate_api, "_retrieve_teaching_knowledge", lambda _intent: "")
    monkeypatch.setattr(generate_api, "_learn_from_generation", lambda _intent, _slides: {"compound_factor": 1.0})
    monkeypatch.setattr(
        generate_api,
        "generate_slides_json",
        lambda _intent, _rag: {
            "theme": {"primary": "#0f172a", "accent": "#60a5fa", "text": "#f8fafc"},
            "pages": [{"type": "content", "title": "测试页", "bullets": ["要点一", "要点二"]}],
        },
    )
    monkeypatch.setattr(
        generate_api,
        "generate_pptx_from_slides_json",
        lambda _intent, _slides, output_path: _write_dummy_file(output_path, b"pptx"),
    )
    monkeypatch.setattr(
        generate_api,
        "generate_docx",
        lambda _intent, _rag, output_path, evidence_entries=None: _write_dummy_file(output_path, b"docx"),
    )

    req = generate_api.GenerateRequest(
        intent={
            "topic": "测试主题",
            "teaching_goal": "理解并应用",
            "audience": "本科生",
            "difficulty_focus": "重点难点",
            "key_points": ["A", "B"],
        },
        file_ids=[],
    )

    result = generate_api.generate(req)

    assert result["pptx"].endswith(".pptx")
    assert result["docx"].endswith(".docx")
    assert (tmp_path / result["pptx"]).exists()
    assert (tmp_path / result["docx"]).exists()
    assert result["slides_json"]["pages"]
    assert isinstance(result["slide_plan"], list)
    assert result["slide_plan"][0]["slide_type"] == "cover"
    assert isinstance(result["slide_drafts"], list)
    assert result["slides_json"]["meta"]["pipeline"]["stage"] == "SlideDraft"


def test_revise_returns_updated_slides_and_pptx(monkeypatch, tmp_path):
    monkeypatch.setattr(generate_api, "OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(
        generate_api,
        "revise_slides_json",
        lambda original_slides_json, instruction, intent, page_indexes: {
            **original_slides_json,
            "pages": [
                {
                    "type": "content",
                    "title": "修改后页面",
                    "bullets": [f"已执行修改：{instruction}"],
                }
            ],
        },
    )
    monkeypatch.setattr(
        generate_api,
        "generate_pptx_from_slides_json",
        lambda _intent, _slides, output_path: _write_dummy_file(output_path, b"pptx"),
    )

    req = generate_api.ReviseRequest(
        intent={
            "topic": "测试主题",
            "teaching_goal": "理解并应用",
            "audience": "本科生",
            "difficulty_focus": "重点难点",
        },
        slides_json={
            "theme": {"primary": "#0f172a", "accent": "#60a5fa", "text": "#f8fafc"},
            "pages": [{"type": "content", "title": "原始页", "bullets": ["原始要点"]}],
        },
        instruction="增加一个案例并简化文字",
        page_indexes=[1],
    )

    result = generate_api.revise(req)

    assert result["pptx"].endswith(".pptx")
    assert (tmp_path / result["pptx"]).exists()
    assert result["slides_json"]["pages"][0]["title"] == "修改后页面"
    assert result["block_summary"]["total_pages"] == 1
    assert result["revision_patch"]["operations"]
    assert result["slides_json"]["meta"]["pipeline"]["stage"] == "RevisionPatch"


def test_async_generate_builds_slide_plan_after_mode_a_outline(monkeypatch, tmp_path):
    monkeypatch.setattr(generate_api, "OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(generate_api, "_retrieve_teaching_knowledge", lambda _intent: "")
    monkeypatch.setattr(generate_api, "_learn_from_generation", lambda _intent, _slides: {"compound_factor": 1.0})
    monkeypatch.setattr(
        generate_api,
        "_collect_rag_and_evidence",
        lambda _intent, _file_ids: {"chunks": [], "evidence_by_key_point": {}, "general_evidence": []},
    )

    def fake_mode_a(intent, _file_ids):
        intent["preserve_structure"] = True
        intent["reference_outline"] = ["旧目录A", "旧目录B"]
        return {"enabled": True, "outline_size": 2, "source_file": "old.pptx"}

    captured_plan = {"items": None}

    def fake_generate_slide_drafts(spec, intent, rag_chunks, slide_plan, generator):
        _ = spec, intent, rag_chunks, generator
        captured_plan["items"] = [item.to_dict() for item in slide_plan]
        return (
            {
                "theme": {"primary": "#0f172a", "accent": "#60a5fa", "text": "#f8fafc"},
                "pages": [{"type": "content", "title": "测试", "bullets": ["a"]}],
            },
            [],
        )

    monkeypatch.setattr(generate_api, "_apply_reference_outline_context", fake_mode_a)
    monkeypatch.setattr(generate_api, "generate_slide_drafts", fake_generate_slide_drafts)
    monkeypatch.setattr(
        generate_api,
        "generate_pptx_from_slides_json",
        lambda _intent, _slides, output_path: _write_dummy_file(output_path, b"pptx"),
    )
    monkeypatch.setattr(
        generate_api,
        "generate_docx",
        lambda _intent, _rag, output_path, evidence_entries=None: _write_dummy_file(output_path, b"docx"),
    )

    job_id = "job_async_order"
    generate_api._jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "message": "",
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

    intent = {
        "topic": "测试主题",
        "teaching_goal": "理解并应用",
        "audience": "本科生",
        "difficulty_focus": "重点难点",
        "key_points": ["默认A", "默认B"],
    }
    asyncio.run(generate_api._run_generate(job_id, intent, ["file1"]))

    assert generate_api._jobs[job_id]["status"] == "done"
    assert captured_plan["items"] is not None
    content_titles = [item["title"] for item in captured_plan["items"] if item["slide_type"] == "content"]
    assert content_titles[:2] == ["旧目录A", "旧目录B"]
