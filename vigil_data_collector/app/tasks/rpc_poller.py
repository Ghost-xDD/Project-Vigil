import asyncio
import logging
import random
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple, List
from collections import deque
import httpx

from app.core.config import settings
from app.schemas.metric import NodeMetrics

# Configure logging
logger = logging.getLogger(__name__)

# Global in-memory cache for latest metrics
latest_metrics_cache: Dict[str, NodeMetrics] = {}

# Global in-memory history storage (last 30 data points per node)
metrics_history: Dict[str, deque] = {}


async def get_slot_and_latency_async(
    node_name: str, 
    url: str, 
    timeout: int
) -> Tuple[int, Optional[int], Optional[float]]:
    """
    Query a Solana RPC node for its current slot and measure latency.
    
    Args:
        node_name: Identifier for the node
        url: RPC endpoint URL
        timeout: Request timeout in seconds
    
    Returns:
        Tuple of (is_healthy, slot, latency_ms)
        - is_healthy: 1 for success, 0 for failure
        - slot: Slot number or None if failed
        - latency_ms: Latency in milliseconds or None if failed
    """
    # Prepare JSON-RPC request for getSlot
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSlot",
        "params": []
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    start_time = asyncio.get_event_loop().time()
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            end_time = asyncio.get_event_loop().time()
            
            # Calculate latency in milliseconds
            latency_ms = (end_time - start_time) * 1000
            
            # Check if request was successful
            if response.status_code != 200:
                logger.warning(
                    f"[{node_name}] Non-200 status code: {response.status_code}"
                )
                return 0, None, latency_ms
            
            # Parse JSON response
            try:
                data = response.json()
            except Exception as e:
                logger.error(f"[{node_name}] Failed to parse JSON: {e}")
                return 0, None, latency_ms
            
            # Check for JSON-RPC errors
            if "error" in data:
                logger.error(
                    f"[{node_name}] JSON-RPC error: {data['error']}"
                )
                return 0, None, latency_ms
            
            # Extract slot number
            if "result" in data and isinstance(data["result"], int):
                slot = data["result"]
                logger.info(
                    f"[{node_name}] Successfully queried - Slot: {slot}, "
                    f"Latency: {latency_ms:.2f}ms"
                )
                return 1, slot, latency_ms
            else:
                logger.error(
                    f"[{node_name}] Invalid response format: {data}"
                )
                return 0, None, latency_ms
                
    except httpx.TimeoutException:
        end_time = asyncio.get_event_loop().time()
        latency_ms = (end_time - start_time) * 1000
        logger.error(
            f"[{node_name}] Request timeout after {latency_ms:.2f}ms"
        )
        return 0, None, latency_ms
        
    except httpx.ConnectError as e:
        end_time = asyncio.get_event_loop().time()
        latency_ms = (end_time - start_time) * 1000
        logger.error(
            f"[{node_name}] Connection error: {e}"
        )
        return 0, None, latency_ms
        
    except Exception as e:
        end_time = asyncio.get_event_loop().time()
        latency_ms = (end_time - start_time) * 1000
        logger.error(
            f"[{node_name}] Unexpected error: {type(e).__name__}: {e}"
        )
        return 0, None, latency_ms


def simulate_os_metrics() -> Tuple[float, float, float]:
    """
    Generate OS metrics for the self-hosted node.
    
    Returns:
        Tuple of (cpu_usage, memory_usage, disk_io) as percentages
    """
    # CPU: Mostly high usage (70-95%), occasional spikes
    cpu_usage = random.uniform(70.0, 95.0)
    
    # Memory: Moderate to high (60-85%)
    memory_usage = random.uniform(60.0, 85.0)
    
    # Disk I/O: Mostly low (5-25%), occasional spikes to 60%
    if random.random() < 0.15:  # 15% chance of spike
        disk_io = random.uniform(45.0, 60.0)
    else:
        disk_io = random.uniform(5.0, 25.0)
    
    return cpu_usage, memory_usage, disk_io


def simulate_node_metrics(current_max_slot: int) -> Tuple[float, int]:
    """
    Generate  RPC metrics (latency and slot) for the self-hosted node.
    
    Args:
        current_max_slot: The highest slot observed from real nodes
    
    Returns:
        Tuple of (latency_ms, slot)
    """
    # Latency: Generally good (50-150ms), occasionally higher (150-300ms)
    if random.random() < 0.2:  # 20% chance of higher latency
        latency_ms = random.uniform(150.0, 300.0)
    else:
        latency_ms = random.uniform(50.0, 150.0)
    
    # Slot: Usually within 0-5 slots of the max, occasionally lagging more
    if current_max_slot > 0:
        if random.random() < 0.1:  # 10% chance of significant lag
            slot_lag = random.randint(5, 20)
        else:
            slot_lag = random.randint(0, 5)
        
        slot = max(0, current_max_slot - slot_lag)
    else:
        # If no real nodes reported, generate a reasonable slot number
        slot = random.randint(366000000, 366100000)
    
    return latency_ms, slot


async def poll_nodes_job():
    """
    Background job that polls all configured RPC nodes and stores metrics.
    This function is called periodically by APScheduler.
    """
    logger.info("=" * 60)
    logger.info("Starting RPC node polling job...")
    
    try:
        # Get current UTC timestamp
        timestamp = datetime.now(timezone.utc)
        
        # Get configured node URLs
        node_urls = settings.NODE_URLS
        
        if not node_urls:
            logger.warning("No node URLs configured. Skipping poll.")
            return
        
        logger.info(f"Polling {len(node_urls)} nodes...")
        
        # Query all nodes concurrently
        tasks = [
            get_slot_and_latency_async(
                node_name, 
                url, 
                settings.REQUEST_TIMEOUT_SECONDS
            )
            for node_name, url in node_urls.items()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and find the highest slot
        node_results = {}
        current_max_slot = 0
        
        for (node_name, url), result in zip(node_urls.items(), results):
            if isinstance(result, Exception):
                logger.error(
                    f"[{node_name}] Task failed with exception: {result}"
                )
                node_results[node_name] = (0, None, None)
            else:
                is_healthy, slot, latency_ms = result
                node_results[node_name] = (is_healthy, slot, latency_ms)
                
                # Track the highest slot among healthy nodes
                if is_healthy and slot is not None:
                    current_max_slot = max(current_max_slot, slot)
        
        logger.info(f"Current max slot across all nodes: {current_max_slot}")
        
        # Generate  OS metrics for the  node
        cpu_usage, memory_usage, disk_io = simulate_os_metrics()
        
        # Generate  RPC metrics (latency and slot) for the  node
        sim_latency_ms, sim_slot = simulate_node_metrics(current_max_slot)
        
        # Create NodeMetrics objects for each real node
        for node_name, (is_healthy, slot, latency_ms) in node_results.items():
            # Calculate block height gap
            block_height_gap = None
            if is_healthy and slot is not None and current_max_slot > 0:
                block_height_gap = max(0, current_max_slot - slot)
            
            metrics = NodeMetrics(
                timestamp=timestamp,
                node_name=node_name,
                latency_ms=latency_ms,
                slot=slot,
                is_healthy=is_healthy,
                block_height_gap=block_height_gap,
                cpu_usage=None,
                memory_usage=None,
                disk_io=None,
                failure_imminent=None
            )
            
            latest_metrics_cache[node_name] = metrics
            
            # Add to history (keep last 30 points)
            if node_name not in metrics_history:
                metrics_history[node_name] = deque(maxlen=30)
            metrics_history[node_name].append(metrics)
            
            logger.debug(f"[{node_name}] Metrics cached: {metrics}")
        
        # Calculate block height gap for node
        sim_block_height_gap = None
        if current_max_slot > 0:
            sim_block_height_gap = max(0, current_max_slot - sim_slot)
        
        # Create NodeMetrics object for the node
        simulated_metrics = NodeMetrics(
            timestamp=timestamp,
            node_name=settings.SIMULATED_NODE_NAME,
            latency_ms=round(sim_latency_ms, 2),
            slot=sim_slot,
            is_healthy=1,  #  node is always "healthy"
            block_height_gap=sim_block_height_gap,
            cpu_usage=round(cpu_usage, 2),
            memory_usage=round(memory_usage, 2),
            disk_io=round(disk_io, 2),
            failure_imminent=None
        )
        
        latest_metrics_cache[settings.SIMULATED_NODE_NAME] = simulated_metrics
        
        # Add to history (keep last 30 points)
        if settings.SIMULATED_NODE_NAME not in metrics_history:
            metrics_history[settings.SIMULATED_NODE_NAME] = deque(maxlen=30)
        metrics_history[settings.SIMULATED_NODE_NAME].append(simulated_metrics)
        
        logger.info(
            f"[{settings.SIMULATED_NODE_NAME}] Simulated metrics - "
            f"Latency: {sim_latency_ms:.2f}ms, Slot: {sim_slot}, "
            f"Gap: {sim_block_height_gap}, "
            f"CPU: {cpu_usage:.2f}%, MEM: {memory_usage:.2f}%, "
            f"DISK: {disk_io:.2f}%"
        )
        
        logger.info(
            f"Polling job completed successfully. "
            f"Total metrics cached: {len(latest_metrics_cache)}"
        )
        
    except Exception as e:
        logger.error(f"Error in polling job: {type(e).__name__}: {e}", exc_info=True)
    
    logger.info("=" * 60)

