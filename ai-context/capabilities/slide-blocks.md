# Capability: slide-blocks

## What it is

The block schema that standardizes page content into typed, more reusable units such as text, bullets, code, formula, table, image, and flowchart blocks.

## Read when

- adding a new block type
- migrating renderer/exporter away from `page.type`
- debugging structured preview or export mismatches

## Source of truth

- `backend/core/slide_blocks.py`
- `backend/api/generate.py`
- `docs/engineering/feature-decomposition-and-implementation.md`

## Current status

- `partial`
- Backend normalization exists
- Frontend and exporter still keep a compatibility layer around page-level types

## Inputs / outputs

- Input: raw page structures from generation
- Output: page structures augmented with `blocks[]` and a block summary

## Known gaps

- Preview is not fully block-first yet.
- PPTX export is not yet a clean registry-based block exporter.
- Validation per block type is still basic.

