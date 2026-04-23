"""Thin chat API router delegating orchestration to service layer."""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import chat_service

logger = logging.getLogger(__name__)
router = APIRouter()

chat_with_claude = chat_service.chat_with_claude
chat_stream = chat_service.chat_stream


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    stream: bool = False
    use_agent: bool = False
    session_id: str | None = None


def _normalize_messages(messages: list[Message]) -> list[dict[str, str]]:
    return [{"role": msg.role, "content": msg.content} for msg in messages]


def _sync_service_hooks() -> None:
    chat_service.chat_with_claude = chat_with_claude
    chat_service.chat_stream = chat_stream


@router.post("/chat")
async def chat(req: ChatRequest):
    _sync_service_hooks()
    session_id = req.session_id or str(uuid.uuid4())
    messages = _normalize_messages(req.messages)

    enabled = chat_service.agent_enabled()
    force_plain = chat_service.contest_force_plain()
    wants_agent = req.use_agent and enabled and not force_plain

    if req.use_agent and not wants_agent:
        if force_plain:
            logger.info("Contest plain mode enabled; forcing plain chat path")
        elif not enabled:
            logger.info("Agent disabled by config; fallback to plain chat")

    if wants_agent and req.stream:
        return chat_service.stream_agent_response(messages, session_id)

    if wants_agent:
        try:
            return await chat_service.agent_chat(messages, session_id)
        except Exception as agent_exc:
            logger.exception("Agent chat failed, trying fallback")
            try:
                fallback = chat_service.plain_chat_response(messages, session_id)
                fallback["fallback_mode"] = True
                fallback["agent_error"] = str(agent_exc)
                return fallback
            except Exception as fallback_exc:
                raise HTTPException(
                    status_code=500,
                    detail=f"Agent path failed: {agent_exc}; fallback path failed: {fallback_exc}",
                ) from fallback_exc

    if req.stream:
        return chat_service.stream_response(messages, session_id=session_id)

    try:
        return chat_service.plain_chat_response(messages, session_id)
    except Exception as exc:
        raise HTTPException(500, f"LLM call failed: {exc}") from exc
