"""LLM 封装：DeepSeek 为主，DashScope Qwen 为次，Anthropic Claude 为备用"""
import os
import json
import re
# Note: Environment variables should be set before starting the application
# load_dotenv() is removed to avoid overriding environment variables


def _get_deepseek_key() -> str:
    return os.environ.get("DEEPSEEK_API_KEY", "")


def _deepseek_chat(messages: list[dict], system: str = "", model: str = "deepseek-chat") -> str:
    from openai import OpenAI
    client = OpenAI(api_key=_get_deepseek_key(), base_url="https://api.deepseek.com")
    full_messages = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)
    response = client.chat.completions.create(
        model=model, messages=full_messages, max_tokens=4096
    )
    return response.choices[0].message.content


def _deepseek_chat_stream(messages: list[dict], system: str = "", model: str = "deepseek-chat"):
    from openai import OpenAI
    client = OpenAI(api_key=_get_deepseek_key(), base_url="https://api.deepseek.com")
    full_messages = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)
    stream = client.chat.completions.create(
        model=model, messages=full_messages, max_tokens=4096, stream=True
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


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
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "").strip()

    # Debug logging
    print(f"[DEBUG] _claude_chat called")
    print(f"[DEBUG] API Key: {api_key[:20] if api_key else 'NOT SET'}...")
    print(f"[DEBUG] Base URL: {base_url or 'NOT SET'}")

    kwargs = {"api_key": api_key}
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


def _chat(messages: list[dict], system: str = "", model: str = "deepseek-chat") -> str:
    """统一入口：优先 DeepSeek，次 DashScope，失败则 fallback Claude"""
    if _get_deepseek_key():
        try:
            return _deepseek_chat(messages, system)
        except Exception as e:
            print(f"[LLM] DeepSeek failed ({e}), trying DashScope")
    if _get_dashscope_key():
        try:
            return _qwen_chat(messages, system)
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
2. 教学目标（teaching_goal）- 如“理解XX并能应用到XX场景”
3. 目标受众（audience）- 如大一本科生、高中生、研究生等
4. 重点难点（difficulty_focus）- 本节课最需要重点突破的点
5. 核心知识点（key_points）- 用逗号分隔
6. 计划课时（duration）- 如45分钟、2课时
7. 课件风格（style）- 如简洁学术、活泼互动、图文并茂

对话风格：亲切、专业、简洁。每次只问一个问题或确认一项信息。
当你已经收集到全部7项信息后，在回复末尾另起一行，输出以下标记（不要有多余内容）：
[INTENT_READY]
{"topic":"...","teaching_goal":"...","audience":"...","difficulty_focus":"...","key_points":["...","..."],"duration":"...","style":"..."}

注意：key_points 必须是数组，每个元素是一个独立知识点。"""


def chat_with_claude(messages: list[dict]) -> str:
    """多轮对话（优先 DeepSeek）"""
    return _chat(messages, system=CHAT_SYSTEM)


def chat_stream(messages: list[dict]):
    """流式多轮对话，yield 文本片段"""
    if _get_deepseek_key():
        try:
            yield from _deepseek_chat_stream(messages, system=CHAT_SYSTEM)
            return
        except Exception as e:
            print(f"[LLM] DeepSeek stream failed ({e}), fallback")
    if _get_dashscope_key():
        try:
            yield from _qwen_chat_stream(messages, system=CHAT_SYSTEM)
            return
        except Exception as e:
            print(f"[LLM] Qwen stream failed ({e}), fallback")
    yield _claude_chat(messages, system=CHAT_SYSTEM)


def generate_slides_json(intent: dict, rag_chunks: list[str]) -> dict:
    """
    一次调用生成完整课件 JSON。
    返回 {"theme": {...}, "pages": [{...}, ...]}
    """
    topic = intent.get("topic", "未知主题")
    teaching_goal = intent.get("teaching_goal", "明确本节课目标并达成可评估学习结果")
    audience = intent.get("audience", "学生")
    key_points = intent.get("key_points", [])
    difficulty_focus = intent.get("difficulty_focus", key_points[-1] if key_points else "关键难点")
    duration = intent.get("duration", "45分钟")
    style = intent.get("style", "简洁学术")
    rag_text = "\n".join(rag_chunks[:5]) if rag_chunks else ""
    rag_section = f"\n\n参考资料（可适当引用）：\n{rag_text[:800]}" if rag_text else ""

    # 复利知识库上下文
    knowledge_context = intent.get("knowledge_context", "")

    kp_list = "、".join(key_points)

    prompt = f"""你是一位顶级课件设计师。请为以下课程生成一份完整的 PPT 课件内容。

课程信息：
- 主题：{topic}
- 教学目标：{teaching_goal}
- 受众：{audience}
- 重点难点：{difficulty_focus}
- 课时：{duration}
- 风格：{style}
- 核心知识点：{kp_list}{rag_section}{knowledge_context}

可用幻灯片类型（严格按以下 JSON 格式，字段名不能改变）：
1. {{"type":"cover","title":"课程名","subtitle":"受众 · 课时"}}
2. {{"type":"agenda","title":"目录","items":["知识点1","知识点2","知识点3"]}}
3. {{"type":"content","title":"章节标题","bullets":["完整知识点描述1","完整知识点描述2","完整知识点描述3"],"tip":"教学提示"}}
4. {{"type":"code","title":"代码示例","language":"python","code":"实际可运行代码","explanation":"代码说明"}}
5. {{"type":"formula","title":"公式推导","formulas":[{{"label":"公式名","expr":"LaTeX表达式"}}],"explanation":"说明"}}
6. {{"type":"example","title":"例题","problem":"题目描述","steps":["步骤1","步骤2"],"answer":"最终答案"}}
7. {{"type":"two_column","title":"对比标题","left":{{"heading":"左列标题","points":["要点1","要点2"]}},"right":{{"heading":"右列标题","points":["要点1","要点2"]}}}}
8. {{"type":"quote","title":"引言","text":"引用内容"}}
9. {{"type":"summary","title":"总结","takeaways":["收获1","收获2","收获3"]}}
10. {{"type":"animation","title":"动画标题","template":"flowchart","template_data":{{"accent":"#60a5fa","steps":["步骤1","步骤2"]}}}}

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

主题色根据风格（请严格按照风格选择，支持浅色和深色）：
- 简洁学术 → {{"primary":"#1e3a5f","accent":"#60a5fa","text":"#f0f7ff","bg2":"#2d4f7a"}}
- 活泼互动 → {{"primary":"#ffffff","accent":"#7c3aed","text":"#1e1b4b","bg2":"#f5f3ff"}}
- 图文并茂 → {{"primary":"#fafafa","accent":"#059669","text":"#064e3b","bg2":"#ecfdf5"}}
- 商务专业 → {{"primary":"#18181b","accent":"#f59e0b","text":"#fef9c3","bg2":"#27272a"}}
- 清新教育 → {{"primary":"#eff6ff","accent":"#2563eb","text":"#1e3a8a","bg2":"#dbeafe"}}
- 科技感 → {{"primary":"#020617","accent":"#22d3ee","text":"#e0f2fe","bg2":"#0f172a"}}

【输出要求】严格遵守：
1. 只输出纯 JSON，不要任何解释文字，不要 markdown 代码块（不要```）
2. 必须生成 8-12 页幻灯片
3. 每页内容必须详实具体，bullets 每条至少 15 字，表达完整的知识点而非关键词
4. 所有字段必须填写，不能出现空字符串或空数组
5. 格式：{{"theme":{{"primary":"#1e3a5f","accent":"#60a5fa","text":"#f0f7ff"}},"pages":[{{"type":"cover","title":"...","subtitle":"..."}},...]}}"""

    text = _chat([{"role": "user", "content": prompt}])
    text = text.strip()
    # 去掉 markdown 代码块包裹（```json ... ``` 或 ``` ... ```）
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()
    # 提取最外层 JSON 对象
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            result = json.loads(match.group())
            # 基本校验
            if isinstance(result.get('pages'), list) and len(result['pages']) > 0:
                return _normalize_slides(result)
        except json.JSONDecodeError as e:
            print(f"[LLM] JSON parse error: {e}\nRaw text: {text[:500]}")
    print(f"[LLM] generate_slides_json fallback. Raw: {text[:300]}")
    return _fallback_slides(intent)


def _normalize_slides(data: dict) -> dict:
    """规范化 LLM 输出，统一字段名，避免前端渲染空白"""
    pages = data.get('pages', [])
    normalized = []
    for p in pages:
        t = p.get('type', 'content')
        # agenda: items 兼容 points/chapters/sections
        if t == 'agenda':
            p['items'] = p.get('items') or p.get('points') or p.get('chapters') or p.get('sections') or []
        # content: bullets 兼容 points/items/keyPoints
        if t in ('content', 'summary'):
            p['bullets'] = p.get('bullets') or p.get('points') or p.get('items') or p.get('keyPoints') or []
            if t == 'summary':
                p['takeaways'] = p.get('takeaways') or p.get('bullets') or p.get('points') or []
        # two_column: 兼容各种嵌套
        if t == 'two_column':
            left = p.get('left') or p.get('column1') or p.get('leftColumn') or {}
            right = p.get('right') or p.get('column2') or p.get('rightColumn') or {}
            left['points'] = left.get('points') or left.get('bullets') or left.get('items') or []
            right['points'] = right.get('points') or right.get('bullets') or right.get('items') or []
            p['left'] = left
            p['right'] = right
        # example: steps 兼容 process/procedure
        if t == 'example':
            p['steps'] = p.get('steps') or p.get('process') or p.get('procedure') or []
        normalized.append(p)
    data['pages'] = normalized
    return data


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


