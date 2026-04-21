"""TeachingSpec compilation and normalization utilities."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any

_SPLIT_RE = re.compile(r"[,，、；;\n]+")

_DEFAULT_KEY_POINTS = [
    "核心概念",
    "基本原理",
    "实际应用",
]

REQUIRED_PREFLIGHT_FIELDS = (
    "teaching_goal",
    "audience",
    "difficulty_focus",
)

REQUIRED_FIELD_LABELS = {
    "teaching_goal": "教学目标",
    "audience": "面向学生类型",
    "difficulty_focus": "重点难点",
}


def _pick_first(data: dict[str, Any], keys: tuple[str, ...], default: str = "") -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return default


def _normalize_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in _SPLIT_RE.split(value) if item.strip()]
    return []


def _normalize_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "y", "on", "是"}:
            return True
        if lowered in {"0", "false", "no", "n", "off", "否"}:
            return False
    return default


@dataclass
class TeachingSpec:
    topic: str
    teaching_goal: str
    audience: str
    duration: str
    style: str
    key_points: list[str]
    difficulty_focus: str
    must_include_visuals: bool = True
    must_include_latest_cases: bool = True
    required_sources: list[str] = field(default_factory=list)
    optional_sources: list[str] = field(default_factory=list)
    unresolved_fields: list[str] = field(default_factory=list)
    schema_version: str = "teaching-spec.v1"

    def to_intent(self) -> dict[str, Any]:
        """Return a backward-compatible intent payload for existing pipeline."""
        return {
            "topic": self.topic,
            "teaching_goal": self.teaching_goal,
            "audience": self.audience,
            "duration": self.duration,
            "style": self.style,
            "key_points": self.key_points,
            "difficulty_focus": self.difficulty_focus,
            "must_include_visuals": self.must_include_visuals,
            "must_include_latest_cases": self.must_include_latest_cases,
            "required_sources": self.required_sources,
            "optional_sources": self.optional_sources,
            "unresolved_fields": self.unresolved_fields,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def missing_preflight_fields(self) -> list[str]:
        missing = []
        for key in REQUIRED_PREFLIGHT_FIELDS:
            value = getattr(self, key, "")
            if isinstance(value, str):
                if not value.strip():
                    missing.append(key)
            elif not value:
                missing.append(key)
        return missing

    def missing_preflight_labels(self) -> list[str]:
        return [REQUIRED_FIELD_LABELS.get(key, key) for key in self.missing_preflight_fields()]


def compile_teaching_spec(raw_intent: dict[str, Any] | None) -> TeachingSpec:
    """Compile incoming intent into a stable TeachingSpec object."""
    data = raw_intent or {}
    unresolved: list[str] = []

    topic = _pick_first(data, ("topic", "title", "course_topic"))
    if not topic:
        unresolved.append("topic")
        topic = "未命名课程"

    teaching_goal = _pick_first(
        data,
        ("teaching_goal", "goal", "objective", "teaching_objective"),
        default="",
    )
    if not teaching_goal:
        unresolved.append("teaching_goal")

    audience = _pick_first(data, ("audience", "target_audience", "students"), default="本科生")
    if audience == "本科生" and not any(key in data for key in ("audience", "target_audience", "students")):
        unresolved.append("audience")

    duration = _pick_first(data, ("duration", "class_duration", "course_duration"), default="45分钟")
    if duration == "45分钟" and not any(key in data for key in ("duration", "class_duration", "course_duration")):
        unresolved.append("duration")

    style = _pick_first(data, ("style", "ppt_style", "visual_style"), default="简洁学术")
    if style == "简洁学术" and not any(key in data for key in ("style", "ppt_style", "visual_style")):
        unresolved.append("style")

    key_points = _normalize_list(data.get("key_points"))
    if not key_points:
        key_points = _normalize_list(data.get("core_points"))
    if not key_points:
        key_points = list(_DEFAULT_KEY_POINTS)
        unresolved.append("key_points")

    difficulty_focus = _pick_first(data, ("difficulty_focus", "focus", "hard_part"), default=key_points[-1])
    if not _pick_first(data, ("difficulty_focus", "focus", "hard_part"), default=""):
        unresolved.append("difficulty_focus")

    must_include_visuals = _normalize_bool(
        data.get("must_include_visuals", data.get("need_images")),
        default=True,
    )
    must_include_latest_cases = _normalize_bool(
        data.get("must_include_latest_cases", data.get("need_latest_cases")),
        default=True,
    )

    required_sources = _normalize_list(data.get("required_sources"))
    optional_sources = _normalize_list(data.get("optional_sources"))

    return TeachingSpec(
        topic=topic,
        teaching_goal=teaching_goal,
        audience=audience,
        duration=duration,
        style=style,
        key_points=key_points,
        difficulty_focus=difficulty_focus,
        must_include_visuals=must_include_visuals,
        must_include_latest_cases=must_include_latest_cases,
        required_sources=required_sources,
        optional_sources=optional_sources,
        unresolved_fields=sorted(set(unresolved)),
    )
