# SipSetu - Oracle Cloud Free Tier Deployment Guide

Deploy SipSetu to Oracle Cloud Free Tier - **Always Free** with 4 ARM OCPUs and 24GB RAM!

## Prerequisites

1. **Oracle Cloud Account** - https://cloud.oracle.com/free
2. **SSH client** - Terminal, PuTTY, or Windows Terminal

## Step 1: Create Oracle Cloud Account

1. Go to: https://cloud.oracle.com/free
2. Click "Start for Free"
3. Sign up with your email
4. Verify your email and complete registration
5. Add a payment method (won't be charged for free tier)

## Step 2: Create ARM Instance

1. Log in to Oracle Cloud Console
2. Click "Create a VM Instance"
3. Configure:
   - **Name**: sipsetu
   - **Image**: Oracle Linux 8 (or Ubuntu 22.04)
   - **Shape**: VM.Standard.A1.Flex (ARM)
   - **OCPUs**: 4
   - **RAM**: 24 GB
   - **Storage**: 200 GB (boot volume)
4. Add SSH public key (generate one if needed)
5. Click "Create"

## Step 3: Connect to Instance

```bash
# Get public IP from Oracle Cloud Console
ssh -i ~/.ssh/id_rsa ubuntu@YOUR_PUBLIC_IP

# Or for Oracle Linux
ssh -i ~/.ssh/id_rsa opc@YOUR_PUBLIC_IP
```

## Step 4: Install Docker

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker

# Verify Docker
docker --version
docker compose version
```

## Step 5: Clone SipSetu

```bash
# Install git
sudo apt install git -y

# Clone repository
git clone https://github.com/Ankit-49/SipSetu.git
cd SipSetu
```

## Step 6: Configure Environment

```bash
# Copy environment template
cp .env.production.example .env.production

# Edit environment file
nano .env.production
```

Update these values:
```bash
# Generate strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Set your domain or IP
FRONTEND_URL=http://YOUR_PUBLIC_IP

# Admin email
ADMIN_EMAILS=your-email@gmail.com
```

## Step 7: Build and Deploy

```bash
# Build Docker images
docker compose -f docker-compose.prod.yml build

# Start services
docker compose -f docker-compose.prod.yml up -d

# Check status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f
```

## Step 8: Access SipSetu

Open browser and go to:
```
http://YOUR_PUBLIC_IP
```

## Optional: Domain & SSL

### Add Domain Name

1. Buy a domain (e.g., from Namecheap, Cloudflare)
2. Add DNS A record pointing to your public IP
3. Update `FRONTEND_URL` in `.env.production`

### Enable SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot -y

# Get certificate (replace your domain)
sudo certbot certonly --standalone -d yourdomain.com

# Update nginx config
nano backend/nginx.conf
# Uncomment the HTTPS server block
# Update certificate paths

# Restart services
docker compose -f docker-compose.prod.yml restart frontend
```

## Useful Commands

```bash
# View running containers
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f backend

# Restart a service
docker compose -f docker-compose.prod.yml restart backend

# Stop all services
docker compose -f docker-compose.prod.yml down

# Update and redeploy
git pull
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Check disk usage
df -h

# Check memory usage
free -h

# Check running processes
docker stats
```

## Monitoring

```bash
# View container resources
docker stats

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Check health
curl http://localhost:5000/api/health
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 80
sudo lsof -i :80

# Kill the process
sudo kill -9 PID
```

### Out of Memory

```bash
# Check memory
free -h

# Add swap space
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Docker Issues

```bash
# Restart Docker
sudo systemctl restart docker

# Clean up
docker system prune -a

# View Docker logs
sudo journalctl -u docker
```

### Firewall Rules

```bash
# Check firewall
sudo iptables -L

# Open ports (if needed)
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

## Cost Breakdown

| Component | Cost |
|-----------|------|
| VM Instance (4 OCPU, 24GB) | **Free** |
| Storage (200GB) | **Free** |
| Network (10TB/month) | **Free** |
| **Total** | **$0/month** |

## Limitations

- ARM instances only (no x86)
- Limited to 4 OCPUs, 24GB RAM
- 200GB boot volume
- 10TB/month network egress
- No GPU instances

## Alternatives

If you need more resources:

1. **Always Free Tier**: Use Oracle Cloud Free Tier (recommended)
2. **Paid Tier**: Upgrade to pay-as-you-go
3. **Other Providers**: AWS, GCP, Azure free tiers

## Support

- Oracle Cloud Documentation: https://docs.oracle.com/en-us/iaas/Content/home.htm
- Oracle Cloud Forums: https://community.oracle.com/community/cloud-computing
- SipSetu Issues: https://github.com/Ankit-49/SipSetu/issues
