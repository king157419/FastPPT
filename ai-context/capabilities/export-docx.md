# Capability: export-docx

## What it is

The DOCX lesson-plan export path built from teaching intent, suggested flow, retrieval snippets, and evidence.

## Read when

- lesson plan formatting needs to change
- evidence should appear differently in the document
- generation completeness is being reviewed

## Source of truth

- `backend/core/doc_gen.py`
- `backend/api/generate.py`

## Current status

- `active`
- Simple but usable

## Inputs / outputs

- Input: normalized intent, retrieved chunks, optional evidence entries
- Output: `.docx` lesson plan

## Known gaps

- Formatting is still template-light.
- Course-specific pedagogy sections can be more tailored.

