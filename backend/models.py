"""Shared domain models for current/target pipeline convergence."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class TeachingSpecModel(BaseModel):
    topic: str
    audience: str | None = None
    goals: list[str] = Field(default_factory=list)
    key_points: list[str] = Field(default_factory=list)
    difficult_points: list[str] = Field(default_factory=list)
    duration_minutes: int | None = None
    style: str | None = None
    mode: str = "mode_a"
    must_include: list[str] = Field(default_factory=list)
    must_avoid: list[str] = Field(default_factory=list)
    uploaded_source_ids: list[str] = Field(default_factory=list)


class SourceChunk(BaseModel):
    chunk_id: str
    source_id: str
    source_name: str
    source_type: str
    page_no: int | None = None
    text: str
    score: float | None = None


class EvidenceRef(BaseModel):
    chunk_id: str
    source_id: str
    source_name: str
    page_no: int | None = None
    snippet: str
    score: float | None = None


class SlidePlan(BaseModel):
    slide_id: str
    title: str
    slide_type: str
    intent: str
    target_bullet_count: int = 3
    density_limit: int = 80
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)


class SlideBlock(BaseModel):
    block_id: str
    type: Literal["title", "bullet", "paragraph", "case", "table", "image", "formula"]
    data: dict[str, Any] = Field(default_factory=dict)


class SlideDraftModel(BaseModel):
    slide_id: str
    title: str
    slide_type: str
    blocks: list[SlideBlock] = Field(default_factory=list)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class RevisionPatch(BaseModel):
    slide_id: str
    action: str
    instruction: str
    keep_title: bool = True
    keep_layout: bool = True
