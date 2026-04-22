"""Chat API with SSE streaming, TeachingSpec normalization, and optional Agent mode."""
from __future__ import annotations

import json
import logging
import os
import re
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.llm import chat_stream, chat_with_claude
from core.teaching_spec import REQUIRED_FIELD_LABELS, compile_teaching_spec

logger = logging.getLogger(__name__)
router = APIRouter()


def _agent_enabled() -> bool:
    return os.getenv("ENABLE_AGENT", "false").strip().lower() == "true"


def _contest_force_plain() -> bool:
    return os.getenv("CONTEST_FORCE_PLAIN", "true").strip().lower() == "true"


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    stream: bool = False
    use_agent: bool = False
    session_id: str | None = None


def _parse_intent(reply: str) -> tuple[str, dict | None]:
    """Parse [INTENT_READY] payload from model response."""
    marker = "[INTENT_READY]"
    if marker not in reply:
        return reply, None

    visible, _, tail = reply.partition(marker)
    match = re.search(r"\{.*\}", tail, re.DOTALL)
    if not match:
        return visible.strip(), None

    try:
        parsed = json.loads(match.group())
    except json.JSONDecodeError:
        return visible.strip(), None

    return visible.strip(), parsed


def _build_summary(visible_reply: str, spec: dict) -> str:
    key_points = spec.get("key_points", []) or []
    unresolved = spec.get("unresolved_fields", []) or []
    unresolved_labels = [REQUIRED_FIELD_LABELS.get(item, item) for item in unresolved]
    unresolved_text = ", ".join(unresolved_labels) if unresolved_labels else "None"

    return (
        f"{visible_reply}\n\n"
        f"**Topic**: {spec.get('topic', '')}\n"
        f"**Teaching Goal**: {spec.get('teaching_goal', '')}\n"
        f"**Audience**: {spec.get('audience', '')}\n"
        f"**Difficulty Focus**: {spec.get('difficulty_focus', '')}\n"
        f"**Duration**: {spec.get('duration', '')}\n"
        f"**Style**: {spec.get('style', '')}\n"
        f"**Key Points**: {', '.join(key_points) if key_points else 'None'}\n"
        f"**Missing Fields**: {unresolved_text}\n\n"
        "Click Generate to create PPT + lesson plan."
    )


def _normalize_messages(messages: list[Message]) -> list[dict[str, str]]:
    """Convert Message objects to dict format."""
    return [{"role": msg.role, "content": msg.content} for msg in messages]


def _build_final_payload(full_text: str, session_id: str | None, extra: dict | None = None) -> dict:
    visible, intent_payload = _parse_intent(full_text)
    payload: dict = {"done": True, "intent_ready": False}

    if intent_payload:
        spec = compile_teaching_spec(intent_payload)
        payload.update(
            {
                "intent_ready": True,
                "intent": spec.to_intent(),
                "teaching_spec": spec.to_dict(),
                "summary": _build_summary(visible, spec.to_dict()),
            }
        )

    if session_id:
        payload["session_id"] = session_id
    if extra:
        payload.update(extra)
    return payload


def _plain_chat_response(messages: list[dict[str, str]], session_id: str) -> dict:
    reply = chat_with_claude(messages)
    visible, intent_payload = _parse_intent(reply)

    base: dict = {
        "session_id": session_id,
        "agent_mode": False,
    }

    if not intent_payload:
        base.update({"reply": reply, "intent_ready": False, "intent": None})
        return base

    spec = compile_teaching_spec(intent_payload)
    base.update(
        {
            "reply": _build_summary(visible, spec.to_dict()),
            "intent_ready": True,
            "intent": spec.to_intent(),
            "teaching_spec": spec.to_dict(),
        }
    )
    return base


@router.post("/chat")
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    messages = _normalize_messages(req.messages)

    agent_enabled = _agent_enabled()
    contest_force_plain = _contest_force_plain()
    wants_agent = req.use_agent and agent_enabled and not contest_force_plain

    if req.use_agent and not wants_agent:
        if contest_force_plain:
            logger.info("Contest plain mode enabled; forcing plain chat path")
        elif not agent_enabled:
            logger.info("Agent disabled by config; fallback to plain chat")

    if wants_agent and req.stream:
        return _stream_agent_response(messages, session_id)

    if wants_agent:
        try:
            return await _agent_chat(messages, session_id)
        except Exception as agent_exc:
            logger.exception("Agent chat failed, trying fallback")
            try:
                fallback = _plain_chat_response(messages, session_id)
                fallback["fallback_mode"] = True
                fallback["agent_error"] = str(agent_exc)
                return fallback
            except Exception as fallback_exc:
                raise HTTPException(
                    status_code=500,
                    detail=f"Agent path failed: {agent_exc}; fallback path failed: {fallback_exc}",
                ) from fallback_exc

    if req.stream:
        return _stream_response(messages, session_id=session_id)

    try:
        return _plain_chat_response(messages, session_id)
    except Exception as exc:
        raise HTTPException(500, f"LLM call failed: {exc}") from exc


def _stream_response(
    messages: list[dict[str, str]],
    session_id: str | None = None,
    stream_meta: dict | None = None,
    initial_agent_error: Exception | None = None,
) -> StreamingResponse:
    async def event_gen() -> AsyncGenerator[str, None]:
        full_text = ""
        try:
            for chunk in chat_stream(messages):
                full_text += chunk
                payload = {"chunk": chunk}
                if stream_meta:
                    payload.update(stream_meta)
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        except Exception as fallback_exc:
            if initial_agent_error is not None:
                error_message = (
                    f"Agent path failed: {initial_agent_error}; "
                    f"fallback path failed: {fallback_exc}"
                )
            else:
                error_message = str(fallback_exc)

            err_payload = {"error": error_message}
            if stream_meta:
                err_payload.update(stream_meta)
            yield f"data: {json.dumps(err_payload, ensure_ascii=False)}\n\n"
            return

        done = _build_final_payload(full_text, session_id, stream_meta)
        yield f"data: {json.dumps(done, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _agent_chat(messages: list[dict[str, str]], session_id: str) -> dict:
    from integrations.langchain_agent import get_teaching_agent

    agent = get_teaching_agent()
    user_message = messages[-1]["content"] if messages else ""
    reply = await agent.chat(message=user_message, session_id=session_id)

    visible, intent_payload = _parse_intent(reply)
    if not intent_payload:
        return {
            "reply": reply,
            "intent_ready": False,
            "intent": None,
            "session_id": session_id,
            "agent_mode": True,
        }

    spec = compile_teaching_spec(intent_payload)
    return {
        "reply": _build_summary(visible, spec.to_dict()),
        "intent_ready": True,
        "intent": spec.to_intent(),
        "teaching_spec": spec.to_dict(),
        "session_id": session_id,
        "agent_mode": True,
    }


def _stream_agent_response(messages: list[dict[str, str]], session_id: str) -> StreamingResponse:
    async def event_gen() -> AsyncGenerator[str, None]:
        full_text = ""

        try:
            from integrations.langchain_agent import get_teaching_agent

            agent = get_teaching_agent()
            user_message = messages[-1]["content"] if messages else ""
            async for chunk in agent.chat_stream(message=user_message, session_id=session_id):
                full_text += chunk
                payload = {"chunk": chunk, "agent_mode": True}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

            done = _build_final_payload(full_text, session_id, {"agent_mode": True})
            yield f"data: {json.dumps(done, ensure_ascii=False)}\n\n"
        except Exception as agent_exc:
            logger.exception("Agent streaming failed, trying fallback")

            fallback_stream = _stream_response(
                messages,
                session_id=session_id,
                stream_meta={"agent_mode": False, "fallback_mode": True},
                initial_agent_error=agent_exc,
            )
            async for chunk in fallback_stream.body_iterator:
                yield chunk

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
