# Frontend Component Map

## Purpose

`frontend/src/components/` owns the user-facing lesson-prep workflow.

## Main components

- `FileUpload.vue`: upload and file-state entry
- `DocumentPanel.vue`: knowledge and document-side controls
- `ChatPanel.vue`: clarification chat
- `GenerateBtn.vue`: generation preflight and trigger
- `PreviewPanel.vue`: output review, evidence folding, and revise entry
- `SlideRenderer.vue`: actual per-slide render logic

## Read this before editing

- `../../../ai-context/CAPABILITY_INDEX.yaml`
- `../../../ai-context/capabilities/chat-clarification.md`
- `../../../ai-context/capabilities/preview-renderer.md`
- `../../../ai-context/capabilities/slide-blocks.md`

## UI ownership

- Keep upload, chat, generate, and preview as a coherent single flow.
- Do not add UI switches for advanced backend modes unless those modes are stable and intentional.
- If preview behavior changes, update the relevant capability card.

