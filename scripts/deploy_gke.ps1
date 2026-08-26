# SipSetu - GKE Deployment Script
# This script deploys SipSetu to Google Kubernetes Engine

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    
    [Parameter(Mandatory=$true)]
    [string]$ClusterName,
    
    [Parameter(Mandatory=$true)]
    [string]$Zone,
    
    [string]$Namespace = "sipsetu"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SipSetu - GKE Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Project: $ProjectId" -ForegroundColor Yellow
Write-Host "Cluster: $ClusterName" -ForegroundColor Yellow
Write-Host "Zone: $Zone" -ForegroundColor Yellow
Write-Host "Namespace: $Namespace" -ForegroundColor Yellow
Write-Host ""

# Check if gcloud is installed
$gcloudPath = Get-Command gcloud -ErrorAction SilentlyContinue
if (-not $gcloudPath) {
    Write-Host "ERROR: gcloud CLI is not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install gcloud CLI first:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Gray
    Write-Host "2. Run: gcloud init" -ForegroundColor Gray
    Write-Host "3. Re-run this script" -ForegroundColor Gray
    exit 1
}

# Set project
Write-Host "Setting GCP project..." -ForegroundColor Yellow
gcloud config set project $ProjectId

# Enable required APIs
Write-Host "Enabling required APIs..." -ForegroundColor Yellow
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Check if cluster exists
Write-Host "Checking if GKE cluster exists..." -ForegroundColor Yellow
$clusterExists = gcloud container clusters describe $ClusterName --zone $Zone --project $ProjectId 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating new GKE cluster..." -ForegroundColor Yellow
    gcloud container clusters create $ClusterName `
        --zone $Zone `
        --num-nodes 3 `
        --machine-type e2-standard-4 `
        --enable-autoscaling `
        --min-nodes 1 `
        --max-nodes 5 `
        --enable-autorepair `
        --enable-autoupgrade `
        --release-channel regular
} else {
    Write-Host "Cluster already exists" -ForegroundColor Green
}

# Get cluster credentials
Write-Host "Getting cluster credentials..." -ForegroundColor Yellow
gcloud container clusters get-credentials $ClusterName --zone $Zone --project $ProjectId

# Create namespace
Write-Host "Creating namespace..." -ForegroundColor Yellow
kubectl create namespace $Namespace --dry-run=client -o yaml | kubectl apply -f -

# Create secrets
Write-Host "Creating Kubernetes secrets..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Please provide the following values:" -ForegroundColor Yellow

$postgresPassword = Read-Host "PostgreSQL Password" -AsSecureString
$redisPassword = Read-Host "Redis Password" -AsSecureString
$jwtSecret = Read-Host "JWT Secret Key" -AsSecureString

# Create secret
kubectl create secret generic sipsetu-secrets `
    --namespace $Namespace `
    --from-literal=POSTGRES_PASSWORD=$postgresPassword `
    --from-literal=REDIS_PASSWORD=$redisPassword `
    --from-literal=JWT_SECRET_KEY=$jwtSecret `
    --dry-run=client -o yaml | kubectl apply -f -

# Apply Kubernetes manifests
Write-Host "Deploying to GKE..." -ForegroundColor Yellow
kubectl apply -f k8s/ --namespace $Namespace

# Wait for deployment
Write-Host "Waiting for deployment to be ready..." -ForegroundColor Yellow
kubectl rollout status deployment/sipsetu-backend --namespace $Namespace --timeout=300s
kubectl rollout status deployment/sipsetu-frontend --namespace $Namespace --timeout=300s

# Get external IP
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$externalIp = kubectl get service sipsetu-frontend --namespace $Namespace -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
Write-Host "Frontend URL: http://$externalIp" -ForegroundColor Green
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  kubectl get pods --namespace $Namespace" -ForegroundColor Gray
Write-Host "  kubectl logs -f deployment/sipsetu-backend --namespace $Namespace" -ForegroundColor Gray
Write-Host "  kubectl delete -f k8s/ --namespace $Namespace" -ForegroundColor Gray
