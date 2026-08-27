@echo off
echo ============================================
echo   SipSetu - Public Deployment via Cloudflare
echo ============================================
echo.

REM Check cloudflared
where cloudflared >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] cloudflared not found!
    echo Run: scripts\install_cloudflared.bat
    pause
    exit /b 1
)

REM Check Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

echo Starting services...
echo.

REM Start Redis (if running locally via Docker)
docker ps --format "{{.Names}}" 2>nul | findstr /i "redis" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [1/4] Starting Redis...
    docker run -d --name sipsetu-redis -p 6379:6379 redis:7-alpine 2>nul
) else (
    echo [1/4] Redis already running
)

REM Start PostgreSQL (if running locally via Docker)
docker ps --format "{{.Names}}" 2>nul | findstr /i "postgres" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [2/4] Starting PostgreSQL...
    docker run -d --name sipsetu-postgres -p 5432:5432 -e POSTGRES_DB=sipsetu -e POSTGRES_USER=sipsetu -e POSTGRES_PASSWORD=sipsetu_dev_password postgres:16-alpine 2>nul
) else (
    echo [2/4] PostgreSQL already running
)

REM Wait for DB to be ready
echo [3/4] Waiting for database...
timeout /t 3 /nobreak >nul

REM Start backend
echo [4/4] Starting backend server...
echo.
echo Starting Flask backend on port 5000...
start "SipSetu-Backend" cmd /c "cd backend && python -m flask run --host=0.0.0.0 --port=5000"

REM Wait for backend to start
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo.
echo ============================================
echo   Backend started on http://localhost:5000
echo ============================================
echo.

REM Start Cloudflare Tunnel
echo ============================================
echo   Starting Cloudflare Tunnel...
echo   Your public URL will appear below
echo ============================================
echo.
echo   Press Ctrl+C to stop everything
echo.

cloudflared tunnel --url http://localhost:5000
