"""Generate a Chinese lesson-plan (教案) DOCX from the generated deck + intent.

Unlike the previous version (English, generic template, ignored the generated
slides), this builds a real 教案 from ``slides_json``: per-page teaching content
(bullets / formulas / code / examples / comparisons + speaker notes), plus
teaching goal, key/difficult points, blackboard design, homework and sources.
``slides_json`` is optional so old callers keep working.
"""
from __future__ import annotations

import datetime
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

_SKIP_TYPES = {"cover", "agenda"}


def _safe_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _page_bullets(page: dict) -> list[str]:
    return _safe_list(page.get("bullets") or page.get("takeaways") or page.get("points"))


def _add_notes_and_tip(doc: Document, page: dict) -> None:
    notes = str(page.get("notes") or "").strip()
    if notes:
        p = doc.add_paragraph()
        run = p.add_run(f"讲解要点：{notes}")
        run.italic = True
        run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    tip = str(page.get("tip") or "").strip()
    if tip:
        p = doc.add_paragraph()
        run = p.add_run(f"教学提示：{tip}")
        run.italic = True
        run.font.color.rgb = RGBColor(0x2E, 0x6F, 0xB7)


def _render_page(doc: Document, page: dict) -> None:
    ptype = str(page.get("type") or "content")
    if ptype in _SKIP_TYPES:
        return
    title = str(page.get("title") or "")

    if ptype == "summary":
        doc.add_heading("课堂小结", level=2)
        for item in _safe_list(page.get("takeaways")):
            doc.add_paragraph(item, style="List Bullet")
        return

    doc.add_heading(title or "教学环节", level=2)

    if ptype == "formula":
        for fm in (page.get("formulas") or []):
            if isinstance(fm, dict):
                line = f"{fm.get('label', '公式')}： {fm.get('expr', '')}"
                if fm.get("explanation"):
                    line += f" （{fm['explanation']}）"
            else:
                line = str(fm)
            doc.add_paragraph(line, style="List Bullet")
        if page.get("explanation"):
            doc.add_paragraph(str(page["explanation"]))
    elif ptype == "code":
        doc.add_paragraph(f"示例代码（{page.get('language', 'text')}）：")
        code_p = doc.add_paragraph(str(page.get("code") or ""))
        for run in code_p.runs:
            run.font.name = "Consolas"
            run.font.size = Pt(9)
        if page.get("explanation"):
            doc.add_paragraph(str(page["explanation"]))
    elif ptype == "example":
        if page.get("problem"):
            doc.add_paragraph(f"题目：{page['problem']}")
        for i, step in enumerate(_safe_list(page.get("steps")), start=1):
            doc.add_paragraph(f"{i}. {step}", style="List Number")
        if page.get("answer"):
            doc.add_paragraph(f"答案：{page['answer']}")
    elif ptype == "two_column":
        for side in ("left", "right"):
            col = page.get(side) if isinstance(page.get(side), dict) else {}
            if col.get("title"):
                doc.add_paragraph(str(col["title"]), style="Intense Quote")
            for point in _safe_list(col.get("points")):
                doc.add_paragraph(point, style="List Bullet")
    else:  # content / chart / image / fallback
        for bullet in _page_bullets(page):
            doc.add_paragraph(bullet, style="List Bullet")

    _add_notes_and_tip(doc, page)


def generate_docx(
    intent: dict,
    rag_chunks: list[str],
    output_path: str,
    evidence_entries: list[dict[str, Any]] | None = None,
    slides_json: dict | None = None,
) -> str:
    topic = str(intent.get("topic") or "课程主题")
    audience = str(intent.get("audience") or "本科生")
    duration = str(intent.get("duration") or "45分钟")
    style = str(intent.get("style") or "简洁学术")
    teaching_goal = str(intent.get("teaching_goal") or "帮助学生理解并应用本节核心概念。")
    difficulty_focus = str(intent.get("difficulty_focus") or "本节重点难点")
    key_points = _safe_list(intent.get("key_points")) or ["核心概念", "基本原理", "实际应用"]
    today = datetime.date.today().strftime("%Y-%m-%d")

    doc = Document()

    title = doc.add_heading(f"《{topic}》教学设计（教案）", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    info = doc.add_table(rows=5, cols=2)
    info.style = "Table Grid"
    for idx, (k, v) in enumerate(
        [("课程主题", topic), ("授课对象", audience), ("课时", duration), ("授课风格", style), ("编制日期", today)]
    ):
        info.rows[idx].cells[0].text = k
        info.rows[idx].cells[1].text = v

    doc.add_heading("一、教学目标", level=1)
    doc.add_paragraph(teaching_goal)

    doc.add_heading("二、教学重点与难点", level=1)
    doc.add_paragraph(f"难点聚焦：{difficulty_focus}")
    for item in key_points:
        doc.add_paragraph(item, style="List Bullet")

    doc.add_heading("三、教学内容与过程", level=1)
    pages = slides_json.get("pages") if isinstance(slides_json, dict) else None
    rendered = 0
    if isinstance(pages, list) and pages:
        for page in pages:
            if isinstance(page, dict):
                before = len(doc.paragraphs)
                _render_page(doc, page)
                if len(doc.paragraphs) > before:
                    rendered += 1
    if rendered == 0:
        # Fallback (no deck available): outline from key points.
        for kp in key_points:
            doc.add_heading(kp, level=2)
            doc.add_paragraph(f"讲解「{kp}」的定义、原理与典型应用，并结合一个具体案例。")

    doc.add_heading("四、板书设计", level=1)
    doc.add_paragraph(f"主板书：{topic}")
    for kp in key_points:
        doc.add_paragraph(kp, style="List Bullet")

    doc.add_heading("五、作业布置", level=1)
    for kp in key_points[:3]:
        doc.add_paragraph(f"复习并用自己的话总结「{kp}」的核心要点。", style="List Number")
    doc.add_paragraph("完成与本节内容相关的练习题，标注疑问点供下次课讨论。", style="List Number")

    if evidence_entries:
        doc.add_heading("六、参考资料与出处", level=1)
        for item in evidence_entries[:20]:
            file_name = str(item.get("file_name") or "未知来源")
            location = str(item.get("page_or_slide") or "")
            snippet = str(item.get("snippet") or "")[:260]
            p = doc.add_paragraph(style="List Number")
            loc = f"（{location}）" if location else ""
            p.add_run(f"{file_name}{loc}\n{snippet}")

    footer = doc.add_paragraph(f"由 TeachMind · FastPPT 生成于 {today}")
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if footer.runs:
        footer.runs[0].font.size = Pt(9)
        footer.runs[0].font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    doc.save(output_path)
    return output_path
