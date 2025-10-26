# Docker Deployment Guide

Complete guide to running Project Vigil with Docker.

## 🐳 Quick Start (All Services)

### Step 1: Set Up Environment Files

```bash
# Run the setup script
./setup.sh

# Edit .env files with your API keys
nano data_collector/.env
nano vigil-intelligent-router/.env
```

### Step 2: Start All Services

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Step 3: Verify Services

```bash
# Check health endpoints
curl http://localhost:8080/health  # Router (should see: "status": "healthy")
curl http://localhost:8000/health  # Data Collector
curl http://localhost:8001/health  # ML Service (may fail if models not trained)
```

## 🔧 Training ML Models in Docker

The ML Service requires trained models. Here's how to train them:

### Option 1: Train Before Starting

```bash
# Start only data collector and ML service
docker-compose up -d data-collector ml-service

# Access ML service container
docker-compose exec ml-service bash

# Inside container, train models
python -m src.generate_data
python -m src.train
exit

# Restart ML service to load models
docker-compose restart ml-service

# Now start the router
docker-compose up -d intelligent-router
```

### Option 2: Train Locally, Mount Volume

```bash
# Train locally
cd vigil-ml-layer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m src.generate_data
python -m src.train

# Models are now in vigil-ml-layer/models/ and vigil-ml-layer/artifacts/
# docker-compose.yml already mounts these as volumes

# Start all services
cd ..
docker-compose up -d
```

## 📊 Service Startup Order

Docker Compose handles dependencies automatically:

```
1. data-collector starts first
   ↓
2. ml-service starts (depends on data-collector)
   ↓
3. intelligent-router starts last (depends on both)
```

## 🔍 Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f intelligent-router
docker-compose logs -f data-collector
docker-compose logs -f ml-service

# Last 100 lines
docker-compose logs --tail=100 -f
```

### Check Service Status

```bash
# List running containers
docker-compose ps

# Should show:
# NAME                      STATUS         PORTS
# vigil-data-collector      Up (healthy)   0.0.0.0:8000->8000/tcp
# vigil-ml-service          Up (healthy)   0.0.0.0:8001->8001/tcp
# vigil-intelligent-router  Up (healthy)   0.0.0.0:8080->8080/tcp
```

### Access Container Shells

```bash
# Data Collector
docker-compose exec data-collector bash

# ML Service
docker-compose exec ml-service bash

# Intelligent Router
docker-compose exec intelligent-router sh
```

## 🧪 Testing the Stack

### Test Data Collector

```bash
curl http://localhost:8000/api/v1/metrics/latest-metrics | jq
```

Expected: JSON array with 5 node metrics.

### Test ML Service

```bash
# First, ensure models are trained
docker-compose exec ml-service ls -la models/

# Check health
curl http://localhost:8001/health | jq

# Should show: "models_loaded": true
```

### Test Intelligent Router

```bash
# Send RPC request through the router
curl -X POST http://localhost:8080/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "getHealth"
  }' | jq

# Check router logs
docker-compose logs intelligent-router | tail -20
```

## 🛠️ Common Commands

### Start/Stop

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Restart specific service
docker-compose restart intelligent-router
```

### Rebuild

```bash
# Rebuild all images
docker-compose build

# Rebuild specific service
docker-compose build data-collector

# Rebuild and start
docker-compose up -d --build
```

### Scale Services

```bash
# Run multiple router instances for high availability
docker-compose up -d --scale intelligent-router=3

# Note: You'll need a load balancer in front for this to work properly
```

## 📁 Volume Management

### Persistent Data

The ML service uses volumes for models:

```yaml
volumes:
  - ./vigil-ml-layer/models:/app/models
  - ./vigil-ml-layer/artifacts:/app/artifacts
```

This means:

- Models trained locally are available in Docker
- Models trained in Docker are available locally
- Data persists across container restarts

### Clean Up Volumes

```bash
# List volumes
docker volume ls

# Remove unused volumes
docker volume prune

# Remove all project data (careful!)
docker-compose down -v
```

## 🐛 Troubleshooting

### ML Service Shows "models_loaded": false

**Problem**: Models not trained

**Solution**:

```bash
docker-compose exec ml-service python -m src.generate_data
docker-compose exec ml-service python -m src.train
docker-compose restart ml-service
```

### Container Exits Immediately

```bash
# Check logs for errors
docker-compose logs <service-name>

# Common causes:
# - Missing .env file
# - Invalid configuration
# - Port already in use
```

### Port Already in Use

```bash
# Find and kill process using port
lsof -ti:8080 | xargs kill -9  # Router
lsof -ti:8000 | xargs kill -9  # Data Collector
lsof -ti:8001 | xargs kill -9  # ML Service

# Or change ports in docker-compose.yml
```

### Network Issues Between Services

```bash
# Verify network exists
docker network ls | grep vigil

# Inspect network
docker network inspect project-vigil_vigil-network

# Check if containers are on the network
docker-compose ps
```

### Permission Issues with Volumes

```bash
# Fix permissions on mounted directories
sudo chown -R $USER:$USER vigil-ml-layer/models
sudo chown -R $USER:$USER vigil-ml-layer/artifacts
```

## 🔄 Update Workflow

### Update Code

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build
```

### Update Dependencies

```bash
# Rebuild specific service
docker-compose build --no-cache ml-service
docker-compose up -d ml-service
```

## 💾 Backup & Restore

### Backup ML Models

```bash
# Models are in vigil-ml-layer/models/
tar -czf models-backup-$(date +%Y%m%d).tar.gz vigil-ml-layer/models/ vigil-ml-layer/artifacts/
```

### Restore Models

```bash
# Extract backup
tar -xzf models-backup-20231025.tar.gz
docker-compose restart ml-service
```

## 🚀 Production Deployment

### Environment-Specific Configs

```bash
# Use different compose files for different environments
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Resource Limits

Add to docker-compose.yml:

```yaml
services:
  intelligent-router:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 128M
```

## 📋 Complete Docker Command Reference

```bash
# Build
docker-compose build                    # Build all
docker-compose build <service>          # Build one

# Start
docker-compose up                       # Start (foreground)
docker-compose up -d                    # Start (background)
docker-compose up -d --build            # Build and start

# Stop
docker-compose stop                     # Stop (keep containers)
docker-compose down                     # Stop and remove containers
docker-compose down -v                  # Stop, remove containers and volumes

# Logs
docker-compose logs                     # All logs
docker-compose logs -f                  # Follow logs
docker-compose logs -f <service>        # Follow specific service

# Status
docker-compose ps                       # List containers
docker-compose top                      # Show running processes

# Execute
docker-compose exec <service> bash      # Enter container
docker-compose exec <service> <cmd>     # Run command

# Restart
docker-compose restart                  # Restart all
docker-compose restart <service>        # Restart one
```

## ✅ Pre-Flight Checklist

Before running `docker-compose up`:

- [ ] `.env` files created from `.env.example`
- [ ] API keys added to `.env` files
- [ ] Docker and Docker Compose installed
- [ ] Ports 8000, 8001, 8080 are available
- [ ] ML models trained (or will train in container)
- [ ] `.env` files are in `.gitignore`

## 🎯 Expected Results

After successful startup:

```bash
$ docker-compose ps
NAME                       STATUS         PORTS
vigil-data-collector       Up (healthy)   0.0.0.0:8000->8000/tcp
vigil-ml-service           Up (healthy)   0.0.0.0:8001->8001/tcp
vigil-intelligent-router   Up (healthy)   0.0.0.0:8080->8080/tcp

$ curl http://localhost:8080/health
{"status":"healthy","service":"vigil-intelligent-router","time":"2023-10-25T12:00:00Z"}
```

You're ready to send RPC requests! 🚀
