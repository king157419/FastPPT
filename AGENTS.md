# FastPPT Repository Guidance

This repository uses a layered context model for both humans and coding agents.

## Read order

1. Read `ai-context/PROJECT_CURRENT.md` for current code-grounded scope and maturity.
2. Read `ai-context/CAPABILITY_INDEX_CURRENT.yaml` to route current capabilities.
3. Read only the 1 to 3 cards that match the task.
4. If work touches roadmap or planned architecture, read `ai-context/PROJECT_TARGET.md` and `ai-context/CAPABILITY_INDEX_TARGET.yaml`.
5. Then read concrete code and local module README files.

## Source-of-truth rules

- `ai-context/` is the fast entry layer for current understanding.
- `docs/product/` and `docs/engineering/` hold stable narrative docs.
- `docs/archive/strategy-history/` is historical context, not the default entry point.
- If behavior changes, update the relevant capability card and any local module README that is now stale.
- `current` facts take priority over `target` design notes when they conflict.

## Local navigation

- `backend/api/README.md`: API entry points and route ownership
- `backend/core/README.md`: generation, retrieval, export, and normalization internals
- `frontend/src/components/README.md`: UI responsibilities and flow ownership
