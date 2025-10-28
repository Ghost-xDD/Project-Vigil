# Railway Deployment Guide - Project Vigil

Complete guide to deploy all three Vigil services to Railway.

---

## Prerequisites

- GitHub account with project-vigil repository
- Railway account (sign up at https://railway.app)
- RPC API keys (Helius, Alchemy) - optional but recommended

## What's Included

✅ **Config as Code**: Each service has a `railway.toml` file that automatically configures build and deployment settings ([Railway Config as Code docs](https://docs.railway.com/guides/config-as-code))

- `vigil_data_collector/railway.toml`
- `vigil-ml-layer/railway.toml`
- `vigil-intelligent-router/railway.toml`

This means Railway will automatically:

- Use the correct Dockerfile
- Set up health checks
- Configure restart policies
- No manual configuration needed!

---

## Step 1: Create Railway Project

1. Go to https://railway.app/dashboard
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select **`project-vigil`** repository
6. Railway will detect your repo but **don't auto-deploy yet**

---

## Step 2: Deploy Data Collector Service

### Create the Service:

1. In your Railway project, click **"+ New"**
2. Select **"GitHub Repo"** → Choose `project-vigil`
3. Click on the new service card
4. Go to **Settings** tab:
   - **Service Name**: `vigil-data-collector`
   - **Root Directory**: `/vigil_data_collector`

✨ **Railway will automatically detect `railway.toml` and configure the Dockerfile, health checks, and restart policy!**

### Configure Environment Variables:

Go to **Variables** tab and add:

```bash
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# RPC URLs (replace with your actual keys)
ANKR_DEVNET_RPC_URL=https://rpc.ankr.com/solana_devnet
HELIUS_DEVNET_RPC_URL=https://devnet.helius-rpc.com/?api-key=YOUR_HELIUS_KEY
ALCHEMY_DEVNET_RPC_URL=https://solana-devnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
SOLANA_PUBLIC_DEVNET_RPC_URL=https://api.devnet.solana.com

# Polling
POLL_INTERVAL_SECONDS=15
REQUEST_TIMEOUT_SECONDS=8

# CORS (add your Vercel domain later)
CORS_ORIGINS=["*"]
```

### Expose Port:

1. Go to **Settings** → **Networking**
2. Click **"Generate Domain"** (this creates a public URL)
3. **Save the URL** - you'll need it! Example: `https://vigil-data-collector-production.up.railway.app`

### Deploy:

1. Click **"Deploy"** or push to GitHub
2. Wait for build to complete (~2-3 minutes)
3. Check **"Deployments"** tab for status

---

## Step 3: Deploy ML Service

### Create the Service:

1. Click **"+ New"** → **"GitHub Repo"** → `project-vigil`
2. Go to **Settings**:
   - **Service Name**: `vigil-ml-service`
   - **Root Directory**: `/vigil-ml-layer`

✨ **Railway will automatically detect `railway.toml` and configure everything!**

### Configure Environment Variables:

Go to **Variables** tab:

```bash
# Server
HOST=0.0.0.0
PORT=8001
```

⚠️ **Note**: The ML models in `/models` and `/artifacts` directories will be included in the Docker build automatically since they're in your repo.

### Expose Port:

1. Go to **Settings** → **Networking**
2. Click **"Generate Domain"**
3. **Save the URL** - Example: `https://vigil-ml-service-production.up.railway.app`

### Deploy:

1. Click **"Deploy"**
2. Wait for build (~3-4 minutes - larger image with ML dependencies)

---

## Step 4: Deploy Intelligent Router

### Create the Service:

1. Click **"+ New"** → **"GitHub Repo"** → `project-vigil`
2. Go to **Settings**:
   - **Service Name**: `vigil-intelligent-router`
   - **Root Directory**: `/vigil-intelligent-router`

✨ **Railway will automatically detect `railway.toml` and configure everything!**

### Configure Environment Variables:

Go to **Variables** tab and add:

```bash
# Server
ROUTER_HOST=0.0.0.0
ROUTER_PORT=8080

# Service URLs (use your Railway URLs from steps 2 & 3)
ML_SERVICE_URL=https://vigil-ml-service-production.up.railway.app
DATA_COLLECTOR_URL=https://vigil-data-collector-production.up.railway.app

# RPC Node URLs (same as Data Collector)
ANKR_DEVNET_RPC_URL=https://rpc.ankr.com/solana_devnet
HELIUS_DEVNET_RPC_URL=https://devnet.helius-rpc.com/?api-key=YOUR_HELIUS_KEY
ALCHEMY_DEVNET_RPC_URL=https://solana-devnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
SOLANA_PUBLIC_DEVNET_RPC_URL=https://api.devnet.solana.com

# Fallback
FALLBACK_RPC_URL=https://api.devnet.solana.com
FALLBACK_ENABLED=true

# Timeouts
REQUEST_TIMEOUT_SECONDS=30
ML_QUERY_TIMEOUT_SECONDS=5

# Logging
LOG_LEVEL=info
LOG_FORMAT=json
HEALTH_CHECK_ENABLED=true
```

### Expose Port:

1. Go to **Settings** → **Networking**
2. Click **"Generate Domain"**
3. **Save the URL** - Example: `https://vigil-intelligent-router-production.up.railway.app`

### Deploy:

1. Click **"Deploy"**
2. Wait for build (~2 minutes)

---

## Step 5: Verify All Services

### Test Each Service:

**1. Data Collector:**

```bash
curl https://vigil-data-collector-production.up.railway.app/health
```

Expected: `{"status":"healthy","scheduler_running":true,...}`

**2. ML Service:**

```bash
curl https://vigil-ml-service-production.up.railway.app/health
```

Expected: `{"status":"healthy","models_loaded":true}`

**3. Intelligent Router:**

```bash
curl https://vigil-intelligent-router-production.up.railway.app/health
```

Expected: `{"status":"healthy"}`

**4. Test Full RPC Flow:**

```bash
curl -X POST https://vigil-intelligent-router-production.up.railway.app \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "getHealth"
  }'
```

**5. Check Data Collection:**

```bash
curl https://vigil-data-collector-production.up.railway.app/api/v1/metrics/latest-metrics
```

**6. Test ML Predictions:**

```bash
curl https://vigil-ml-service-production.up.railway.app/predict \
  -X POST \
  -H "Content-Type: application/json" \
  -d "{\"metrics\":$(curl -s https://vigil-data-collector-production.up.railway.app/api/v1/metrics/history?limit=20)}"
```

---

## Step 6: Update Vercel Environment Variables

1. Go to your Vercel project → **Settings** → **Environment Variables**
2. Update or add:

```bash
NEXT_PUBLIC_ROUTER_URL=https://vigil-intelligent-router-production.up.railway.app
NEXT_PUBLIC_DATA_COLLECTOR_URL=https://vigil-data-collector-production.up.railway.app
NEXT_PUBLIC_ML_SERVICE_URL=https://vigil-ml-service-production.up.railway.app
NEXT_PUBLIC_PRIVY_APP_ID=cmhaefijm00c0l40c7b7zx14p
```

3. **Redeploy** your Vercel app to apply changes

---

## Step 7: Update CORS Settings

Now that you have your Vercel domain, update the Data Collector CORS:

1. Go to Railway → **vigil-data-collector** → **Variables**
2. Update `CORS_ORIGINS`:

```bash
CORS_ORIGINS=["https://your-vercel-app.vercel.app","http://localhost:3000"]
```

3. Redeploy the service

---

## Railway Tips & Tricks

### View Logs:

- Click on any service → **Deployments** → Click latest deployment → **View Logs**

### Monitor Resources:

- Go to service → **Metrics** tab to see CPU/Memory/Network usage

### Cost Management:

- Railway gives you **$5/month free credit**
- Each service costs ~$5-10/month depending on usage
- Total estimated cost: **~$10-20/month** for all 3 services

### Custom Domains (Optional):

1. Go to service → **Settings** → **Domains**
2. Add custom domain like `api.yourdomain.com`
3. Point your DNS to Railway's proxy

### Environment Groups (Pro Tip):

1. Create a **Shared Variables** group for common configs
2. Reference across services like `${{shared.RPC_URL}}`

---

## Troubleshooting

### Issue 1: Service Won't Start

**Check**: Railway logs for errors
**Fix**: Verify Dockerfile path and root directory are correct

### Issue 2: Services Can't Communicate

**Check**: Environment variables for service URLs
**Fix**: Make sure URLs include `https://` and are the public Railway URLs

### Issue 3: ML Service Out of Memory

**Check**: Railway Metrics tab
**Fix**: Upgrade to a larger instance size in Settings

### Issue 4: Data Collector Not Polling

**Check**: Logs for RPC errors
**Fix**: Verify RPC URLs and API keys are valid

### Issue 5: Router Returns 502

**Check**: ML_SERVICE_URL and DATA_COLLECTOR_URL are correct
**Fix**: Test each service health endpoint individually

---

## Monitoring & Maintenance

### Health Checks:

Set up a cron job or monitoring service (like UptimeRobot) to ping:

- `/health` endpoint on all 3 services every 5 minutes

### Log Monitoring:

- Check Railway logs daily for errors
- Look for RPC timeouts or ML prediction failures

### Cost Monitoring:

- Railway dashboard shows daily usage
- Set up billing alerts in Railway settings

---

## Next Steps

✅ All services deployed
✅ Vercel connected
✅ Health checks passing

**You're ready to go! Visit your Vercel app and test:**

1. Login with Privy
2. Check Dashboard for node metrics
3. Run Chaos test
4. Test RPC requests in Playground

---

## Support

**Railway Issues**: https://help.railway.app
**Project Issues**: Check Railway logs → Deployments → View Logs
**Need Help?**: Railway has great Discord community

---

**Deployment Date**: _Add date when deployed_
**Deployed By**: _Your name_
**Railway Project**: _Add Railway project URL_
