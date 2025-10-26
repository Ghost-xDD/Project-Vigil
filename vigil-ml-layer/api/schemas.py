from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class NodeMetric(BaseModel):
    """Single node metric data point"""
    timestamp: datetime
    node_id: Optional[str] = None  # Optional, will use node_name if not provided
    node_name: Optional[str] = None  # From Data Collector
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_io: Optional[float] = None
    latency_ms: Optional[float] = None
    block_height_gap: Optional[int] = None
    is_healthy: int = Field(1, description="1 for healthy, 0 for unhealthy")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2023-10-25T12:00:00Z",
                "node_id": "ankr_devnet",
                "cpu_usage": 75.5,
                "memory_usage": 68.2,
                "disk_io": 25.3,
                "latency_ms": 150.5,
                "block_height_gap": 2,
                "is_healthy": 1
            }
        }


class MetricsBatch(BaseModel):
    """Batch of metrics for multiple nodes over time"""
    metrics: List[NodeMetric]
    
    class Config:
        json_schema_extra = {
            "example": {
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
                    }
                ]
            }
        }


class NodePrediction(BaseModel):
    """Prediction results for a single node"""
    node_id: str
    failure_prob: float = Field(..., description="Probability of failure (0-1)")
    predicted_latency_ms: float = Field(..., description="Predicted latency in milliseconds")
    anomaly_detected: bool = Field(..., description="Whether an anomaly was detected")
    cost_score: float = Field(..., description="Combined cost score for routing optimization")
    
    class Config:
        json_schema_extra = {
            "example": {
                "node_id": "ankr_devnet",
                "failure_prob": 0.15,
                "predicted_latency_ms": 145.2,
                "anomaly_detected": False,
                "cost_score": 0.215
            }
        }


class RoutingRecommendation(BaseModel):
    """Complete routing recommendation response"""
    recommended_node: str = Field(..., description="The recommended node to route to")
    explanation: str = Field(..., description="Human-readable explanation of the recommendation")
    timestamp: datetime = Field(..., description="Time of recommendation")
    all_predictions: List[NodePrediction] = Field(..., description="Predictions for all available nodes")
    recommendation_details: NodePrediction = Field(..., description="Details of the recommended node")
    
    class Config:
        json_schema_extra = {
            "example": {
                "recommended_node": "helius_devnet",
                "explanation": "Recommending helius_devnet (Cost: 0.125) due to low failure prob (0.08) and low latency (120.5ms). Next best is ankr_devnet (Cost: 0.215).",
                "timestamp": "2023-10-25T12:00:00Z",
                "all_predictions": [
                    {
                        "node_id": "helius_devnet",
                        "failure_prob": 0.08,
                        "predicted_latency_ms": 120.5,
                        "anomaly_detected": False,
                        "cost_score": 0.125
                    }
                ],
                "recommendation_details": {
                    "node_id": "helius_devnet",
                    "failure_prob": 0.08,
                    "predicted_latency_ms": 120.5,
                    "anomaly_detected": False,
                    "cost_score": 0.125
                }
            }
        }


class HealthStatus(BaseModel):
    """API health status"""
    status: str
    models_loaded: bool
    available_models: List[str]
    version: str


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime

