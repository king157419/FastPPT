# IR Schema (Current Baseline)

This document defines the minimum intermediate representations currently used by FastPPT.

## TeachingSpec

- source: `backend/core/teaching_spec.py`
- role: normalized generation input
- key fields:
  - `topic`
  - `teaching_goal`
  - `audience`
  - `duration`
  - `style`
  - `key_points`
  - `difficulty_focus`

## SlidePlanItem

- source: `backend/core/slide_pipeline.py`
- role: high-level page planning unit
- key fields:
  - `slide_id`
  - `title`
  - `slide_type`
  - `objective`
  - `key_point`

## SlideDraft

- source: `backend/core/slide_pipeline.py`
- role: structured draft before block normalization
- key fields:
  - `slide_id`
  - `slide_type`
  - `title`
  - `content`
  - `evidence`

## RevisionPatch / RevisionOperation

- source: `backend/core/slide_pipeline.py`
- role: delta representation for revise
- operation set:
  - `add_slide`
  - `delete_slide`
  - `move_slide`
  - `replace_slide`

## slides_json + blocks

- source: `backend/core/slide_blocks.py`
- role: preview/export payload with page-level and block-level information
- note:
  - blocks are attached but export path is not yet fully block-first

