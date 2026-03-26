"""Mock 意图提取：根据对话轮次和内容拼装结构化 JSON"""
import re

QUESTIONS = [
    "请问这门课的主题是什么？",
    "目标受众是哪类学生（如大一本科生、研究生等）？",
    "课程的核心知识点和重难点是什么？",
    "计划课时是多少？（如 45 分钟 / 2 课时）",
    "希望课件的风格是什么？（简洁学术 / 活泼互动 / 图文并茂）",
]


def get_next_question(round_index: int) -> str:
    """返回当前轮次应问的问题，超出范围返回空串表示意图收集完毕"""
    if round_index < len(QUESTIONS):
        return QUESTIONS[round_index]
    return ""


def extract_intent(messages: list[dict]) -> dict:
    """
    从对话历史提取意图 JSON。
    messages 格式: [{"role": "user"|"assistant", "content": str}]
    """
    user_msgs = [m["content"] for m in messages if m["role"] == "user"]

    topic = _find_by_index(user_msgs, 0) or "未知主题"
    audience = _find_by_index(user_msgs, 1) or "本科生"
    key_points_raw = _find_by_index(user_msgs, 2) or ""
    key_points = [kp.strip() for kp in re.split(r"[,，、；;]", key_points_raw) if kp.strip()] or ["核心概念", "基本原理", "实际应用"]
    duration = _find_by_index(user_msgs, 3) or "45分钟"
    style = _find_by_index(user_msgs, 4) or "简洁学术"

    return {
        "topic": topic,
        "audience": audience,
        "key_points": key_points,
        "difficulty_focus": key_points[-1] if key_points else "综合应用",
        "duration": duration,
        "style": style,
    }


def _find_by_index(msgs: list[str], idx: int) -> str:
    if idx < len(msgs):
        return msgs[idx].strip()
    return ""
