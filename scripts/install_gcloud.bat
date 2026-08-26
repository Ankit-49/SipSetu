@echo off
REM ========================================
REM SipSetu - GCloud CLI Installation Script
REM ========================================

echo.
echo ========================================
echo   SipSetu - GCloud CLI Installation
echo ========================================
echo.

REM Check if gcloud is already installed
where gcloud >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo gcloud CLI is already installed!
    gcloud --version
    echo.
    echo To update, run: gcloud components update
    goto :end
)

echo Downloading Google Cloud SDK installer...
echo.

REM Download the installer
set INSTALLER_URL=https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe
set INSTALLER_PATH=%TEMP%\GoogleCloudSDKInstaller.exe

echo URL: %INSTALLER_URL%
echo Path: %INSTALLER_PATH%
echo.

REM Use PowerShell to download
powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%INSTALLER_URL%' -OutFile '%INSTALLER_PATH%' -UseBasicParsing }"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to download installer!
    echo.
    echo Please download manually from:
    echo https://cloud.google.com/sdk/docs/install
    goto :end
)

echo.
echo Download complete! Running installer...
echo.
echo Please follow the installation wizard.
echo.

REM Run the installer
start /wait "" "%INSTALLER_PATH%"

REM Clean up
del "%INSTALLER_PATH%" 2>nul

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Open a new Command Prompt or PowerShell
echo 2. Run: gcloud init
echo 3. Follow the authentication prompts
echo.
echo For SipSetu deployment:
echo 1. Set your project: gcloud config set project YOUR_PROJECT_ID
echo 2. Enable required APIs:
echo    gcloud services enable container.googleapis.com
echo    gcloud services enable compute.googleapis.com
echo    gcloud services enable sqladmin.googleapis.com
echo.

:end
pause
