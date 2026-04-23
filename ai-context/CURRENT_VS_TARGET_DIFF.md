# CURRENT vs TARGET Diff

This file records where current implementation stands versus target architecture.

## 1) Generation core

- current:
  - `TeachingSpec -> SlidePlan -> SlideDraft` objects are wired in `backend/services/generate_service.py`
  - `slides_json` remains the main transport shape
- target:
  - true per-slide worker generation and retry
  - stronger planner contracts between `SlidePlan` and page outputs
- gap:
  - currently still single-LLM-call full page generation before draft mapping

## 2) Revision semantics

- current:
  - `RevisionPatch` exists with `add/delete/move/replace`
  - patch applies with `slide_id`-first behavior
- target:
  - block-level patch granularity
  - stronger cross-version replay guarantees
- gap:
  - complex mixed operations still need deeper property tests

## 3) Evidence and retrieval

- current:
  - page-level evidence is attached and visible in preview
  - source metadata fields (`file_name`, `page_or_slide`, `chunk_index`) are present
- target:
  - stable evidence binding at block granularity
  - stronger retrieval scoring/re-ranking contracts
- gap:
  - evidence is partial and not full block-level source graph

## 4) Export and rendering

- current:
  - preview and export chain works in demo flow
  - PPTX export still mediated by backend renderer gateway
- target:
  - fully block-first export pipeline
  - richer theme/layout token system
- gap:
  - export is not yet a pure block registry pipeline

## 5) Repo governance

- current:
  - split `PROJECT_CURRENT` and `PROJECT_TARGET` exists
  - current/target capability indexes exist
  - thin API routes now delegate orchestration to `backend/services/*`
- target:
  - automated guardrails to prevent mixed claims
- gap:
  - checker added now, but enforcement in CI is pending

## Decision policy

- Accept into `current` only when path exists and behavior is testable.
- Keep forward-looking design in `target` with explicit `planned/partial` status.
- Never claim target features as current implementation.
