# Project Vigil - Secure Setup Guide

## 🔐 Security First Setup

Follow these steps to set up Project Vigil without exposing API keys.

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd project-vigil
```

### Step 2: Run the Automated Setup Script

```bash
chmod +x setup.sh
./setup.sh
```

This will create `.env` files from `.env.example` templates.

### Step 3: Add Your API Keys

**IMPORTANT**: Never commit these files!

#### Data Collector (data_collector/.env)

Edit `data_collector/.env`:

```bash
nano data_collector/.env
```

Replace the placeholder values:

```env
ANKR_DEVNET_RPC_URL=https://rpc.ankr.com/solana_devnet/YOUR_ACTUAL_ANKR_KEY
HELIUS_DEVNET_RPC_URL=https://devnet.helius-rpc.com/?api-key=YOUR_ACTUAL_HELIUS_KEY
ALCHEMY_DEVNET_RPC_URL=https://solana-devnet.g.alchemy.com/v2/YOUR_ACTUAL_ALCHEMY_KEY
```

#### Intelligent Router (vigil-intelligent-router/.env)

Edit `vigil-intelligent-router/.env`:

```bash
nano vigil-intelligent-router/.env
```

Replace the placeholder values with the SAME keys:

```env
ANKR_DEVNET_RPC_URL=https://rpc.ankr.com/solana_devnet/YOUR_ACTUAL_ANKR_KEY
HELIUS_DEVNET_RPC_URL=https://devnet.helius-rpc.com/?api-key=YOUR_ACTUAL_HELIUS_KEY
ALCHEMY_DEVNET_RPC_URL=https://solana-devnet.g.alchemy.com/v2/YOUR_ACTUAL_ALCHEMY_KEY
```

### Step 4: Verify .env Files Are Gitignored

```bash
# This should return nothing (or only show .env.example files)
git status | grep "\.env"

# Verify .gitignore is working
git check-ignore data_collector/.env
# Should output: data_collector/.env

git check-ignore vigil-intelligent-router/.env
# Should output: vigil-intelligent-router/.env
```

### Step 5: Start the Services

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or start each service manually
# Terminal 1: Data Collector
cd data_collector
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py

# Terminal 2: ML Service (after training models)
cd vigil-ml-layer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m src.generate_data
python -m src.train
python run_api.py

# Terminal 3: Intelligent Router
cd vigil-intelligent-router
go build -o vigil-router .
./vigil-router
```

## ✅ Security Checklist

Before pushing to GitHub:

- [ ] All `.env` files are in `.gitignore`
- [ ] Only `.env.example` files are tracked by Git
- [ ] No API keys in `docker-compose.yml`
- [ ] No API keys in source code
- [ ] Run: `git status` - no `.env` files should appear
- [ ] Run: `git diff` - no secrets visible
- [ ] Optional: Install pre-commit hooks: `pip install pre-commit && pre-commit install`

## 🚨 If You Accidentally Commit a Secret

**STOP! Don't panic, but act quickly:**

1. **DO NOT push to GitHub yet** if you haven't already

2. **Remove from last commit**:

   ```bash
   git reset HEAD~1
   # Fix the .env files
   git add .
   git commit -m "Your commit message"
   ```

3. **If already pushed**:
   - Rotate ALL exposed API keys immediately at the provider
   - Use BFG Repo-Cleaner or git-filter-repo to remove from history
   - Force push (understand the implications)
   - Treat repository as potentially compromised

## 🎯 Quick Reference

### Get API Keys

- **Ankr**: https://www.ankr.com/rpc/
- **Helius**: https://www.helius.dev/
- **Alchemy**: https://www.alchemy.com/
- **Solana Public**: No key needed

### File Locations

```
project-vigil/
├── data_collector/.env              ← Contains RPC API keys (GITIGNORED)
├── data_collector/.env.example      ← Safe template (TRACKED)
├── vigil-intelligent-router/.env    ← Contains RPC URLs with keys (GITIGNORED)
├── vigil-intelligent-router/.env.example ← Safe template (TRACKED)
├── docker-compose.yml               ← Uses env_file (SAFE - no secrets)
└── .gitignore                       ← Protects all .env files
```

### Verify Your Setup

```bash
# Should show .env files are ignored
git status --ignored | grep "\.env$"

# Should return files
git check-ignore **/.env
```

## 🔒 Production Deployment

For production, use proper secrets management:

### Docker Swarm

```bash
# Create secrets
echo "your-api-key" | docker secret create ankr_key -
echo "your-api-key" | docker secret create helius_key -

# Reference in docker-compose
secrets:
  ankr_key:
    external: true
```

### Kubernetes

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: rpc-secrets
type: Opaque
stringData:
  ankr-key: your-ankr-key
  helius-key: your-helius-key
```

### Cloud Platforms

- **AWS**: Use AWS Secrets Manager or Parameter Store
- **GCP**: Use Secret Manager
- **Azure**: Use Key Vault
- **Heroku**: Use Config Vars
- **Render**: Use Environment Groups

## 📞 Questions?

See `SECURITY.md` for comprehensive security documentation.
