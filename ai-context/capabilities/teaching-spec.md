# Capability: teaching-spec

## What it is

`TeachingSpec` is the normalized intent schema that turns raw user input into stable generation fields.

## Read when

- changing required fields
- debugging generation refusal or missing-field errors
- adjusting how chat/form data is normalized

## Source of truth

- Code:
  - `backend/core/teaching_spec.py`
  - `backend/api/generate.py`
- Supporting docs:
  - `docs/engineering/feature-decomposition-and-implementation.md`

## Current status

- `active`
- Production-critical entry point

## Inputs / outputs

- Input: raw intent from chat or form fields
- Output: normalized `TeachingSpec` and backward-compatible intent dict

## Important behavior

- Required preflight fields are:
  - `teaching_goal`
  - `audience`
  - `difficulty_focus`
- Missing required fields are surfaced before generation.
- Defaults still exist for non-critical fields such as duration or style.

## Upstream / downstream

- Upstream: chat clarification, generation form
- Downstream: retrieval query shaping, `generate_slides_json`, export metadata

## Known gaps

- Schema is stable, but intent collection in chat can still produce uneven quality.
- Mode-specific fields for stronger Mode A behavior are not fully formalized yet.

