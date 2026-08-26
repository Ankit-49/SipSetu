# Google Cloud SDK (gcloud CLI) Installation Guide

This guide helps you install the gcloud CLI for deploying SipSetu to GKE.

## Method 1: Run the Installation Script (Recommended)

1. Open Command Prompt or PowerShell as Administrator
2. Navigate to the SipSetu directory:
   ```cmd
   cd "F:\Project\Reseme Analyzer\SipSetu"
   ```
3. Run the installation script:
   ```cmd
   scripts\install_gcloud.bat
   ```
4. Follow the installation wizard

## Method 2: Manual Installation

### Step 1: Download the Installer

1. Go to: https://cloud.google.com/sdk/docs/install
2. Click "Windows" to download the installer
3. Run the downloaded `GoogleCloudSDKInstaller.exe`

### Step 2: Follow the Installation Wizard

1. Choose installation options:
   - ✅ Install Cloud SDK
   - ✅ Create desktop shortcut
   - ✅ Add to PATH
2. Select Python version (use default)
3. Complete installation

### Step 3: Initialize gcloud

1. Open a new Command Prompt or PowerShell
2. Run:
   ```cmd
   gcloud init
   ```
3. Follow the prompts:
   - Log in to your Google account
   - Select or create a project
   - Set default region/zone

## Method 3: Using Chocolatey (if installed)

```cmd
choco install gcloudsdk
```

## Method 4: Using Winget (Windows 11)

```cmd
winget install Google.SDK
```

## After Installation

### Verify Installation

```cmd
gcloud --version
```

### Configure for SipSetu

```cmd
REM Set your project
gcloud config set project YOUR_PROJECT_ID

REM Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com

REM Configure Docker for GCR
gcloud auth configure-docker
```

### Deploy SipSetu

```cmd
REM Get cluster credentials
gcloud container clusters get-credentials sipsetu-cluster --zone us-central1-a

REM Build and push images
export PROJECT_ID=$(gcloud config get-value project)
docker build -t gcr.io/$PROJECT_ID/sipsetu-backend:latest -f backend/Dockerfile.prod backend
docker build -t gcr.io/$PROJECT_ID/sipsetu-frontend:latest frontend
docker push gcr.io/$PROJECT_ID/sipsetu-backend:latest
docker push gcr.io/$PROJECT_ID/sipsetu-frontend:latest

REM Deploy to GKE
kubectl apply -f k8s/ --namespace sipsetu
```

## Troubleshooting

### "gcloud is not recognized"

- Close and reopen Command Prompt/PowerShell
- Or run: `refreshenv`

### "Permission denied"

- Run Command Prompt as Administrator
- Or check PATH environment variable

### "Python not found"

- Install Python 3.7+ from https://python.org
- Or select Python during gcloud installation

### "API not enabled"

- Run: `gcloud services enable SERVICE_NAME`
- Or enable via Cloud Console: https://console.cloud.google.com/apis/library

## Next Steps

After installing gcloud, run the deployment script:

```cmd
.\scripts\deploy_gke.ps1 -ProjectId "your-project-id" -ClusterName "sipsetu-cluster" -Zone "us-central1-a"
```

Or follow the step-by-step guide in `DEPLOYMENT_GKE.md`.
