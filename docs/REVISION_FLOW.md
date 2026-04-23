# Revision Flow (Current)

## Purpose

Describe the grounded revise flow in the current code path.

## Flow

1. Client sends `slides_json`, `instruction`, optional `page_indexes` to `/api/generate/revise`.
2. Backend compiles `TeachingSpec` from intent fields.
3. Backend calls `revise_slides_json(...)` to produce revised candidate pages.
4. Backend builds `RevisionPatch` from original vs revised payload.
5. Backend applies patch to original slides with slide-id-first semantics.
6. Backend normalizes blocks and re-exports PPTX.
7. Response returns:
  - patched `slides_json`
  - `revision_patch`
  - `block_summary`
  - revised ppt filename

## Current guarantees

- page-level revise supports add/delete/move/replace operations in patch model
- asynchronous and synchronous generation now align on outline->plan ordering

## Known limits

- block-level patch is not fully implemented
- complex cross-version patch replay still needs stronger hardening

