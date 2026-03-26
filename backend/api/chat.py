import json
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.llm import chat_with_claude

router = APIRouter()


class ChatRequest(BaseModel):
    messages: list[dict]  # [{"role": "user"|"assistant", "content": str}]


@router.post("/chat")
def chat(req: ChatRequest):
    messages = req.messages

    try:
        reply = chat_with_claude(messages)
    except Exception as e:
        raise HTTPException(500, f"LLM 调用失败：{e}")

    # 检测意图收集完毕标记
    if "[INTENT_READY]" in reply:
        # 分离正文和 JSON
        parts = reply.split("[INTENT_READY]")
        visible_reply = parts[0].strip()
        json_part = parts[1].strip() if len(parts) > 1 else ""

        intent = None
        match = re.search(r'\{.*\}', json_part, re.DOTALL)
        if match:
            try:
                intent = json.loads(match.group())
                # 确保 key_points 是列表
                if isinstance(intent.get("key_points"), str):
                    intent["key_points"] = [
                        kp.strip() for kp in re.split(r'[,，、；;]', intent["key_points"]) if kp.strip()
                    ]
            except json.JSONDecodeError:
                intent = None

        if intent:
            summary = (
                f"{visible_reply}\n\n"
                f"**课程主题**：{intent.get('topic', '')}\n"
                f"**目标受众**：{intent.get('audience', '')}\n"
                f"**核心知识点**：{'、'.join(intent.get('key_points', []))}\n"
                f"**课时**：{intent.get('duration', '')}\n"
                f"**风格**：{intent.get('style', '')}\n\n"
                f"点击「生成课件」按钮即可生成 PPT 和 Word 教案！"
            )
            return {"reply": summary, "intent_ready": True, "intent": intent}

    return {"reply": reply, "intent_ready": False, "intent": None}
