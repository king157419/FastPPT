# Capability: rag-evidence

## What it is

The retrieval path that pulls context from uploaded materials and attaches evidence into generation outputs.

## Read when

- retrieval feels weak
- generated content cannot be traced
- storage or persistence behavior is being changed

## Source of truth

- `backend/core/rag.py`
- `backend/core/source_index.py`
- `backend/api/generate.py`

## Current status

- `partial`
- Hybrid retrieval exists
- Evidence attachment exists, but fidelity is not yet a finished system

## Inputs / outputs

- Input: uploaded files, parsed chunks, generation intent
- Output:
  - retrieval snippets
  - source metadata
  - page-level or generation-level evidence payloads

## Important behavior

- Retrieval strategy falls back through configured vector options to TF-IDF.
- Redis caching is effectively disabled in current contest-safe path.
- Generation attaches evidence after raw slide JSON is produced.

## Known gaps

- Long-term persistence is not fully hardened.
- Evidence structure is still weaker than the intended "every page can clearly cite sources" goal.
- Chunk metadata and source localization can be improved further.

