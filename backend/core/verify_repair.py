"""Post-generation verification and low-risk repair (P1).

After generation, each page is checked for thin/empty/over-long content. Only
*low-risk* repairs are applied -- a too-thin content/summary page is regenerated
via the per-page Stage-2 generator, and over-long bullets are trimmed. There is
no global redesign and no style drift (the Auto-Slides principle: a repair agent
should only do high-confidence, local, low-risk fixes). Behind VERIFY_REPAIR
(default on); any failure leaves the original content untouched.
"""
from __future__ import annotations

import os
from typing import Any

from core.two_stage_gen import _norm_list, _safe_str, generate_page

MIN_BULLETS = 3
MAX_BULLET_CHARS = 72


def verify_repair_enabled() -> bool:
    """Feature flag. Default ON; set VERIFY_REPAIR=0/false/off to disable."""
    raw = os.environ.get("VERIFY_REPAIR", "1").strip().lower()
    return raw not in {"0", "false", "off", "no"}


def _bullets_of(page: dict) -> list[str]:
    items = page.get("bullets") if page.get("type") != "summary" else page.get("takeaways")
    return [str(b) for b in (items or []) if str(b).strip()]


def _trim(text: str, limit: int = MAX_BULLET_CHARS) -> str:
    text = str(text).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for sep in ("。", "；", ";", "，", ",", "、", " "):
        idx = cut.rfind(sep)
        if idx >= int(limit * 0.6):
            return cut[:idx].rstrip("，,、 ")
    return cut.rstrip() + "…"


def _page_issues(page: dict) -> list[str]:
    issues: list[str] = []
    ptype = str(page.get("type") or "content")
    if ptype in ("content", "summary"):
        bullets = _bullets_of(page)
        if len(bullets) < MIN_BULLETS:
            issues.append("thin")
        if any(len(b) > MAX_BULLET_CHARS for b in bullets):
            issues.append("overlong")
    elif ptype == "formula":
        if not page.get("formulas"):
            issues.append("thin")
    elif ptype == "code":
        if not str(page.get("code") or "").strip():
            issues.append("thin")
    elif ptype == "example":
        if not str(page.get("problem") or "").strip() and not page.get("steps"):
            issues.append("thin")
    elif ptype == "two_column":
        left = (page.get("left") or {}).get("points") or []
        right = (page.get("right") or {}).get("points") or []
        if not left and not right:
            issues.append("thin")
    return issues


def verify_and_repair(
    slides_json: dict, intent: dict, rag_chunks: list[str] | None = None
) -> tuple[dict, dict[str, Any]]:
    """Check every page; apply low-risk repairs. Returns (slides_json, report)."""
    report: dict[str, Any] = {"checked": 0, "issues": [], "repaired": [], "errors": []}
    if not isinstance(slides_json, dict) or not isinstance(slides_json.get("pages"), list):
        return slides_json, report

    pages = slides_json["pages"]
    global_titles = [_safe_str(p.get("title")) for p in pages if isinstance(p, dict)]

    for idx, page in enumerate(pages):
        if not isinstance(page, dict):
            continue
        report["checked"] += 1
        issues = _page_issues(page)
        if not issues:
            continue
        report["issues"].append({"index": idx, "type": page.get("type"), "issues": issues})

        if "overlong" in issues:
            key = "takeaways" if page.get("type") == "summary" else "bullets"
            if isinstance(page.get(key), list):
                page[key] = [_trim(b) for b in page[key]]
                report["repaired"].append({"index": idx, "action": "trim"})

        if "thin" in issues and page.get("type") in ("content", "summary"):
            seed = _norm_list(page.get("bullets") or page.get("takeaways")) or [_safe_str(page.get("title"))]
            descriptor = {"title": _safe_str(page.get("title")), "type": "content", "keyPoints": seed[:5]}
            try:
                regen = generate_page(descriptor, global_titles, intent, "")
                new_bullets = [b for b in (regen.get("bullets") or []) if str(b).strip()]
                if len(new_bullets) >= MIN_BULLETS:
                    if page.get("type") == "summary":
                        page["takeaways"] = new_bullets
                    else:
                        page["bullets"] = new_bullets
                        if regen.get("tip"):
                            page["tip"] = regen["tip"]
                    report["repaired"].append({"index": idx, "action": "regenerate"})
            except Exception as exc:  # noqa: BLE001 - repair must never break generation
                report["errors"].append(str(exc))

    meta = slides_json.get("meta") if isinstance(slides_json.get("meta"), dict) else {}
    meta["verify_repair"] = {"issues": len(report["issues"]), "repaired": len(report["repaired"])}
    slides_json["meta"] = meta
    return slides_json, report
