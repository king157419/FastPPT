"""Regression tests for /health runtime mode fields."""
from __future__ import annotations

import asyncio

import main as backend_main


def test_health_contains_runtime_mode_fields(monkeypatch):
    async def fake_health_check():
        return {"status": "healthy"}

    monkeypatch.setattr(backend_main, "health_check", fake_health_check)
    monkeypatch.setenv("CONTEST_FORCE_PLAIN", "true")
    monkeypatch.setenv("ENABLE_AGENT", "false")
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("RAGFLOW_BASE_URL", raising=False)
    monkeypatch.delenv("RAGFLOW_API_KEY", raising=False)
    monkeypatch.delenv("RAGFLOW_KB_ID", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setenv("PPTXGENJS_SERVICE_URL", "http://localhost:3000")

    payload = asyncio.run(backend_main.health())

    assert payload["status"] == "healthy"
    assert payload["chat_mode"] == "plain"
    assert payload["agent_enabled"] is False
    assert payload["contest_force_plain"] is True
    assert payload["redis"] == "skipped"
    assert payload["rag_mode"] == "tfidf"
    assert payload["ppt_export"] == "pptxgenjs+python-pptx-fallback"
    assert payload["demo_mode"] is True
