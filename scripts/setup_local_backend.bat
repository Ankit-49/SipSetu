@echo off
REM ========================================
REM SipSetu - Local Backend Setup Script
REM ========================================

echo.
echo ========================================
echo   SipSetu - Local Backend Setup
echo ========================================
echo.

REM Check if Docker is installed
where docker >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ Docker found
    set USE_DOCKER=true
) else (
    echo ⚠ Docker not found
    echo Will use local Python installation
    set USE_DOCKER=false
)

REM Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ Python found
) else (
    if "%USE_DOCKER%"=="false" (
        echo ✗ Python not found! Please install Python 3.11+
        goto :end
    )
)

echo.

REM Option 1: Docker deployment
if "%USE_DOCKER%"=="true" (
    echo Docker detected. Starting services with Docker Compose...
    echo.
    
    REM Copy environment file if not exists
    if not exist ".env.production" (
        echo Creating .env.production...
        copy .env.production.example .env.production
        
        echo ✓ .env.production created
        echo ⚠ Please edit .env.production with your settings
    )
    
    echo Starting Docker services...
    docker compose -f docker-compose.prod.yml up -d postgres redis backend celery-worker celery-beat
    
    echo.
    echo Waiting for services to start...
    timeout /t 15 /nobreak
    
    echo.
    echo Checking service status...
    docker compose -f docker-compose.prod.yml ps
    
    echo.
    echo ✓ Backend started on http://localhost:5000
    
) else (
    echo Starting local Python deployment...
    echo.
    
    cd backend
    
    REM Create virtual environment if not exists
    if not exist "venv" (
        echo Creating virtual environment...
        python -m venv venv
    )
    
    REM Activate virtual environment
    call venv\Scripts\activate.bat
    
    echo ✓ Virtual environment activated
    
    REM Install dependencies
    echo Installing dependencies...
    pip install -r requirements.txt
    
    echo ✓ Dependencies installed
    
    echo.
    echo ⚠ Make sure PostgreSQL and Redis are running:
    echo   - PostgreSQL: localhost:5432
    echo   - Redis: localhost:6379
    echo.
    
    REM Run migrations
    echo Running database migrations...
    python -m alembic upgrade head
    
    echo ✓ Migrations completed
    
    REM Start backend
    echo.
    echo Starting backend server...
    start python app.py
    
    echo.
    echo ✓ Backend started on http://localhost:5000
)

echo.
echo ========================================
echo   Backend Setup Complete!
echo ========================================
echo.
echo Backend URL: http://localhost:5000
echo Health Check: http://localhost:5000/api/health
echo.
echo Next steps:
echo 1. Deploy frontend to Cloudflare Pages
echo 2. Set VITE_API_URL to http://localhost:5000/api
echo 3. Or use ngrok to expose backend: ngrok http 5000
echo.

:end
pause
