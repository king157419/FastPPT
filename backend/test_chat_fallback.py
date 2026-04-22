"""Regression tests for chat agent fallback behaviors."""
from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from api import chat as chat_api


def test_use_agent_request_falls_back_when_agent_disabled(monkeypatch):
    monkeypatch.setenv("CONTEST_FORCE_PLAIN", "true")
    monkeypatch.setenv("ENABLE_AGENT", "false")

    calls = {"plain": 0, "agent": 0}

    def fake_plain(messages, session_id):
        calls["plain"] += 1
        return {
            "reply": "ok",
            "intent_ready": False,
            "intent": None,
            "session_id": session_id,
            "agent_mode": False,
        }

    async def fake_agent(messages, session_id):
        calls["agent"] += 1
        return {"reply": "should-not-hit"}

    monkeypatch.setattr(chat_api, "_plain_chat_response", fake_plain)
    monkeypatch.setattr(chat_api, "_agent_chat", fake_agent)

    req = chat_api.ChatRequest(
        messages=[{"role": "user", "content": "hello"}],
        use_agent=True,
        stream=False,
    )
    result = asyncio.run(chat_api.chat(req))

    assert calls["plain"] == 1
    assert calls["agent"] == 0
    assert result["agent_mode"] is False


def test_agent_and_fallback_error_are_both_exposed(monkeypatch):
    monkeypatch.setenv("CONTEST_FORCE_PLAIN", "false")
    monkeypatch.setenv("ENABLE_AGENT", "true")

    async def fail_agent(messages, session_id):
        raise RuntimeError("agent exploded")

    def fail_plain(messages, session_id):
        raise RuntimeError("fallback exploded")

    monkeypatch.setattr(chat_api, "_agent_chat", fail_agent)
    monkeypatch.setattr(chat_api, "_plain_chat_response", fail_plain)

    req = chat_api.ChatRequest(
        messages=[{"role": "user", "content": "hello"}],
        use_agent=True,
        stream=False,
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(chat_api.chat(req))

    detail = str(exc_info.value.detail)
    assert "Agent path failed: agent exploded" in detail
    assert "fallback path failed: fallback exploded" in detail


def test_stream_fallback_error_contains_agent_and_fallback(monkeypatch):
    def broken_chat_stream(messages):
        raise RuntimeError("fallback stream exploded")

    monkeypatch.setattr(chat_api, "chat_stream", broken_chat_stream)

    resp = chat_api._stream_response(
        [{"role": "user", "content": "hello"}],
        session_id="s1",
        stream_meta={"agent_mode": False, "fallback_mode": True},
        initial_agent_error=RuntimeError("agent stream exploded"),
    )

    async def collect_body() -> str:
        chunks = []
        async for chunk in resp.body_iterator:
            chunks.append(chunk.decode("utf-8") if isinstance(chunk, (bytes, bytearray)) else str(chunk))
        return "".join(chunks)

    payload = asyncio.run(collect_body())
    assert "Agent path failed: agent stream exploded" in payload
    assert "fallback path failed: fallback stream exploded" in payload
