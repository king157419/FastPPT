"""Tests for Mode A structure preservation and per-page evidence attachment."""
from __future__ import annotations

from pathlib import Path

from api import generate as generate_api
from core import source_index


def _write_dummy_file(path: str, content: bytes) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return str(p)


def test_generate_injects_mode_a_reference_outline(monkeypatch, tmp_path):
    source_index.reset_all()
    monkeypatch.setattr(generate_api, "OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(generate_api, "_retrieve_teaching_knowledge", lambda _intent: "")
    monkeypatch.setattr(generate_api, "_learn_from_generation", lambda _intent, _slides: {"compound_factor": 1.0})
    monkeypatch.setattr(generate_api, "_collect_rag", lambda _intent: ["chunk-a"])  # keep retrieval deterministic

    captured_intent = {}

    def fake_generate_slides_json(intent, rag_chunks):
        captured_intent.update(intent)
        return {
            "theme": {"primary": "#0f172a", "accent": "#60a5fa", "text": "#f8fafc"},
            "pages": [
                {"type": "cover", "title": "封面", "subtitle": "s"},
                {"type": "content", "title": "第一章", "bullets": ["b1", "b2", "b3"]},
                {"type": "summary", "title": "总结", "takeaways": ["t1", "t2"]},
            ],
        }

    monkeypatch.setattr(generate_api, "generate_slides_json", fake_generate_slides_json)
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

    file_id = "ppt001"
    source_index.register_file(file_id, "old-course.pptx", str(tmp_path / "old-course.pptx"), ".pptx")
    source_index.update_outline(file_id, ["第一章", "第二章", "第三章"])
    source_index.add_chunks(
        file_id,
        [
            {"text": "第一章 定义和背景", "metadata": {"page_or_slide": "slide-1", "chunk_index": 0}},
            {"text": "第二章 原理和推导", "metadata": {"page_or_slide": "slide-2", "chunk_index": 1}},
        ],
    )

    req = generate_api.GenerateRequest(
        intent={
            "topic": "测试主题",
            "teaching_goal": "理解并应用",
            "audience": "本科生",
            "difficulty_focus": "重点难点",
            "key_points": ["第一章", "第二章"],
        },
        file_ids=[file_id],
    )

    result = generate_api.generate(req)

    assert captured_intent.get("preserve_structure") is True
    assert captured_intent.get("reference_outline") == ["第一章", "第二章", "第三章"]
    assert result["mode_a"]["enabled"] is True
    assert result["mode_a"]["outline_size"] == 3


def test_generate_attaches_page_evidence(monkeypatch, tmp_path):
    source_index.reset_all()
    monkeypatch.setattr(generate_api, "OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(generate_api, "_retrieve_teaching_knowledge", lambda _intent: "")
    monkeypatch.setattr(generate_api, "_learn_from_generation", lambda _intent, _slides: {"compound_factor": 1.0})
    monkeypatch.setattr(generate_api, "_collect_rag", lambda _intent: ["chunk-a", "chunk-b"])
    monkeypatch.setattr(
        generate_api,
        "generate_slides_json",
        lambda _intent, _rag: {
            "theme": {"primary": "#0f172a", "accent": "#60a5fa", "text": "#f8fafc"},
            "pages": [
                {"type": "content", "title": "第一章", "bullets": ["a", "b", "c"]},
                {"type": "content", "title": "第二章", "bullets": ["x", "y", "z"]},
            ],
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

    file_id = "doc001"
    source_index.register_file(file_id, "material.pdf", str(tmp_path / "material.pdf"), ".pdf")
    source_index.add_chunks(
        file_id,
        [
            {"text": "第一章 关键定义与背景", "metadata": {"page_or_slide": "page-1", "chunk_index": 0}},
            {"text": "第二章 推导过程和案例", "metadata": {"page_or_slide": "page-2", "chunk_index": 1}},
        ],
    )

    req = generate_api.GenerateRequest(
        intent={
            "topic": "测试主题",
            "teaching_goal": "理解并应用",
            "audience": "本科生",
            "difficulty_focus": "重点难点",
            "key_points": ["第一章", "第二章"],
        },
        file_ids=[file_id],
    )

    result = generate_api.generate(req)
    pages = result["slides_json"]["pages"]

    assert isinstance(pages[0].get("evidence"), list)
    assert len(pages[0]["evidence"]) >= 1
    assert pages[0]["evidence"][0]["file_name"] == "material.pdf"
