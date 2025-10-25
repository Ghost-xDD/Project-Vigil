"""
Integration example: Connect Data Collector with ML Prediction Service

This script demonstrates how to:
1. Fetch metrics from the Data Collector
2. Send them to the ML Service for prediction
3. Get routing recommendations
"""
import requests
import time
from datetime import datetime
from typing import List, Dict

# Service URLs
DATA_COLLECTOR_URL = "http://localhost:8000"
ML_SERVICE_URL = "http://localhost:8001"


def get_latest_metrics() -> List[Dict]:
    """Fetch latest metrics from Data Collector"""
    try:
        response = requests.get(f"{DATA_COLLECTOR_URL}/api/v1/metrics/latest-metrics")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching metrics: {e}")
        return []


def get_routing_recommendation(metrics: List[Dict]) -> Dict:
    """Send metrics to ML Service and get routing recommendation"""
    try:
        # The ML service expects a specific format
        payload = {"metrics": metrics}
        
        response = requests.post(
            f"{ML_SERVICE_URL}/predict",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting prediction: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return {}


def check_services_health() -> bool:
    """Check if both services are running"""
    services_ok = True
    
    # Check Data Collector
    try:
        response = requests.get(f"{DATA_COLLECTOR_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Data Collector is healthy")
        else:
            print("✗ Data Collector returned non-200 status")
            services_ok = False
    except Exception as e:
        print(f"✗ Data Collector is not reachable: {e}")
        services_ok = False
    
    # Check ML Service
    try:
        response = requests.get(f"{ML_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ ML Service is healthy (Models loaded: {data.get('models_loaded')})")
        else:
            print("✗ ML Service returned non-200 status")
            services_ok = False
    except Exception as e:
        print(f"✗ ML Service is not reachable: {e}")
        services_ok = False
    
    return services_ok


def main():
    """Main integration loop"""
    print("=" * 60)
    print("Vigil Services Integration Example")
    print("=" * 60)
    print()
    
    # Check services
    print("Checking service health...")
    if not check_services_health():
        print("\n⚠️  One or more services are not running!")
        print("Please start both services:")
        print("  - Data Collector: cd data_collector && python3 main.py")
        print("  - ML Service: cd vigil-ml-layer && python run_api.py")
        return
    
    print("\n" + "=" * 60)
    print("Starting continuous monitoring...")
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")
    
    try:
        while True:
            # Fetch latest metrics
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching metrics...")
            metrics = get_latest_metrics()
            
            if not metrics:
                print("  ⚠️  No metrics available")
                time.sleep(10)
                continue
            
            print(f"  ✓ Received metrics for {len(metrics)} nodes")
            
            # Get routing recommendation
            print(f"  → Requesting ML prediction...")
            recommendation = get_routing_recommendation(metrics)
            
            if recommendation:
                recommended_node = recommendation.get('recommended_node')
                explanation = recommendation.get('explanation')
                details = recommendation.get('recommendation_details', {})
                
                print(f"\n  🎯 RECOMMENDATION: Route to '{recommended_node}'")
                print(f"     Failure Probability: {details.get('failure_prob', 0):.1%}")
                print(f"     Predicted Latency: {details.get('predicted_latency_ms', 0):.1f}ms")
                print(f"     Anomaly Detected: {details.get('anomaly_detected', False)}")
                print(f"     Cost Score: {details.get('cost_score', 0):.3f}")
                print(f"\n  📊 Explanation: {explanation}\n")
                
                # Show all predictions
                all_preds = recommendation.get('all_predictions', [])
                if len(all_preds) > 1:
                    print("  📈 All Node Predictions:")
                    for pred in sorted(all_preds, key=lambda x: x.get('cost_score', 999)):
                        node = pred.get('node_id')
                        cost = pred.get('cost_score', 0)
                        latency = pred.get('predicted_latency_ms', 0)
                        failure = pred.get('failure_prob', 0)
                        print(f"     - {node:25s} Cost: {cost:.3f}  Latency: {latency:6.1f}ms  Failure: {failure:.1%}")
            else:
                print("  ✗ Failed to get recommendation")
            
            print("\n" + "-" * 60 + "\n")
            
            # Wait before next iteration
            time.sleep(15)  # Match the polling interval
            
    except KeyboardInterrupt:
        print("\n\nStopping integration monitor...")
    except Exception as e:
        print(f"\n\nError in main loop: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

