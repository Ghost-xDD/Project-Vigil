import pandas as pd
import numpy as np
import os
import logging
from typing import Dict, Any, Tuple, List
import joblib

from src.utils import load_config, setup_logging, load_model
from src.routing import optimize_routing
from src.features import engineer_features # Import for main
# We'll create explanation logic here to keep it simple
# from src.explanation import generate_explanation

class SentryPredictor:
    """
    A class to load all models and artifacts and perform predictions.
    This is designed to be instantiated once in the API.
    """
    def __init__(self, config_path='config.yaml'):
        self.config = load_config(config_path)
        setup_logging(self.config)
        self.logger = logging.getLogger(__name__)
        
        self.models = {}
        self.scalers = {}
        self.artifacts = {}
        self.load_all_artifacts()

    def load_all_artifacts(self):
        """
        Loads all models, scalers, and artifacts specified in the config.
        """
        self.logger.info("Loading all models and artifacts...")
        try:
            models_dir = self.config['models_dir']
            artifacts_dir = self.config['artifacts_dir']
            
            # 1. Load Feature List
            self.artifacts['feature_list'] = load_model(os.path.join(artifacts_dir, 'feature_list.joblib'))

            # 2. Load Anomaly Model
            anomaly_base = self.config['anomaly_model_base_name']
            self.models['anomaly'] = load_model(os.path.join(models_dir, f"{anomaly_base}_model.joblib"))
            self.scalers['anomaly'] = load_model(os.path.join(models_dir, f"{anomaly_base}_scaler.joblib"))
            self.artifacts['anomaly_threshold'] = load_model(os.path.join(artifacts_dir, 'anomaly_threshold.joblib'))

            # 3. Load Failure Model
            failure_base = self.config['failure_model_base_name']
            self.models['failure'] = load_model(os.path.join(models_dir, f"{failure_base}_model.joblib"))
            self.scalers['failure'] = load_model(os.path.join(models_dir, f"{failure_base}_scaler.joblib"))

            # 4. Load Latency Models (dynamic)
            self.models['latency'] = {}
            latency_template = self.config['latency_model_template']
            
            for f in os.listdir(models_dir):
                if f.startswith('latency_model_') and f.endswith('.joblib'):
                    node_id = f.replace('latency_model_', '').replace('.joblib', '')
                    self.logger.info(f"Loading latency model for {node_id}...")
                    model_path = os.path.join(models_dir, f)
                    self.models['latency'][node_id] = load_model(model_path)

            self.logger.info(f"Successfully loaded artifacts for {len(self.artifacts)} types.")
            self.logger.info(f"Successfully loaded {len(self.models)} model types.")
            self.logger.info(f"Loaded latency models for nodes: {list(self.models['latency'].keys())}")

        except Exception as e:
            self.logger.error(f"FATAL: Failed to load artifacts: {e}", exc_info=True)
            raise

    def get_feature_list(self) -> List[str]:
        return self.artifacts.get('feature_list', [])

    def get_exog_feature_list(self) -> List[str]:
        """
        Gets all features *except* those derived from the latency target.
        """
        all_features = self.get_feature_list()
        target = self.config['latency_model']['target_column']
        return [f for f in all_features if not f.startswith(target)]

    def predict_anomaly(self, X_scaled_row: np.ndarray) -> bool:
        """
        Predicts anomaly on a single row of scaled feature data.
        """
        model = self.models['anomaly']
        threshold = self.artifacts['anomaly_threshold']
        
        reconstructed = model.predict(X_scaled_row.reshape(1, -1))
        mse = np.mean(np.power(X_scaled_row - reconstructed, 2))
        
        return bool(mse > threshold)

    def predict_failure_prob(self, X_scaled_row: np.ndarray) -> float:
        """
        Predicts failure probability on a single row of scaled feature data.
        """
        model = self.models['failure']
        prob = model.predict_proba(X_scaled_row.reshape(1, -1))[0][1]
        return float(prob)

    def forecast_latency(self, node_id: str, exog_row: pd.Series) -> float:
        """
        Forecasts latency for a single node using Gradient Boosting model.
        Production-ready with error handling and bounds checking.
        
        Args:
            node_id (str): The node to forecast for.
            exog_row (pd.Series): The feature vector for prediction.
            
        Returns:
            float: Predicted latency in milliseconds (or penalty if model unavailable)
        """
        model = self.models['latency'].get(node_id)
        if model is None:
            self.logger.warning(f"No latency model for {node_id}, returning default penalty.")
            return 9999.0  # High penalty for missing model
            
        try:
            # Reshape for sklearn prediction (expects 2D array)
            exog_row_2d = exog_row.values.reshape(1, -1)
            
            # Get prediction from Gradient Boosting model
            prediction = model.predict(exog_row_2d)[0]
            
            # Sanity check: latency should be positive and reasonable
            if prediction < 0:
                self.logger.warning(f"Negative prediction for {node_id}: {prediction:.2f}ms, clipping to 0")
                prediction = 0.0
            elif prediction > 10000:
                self.logger.warning(f"Extremely high prediction for {node_id}: {prediction:.2f}ms, capping at 10000")
                prediction = 10000.0
            
            return float(prediction)
            
        except ValueError as e:
            self.logger.error(f"Value error in latency forecast for {node_id}: {e}")
            return 9999.0
        except Exception as e:
            self.logger.error(f"Unexpected error during latency forecast for {node_id}: {e}", exc_info=True)
            return 9999.0  # High penalty on failure

    def generate_explanation(self, recommended_node: str, rec_pred: Dict, all_preds: List[Dict]) -> str:
        """
        Generates a human-readable explanation for the recommendation.
        Note: Router applies auto-calibration and hybrid scoring on top of these predictions.
        """
        rec_fail = rec_pred['failure_prob']
        rec_lat = rec_pred['predicted_latency_ms']
        rec_anomaly = rec_pred.get('anomaly_detected', False)
        
        # Build explanation
        explanation = f"Selected {recommended_node} with {rec_lat:.0f}ms predicted latency and {rec_fail:.2%} failure risk."
        
        # Add anomaly warning if detected
        if rec_anomaly:
            explanation += " ⚠️ Anomaly detected on this node."
        
        # Compare to alternatives
        others = sorted([p for p in all_preds if p['node_id'] != recommended_node], key=lambda x: x['cost_score'])
        if others:
            other = others[0]
            diff = other['predicted_latency_ms'] - rec_lat
            explanation += f" {diff:.0f}ms faster than next best ({other['node_id']})."
        
        explanation += " Note: Router applies auto-calibration (learns environment offset) and hybrid scoring (70% prediction + 30% recent actual) for final routing decision."
            
        return explanation

    def get_recommendation(self, engineered_data: Dict[str, pd.Series]) -> Tuple[str, str, Dict, List[Dict]]:
        """
        Orchestrates all predictions to make a final routing recommendation.
        
        Args:
            engineered_data (Dict[str, pd.Series]): 
                A dictionary where keys are node_ids and values are the *last row*
                of *UNSCALED* engineered features for that node.
                
        Returns:
            Tuple[str, str, Dict, List[Dict]]: 
                (recommended_node, explanation, recommendation_details, all_predictions_list)
        """
        all_features = self.get_feature_list()
        exog_features = self.get_exog_feature_list()
        
        anomaly_scaler = self.scalers['anomaly']
        failure_scaler = self.scalers['failure']
        
        all_predictions = []
        
        for node_id, features_row in engineered_data.items():
            try:
                # --- FIX: We now handle scaling *inside* this loop ---
                
                # 1. Prepare data for Anomaly/Failure models (SCALED)
                # Convert Series to a single-row DataFrame to preserve feature names
                X_row_df = features_row[all_features].to_frame().T
                
                X_scaled_anomaly = anomaly_scaler.transform(X_row_df).flatten()
                X_scaled_failure = failure_scaler.transform(X_row_df).flatten()
                
                # 2. Prepare data for Latency model (UNSCALED)
                exog_row_series = features_row[exog_features]
                
                # 3. Run all models
                anomaly = self.predict_anomaly(X_scaled_anomaly)
                failure_prob = self.predict_failure_prob(X_scaled_failure)
                latency = self.forecast_latency(node_id, exog_row_series)
                
                # 4. Store results
                pred_data = {
                    "node_id": node_id,
                    "failure_prob": failure_prob,
                    "predicted_latency_ms": latency,
                    "anomaly_detected": anomaly
                }
                all_predictions.append(pred_data)
                
            except KeyError as e:
                self.logger.error(f"Missing feature for {node_id}: {e}. Skipping node.")
            except Exception as e:
                self.logger.error(f"Prediction failed for {node_id}: {e}. Skipping node.", exc_info=True)

        # Now, optimize
        if not all_predictions:
            self.logger.error("No predictions generated, cannot optimize.")
            return "no_nodes_available", "No nodes were available for prediction.", {}, []

        node_names = [p['node_id'] for p in all_predictions]
        failure_probs = {p['node_id']: p['failure_prob'] for p in all_predictions}
        latencies = {p['node_id']: p['predicted_latency_ms'] for p in all_predictions}

        recommended_node, cost_scores = optimize_routing(failure_probs, latencies, node_names, self.config)
        
        # Add cost scores to the prediction dictionaries
        for p in all_predictions:
            p['cost_score'] = cost_scores.get(p['node_id'], 999.0)
            
        rec_details = next((p for p in all_predictions if p['node_id'] == recommended_node), {})

        explanation = self.generate_explanation(recommended_node, rec_details, all_predictions)

        return recommended_node, explanation, rec_details, all_predictions

def main():
    try:
        # Load config for feature engineering
        config = load_config('config.yaml')
        
        # Initialize the predictor (loads models and artifacts)
        predictor = SentryPredictor()
        print("SentryPredictor initialized successfully.")
        
        # Create a mock raw DataFrame with multiple rows (e.g., 20 rows per node for rolling windows)
        # FIX: Using 10 samples is enough for rolling windows up to 10
        n_samples = 10
        timestamps = pd.date_range(start='2025-10-23 10:00:00', periods=n_samples, freq='T')
        
        fe_config = config['feature_engineering']
        thresholds = fe_config['thresholds']

        # Mock raw data for agave1 (failing: last row is high)
        agave1_raw_data = {
            'timestamp': timestamps,
            'node_id': ['agave2'] * n_samples,
            'client_type': ['agave'] * n_samples,
            'cpu_usage': np.full(n_samples, 50.0), # 90.0
            'memory_usage': np.full(n_samples, 60.0), # 95.0
            'disk_io': np.full(n_samples, 20.0), # 80.0
            'error_rate': np.full(n_samples, 1.0), # 15.0
            'latency_ms': np.full(n_samples, 80.0),
            'block_height_gap': np.full(n_samples, 1), # 10
        }
        
        # Mock raw data for firedancer1 (healthy: constant values)
        firedancer1_raw_data = {
            'timestamp': timestamps,
            'node_id': ['firedancer1'] * n_samples,
            'client_type': ['firedancer'] * n_samples,
            'cpu_usage': [50.0] * (n_samples - 1) + [thresholds['cpu_usage'] + 10],
            'memory_usage': [60.0] * (n_samples - 1) + [thresholds['memory_usage'] + 10],
            'disk_io': [20.0] * (n_samples - 1) + [thresholds['disk_io'] + 30],
            'error_rate': [1.0] * (n_samples - 1) + [thresholds['error_rate'] + 5],
            'latency_ms': [100.0] * (n_samples - 1) + [250.0],
            'block_height_gap': [1] * (n_samples - 1) + [thresholds['block_height_gap'] + 5],
        }
        
        # Combine into raw DataFrame
        raw_df = pd.concat([pd.DataFrame(agave1_raw_data), pd.DataFrame(firedancer1_raw_data)], ignore_index=True)
        
        # Engineer features using the pipeline from features.py
        engineered_df = engineer_features(raw_df, config)
        
        # Extract the last row for each node to simulate "live" features
        live_feature_map = {}
        for node in ['agave2', 'firedancer1']:
            # FIX: Pass the raw, unscaled, engineered features row
            live_feature_map[node] = engineered_df[engineered_df['node_id'] == node].iloc[-1]

        # Call get_recommendation
        recommended_node, explanation, rec_details, all_predictions = predictor.get_recommendation(live_feature_map)
        
        # Print results
        print(f"Recommended Node: {recommended_node}")
        print(f"Explanation: {explanation}")
        print(f"Recommendation Details: {rec_details}")
        print("All Predictions:")
        for pred in all_predictions:
            print(f"  Node: {pred['node_id']}, Failure Prob: {pred['failure_prob']:.2f}, Latency: {pred['predicted_latency_ms']:.1f}ms, Anomaly Detected: {pred['anomaly_detected']}")
    
    except Exception as e:
        print(f"Error during test usage: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

