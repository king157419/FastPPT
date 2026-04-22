# Flow: revise-courseware

1. Load existing `slides_json` into preview.
2. Collect revise instruction from the user.
3. Optionally target specific pages.
4. Run revise logic against the existing slide structure.
5. Re-render preview.
6. Re-export if needed.

## Main entry points

- `backend/api/generate.py`
- `backend/core/llm.py`
- `frontend/src/components/PreviewPanel.vue`

