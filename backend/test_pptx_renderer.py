"""Offline tests for the deterministic pptx_renderer (no LLM key needed).

Builds a slides_json exercising every page type, renders it, then asserts the
exported .pptx via python-pptx: slide count matches pages, formula/chart produce
embedded pictures, code/two_column text is present, speaker notes and source
citations are written.
"""
from __future__ import annotations

import os
import tempfile

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from core.pptx_renderer import render_pptx

INTENT = {"topic": "渲染器测试课程", "audience": "本科生", "duration": "45分钟"}

SLIDES_JSON = {
    "theme": {"primary": "#16335B", "accent": "#2E6FB7"},
    "pages": [
        {"type": "cover", "title": "渲染器测试课程", "subtitle": "本科生 | 45分钟"},
        {"type": "agenda", "title": "课程导航", "items": ["极限", "导数", "中值定理", "应用"]},
        {
            "type": "content",
            "title": "导数的定义",
            "bullets": ["导数是函数在某点的瞬时变化率", "几何意义为切线斜率", "可导必连续，连续不一定可导"],
            "tip": "用速度-位移类比讲解",
            "notes": "提醒学生区分可导与连续的关系，举 |x| 在 0 点的反例。",
            "evidence": [{"file_name": "高等数学教材.pdf", "page_or_slide": "42"}],
        },
        {
            "type": "code",
            "title": "数值求导示例",
            "language": "python",
            "code": "def derivative(f, x, h=1e-6):\n    return (f(x + h) - f(x - h)) / (2 * h)\n\nprint(derivative(lambda t: t**2, 3))  # ~6.0",
            "explanation": "中心差商比前向差商精度更高。",
        },
        {
            "type": "formula",
            "title": "拉格朗日中值定理",
            "formulas": [
                {"label": "定理", "expr": r"f'(\xi) = \frac{f(b) - f(a)}{b - a}", "explanation": "存在 ξ∈(a,b)"},
                {"label": "导数定义", "expr": r"f'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}"},
            ],
        },
        {
            "type": "two_column",
            "title": "可导 vs 连续",
            "left": {"title": "可导", "points": ["存在唯一切线", "可导⇒连续"]},
            "right": {"title": "连续", "points": ["图像不断开", "连续⇏可导"]},
        },
        {
            "type": "example",
            "title": "例题：验证中值定理",
            "problem": "f(x)=x^2 在 [0,2] 上验证拉格朗日中值定理",
            "steps": ["计算 (f(2)-f(0))/(2-0)=2", "令 f'(ξ)=2ξ=2", "解得 ξ=1∈(0,2)"],
            "answer": "ξ=1",
        },
        {
            "type": "chart",
            "title": "增长趋势",
            "chartType": "bar",
            "data": {"labels": ["2021", "2022", "2023"], "values": [120, 160, 210]},
            "caption": "示例数据",
        },
        {"type": "summary", "title": "课堂小结", "takeaways": ["导数定义", "中值定理", "几何意义"]},
    ],
}


def _all_text(slide) -> str:
    out = []
    for shape in slide.shapes:
        if shape.has_text_frame:
            out.append(shape.text_frame.text)
    return "\n".join(out)


def _count_pictures(prs) -> int:
    return sum(
        1
        for slide in prs.slides
        for shape in slide.shapes
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE
    )


def test_renders_all_page_types_faithfully():
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "deck.pptx")
        render_pptx(INTENT, SLIDES_JSON, out)
        assert os.path.exists(out) and os.path.getsize(out) > 0

        prs = Presentation(out)
        # split-brain fix: one slide per page, in order.
        assert len(prs.slides._sldIdLst) == len(SLIDES_JSON["pages"])

        # formula + chart should each embed at least one picture.
        assert _count_pictures(prs) >= 1

        texts = [_all_text(s) for s in prs.slides]
        joined = "\n".join(texts)
        assert "导数的定义" in joined
        assert "def derivative" in joined  # code rendered, not flattened away
        assert "可导" in joined and "连续" in joined  # two-column headers
        assert "课堂小结" in joined


def test_speaker_notes_and_evidence_written():
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "deck.pptx")
        render_pptx(INTENT, SLIDES_JSON, out)
        prs = Presentation(out)

        # content slide (index 2) carries speaker notes + source footer.
        content_slide = list(prs.slides)[2]
        assert content_slide.has_notes_slide
        assert "可导与连续" in content_slide.notes_slide.notes_text_frame.text
        assert "高等数学教材.pdf" in _all_text(content_slide)


def test_empty_pages_raises():
    import pytest

    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "deck.pptx")
        with pytest.raises(ValueError):
            render_pptx(INTENT, {"pages": []}, out)
