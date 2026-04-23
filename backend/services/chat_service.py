"""Chat orchestration service."""
from __future__ import annotations

import json
import logging
import os
import re
from typing import AsyncGenerator

from fastapi.responses import StreamingResponse

from core.llm import chat_stream, chat_with_claude
from core.teaching_spec import REQUIRED_FIELD_LABELS, compile_teaching_spec


logger = logging.getLogger(__name__)


def agent_enabled() -> bool:
    return os.getenv("ENABLE_AGENT", "false").strip().lower() == "true"


def contest_force_plain() -> bool:
    return os.getenv("CONTEST_FORCE_PLAIN", "true").strip().lower() == "true"


def parse_intent(reply: str) -> tuple[str, dict | None]:
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


def ensure_cn_reply(text: str) -> str:
    content = (text or "").strip()
    if not content:
        return "请告诉我课程主题、教学目标、学生类型、课时和重点难点。"
    if re.search(r"[\u4e00-\u9fff]", content):
        return content
    return (
        "我已收到你的需求。为了继续生成高质量课件，请补充："
        "教学目标、学生类型、课时长短、重点难点。"
    )


def build_summary(visible_reply: str, spec: dict) -> str:
    key_points = spec.get("key_points", []) or []
    unresolved = spec.get("unresolved_fields", []) or []
    unresolved_labels = [REQUIRED_FIELD_LABELS.get(item, item) for item in unresolved]
    unresolved_text = "、".join(unresolved_labels) if unresolved_labels else "无"

    return (
        f"{visible_reply}\n\n"
        f"**课程主题**：{spec.get('topic', '')}\n"
        f"**教学目标**：{spec.get('teaching_goal', '')}\n"
        f"**学生类型**：{spec.get('audience', '')}\n"
        f"**重点难点**：{spec.get('difficulty_focus', '')}\n"
        f"**课时**：{spec.get('duration', '')}\n"
        f"**风格**：{spec.get('style', '')}\n"
        f"**关键要点**：{', '.join(key_points) if key_points else '无'}\n"
        f"**待补充项**：{unresolved_text}\n\n"
        "请点击“生成课件”开始生成 PPT 和教案。"
    )


def build_final_payload(full_text: str, session_id: str | None, extra: dict | None = None) -> dict:
    visible, intent_payload = parse_intent(full_text)
    payload: dict = {"done": True, "intent_ready": False}

    if intent_payload:
        spec = compile_teaching_spec(intent_payload)
        payload.update(
            {
                "intent_ready": True,
                "intent": spec.to_intent(),
                "teaching_spec": spec.to_dict(),
                "summary": build_summary(visible, spec.to_dict()),
            }
        )

    if session_id:
        payload["session_id"] = session_id
    if extra:
        payload.update(extra)
    return payload


def plain_chat_response(messages: list[dict[str, str]], session_id: str) -> dict:
    reply = chat_with_claude(messages)
    visible, intent_payload = parse_intent(reply)

    base: dict = {
        "session_id": session_id,
        "agent_mode": False,
    }

    if not intent_payload:
        base.update({"reply": ensure_cn_reply(reply), "intent_ready": False, "intent": None})
        return base

    spec = compile_teaching_spec(intent_payload)
    base.update(
        {
            "reply": build_summary(visible, spec.to_dict()),
            "intent_ready": True,
            "intent": spec.to_intent(),
            "teaching_spec": spec.to_dict(),
        }
    )
    return base


def stream_response(
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

        done = build_final_payload(full_text, session_id, stream_meta)
        yield f"data: {json.dumps(done, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def agent_chat(messages: list[dict[str, str]], session_id: str) -> dict:
    from integrations.langchain_agent import get_teaching_agent

    agent = get_teaching_agent()
    user_message = messages[-1]["content"] if messages else ""
    reply = await agent.chat(message=user_message, session_id=session_id)

    visible, intent_payload = parse_intent(reply)
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
        "reply": build_summary(visible, spec.to_dict()),
        "intent_ready": True,
        "intent": spec.to_intent(),
        "teaching_spec": spec.to_dict(),
        "session_id": session_id,
        "agent_mode": True,
    }


def stream_agent_response(messages: list[dict[str, str]], session_id: str) -> StreamingResponse:
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

            done = build_final_payload(full_text, session_id, {"agent_mode": True})
            yield f"data: {json.dumps(done, ensure_ascii=False)}\n\n"
        except Exception as agent_exc:
            logger.exception("Agent streaming failed, trying fallback")
            fallback_stream = stream_response(
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
