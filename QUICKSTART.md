# FastPPT Quickstart (Contest)

## 1) Prepare demo env

```bash
cp backend/.env.demo backend/.env
cp docker/.env.demo docker/.env
```

Keep these defaults for stable demo:
- `CONTEST_FORCE_PLAIN=true`
- `ENABLE_AGENT=false`
- `REDIS_URL=`
- `RAGFLOW_*` empty

## 2) Start services

### Docker

```bash
docker compose -f docker/docker-compose.yml up --build
```

If you explicitly need Redis/agent runtime, add profile:

```bash
docker compose -f docker/docker-compose.yml --profile agent up --build
```

### Local

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

## 3) Verify runtime mode

```bash
curl http://localhost:8000/health
```

Expected:
- `chat_mode=plain`
- `agent_enabled=false`
- `contest_force_plain=true`
- `redis=skipped`

## 4) Full demo chain

1. Upload one file in UI (or `/api/upload`)
2. Chat to collect teaching intent
3. Click generate
4. Preview pages
5. Download backend PPTX/DOCX
6. Modify one page in PreviewPanel and regenerate PPTX

## 5) Local quality check

```bash
python -m pytest -q backend
cd frontend && npm run build
```

## 6) Stable branch

The repo includes branch:

`release/contest-demo`

Use it as the baseline branch for judging/demo freeze.
