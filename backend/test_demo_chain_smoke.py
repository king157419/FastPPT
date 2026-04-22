"""Smoke test for contest demo core chain (health/chat/generate/revise)."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

import main as backend_main
from api import chat as chat_api
from api import generate as generate_api


def _write_dummy_file(path: str, content: bytes) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return str(p)


def test_demo_chain_smoke(monkeypatch, tmp_path):
    monkeypatch.setenv("CONTEST_FORCE_PLAIN", "true")
    monkeypatch.setenv("ENABLE_AGENT", "false")
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("RAGFLOW_BASE_URL", raising=False)
    monkeypatch.delenv("RAGFLOW_API_KEY", raising=False)
    monkeypatch.delenv("RAGFLOW_KB_ID", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)

    monkeypatch.setattr(chat_api, "chat_with_claude", lambda _messages: "你好，已收集需求")

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

    client = TestClient(backend_main.app)

    health = client.get("/health")
    assert health.status_code == 200
    health_payload = health.json()
    assert health_payload["chat_mode"] == "plain"
    assert health_payload["agent_enabled"] is False

    chat_resp = client.post(
        "/api/chat",
        json={
            "messages": [{"role": "user", "content": "我要一份光合作用课件"}],
            "stream": False,
            "use_agent": True,
        },
    )
    assert chat_resp.status_code == 200
    chat_payload = chat_resp.json()
    assert chat_payload["agent_mode"] is False

    intent = {
        "topic": "光合作用",
        "teaching_goal": "理解并应用",
        "audience": "高中生",
        "difficulty_focus": "重点难点",
        "key_points": ["过程", "影响因素"],
    }
    gen_resp = client.post("/api/generate", json={"intent": intent, "file_ids": []})
    assert gen_resp.status_code == 200
    gen_payload = gen_resp.json()
    assert gen_payload["pptx"].endswith(".pptx")
    assert gen_payload["docx"].endswith(".docx")

    revise_resp = client.post(
        "/api/generate/revise",
        json={
            "intent": intent,
            "slides_json": gen_payload["slides_json"],
            "instruction": "第1页增加课堂互动问题",
            "page_indexes": [1],
        },
    )
    assert revise_resp.status_code == 200
    revise_payload = revise_resp.json()
    assert revise_payload["pptx"].endswith(".pptx")
    assert revise_payload["slides_json"]["pages"]
