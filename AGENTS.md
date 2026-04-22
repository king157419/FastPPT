# FastPPT Repository Guidance

This repository uses a layered context model for both humans and coding agents.

## Read order

1. Read `ai-context/PROJECT.md` for product scope, architecture boundaries, and current maturity.
2. Read `ai-context/CAPABILITY_INDEX.yaml` to find the relevant capability cards.
3. Read only the 1 to 3 cards that match the task.
4. Then read the concrete code and local module README files.

## Source-of-truth rules

- `ai-context/` is the fast entry layer for current understanding.
- `docs/product/` and `docs/engineering/` hold stable narrative docs.
- `docs/archive/strategy-history/` is historical context, not the default entry point.
- If behavior changes, update the relevant capability card and any local module README that is now stale.

## Local navigation

- `backend/api/README.md`: API entry points and route ownership
- `backend/core/README.md`: generation, retrieval, export, and normalization internals
- `frontend/src/components/README.md`: UI responsibilities and flow ownership

