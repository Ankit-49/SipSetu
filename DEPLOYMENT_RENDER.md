# Deploy Backend to Render (Free, Permanent URL)

## What You Get

- ✅ **Permanent URL** like `sipsetu-api.onrender.com` — never changes
- ✅ **Free hosting** — no credit card required
- ✅ **Managed PostgreSQL** — free 90-day database included
- ✅ **Auto-deploy** — every push to `main` rebuilds
- ✅ **HTTPS** — automatic SSL
- ⚠️ **Spins down after 15min idle** — 30s cold start on first request

## Quick Setup (5 Minutes)

### Step 1: Create Render Account

1. Go to https://dashboard.render.com/register
2. Sign up with **GitHub** (easiest — no credit card needed)

### Step 2: Create a PostgreSQL Database

1. Click **"New +"** → **"PostgreSQL"**
2. Settings:
   - **Name**: `sipsetu-db`
   - **Database**: `sipsetu`
   - **User**: `sipsetu`
   - **Plan**: Free
3. Click **"Create Database"**
4. **Copy the Internal Database URL** (you'll need it)

### Step 3: Create the Backend Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your **GitHub** account if not already connected
3. Select **`Ankit-49/SipSetu`** repository
4. Configure:
   - **Name**: `sipsetu-api`
   - **Region**: Oregon (or closest to you)
   - **Branch**: `main`
   - **Runtime**: Python
   - **Build Command**:
     ```
     pip install -r backend/requirements.txt
     ```
   - **Start Command**:
     ```
     cd backend && gunicorn -k gevent -w 2 -b 0.0.0.0:$PORT app:create_app()
     ```
   - **Plan**: Free

### Step 4: Set Environment Variables

In the Web Service settings → **Environment** tab, add:

| Key | Value |
|-----|-------|
| `FLASK_APP` | `app.py` |
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | (click "Generate") |
| `DATABASE_URL` | Paste your PostgreSQL Internal URL from Step 2 |
| `FRONTEND_URL` | `https://sipsetu.pages.dev` |
| `PYTHON_VERSION` | `3.11` |

### Step 5: Deploy

Click **"Create Web Service"** — Render will build and deploy automatically.

Your backend will be live at: **https://sipsetu-api.onrender.com** 🎉

## Update Frontend to Use Render Backend

Go to GitHub → Settings → Secrets and variables → Actions → **Variables**:

Update `VITE_API_URL`:
```
https://sipsetu-api.onrender.com/api/v1
```

Then re-run the "Deploy to Cloudflare Pages" workflow.

## Architecture (Final)

```
┌─────────────────────────┐     ┌──────────────────────────┐
│   Cloudflare Pages      │     │   Render                  │
│   sipsetu.pages.dev     │────▶│   sipsetu-api.onrender.com│
│   (Frontend)            │     │   (Backend + Database)    │
│                         │     │                           │
│   Free, permanent       │     │   Free, permanent         │
│   Always on             │     │   30s cold start          │
└─────────────────────────┘     └──────────────────────────┘
```

## Cold Start Optimization

Since Render free tier spins down after 15min idle:

1. **UptimeRobot** (free) can ping your backend every 5 minutes to keep it awake:
   - Sign up at https://uptimerobot.com
   - Add HTTP monitor for `https://sipsetu-api.onrender.com/api/v1/health`
   - Set interval to 5 minutes

2. Or use **cron-job.org** (free) to ping every 10 minutes

## Files

| File | Description |
|------|-------------|
| `render.yaml` | Render Blueprint (auto-deploy config) |
| `DEPLOYMENT_RENDER.md` | This guide |
