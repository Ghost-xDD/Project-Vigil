import logging
from datetime import datetime
from typing import List, Dict
import pandas as pd
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.schemas import (
    MetricsBatch,
    RoutingRecommendation,
    HealthStatus,
    ErrorResponse,
    NodePrediction
)
from src.predict import SentryPredictor
from src.features import engineer_features
from src.utils import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global predictor instance
predictor: SentryPredictor = None
config: Dict = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    global predictor, config
    logger.info("=" * 60)
    logger.info("Starting Vigil ML Prediction Service")
    logger.info("=" * 60)
    
    try:
        # Load configuration
        config = load_config('config.yaml')
        logger.info("Configuration loaded successfully")
        
        # Initialize predictor (loads all models)
        predictor = SentryPredictor(config_path='config.yaml')
        logger.info("ML models loaded successfully")
        logger.info(f"Available models: {list(predictor.models.keys())}")
        logger.info(f"Latency models for nodes: {list(predictor.models.get('latency', {}).keys())}")
        
    except Exception as e:
        logger.error(f"FATAL: Failed to initialize service: {e}", exc_info=True)
        raise
    
    logger.info("Service ready to accept requests")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Vigil ML Prediction Service")


# Initialize FastAPI app
app = FastAPI(
    title="Vigil ML Prediction Service",
    version="1.0.0",
    description="Machine Learning prediction service for Solana RPC node routing optimization",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """Root endpoint - Service information"""
    return {
        "service": "Vigil ML Prediction Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthStatus, status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint"""
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Models not loaded"
        )
    
    return HealthStatus(
        status="healthy",
        models_loaded=True,
        available_models=list(predictor.models.keys()),
        version="1.0.0"
    )


@app.post("/predict", response_model=RoutingRecommendation, status_code=status.HTTP_200_OK)
async def predict_routing(batch: MetricsBatch):
    """
    Predict optimal node routing based on historical metrics.
    
    Requires at least 10-15 data points per node for accurate predictions
    (needed for rolling window features).
    
    Args:
        batch: MetricsBatch containing historical metrics for all nodes
        
    Returns:
        RoutingRecommendation with the best node to route to and explanations
    """
    try:
        if predictor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Models not initialized"
            )
        
        # Validate input
        if not batch.metrics:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No metrics provided"
            )
        
        # Convert metrics to DataFrame
        metrics_data = [metric.model_dump() for metric in batch.metrics]
        raw_df = pd.DataFrame(metrics_data)
        
        # Add required columns if missing
        if 'client_type' not in raw_df.columns:
            # Infer client type from node_id (e.g., "agave_self_hosted" -> "agave")
            raw_df['client_type'] = raw_df['node_id'].apply(
                lambda x: x.split('_')[0] if '_' in x else 'unknown'
            )
        
        if 'error_rate' not in raw_df.columns:
            # Calculate error_rate from is_healthy (inverse: 1 - is_healthy = error)
            raw_df['error_rate'] = (1 - raw_df['is_healthy']) * 100.0
        
        # Check minimum data points per node
        node_counts = raw_df['node_id'].value_counts()
        min_required = config.get('prediction_history_size', 15)
        
        insufficient_nodes = node_counts[node_counts < min_required].index.tolist()
        if insufficient_nodes:
            logger.warning(
                f"Nodes with insufficient data (<{min_required} points): {insufficient_nodes}"
            )
        
        # Engineer features
        logger.info(f"Engineering features for {len(raw_df)} data points...")
        engineered_df = engineer_features(raw_df, config)
        
        # Extract last row for each node (most recent engineered features)
        live_feature_map = {}
        unique_nodes = engineered_df['node_id'].unique()
        
        for node in unique_nodes:
            node_data = engineered_df[engineered_df['node_id'] == node]
            if len(node_data) > 0:
                live_feature_map[node] = node_data.iloc[-1]
        
        if not live_feature_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid engineered features generated"
            )
        
        # Get recommendation from predictor
        logger.info(f"Generating predictions for {len(live_feature_map)} nodes...")
        recommended_node, explanation, rec_details, all_predictions = predictor.get_recommendation(
            live_feature_map
        )
        
        # Convert predictions to response model
        prediction_models = [
            NodePrediction(**pred) for pred in all_predictions
        ]
        
        recommendation_detail = NodePrediction(**rec_details)
        
        return RoutingRecommendation(
            recommended_node=recommended_node,
            explanation=explanation,
            timestamp=datetime.utcnow(),
            all_predictions=prediction_models,
            recommendation_details=recommendation_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during prediction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@app.get("/models", status_code=status.HTTP_200_OK)
async def get_models_info():
    """Get information about loaded models"""
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Models not loaded"
        )
    
    return {
        "anomaly_model": "MLPRegressor (Autoencoder)",
        "failure_model": "LogisticRegression",
        "latency_models": list(predictor.models.get('latency', {}).keys()),
        "total_latency_models": len(predictor.models.get('latency', {})),
        "feature_count": len(predictor.get_feature_list()),
        "config": {
            "weight_failure": config.get('optimization', {}).get('weight_failure'),
            "weight_latency": config.get('optimization', {}).get('weight_latency'),
            "prediction_history_size": config.get('prediction_history_size')
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )

