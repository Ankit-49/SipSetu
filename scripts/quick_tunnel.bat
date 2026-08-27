@echo off
echo ============================================
echo   SipSetu - Quick Tunnel (Backend Only)
echo ============================================
echo.
echo Exposes your local backend to the internet.
echo No setup required — just run this!
echo.
echo ============================================
echo.

REM Quick check
where cloudflared >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [1/2] First-time setup: downloading cloudflared...
    echo.
    set ARCH=amd64
    if "%PROCESSOR_ARCHITECTURE%"=="ARM64" set ARCH=arm64
    curl -L -o "%USERPROFILE%\cloudflared.exe" "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-%ARCH%.exe"
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Download failed. Please install cloudflared manually:
        echo   https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/create-local-tunnel/
        pause
        exit /b 1
    )
    set PATH=%PATH%;%USERPROFILE%
    echo [OK] cloudflared downloaded!
    echo.
)

echo [2/2] Starting tunnel to http://localhost:5000
echo.
echo ============================================
echo   Your public URL appears below!
echo   Share it with anyone to access your app.
echo ============================================
echo.

cloudflared tunnel --url http://localhost:5000
