# FastPPT Project Context

## One-line definition

FastPPT is an AI courseware collaboration system for lesson preparation. It is not a generic PPT generator; it prioritizes controllability, source reuse, and teacher-facing revision loops.

## Primary product goal

Given teaching intent and teaching materials, produce previewable and downloadable courseware plus a lesson plan, then support page-level revision with traceable context.

## Current stable main flow

1. Upload files and parse them into chunks and source metadata.
2. Clarify teaching intent through chat and compile it into `TeachingSpec`.
3. Retrieve supporting material from the knowledge layer.
4. Generate `slides_json`.
5. Normalize pages into `blocks[]`.
6. Preview in the frontend.
7. Export PPTX and DOCX.
8. Revise individual pages or the whole deck.

## Product positioning

- Core audience: college teachers and adjacent lesson-prep scenarios
- V1 priority:
  - Mode A: update or execute around teacher-provided structure
  - Mode B: co-create with guided clarification
  - Mode C: full-auto generation as a supplement, not the quality benchmark
- Hard acceptance criteria:
  - content is correct
  - structure is smooth
  - output feels like the teacher's own courseware
  - content can be traced back to provided materials

## Current engineering truth

- Backend is a FastAPI app with separate API and core layers.
- Frontend is a Vue single-page app with upload, chat, generation, and preview panels.
- PPTX export is handled through a local PPTXGenJS service.
- Contest runtime is intentionally frozen to plain chat path by default to avoid agent and Redis drift.

## Current maturity

- Stable enough for demo:
  - upload
  - intent clarification
  - generation
  - preview
  - PPTX and DOCX download
  - revise loop
- Partial / still being hardened:
  - evidence fidelity
  - block-first rendering and export
  - Mode A true structure-preserving updates
  - persistent course memory
- Planned:
  - two-stage outline -> per-page generation
  - richer capability registry around blocks

## Recommended read order by task

- Product / evaluation task:
  - `docs/product/problem-needs.md`
  - `docs/product/product-positioning.md`
  - `docs/product/teacher-feedback.md`
- Generation / retrieval task:
  - `ai-context/capabilities/teaching-spec.md`
  - `ai-context/capabilities/rag-evidence.md`
  - `ai-context/capabilities/generate-pipeline.md`
- Rendering / export task:
  - `ai-context/capabilities/slide-blocks.md`
  - `ai-context/capabilities/preview-renderer.md`
  - `ai-context/capabilities/export-pptx.md`

