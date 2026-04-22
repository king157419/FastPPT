# Capability: revise-loop

## What it is

The editing path that modifies existing `slides_json` based on user instructions instead of discarding the whole result.

## Read when

- page-level updates are weak
- users ask to modify one page or a few sections
- deciding between regenerate and revise

## Source of truth

- `backend/api/generate.py`
- `backend/core/llm.py`
- `frontend/src/components/PreviewPanel.vue`

## Current status

- `partial`
- Entry path exists and now emits a `RevisionPatch`
- Quality of local edits is still below target for strict page-level control

## Inputs / outputs

- Input: existing `slides_json`, revise instruction, optional page indexes
- Output: `RevisionPatch` plus patched `slides_json`
- Current patch ops: `add_slide`, `delete_slide`, `move_slide`, `replace_slide`

## Known gaps

- Some fallback revise behavior is still simplistic.
- Mode A style structure-preserving updates are not fully realized.
- Block-level patch granularity is still limited.
