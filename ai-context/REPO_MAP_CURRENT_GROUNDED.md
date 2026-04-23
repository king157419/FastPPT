# REPO MAP (CURRENT, GROUNDED)

This map only references paths that currently exist in repository `master`.

## Top-level responsibilities

- `backend/`: API and core generation logic
- `frontend/`: Vue app and interaction surfaces
- `services/`: auxiliary render services (including `pptxgenjs`)
- `docs/`: product, engineering, archive docs
- `ai-context/`: model/human routing layer
- `docker/`: local deployment assets

## Backend entry and flow

- Entry:
  - `backend/main.py`
- API layer:
  - `backend/api/upload.py`
  - `backend/api/chat.py`
  - `backend/api/generate.py`
  - `backend/api/download.py`
  - `backend/api/knowledge.py`
- Service layer:
  - `backend/services/upload_service.py`
  - `backend/services/chat_service.py`
  - `backend/services/generate_service.py`
- Core layer:
  - `backend/core/teaching_spec.py`
  - `backend/core/slide_pipeline.py`
  - `backend/core/llm.py`
  - `backend/core/rag.py`
  - `backend/core/source_index.py`
  - `backend/core/slide_blocks.py`
  - `backend/core/ppt_gen.py`
  - `backend/core/doc_gen.py`
  - `backend/core/parser.py`
- Shared models:
  - `backend/models.py`

## Frontend entry and flow

- Entry:
  - `frontend/src/App.vue`
- Component flow:
  - `frontend/src/components/FileUpload.vue`
  - `frontend/src/components/ChatPanel.vue`
  - `frontend/src/components/GenerateBtn.vue`
  - `frontend/src/components/PreviewPanel.vue`
  - `frontend/src/components/SlideRenderer.vue`
- API calls:
  - `frontend/src/api/index.js`

## Service and export

- `services/pptxgenjs/`: Node-side PPT rendering service
- `backend/core/ppt_gen.py`: current backend export gateway

## Tests (key grounded subset)

- `backend/test_generate_pipeline.py`
- `backend/test_slide_pipeline.py`
- `backend/test_mode_a_evidence.py`
- `backend/test_demo_chain_smoke.py`
- `backend/test_full_chain_e2e.py`

## Current truth boundary

- `current` must point to existing files only.
- target architecture ideas must stay in target indexes/docs until code lands.
