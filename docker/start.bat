@echo off
REM FastPPT Quick Start Script for Windows

echo =========================================
echo FastPPT Docker Deployment
echo =========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not installed
    echo Please install Docker Desktop: https://docs.docker.com/desktop/install/windows-install/
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker Compose is not installed
    echo Please install Docker Compose
    pause
    exit /b 1
)

REM Navigate to docker directory
cd /d "%~dp0"

REM Check if .env exists
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo WARNING: Please edit docker\.env with your API keys:
    echo    - DEEPSEEK_API_KEY
    echo    - DASHSCOPE_API_KEY
    echo    - Change default passwords
    echo.
    pause
)

REM Start services
echo Starting FastPPT services...
docker-compose up -d

echo.
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Check service health
echo.
echo Checking service health...
echo.

curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo X FastAPI Backend: Not responding
) else (
    echo √ FastAPI Backend: Running (http://localhost:8000)
)

curl -f http://localhost:3000/health >nul 2>&1
if errorlevel 1 (
    echo X PPTXGenJS Service: Not responding
) else (
    echo √ PPTXGenJS Service: Running (http://localhost:3000)
)

docker exec fastppt-postgres pg_isready -U fastppt >nul 2>&1
if errorlevel 1 (
    echo X PostgreSQL: Not responding
) else (
    echo √ PostgreSQL: Running (localhost:5432)
)

echo.
echo =========================================
echo FastPPT is running!
echo =========================================
echo.
echo Access points:
echo   - API: http://localhost:8000
echo   - Health: http://localhost:8000/health
echo   - Metrics: http://localhost:8000/metrics
echo   - API Docs: http://localhost:8000/docs
echo.
echo Useful commands:
echo   - View logs: docker-compose logs -f
echo   - Stop services: docker-compose down
echo   - Restart: docker-compose restart
echo.
pause
