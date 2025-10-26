# Security Best Practices for Project Vigil

## 🔐 Protecting API Keys and Secrets

### ✅ **DO:**

1. **Use `.env` files for secrets** (these are gitignored):

   ```bash
   # In data_collector/.env
   ANKR_DEVNET_RPC_URL=https://rpc.ankr.com/solana_devnet/YOUR_KEY_HERE
   ```

2. **Always use `.env.example` templates** (safe to commit):

   ```bash
   # In data_collector/.env.example
   ANKR_DEVNET_RPC_URL=https://rpc.ankr.com/solana_devnet/YOUR_ANKR_API_KEY_HERE
   ```

3. **Use environment variables in docker-compose**:

   ```yaml
   services:
     router:
       env_file:
         - ./vigil-intelligent-router/.env # ✅ File is gitignored
   ```

4. **Create your `.env` files locally**:
   ```bash
   cp data_collector/.env.example data_collector/.env
   cp vigil-intelligent-router/.env.example vigil-intelligent-router/.env
   # Then edit with real API keys
   ```

### ❌ **DON'T:**

1. **Never commit `.env` files**:

   ```bash
   # BAD - This file contains secrets!
   git add .env  # ❌ NEVER DO THIS
   ```

2. **Never hardcode API keys in source code**:

   ```go
   // BAD
   url := "https://api.com/?api-key=abc123"  // ❌ Don't hardcode

   // GOOD
   url := os.Getenv("API_URL")  // ✅ Use environment variables
   ```

3. **Never commit API keys in docker-compose.yml**:

   ```yaml
   # BAD
   environment:
     - API_KEY=abc123xyz # ❌ Don't commit secrets

   # GOOD
   env_file:
     - .env # ✅ Use env file (gitignored)
   ```

## 🛡️ Current Protection Status

### Files Protected (Gitignored):

- ✅ `data_collector/.env` - Contains RPC API keys
- ✅ `vigil-intelligent-router/.env` - Contains RPC URL mappings with keys
- ✅ `vigil-ml-layer/.env` (if created)
- ✅ All `*.env` files

### Safe to Commit:

- ✅ `data_collector/.env.example` - Template without real keys
- ✅ `vigil-intelligent-router/.env.example` - Template without real keys
- ✅ `docker-compose.yml` - Now uses env_file instead of hardcoded values

## 🔍 How to Check for Exposed Secrets

### Before Committing:

```bash
# Check what's staged
git status

# Review changes
git diff

# Search for potential API keys
git diff | grep -i "api-key\|api_key"
```

### Scan Repository:

```bash
# Check if .env files are tracked
git ls-files | grep "\.env$"

# Should return nothing! Only .env.example files should show up
git ls-files | grep "\.env"
# Output should only show:
# data_collector/.env.example
# vigil-intelligent-router/.env.example
```

### Use git-secrets (Recommended):

```bash
# Install git-secrets
brew install git-secrets  # macOS
# or: apt-get install git-secrets  # Linux

# Set up in your repo
cd /Users/ghostxd/Desktop/project-vigil
git secrets --install
git secrets --register-aws

# Add custom patterns
git secrets --add 'api-key=[A-Za-z0-9]+'
git secrets --add 'api_key=[A-Za-z0-9]+'
```

## 🔒 Additional Security Measures

### 1. Environment Variable Validation

Each service validates required env vars on startup:

```go
// config.go validates configuration
func (c *Config) Validate() error {
    if c.MLServiceURL == "" {
        return fmt.Errorf("ML_SERVICE_URL is required")
    }
    // ...
}
```

### 2. Secrets Management (Production)

For production deployments, use:

- **Docker Secrets**: For Docker Swarm

  ```yaml
  secrets:
    ankr_api_key:
      external: true
  ```

- **Kubernetes Secrets**: For K8s deployments

  ```yaml
  apiVersion: v1
  kind: Secret
  metadata:
    name: rpc-api-keys
  data:
    ankr-key: <base64-encoded-key>
  ```

- **Cloud Providers**:
  - AWS: AWS Secrets Manager
  - GCP: Secret Manager
  - Azure: Key Vault

### 3. API Key Rotation

Best practices:

- Rotate API keys quarterly
- Use different keys for dev/staging/prod
- Monitor API key usage
- Revoke compromised keys immediately

### 4. Access Control

```bash
# Restrict .env file permissions
chmod 600 .env

# Only owner can read/write
ls -la .env
# -rw------- 1 user user 1234 Oct 25 12:00 .env
```

## ✅ Setup Checklist

Before deploying:

- [ ] All `.env` files are in `.gitignore`
- [ ] `.env.example` files have placeholder values only
- [ ] `docker-compose.yml` uses `env_file` instead of hardcoded secrets
- [ ] File permissions on `.env` files are restrictive (600)
- [ ] API keys are rotated from default/example values
- [ ] Different keys used for production vs development
- [ ] git-secrets or similar tool is installed
- [ ] Repository has been scanned for exposed secrets

## 🚨 If You Accidentally Commit Secrets

1. **Remove from history immediately**:

   ```bash
   # Install BFG Repo-Cleaner
   brew install bfg

   # Remove sensitive file from history
   bfg --delete-files .env

   # Or remove sensitive strings
   bfg --replace-text secrets.txt  # File with patterns to replace

   # Force push (careful!)
   git push --force
   ```

2. **Rotate all exposed API keys immediately**

3. **Consider repository as compromised** - start fresh if necessary

## 📚 Resources

- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [git-secrets](https://github.com/awslabs/git-secrets)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [truffleHog](https://github.com/trufflesecurity/trufflehog) - Scan for secrets

## 🎯 Summary

**The golden rule**: Never commit anything in a `.env` file. Always use `.env.example` with placeholders.
