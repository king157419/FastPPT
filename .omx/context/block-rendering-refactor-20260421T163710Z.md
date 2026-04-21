# Ralph Context Snapshot

- task statement: Refactor frontend rendering to be block-driven (blocks[]) in Ralph mode.
- desired outcome: Slide preview and PPTX export no longer rely primarily on page.type branching; use block dispatch and keep backward compatibility.
- known facts/evidence:
  - backend attaches blocks via backend/core/slide_blocks.py
  - frontend preview still renders by page.type in SlideRenderer.vue and export path in PreviewPanel.vue
  - build currently passes before this refactor
- constraints:
  - keep existing UX stable
  - no new dependencies
  - maintain compatibility when blocks are missing
- unknowns/open questions:
  - exact block->pptx style parity for all existing page types
- likely codebase touchpoints:
  - frontend/src/components/SlideRenderer.vue
  - frontend/src/components/PreviewPanel.vue
