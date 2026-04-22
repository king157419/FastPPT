# Capability: preview-renderer

## What it is

The frontend rendering path that turns generated slides into a human-reviewable preview before export or revision.

## Read when

- slide preview breaks
- UI needs to display a new block type
- revise workflow needs richer inline controls

## Source of truth

- `frontend/src/components/PreviewPanel.vue`
- `frontend/src/components/SlideRenderer.vue`

## Current status

- `partial`
- Preview works
- Rendering still mixes page-level compatibility with block-level support

## Important behavior

- Preview is a review surface, not just a pretty render.
- It should preserve enough structure for users to understand what will be exported.
- Evidence and block details should stay accessible without overwhelming the default view.

## Known gaps

- Full block-first rendering is not complete.
- Inline page editing can be extended further.

