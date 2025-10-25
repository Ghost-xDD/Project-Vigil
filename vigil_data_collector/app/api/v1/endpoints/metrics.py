from fastapi import APIRouter
from typing import List

from app.schemas.metric import NodeMetrics
from app.tasks.rpc_poller import latest_metrics_cache

router = APIRouter()


@router.get("/latest-metrics", response_model=List[NodeMetrics])
async def get_latest_metrics():
    """
    Get the latest metrics for all monitored nodes.
    
    Returns a list of NodeMetrics objects containing:
    - RPC node health, latency, slot, and block height gap
    - OS metrics (CPU, Memory, Disk I/O) for the self-hosted node
    
    The data is updated every POLL_INTERVAL_SECONDS by the background polling job.
    """
    # Convert the cache dictionary to a list of metrics
    metrics_list = list(latest_metrics_cache.values())
    
    return metrics_list

