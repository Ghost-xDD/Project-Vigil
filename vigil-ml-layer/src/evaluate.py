import pandas as pd
import numpy as np
import os
import logging
from typing import List, Dict
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, mean_squared_error
from src.utils import load_config, setup_logging, load_model
from src.train import get_feature_columns # Use the same logic

def evaluate_anomaly_model(df: pd.DataFrame, features: List[str], config: Dict) -> Dict:
    """
    Evaluates the trained anomaly model on test data.
    """
    logging.info("Evaluating anomaly model...")
    try:
        model_config = config['anomaly_model']
        models_dir = config['models_dir']
        artifacts_dir = config['artifacts_dir']
        base_name = config['anomaly_model_base_name']

        # Load model, scaler, and threshold
        model = load_model(os.path.join(models_dir, f"{base_name}_model.joblib"))
        scaler = load_model(os.path.join(models_dir, f"{base_name}_scaler.joblib"))
        threshold = load_model(os.path.join(artifacts_dir, 'anomaly_threshold.joblib'))

        if model is None or scaler is None or threshold is None:
            logging.error("Could not load all anomaly artifacts for evaluation.")
            return {}

        healthy_label = model_config['healthy_state_label']
        healthy_df = df[df['failure_label'] == healthy_label]
        unhealthy_df = df[df['failure_label'] != healthy_label]

        # Evaluate on healthy data
        X_healthy_scaled = scaler.transform(healthy_df[features])
        healthy_reconstructions = model.predict(X_healthy_scaled)
        healthy_errors = np.mean(np.power(X_healthy_scaled - healthy_reconstructions, 2), axis=1)
        healthy_accuracy = (healthy_errors <= threshold).mean() * 100

        # Evaluate on unhealthy data
        X_unhealthy_scaled = scaler.transform(unhealthy_df[features])
        unhealthy_reconstructions = model.predict(X_unhealthy_scaled)
        unhealthy_errors = np.mean(np.power(X_unhealthy_scaled - unhealthy_reconstructions, 2), axis=1)
        unhealthy_detection_rate = (unhealthy_errors > threshold).mean() * 100

        results = {
            "threshold": threshold,
            "healthy_data_accuracy": f"{healthy_accuracy:.2f}%",
            "unhealthy_data_detection_rate": f"{unhealthy_detection_rate:.2f}%"
        }
        logging.info(f"Anomaly Evaluation: {results}")
        return results

    except Exception as e:
        logging.error(f"Error evaluating anomaly model: {e}", exc_info=True)
        return {"error": str(e)}

def evaluate_failure_model(df: pd.DataFrame, features: List[str], config: Dict) -> Dict:
    """
    Evaluates the trained failure model on the test split.
    """
    logging.info("Evaluating failure model...")
    try:
        model_config = config['failure_model']
        models_dir = config['models_dir']
        base_name = config['failure_model_base_name']
        target = model_config['target_column']

        # Load model and scaler
        model = load_model(os.path.join(models_dir, f"{base_name}_model.joblib"))
        scaler = load_model(os.path.join(models_dir, f"{base_name}_scaler.joblib"))

        if model is None or scaler is None:
            logging.error("Could not load all failure model artifacts.")
            return {}

        X = df[features]
        y = df[target]
        
        # Use the same train/test split as in training
        _, X_test, _, y_test = train_test_split(
            X, y, 
            test_size=model_config['test_split_ratio'], 
            random_state=42, 
            stratify=y
        )
        
        X_test_scaled = scaler.transform(X_test)
        y_pred = model.predict(X_test_scaled)
        
        report = classification_report(y_test, y_pred, output_dict=True)
        matrix = confusion_matrix(y_test, y_pred).tolist()

        logging.info("Failure Model Classification Report:\n" + classification_report(y_test, y_pred))
        logging.info("Failure Model Confusion Matrix:\n" + str(matrix))
        
        return {"classification_report": report, "confusion_matrix": matrix}

    except Exception as e:
        logging.error(f"Error evaluating failure model: {e}", exc_info=True)
        return {"error": str(e)}

def evaluate_latency_models(df: pd.DataFrame, features: List[str], config: Dict) -> Dict:
    """
    Evaluates all trained per-node latency models.
    """
    logging.info("Evaluating latency models...")
    results = {}
    try:
        model_config = config['latency_model']
        models_dir = config['models_dir']
        template = config['latency_model_template']
        target = model_config['target_column']
        
        node_ids = df['node_id'].unique()
        if len(node_ids) == 0:
            logging.warning("No nodes found to evaluate.")
            return {}

        for node_id in node_ids:
            logging.info(f"Evaluating latency for {node_id}...")
            model_path = os.path.join(models_dir, template.format(node_id=node_id) + ".joblib")
            model = load_model(model_path)
            
            if model is None:
                logging.warning(f"No latency model found for {node_id}. Skipping.")
                results[node_id] = "No model found"
                continue

            node_df = df[df['node_id'] == node_id].sort_values(by='timestamp')
            
            y = node_df[target]
            exog_features = [f for f in features if not f.startswith(target)]
            X = node_df[exog_features]
            
            test_size = model_config['test_size']
            
            if len(y) < model_config['min_obs'] or len(y) - test_size < model_config['min_obs']:
                logging.warning(f"Not enough data to evaluate {node_id}.")
                results[node_id] = "Not enough data"
                continue
                
            y_test = y[-test_size:]
            X_test = X[-test_size:]
            
            y_pred = model.predict(n_periods=len(y_test), exogenous=X_test)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            
            logging.info(f"Latency model test RMSE for {node_id}: {rmse:.4f}")
            results[node_id] = {"rmse": rmse}
            
        return results

    except Exception as e:
        logging.error(f"Error evaluating latency models: {e}", exc_info=True)
        return {"error": str(e)}


def main():
    """
    Main function to run the entire model evaluation pipeline.
    """
    try:
        config = load_config('config.yaml')
        setup_logging(config)
        logging.info("--- Starting Model Evaluation Pipeline ---")
        
        data_path = config['processed_data_file']
        if not os.path.exists(data_path):
            logging.error(f"Processed data file not found at {data_path}.")
            return
            
        df = pd.read_csv(data_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # We call get_feature_columns, but we don't need the output,
        # as it's just used to save the artifact.
        # The other functions will load the artifact.
        # This is slightly redundant, but ensures consistency.
        # A better way would be to have a shared function.
        # Let's refine this: get_feature_columns in train.py *saves* it.
        # Here, we *load* it.
        artifacts_dir = config['artifacts_dir']
        feature_cols = load_model(os.path.join(artifacts_dir, 'feature_list.joblib'))
        
        if feature_cols is None:
            logging.error("Feature list artifact not found. Run training first.")
            return
            
        logging.info(f"Loaded {len(feature_cols)} features from artifact.")
        
        print("\n--- Anomaly Model Evaluation ---")
        evaluate_anomaly_model(df, feature_cols, config)
        
        print("\n--- Failure Model Evaluation ---")
        evaluate_failure_model(df, feature_cols, config)
        
        print("\n--- Latency Model Evaluation ---")
        evaluate_latency_models(df, feature_cols, config)
            
        logging.info("--- Model Evaluation Pipeline Finished ---")

    except Exception as e:
        logging.error(f"Fatal error in main evaluation pipeline: {e}", exc_info=True)

if __name__ == "__main__":
    main()
