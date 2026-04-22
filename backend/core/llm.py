"""LLM integration helpers for chat, slide generation, revision, and embeddings."""
from __future__ import annotations

import hashlib
import json
import os
import re
from copy import deepcopy


def _get_deepseek_key() -> str:
    return os.environ.get("DEEPSEEK_API_KEY", "").strip()


def _get_dashscope_key() -> str:
    return os.environ.get("DASHSCOPE_API_KEY", "").strip()


def _get_anthropic_key() -> str:
    return os.environ.get("ANTHROPIC_API_KEY", "").strip()


def _deepseek_chat(messages: list[dict], system: str = "", model: str = "deepseek-chat") -> str:
    from openai import OpenAI

    client = OpenAI(api_key=_get_deepseek_key(), base_url="https://api.deepseek.com")
    full_messages: list[dict] = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)
    response = client.chat.completions.create(model=model, messages=full_messages, max_tokens=4096)
    return response.choices[0].message.content or ""


def _deepseek_chat_stream(messages: list[dict], system: str = "", model: str = "deepseek-chat"):
    from openai import OpenAI

    client = OpenAI(api_key=_get_deepseek_key(), base_url="https://api.deepseek.com")
    full_messages: list[dict] = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)

    stream = client.chat.completions.create(
        model=model,
        messages=full_messages,
        max_tokens=4096,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def _qwen_chat(messages: list[dict], system: str = "", model: str = "qwen-max") -> str:
    import dashscope
    from dashscope import Generation

    dashscope.api_key = _get_dashscope_key()
    full_messages: list[dict] = []
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
    full_messages: list[dict] = []
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


def _claude_chat(messages: list[dict], system: str = "", model: str = "claude-haiku-4-5-20251001") -> str:
    import anthropic

    api_key = _get_anthropic_key()
    kwargs: dict[str, str] = {"api_key": api_key}
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "").strip()
    if base_url:
        kwargs["base_url"] = base_url

    client = anthropic.Anthropic(**kwargs)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system or "",
        messages=messages,
    )
    return response.content[0].text


def _local_chat_fallback(messages: list[dict]) -> str:
    """Fallback for local demo when no online LLM key is configured."""
    last_user = ""
    for item in reversed(messages):
        if item.get("role") == "user":
            last_user = str(item.get("content", "")).strip()
            break

    if not last_user:
        return "已收到请求。请提供：课程主题、教学目标、学生类型、课时长短、重点难点。"

    return f"已收到：{last_user}\n请继续补充：教学目标、学生类型、课时长短、重点难点。"


def _chat(messages: list[dict], system: str = "", model: str = "deepseek-chat") -> str:
    # model is reserved for compatibility; current routing is key-driven.
    _ = model
    if _get_deepseek_key():
        try:
            return _deepseek_chat(messages, system=system)
        except Exception as exc:
            print(f"[LLM] DeepSeek failed ({exc}), trying DashScope")

    if _get_dashscope_key():
        try:
            return _qwen_chat(messages, system=system)
        except Exception as exc:
            print(f"[LLM] DashScope failed ({exc}), trying Claude")

    if _get_anthropic_key():
        try:
            return _claude_chat(messages, system=system)
        except Exception as exc:
            print(f"[LLM] Claude failed ({exc}), using local fallback")

    return _local_chat_fallback(messages)


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _extract_json_obj(text: str) -> dict | None:
    cleaned = _strip_json_fence(text)
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


CHAT_SYSTEM = """
你是中文教学设计助手，专门帮助教师澄清备课意图并生成结构化信息。
必须始终使用简体中文回复，回答简洁、实用、可执行。
当信息充分时，在回复末尾附加：
[INTENT_READY]
{"topic":"...","teaching_goal":"...","audience":"...","difficulty_focus":"...","key_points":["..."],"duration":"...","style":"..."}
"""


def chat_with_claude(messages: list[dict]) -> str:
    return _chat(messages, system=CHAT_SYSTEM)


def chat_stream(messages: list[dict]):
    if _get_deepseek_key():
        try:
            yield from _deepseek_chat_stream(messages, system=CHAT_SYSTEM)
            return
        except Exception as exc:
            print(f"[LLM] DeepSeek stream failed ({exc}), fallback")

    if _get_dashscope_key():
        try:
            yield from _qwen_chat_stream(messages, system=CHAT_SYSTEM)
            return
        except Exception as exc:
            print(f"[LLM] Qwen stream failed ({exc}), fallback")

    if _get_anthropic_key():
        try:
            yield _claude_chat(messages, system=CHAT_SYSTEM)
            return
        except Exception as exc:
            print(f"[LLM] Claude stream failed ({exc}), fallback")

    yield _local_chat_fallback(messages)


def _normalize_slides(data: dict) -> dict:
    pages = data.get("pages", [])
    if not isinstance(pages, list):
        data["pages"] = []
        return data

    normalized: list[dict] = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        page_type = page.get("type", "content")
        if page_type == "agenda":
            page["items"] = page.get("items") or page.get("points") or page.get("chapters") or []
        if page_type in ("content", "summary"):
            bullets = page.get("bullets") or page.get("points") or page.get("items") or []
            if page_type == "content":
                page["bullets"] = bullets
            else:
                page["takeaways"] = page.get("takeaways") or bullets
        if page_type == "two_column":
            left = page.get("left") or {}
            right = page.get("right") or {}
            left["points"] = left.get("points") or left.get("items") or []
            right["points"] = right.get("points") or right.get("items") or []
            page["left"] = left
            page["right"] = right
        if page_type == "example":
            page["steps"] = page.get("steps") or page.get("process") or []
        normalized.append(page)

    data["pages"] = normalized
    if not isinstance(data.get("theme"), dict):
        data["theme"] = {"primary": "#0f172a", "accent": "#60a5fa", "text": "#f8fafc"}
    return data


def _fallback_slides(intent: dict) -> dict:
    topic = str(intent.get("topic") or "Course")
    audience = str(intent.get("audience") or "Learners")
    duration = str(intent.get("duration") or "45 min")
    key_points = intent.get("key_points") or ["Core concept", "Key principle", "Classroom application"]
    key_points = [str(item) for item in key_points if str(item).strip()]

    preserve_structure = bool(intent.get("preserve_structure", False))
    reference_outline = intent.get("reference_outline") or []
    if preserve_structure and reference_outline:
        key_points = [str(item).strip() for item in reference_outline if str(item).strip()][:8] or key_points

    pages: list[dict] = [
        {"type": "cover", "title": topic, "subtitle": f"{audience} | {duration}"},
        {"type": "agenda", "title": "Agenda", "items": key_points[:8]},
    ]
    for kp in key_points[:8]:
        pages.append(
            {
                "type": "content",
                "title": kp,
                "bullets": [
                    f"Define {kp} and explain classroom context",
                    f"Explain key principles and common misunderstandings of {kp}",
                    f"Provide classroom exercise suggestions for {kp}",
                ],
                "tip": "Use one concrete classroom case for explanation",
            }
        )

    pages.append(
        {
            "type": "summary",
            "title": "Summary",
            "takeaways": [f"Understand {kp}" for kp in key_points[:3]],
        }
    )

    return {
        "theme": {"primary": "#0f172a", "accent": "#60a5fa", "text": "#f8fafc"},
        "pages": pages,
    }


def generate_slides_json(intent: dict, rag_chunks: list[str]) -> dict:
    topic = str(intent.get("topic") or "Untitled topic")
    teaching_goal = str(intent.get("teaching_goal") or "Help learners understand and apply concepts")
    audience = str(intent.get("audience") or "Students")
    key_points = [str(item) for item in (intent.get("key_points") or []) if str(item).strip()]
    difficulty_focus = str(intent.get("difficulty_focus") or (key_points[-1] if key_points else "Key difficulty"))
    duration = str(intent.get("duration") or "45 min")
    style = str(intent.get("style") or "Structured and clear")
    preserve_structure = bool(intent.get("preserve_structure", False))
    reference_outline = [str(item) for item in (intent.get("reference_outline") or []) if str(item).strip()]
    slide_plan = intent.get("slide_plan") or []
    plan_lines: list[str] = []
    if isinstance(slide_plan, list):
        for item in slide_plan[:20]:
            if not isinstance(item, dict):
                continue
            slide_id = str(item.get("slide_id", "")).strip()
            title = str(item.get("title", "")).strip()
            objective = str(item.get("objective", "")).strip()
            slide_type = str(item.get("slide_type", "")).strip()
            if title:
                plan_lines.append(f"- {slide_id or 'auto'} | {slide_type or 'content'} | {title} | {objective}")

    rag_context = "\n".join(rag_chunks[:6])[:1200] if rag_chunks else ""
    knowledge_context = str(intent.get("knowledge_context") or "")
    kp_list = ", ".join(key_points) if key_points else "None"

    reference_section = ""
    if preserve_structure and reference_outline:
        ordered_outline = "\n".join(f"{idx + 1}. {item}" for idx, item in enumerate(reference_outline[:20]))
        reference_section = (
            "\nReference structure (keep order whenever possible):\n"
            f"{ordered_outline}\n"
            "Requirement: keep chapter ordering from reference outline, then refresh per-page content."
        )
    plan_section = ""
    if plan_lines:
        plan_section = (
            "\nSlide plan (must follow sequence and titles when possible):\n"
            f"{chr(10).join(plan_lines)}\n"
        )

    prompt = f"""
Generate a complete slides_json object. Output JSON only.
- topic: {topic}
- teaching_goal: {teaching_goal}
- audience: {audience}
- difficulty_focus: {difficulty_focus}
- duration: {duration}
- style: {style}
- key_points: {kp_list}

Reference material:
{rag_context or 'None'}
{knowledge_context}
{reference_section}
{plan_section}

Output schema:
{{
  "theme": {{"primary":"#1e3a5f","accent":"#60a5fa","text":"#f0f7ff"}},
  "pages": [
    {{"type":"cover","title":"...","subtitle":"..."}},
    {{"type":"agenda","title":"Agenda","items":["..."]}},
    {{"type":"content","title":"...","bullets":["...","...","..."],"tip":"..."}},
    {{"type":"summary","title":"Summary","takeaways":["...","...","..."]}}
  ]
}}

Requirements:
1) 8-12 pages.
2) No empty key fields.
3) Prioritize key_points coverage.
4) If slide plan exists, keep the plan order and avoid skipping planned titles.
"""

    text = _chat([{"role": "user", "content": prompt}])
    parsed = _extract_json_obj(text)
    if parsed and isinstance(parsed.get("pages"), list) and parsed["pages"]:
        return _normalize_slides(parsed)

    print(f"[LLM] generate_slides_json fallback. Raw: {text[:300]}")
    return _fallback_slides(intent)


def _fallback_revise(slides: dict, instruction: str, page_indexes: list[int]) -> dict:
    data = deepcopy(slides)
    pages = data.get("pages", [])
    if not isinstance(pages, list):
        return data

    targets = set(page_indexes) if page_indexes else set(range(1, len(pages) + 1))
    for idx, page in enumerate(pages, start=1):
        if idx not in targets or not isinstance(page, dict):
            continue

        page_type = page.get("type", "content")
        if page_type in {"content", "summary"}:
            key = "bullets" if page_type == "content" else "takeaways"
            items = page.get(key)
            if not isinstance(items, list):
                items = []
            items.append(f"Updated per instruction: {instruction}")
            page[key] = items[:8]
        elif page_type == "example":
            steps = page.get("steps")
            if not isinstance(steps, list):
                steps = []
            steps.append(f"Additional step: {instruction}")
            page["steps"] = steps[:6]
        else:
            tip = str(page.get("tip") or "")
            merged = f"{tip}; updated per instruction: {instruction}" if tip else f"Updated per instruction: {instruction}"
            page["tip"] = merged[:220]

    return data


def revise_slides_json(
    original_slides_json: dict,
    instruction: str,
    intent: dict | None = None,
    page_indexes: list[int] | None = None,
) -> dict:
    cleaned_instruction = (instruction or "").strip()
    if not cleaned_instruction:
        return deepcopy(original_slides_json or {})

    slides = deepcopy(original_slides_json or {})
    pages = slides.get("pages")
    if not isinstance(pages, list) or not pages:
        return slides

    selected = [idx for idx in (page_indexes or []) if isinstance(idx, int) and idx > 0]
    target_text = ",".join(str(idx) for idx in selected) if selected else "all pages"

    topic = (intent or {}).get("topic", "")
    audience = (intent or {}).get("audience", "")
    style = (intent or {}).get("style", "")

    prompt = f"""
Revise slides_json and output JSON only:
- target_pages: {target_text}
- instruction: {cleaned_instruction}
- topic: {topic}
- audience: {audience}
- style: {style}

Original slides_json:
{json.dumps(slides, ensure_ascii=False)}
"""

    try:
        text = _chat([{"role": "user", "content": prompt}])
        parsed = _extract_json_obj(text)
        if parsed and isinstance(parsed.get("pages"), list) and parsed["pages"]:
            if "theme" not in parsed and isinstance(slides.get("theme"), dict):
                parsed["theme"] = slides["theme"]
            return _normalize_slides(parsed)
    except Exception as exc:
        print(f"[LLM] revise_slides_json fallback: {exc}")

    return _fallback_revise(slides, cleaned_instruction, selected)


def describe_image(image_base64: str, prompt: str = "") -> str:
    if _get_dashscope_key():
        import dashscope
        from dashscope import MultiModalConversation

        dashscope.api_key = _get_dashscope_key()
        final_prompt = prompt or "Describe key visual content for teaching usage."
        response = MultiModalConversation.call(
            model="qwen-vl-max",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"image": f"data:image/jpeg;base64,{image_base64}"},
                        {"text": final_prompt},
                    ],
                }
            ],
        )
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            if isinstance(content, list) and content:
                return content[0].get("text", "")
            return str(content)
        raise RuntimeError(f"Qwen-VL error {response.status_code}: {response.message}")

    _ = image_base64
    return prompt or "Image uploaded. (No vision model key configured; skipped semantic description.)"


def _hash_embedding(text: str, dim: int = 64) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    for i in range(dim):
        b = digest[i % len(digest)]
        values.append((b / 255.0) * 2.0 - 1.0)
    return values


def embed_texts(texts: list[str]) -> list[list[float]]:
    if _get_dashscope_key():
        import dashscope
        from dashscope import TextEmbedding

        dashscope.api_key = _get_dashscope_key()
        embeddings: list[list[float]] = []
        for i in range(0, len(texts), 25):
            batch = texts[i : i + 25]
            resp = TextEmbedding.call(model="text-embedding-v3", input=batch)
            if resp.status_code != 200:
                raise RuntimeError(f"Embedding error {resp.status_code}: {resp.message}")
            items = sorted(resp.output["embeddings"], key=lambda x: x["text_index"])
            embeddings.extend([item["embedding"] for item in items])
        return embeddings

    return [_hash_embedding(str(text)) for text in texts]
