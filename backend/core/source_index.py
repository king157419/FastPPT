"""In-memory source index for contest demo evidence and reference-outline support."""
from __future__ import annotations

import re
from typing import Any

_file_registry: dict[str, dict[str, Any]] = {}
_chunk_registry: dict[str, list[dict[str, Any]]] = {}


def reset_all() -> None:
    _file_registry.clear()
    _chunk_registry.clear()


def register_file(file_id: str, filename: str, path: str, ext: str) -> None:
    _file_registry[file_id] = {
        "file_id": file_id,
        "file_name": filename,
        "path": path,
        "ext": ext.lower(),
        "outline": [],
    }


def update_outline(file_id: str, outline: list[str]) -> None:
    if file_id not in _file_registry:
        return
    _file_registry[file_id]["outline"] = [str(item).strip() for item in (outline or []) if str(item).strip()]


def add_chunks(file_id: str, chunks: list[dict[str, Any]]) -> None:
    rows: list[dict[str, Any]] = []
    file_meta = _file_registry.get(file_id, {})
    for item in chunks or []:
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        row = {
            "file_id": file_id,
            "file_name": file_meta.get("file_name", ""),
            "text": text,
            "page_or_slide": str(metadata.get("page_or_slide", "")),
            "chunk_index": int(metadata.get("chunk_index", 0) or 0),
        }
        rows.append(row)
    _chunk_registry[file_id] = rows


def get_file(file_id: str) -> dict[str, Any] | None:
    return _file_registry.get(file_id)


def choose_reference_outline(file_ids: list[str] | None = None) -> tuple[list[str], dict[str, Any] | None]:
    candidates: list[dict[str, Any]] = []
    targets = file_ids or list(_file_registry.keys())
    for file_id in targets:
        meta = _file_registry.get(file_id)
        if not meta:
            continue
        if meta.get("ext") not in {".pptx", ".ppt"}:
            continue
        outline = meta.get("outline") or []
        if outline:
            candidates.append(meta)

    if not candidates:
        return [], None

    best = max(candidates, key=lambda item: len(item.get("outline") or []))
    return list(best.get("outline") or []), best


def _tokenize(text: str) -> set[str]:
    raw = re.findall(r"[a-zA-Z0-9_\u4e00-\u9fff]+", (text or "").lower())
    return {token for token in raw if len(token) >= 1}


def search_chunks(query: str, top_k: int = 5, file_ids: list[str] | None = None) -> list[dict[str, Any]]:
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    candidate_ids = file_ids or list(_chunk_registry.keys())
    scored: list[dict[str, Any]] = []

    for file_id in candidate_ids:
        rows = _chunk_registry.get(file_id, [])
        for row in rows:
            tokens = _tokenize(row.get("text", ""))
            if not tokens:
                continue
            overlap = query_tokens.intersection(tokens)
            if not overlap:
                continue

            score = len(overlap) / (len(query_tokens) + 0.5)
            scored.append(
                {
                    **row,
                    "score": round(score, 4),
                    "snippet": row.get("text", "")[:220],
                }
            )

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[: max(1, top_k)]
