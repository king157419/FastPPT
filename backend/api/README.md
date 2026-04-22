# Backend API Map

## Purpose

`backend/api/` holds HTTP route definitions and request/response shaping. Business rules should stay in `backend/core/` unless they are inherently transport-specific.

## Main route files

- `upload.py`: upload, parse, and register files into the knowledge layer
- `chat.py`: chat and streaming clarification path
- `generate.py`: generation, async progress, and revise endpoints
- `download.py`: file download endpoints
- `knowledge.py`: knowledge-base management endpoints
- `retrieval.py`: retrieval inspection or helper endpoints
- `agent.py`: optional agent-oriented routes, not the default contest path

## Read this before editing

- `../../ai-context/CAPABILITY_INDEX.yaml`
- `../../ai-context/capabilities/chat-clarification.md`
- `../../ai-context/capabilities/generate-pipeline.md`

## Rules of thumb

- Validate request shape here, but keep generation and retrieval rules in `core/`.
- If route behavior changes, sync the matching capability card.
- Do not make `agent.py` assumptions part of the default user path unless runtime mode explicitly allows it.

