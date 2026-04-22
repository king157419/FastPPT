# Repository Map

## Root

- `README.md`: user-facing project overview and startup instructions
- `AGENTS.md`: repository-level reading and sync rules
- `ai-context/`: fast-entry context layer for humans and coding agents
- `docs/`: stable product and engineering docs
- `docker/`: compose-based local deployment assets

## Backend

- `backend/main.py`: FastAPI bootstrap, router mounting, health reporting
- `backend/api/`: HTTP routes for upload, chat, generate, revise, download, retrieval, knowledge
- `backend/core/`: business logic, normalization, retrieval, export, parsing
- `backend/integrations/`: optional external integrations such as agent or RAGFlow clients
- `backend/tests` or `backend/test_*.py`: behavior verification

## Frontend

- `frontend/src/App.vue`: page shell and major panel layout
- `frontend/src/components/`: upload, chat, generate, preview, slide rendering
- `frontend/src/api/`: HTTP client layer to backend routes

## Services

- `services/pptxgenjs/`: local PPTX rendering service used by export path

## Docs split

- `docs/product/`: problem framing, positioning, teacher research
- `docs/engineering/`: feature decomposition and implementation direction
- `docs/archive/strategy-history/`: original step-based strategy documents kept for history

