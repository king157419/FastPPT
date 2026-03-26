"""LLM 封装：DashScope Qwen 为主，Anthropic Claude 为备用"""
import os
import json
import re


def _get_dashscope_key() -> str:
    return os.environ.get("DASHSCOPE_API_KEY", "")


def _qwen_chat(messages: list[dict], system: str = "", model: str = "qwen-max") -> str:
    import dashscope
    from dashscope import Generation
    dashscope.api_key = _get_dashscope_key()
    full_messages = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)
    response = Generation.call(
        model=model,
        messages=full_messages,
        result_format="message",
        max_tokens=4096,
    )
    if response.status_code == 200:
        return response.output.choices[0].message.content
    raise RuntimeError(f"Qwen API error {response.status_code}: {response.message}")


def _qwen_chat_stream(messages: list[dict], system: str = "", model: str = "qwen-max"):
    import dashscope
    from dashscope import Generation
    dashscope.api_key = _get_dashscope_key()
    full_messages = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)
    responses = Generation.call(
        model=model,
        messages=full_messages,
        result_format="message",
        stream=True,
        incremental_output=True,
        max_tokens=4096,
    )
    for resp in responses:
        if resp.status_code == 200:
            chunk = resp.output.choices[0].message.content
            if chunk:
                yield chunk

def _claude_chat(messages: list[dict], system: str = "") -> str:
    import anthropic
    kwargs = {"api_key": os.environ.get("ANTHROPIC_API_KEY")}
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "").strip()
    if base_url:
        kwargs["base_url"] = base_url
    client = anthropic.Anthropic(**kwargs)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=system or "",
        messages=messages,
    )
    return response.content[0].text


def _chat(messages: list[dict], system: str = "", model: str = "qwen-max") -> str:
    """统一入口：优先 DashScope，失败则 fallback Claude"""
    if _get_dashscope_key():
        try:
            return _qwen_chat(messages, system, model)
        except Exception as e:
            print(f"[LLM] DashScope failed ({e}), falling back to Claude")
    return _claude_chat(messages, system)


def describe_image(image_base64: str, prompt: str = "") -> str:
    """用 Qwen-VL-Max 理解图片/帧内容"""
    import dashscope
    from dashscope import MultiModalConversation
    dashscope.api_key = _get_dashscope_key()
    if not prompt:
        prompt = "请描述这张图片的内容，提取其中的关键知识点、公式、图表信息，用于课件制作参考。"
    response = MultiModalConversation.call(
        model="qwen-vl-max",
        messages=[{"role": "user", "content": [
            {"image": f"data:image/jpeg;base64,{image_base64}"},
            {"text": prompt},
        ]}],
    )
    if response.status_code == 200:
        content = response.output.choices[0].message.content
        if isinstance(content, list):
            return content[0].get("text", "")
        return str(content)
    raise RuntimeError(f"Qwen-VL error {response.status_code}: {response.message}")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """用 text-embedding-v3 向量化"""
    import dashscope
    from dashscope import TextEmbedding
    dashscope.api_key = _get_dashscope_key()
    all_embeddings = []
    for i in range(0, len(texts), 25):
        batch = texts[i:i + 25]
        resp = TextEmbedding.call(model="text-embedding-v3", input=batch)
        if resp.status_code == 200:
            items = sorted(resp.output["embeddings"], key=lambda x: x["text_index"])
            all_embeddings.extend([item["embedding"] for item in items])
        else:
            raise RuntimeError(f"Embedding error {resp.status_code}: {resp.message}")
    return all_embeddings


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
    """多轮对话（保留兼容名称，实际优先 Qwen）"""
    return _chat(messages, system=CHAT_SYSTEM, model="qwen-max")


def chat_stream(messages: list[dict]):
    """流式多轮对话，yield 文本片段"""
    if _get_dashscope_key():
        try:
            yield from _qwen_chat_stream(messages, system=CHAT_SYSTEM, model="qwen-max")
            return
        except Exception as e:
            print(f"[LLM] Stream failed ({e}), fallback")
    yield _claude_chat(messages, system=CHAT_SYSTEM)


def generate_slides_json(intent: dict, rag_chunks: list[str]) -> dict:
    """
    一次调用生成完整课件 JSON。
    返回 {"theme": {...}, "pages": [{...}, ...]}
    """
    topic = intent.get("topic", "未知主题")
    audience = intent.get("audience", "学生")
    key_points = intent.get("key_points", [])
    duration = intent.get("duration", "45分钟")
    style = intent.get("style", "简洁学术")
    rag_text = "\n".join(rag_chunks[:5]) if rag_chunks else ""
    rag_section = f"\n\n参考资料（可适当引用）：\n{rag_text[:800]}" if rag_text else ""
    kp_list = "、".join(key_points)

    prompt = f"""你是一位顶级课件设计师。请为以下课程生成一份完整的 PPT 课件内容。

课程信息：
- 主题：{topic}
- 受众：{audience}
- 课时：{duration}
- 风格：{style}
- 核心知识点：{kp_list}{rag_section}

可用幻灯片类型（根据课程内容智能选择）：
1. cover — 封面（必须有，第一页）
2. agenda — 目录（必须有，第二页）
3. content — 文字要点页：bullets(≤4条，每条≤10字，关键词非完整句) + tip
4. code — 代码演示页：language + code(实际可运行代码) + explanation
5. formula — 公式推导页：formulas([{{label,expr}}]) + explanation（expr 必须用 LaTeX 语法）
6. example — 例题解答页：problem + steps([...]) + answer
7. two_column — 双栏对比页：left/right 各有 heading + points([...])
8. quote — 金句/过渡页：text
9. summary — 总结页（必须有，最后一页）：takeaways(3条)
10. animation — 互动动画页：template(从 bar_chart/card_flip/flowchart/quiz/timeline 选一) + template_data(对应模板数据)
11. image — 图片讲解页：image_url(可留空) + caption(图片说明文字)

动画模板数据格式：
- bar_chart: {{"title":"...","accent":"#hex","labels":[...],"values":[...]}}
- card_flip: {{"accent":"#hex","cards":[{{"term":"...","def":"..."}}]}}
- flowchart: {{"accent":"#hex","steps":["步骤1","步骤2",...]}}
- quiz: {{"title":"...","accent":"#hex","questions":[{{"q":"...","options":[...],"answer":0,"explain":"..."}}]}}
- timeline: {{"title":"...","accent":"#hex","events":[{{"year":"...","title":"...","desc":"..."}}]}}

类型选择规则：
- 编程/算法类 → 必须 ≥1 页 code
- 数学/物理/工程类 → 必须 ≥1 页 formula
- 任何课程 → 必须 ≥1 页 example
- 有概念对比/优缺点 → 用 two_column
- 有数据统计/知识卡片/流程/测验/历史时间轴 → 选对应 animation 模板
- 上传了图片/视频帧可视化 → 用 image 类型

主题色根据风格：
- 简洁学术 → {{"primary":"#0f172a","accent":"#3b82f6","text":"#f8fafc"}}
- 活泼互动 → {{"primary":"#1a0533","accent":"#a855f7","text":"#fdf4ff"}}
- 图文并茂 → {{"primary":"#0c1a0f","accent":"#22c55e","text":"#f0fdf4"}}
- 商务专业 → {{"primary":"#0a0a0a","accent":"#f59e0b","text":"#fffbeb"}}

输出合法 JSON，格式：
{{"theme":{{"primary":"#0f172a","accent":"#3b82f6","text":"#f8fafc"}},"pages":[...]}}"""

    text = _chat([{"role": "user", "content": prompt}], model="qwen-max")
    text = text.strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return _fallback_slides(intent)


def _fallback_slides(intent: dict) -> dict:
    topic = intent.get("topic", "课程")
    audience = intent.get("audience", "学生")
    duration = intent.get("duration", "45分钟")
    key_points = intent.get("key_points", ["核心概念", "基本原理", "实践应用"])
    pages = [
        {"type": "cover", "title": topic, "subtitle": f"{audience} · {duration}"},
        {"type": "agenda", "title": "课程目录", "items": key_points},
    ]
    for kp in key_points:
        pages.append({"type": "content", "title": kp,
                      "bullets": [f"{kp}基本概念", f"{kp}核心原理", f"{kp}实际应用"],
                      "tip": "结合案例讲解"})
    pages.append({"type": "summary", "title": "课程总结",
                  "takeaways": [f"掌握{kp}" for kp in key_points[:3]]})
    return {"theme": {"primary": "#0f172a", "accent": "#3b82f6", "text": "#f8fafc"}, "pages": pages}



