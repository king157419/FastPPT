"""Two-stage slide generation: outline planning -> concurrent per-page content.

Why this exists
---------------
The legacy ``core.llm.generate_slides_json`` asks the LLM to produce an entire
8-12 page deck in a single 4096-token completion. The token budget is split
across every page, so each page ends up thin ("hollow content"). This module
follows the OpenMAIC pattern instead:

* **Stage 1 (outline)** - one cheap LLM call assigns each content page 3-5
  *specific* knowledge points (not vague titles).
* **Stage 2 (per page)** - every content page gets its own focused LLM call,
  run concurrently. Each page now owns the full token budget and only has to
  expand its own knowledge points, so content is substantially richer.

``generate_slides_json_two_stage`` is a drop-in replacement for
``generate_slides_json`` (same ``(intent, rag_chunks) -> dict`` signature) and
falls back to the legacy single-shot generator if Stage 1 fails, so it can never
break the existing pipeline.
"""
from __future__ import annotations

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from core.llm import (
    _chat,
    _extract_json_obj,
    _normalize_slides,
    generate_slides_json,
)

DEFAULT_THEME = {"primary": "#1e3a5f", "accent": "#60a5fa", "text": "#f0f7ff"}
MAX_CONTENT_PAGES = 12
MIN_CONTENT_PAGES = 3
MAX_WORKERS = 6
CONTENT_PAGE_TYPES = {"content", "formula", "code", "example", "two_column", "chart"}


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def _safe_str(value: Any, default: str = "") -> str:
    text = str(value).strip() if value is not None else ""
    return text or default


def _norm_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


_PLACEHOLDER_RE = re.compile(r"[<>]")


def _clean_points(value: Any) -> list[str]:
    """Drop placeholder/echoed junk (e.g. '<沿用上面的标题>', '...', '。。。')."""
    out: list[str] = []
    for item in _norm_list(value):
        if _PLACEHOLDER_RE.search(item):
            continue
        if not item.strip(".。、 ·-—…"):
            continue
        out.append(item)
    return out


_CODE_SIGNALS = re.compile(
    r"代码|算法|函数|实现|编程|语法|程序|脚本|命令|伪代码|遍历|递归|SQL|API|def |class |for |while |code",
    re.IGNORECASE,
)
_FORMULA_SIGNALS = re.compile(
    r"公式|定理|方程|推导|证明|积分|导数|微分|极限|级数|矩阵|向量|概率|分布|期望|方差|不等式|求和|sqrt|frac"
)


def _ensure_rich_coverage(outline: list[dict]) -> list[dict]:
    """Safety net: if the deck shows strong code/formula signals but the planner
    left every page as 'content', upgrade the single strongest-signal page so the
    renderer's code/formula capabilities actually get exercised for that subject."""
    present = {p.get("type") for p in outline}
    for rich, pattern in (("code", _CODE_SIGNALS), ("formula", _FORMULA_SIGNALS)):
        if rich in present:
            continue
        best, best_score = None, 0
        for page in outline:
            if page.get("type") != "content":
                continue
            text = f"{page.get('title', '')} {' '.join(page.get('keyPoints', []))}"
            score = len(pattern.findall(text))
            if score > best_score:
                best, best_score = page, score
        if best is not None and best_score > 0:
            best["type"] = rich
            present.add(rich)
    return outline


def _content_titles_from_plan(intent: dict) -> list[str]:
    """Titles of the planned content pages, preserving order (pipeline case)."""
    plan = intent.get("slide_plan")
    titles: list[str] = []
    if isinstance(plan, list):
        for item in plan:
            if isinstance(item, dict) and str(item.get("slide_type")) == "content":
                title = _safe_str(item.get("title"))
                if title:
                    titles.append(title)
    return titles


def _seed_titles(intent: dict) -> list[str]:
    """Resolve the ordered list of content-page titles to plan against."""
    titles = _content_titles_from_plan(intent)
    if titles:
        return titles[:MAX_CONTENT_PAGES]

    # Standalone / no plan: prefer Mode-A reference outline, else key_points.
    if intent.get("preserve_structure"):
        titles = _norm_list(intent.get("reference_outline"))
        if titles:
            return titles[:MAX_CONTENT_PAGES]

    titles = _norm_list(intent.get("key_points"))
    if not titles:
        titles = ["核心概念", "关键原理", "课堂应用"]
    return titles[:MAX_CONTENT_PAGES]


# --------------------------------------------------------------------------- #
# Stage 1 - outline planning
# --------------------------------------------------------------------------- #
_OUTLINE_SYSTEM = "你是资深高校教学设计专家，擅长把一节课拆解成结构清晰、知识点具体的幻灯片大纲。必须使用简体中文，只输出 JSON。"


def _build_outline_prompt(intent: dict, titles: list[str], rag_context: str) -> str:
    topic = _safe_str(intent.get("topic"), "未命名课程")
    teaching_goal = _safe_str(intent.get("teaching_goal"), "帮助学生理解并应用本节核心概念")
    audience = _safe_str(intent.get("audience"), "本科生")
    difficulty_focus = _safe_str(intent.get("difficulty_focus"))
    style = _safe_str(intent.get("style"), "简洁学术")
    numbered = "\n".join(f"{idx + 1}. {title}" for idx, title in enumerate(titles))

    return f"""请为下面这节课的【内容页】规划知识点大纲。

课程主题：{topic}
教学目标：{teaching_goal}
面向学生：{audience}
重点难点：{difficulty_focus or '未特别指定'}
讲授风格：{style}

参考资料（可用于提炼知识点，没有则忽略）：
{rag_context or '无'}

需要规划的内容页（保持顺序与数量，不要增删页）：
{numbered}

要求：
1) 为每一页给出 3-5 个【具体】知识点（keyPoints），每条要可讲解、有信息量。
   反例（太空泛，禁止）：「介绍 IPv6 地址」「讲解基本原理」
   正例（具体）：「IPv6 用 128 位地址，写作 8 组 16 位十六进制，可省略前导零与连续零段」
2) 为每页选择最合适的页类型 type，让课件有恰当的富类型，不要所有页都用 content：
   - formula：本页核心是数学公式/定理/方程/推导/统计模型 → 用 formula（数学/理工类课程通常应有 1-2 页）
   - code：本页核心是代码/算法实现/编程示例/命令/SQL → 用 code（计算机/编程类课程通常应有 1-2 页）
   - two_column：本页是两个概念/方法/方案的对比 → 用 two_column
   - example：本页是例题/案例的求解步骤 → 用 example
   - chart：本页核心是数据/趋势/占比且适合可视化 → 用 chart
   - content：以上都不典型时用（要点讲解）
   判据：标题或知识点含"公式/定理/方程/推导/积分/导数/概率"→formula；含"代码/算法/函数/实现/语法/SQL"→code；含"对比/区别/优缺点"→two_column；含"例题/求解/计算步骤"→example
3) 严格保持给定页数与顺序，用 index 对应上面的页（标题已固定，无需返回标题）。

只输出 JSON：
{{"pages":[{{"index":1,"type":"content","keyPoints":["...","...","..."]}}]}}"""


def _fallback_outline(titles: list[str]) -> list[dict]:
    return [
        {"index": idx + 1, "type": "content", "title": title, "keyPoints": [title]}
        for idx, title in enumerate(titles)
    ]


def generate_outline(intent: dict, rag_chunks: list[str]) -> list[dict]:
    """Stage 1: return one descriptor per content page with specific keyPoints."""
    titles = _seed_titles(intent)
    rag_context = "\n".join(rag_chunks[:6])[:1200] if rag_chunks else ""

    prompt = _build_outline_prompt(intent, titles, rag_context)
    text = _chat([{"role": "user", "content": prompt}], system=_OUTLINE_SYSTEM)
    parsed = _extract_json_obj(text)

    pages = parsed.get("pages") if isinstance(parsed, dict) else None
    if not isinstance(pages, list) or not pages:
        return _fallback_outline(titles)

    # Map model output back by index. Titles stay authoritative (the model only
    # supplies type + keyPoints), so agenda/plan ordering can never drift and the
    # model can't echo a placeholder into a title.
    by_index: dict[int, dict] = {}
    for item in pages:
        if not isinstance(item, dict):
            continue
        try:
            by_index[int(item.get("index"))] = item
        except (TypeError, ValueError):
            continue

    outline: list[dict] = []
    for idx, title in enumerate(titles):
        match = by_index.get(idx + 1)
        if match is None and idx < len(pages) and isinstance(pages[idx], dict):
            match = pages[idx]
        match = match or {}

        key_points = _clean_points(match.get("keyPoints") or match.get("key_points")) or [title]
        page_type = _safe_str(match.get("type"), "content")
        if page_type not in CONTENT_PAGE_TYPES:
            page_type = "content"
        outline.append(
            {
                "index": idx + 1,
                "type": page_type,
                "title": title,
                "keyPoints": key_points[:5],
            }
        )
    return _ensure_rich_coverage(outline)


# --------------------------------------------------------------------------- #
# Stage 2 - per-page content generation
# --------------------------------------------------------------------------- #
_PAGE_SYSTEM = (
    "你是资深高校教学设计专家，正在逐页打磨教学幻灯片。"
    "牢记：幻灯片是视觉辅助，不是讲稿——写要点、短语、数据、公式，"
    "不要写完整口语段落或「下面我们来看」这类过渡语。必须使用简体中文，只输出 JSON。"
)

_PAGE_SCHEMA_HINT = """根据页类型(type)输出对应字段，只输出 JSON：
- content：{"type":"content","title":"...","bullets":["以关键术语开头、≤24字、句式平行、含具体信息(定义/数据/对比/步骤)","..."],"tip":"给老师的一句讲解提示","notes":"可选：本页讲稿要点"}
- formula：{"type":"formula","title":"...","formulas":[{"label":"名称","expr":"合法LaTeX公式(标准LaTeX数学语法:分数frac/根号sqrt/求和sum/积分int/上标^/下标_;禁止中文与$符号)","explanation":"中文含义"}],"explanation":"整体说明"} （至少给出1-2个核心公式）
- code：{"type":"code","title":"...","language":"python","code":"真实可运行的多行示例代码(含简短注释)","explanation":"代码讲解"}
- example：{"type":"example","title":"...","problem":"题目","steps":["求解步骤1","步骤2"],"answer":"答案"}
- two_column：{"type":"two_column","title":"...","left":{"title":"左栏标题","points":["..."]},"right":{"title":"右栏标题","points":["..."]}}
- chart：{"type":"chart","title":"...","chartType":"bar|line|pie","data":{"labels":["..."],"values":[数字]},"caption":"图注"}"""


def _build_page_prompt(page: dict, global_titles: list[str], intent: dict, page_rag: str) -> str:
    topic = _safe_str(intent.get("topic"), "本课程")
    audience = _safe_str(intent.get("audience"), "本科生")
    style = _safe_str(intent.get("style"), "简洁学术")
    title = _safe_str(page.get("title"))
    page_type = _safe_str(page.get("type"), "content")
    key_points = _norm_list(page.get("keyPoints"))
    kp_block = "\n".join(f"  - {kp}" for kp in key_points) or "  - （围绕标题展开）"
    outline_block = "\n".join(f"{idx + 1}. {t}" for idx, t in enumerate(global_titles))

    return f"""请只为【当前这一页】生成详实的幻灯片内容。

课程：{topic}（面向{audience}，风格：{style}）

全课内容页大纲（仅供上下文，避免与其它页重复；不要复述其它页）：
{outline_block}

当前页：
- 标题：{title}
- 页类型：{page_type}
- 本页必须讲清的知识点：
{kp_block}

相关参考资料（可引用，没有则忽略）：
{page_rag or '无'}

要求：
1) 内容要具体、有信息量，体现学科深度，优先覆盖上面列出的知识点。
2) content 页给 4-6 条要点；每条 ≤24 字、以关键术语开头、句式平行，是实质信息（定义/数据/对比/步骤/易错点），杜绝空话与完整口语句。
3) 不要写过渡语、不要写完整口语句子。

{_PAGE_SCHEMA_HINT}"""


def _fallback_page(page: dict) -> dict:
    """Deterministic but structured page if the LLM call/parse fails."""
    title = _safe_str(page.get("title"), "知识点")
    key_points = _norm_list(page.get("keyPoints")) or [title]
    bullets = []
    for kp in key_points:
        bullets.append(kp if len(kp) > 6 else f"{kp}：核心定义与适用场景")
    if len(bullets) < 3:
        bullets.append(f"{title}的常见易错点与课堂提问")
    return {
        "type": "content",
        "title": title,
        "bullets": bullets[:6],
        "tip": f"结合一个具体案例讲解「{title}」",
    }


def _coerce_page(raw: dict, page: dict) -> dict:
    """Validate/normalize an LLM page result; keep title from the outline."""
    page_type = _safe_str(raw.get("type"), _safe_str(page.get("type"), "content"))
    # Keep the authoritative outline title; never let the per-page model rename it
    # (renaming would break agenda/plan/slide_id alignment).
    title = _safe_str(page.get("title")) or _safe_str(raw.get("title"))
    result: dict[str, Any] = {"type": page_type, "title": title}

    if page_type == "formula":
        formulas = raw.get("formulas")
        result["formulas"] = formulas if isinstance(formulas, list) and formulas else []
        result["explanation"] = _safe_str(raw.get("explanation"))
        if not result["formulas"]:
            return _fallback_page(page)
    elif page_type == "code":
        result["language"] = _safe_str(raw.get("language"), "text")
        result["code"] = _safe_str(raw.get("code"))
        result["explanation"] = _safe_str(raw.get("explanation"))
        if not result["code"]:
            return _fallback_page(page)
    elif page_type == "example":
        result["problem"] = _safe_str(raw.get("problem"))
        result["steps"] = _norm_list(raw.get("steps"))
        result["answer"] = _safe_str(raw.get("answer"))
        if not result["problem"] and not result["steps"]:
            return _fallback_page(page)
    elif page_type == "two_column":
        left = raw.get("left") if isinstance(raw.get("left"), dict) else {}
        right = raw.get("right") if isinstance(raw.get("right"), dict) else {}
        result["left"] = {"title": _safe_str(left.get("title")), "points": _norm_list(left.get("points"))}
        result["right"] = {"title": _safe_str(right.get("title")), "points": _norm_list(right.get("points"))}
        if not result["left"]["points"] and not result["right"]["points"]:
            return _fallback_page(page)
    else:  # content (default)
        bullets = _norm_list(raw.get("bullets") or raw.get("points") or raw.get("items"))
        if not bullets:
            return _fallback_page(page)
        result["type"] = "content"
        result["bullets"] = bullets[:6]
        result["tip"] = _safe_str(raw.get("tip"))
        notes = _safe_str(raw.get("notes"))
        if notes:
            result["notes"] = notes
    return result


def generate_page(page: dict, global_titles: list[str], intent: dict, page_rag: str) -> dict:
    """Stage 2: generate a single content page (one LLM call)."""
    try:
        prompt = _build_page_prompt(page, global_titles, intent, page_rag)
        text = _chat([{"role": "user", "content": prompt}], system=_PAGE_SYSTEM)
        parsed = _extract_json_obj(text)
        if isinstance(parsed, dict):
            return _coerce_page(parsed, page)
    except Exception as exc:  # noqa: BLE001 - never let one page break the deck
        print(f"[two_stage] page generation failed for '{page.get('title')}': {exc}")
    return _fallback_page(page)


# --------------------------------------------------------------------------- #
# assembly
# --------------------------------------------------------------------------- #
def _cover_page(intent: dict) -> dict:
    topic = _safe_str(intent.get("topic"), "未命名课程")
    audience = _safe_str(intent.get("audience"), "学生")
    duration = _safe_str(intent.get("duration"), "45分钟")
    return {"type": "cover", "title": topic, "subtitle": f"适用对象：{audience}　|　课时：{duration}"}


def _agenda_page(titles: list[str]) -> dict:
    return {"type": "agenda", "title": "课程导航", "items": titles}


def _summary_page(intent: dict, outline: list[dict]) -> dict:
    takeaways: list[str] = []
    for page in outline:
        title = _safe_str(page.get("title"))
        if title and 2 <= len(title) <= 24:
            takeaways.append(title)  # clean recap of what each page covered
            continue
        kps = _clean_points(page.get("keyPoints"))
        raw = kps[0] if kps else title
        crisp = re.split(r"[：:。，,；;]", raw)[0].strip() if raw else ""
        takeaways.append(crisp[:24] if crisp else title)
    takeaways = _clean_points(takeaways)
    seen: set[str] = set()
    deduped = [t for t in takeaways if t and not (t in seen or seen.add(t))]
    if not deduped:
        deduped = _norm_list(intent.get("key_points")) or ["回顾本节核心知识点"]
    return {"type": "summary", "title": "课堂小结", "takeaways": deduped[:6]}


def _page_rag(page: dict, rag_chunks: list[str]) -> str:
    """Pick the chunks most relevant to this page's title/keyPoints (cheap lexical)."""
    if not rag_chunks:
        return ""
    terms = [_safe_str(page.get("title"))] + _norm_list(page.get("keyPoints"))
    terms = [t for t in terms if t]
    scored: list[tuple[int, str]] = []
    for chunk in rag_chunks:
        score = sum(1 for t in terms if t and t in chunk)
        scored.append((score, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    picked = [chunk for score, chunk in scored if score > 0][:3]
    if not picked:
        picked = rag_chunks[:2]
    return "\n".join(picked)[:1000]


def generate_slides_json_two_stage(intent: dict, rag_chunks: list[str]) -> dict:
    """Drop-in replacement for generate_slides_json using outline -> per-page.

    Falls back to the legacy single-shot generator if Stage 1 planning fails.
    """
    rag_chunks = [str(c) for c in (rag_chunks or []) if str(c).strip()]
    try:
        outline = generate_outline(intent, rag_chunks)
        if not outline:
            raise ValueError("empty outline")
    except Exception as exc:  # noqa: BLE001
        print(f"[two_stage] outline planning failed ({exc}); falling back to single-shot")
        return generate_slides_json(intent, rag_chunks)

    global_titles = [_safe_str(p.get("title")) for p in outline]

    # Stage 2: generate every content page concurrently.
    def _task(page: dict) -> dict:
        return generate_page(page, global_titles, intent, _page_rag(page, rag_chunks))

    workers = max(1, min(MAX_WORKERS, len(outline)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        content_pages = list(pool.map(_task, outline))

    pages: list[dict] = [_cover_page(intent), _agenda_page(global_titles)]
    pages.extend(content_pages)
    pages.append(_summary_page(intent, outline))

    slides_json = {
        "theme": dict(DEFAULT_THEME),
        "pages": pages,
        "meta": {"generator": "two-stage.v1", "content_pages": len(content_pages)},
    }
    return _normalize_slides(slides_json)


def two_stage_enabled() -> bool:
    """Feature flag. Defaults to ON; set TWO_STAGE_GEN=0/false/off to disable."""
    raw = os.environ.get("TWO_STAGE_GEN", "1").strip().lower()
    return raw not in {"0", "false", "off", "no"}
