#!/bin/bash
# FastPPT Backend Startup Script

cd "$(dirname "$0")"

# Set environment variables explicitly
export PYTHONPATH=.
export DEEPSEEK_API_KEY=sk-f6a3e145bcdf477a8b07d964fadf9220
export ANTHROPIC_API_KEY=B003MH0H-6TY8-2N5X-90Z2-EWXQ2JKKFNBC
export ANTHROPIC_BASE_URL=https://yunyi.cfd/claude
export DASHSCOPE_API_KEY=
export CONTEST_FORCE_PLAIN=true
export ENABLE_AGENT=false
export REDIS_URL=
export PPTXGENJS_SERVICE_URL=http://localhost:3000
export HOST=0.0.0.0
export PORT=8000

echo "Starting FastPPT backend..."
echo "Using DeepSeek API"

# Start uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
