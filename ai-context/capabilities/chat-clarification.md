# Capability: chat-clarification

## What it is

The conversational path that collects teaching intent, streams assistant responses, and decides when intent is ready for generation.

## Read when

- chat appears to stall
- streaming SSE breaks
- clarification prompts need tuning

## Source of truth

- `backend/api/chat.py`
- `backend/core/llm.py`
- `frontend/src/components/ChatPanel.vue`

## Current status

- `partial`
- Stable enough for plain demo path
- Still mixed between collection logic and generation-readiness heuristics

## Inputs / outputs

- Input: user messages and optional session context
- Output:
  - streamed or non-streamed assistant text
  - `intent_ready` state
  - normalized or inferred intent fields

## Important behavior

- Contest runtime is frozen to plain chat path by default.
- Chat should keep asking for missing key fields until preflight is satisfied.
- Frontend should not rely on agent-mode behavior in the default path.

## Known gaps

- Clarification quality still depends heavily on prompt behavior.
- Agent-enabled path exists in the codebase but is intentionally not the default.

