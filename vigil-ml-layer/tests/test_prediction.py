import pytest
import pandas as pd
import numpy as np
import os
from src.utils import load_config
from src.features import engineer_features
from src.predict import SentryPredictor

# --- Fixtures ---

@pytest.fixture(scope="module")
def config():
    """Loads the main config file."""
    try:
        return load_config('config.yaml')
    except FileNotFoundError:
        pytest.fail("config.yaml not found. Make sure you are running pytest from the root directory.")

@pytest.fixture(scope="module")
def trained_predictor(config):
    """
    Loads the SentryPredictor.
    This fixture FAILS if models haven't been trained (python src/train.py).
    """
    try:
        # predictor = SentryPredictor(config) # <--- This was the bug
        
        # This is the fix:
        # Call with no arguments to use the default 'config.yaml' path
        predictor = SentryPredictor()
        return predictor
    except FileNotFoundError as e:
        print(f"\nTest setup failed: Model artifact not found.")
        print("Please run 'python src/train.py' before running tests.")
        pytest.fail(f"Model artifact not found, run train.py first. Error: {e}")
    except Exception as e:
        pytest.fail(f"Failed to initialize SentryPredictor: {e}")


@pytest.fixture(scope="module")
def failing_raw_metrics_payload(config):
    """
    Creates a small DataFrame of RAW metrics where the *last row*
    represents a clear failure state based on config thresholds.
    We need 10 rows to properly generate rolling/lag features.
    """
    fe_config = config['feature_engineering']
    thresholds = fe_config['thresholds']
    
    # Create 9 healthy rows
    data = {
        "timestamp": pd.date_range(start="2025-01-01", periods=10, freq="T"),
        "node_id": ["agave1"] * 10,
        "client_type": ["agave"] * 10,
        "cpu_usage": [50.0] * 9 + [thresholds['cpu_usage'] + 10], # 90.0
        "memory_usage": [60.0] * 9 + [thresholds['memory_usage'] + 10], # 95.0
        "disk_io": [20.0] * 9 + [thresholds['disk_io'] + 30], # 80.0
        "error_rate": [1.0] * 9 + [thresholds['error_rate'] + 5], # 15.0
        "latency_ms": [100.0] * 9 + [250.0],
        "block_height_gap": [1] * 9 + [thresholds['block_height_gap'] + 5], # 10
        "failure_label": [0] * 10 # Not used by predictor, but good to have
    }
    return pd.DataFrame(data)

@pytest.fixture(scope="module")
def healthy_raw_metrics_payload(config):
    """
    Creates a small DataFrame of RAW metrics that are all healthy.
    """
    data = {
        "timestamp": pd.date_range(start="2025-01-01", periods=10, freq="T"),
        "node_id": ["firedancer1"] * 10,
        "client_type": ["firedancer"] * 10,
        "cpu_usage": [50.0] * 10,
        "memory_usage": [60.0] * 10,
        "disk_io": [20.0] * 10,
        "error_rate": [1.0] * 10,
        "latency_ms": [80.0] * 10,
        "block_height_gap": [1] * 10,
        "failure_label": [0] * 10
    }
    return pd.DataFrame(data)

@pytest.fixture(scope="module")
def engineered_data_for_test(config, failing_raw_metrics_payload, healthy_raw_metrics_payload):
    """
    Pre-computes the engineered features for both healthy and failing nodes.
    This is the exact input the get_recommendation method expects.
    """
    # 1. Engineer features for both
    engineered_failing_df = engineer_features(failing_raw_metrics_payload, config)
    engineered_healthy_df = engineer_features(healthy_raw_metrics_payload, config)
    
    # 2. Get the last (most recent) row of features
    failing_features_row = engineered_failing_df.iloc[-1]
    healthy_features_row = engineered_healthy_df.iloc[-1]
    
    # 3. Create the input dictionary
    engineered_data = {
        'agave1': failing_features_row,      # The failing node
        'firedancer1': healthy_features_row  # The healthy node
    }
    return engineered_data

# --- Tests ---

def test_get_recommendation_end_to_end(trained_predictor, engineered_data_for_test):
    """
    This is the main integration test for the SentryPredictor class.
    It simulates a real-world scenario with one healthy and one failing node.
    
    It tests the full orchestration:
    - Feature scaling (internal)
    - Anomaly prediction (internal)
    - Failure prediction (internal)
    - Latency forecast (internal)
    - Routing optimization (call to optimize_routing)
    - Explanation generation
    """
    
    # --- 1. Run the main prediction/recommendation method ---
    rec_node, explanation, rec_details, all_preds = trained_predictor.get_recommendation(engineered_data_for_test)
    
    # --- 2. Assert Recommendation ---
    # The recommendation MUST be the healthy node
    assert rec_node == 'firedancer1'
    
    # --- 3. Assert Explanation ---
    assert "Recommending firedancer1" in explanation
    assert "Next best is agave1" in explanation # Check that it mentions the other node
    
    # --- 4. Assert Full Prediction List ---
    assert len(all_preds) == 2
    
    # --- 5. Assert Details for the FAILING node (agave1) ---
    failing_pred = next(p for p in all_preds if p['node_id'] == 'agave1')
    
    # This is the test that was failing before (assert True == False)
    # With models trained on the new features, this should pass.
    assert failing_pred['anomaly_detected'] == True
    assert failing_pred['failure_prob'] > 0.5
    assert failing_pred['cost_score'] > 1.0 # Cost should be high
    
    # --- 6. Assert Details for the HEALTHY node (firedancer1) ---
    healthy_pred = next(p for p in all_preds if p['node_id'] == 'firedancer1')
    
    assert healthy_pred['anomaly_detected'] == False
    assert healthy_pred['failure_prob'] < 0.5
    assert healthy_pred['cost_score'] < 1.0 # Cost should be low
    assert healthy_pred['cost_score'] < failing_pred['cost_score']
    
    # --- 7. Assert Recommendation Details Object ---
    assert rec_details['node_id'] == 'firedancer1'
    assert rec_details['cost_score'] == healthy_pred['cost_score']


