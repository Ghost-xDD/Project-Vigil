# Vigil ML Prediction Service

ML-powered prediction and routing optimization service for Solana RPC nodes in Project Vigil.

## 🎯 Features

- **Anomaly Detection**: Autoencoder-based detection of unusual node behavior
- **Failure Prediction**: Logistic regression for failure probability estimation
- **Latency Forecasting**: SARIMA models for per-node latency prediction
- **Routing Optimization**: Weighted cost function for optimal node selection
- **FastAPI Integration**: RESTful API for real-time predictions

## 🏗️ Architecture

```
Data Collector → Metrics → Feature Engineering → ML Models → Routing Decision
                    ↓            ↓                   ↓              ↓
              (Real-time)   (Rolling/Lag)      (Predictions)  (Best Node)
```

### Models

1. **Anomaly Detector**: MLPRegressor (Autoencoder architecture)

   - Encoder → Bottleneck → Decoder
   - Detects deviations from normal behavior patterns

2. **Failure Classifier**: LogisticRegression

   - Predicts probability of node failure (0-1)
   - Uses balanced class weights for handling imbalanced data

3. **Latency Forecaster**: SARIMA (per-node models)

   - Time-series forecasting with seasonal components
   - Trained individually for each node's characteristics

4. **Routing Optimizer**: Weighted cost function
   - Cost = 0.7 × failure_prob + 0.3 × normalized_latency
   - Selects node with minimum cost score

## 📦 Installation

### 1. Clone the Repository

```bash
cd vigil-ml-layer
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Configuration

```bash
cat config.yaml
```

## 🚀 Usage

### Training Models (Required First Time)

Before running the API, you need to train the models:

```bash
# Generate synthetic training data
python -m src.generate_data

# Train all models
python -m src.train

# Verify models are created
ls -la models/ artifacts/
```

### Running the API

#### Option 1: Using the startup script (Recommended)

```bash
python run_api.py
```

#### Option 2: Direct uvicorn

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

### API Endpoints

Once running, the API is available at: **http://localhost:8001**

#### **GET /** - Service Information

```bash
curl http://localhost:8001/
```

#### **GET /health** - Health Check

```bash
curl http://localhost:8001/health
```

Response:

```json
{
  "status": "healthy",
  "models_loaded": true,
  "available_models": ["anomaly", "failure", "latency"],
  "version": "1.0.0"
}
```

#### **GET /models** - Model Information

```bash
curl http://localhost:8001/models
```

#### **POST /predict** - Get Routing Recommendation

Request body requires at least 10-15 historical data points per node:

```bash
curl -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": [
      {
        "timestamp": "2023-10-25T12:00:00Z",
        "node_id": "ankr_devnet",
        "cpu_usage": 75.5,
        "memory_usage": 68.2,
        "disk_io": 25.3,
        "latency_ms": 150.5,
        "block_height_gap": 2,
        "is_healthy": 1
      },
      ...more data points...
    ]
  }'
```

Response:

```json
{
  "recommended_node": "helius_devnet",
  "explanation": "Recommending helius_devnet (Cost: 0.125) due to low failure prob (0.08) and low latency (120.5ms).",
  "timestamp": "2023-10-25T12:00:00Z",
  "all_predictions": [
    {
      "node_id": "helius_devnet",
      "failure_prob": 0.08,
      "predicted_latency_ms": 120.5,
      "anomaly_detected": false,
      "cost_score": 0.125
    }
  ],
  "recommendation_details": {
    "node_id": "helius_devnet",
    "failure_prob": 0.08,
    "predicted_latency_ms": 120.5,
    "anomaly_detected": false,
    "cost_score": 0.125
  }
}
```

### Interactive API Documentation

Visit these URLs after starting the API:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## 🔧 Configuration

Edit `config.yaml` to customize:

```yaml
# Model weights for routing optimization
optimization:
  weight_failure: 0.7 # 70% importance on failure probability
  weight_latency: 0.3 # 30% importance on latency

# Feature engineering parameters
feature_engineering:
  rolling_windows: [5, 10] # Minutes
  lag_periods: [1, 2] # Minutes
  thresholds:
    cpu_usage: 80.0
    memory_usage: 85.0
    error_rate: 10.0
```

## 🔗 Integration with Data Collector

The ML Service consumes metrics from the Data Collector Service:

### Data Flow:

```
Data Collector (Port 8000) → ML Service (Port 8001)
        ↓                              ↓
  Latest Metrics              Predictions + Routing
```

### Integration Example:

```python
import requests
import httpx

# Get metrics from Data Collector
collector_url = "http://localhost:8000/api/v1/metrics/latest-metrics"
response = requests.get(collector_url)
metrics = response.json()

# Send to ML Service for prediction
ml_url = "http://localhost:8001/predict"
prediction = requests.post(ml_url, json={"metrics": metrics})
recommendation = prediction.json()

print(f"Route to: {recommendation['recommended_node']}")
```

## 📊 Feature Engineering

The service automatically engineers features from raw metrics:

### Base Metrics (Required):

- `cpu_usage` (%)
- `memory_usage` (%)
- `disk_io` (%)
- `latency_ms`
- `block_height_gap`
- `is_healthy` (0 or 1)

### Engineered Features:

- **Rolling Statistics**: Mean, std, min, max over 5 and 10 minute windows
- **Lag Features**: Previous 1 and 2 minute values
- **Threshold Flags**: Binary indicators when metrics exceed thresholds
- **Interaction Features**: Products of related metrics (e.g., cpu × error_rate)

## 🧪 Testing

### Run Tests

```bash
pytest tests/
```

### Test Prediction Manually

```bash
python test_predictor_usage.py
```

## 📝 Development

### Project Structure

```
vigil-ml-layer/
├── api/
│   ├── main.py           # FastAPI application
│   └── schemas.py        # Pydantic models
├── src/
│   ├── features.py       # Feature engineering
│   ├── train.py          # Model training
│   ├── predict.py        # Prediction logic
│   └── routing.py        # Optimization
├── models/               # Trained models (generated)
├── artifacts/            # Feature lists, thresholds (generated)
├── data/                 # Training data (generated)
├── config.yaml           # Configuration
└── run_api.py           # Startup script
```

### Adding New Features

1. Edit `config.yaml` to add new interaction pairs or thresholds
2. Retrain models: `python -m src.train`
3. Restart API: `python run_api.py`

## 🐛 Troubleshooting

### Models Not Found Error

```
Error: Models not loaded
```

**Solution**: Train models first with `python -m src.train`

### Insufficient Data Points

```
Error: No valid engineered features generated
```

**Solution**: Ensure you send at least 10-15 historical data points per node

### Feature Mismatch Error

```
KeyError: 'cpu_usage_rolling_mean_5'
```

**Solution**: Retrain models with current config: `python -m src.train`

## 📈 Performance

- **Prediction Latency**: ~50-200ms for 5 nodes
- **Memory Usage**: ~500MB (includes loaded models)
- **Throughput**: ~100 predictions/second

## 🔐 Production Considerations

1. **CORS**: Update `allow_origins` in `api/main.py` for production
2. **Authentication**: Add API key/JWT authentication
3. **Rate Limiting**: Implement rate limiting middleware
4. **Model Updates**: Set up automated retraining pipeline
5. **Monitoring**: Add Prometheus metrics and logging

## 📄 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/xyz`
3. Commit changes with descriptive messages
4. Run tests: `pytest tests/`
5. Submit pull request

## 📞 Support

For issues or questions:

- Check logs in `logs/sentry_ml.log`
- Review configuration in `config.yaml`
- Consult API documentation at `/docs`

## 🔗 Related Services

- **Data Collector Service** (Port 8000): Collects RPC node metrics
- **ML Prediction Service** (Port 8001): This service
- **Routing Service** (Future): Implements routing based on ML recommendations
