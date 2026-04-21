# PRD: Block Rendering Refactor

## Goal
Move rendering and export to block-dispatch architecture while preserving existing behavior.

## Scope
- Block-first rendering in SlideRenderer.
- Block-first PPTX export in PreviewPanel.
- Backward compatibility fallback to page.type.

## Non-goals
- Redesign page aesthetics.
- Introduce new block types.
