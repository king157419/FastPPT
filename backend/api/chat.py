"""Chat API with optional SSE streaming and resilient agent fallback."""
from __future__ import annotations

import json
import logging
import re
import uuid
from typing import AsyncGenerator, Optional, Sequence

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.llm import chat_stream, chat_with_claude
from core.teaching_spec import REQUIRED_FIELD_LABELS, compile_teaching_spec
from integrations.langchain_agent import get_teaching_agent

logger = logging.getLogger(__name__)
router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    stream: bool = False
    use_agent: bool = False
    session_id: Optional[str] = None


def _normalize_messages(messages: Sequence[Message | dict]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in messages:
        if isinstance(item, Message):
            normalized.append({"role": item.role, "content": item.content})
            continue

        if isinstance(item, dict):
            normalized.append(
                {
                    "role": str(item.get("role", "user")),
                    "content": str(item.get("content", "")),
                }
            )
            continue

        normalized.append(
            {
                "role": str(getattr(item, "role", "user")),
                "content": str(getattr(item, "content", "")),
            }
        )
    return normalized


def _is_redis_connection_error(exc: Exception) -> bool:
    text = str(exc).lower()
    markers = (
        "localhost:6379",
        "127.0.0.1",
        "connect call failed",
        "errno 10061",
        "connecting to",
        "redis",
    )
    return any(marker in text for marker in markers)


def _parse_intent(reply: str) -> tuple[str, dict | None]:
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
    unresolved_text = "、".join(unresolved_labels) if unresolved_labels else "无"

    return (
        f"{visible_reply}\n\n"
        f"**课程主题**：{spec.get('topic', '')}\n"
        f"**教学目标**：{spec.get('teaching_goal', '')}\n"
        f"**目标受众**：{spec.get('audience', '')}\n"
        f"**重点难点**：{spec.get('difficulty_focus', '')}\n"
        f"**课时**：{spec.get('duration', '')}\n"
        f"**风格**：{spec.get('style', '')}\n"
        f"**核心知识点**：{'、'.join(key_points)}\n"
        f"**待确认字段**：{unresolved_text}\n\n"
        "点击“生成课件”即可进入课件与教案生成。"
    )


@router.post("/chat")
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    messages = _normalize_messages(req.messages)

    if req.use_agent and req.stream:
        return _stream_agent_response(messages, session_id)

    if req.use_agent:
        return await _agent_chat(messages, session_id)

    if req.stream:
        return _stream_response(messages)

    try:
        reply = chat_with_claude(messages)
    except Exception as exc:
        raise HTTPException(500, f"LLM 调用失败: {exc}") from exc

    visible, intent_payload = _parse_intent(reply)
    if not intent_payload:
        return {"reply": reply, "intent_ready": False, "intent": None}

    spec = compile_teaching_spec(intent_payload)
    intent = spec.to_intent()
    teaching_spec = spec.to_dict()
    summary = _build_summary(visible, teaching_spec)

    return {
        "reply": summary,
        "intent_ready": True,
        "intent": intent,
        "teaching_spec": teaching_spec,
        "session_id": session_id,
    }


def _stream_response(messages: list[dict[str, str]]) -> StreamingResponse:
    async def event_gen() -> AsyncGenerator[str, None]:
        full_text = ""
        try:
            for chunk in chat_stream(messages):
                full_text += chunk
                payload = json.dumps({"chunk": chunk}, ensure_ascii=False)
                yield f"data: {payload}\n\n"
        except Exception as exc:
            err = json.dumps({"error": str(exc)}, ensure_ascii=False)
            yield f"data: {err}\n\n"
            return

        visible, intent_payload = _parse_intent(full_text)
        if not intent_payload:
            done = json.dumps({"done": True, "intent_ready": False}, ensure_ascii=False)
            yield f"data: {done}\n\n"
            return

        spec = compile_teaching_spec(intent_payload)
        intent = spec.to_intent()
        teaching_spec = spec.to_dict()
        summary = _build_summary(visible, teaching_spec)

        done = json.dumps(
            {
                "done": True,
                "intent_ready": True,
                "intent": intent,
                "teaching_spec": teaching_spec,
                "summary": summary,
            },
            ensure_ascii=False,
        )
        yield f"data: {done}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _agent_chat(messages: list[dict[str, str]], session_id: str) -> dict:
    try:
        agent = get_teaching_agent()
        user_message = messages[-1].get("content", "") if messages else ""

        logger.info("Agent chat started - session_id: %s", session_id)
        response = await agent.chat(message=user_message, session_id=session_id)
        logger.info("Agent chat completed - session_id: %s", session_id)

        visible, intent_payload = _parse_intent(response)
        if not intent_payload:
            return {
                "reply": response,
                "intent_ready": False,
                "intent": None,
                "session_id": session_id,
                "agent_mode": True,
            }

        spec = compile_teaching_spec(intent_payload)
        intent = spec.to_intent()
        teaching_spec = spec.to_dict()
        summary = _build_summary(visible, teaching_spec)

        return {
            "reply": summary,
            "intent_ready": True,
            "intent": intent,
            "teaching_spec": teaching_spec,
            "session_id": session_id,
            "agent_mode": True,
        }

    except Exception as exc:
        if _is_redis_connection_error(exc):
            logger.warning("Agent chat fallback due to Redis connection error - session_id: %s", session_id)
            reply = chat_with_claude(messages)
            visible, intent_payload = _parse_intent(reply)
            if not intent_payload:
                return {
                    "reply": reply,
                    "intent_ready": False,
                    "intent": None,
                    "session_id": session_id,
                    "agent_mode": False,
                    "fallback_mode": True,
                }

            spec = compile_teaching_spec(intent_payload)
            intent = spec.to_intent()
            teaching_spec = spec.to_dict()
            summary = _build_summary(visible, teaching_spec)
            return {
                "reply": summary,
                "intent_ready": True,
                "intent": intent,
                "teaching_spec": teaching_spec,
                "session_id": session_id,
                "agent_mode": False,
                "fallback_mode": True,
            }

        logger.error("Agent chat failed - session_id: %s, error: %s", session_id, exc)
        raise HTTPException(500, f"Agent 调用失败: {exc}") from exc


def _stream_agent_response(messages: list[dict[str, str]], session_id: str) -> StreamingResponse:
    async def event_gen() -> AsyncGenerator[str, None]:
        full_text = ""
        try:
            agent = get_teaching_agent()
            user_message = messages[-1].get("content", "") if messages else ""

            logger.info("Agent streaming started - session_id: %s", session_id)
            async for chunk in agent.chat_stream(message=user_message, session_id=session_id):
                full_text += chunk
                payload = json.dumps({"chunk": chunk}, ensure_ascii=False)
                yield f"data: {payload}\n\n"
            logger.info("Agent streaming completed - session_id: %s", session_id)

        except Exception as exc:
            if _is_redis_connection_error(exc):
                logger.warning("Agent streaming fallback due to Redis connection error - session_id: %s", session_id)
                try:
                    fallback_text = ""
                    for chunk in chat_stream(messages):
                        fallback_text += chunk
                        payload = json.dumps({"chunk": chunk, "fallback_mode": True}, ensure_ascii=False)
                        yield f"data: {payload}\n\n"

                    visible, intent_payload = _parse_intent(fallback_text)
                    if not intent_payload:
                        done = json.dumps(
                            {
                                "done": True,
                                "intent_ready": False,
                                "session_id": session_id,
                                "agent_mode": False,
                                "fallback_mode": True,
                            },
                            ensure_ascii=False,
                        )
                        yield f"data: {done}\n\n"
                        return

                    spec = compile_teaching_spec(intent_payload)
                    intent = spec.to_intent()
                    teaching_spec = spec.to_dict()
                    summary = _build_summary(visible, teaching_spec)
                    done = json.dumps(
                        {
                            "done": True,
                            "intent_ready": True,
                            "intent": intent,
                            "teaching_spec": teaching_spec,
                            "summary": summary,
                            "session_id": session_id,
                            "agent_mode": False,
                            "fallback_mode": True,
                        },
                        ensure_ascii=False,
                    )
                    yield f"data: {done}\n\n"
                    return
                except Exception as fallback_exc:
                    logger.error(
                        "Fallback streaming also failed - session_id: %s, error: %s",
                        session_id,
                        fallback_exc,
                    )

            logger.error("Agent streaming failed - session_id: %s, error: %s", session_id, exc)
            err = json.dumps({"error": str(exc)}, ensure_ascii=False)
            yield f"data: {err}\n\n"
            return

        visible, intent_payload = _parse_intent(full_text)
        if not intent_payload:
            done = json.dumps(
                {
                    "done": True,
                    "intent_ready": False,
                    "session_id": session_id,
                    "agent_mode": True,
                },
                ensure_ascii=False,
            )
            yield f"data: {done}\n\n"
            return

        spec = compile_teaching_spec(intent_payload)
        intent = spec.to_intent()
        teaching_spec = spec.to_dict()
        summary = _build_summary(visible, teaching_spec)

        done = json.dumps(
            {
                "done": True,
                "intent_ready": True,
                "intent": intent,
                "teaching_spec": teaching_spec,
                "summary": summary,
                "session_id": session_id,
                "agent_mode": True,
            },
            ensure_ascii=False,
        )
        yield f"data: {done}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
