# Vigil MACHINE LEARNING CORE 

ML Prediction Service for Project Sentinel: Predictive failure and performance forecasting for Solana RPC nodes.

## Installation
1. Clone the repo: `git clone https://github.com/your-org/sentry-predict.git`
2. Install Requirements: `pip install -r requirements.txt`

## Usage
- Generate data: `generate-data`
- Train models: `train-sentry`
- Run API: `uvicorn api.main:app --reload`

## Testing
`pytest tests/`

## Contributing
1. Fork the repo
2. Create branch: `git checkout -b feature/xyz`
3. Commit with pre-commit
4. PR

## Architecture
- Data generation with AR(1) for time-series realism
- Feature engineering for trends/lags
- Models: Autoencoder (anomaly), LogisticRegression (failure), SARIMA (forecasting)
- API for predictions

## License
MIT