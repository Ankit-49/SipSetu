# SipSetu - Cloudflare Pages + Local Backend

Deploy frontend to Cloudflare Pages (free) and run backend locally!

## Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│   Cloudflare Pages  │     │   Local Backend     │
│   (Frontend)        │     │   (Your Machine)    │
│                     │     │                     │
│   - React App       │────▶│   - Flask API       │
│   - Static Assets   │     │   - PostgreSQL      │
│                     │     │   - Redis           │
│   Free Tier         │     │   - Celery          │
│   No Credit Card    │     │   Free              │
└─────────────────────┘     └─────────────────────┘
```

## Part 1: Deploy Frontend to Cloudflare Pages

### Step 1: Create Cloudflare Account

1. Go to: https://dash.cloudflare.com/sign-up
2. Sign up with email (no credit card needed)
3. Verify your email

### Step 2: Connect GitHub Repository

1. Log in to Cloudflare Dashboard
2. Go to "Workers & Pages"
3. Click "Create application"
4. Click "Pages" tab
5. Click "Connect to Git"
6. Select "GitHub"
7. Authorize Cloudflare
8. Select repository: `Ankit-49/SipSetu`
9. Click "Begin setup"

### Step 3: Configure Build Settings

**Build settings:**
- **Production branch**: `main`
- **Build command**: `cd frontend && npm install && npm run build`
- **Build output directory**: `frontend/dist`

**Environment variables:**
- `NODE_VERSION`: `18`
- `VITE_API_URL`: `http://localhost:5000/api`

Click "Save and Deploy"

### Step 4: Get Your Cloudflare URL

After deployment, you'll get a URL like:
```
https://sipsetu.pages.dev
```

### Step 5: Update Backend CORS

Edit `backend/app.py` to allow Cloudflare Pages:

```python
# Add your Cloudflare Pages URL to CORS origins
CORS(app, origins=[
    "http://localhost:5173",  # Local dev
    "http://localhost:3000",  # Local prod
    "https://sipsetu.pages.dev",  # Cloudflare Pages
    settings.FRONTEND_URL
], supports_credentials=True)
```

## Part 2: Run Backend Locally

### Step 1: Start Backend with Docker

```bash
cd SipSetu

# Copy environment template
cp .env.production.example .env.production

# Edit .env.production
# Set your configuration

# Start services
docker compose -f docker-compose.prod.yml up -d postgres redis backend celery-worker celery-beat
```

### Step 2: Or Run Without Docker

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis (if not using Docker)
# Or use local installations

# Run migrations
python -m alembic upgrade head

# Start backend
python app.py
```

### Step 3: Expose Backend to Internet (Optional)

To make your local backend accessible from Cloudflare Pages:

#### Option A: ngrok (Recommended)

```bash
# Install ngrok
# https://ngrok.com/download

# Start ngrok
ngrok http 5000
```

You'll get a URL like:
```
https://abc123.ngrok-free.app
```

#### Option B: Cloudflare Tunnel (Free)

```bash
# Install cloudflared
# https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

# Login
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create sipsetu

# Configure tunnel
cat > ~/.cloudflared/config.yml << EOF
tunnel: YOUR_TUNNEL_ID
credentials-file: ~/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: api.sipsetu.com
    service: http://localhost:5000
  - service: http_status:404
EOF

# Run tunnel
cloudflared tunnel run sipsetu
```

### Step 4: Update Cloudflare Pages Environment

1. Go to Cloudflare Dashboard → Workers & Pages → sipsetu
2. Go to "Settings" → "Environment variables"
3. Add:
   - `VITE_API_URL`: `https://abc123.ngrok-free.app/api`
   - Or your Cloudflare Tunnel URL

4. Redeploy the site

## Part 3: Custom Domain (Optional)

### Add Custom Domain to Cloudflare Pages

1. Buy a domain (e.g., from Namecheap, Google Domains)
2. In Cloudflare Dashboard:
   - Go to your domain
   - Change nameservers to Cloudflare's
3. In Pages settings:
   - Go to "Custom domains"
   - Add your domain
4. SSL is automatic!

## Useful Commands

```bash
# Frontend
# Redeploy to Cloudflare Pages
git push origin main
# Cloudflare will auto-deploy

# Backend
# View logs
docker compose -f docker-compose.prod.yml logs -f backend

# Restart backend
docker compose -f docker-compose.prod.yml restart backend

# Stop all
docker compose -f docker-compose.prod.yml down
```

## Limitations

### Cloudflare Pages (Free Tier)
- 500 builds per month
- 1 build per minute
- 100GB bandwidth per month
- No server-side rendering

### Local Backend
- Only accessible when your computer is on
- ngrok free tier: 1 tunnel, random URL
- Cloudflare Tunnel: Always on (if configured)

## Cost Breakdown

| Component | Cost |
|-----------|------|
| Cloudflare Pages | **Free** |
| Local Backend | **Free** |
| ngrok (free tier) | **Free** |
| **Total** | **$0/month** |

## Troubleshooting

### CORS Errors

1. Check that Cloudflare Pages URL is in CORS origins
2. Make sure backend is running
3. Check ngrok/tunnel is running

### Build Fails on Cloudflare

1. Check build logs in Cloudflare Dashboard
2. Ensure `package.json` has correct build script
3. Check Node.js version is set to 18

### Backend Not Accessible

1. Check if backend is running: `curl http://localhost:5000/api/health`
2. Check ngrok/tunnel is running
3. Check firewall allows incoming connections

### ngrok URL Changes

ngrok free tier changes URL on restart. Solutions:

1. Use Cloudflare Tunnel (stable URL)
2. Update Cloudflare Pages env var after each restart
3. Use ngrok paid tier (stable URL)

## Next Steps

1. Set up Cloudflare Tunnel for stable URL
2. Add custom domain
3. Enable Cloudflare analytics
4. Set up automatic backend deployment

## Support

- Cloudflare Pages Docs: https://developers.cloudflare.com/pages/
- Cloudflare Tunnel Docs: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
- SipSetu Issues: https://github.com/Ankit-49/SipSetu/issues
