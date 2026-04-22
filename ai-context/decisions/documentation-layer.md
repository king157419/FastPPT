# Decision: layered repository context

## Status

Accepted

## Decision

FastPPT should not use the old step-number documents as the default repository entry point. The repository now uses a layered context model:

1. `ai-context/` for short routing-oriented context
2. stable thematic docs under `docs/product/` and `docs/engineering/`
3. archived historical strategy docs under `docs/archive/strategy-history/`

## Why

- The old step-based filenames were good for a one-time reasoning exercise, not for long-term maintenance.
- Models and new contributors should route to the minimum relevant context instead of re-reading the full historical narrative.
- Capability cards create a stable bridge between product narrative and concrete code.

## Consequences

- New behavior changes should update capability cards, not only raw Markdown notes.
- Historical step docs remain available, but are not the default read path.

