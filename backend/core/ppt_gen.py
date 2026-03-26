"""使用 python-pptx 生成 .pptx 课件"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import os


SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

COLOR_BG = RGBColor(0x1A, 0x1A, 0x2E)       # 深蓝背景
COLOR_ACCENT = RGBColor(0x16, 0x21, 0x3E)   # 次背景
COLOR_HL = RGBColor(0x0F, 0x3A, 0x7A)       # 蓝色高亮
COLOR_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
COLOR_YELLOW = RGBColor(0xFF, 0xD7, 0x00)
COLOR_LIGHT = RGBColor(0xB0, 0xC4, 0xDE)


def _add_bg(slide, prs):
    """给幻灯片填充深色背景"""
    from pptx.util import Emu
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = COLOR_BG


def _add_textbox(slide, text, left, top, width, height,
                 font_size=24, bold=False, color=None, align=PP_ALIGN.LEFT, wrap=True):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color or COLOR_WHITE
    return txBox


def _add_rect(slide, left, top, width, height, color):
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def _cover_slide(prs, topic, audience, duration):
    slide_layout = prs.slide_layouts[6]  # blank
    slide = prs.slides.add_slide(slide_layout)
    _add_bg(slide, prs)
    # 顶部装饰条
    _add_rect(slide, 0, 0, SLIDE_W, Inches(0.08), COLOR_YELLOW)
    # 主标题
    _add_textbox(slide, topic,
                 Inches(1), Inches(2), Inches(11), Inches(1.5),
                 font_size=44, bold=True, color=COLOR_WHITE, align=PP_ALIGN.CENTER)
    # 副标题
    sub = f"适用对象：{audience}　|　课时：{duration}"
    _add_textbox(slide, sub,
                 Inches(1), Inches(3.8), Inches(11), Inches(0.6),
                 font_size=20, color=COLOR_LIGHT, align=PP_ALIGN.CENTER)
    # 底部
    _add_textbox(slide, "TeachMind · AI 智能备课系统",
                 Inches(1), Inches(6.5), Inches(11), Inches(0.5),
                 font_size=14, color=COLOR_LIGHT, align=PP_ALIGN.CENTER)
    return slide


def _toc_slide(prs, key_points):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_bg(slide, prs)
    _add_rect(slide, 0, 0, SLIDE_W, Inches(0.08), COLOR_YELLOW)
    _add_textbox(slide, "目  录",
                 Inches(0.8), Inches(0.3), Inches(6), Inches(0.8),
                 font_size=32, bold=True, color=COLOR_YELLOW)
    for i, kp in enumerate(key_points):
        y = Inches(1.4 + i * 0.85)
        _add_rect(slide, Inches(0.8), y + Inches(0.1), Inches(0.35), Inches(0.45), COLOR_HL)
        _add_textbox(slide, str(i + 1),
                     Inches(0.85), y, Inches(0.3), Inches(0.65),
                     font_size=18, bold=True, color=COLOR_WHITE, align=PP_ALIGN.CENTER)
        _add_textbox(slide, kp,
                     Inches(1.4), y, Inches(10), Inches(0.65),
                     font_size=22, color=COLOR_WHITE)
    return slide


def _content_slide(prs, title, bullets, rag_context=""):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_bg(slide, prs)
    _add_rect(slide, 0, 0, Inches(0.5), SLIDE_H, COLOR_HL)
    _add_rect(slide, 0, 0, SLIDE_W, Inches(0.08), COLOR_YELLOW)
    _add_textbox(slide, title,
                 Inches(0.8), Inches(0.2), Inches(11), Inches(0.9),
                 font_size=30, bold=True, color=COLOR_YELLOW)
    # 分隔线效果
    _add_rect(slide, Inches(0.8), Inches(1.15), Inches(11.5), Inches(0.04), COLOR_HL)
    # 内容要点
    for i, b in enumerate(bullets):
        y = Inches(1.35 + i * 0.85)
        if y + Inches(0.85) > SLIDE_H - Inches(0.3):
            break
        _add_rect(slide, Inches(0.8), y + Inches(0.18), Inches(0.12), Inches(0.35), COLOR_YELLOW)
        _add_textbox(slide, b,
                     Inches(1.1), y, Inches(11.2), Inches(0.75),
                     font_size=20, color=COLOR_WHITE)
    # RAG 参考（右下角小字）
    if rag_context:
        snippet = rag_context[:80] + "..." if len(rag_context) > 80 else rag_context
        _add_textbox(slide, f"📚 参考：{snippet}",
                     Inches(0.8), Inches(6.8), Inches(11.5), Inches(0.45),
                     font_size=11, color=COLOR_LIGHT)
    return slide


def _summary_slide(prs, topic, key_points):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_bg(slide, prs)
    _add_rect(slide, 0, 0, SLIDE_W, Inches(0.08), COLOR_YELLOW)
    _add_textbox(slide, "课程小结",
                 Inches(0.8), Inches(0.3), Inches(6), Inches(0.8),
                 font_size=32, bold=True, color=COLOR_YELLOW)
    _add_textbox(slide, f"本节课围绕「{topic}」，共覆盖以下核心知识点：",
                 Inches(0.8), Inches(1.3), Inches(11.5), Inches(0.6),
                 font_size=20, color=COLOR_LIGHT)
    for i, kp in enumerate(key_points):
        y = Inches(2.1 + i * 0.75)
        _add_textbox(slide, f"✓  {kp}",
                     Inches(1.2), y, Inches(10), Inches(0.65),
                     font_size=20, color=COLOR_WHITE)
    _add_textbox(slide, "感谢聆听，欢迎提问！",
                 Inches(0.8), Inches(6.5), Inches(11.5), Inches(0.6),
                 font_size=22, bold=True, color=COLOR_YELLOW, align=PP_ALIGN.CENTER)
    return slide


def generate_pptx(intent: dict, rag_chunks: list[str], output_path: str) -> str:
    """
    根据 intent JSON 和 RAG 检索结果生成 .pptx 文件。
    返回输出文件路径。
    """
    topic = intent.get("topic", "未知主题")
    audience = intent.get("audience", "学生")
    key_points = intent.get("key_points", ["核心概念", "基本原理", "实际应用"])
    duration = intent.get("duration", "45分钟")

    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    _cover_slide(prs, topic, audience, duration)
    _toc_slide(prs, key_points)

    for i, kp in enumerate(key_points):
        rag_ctx = rag_chunks[i] if i < len(rag_chunks) else ""
        bullets = [
            f"{kp}的基本概念与定义",
            f"{kp}的核心原理与机制",
            f"{kp}在实际场景中的应用",
            f"常见问题与解决思路",
        ]
        _content_slide(prs, f"{i+1}. {kp}", bullets, rag_ctx)

    _summary_slide(prs, topic, key_points)

    prs.save(output_path)
    return output_path
