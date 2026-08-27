# Deploy Frontend to Cloudflare Pages (Free, Permanent URL)

## What You Get

- ✅ **Permanent URL** like `sipsetu.pages.dev` — never changes
- ✅ **Free hosting** — unlimited bandwidth, no credit card
- ✅ **Auto-deploy** — every push to `main` rebuilds and deploys
- ✅ **HTTPS** — automatic SSL
- ✅ **Global CDN** — fast worldwide

## Setup (One-Time, ~10 Minutes)

### Step 1: Create a Free Cloudflare Account

1. Go to https://dash.cloudflare.com/sign-up
2. Sign up with email (no credit card needed)
3. Verify your email

### Step 2: Get Your Cloudflare API Token

1. Go to https://dash.cloudflare.com/profile/api-tokens
2. Click **"Create Token"**
3. Select **"Cloudflare Pages — Edit"** template
4. Under **Account Resources**, select your account
5. Click **"Continue to summary"** → **"Create Token"**
6. **Copy the token** (you'll need it in Step 4)

### Step 3: Get Your Account ID

1. Go to https://dash.cloudflare.com/
2. Select any domain (or the right sidebar shows your Account ID)
3. Or go to https://dash.cloudflare.com/ → right sidebar → **Account ID**

### Step 4: Add Secrets to GitHub

1. Go to https://github.com/Ankit-49/SipSetu/settings/secrets/actions
2. Click **"New repository secret"**
3. Add two secrets:

| Name | Value |
|------|-------|
| `CLOUDFLARE_API_TOKEN` | Your API token from Step 2 |
| `CLOUDFLARE_ACCOUNT_ID` | Your Account ID from Step 3 |

### Step 5: Set the API URL Variable

1. Go to https://github.com/Ankit-49/SipSetu/settings/variables/actions
2. Click **"New repository variable"**
3. Add:

| Name | Value |
|------|-------|
| `VITE_API_URL` | `https://YOUR-TUNNEL-URL.trycloudflare.com/api/v1` |

Replace `YOUR-TUNNEL-URL` with your current tunnel URL (e.g., `vcr-investigated-org-fruit`).

**⚠️ Important:** Update this variable whenever you restart the tunnel and get a new URL!

### Step 6: Trigger Deployment

1. Go to https://github.com/Ankit-49/SipSetu/actions
2. Find **"Deploy to Cloudflare Pages"** workflow
3. Click **"Run workflow"** → select `main` → **"Run workflow"**

### Step 7: Access Your App

After ~2 minutes, your app is live at:

**https://sipsetu.pages.dev** 🎉

---

## How It Works

```
┌─────────────────────┐     ┌──────────────────────────┐
│   Cloudflare Pages  │────▶│   Cloudflare Tunnel       │
│   sipsetu.pages.dev │     │   your-tunnel.trycloud... │
│   (Frontend)        │     │   (Backend on your PC)    │
│                     │     │                           │
│   Free, permanent   │     │   Free, needs PC on       │
│   Auto-deploy       │     │   URL changes on restart  │
└─────────────────────┘     └──────────────────────────┘
```

1. User visits `sipsetu.pages.dev`
2. Frontend loads from Cloudflare's global CDN
3. API calls go to `YOUR-TUNNEL-URL.trycloudflare.com`
4. Cloudflare Tunnel forwards to `localhost:5000` on your PC
5. Backend processes and returns data

## Updating the API URL

When you restart the tunnel, you get a new URL. Update it:

1. Go to GitHub → Settings → Secrets and variables → Actions → **Variables**
2. Edit `VITE_API_URL` with the new tunnel URL
3. The next push to `main` will auto-deploy, OR:
4. Manually re-run the workflow

## Alternative: Manual Deployment (No GitHub Actions)

If you prefer not to use GitHub Actions:

```bash
# Install wrangler CLI
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Build and deploy
cd frontend
VITE_API_URL=https://YOUR-TUNNEL.trycloudflare.com/api/v1 npm run build
wrangler pages deploy dist --project-name=sipsetu
```

## Troubleshooting

### "Authentication error" in GitHub Actions
- Make sure `CLOUDFLARE_API_TOKEN` is set correctly
- Token must have **Cloudflare Pages — Edit** permission

### Frontend loads but API calls fail
- Check `VITE_API_URL` in GitHub Actions variables
- Make sure your tunnel is running: `cloudflared tunnel --url http://localhost:5000`
- Test the tunnel URL directly in browser

### Build fails
- Check Node.js version is 22+ in the workflow
- Check the build logs in GitHub Actions

### Want a custom domain?
1. Buy a domain or use a free one from Freenom
2. In Cloudflare Pages → your project → **Custom domains**
3. Add your domain
4. Update DNS as instructed

## Files

| File | Description |
|------|-------------|
| `frontend/wrangler.toml` | Cloudflare Pages config |
| `frontend/.env.production` | Production environment variables |
| `.github/workflows/cloudflare-pages.yml` | Auto-deploy workflow |
| `DEPLOYMENT_CLOUDFLARE_PAGES.md` | This guide |
