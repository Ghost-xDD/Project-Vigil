# Project Vigil: A Predictive Intelligence Layer for Solana's Multi-Client Future

Intelligent monitoring and routing system for Solana RPC nodes with ML-powered failure prediction and optimization.

## 🎯 Overview

At its core, Vigil is a machine learning engine that functions as a predictive nervous system for Solana's infrastructure. It moves beyond simple uptime checks to analyze a rich stream of real-time performance data from both Agave and Firedancer nodes. 

By learning the subtle, client-specific leading indicators of instability—such as memory pressure patterns, scheduling stalls, or RPC latency variance—our service can forecast node degradation and failure before it happens.

### Architecture

```
┌─────────────────────┐         ┌──────────────────────┐
│  Data Collector     │────────▶│   ML Prediction      │
│  Service            │         │   Service            │
│  (Port 8000)        │         │   (Port 8001)        │
│                     │         │                      │
│  • RPC Polling      │         │  • Anomaly Detection │
│  • Metrics Storage  │         │  • Failure Prediction│
│  • Health Tracking  │         │  • Latency Forecast  │
│  • OS Simulation    │         │  • Route Optimization│
└─────────────────────┘         └──────────────────────┘
         ↓                               ↓
    Real-time Metrics             Routing Decision
```

## 📦 Components

### 1. Data Collector Service (`data_collector/`)

FastAPI service that monitors Solana RPC nodes:

- **Real RPC Nodes**: Ankr, Helius, Alchemy, Solana Public (Devnet)
- **Simulated Node**: Self-hosted Agave with OS metrics
- **Metrics Tracked**: Latency, slot height, block gaps, CPU, memory, disk I/O
- **Polling Frequency**: Every 15 seconds (configurable)

### 2. ML Prediction Service (`vigil-ml-layer/`)

Machine learning service for predictive analytics:

- **Anomaly Detection**: Autoencoder (MLPRegressor)
- **Failure Prediction**: Logistic Regression
- **Latency Forecasting**: SARIMA (per-node models)
- **Routing Optimization**: Weighted cost function (70% failure, 30% latency)

### 3. Intelligent Router (`vigil-intelligent-router/`)

Go-based high-performance reverse proxy:

- **ML-Powered Routing**: Real-time node selection per request
- **Concurrent Handling**: Goroutines for high throughput
- **Response Streaming**: Zero-copy streaming for minimal latency
- **Fallback Support**: Automatic failover to public RPC
- **Production Ready**: Docker, health checks, structured logging

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- pip
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/project-vigil.git
cd project-vigil
```

### 2. Set Up Data Collector

```bash
cd data_collector

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (copy .env.example to .env if needed)
cp .env.example .env

# Start the service
python3 main.py
```

The Data Collector will be available at: **http://localhost:8000**

### 3. Set Up ML Service

```bash
cd ../vigil-ml-layer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Generate training data and train models (first time only)
python -m src.generate_data
python -m src.train

# Start the ML service
python run_api.py
```

The ML Service will be available at: **http://localhost:8001**

### 4. Test the Integration

```bash
# In a new terminal
cd vigil-ml-layer
source venv/bin/activate
python examples/integration_example.py
```

## 📊 API Endpoints

### Data Collector (Port 8000)

| Endpoint                         | Method | Description                        |
| -------------------------------- | ------ | ---------------------------------- |
| `/`                              | GET    | Service information                |
| `/health`                        | GET    | Health check with scheduler status |
| `/api/v1/metrics/latest-metrics` | GET    | Latest metrics for all nodes       |
| `/docs`                          | GET    | Interactive API documentation      |

### ML Prediction Service (Port 8001)

| Endpoint   | Method | Description                     |
| ---------- | ------ | ------------------------------- |
| `/`        | GET    | Service information             |
| `/health`  | GET    | Health check with model status  |
| `/predict` | POST   | Get routing recommendation      |
| `/models`  | GET    | Information about loaded models |
| `/docs`    | GET    | Interactive API documentation   |

## 🔧 Configuration

### Data Collector (`data_collector/.env`)

```env
# Solana RPC Endpoints
ANKR_DEVNET_RPC_URL=https://rpc.ankr.com/solana_devnet/YOUR_KEY
HELIUS_DEVNET_RPC_URL=https://devnet.helius-rpc.com/?api-key=YOUR_KEY
ALCHEMY_DEVNET_RPC_URL=https://solana-devnet.g.alchemy.com/v2/YOUR_KEY
SOLANA_PUBLIC_DEVNET_RPC_URL=https://api.devnet.solana.com

# Polling Configuration
POLL_INTERVAL_SECONDS=15
REQUEST_TIMEOUT_SECONDS=8

# Simulated Node
SIMULATED_NODE_NAME=agave_self_hosted
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

## 📈 Example Usage

### Python Integration

```python
import requests

# 1. Get metrics from Data Collector
metrics_response = requests.get("http://localhost:8000/api/v1/metrics/latest-metrics")
metrics = metrics_response.json()

# 2. Send to ML Service for prediction
prediction_response = requests.post(
    "http://localhost:8001/predict",
    json={"metrics": metrics}
)
recommendation = prediction_response.json()

# 3. Use the recommendation
best_node = recommendation['recommended_node']
print(f"Route traffic to: {best_node}")
```

### cURL Examples

**Get latest metrics:**

```bash
curl http://localhost:8000/api/v1/metrics/latest-metrics | jq
```

**Get routing recommendation:**

```bash
curl -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d @metrics.json | jq
```

## 🧪 Testing

### Data Collector

```bash
cd data_collector
pytest tests/  # (if tests exist)
```

### ML Service

```bash
cd vigil-ml-layer
pytest tests/
```

## 📚 Documentation

- **Data Collector**: See `data_collector/README.md`
- **ML Service**: See `vigil-ml-layer/README.md`
- **API Docs**:
  - Data Collector: http://localhost:8000/docs
  - ML Service: http://localhost:8001/docs

## 🏗️ Development

### Project Structure

```
project-vigil/
├── data_collector/           # RPC monitoring service
│   ├── app/
│   │   ├── api/             # API endpoints
│   │   ├── core/            # Configuration
│   │   ├── schemas/         # Data models
│   │   └── tasks/           # Background jobs
│   ├── main.py              # Entry point
│   └── requirements.txt
│
├── vigil-ml-layer/          # ML prediction service
│   ├── api/                 # FastAPI application
│   ├── src/                 # ML logic
│   ├── models/              # Trained models
│   ├── config.yaml
│   └── requirements.txt
│
└── README.md                # This file
```

### Adding New RPC Endpoints

Edit `data_collector/.env`:

```env
NEW_PROVIDER_DEVNET_RPC_URL=https://your-provider.com/api-key
```

Update `data_collector/app/core/config.py` to include the new provider in `NODE_URLS`.

### Retraining ML Models

```bash
cd vigil-ml-layer
python -m src.generate_data  # Generate new training data
python -m src.train          # Retrain models
```

## 🐛 Troubleshooting

### Data Collector Issues

**Port already in use:**

```bash
lsof -ti:8000 | xargs kill -9
```

**Metrics not updating:**

- Check RPC endpoint URLs in `.env`
- Verify internet connectivity
- Check logs for errors

### ML Service Issues

**Models not found:**

```bash
cd vigil-ml-layer
python -m src.train  # Train models first
```

**Prediction errors:**

- Ensure at least 10-15 data points per node
- Check that required fields are present in metrics
- Review logs in `logs/sentry_ml.log`

## 🔐 Production Considerations

1. **Security**:

   - Add API authentication (API keys/JWT)
   - Use HTTPS/TLS
   - Implement rate limiting
   - Secure RPC API keys

2. **Scalability**:

   - Deploy services in containers (Docker)
   - Use Redis for caching
   - Implement load balancing
   - Set up horizontal scaling

3. **Monitoring**:

   - Add Prometheus metrics
   - Set up Grafana dashboards
   - Configure alerting (PagerDuty, etc.)
   - Implement distributed tracing

4. **Reliability**:
   - Set up health checks
   - Implement circuit breakers
   - Add retry logic
   - Configure backup RPC endpoints

## 📊 Performance Metrics

- **Data Collector**:

  - Polling latency: ~800-1500ms per node
  - Memory usage: ~100MB
  - CPU usage: <5%

- **ML Service**:
  - Prediction latency: ~50-200ms
  - Memory usage: ~500MB (with models)
  - Throughput: ~100 predictions/second

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

MIT License - see LICENSE files in individual services

## 👥 Authors

Project Vigil Team

## 🙏 Acknowledgments

- Solana Foundation
- RPC providers: Ankr, Helius, Alchemy
- FastAPI and Pydantic teams
- scikit-learn and statsmodels communities

## 📞 Support

- **Issues**: Open an issue on GitHub
- **Documentation**: Check service-specific READMEs
- **API Docs**: Visit `/docs` endpoints on running services

---

Built with ❤️ for the Solana ecosystem
