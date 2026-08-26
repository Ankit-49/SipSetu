# SipSetu - GCloud CLI Installation Script
# Run this script as Administrator

param(
    [string]$InstallPath = "C:\Google\Cloud SDK"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SipSetu - GCloud CLI Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if gcloud is already installed
$gcloudPath = Get-Command gcloud -ErrorAction SilentlyContinue
if ($gcloudPath) {
    Write-Host "gcloud CLI is already installed at: $($gcloudPath.Source)" -ForegroundColor Green
    Write-Host ""
    Write-Host "To update, run: gcloud components update" -ForegroundColor Yellow
    exit 0
}

Write-Host "Installing Google Cloud SDK (gcloud CLI)..." -ForegroundColor Yellow
Write-Host ""

# Download the installer
$installerUrl = "https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe"
$installerPath = "$env:TEMP\GoogleCloudSDKInstaller.exe"

Write-Host "Downloading installer from: $installerUrl" -ForegroundColor Gray
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing
    Write-Host "Download complete!" -ForegroundColor Green
} catch {
    Write-Host "Failed to download installer: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Running installer..." -ForegroundColor Yellow
Write-Host "Please follow the installation wizard." -ForegroundColor Gray
Write-Host ""

# Run the installer
Start-Process -FilePath $installerPath -ArgumentList "/S /D=$InstallPath" -Wait

# Clean up
Remove-Item -Path $installerPath -Force -ErrorAction SilentlyContinue

# Add to PATH
$currentUserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentUserPath -notlike "*$InstallPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$currentUserPath;$InstallPath\bin", "User")
    $env:Path += ";$InstallPath\bin"
    Write-Host "Added gcloud to PATH" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Open a new terminal (or restart current one)" -ForegroundColor Gray
Write-Host "2. Run: gcloud init" -ForegroundColor Gray
Write-Host "3. Follow the authentication prompts" -ForegroundColor Gray
Write-Host ""
Write-Host "For SipSetu deployment:" -ForegroundColor Yellow
Write-Host "1. Set your project: gcloud config set project YOUR_PROJECT_ID" -ForegroundColor Gray
Write-Host "2. Enable required APIs:" -ForegroundColor Gray
Write-Host "   gcloud services enable container.googleapis.com" -ForegroundColor Gray
Write-Host "   gcloud services enable compute.googleapis.com" -ForegroundColor Gray
Write-Host "   gcloud services enable sqladmin.googleapis.com" -ForegroundColor Gray
Write-Host ""
