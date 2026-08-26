# SipSetu - GKE Deployment Guide

This guide covers deploying SipSetu to Google Kubernetes Engine (GKE).

## Prerequisites

1. **Google Cloud Account** - https://cloud.google.com/
2. **gcloud CLI** - https://cloud.google.com/sdk/docs/install
3. **kubectl** - https://kubernetes.io/docs/tasks/tools/
4. **Docker** - https://docs.docker.com/get-docker/

## Quick Start

### 1. Install gcloud CLI (if not installed)

```powershell
# Windows
.\scripts\install_gcloud.ps1

# Or download from: https://cloud.google.com/sdk/docs/install
```

### 2. Initialize gcloud

```bash
gcloud init
```

Follow the prompts to:
- Log in to your Google account
- Select or create a project
- Set default region/zone

### 3. Enable Required APIs

```bash
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 4. Create GKE Cluster

```bash
# Create a cluster with autoscaling
gcloud container clusters create sipsetu-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type e2-standard-4 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 5 \
  --enable-autorepair \
  --enable-autoupgrade \
  --release-channel regular
```

### 5. Get Cluster Credentials

```bash
gcloud container clusters get-credentials sipsetu-cluster \
  --zone us-central1-a \
  --project YOUR_PROJECT_ID
```

### 6. Build and Push Docker Images

```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Set project ID
export PROJECT_ID=$(gcloud config get-value project)

# Build backend image
docker build -t gcr.io/$PROJECT_ID/sipsetu-backend:latest -f backend/Dockerfile.prod backend

# Build frontend image
docker build -t gcr.io/$PROJECT_ID/sipsetu-frontend:latest frontend

# Push images
docker push gcr.io/$PROJECT_ID/sipsetu-backend:latest
docker push gcr.io/$PROJECT_ID/sipsetu-frontend:latest
```

### 7. Update Kubernetes Manifests

Edit the following files to replace `PROJECT_ID` with your GCP project ID:

- `k8s/backend-deployment.yaml`
- `k8s/frontend-deployment.yaml`
- `k8s/celery-deployment.yaml`

### 8. Create Namespace and Secrets

```bash
# Create namespace
kubectl create namespace sipsetu

# Create secrets (replace with your values)
kubectl create secret generic sipsetu-secrets \
  --namespace sipsetu \
  --from-literal=DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@sipsetu-postgres:5432/sipsetu \
  --from-literal=REDIS_URL=redis://:YOUR_PASSWORD@sipsetu-redis:6379/0 \
  --from-literal=POSTGRES_PASSWORD=YOUR_POSTGRES_PASSWORD \
  --from-literal=REDIS_PASSWORD=YOUR_REDIS_PASSWORD \
  --from-literal=JWT_SECRET_KEY=YOUR_JWT_SECRET
```

### 9. Deploy to GKE

```bash
# Apply all manifests
kubectl apply -f k8s/ --namespace sipsetu

# Or apply individually
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/celery-deployment.yaml
kubectl apply -f k8s/ingress.yaml
```

### 10. Verify Deployment

```bash
# Check pods
kubectl get pods --namespace sipsetu

# Check services
kubectl get services --namespace sipsetu

# Check ingress
kubectl get ingress --namespace sipsetu

# View logs
kubectl logs -f deployment/sipsetu-backend --namespace sipsetu
```

## Using the Deployment Script

```powershell
# Run the deployment script
.\scripts\deploy_gke.ps1 \
  -ProjectId "your-project-id" \
  -ClusterName "sipsetu-cluster" \
  -Zone "us-central1-a" \
  -Namespace "sipsetu"
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `JWT_SECRET_KEY` | JWT signing key | Yes |
| `POSTGRES_PASSWORD` | PostgreSQL password | Yes |
| `REDIS_PASSWORD` | Redis password | Yes |
| `FLASK_ENV` | Flask environment | Yes |
| `LOG_LEVEL` | Logging level | No |

### Resource Limits

| Service | CPU Request | CPU Limit | Memory Request | Memory Limit |
|---------|-------------|-----------|----------------|--------------|
| Backend | 250m | 1000m | 512Mi | 1Gi |
| Frontend | 100m | 500m | 128Mi | 256Mi |
| PostgreSQL | 250m | 1000m | 512Mi | 1Gi |
| Redis | 100m | 500m | 256Mi | 512Mi |
| Celery Worker | 250m | 1000m | 256Mi | 512Mi |

## Useful Commands

```bash
# View pods
kubectl get pods --namespace sipsetu

# View services
kubectl get services --namespace sipsetu

# View logs
kubectl logs -f deployment/sipsetu-backend --namespace sipsetu

# Scale backend
kubectl scale deployment sipsetu-backend --replicas=5 --namespace sipsetu

# Restart deployment
kubectl rollout restart deployment/sipsetu-backend --namespace sipsetu

# Check rollout status
kubectl rollout status deployment/sipsetu-backend --namespace sipsetu

# Delete deployment
kubectl delete -f k8s/ --namespace sipsetu

# Get external IP
kubectl get service sipsetu-frontend --namespace sipsetu -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

## Monitoring

### Prometheus

```bash
# Port-forward Prometheus
kubectl port-forward svc/prometheus 9090:9090 --namespace sipsetu

# Access at http://localhost:9090
```

### Grafana

```bash
# Port-forward Grafana
kubectl port-forward svc/grafana 3000:3000 --namespace sipsetu

# Access at http://localhost:3000
```

## Troubleshooting

### Pod Stuck in Pending

```bash
kubectl describe pod POD_NAME --namespace sipsetu
kubectl get events --namespace sipsetu --sort-by='.lastTimestamp'
```

### Pod Crash Looping

```bash
kubectl logs POD_NAME --namespace sipsetu --previous
```

### Service Not Accessible

```bash
kubectl get endpoints --namespace sipsetu
kubectl describe ingress sipsetu-ingress --namespace sipsetu
```

### Database Connection Issues

```bash
# Check PostgreSQL pod
kubectl exec -it deployment/sipsetu-postgres --namespace sipsetu -- psql -U postgres -d sipsetu

# Check secrets
kubectl get secret sipsetu-secrets --namespace sipsetu -o yaml
```

## Cleanup

```bash
# Delete all resources
kubectl delete -f k8s/ --namespace sipsetu

# Delete namespace
kubectl delete namespace sipsetu

# Delete GKE cluster
gcloud container clusters delete sipsetu-cluster --zone us-central1-a
```

## Cost Optimization

1. **Use Spot VMs** for non-critical workloads
2. **Enable autoscaling** to scale down during low traffic
3. **Right-size resources** based on actual usage
4. **Use preemptible nodes** for batch jobs

## Security Best Practices

1. **Use Workload Identity** instead of service account keys
2. **Enable Network Policy** to restrict pod-to-pod communication
3. **Use Secret Manager** for sensitive configuration
4. **Enable Pod Security Standards**
5. **Regularly update images** for security patches

## Next Steps

1. Set up CI/CD pipeline with Cloud Build
2. Configure monitoring with Cloud Monitoring
3. Set up log aggregation with Cloud Logging
4. Configure backups for PostgreSQL
5. Set up SSL/TLS certificates with cert-manager
