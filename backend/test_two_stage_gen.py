"""Structural tests for the two-stage generator (no live LLM key required).

We stub ``_chat`` so we can prove the architecture without network access:
  * Stage 1 makes exactly one outline call.
  * Stage 2 fans out to one call per content page (the core change vs single-shot).
  * The assembled deck keeps the legacy shape (cover/agenda/content*/summary).
  * A broken Stage 1 safely falls back to the legacy single-shot generator.
"""
from __future__ import annotations

import json

import core.two_stage_gen as tsg


def _plan_intent(n_content: int = 4) -> dict:
    plan = [
        {"slide_id": "s01", "title": "封面", "slide_type": "cover"},
        {"slide_id": "s02", "title": "课程导航", "slide_type": "agenda"},
    ]
    for i in range(n_content):
        plan.append(
            {"slide_id": f"s{i + 3:02d}", "title": f"知识点{i + 1}", "slide_type": "content"}
        )
    plan.append({"slide_id": "s99", "title": "课堂小结", "slide_type": "summary"})
    return {
        "topic": "计算机网络-IPv6 路由原理",
        "teaching_goal": "理解 IPv6 路由原理",
        "audience": "本科三年级",
        "difficulty_focus": "最长前缀匹配",
        "key_points": [f"知识点{i + 1}" for i in range(n_content)],
        "duration": "45分钟",
        "style": "简洁学术",
        "slide_plan": plan,
    }


def _make_fake_chat(calls: list[str]):
    def fake_chat(messages, system: str = "", model: str = "deepseek-chat") -> str:
        content = messages[-1]["content"]
        if "【当前这一页】" in content:  # Stage 2 per-page prompt
            calls.append("page")
            return json.dumps(
                {
                    "type": "content",
                    "title": "X",
                    "bullets": ["实质要点一", "实质要点二", "实质要点三", "实质要点四"],
                    "tip": "结合案例讲解",
                },
                ensure_ascii=False,
            )
        calls.append("outline")  # Stage 1 outline prompt
        return json.dumps(
            {
                "pages": [
                    {"index": i + 1, "type": "content", "title": f"知识点{i + 1}",
                     "keyPoints": ["kp-a", "kp-b", "kp-c"]}
                    for i in range(8)
                ]
            },
            ensure_ascii=False,
        )

    return fake_chat


def test_two_stage_fans_out_per_page(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(tsg, "_chat", _make_fake_chat(calls))

    intent = _plan_intent(n_content=4)
    result = tsg.generate_slides_json_two_stage(intent, rag_chunks=[])

    # Architecture: 1 outline call + 1 call per content page.
    assert calls.count("outline") == 1
    assert calls.count("page") == 4
    assert len(calls) == 5  # vs exactly 1 for the legacy single-shot generator

    pages = result["pages"]
    types = [p["type"] for p in pages]
    assert types == ["cover", "agenda", "content", "content", "content", "content", "summary"]

    # Every content page carries real bullets (not empty).
    for page in pages:
        if page["type"] == "content":
            assert len(page.get("bullets", [])) >= 3


def test_outline_respects_planned_page_count(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(tsg, "_chat", _make_fake_chat(calls))

    # Plan says 6 content pages even though the fake outline returns 8.
    intent = _plan_intent(n_content=6)
    result = tsg.generate_slides_json_two_stage(intent, rag_chunks=[])

    content_pages = [p for p in result["pages"] if p["type"] == "content"]
    assert len(content_pages) == 6  # aligned to plan, keeps index mapping valid
    assert calls.count("page") == 6


def test_falls_back_to_single_shot_when_outline_breaks(monkeypatch):
    sentinel = {"pages": [{"type": "cover", "title": "FALLBACK"}], "theme": {}}

    def broken_chat(messages, system: str = "", model: str = "deepseek-chat") -> str:
        return "this is not json at all"

    monkeypatch.setattr(tsg, "_chat", broken_chat)
    monkeypatch.setattr(tsg, "generate_slides_json", lambda intent, rag: sentinel)

    # No slide_plan -> outline seeds from key_points; broken JSON -> _fallback_outline
    # still yields pages, so Stage 2 runs. To force the *single-shot* fallback we make
    # generate_outline raise instead:
    monkeypatch.setattr(tsg, "generate_outline", lambda intent, rag: (_ for _ in ()).throw(RuntimeError("boom")))

    result = tsg.generate_slides_json_two_stage({"topic": "x", "key_points": ["a"]}, [])
    assert result is sentinel


if __name__ == "__main__":
    # Manual run without pytest: prove fan-out and print a summary.
    calls: list[str] = []
    tsg._chat = _make_fake_chat(calls)  # type: ignore[assignment]
    intent = _plan_intent(n_content=5)
    result = tsg.generate_slides_json_two_stage(intent, [])
    print("Stage1 (outline) calls:", calls.count("outline"))
    print("Stage2 (per-page) calls:", calls.count("page"))
    print("total LLM calls:", len(calls), "(legacy single-shot would be 1)")
    print("page types:", [p["type"] for p in result["pages"]])
    print("sample content page:", json.dumps(result["pages"][2], ensure_ascii=False))
