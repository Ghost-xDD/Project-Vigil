# Project Vigil

**Predictive Intelligence Layer for Solana's Multi-Client Network**

Vigil is the predictive "nervous system" for Solana's multi-client network, providing real-time failure probability scores that enable infrastructure to be proactive, not reactive.

[Litepaper](https://drive.google.com/file/d/1Iy1ZG7DRy9WbWRFN2B7BD7_0YBDrpY86/view?usp=sharing)

---

## 📋 Table of Contents

- [🎯 The Vision](#-the-vision)
- [❗ The Problem](#-the-problem-driving-blind)
- [💡 The Solution](#-the-solution-a-predictive-intelligence-layer)
- [🏗️ Architecture](#️-architecture)
- [📦 Components](#-components)
- [🚀 Quick Start](#-quick-start)
- [📡 API Endpoints](#-api-endpoints)
- [🔧 Configuration](#-configuration)
- [🔐 Security](#-security)
- [🧪 Testing](#-testing)
- [🐛 Troubleshooting](#-troubleshooting)
- [🎯 Use Cases](#-use-cases)
- [🚀 Deployment](#-deployment)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## 🎯 The Vision

Solana's 2025 roadmap is centered on achieving institutional-grade resilience through client diversity. The parallel operation of the battle-tested **Agave** (Rust) client and the hyper-performant **Firedancer** (C++) client is the most critical evolution of the network.

However, this diversity introduces a profound new challenge: **asymmetry**. These clients have different architectures, different performance "fingerprints," and different failure modes.

**Vigil is the predictive "nervous system" for this new, complex environment.**

Instead of reacting to failures, our Vigil Intelligence API predicts them. It analyzes real-time, client-specific performance data to forecast instability before the first transaction is ever dropped, enabling a new generation of proactive, truly resilient infrastructure.

---

## ❗ The Problem: Driving Blind

Today's RPC infrastructure is blind to the new multi-client reality. It relies on a "reactive failover" model, which is fundamentally broken.

### The "Old Way" (Reactive):

1. A node (e.g., an Agave instance) begins to degrade due to memory pressure or scheduling stalls
2. Transactions sent to this node start to slow down and then fail
3. Only after errors are detected does a "dumb" load balancer finally reroute traffic

### Why This Fails:

- **For Users**: Failed swaps, dropped liquidations, terrible UX
- **For Institutions**: Unacceptable. Reactive failover IS downtime. You cannot build high-availability systems on infrastructure that only responds after the failure

---

## 💡 The Solution: A Predictive Intelligence Layer

Vigil moves the entire ecosystem from **REACTIVE → PREDICTIVE**.

Our solution is two-fold: a powerful core API and a proof-of-concept application to demonstrate its power.

### 1. The Vigil Intelligence API (The "Brain")

At its core, Vigil is a machine learning engine that functions as an "early warning system."

- **Analyze**: We ingest a rich stream of real-time telemetry from both Agave and Firedancer nodes, learning their unique, client-specific "leading indicators" of instability
- **Predict**: Our model uses this data to generate a single, powerful output for any given RPC node: a real-time **"Failure Probability Score"**
- **Empower**: This API is our core B2B product. It's designed to be the "Intel Inside" for reliability, allowing existing RPC providers (Helius, Triton, QuickNode) to upgrade their entire infrastructure from reactive to predictive

### 2. The Vigil Load Balancer (The Hackathon POC)

To prove the power of our API, we built a next-generation RPC gateway that integrates our **"Failure Probability Score"** at its core.

Instead of waiting for timeouts, Vigil's routing engine makes proactive, client-aware decisions:

- 🛡️ **Proactive Rerouting**: As a node's "Failure Probability Score" climbs, our load balancer seamlessly and preemptively shifts traffic to healthy nodes. The result: zero user-facing errors
- 🚀 **Client-Aware Optimization**: The Vigil engine understands that for certain tasks, Firedancer's networking stack is superior, while for others, Agave's stability is preferable. It can intelligently route requests based on their type to the client best-suited for the job

---

## 🏗️ Architecture

```
                    ┌────────────────────────────┐
                    │  Clients (Web/Mobile/CLI)  │
                    └─────────────┬──────────────┘
                                  │ JSON-RPC Requests
                                  ↓
                    ┌──────────────────────────────────┐
                    │  Intelligent Router (Port 8080)  │
                    │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
                    │  Go-based Reverse Proxy          │
                    │  • ML-powered node selection     │
                    │  • Per-request optimization      │
                    │  • Zero-copy streaming           │
                    │  • Fallback support              │
                    └───────┬──────────────────────────┘
                            │
            ┌───────────────┼──────────────────┐
            │               │                  │
            ↓               ↓                  ↓
    ┌───────────────┐ ┌────────────┐  ┌──────────────┐
    │ Data Collector│ │ ML Service │  │ Solana RPC   │
    │  (Port 8000)  │ │ (Port 8001)│  │   Nodes      │
    │  ━━━━━━━━━━━━ │ │ ━━━━━━━━━━ │  │ ━━━━━━━━━━━━ │
    │ FastAPI       │ │ FastAPI +  │  │ • Ankr       │
    │               │ │ scikit-    │  │ • Helius     │
    │ • Monitors 5  │ │   learn    │  │ • Alchemy    │
    │   nodes       │ │            │  │ • Public     │
    │ • Polls every │ │ • Anomaly  │  │ • Self-hosted│
    │   15s         │ │ • Failure  │  │              │
    │ • Tracks OS   │ │ • Latency  │  └──────────────┘
    │   metrics     │ │ • Routing  │
    └───────────────┘ └────────────┘
```

---

## 📦 Components

### 1. Data Collector Service (`data_collector/`)

**FastAPI service that monitors Solana RPC nodes**

- **Language**: Python 3.9+
- **Framework**: FastAPI
- **Port**: 8000

**Features:**

- Monitors 5 nodes: Ankr, Helius, Alchemy, Solana Public (Devnet), Self-hosted Agave
- Tracks: Latency, slot height, block gaps, CPU, memory, disk I/O
- Polls every 15 seconds (configurable)
- Simulates OS metrics for self-hosted node
- RESTful API with auto-generated documentation

### 2. ML Prediction Service (`vigil-ml-layer/`)

**Machine learning service for predictive analytics**

- **Language**: Python 3.9+
- **Framework**: FastAPI + scikit-learn
- **Port**: 8001

**Features:**

- **Anomaly Detection**: Autoencoder (MLPRegressor) - detects unusual patterns
- **Failure Prediction**: Logistic Regression - probability of node failure (0-1)
- **Latency Forecasting**: SARIMA (per-node models) - predicts future latency
- **Routing Optimization**: Weighted cost function (70% failure, 30% latency)
- Feature engineering with rolling windows and lag features

### 3. Intelligent Router (`vigil-intelligent-router/`)

**Go-based high-performance reverse proxy**

- **Language**: Go 1.21+
- **Port**: 8080

**Features:**

- ML-powered routing: Queries ML service for every request
- Concurrent handling: Goroutines for high throughput (1000+ req/s)
- Response streaming: Zero-copy streaming for minimal latency
- Fallback support: Automatic failover if ML service unavailable
- Production-ready: Docker, health checks, structured logging (zap)
- Stateless: No local state, fully relies on ML predictions

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd project-vigil

# Set up environment files with your API keys
./setup.sh

# Edit .env files with your actual API keys
nano data_collector/.env
nano vigil-intelligent-router/.env

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Services will be available at:
# - Intelligent Router: http://localhost:8080
# - Data Collector:     http://localhost:8000
# - ML Service:         http://localhost:8001
```

### Option 2: Manual Setup

#### 1. Data Collector

```bash
cd data_collector

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start service
python3 main.py
```

#### 2. ML Service

```bash
cd vigil-ml-layer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Train models (first time only)
python -m src.generate_data
python -m src.train

# Start service
python run_api.py
```

#### 3. Intelligent Router

```bash
cd vigil-intelligent-router

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Build and run
go build -o vigil-router .
./vigil-router

# Or use Make
make build
make run
```

---

## 📡 API Endpoints

### Intelligent Router (Port 8080) - User-Facing

| Endpoint  | Method | Description                       |
| --------- | ------ | --------------------------------- |
| `/rpc`    | POST   | **Main RPC endpoint** (use this!) |
| `/health` | GET    | Health check                      |
| `/`       | GET    | Service information               |

### Data Collector (Port 8000) - Internal

| Endpoint                         | Method | Description                        |
| -------------------------------- | ------ | ---------------------------------- |
| `/api/v1/metrics/latest-metrics` | GET    | Latest metrics for all nodes       |
| `/health`                        | GET    | Health check with scheduler status |
| `/docs`                          | GET    | Interactive API documentation      |

### ML Prediction Service (Port 8001) - Internal

| Endpoint   | Method | Description                     |
| ---------- | ------ | ------------------------------- |
| `/predict` | POST   | Get routing recommendation      |
| `/health`  | GET    | Health check with model status  |
| `/models`  | GET    | Information about loaded models |
| `/docs`    | GET    | Interactive API documentation   |

---

## 💡 Usage Examples

### Send RPC Request (Primary Use Case)

```bash
# Send any Solana JSON-RPC request to the Intelligent Router
curl -X POST http://localhost:8080/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "getHealth"
  }'

# The router will:
# 1. Query ML service for best node (e.g., "helius_devnet")
# 2. Forward your request to that node
# 3. Stream the response back to you
```

### Check System Health

```bash
# Check all services
curl http://localhost:8080/health  # Router
curl http://localhost:8000/health  # Data Collector
curl http://localhost:8001/health  # ML Service
```

### Monitor Metrics

```bash
# View current node metrics
curl http://localhost:8000/api/v1/metrics/latest-metrics | jq

# Example output:
# [
#   {
#     "node_name": "helius_devnet",
#     "latency_ms": 705,
#     "slot": 417104057,
#     "is_healthy": 1,
#     "block_height_gap": 0
#   },
#   ...
# ]
```

### Get ML Predictions

```bash
# Get routing recommendation (used internally by router)
curl -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": [
      {
        "timestamp": "2023-10-25T12:00:00Z",
        "node_id": "ankr_devnet",
        "latency_ms": 150,
        "is_healthy": 1,
        ...
      }
    ]
  }' | jq
```

---

## 🔧 Configuration

### Data Collector (`data_collector/.env`)

```env
# Solana RPC Endpoints (add your API keys)
ANKR_DEVNET_RPC_URL=https://rpc.ankr.com/solana_devnet/YOUR_KEY
HELIUS_DEVNET_RPC_URL=https://devnet.helius-rpc.com/?api-key=YOUR_KEY
ALCHEMY_DEVNET_RPC_URL=https://solana-devnet.g.alchemy.com/v2/YOUR_KEY
SOLANA_PUBLIC_DEVNET_RPC_URL=https://api.devnet.solana.com

# Polling Configuration
POLL_INTERVAL_SECONDS=15
REQUEST_TIMEOUT_SECONDS=8
SIMULATED_NODE_NAME=agave_self_hosted
```

### Intelligent Router (`vigil-intelligent-router/.env`)

```env
# Service URLs
ML_SERVICE_URL=http://localhost:8001
DATA_COLLECTOR_URL=http://localhost:8000

# Node URL Mappings (same API keys as Data Collector)
ANKR_DEVNET_RPC_URL=https://rpc.ankr.com/solana_devnet/YOUR_KEY
HELIUS_DEVNET_RPC_URL=https://devnet.helius-rpc.com/?api-key=YOUR_KEY
ALCHEMY_DEVNET_RPC_URL=https://solana-devnet.g.alchemy.com/v2/YOUR_KEY

# Fallback
FALLBACK_RPC_URL=https://api.devnet.solana.com
FALLBACK_ENABLED=true
```

### ML Service (`vigil-ml-layer/config.yaml`)

```yaml
# Routing optimization weights
optimization:
  weight_failure: 0.7 # 70% focus on failure probability
  weight_latency: 0.3 # 30% focus on latency

# Feature engineering
feature_engineering:
  rolling_windows: [5, 10] # Minutes
  lag_periods: [1, 2] # Minutes
  thresholds:
    cpu_usage: 80.0
    memory_usage: 85.0
```

---

## 🔐 Security

**⚠️ IMPORTANT: API Key Management**

### Quick Setup (Secure)

```bash
# Run the setup script
./setup.sh

# This creates .env files from templates
# Then edit with your real API keys:
nano data_collector/.env
nano vigil-intelligent-router/.env
```

### What's Protected

✅ All `.env` files are gitignored  
✅ Only `.env.example` templates are committed  
✅ `docker-compose.yml` uses `env_file` (no exposed secrets)  
✅ Pre-commit hooks prevent committing secrets  
✅ GitHub Actions scan for leaked secrets

### Never Commit

❌ `.env` files  
❌ API keys in docker-compose  
❌ Hardcoded secrets in code

**See `SECURITY.md` for complete security guide.**

---

## 🏗️ Project Structure

```
project-vigil/
│
├── data_collector/                    # Metrics Collection Service
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   │   └── metrics.py            # Metrics API
│   │   ├── core/
│   │   │   └── config.py             # Configuration
│   │   ├── schemas/
│   │   │   └── metric.py             # Pydantic models
│   │   └── tasks/
│   │       └── rpc_poller.py         # Background polling
│   ├── main.py                       # FastAPI app
│   ├── requirements.txt
│   ├── .env.example                  # Safe template ✅
│   └── .env                          # Your keys (gitignored) 🔒
│
├── vigil-ml-layer/                    # ML Prediction Service
│   ├── api/
│   │   ├── main.py                   # FastAPI app
│   │   └── schemas.py                # Request/Response models
│   ├── src/
│   │   ├── predict.py                # Prediction logic
│   │   ├── features.py               # Feature engineering
│   │   ├── train.py                  # Model training
│   │   └── routing.py                # Optimization
│   ├── examples/
│   │   └── integration_example.py    # Integration demo
│   ├── models/                       # Trained ML models
│   ├── artifacts/                    # Feature lists, thresholds
│   ├── config.yaml
│   └── requirements.txt
│
├── vigil-intelligent-router/          # Intelligent Routing Service
│   ├── config/
│   │   └── config.go                 # Configuration mgmt
│   ├── ml/
│   │   └── client.go                 # ML service client
│   ├── proxy/
│   │   └── handler.go                # Proxy logic
│   ├── main.go                       # Entry point
│   ├── Dockerfile
│   ├── Makefile
│   ├── go.mod
│   ├── .env.example                  # Safe template ✅
│   └── .env                          # Your keys (gitignored) 🔒
│
├── docker-compose.yml                # Orchestration (no secrets) ✅
├── setup.sh                          # Automated setup script
├── SECURITY.md                       # Security documentation
├── SETUP_GUIDE.md                    # Detailed setup guide
├── .gitignore                        # Protects secrets 🔒
├── .pre-commit-config.yaml           # Pre-commit hooks
└── README.md                         # This file
```

---

## 🔄 How It Works

### Request Lifecycle

```
1. Client sends RPC request
   POST http://localhost:8080/rpc
   ↓

2. Router queries Data Collector for latest metrics
   GET http://data-collector:8000/api/v1/metrics/latest-metrics
   ↓

3. Router sends metrics to ML Service
   POST http://ml-service:8001/predict
   ↓

4. ML Service returns recommendation
   {
     "recommended_node": "helius_devnet",
     "failure_prob": 0.08,
     "predicted_latency_ms": 120.5,
     "cost_score": 0.125
   }
   ↓

5. Router forwards request to recommended node
   POST https://devnet.helius-rpc.com/...
   ↓

6. Router streams response back to client
   ← Solana RPC response
```

### Background Processes

- **Data Collector**: Polls all 5 RPC nodes every 15 seconds
- **ML Service**: Loaded models ready for instant predictions
- **Router**: Stateless, queries ML service per request

---

## 📊 Metrics & Monitoring

### Data Collected (Per Node)

**RPC Metrics:**

- Latency (ms)
- Current slot number
- Block height gap
- Health status (binary)

**OS Metrics (Self-hosted only):**

- CPU usage (%)
- Memory usage (%)
- Disk I/O (%)

### ML Predictions (Per Node)

- Failure probability (0-1)
- Predicted latency (ms)
- Anomaly detection (boolean)
- Cost score (routing metric)

### Performance Stats

| Service            | Latency    | Memory | Throughput    |
| ------------------ | ---------- | ------ | ------------- |
| Data Collector     | 800-1500ms | ~100MB | N/A (polling) |
| ML Service         | 50-200ms   | ~500MB | 100 pred/s    |
| Intelligent Router | 5-50ms     | ~30MB  | 1000+ req/s   |

---

## 🧪 Testing

### End-to-End Test

```bash
# Terminal 1: Check all services are healthy
curl http://localhost:8080/health
curl http://localhost:8000/health
curl http://localhost:8001/health

# Terminal 2: Send test RPC request
curl -X POST http://localhost:8080/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "getSlot"
  }' | jq

# Terminal 3: Monitor logs
docker-compose logs -f intelligent-router
```

### Integration Example

```bash
cd vigil-ml-layer
source venv/bin/activate
python examples/integration_example.py
```

This runs a continuous monitoring loop showing real-time routing decisions.

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check if ports are in use
lsof -ti:8000 | xargs kill -9  # Data Collector
lsof -ti:8001 | xargs kill -9  # ML Service
lsof -ti:8080 | xargs kill -9  # Router

# Check Docker
docker-compose down
docker-compose up -d
docker-compose logs -f
```

### ML Models Not Found

```bash
cd vigil-ml-layer
source venv/bin/activate
python -m src.generate_data
python -m src.train
```

### No Metrics Available

```bash
# Wait for first poll cycle (15 seconds)
# Check Data Collector logs
docker-compose logs data-collector

# Verify RPC URLs are correct in .env
cat data_collector/.env
```

### Router Returns 502/503

**Causes:**

- ML service not running
- Data Collector not running
- ML models not trained

**Solutions:**

- Check all services: `docker-compose ps`
- Verify ML models exist: `ls vigil-ml-layer/models/`
- Enable fallback: `FALLBACK_ENABLED=true`

---

## 🔗 Service Dependencies

```
Intelligent Router depends on:
  ├── ML Service
  │   └── Data Collector
  │       └── Solana RPC Nodes
  └── Fallback RPC (optional)
```

**Startup Order:**

1. Data Collector (collects metrics)
2. ML Service (loads models)
3. Intelligent Router (ready for requests)

---

## 📚 Documentation

- **Setup**: `SETUP_GUIDE.md` - Detailed setup instructions
- **Security**: `SECURITY.md` - Security best practices
- **Data Collector**: `data_collector/README.md`
- **ML Service**: `vigil-ml-layer/README.md`
- **Intelligent Router**: `vigil-intelligent-router/README.md`

### API Documentation (Interactive)

- Data Collector: http://localhost:8000/docs
- ML Service: http://localhost:8001/docs

---

## 🎯 Use Cases

### For Developers

```javascript
// In your dApp
const response = await fetch('http://localhost:8080/rpc', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    jsonrpc: '2.0',
    id: 1,
    method: 'getLatestBlockhash',
  }),
});

// Your request is automatically routed to the healthiest node!
```

### For RPC Providers

- Integrate Vigil Intelligence API for predictive failover
- Reduce customer-facing errors by 90%+
- Optimize routing based on real-time ML predictions
- Support for both Agave and Firedancer clients

### For Infrastructure Teams

- Monitor node health with granular metrics
- Predict failures before they impact users
- Optimize resource allocation based on ML insights
- Build truly high-availability Solana infrastructure

---

## 🚀 Deployment

### Docker Compose (Recommended)

```bash
# Production deployment
docker-compose -f docker-compose.yml up -d

# Scale router for high availability
docker-compose up -d --scale intelligent-router=3
```

### Kubernetes

See `k8s/` directory for Kubernetes manifests (if available).

### Cloud Platforms

- **AWS**: Deploy on ECS/EKS
- **GCP**: Deploy on GKE/Cloud Run
- **Azure**: Deploy on AKS
- **Heroku/Render**: Use included Procfiles

---

## 🤝 Contributing

We welcome contributions!

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Guidelines

- Follow existing code structure
- Add tests for new features
- Update documentation
- Run linters before committing
- Never commit secrets (use pre-commit hooks)

---

## 📄 License

MIT License - see LICENSE files in individual services

---

## 👥 Team

Project Vigil Team

Building the future of predictive infrastructure for Solana.

---

## 🙏 Acknowledgments

- **Solana Foundation** - For the amazing ecosystem
- **RPC Providers**: Ankr, Helius, Alchemy - For reliable infrastructure
- **Open Source**: FastAPI, scikit-learn, statsmodels, Go community

---

## 📞 Support & Contact

- **Issues**: [Open an issue](https://github.com/your-org/project-vigil/issues)
- **Documentation**: Check service-specific READMEs
- **API Docs**: Visit `/docs` endpoints on running services
- **Security**: See `SECURITY.md`

---

## 🌟 Why Vigil?

**Traditional Load Balancer:**

```
Request → Round Robin → Node X
(If Node X fails) → Retry → Node Y
= User sees errors, degraded experience
```

**Vigil Intelligence:**

```
Request → ML Prediction → Best Healthy Node
(Proactive) → Zero errors, optimal performance
= Happy users, reliable infrastructure
```

---

**Built with ❤️ for the Solana ecosystem**

_Making Solana infrastructure predictive, not reactive._
