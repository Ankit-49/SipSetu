@echo off
echo ============================================
echo   SipSetu - Full Stack via Cloudflare Tunnel
echo ============================================
echo.
echo This script starts both frontend and backend
echo and exposes them via Cloudflare Tunnel.
echo.

REM Check cloudflared
where cloudflared >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] cloudflared not found!
    echo Run: scripts\install_cloudflared.bat first
    pause
    exit /b 1
)

REM Check node
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js not found! Install from https://nodejs.org
    pause
    exit /b 1
)

echo ============================================
echo   Step 1: Starting Backend
echo ============================================

REM Check if backend venv exists
if not exist "backend\.venv" (
    echo Creating Python virtual environment...
    cd backend
    python -m venv .venv
    call .venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call backend\.venv\Scripts\activate
)

REM Start backend in new window
echo Starting Flask backend...
start "SipSetu-Backend" cmd /c "cd backend && .venv\Scripts\python -m flask run --host=0.0.0.0 --port=5000"
echo [OK] Backend starting on port 5000

echo.
echo ============================================
echo   Step 2: Starting Frontend
echo ============================================

REM Start frontend dev server in new window
echo Starting Vite dev server...
start "SipSetu-Frontend" cmd /c "cd frontend && npm run dev"
echo [OK] Frontend starting on port 5173

echo.
echo ============================================
echo   Step 3: Starting Cloudflare Tunnels
echo ============================================
echo.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:5173
echo.
echo Two public URLs will appear below.
echo Copy the "https://xxx.trycloudflare.com" URLs
echo and update your frontend VITE_API_URL if needed.
echo.
echo Press Ctrl+C to stop.
echo.

REM Start tunnel for backend
echo --- BACKEND TUNNEL ---
start "Tunnel-Backend" cmd /c "cloudflared tunnel --url http://localhost:5000 > %TEMP%\tunnel_backend.log 2>&1"

REM Start tunnel for frontend
echo --- FRONTEND TUNNEL ---
start "Tunnel-Frontend" cmd /c "cloudflared tunnel --url http://localhost:5173 > %TEMP%\tunnel_frontend.log 2>&1"

REM Wait and show URLs
timeout /t 8 /nobreak >nul

echo.
echo ============================================
echo   PUBLIC URLs (check console windows too)
echo ============================================
echo.
echo Backend tunnel log:
type %TEMP%\tunnel_backend.log 2>nul | findstr /i "trycloudflare"
echo.
echo Frontend tunnel log:
type %TEMP%\tunnel_frontend.log 2>nul | findstr /i "trycloudflare"
echo.
echo ============================================
echo   IMPORTANT: Copy your backend URL and set it
echo   as VITE_API_URL in your frontend build
echo ============================================
echo.
echo   To stop: Close the console windows, or run:
echo   taskkill /FI "WINDOWTITLE eq SipSetu-Backend"
echo   taskkill /FI "WINDOWTITLE eq SipSetu-Frontend"
echo   taskkill /FI "WINDOWTITLE eq Tunnel-Backend"
echo   taskkill /FI "WINDOWTITLE eq Tunnel-Frontend"
echo.
pause
