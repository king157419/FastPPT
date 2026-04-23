"""Generate grounded repository snapshot for ai-context."""
from __future__ import annotations

from pathlib import Path


EXCLUDE_DIRS = {
    ".git",
    ".omc",
    ".omx",
    ".fastppt",
    ".pytest_cache",
    ".pytest_tmp",
    "__pycache__",
    "node_modules",
    "chroma_db",
    "outputs",
    "uploads",
    "logs",
}
EXCLUDE_PREFIXES = (
    ".pytest",
    ".tmp",
)

MAX_DEPTH = 3


def iter_tree(root: Path, base: Path, depth: int = 0):
    if depth > MAX_DEPTH:
        return
    try:
        entries = sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except OSError:
        return

    for entry in entries:
        if entry.name in EXCLUDE_DIRS:
            continue
        if any(entry.name.startswith(prefix) for prefix in EXCLUDE_PREFIXES):
            continue
        rel = entry.relative_to(base).as_posix()
        yield depth, entry.is_dir(), rel
        if entry.is_dir():
            yield from iter_tree(entry, base, depth + 1)


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    out_file = repo / "ai-context" / "REPO_SNAPSHOT.txt"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append(f"repo: {repo.as_posix()}")
    lines.append(f"max_depth: {MAX_DEPTH}")
    lines.append("")

    for depth, is_dir, rel in iter_tree(repo, repo):
        indent = "  " * depth
        marker = "[D]" if is_dir else "[F]"
        lines.append(f"{indent}{marker} {rel}")

    out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
