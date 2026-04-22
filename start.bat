@echo off
echo === TeachMind FastPPT ===

echo [1/3] Installing Python dependencies...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: pip install failed
    pause
    exit /b 1
)

echo [2/3] Starting backend (uvicorn)...
start "FastPPT Backend" cmd /k "set CONTEST_FORCE_PLAIN=true && set ENABLE_AGENT=false && set REDIS_URL= && set RAGFLOW_BASE_URL= && set RAGFLOW_API_KEY= && set RAGFLOW_KB_ID= && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo [3/3] Starting frontend (vite)...
cd ../frontend
call npm install
start "FastPPT Frontend" cmd /k "npm run dev"

echo.
echo === Started! ===
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
pause
