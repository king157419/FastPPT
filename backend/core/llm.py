"""Anthropic Claude API 封装"""
import os
import json
import re
import anthropic

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _client


CHAT_SYSTEM = """你是一位专业的教学设计助手，帮助教师设计课件。
你需要通过自然对话，收集以下信息：
1. 课程主题（topic）
2. 目标受众（audience）- 如大一本科生、高中生、研究生等
3. 核心知识点（key_points）- 用逗号分隔
4. 计划课时（duration）- 如45分钟、2课时
5. 课件风格（style）- 如简洁学术、活泼互动、图文并茂

对话风格：亲切、专业、简洁。每次只问一个问题或确认一项信息。
当你已经收集到全部5项信息后，在回复末尾另起一行，输出以下标记（不要有多余内容）：
[INTENT_READY]
{"topic":"...","audience":"...","key_points":["...","..."],"duration":"...","style":"..."}

注意：key_points 必须是数组，每个元素是一个独立知识点。"""


def chat_with_claude(messages: list[dict]) -> str:
    """
    messages: [{"role": "user"|"assistant", "content": str}]
    返回 Claude 的回复文本
    """
    client = _get_client()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=CHAT_SYSTEM,
        messages=messages,
    )
    return response.content[0].text


def generate_slide_content(topic: str, key_point: str, rag_ctx: str = "") -> dict:
    """
    为单个知识点生成 PPT 页面内容。
    返回 {"bullets": [str, ...], "tip": str}
    """
    client = _get_client()
    rag_section = f"\n\n参考资料：\n{rag_ctx[:400]}" if rag_ctx else ""
    prompt = f"""课程主题：{topic}
当前知识点：{key_point}{rag_section}

请为这个知识点生成 PPT 幻灯片内容，要求：
- 3到4条核心要点（bullet points），每条15-30字，简洁有力
- 1条教师提示语（tip），20字以内，提示讲授重点或互动方式

严格按以下 JSON 格式输出，不要有其他内容：
{{"bullets":["要点1","要点2","要点3"],"tip":"教师提示"}}"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    # 提取 JSON
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    # fallback
    return {
        "bullets": [
            f"{key_point}的基本概念与定义",
            f"{key_point}的核心原理与机制",
            f"{key_point}在实际场景中的应用",
        ],
        "tip": "结合实际案例讲解，引导学生思考",
    }
