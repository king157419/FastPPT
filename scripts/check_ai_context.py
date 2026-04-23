"""Validate ai-context indexes and grounded path references."""
from __future__ import annotations

from pathlib import Path
import re
import sys


REQUIRED_FIELDS = [
    "id",
    "title",
    "status",
    "grounding",
    "summary",
    "verified_paths",
    "read_when",
    "do_not_assume",
]
VALID_STATUS = {"active", "partial", "planned", "deprecated"}


def parse_capabilities(yaml_path: Path) -> list[dict]:
    lines = yaml_path.read_text(encoding="utf-8").splitlines()
    caps: list[dict] = []
    current = None
    list_key = None
    in_caps = False

    for line in lines:
        if line.strip() == "capabilities:":
            in_caps = True
            continue
        if not in_caps:
            continue

        m_new = re.match(r"^\s{2}-\s+id:\s*(.+?)\s*$", line)
        if m_new:
            if current:
                caps.append(current)
            current = {"id": m_new.group(1).strip()}
            list_key = None
            continue

        if current is None:
            continue

        m_key = re.match(r"^\s{4}([a-zA-Z0-9_]+):\s*(.*?)\s*$", line)
        if m_key:
            key = m_key.group(1)
            val = m_key.group(2)
            if val == "":
                current[key] = []
                list_key = key
            else:
                current[key] = val
                list_key = None
            continue

        m_item = re.match(r"^\s{6}-\s*(.+?)\s*$", line)
        if m_item and list_key:
            current.setdefault(list_key, []).append(m_item.group(1).strip())

    if current:
        caps.append(current)
    return caps


def check_file(repo: Path, yaml_path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    caps = parse_capabilities(yaml_path)

    for cap in caps:
        cid = cap.get("id", "<missing-id>")
        for field in REQUIRED_FIELDS:
            if field not in cap:
                errors.append(f"{yaml_path.name}:{cid}: missing field `{field}`")

        status = cap.get("status")
        if status and status not in VALID_STATUS:
            errors.append(f"{yaml_path.name}:{cid}: invalid status `{status}`")

        grounding = cap.get("grounding")
        verified_paths = cap.get("verified_paths", [])
        if isinstance(verified_paths, str):
            verified_paths = [verified_paths]

        if grounding == "current":
            for rel in verified_paths:
                path = repo / rel
                if not path.exists():
                    errors.append(f"{yaml_path.name}:{cid}: missing grounded path `{rel}`")
        elif grounding == "target":
            for rel in verified_paths:
                path = repo / rel
                if not path.exists():
                    warnings.append(f"{yaml_path.name}:{cid}: target path not present yet `{rel}`")
        else:
            errors.append(f"{yaml_path.name}:{cid}: grounding must be `current` or `target`")

    return errors, warnings


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    target_files = [
        repo / "ai-context" / "CAPABILITY_INDEX_CURRENT.yaml",
        repo / "ai-context" / "CAPABILITY_INDEX_TARGET.yaml",
    ]
    all_errors: list[str] = []
    all_warnings: list[str] = []
    for f in target_files:
        if not f.exists():
            all_errors.append(f"missing required file: {f.as_posix()}")
            continue
        errs, warns = check_file(repo, f)
        all_errors.extend(errs)
        all_warnings.extend(warns)

    report = [
        "AI Context Check Report",
        "======================",
        f"errors: {len(all_errors)}",
        f"warnings: {len(all_warnings)}",
        "",
    ]
    report.extend([f"[ERROR] {e}" for e in all_errors])
    report.extend([f"[WARN] {w}" for w in all_warnings])
    out = "\n".join(report) + "\n"
    report_file = repo / "ai-context" / "CHECK_AI_CONTEXT_REPORT.txt"
    report_file.write_text(out, encoding="utf-8")
    print(out)
    print(f"report_file: {report_file}")
    return 1 if all_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

