from scipy.optimize import linprog
from src.utils import load_config, setup_logging
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

def optimize_routing(failure_probs: Dict[str, float], 
                     latencies: Dict[str, float], 
                     nodes: List[str],
                     config: Dict) -> Tuple[str, Dict[str, float]]:
    """
    Optimize routing recommendation using linear programming.
    
    Args:
        failure_probs (Dict[str, float]): Failure probabilities per node.
        latencies (Dict[str, float]): Predicted latencies per node.
        nodes (List[str]): List of node names.
        config (Dict): The loaded configuration dictionary.
    
    Returns:
        Tuple[str, Dict[str, float]]: (Recommended node, Dictionary of cost scores)
    """
    try:
        n_nodes = len(nodes)
        if n_nodes == 0:
            logger.warning("No nodes provided to optimize_routing.")
            return "no_nodes_available", {}
            
        opt_config = config.get('optimization', {})
        weight_failure = opt_config.get('weight_failure', 0.7)
        weight_latency = opt_config.get('weight_latency', 0.3)

        # Normalize latencies to 0-1 range to be comparable to 0-1 failure prob
        min_lat = min(latencies.values())
        max_lat = max(latencies.values())
        
        # Avoid division by zero if all latencies are the same
        if max_lat - min_lat == 0:
            normalized_latencies = {n: 0.0 for n in nodes}
        else:
            normalized_latencies = {
                n: (latencies[n] - min_lat) / (max_lat - min_lat) for n in nodes
            }
        
        # Calculate cost for each node
        cost_scores = {
            n: weight_failure * failure_probs[n] + weight_latency * normalized_latencies[n]
            for n in nodes
        }
        
        recommended_node = min(cost_scores, key=cost_scores.get)
        
        return recommended_node, cost_scores
            
    except Exception as e:
        logger.error(f"Error during optimization: {e}. Falling back to lowest latency.", exc_info=True)
        if not latencies:
            return nodes[0] if nodes else "no_node_available", {}
        
        fallback_node = min(latencies, key=latencies.get)
        fallback_costs = {n: latencies.get(n, 9999.0) for n in nodes}
        return fallback_node, fallback_costs

