"""End-to-end smoke test: upload -> chat -> generate -> revise."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

import main as backend_main
from api import chat as chat_api
from api import generate as generate_api
from core import source_index


def _write_dummy_file(path: str, content: bytes) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return str(p)


def test_full_chain_upload_chat_generate_revise(monkeypatch, tmp_path):
    source_index.reset_all()
    monkeypatch.setenv("ENABLE_AGENT", "false")
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setattr(generate_api, "OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(generate_api, "_retrieve_teaching_knowledge", lambda _intent: "")
    monkeypatch.setattr(generate_api, "_learn_from_generation", lambda _intent, _slides: {"compound_factor": 1.0})
    monkeypatch.setattr(chat_api, "chat_with_claude", lambda _messages: "已记录需求")
    monkeypatch.setattr(
        generate_api,
        "generate_slides_json",
        lambda _intent, _rag: {
            "theme": {"primary": "#0f172a", "accent": "#60a5fa", "text": "#f8fafc"},
            "pages": [
                {"type": "content", "title": "光合作用过程", "bullets": ["步骤", "条件", "意义"]},
                {"type": "summary", "title": "课堂总结", "takeaways": ["核心过程", "影响因素"]},
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

    client = TestClient(backend_main.app)

    upload_resp = client.post(
        "/api/upload",
        files={"file": ("notes.txt", "光合作用 过程 影响因素 与课堂实验".encode("utf-8"), "text/plain")},
    )
    assert upload_resp.status_code == 200
    file_id = upload_resp.json()["file_id"]
    assert file_id

    chat_resp = client.post(
        "/api/chat",
        json={
            "messages": [{"role": "user", "content": "我要一节光合作用课程"}],
            "stream": False,
            "use_agent": True,
        },
    )
    assert chat_resp.status_code == 200
    assert chat_resp.json()["agent_mode"] is False

    intent = {
        "topic": "光合作用",
        "teaching_goal": "理解并应用",
        "audience": "高中生",
        "difficulty_focus": "重点难点",
        "key_points": ["过程", "影响因素"],
        "duration": "45分钟",
        "style": "结构化讲解",
    }
    generate_resp = client.post("/api/generate", json={"intent": intent, "file_ids": [file_id]})
    assert generate_resp.status_code == 200
    payload = generate_resp.json()
    assert payload["pptx"].endswith(".pptx")
    assert payload["docx"].endswith(".docx")
    assert payload["mode_a"]["enabled"] is False
    assert payload["slides_json"]["pages"]
    assert isinstance(payload["slides_json"]["pages"][0].get("evidence"), list)

    revise_resp = client.post(
        "/api/generate/revise",
        json={
            "intent": intent,
            "slides_json": payload["slides_json"],
            "instruction": "第1页增加课堂互动提问",
            "page_indexes": [1],
        },
    )
    assert revise_resp.status_code == 200
    revise_payload = revise_resp.json()
    assert revise_payload["pptx"].endswith(".pptx")
    assert revise_payload["slides_json"]["pages"]
