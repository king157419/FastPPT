"""对话接口：支持同步和 SSE 流式两种模式"""
import json
import re
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from core.llm import chat_with_claude, chat_stream

router = APIRouter()


class ChatRequest(BaseModel):
    messages: list[dict]  # [{"role": "user"|"assistant", "content": str}]
    stream: bool = False


def _parse_intent(reply: str) -> tuple[str, dict | None]:
    """从 reply 中分离正文和意图 JSON"""
    if "[INTENT_READY]" not in reply:
        return reply, None
    parts = reply.split("[INTENT_READY]")
    visible = parts[0].strip()
    json_part = parts[1].strip() if len(parts) > 1 else ""
    match = re.search(r'\{.*\}', json_part, re.DOTALL)
    if not match:
        return visible, None
    try:
        intent = json.loads(match.group())
        if isinstance(intent.get("key_points"), str):
            intent["key_points"] = [
                kp.strip() for kp in re.split(r'[,，、；;]', intent["key_points"]) if kp.strip()
            ]
        return visible, intent
    except json.JSONDecodeError:
        return visible, None


def _build_summary(visible: str, intent: dict) -> str:
    return (
        f"{visible}\n\n"
        f"**课程主题**：{intent.get('topic', '')}\n"
        f"**目标受众**：{intent.get('audience', '')}\n"
        f"**核心知识点**：{'、'.join(intent.get('key_points', []))}\n"
        f"**课时**：{intent.get('duration', '')}\n"
        f"**风格**：{intent.get('style', '')}\n\n"
        f"点击「生成课件」按钮即可生成 PPT 和 Word 教案！"
    )


@router.post("/chat")
async def chat(req: ChatRequest):
    if req.stream:
        return _stream_response(req.messages)
    # 同步模式
    try:
        reply = chat_with_claude(req.messages)
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(500, f"LLM 调用失败：{e}")

    visible, intent = _parse_intent(reply)
    if intent:
        summary = _build_summary(visible, intent)
        return {"reply": summary, "intent_ready": True, "intent": intent}
    return {"reply": reply, "intent_ready": False, "intent": None}


def _stream_response(messages: list[dict]) -> StreamingResponse:
    """SSE 流式响应"""
    async def event_gen():
        full_text = ""
        try:
            for chunk in chat_stream(messages):
                full_text += chunk
                data = json.dumps({"chunk": chunk}, ensure_ascii=False)
                yield f"data: {data}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return

        # 流结束后检测意图
        visible, intent = _parse_intent(full_text)
        if intent:
            summary = _build_summary(visible, intent)
            done_data = json.dumps(
                {"done": True, "intent_ready": True, "intent": intent, "summary": summary},
                ensure_ascii=False,
            )
        else:
            done_data = json.dumps(
                {"done": True, "intent_ready": False},
                ensure_ascii=False,
            )
        yield f"data: {done_data}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
