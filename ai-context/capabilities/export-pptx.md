# Capability: export-pptx

## What it is

The PPTX export path that transforms generated courseware into a downloadable deck.

## Read when

- exported deck layout is wrong
- docker or service wiring breaks
- a new visual block needs export support

## Source of truth

- `backend/core/ppt_gen.py`
- `services/pptxgenjs/`

## Current status

- `active`
- Main demo path is working

## Inputs / outputs

- Input: normalized intent and `slides_json`
- Output: `.pptx` file in `outputs/`

## Known gaps

- Export logic is still not fully block-registry based.
- Some advanced layouts may still rely on page-level assumptions.

