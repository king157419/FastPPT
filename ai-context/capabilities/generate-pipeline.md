# Capability: generate-pipeline

## What it is

The main generation flow now runs through:

`TeachingSpec -> SlidePlan -> SlideDraft -> slides_json -> evidence -> blocks -> export`

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
- Slide plan and slide draft stages are implemented in the main API path

## Current flow

1. Compile `TeachingSpec`
2. Reject requests missing required preflight fields
3. Apply reference-outline context if available
4. Build `SlidePlan`
5. Retrieve teaching knowledge and RAG context
6. Generate `SlideDraft` objects and raw `slides_json`
7. Attach page evidence
8. Normalize to `blocks[]`
9. Export PPTX and DOCX

## Known gaps

- The LLM still returns pages in one response; per-slide generation workers are not fully split yet.
- Mode A is partially wired and still needs stronger structure-preserving behavior.
