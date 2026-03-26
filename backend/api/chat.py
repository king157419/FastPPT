from fastapi import APIRouter
from pydantic import BaseModel
from core.intent import get_next_question, extract_intent

router = APIRouter()


class ChatRequest(BaseModel):
    messages: list[dict]  # [{"role": "user"|"assistant", "content": str}]


@router.post("/chat")
def chat(req: ChatRequest):
    messages = req.messages

    # 计算用户已回答的轮数
    user_count = sum(1 for m in messages if m["role"] == "user")

    next_q = get_next_question(user_count)

    if next_q:
        # 还有问题要问
        return {
            "reply": next_q,
            "intent_ready": False,
            "intent": None,
        }
    else:
        # 所有问题已收集完毕
        intent = extract_intent(messages)
        return {
            "reply": (
                f"好的！我已经完整理解了您的教学需求。\n\n"
                f"**课程主题**：{intent['topic']}\n"
                f"**目标受众**：{intent['audience']}\n"
                f"**核心知识点**：{'、'.join(intent['key_points'])}\n"
                f"**课时**：{intent['duration']}\n"
                f"**风格**：{intent['style']}\n\n"
                f"点击下方「生成课件」按钮，即可生成 PPT 和 Word 教案！"
            ),
            "intent_ready": True,
            "intent": intent,
        }
