"""Deterministic python-pptx renderer that draws slides faithfully from slides_json.pages[].

Why this exists
---------------
The legacy renderer (`ppt_gen._generate_pptx_pythonpptx`) ignored the generated
``pages[]`` and rebuilt a fixed cover/TOC/content/summary deck straight from
``intent.key_points``, flattening every rich block (code / formula / table /
example) into plain bullets. That "split-brain" meant the front-end preview and
the exported .pptx showed different things, and all the rich content was lost.

This renderer draws each page in ``slides_json.pages[]`` according to its own
``type`` -- content, agenda, code (mono dark panel), formula (LaTeX -> matplotlib
PNG), two_column, example, chart, image, summary -- and writes speaker notes and
source citations. It is pure python-pptx (no external PptxGenJS service), so it
is fast and deterministic. Routed behind ``NEW_RENDERER`` (default on).
"""
from __future__ import annotations

import base64
import os
import shutil
import tempfile
from dataclasses import dataclass
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

from PIL import Image  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.dml.color import RGBColor  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: E402
from pptx.oxml.ns import qn  # noqa: E402
from pptx.util import Inches, Pt  # noqa: E402

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
EMU_PER_INCH = 914400

FONT_CN = "Microsoft YaHei"
FONT_MONO = "Consolas"

C_BG = "#FFFFFF"
C_TITLE = "#16335B"
C_ACCENT = "#2E6FB7"
C_TEXT = "#222831"
C_MUTED = "#7A828E"
C_CODE_BG = "#1E1E2E"
C_CODE_FG = "#E6E6E6"


def render_enabled() -> bool:
    """Feature flag. Default ON; set NEW_RENDERER=0/false/off to use legacy path."""
    raw = os.environ.get("NEW_RENDERER", "1").strip().lower()
    return raw not in {"0", "false", "off", "no"}


def _rgb(hexstr: str | None, default: str = "#000000") -> RGBColor:
    s = (hexstr or default).lstrip("#")
    if len(s) != 6:
        s = default.lstrip("#")
    try:
        return RGBColor(int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    except ValueError:
        return RGBColor(0, 0, 0)


@dataclass
class RenderCtx:
    tmpdir: str
    title: RGBColor
    accent: RGBColor
    text: RGBColor
    muted: RGBColor


# --------------------------------------------------------------------------- #
# low-level drawing helpers
# --------------------------------------------------------------------------- #
def _set_font(run, size=None, bold=None, italic=None, color=None, name=FONT_CN) -> None:
    f = run.font
    if size is not None:
        f.size = Pt(size)
    if bold is not None:
        f.bold = bold
    if italic is not None:
        f.italic = italic
    if color is not None:
        f.color.rgb = color
    if name:
        f.name = name
        # Apply the same typeface to East-Asian + complex scripts so Chinese
        # glyphs use the intended font instead of a fallback.
        rpr = run._r.get_or_add_rPr()
        for tag in ("a:latin", "a:ea", "a:cs"):
            el = rpr.find(qn(tag))
            if el is None:
                el = rpr.makeelement(qn(tag), {})
                rpr.append(el)
            el.set("typeface", name)


def _rect(slide, left, top, width, height, color) -> object:
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    try:
        shape.shadow.inherit = False
    except Exception:
        pass
    return shape


def _text(slide, text, left, top, width, height, *, size=18, bold=False, italic=False,
          color=None, align=PP_ALIGN.LEFT, name=FONT_CN, anchor=None, wrap=True):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = wrap
    if anchor is not None:
        tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text or ""
    _set_font(run, size=size, bold=bold, italic=italic, color=color or _rgb(C_TEXT), name=name)
    return box


def _multiline(slide, items, left, top, width, height, *, size=18, color=None,
               name=FONT_CN, marker="", numbered=False, space_after=8, line_spacing=1.08, limit=10):
    items = [str(x).strip() for x in (items or []) if str(x).strip()]
    if not items:
        return None
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items[:limit]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(space_after)
        p.line_spacing = line_spacing
        run = p.add_run()
        if numbered:
            run.text = f"{i + 1:02d}   {item}"
        elif marker:
            run.text = f"{marker}  {item}"
        else:
            run.text = item
        _set_font(run, size=size, color=color or _rgb(C_TEXT), name=name)
    return box


def _bullet_size(n: int) -> int:
    if n <= 4:
        return 20
    if n == 5:
        return 18
    if n == 6:
        return 17
    if n <= 8:
        return 16
    return 14


def _blank(prs, ctx: RenderCtx, *, bar=True):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = _rgb(C_BG)
    if bar:
        _rect(slide, 0, 0, SLIDE_W, Inches(0.16), ctx.accent)
    return slide


def _title(slide, ctx: RenderCtx, text: str) -> None:
    _text(slide, text, Inches(0.7), Inches(0.34), Inches(12.0), Inches(1.0),
          size=30, bold=True, color=ctx.title)
    _rect(slide, Inches(0.75), Inches(1.34), Inches(11.85), Pt(2.4), ctx.accent)


def _tip(slide, ctx: RenderCtx, tip: str) -> None:
    tip = str(tip or "").strip()
    if tip:
        _text(slide, f"教学提示：{tip}", Inches(0.85), Inches(6.74), Inches(11.7),
              Inches(0.5), size=12, italic=True, color=ctx.accent)


def _evidence_footer(slide, ctx: RenderCtx, evidence) -> None:
    if not isinstance(evidence, list) or not evidence:
        return
    parts = []
    for e in evidence[:2]:
        if not isinstance(e, dict):
            continue
        fn = str(e.get("file_name", "")).strip()
        loc = str(e.get("page_or_slide", "")).strip()
        if fn:
            parts.append(fn + (f" p{loc}" if loc else ""))
    if parts:
        _text(slide, "来源：" + "；".join(parts), Inches(0.85), Inches(7.06),
              Inches(11.7), Inches(0.34), size=9, color=ctx.muted)


def _notes(slide, page) -> None:
    notes = str(page.get("notes") or "").strip()
    if notes:
        try:
            slide.notes_slide.notes_text_frame.text = notes
        except Exception:
            pass


# --------------------------------------------------------------------------- #
# matplotlib image helpers
# --------------------------------------------------------------------------- #
def _latex_png(expr: str, tmpdir: str, *, color: str = C_TITLE, fontsize: int = 30) -> str | None:
    expr = str(expr or "").strip()
    if not expr:
        return None
    tex = expr if (expr.startswith("$") and expr.endswith("$")) else f"${expr}$"
    path = os.path.join(tmpdir, f"formula_{uuid4().hex[:8]}.png")
    try:
        fig = plt.figure(figsize=(0.1, 0.1))
        fig.text(0.5, 0.5, tex, fontsize=fontsize, color=color, ha="center", va="center")
        fig.savefig(path, dpi=200, bbox_inches="tight", pad_inches=0.12, transparent=True)
        plt.close(fig)
        return path if os.path.exists(path) else None
    except Exception:
        plt.close("all")
        return None


def _chart_png(chart: dict, tmpdir: str) -> str | None:
    if not isinstance(chart, dict):
        return None
    ctype = str(chart.get("chartType") or chart.get("type") or "bar").lower()
    data = chart.get("data") if isinstance(chart.get("data"), dict) else {}
    labels = [str(x) for x in (data.get("labels") or [])]
    datasets = data.get("datasets") if isinstance(data.get("datasets"), list) else None
    path = os.path.join(tmpdir, f"chart_{uuid4().hex[:8]}.png")
    try:
        fig, ax = plt.subplots(figsize=(7.4, 4.3))
        if datasets:
            for ds in datasets:
                vals = [float(v) for v in (ds.get("data") or []) if _is_num(v)]
                xs = labels[: len(vals)] or list(range(len(vals)))
                if ctype == "line":
                    ax.plot(xs, vals, marker="o", label=str(ds.get("label", "")))
                else:
                    ax.bar(xs, vals, label=str(ds.get("label", "")))
            if any(ds.get("label") for ds in datasets):
                ax.legend()
        else:
            vals = [float(v) for v in (data.get("values") or []) if _is_num(v)]
            if not vals:
                plt.close(fig)
                return None
            xs = labels[: len(vals)] or list(range(len(vals)))
            if ctype == "pie":
                ax.pie(vals, labels=xs, autopct="%1.0f%%")
            elif ctype == "line":
                ax.plot(xs, vals, marker="o")
            else:
                ax.bar(xs, vals)
        ax.tick_params(labelsize=11)
        fig.tight_layout()
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path if os.path.exists(path) else None
    except Exception:
        plt.close("all")
        return None


def _is_num(v) -> bool:
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


def _resolve_image(page: dict, tmpdir: str) -> str | None:
    b64 = page.get("image_base64")
    if isinstance(b64, str) and b64.strip():
        raw = b64.split(",", 1)[1] if b64.strip().startswith("data:") else b64.strip()
        try:
            path = os.path.join(tmpdir, f"img_{uuid4().hex[:8]}.png")
            with open(path, "wb") as fh:
                fh.write(base64.b64decode(raw))
            return path
        except Exception:
            return None
    for key in ("image_path", "path", "image"):
        val = page.get(key)
        if isinstance(val, str) and os.path.exists(val):
            return val
    return None


def _fit_width(img_path: str, max_w_in: float, max_h_in: float) -> float:
    try:
        w, h = Image.open(img_path).size
        if not w or not h:
            return max_w_in
        wn = max_w_in
        hn = wn * h / w
        if hn > max_h_in:
            wn = max_h_in * w / h
        return max(1.0, min(wn, max_w_in))
    except Exception:
        return max_w_in


# --------------------------------------------------------------------------- #
# per-type slide builders
# --------------------------------------------------------------------------- #
def _render_cover(slide, page, ctx: RenderCtx) -> None:
    _text(slide, page.get("title", ""), Inches(1.0), Inches(2.4), Inches(11.33), Inches(1.7),
          size=42, bold=True, color=ctx.title, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    sub = str(page.get("subtitle") or "")
    if sub:
        _text(slide, sub, Inches(1.0), Inches(4.15), Inches(11.33), Inches(0.7),
              size=20, color=ctx.muted, align=PP_ALIGN.CENTER)
    _rect(slide, Inches(5.17), Inches(3.95), Inches(3.0), Pt(2.4), ctx.accent)
    _text(slide, "TeachMind · AI 智能备课", Inches(1.0), Inches(6.7), Inches(11.33), Inches(0.5),
          size=13, color=ctx.muted, align=PP_ALIGN.CENTER)


def _render_agenda(slide, page, ctx: RenderCtx) -> None:
    _title(slide, ctx, page.get("title", "课程导航"))
    items = page.get("items") or page.get("points") or []
    size = 20 if len(items) <= 6 else 18
    _multiline(slide, items, Inches(0.95), Inches(1.7), Inches(11.6), Inches(5.1),
               size=size, numbered=True, space_after=10)


def _render_content(slide, page, ctx: RenderCtx) -> None:
    _title(slide, ctx, page.get("title", ""))
    bullets = page.get("bullets") or page.get("points") or page.get("takeaways") or []
    _multiline(slide, bullets, Inches(0.85), Inches(1.6), Inches(11.7), Inches(5.0),
               size=_bullet_size(len(bullets)), marker="▪", limit=9)
    _tip(slide, ctx, page.get("tip"))


def _render_summary(slide, page, ctx: RenderCtx) -> None:
    _title(slide, ctx, page.get("title", "课堂小结"))
    items = page.get("takeaways") or page.get("bullets") or []
    _multiline(slide, items, Inches(0.85), Inches(1.6), Inches(11.7), Inches(4.6),
               size=_bullet_size(len(items)), marker="✓", limit=8)
    _text(slide, "感谢聆听，欢迎提问！", Inches(0.85), Inches(6.6), Inches(11.7), Inches(0.6),
          size=18, bold=True, color=ctx.accent, align=PP_ALIGN.CENTER)


def _render_code(slide, page, ctx: RenderCtx) -> None:
    _title(slide, ctx, page.get("title", "代码示例"))
    lang = str(page.get("language") or "text")
    code = str(page.get("code") or "")
    expl = str(page.get("explanation") or "").strip()

    panel_top = Inches(1.55)
    panel_h = Inches(4.4) if expl else Inches(5.1)
    _rect(slide, Inches(0.7), panel_top, Inches(11.9), panel_h, _rgb(C_CODE_BG))
    _rect(slide, Inches(11.0), Inches(1.67), Inches(1.45), Inches(0.42), ctx.accent)
    _text(slide, lang, Inches(11.0), Inches(1.67), Inches(1.45), Inches(0.42),
          size=12, bold=True, color=_rgb("#FFFFFF"), align=PP_ALIGN.CENTER)

    lines = code.split("\n")
    csize = 14 if len(lines) <= 18 else 12 if len(lines) <= 26 else 10
    box = slide.shapes.add_textbox(Inches(0.95), Inches(2.15), Inches(11.4), panel_h - Inches(0.7))
    tf = box.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines[:36]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 1.0
        run = p.add_run()
        run.text = line if line else " "
        _set_font(run, size=csize, color=_rgb(C_CODE_FG), name=FONT_MONO)
    if expl:
        _text(slide, expl, Inches(0.7), panel_top + panel_h + Inches(0.12), Inches(11.9),
              Inches(0.8), size=14, color=ctx.text)


def _render_formula(slide, page, ctx: RenderCtx) -> None:
    _title(slide, ctx, page.get("title", "公式推导"))
    formulas = page.get("formulas")
    if not isinstance(formulas, list) or not formulas:
        _multiline(slide, page.get("bullets") or [], Inches(0.85), Inches(1.6),
                   Inches(11.7), Inches(5.0), size=18, marker="▪")
        return

    y = 1.65
    for fm in formulas[:4]:
        if isinstance(fm, dict):
            label = str(fm.get("label") or "")
            expr = str(fm.get("expr") or fm.get("latex") or "")
            fexpl = str(fm.get("explanation") or "")
        else:
            label, expr, fexpl = "", str(fm), ""
        if label:
            _text(slide, label, Inches(0.85), Inches(y), Inches(11.6), Inches(0.4),
                  size=16, bold=True, color=ctx.title)
            y += 0.46
        png = _latex_png(expr, ctx.tmpdir)
        if png:
            disp_w = _fit_width(png, 8.5, 1.8)
            pic = slide.shapes.add_picture(png, Inches(0.95), Inches(y), width=Inches(disp_w))
            y += pic.height / EMU_PER_INCH + 0.18
        else:
            _text(slide, expr, Inches(0.95), Inches(y), Inches(11.4), Inches(0.6),
                  size=18, color=ctx.text, name=FONT_MONO)
            y += 0.7
        if fexpl:
            _text(slide, fexpl, Inches(0.95), Inches(y), Inches(11.5), Inches(0.6),
                  size=13, color=ctx.muted)
            y += 0.58
        if y > 6.4:
            break


def _render_two_column(slide, page, ctx: RenderCtx) -> None:
    _title(slide, ctx, page.get("title", "对比"))
    left = page.get("left") if isinstance(page.get("left"), dict) else {}
    right = page.get("right") if isinstance(page.get("right"), dict) else {}

    def column(x: float, data: dict, header_color: RGBColor) -> None:
        head = str(data.get("title") or "")
        points = [str(p) for p in (data.get("points") or data.get("items") or []) if str(p).strip()]
        _rect(slide, Inches(x), Inches(1.7), Inches(5.7), Inches(0.6), header_color)
        _text(slide, head, Inches(x), Inches(1.72), Inches(5.7), Inches(0.55),
              size=18, bold=True, color=_rgb("#FFFFFF"), align=PP_ALIGN.CENTER)
        _multiline(slide, points, Inches(x + 0.15), Inches(2.5), Inches(5.4), Inches(4.3),
                   size=18 if len(points) <= 5 else 15, marker="•", limit=8, space_after=7)

    column(0.7, left, ctx.accent)
    column(6.93, right, ctx.title)


def _render_example(slide, page, ctx: RenderCtx) -> None:
    _title(slide, ctx, page.get("title", "例题"))
    y = 1.65
    problem = str(page.get("problem") or "")
    if problem:
        _text(slide, f"题目：{problem}", Inches(0.85), Inches(y), Inches(11.6), Inches(1.0),
              size=18, bold=True, color=ctx.title)
        y += 1.0
    steps = [str(s) for s in (page.get("steps") or []) if str(s).strip()]
    if steps:
        _multiline(slide, steps, Inches(0.95), Inches(y), Inches(11.5), Inches(3.6),
                   size=16, numbered=True, limit=8, space_after=7)
        y = min(6.3, y + 0.46 * min(len(steps), 8) + 0.2)
    answer = str(page.get("answer") or "")
    if answer:
        _text(slide, f"答案：{answer}", Inches(0.85), Inches(min(y, 6.4)), Inches(11.6),
              Inches(0.8), size=16, bold=True, color=ctx.accent)


def _render_chart(slide, page, ctx: RenderCtx) -> None:
    _title(slide, ctx, page.get("title", "数据图表"))
    chart = page.get("chart") if isinstance(page.get("chart"), dict) else None
    if chart is None and (page.get("chartType") or page.get("data")):
        chart = {"chartType": page.get("chartType"), "data": page.get("data")}
    png = _chart_png(chart, ctx.tmpdir) if chart else None
    if png:
        disp_w = _fit_width(png, 9.3, 4.7)
        slide.shapes.add_picture(png, Inches((13.333 - disp_w) / 2), Inches(1.7), width=Inches(disp_w))
    else:
        _multiline(slide, page.get("bullets") or [], Inches(0.85), Inches(1.6),
                   Inches(11.7), Inches(5.0), size=18, marker="▪")
    cap = str(page.get("caption") or "")
    if cap:
        _text(slide, cap, Inches(0.85), Inches(6.7), Inches(11.6), Inches(0.5),
              size=13, italic=True, color=ctx.muted, align=PP_ALIGN.CENTER)


def _render_image(slide, page, ctx: RenderCtx) -> None:
    _title(slide, ctx, page.get("title", ""))
    path = _resolve_image(page, ctx.tmpdir)
    if path:
        disp_w = _fit_width(path, 10.5, 4.6)
        slide.shapes.add_picture(path, Inches((13.333 - disp_w) / 2), Inches(1.7), width=Inches(disp_w))
    else:
        _multiline(slide, page.get("bullets") or ["（图片缺失）"], Inches(0.85), Inches(1.7),
                   Inches(11.7), Inches(4.6), size=18, marker="▪")
    cap = str(page.get("caption") or "")
    if cap:
        _text(slide, cap, Inches(0.85), Inches(6.6), Inches(11.6), Inches(0.6),
              size=13, italic=True, color=ctx.muted, align=PP_ALIGN.CENTER)


_BUILDERS = {
    "cover": _render_cover,
    "agenda": _render_agenda,
    "content": _render_content,
    "summary": _render_summary,
    "code": _render_code,
    "formula": _render_formula,
    "two_column": _render_two_column,
    "example": _render_example,
    "chart": _render_chart,
    "image": _render_image,
}


# --------------------------------------------------------------------------- #
# entry point
# --------------------------------------------------------------------------- #
def render_pptx(intent: dict, slides_json: dict, output_path: str) -> str:
    """Render slides_json.pages[] into a .pptx. Raises if there are no pages."""
    pages = slides_json.get("pages") if isinstance(slides_json, dict) else None
    if not isinstance(pages, list) or not pages:
        raise ValueError("slides_json has no pages to render")

    theme = slides_json.get("theme") if isinstance(slides_json.get("theme"), dict) else {}
    ctx = RenderCtx(
        tmpdir=tempfile.mkdtemp(prefix="fastppt_render_"),
        title=_rgb(theme.get("primary"), C_TITLE),
        accent=_rgb(theme.get("accent"), C_ACCENT),
        text=_rgb(C_TEXT),
        muted=_rgb(C_MUTED),
    )
    try:
        prs = Presentation()
        prs.slide_width = SLIDE_W
        prs.slide_height = SLIDE_H

        for page in pages:
            if not isinstance(page, dict):
                continue
            page_type = str(page.get("type") or "content")
            builder = _BUILDERS.get(page_type, _render_content)
            slide = _blank(prs, ctx, bar=(page_type != "cover"))
            try:
                builder(slide, page, ctx)
            except Exception as exc:  # never let one page break the deck
                print(f"[pptx_renderer] page '{page.get('title')}' ({page_type}) failed: {exc}")
                try:
                    _render_content(slide, page, ctx)
                except Exception:
                    pass
            _notes(slide, page)
            _evidence_footer(slide, ctx, page.get("evidence"))

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        prs.save(output_path)
        return output_path
    finally:
        shutil.rmtree(ctx.tmpdir, ignore_errors=True)
