@echo off
echo ============================================
echo   Cloudflare Tunnel Setup for SipSetu
echo ============================================
echo.

REM Check if already installed
where cloudflared >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] cloudflared is already installed!
    cloudflared --version
    goto :done
)

REM Try winget first
echo Trying winget install...
winget install Cloudflare.cloudflared 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Installed via winget!
    goto :done
)

REM Try chocolatey
echo Trying choco install...
choco install cloudflared -y 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Installed via chocolatey!
    goto :done
)

REM Manual download
echo Downloading cloudflared manually...
set ARCH=amd64
if "%PROCESSOR_ARCHITECTURE%"=="ARM64" set ARCH=arm64
set URL=https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-%ARCH%.exe
echo Downloading from: %URL%
curl -L -o "%USERPROFILE%\cloudflared.exe" "%URL%"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Download failed. Please download manually from:
    echo   https://github.com/cloudflare/cloudflared/releases/latest
    echo   Download cloudflared-windows-amd64.exe
    echo   Save as: %USERPROFILE%\cloudflared.exe
    echo   Then add %USERPROFILE% to your PATH
    pause
    exit /b 1
)

REM Add to PATH for this session
set PATH=%PATH%;%USERPROFILE%
echo [OK] Downloaded to %USERPROFILE%\cloudflared.exe
echo NOTE: Add %USERPROFILE% to your system PATH for permanent access.

:done
echo.
echo ============================================
echo   Next step: Run scripts\start_tunnel.bat
echo ============================================
pause
