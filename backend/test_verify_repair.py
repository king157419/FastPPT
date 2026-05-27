"""Offline tests for verify_and_repair (stubs the per-page generator)."""
from __future__ import annotations

import core.verify_repair as vr


def test_thin_content_regenerated(monkeypatch):
    def fake_gen(descriptor, titles, intent, rag):
        return {
            "type": "content",
            "title": descriptor["title"],
            "bullets": ["要点一内容", "要点二内容", "要点三内容", "要点四内容"],
            "tip": "讲解提示",
        }

    monkeypatch.setattr(vr, "generate_page", fake_gen)
    sj = {
        "pages": [
            {"type": "cover", "title": "封面"},
            {"type": "content", "title": "薄页", "bullets": ["只有一条"]},
            {"type": "summary", "title": "小结", "takeaways": ["甲", "乙", "丙"]},
        ]
    }
    out, report = vr.verify_and_repair(sj, {"topic": "x"})
    assert len(out["pages"][1]["bullets"]) >= vr.MIN_BULLETS
    assert any(r["action"] == "regenerate" for r in report["repaired"])


def test_overlong_bullets_trimmed():
    long_bullet = "这是一条非常冗长的要点" * 10  # ~110 chars, no separators
    sj = {"pages": [{"type": "content", "title": "超长", "bullets": [long_bullet, "短要点二", "短要点三"]}]}
    out, report = vr.verify_and_repair(sj, {"topic": "x"})
    assert all(len(b) <= vr.MAX_BULLET_CHARS + 1 for b in out["pages"][0]["bullets"])
    assert any(r["action"] == "trim" for r in report["repaired"])


def test_good_pages_untouched(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("good pages must not be regenerated")

    monkeypatch.setattr(vr, "generate_page", boom)
    sj = {"pages": [{"type": "content", "title": "好页", "bullets": ["要点一", "要点二", "要点三", "要点四"]}]}
    out, report = vr.verify_and_repair(sj, {"topic": "x"})
    assert report["issues"] == []
    assert report["repaired"] == []
