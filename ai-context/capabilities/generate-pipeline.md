# Capability: generate-pipeline

## What it is

The main generation flow that produces slide JSON, attaches evidence and blocks, then exports PPTX and DOCX.

## Read when

- generation fails
- async progress is wrong
- a new capability needs to be inserted into the pipeline

## Source of truth

- `backend/api/generate.py`
- `backend/core/llm.py`
- `backend/core/ppt_gen.py`
- `backend/core/doc_gen.py`

## Current status

- `active`
- This is the main working path in the current product

## Current flow

1. Compile `TeachingSpec`
2. Reject requests missing required preflight fields
3. Apply reference-outline context if available
4. Retrieve teaching knowledge and RAG context
5. Generate raw `slides_json`
6. Attach page evidence
7. Normalize to `blocks[]`
8. Export PPTX and DOCX

## Known gaps

- True two-stage `outline -> per-page generation` is not fully implemented.
- Mode A is present as scaffolding, not yet as a full structure-preserving engine.

