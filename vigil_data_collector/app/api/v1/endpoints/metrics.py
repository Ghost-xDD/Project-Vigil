from fastapi import APIRouter, Query
from typing import List

from app.schemas.metric import NodeMetrics
from app.tasks.rpc_poller import latest_metrics_cache, metrics_history

router = APIRouter()


@router.get("/latest-metrics", response_model=List[NodeMetrics])
async def get_latest_metrics():
    """
    Get the latest metrics for all monitored nodes.
    
    Returns a list of NodeMetrics objects containing:
    - RPC node health, latency, slot, and block height gap
    - Simulated OS metrics (CPU, Memory, Disk I/O) for the self-hosted node
    
    The data is updated every POLL_INTERVAL_SECONDS by the background polling job.
    """
    # Convert the cache dictionary to a list of metrics
    metrics_list = list(latest_metrics_cache.values())
    
    return metrics_list


@router.get("/history", response_model=List[NodeMetrics])
async def get_metrics_history(
    limit: int = Query(20, ge=1, le=100, description="Number of historical points per node")
):
    """
    Get historical metrics for all monitored nodes.
    
    Returns the last N data points per node (default 20) needed for ML predictions
    with rolling windows and lag features.
    
    Args:
        limit: Number of historical data points to return (default: 20)
    
    Returns:
        List of NodeMetrics with historical data points
    """
    # Get last `limit` points per node from history
    historical_metrics = []
    
    for node_name, history in metrics_history.items():
        # Get last N points for this node
        node_history = list(history)[-limit:]
        historical_metrics.extend(node_history)
    
    return historical_metrics
