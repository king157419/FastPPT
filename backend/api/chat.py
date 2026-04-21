"""Chat API with SSE streaming, TeachingSpec normalization, and optional Agent mode."""
from __future__ import annotations

import json
import logging
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
        '点击"生成课件"即可进入课件与教案生成。'
    )


def _normalize_messages(messages: list[Message]) -> list[dict[str, str]]:
    """Convert Message objects to dict format."""
    return [{"role": msg.role, "content": msg.content} for msg in messages]


@router.post("/chat")
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    messages = _normalize_messages(req.messages)

    # Agent mode
    if req.use_agent:
        try:
            from integrations.langchain_agent import get_teaching_agent
            agent = get_teaching_agent()

            if req.stream:
                return _stream_agent_response(agent, messages[-1]["content"], session_id)
            else:
                reply = await agent.chat(message=messages[-1]["content"], session_id=session_id)
                return {"reply": reply, "agent_mode": True, "session_id": session_id}
        except Exception as exc:
            logger.error(f"Agent mode failed: {exc}")
            # Fallback to traditional mode
            logger.info("Falling back to traditional mode")

    # Traditional mode
    if req.stream:
        return _stream_response(messages)

    # Non-streaming traditional mode
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


def _stream_agent_response(agent, message: str, session_id: str) -> StreamingResponse:
    async def event_gen() -> AsyncGenerator[str, None]:
        try:
            async for chunk in agent.chat_stream(message=message, session_id=session_id):
                payload = json.dumps({"chunk": chunk, "agent_mode": True}, ensure_ascii=False)
                yield f"data: {payload}\n\n"

            done = json.dumps({"done": True, "agent_mode": True}, ensure_ascii=False)
            yield f"data: {done}\n\n"
        except Exception as exc:
            err = json.dumps({"error": str(exc), "agent_mode": True}, ensure_ascii=False)
            yield f"data: {err}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
