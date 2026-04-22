# FastPPT (Contest Demo Ready)

FastPPT is an AI lesson-prep system for teachers:

`upload materials -> chat for teaching intent -> generate slides_json + PPTX + DOCX -> preview/download -> revise PPT`

This repository is prepared for **contest demo stability first**.

## Demo Defaults (Important)

Use demo profile before running:

```bash
cp backend/.env.demo backend/.env
cp docker/.env.demo docker/.env
```

Demo profile guarantees:
- `CONTEST_FORCE_PLAIN=true` (hard-disable agent path for contest demo)
- `ENABLE_AGENT=false` (agent path disabled by default)
- `REDIS_URL=` (Redis optional, not required for demo)
- `RAGFLOW_*` empty by default

Check runtime mode:

```bash
curl http://localhost:8000/health
```

Expected key fields in demo mode:
- `chat_mode: plain`
- `agent_enabled: false`
- `contest_force_plain: true`
- `redis: skipped`
- `demo_mode: true`

## Core Features

- Multi-file upload: PDF/DOCX/PPTX/TXT + image + video
- Intent chat: collect topic/goal/audience/difficulty/key points/duration/style
- Generation:
  - `slides_json` for frontend preview/edit
  - real `PPTX` export
  - `DOCX` lesson plan export
- Mode A minimal support:
  - if old PPT is uploaded, preserve reference outline order during generation
- Per-page evidence:
  - each generated page contains `evidence[]` from uploaded knowledge chunks
- Revision:
  - `/api/generate/revise` supports page-level updates and re-exports PPTX

## Run

### Option A: Docker (recommended for judging)

```bash
docker compose -f docker/docker-compose.yml up --build
```

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

Redis is optional in contest mode. If you explicitly need agent runtime, start with:

```bash
docker compose -f docker/docker-compose.yml --profile agent up --build
```

### Option B: Local development

Backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## API Chain (Demo)

1. Upload material:

```bash
curl -X POST http://localhost:8000/api/upload -F "file=@example.pdf"
```

2. Chat for intent:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"我要一节光合作用课程"}],"stream":false,"use_agent":false}'
```

3. Generate:

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"intent":{"topic":"光合作用","teaching_goal":"理解并应用","audience":"高中生","difficulty_focus":"重点难点","key_points":["过程","影响因素"],"duration":"45分钟","style":"结构化讲解"},"file_ids":[]}'
```

4. Revise:

```bash
curl -X POST http://localhost:8000/api/generate/revise \
  -H "Content-Type: application/json" \
  -d '{"intent":{"topic":"光合作用"},"slides_json":{"theme":{},"pages":[{"type":"content","title":"示例","bullets":["a"]}]},"instruction":"第1页增加互动题","page_indexes":[1]}'
```

## Verification Commands

Backend critical tests:

```bash
python -m pytest -q backend
```

Frontend build:

```bash
cd frontend
npm run build
```

## Project Layout

```
backend/
  api/        # upload/chat/generate/download
  core/       # llm/rag/parser/ppt/doc/evidence
frontend/
  src/
    components/
docker/
docs/
```

## Notes

- Advanced agent path is kept as optional mode and is **not** the default contest path.
- If you intentionally enable agent mode, configure Redis and related dependencies first.
