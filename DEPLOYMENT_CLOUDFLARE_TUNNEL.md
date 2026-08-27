# Deploy SipSetu via Cloudflare Tunnel (Free, No Credit Card)

## What You Get

- ✅ **Public URL** — share with anyone
- ✅ **HTTPS** — automatic
- ✅ **Zero cost** — no signup, no credit card
- ✅ **2 minutes** to set up
- ⚠️ **Must be online** — your PC must be on for the tunnel to work

## Quick Start (3 Steps)

### Step 1: Start your backend

```cmd
cd "F:\Project\Reseme Analyzer\SipSetu\backend"
.venv\Scripts\activate
python -m flask run --host=0.0.0.0 --port=5000
```

### Step 2: Start the tunnel

```cmd
scripts\quick_tunnel.bat
```

Or manually:
```cmd
cloudflared tunnel --url http://localhost:5000
```

### Step 3: Copy your public URL

You'll see something like:
```
+--------------------------------------------------------------------------------------------+
|  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
|  https://random-name-here.trycloudflare.com                                                |
+--------------------------------------------------------------------------------------------+
```

**That's it!** Open that URL in any browser. You're live on the internet.

## Full Stack (Frontend + Backend)

For both frontend and backend with public URLs:

```cmd
scripts\start_fullstack.bat
```

This gives you **two URLs**:
- `https://xxx.trycloudflare.com` → Backend API (port 5000)
- `https://yyy.trycloudflare.com` → Frontend UI (port 5173)

### Configure frontend to use backend tunnel

Set the environment variable before starting the frontend:

```cmd
set VITE_API_URL=https://xxx.trycloudflare.com/api/v1
cd frontend
npm run dev
```

Or in `frontend/.env`:
```
VITE_API_URL=https://YOUR-BACKEND-TUNNEL.trycloudflare.com/api/v1
```

## Deploy Frontend to Cloudflare Pages (Permanent URL)

For a **permanent** frontend URL that doesn't need your PC:

1. Create a free Cloudflare account: https://dash.cloudflare.com/sign-up
2. Go to "Workers & Pages" → "Create" → "Pages" → "Connect to Git"
3. Select your GitHub repo
4. Set build config:
   - **Build command**: `cd frontend && npm install && npm run build`
   - **Output directory**: `frontend/dist`
5. Add environment variable:
   - `VITE_API_URL` = `https://YOUR-TUNNEL-URL.trycloudflare.com/api/v1`
6. Deploy

Your frontend gets a URL like `sipsetu.pages.dev` permanently!

## Architecture

```
┌──────────────────────────┐     ┌──────────────────────────┐
│   Cloudflare Pages       │     │   Cloudflare Tunnel       │
│   (Permanent URL)        │     │   (Your PC)              │
│                          │     │                          │
│   sipsetu.pages.dev ─────┼────▶│   localhost:5000         │
│   Free, always-on        │     │   Flask Backend          │
│   No credit card         │     │   PostgreSQL             │
│                          │     │   Redis                  │
└──────────────────────────┘     └──────────────────────────┘
```

## Troubleshooting

### "cloudflared not found"
Run `scripts\install_cloudflared.bat` or download from:
https://github.com/cloudflare/cloudflared/releases/latest

### Tunnel connects but API returns errors
Check that the frontend's `VITE_API_URL` points to the correct tunnel URL.

### Backend shows 500 errors
Make sure PostgreSQL and Redis are running:
```cmd
docker ps
# If not running:
docker compose up -d postgres redis
```

### Want a stable subdomain?
Sign up for a free Cloudflare account, then:
```cmd
cloudflared tunnel login
cloudflared tunnel create sipsetu
cloudflared tunnel route dns sipsetu your-subdomain.trycloudflare.com
cloudflared tunnel run --url http://localhost:5000 sipsetu
```

## Files

| File | Description |
|------|-------------|
| `scripts/quick_tunnel.bat` | One-click tunnel (backend only) |
| `scripts/start_fullstack.bat` | Full stack with two tunnels |
| `scripts/install_cloudflared.bat` | Install cloudflared |
| `scripts/start_tunnel.bat` | Start services + tunnel |
