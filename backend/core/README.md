# Backend Core Map

## Purpose

`backend/core/` contains the main product behavior: intent normalization, retrieval, parsing, generation, block normalization, and export.

## Main modules

- `teaching_spec.py`: compile raw intent into stable teaching fields
- `llm.py`: chat, generation, revise, and provider-facing prompt logic
- `rag.py`: hybrid retrieval path and fallbacks
- `source_index.py`: source metadata registration and lookup
- `parser.py`: parse uploaded files into chunkable content
- `slide_blocks.py`: attach normalized `blocks[]`
- `ppt_gen.py`: PPTX export bridge
- `doc_gen.py`: DOCX lesson-plan export
- `compound_knowledge.py`: reusable knowledge enrichment
- `video_parser.py`: video-specific extraction path

## Read this before editing

- `../../ai-context/CAPABILITY_INDEX.yaml`
- relevant cards in `../../ai-context/capabilities/`

## Design intent

- Keep the main user path stable:
  - normalize intent
  - retrieve context
  - generate content
  - attach evidence
  - normalize blocks
  - export
- Prefer strengthening current modules over adding parallel abstractions.

