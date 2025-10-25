import pandas as pd
import numpy as np
import os
import logging
from typing import List, Dict, Tuple
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import classification_report, confusion_matrix, mean_squared_error
import pmdarima as pm

from src.utils import load_config, setup_logging, save_model

def get_feature_columns(df: pd.DataFrame, config: Dict) -> List[str]:
    """
    Gets the list of feature columns and saves it as an artifact.
    """
    metadata_cols = config.get('metadata_columns', [])
    target_cols = config.get('target_columns', [])
    
    exclude_cols = set(metadata_cols + target_cols)
    exclude_cols.add(config['latency_model']['target_column'])
    
    all_cols = set(df.columns)
    feature_cols = sorted([col for col in all_cols if col not in exclude_cols])
    
    logging.info(f"Identified {len(feature_cols)} feature columns.")
    
    # Save the feature list
    artifacts_dir = config['artifacts_dir']
    os.makedirs(artifacts_dir, exist_ok=True)
    save_model(feature_cols, os.path.join(artifacts_dir, 'feature_list.joblib'))
    
    return feature_cols

def train_anomaly_model(df: pd.DataFrame, features: List[str], config: Dict) -> None:
    """
    Trains an sklearn MLPRegressor as an Autoencoder and saves the threshold.
    """
    logging.info("Starting anomaly model training (sklearn MLPRegressor)...")
    try:
        model_config = config['anomaly_model']
        models_dir = config['models_dir']
        artifacts_dir = config['artifacts_dir']
        base_name = config['anomaly_model_base_name']

        healthy_label = model_config['healthy_state_label']
        healthy_df = df[df['failure_label'] == healthy_label].copy()
        
        if healthy_df.empty:
            logging.error("No 'healthy' data found. Check 'healthy_state_label'.")
            return

        unhealthy_df = df[df['failure_label'] != healthy_label].copy()

        scaler = StandardScaler()
        X_healthy_scaled = scaler.fit_transform(healthy_df[features])
        
        X_train, X_val = train_test_split(
            X_healthy_scaled, 
            test_size=model_config['test_split_ratio'], 
            random_state=42
        )
        
        logging.info(f"Training anomaly model on {len(X_train)} healthy samples. Validating on {len(X_val)}.")
        
        autoencoder = MLPRegressor(
            hidden_layer_sizes=model_config['hidden_layer_sizes'],
            activation=model_config['activation'],
            solver=model_config['solver'],
            max_iter=model_config['max_iter'],
            learning_rate_init=model_config['learning_rate_init'],
            alpha=model_config['alpha'],
            early_stopping=model_config['early_stopping'],
            n_iter_no_change=model_config['n_iter_no_change'],
            batch_size=model_config['batch_size'],
            random_state=42,
            verbose=False # Quieter logs
        )
        
        autoencoder.fit(X_train, X_train)
        
        healthy_reconstructions = autoencoder.predict(X_healthy_scaled)
        train_reconstruction_errors = np.mean(np.power(X_healthy_scaled - healthy_reconstructions, 2), axis=1)
        
        threshold = np.mean(train_reconstruction_errors) + 3 * np.std(train_reconstruction_errors)
        logging.info(f"Calculated anomaly threshold based on healthy data: {threshold:.6f}")
        
        if not unhealthy_df.empty:
            X_unhealthy_scaled = scaler.transform(unhealthy_df[features])
            unhealthy_reconstructions = autoencoder.predict(X_unhealthy_scaled)
            unhealthy_reconstruction_errors = np.mean(np.power(X_unhealthy_scaled - unhealthy_reconstructions, 2), axis=1)
            
            anomalies_detected = (unhealthy_reconstruction_errors > threshold).sum()
            logging.info(f"Anomaly model performance: Detected {anomalies_detected} / {len(unhealthy_df)} ({anomalies_detected / len(unhealthy_df) * 100:.2f}%) of unhealthy samples as anomalies.")
        
        # Save models and artifacts
        save_model(autoencoder, os.path.join(models_dir, f"{base_name}_model.joblib"))
        save_model(scaler, os.path.join(models_dir, f"{base_name}_scaler.joblib"))
        save_model(threshold, os.path.join(artifacts_dir, 'anomaly_threshold.joblib'))
        
        logging.info("Anomaly model training complete.")

    except Exception as e:
        logging.error(f"Error in train_anomaly_model: {e}", exc_info=True)

def train_failure_model(df: pd.DataFrame, features: List[str], config: Dict) -> None:
    """
    Trains a Logistic Regression model and logs feature importances.
    """
    logging.info("Starting failure prediction model training...")
    try:
        model_config = config['failure_model']
        models_dir = config['models_dir']
        base_name = config['failure_model_base_name']
        target = model_config['target_column']
        
        X = df[features]
        y = df[target]
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=model_config['test_split_ratio'], 
            random_state=42, 
            stratify=y
        )
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        logging.info(f"Training failure model on {len(X_train_scaled)} samples. Testing on {len(X_test_scaled)}.")
        
        model = LogisticRegression(
            C=model_config['C'],
            solver=model_config['solver'],
            class_weight=model_config['class_weight'],
            random_state=42, 
            max_iter=1000
        )
        model.fit(X_train_scaled, y_train)
        
        y_pred = model.predict(X_test_scaled)
        
        logging.info("Failure Model Classification Report:\n" + classification_report(y_test, y_pred))
        logging.info("Failure Model Confusion Matrix:\n" + str(confusion_matrix(y_test, y_pred)))
        
        # --- Log Feature Importances ---
        if hasattr(model, 'coef_'):
            importances = pd.Series(model.coef_[0], index=features)
            logging.info("Top 10 features promoting failure (Positive Coefs):")
            logging.info("\n" + importances.nlargest(10).to_string())
            logging.info("Top 10 features inhibiting failure (Negative Coefs):")
            logging.info("\n" + importances.nsmallest(10).to_string())
        # --- End ---

        save_model(model, os.path.join(models_dir, f"{base_name}_model.joblib"))
        save_model(scaler, os.path.join(models_dir, f"{base_name}_scaler.joblib"))
        
        logging.info("Failure prediction model training complete.")

    except Exception as e:
        logging.error(f"Error in train_failure_model: {e}", exc_info=True)

def train_latency_model_for_node(node_df: pd.DataFrame, features: List[str], node_id: str, config: Dict) -> None:
    """
    Trains a SARIMAX model for a single node using auto_arima.
    """
    logging.info(f"Starting latency model training for node: {node_id}...")
    try:
        model_config = config['latency_model']
        models_dir = config['models_dir']
        template = config['latency_model_template']
        target = model_config['target_column']
        
        node_df = node_df.sort_values(by='timestamp')
        
        if len(node_df) < model_config['min_obs']:
            logging.warning(f"Skipping latency model for {node_id}: not enough data ({len(node_df)} < {model_config['min_obs']}).")
            return
            
        y = node_df[target]
        
        # Exogenous variables: all features *except* those derived from latency itself
        exog_features = [f for f in features if not f.startswith(target)]
        X = node_df[exog_features]
        
        test_size = model_config['test_size']
        if len(y) - test_size < model_config['min_obs']:
             logging.warning(f"Skipping {node_id}: Not enough data for train/test split with test_size={test_size}.")
             return
             
        y_train, y_test = y[:-test_size], y[-test_size:]
        X_train, X_test = X[:-test_size], X[-test_size:]
        
        logging.info(f"Training latency model on {len(y_train)} samples. Testing on {len(y_test)}.")

        model = pm.auto_arima(
            y_train,
            exogenous=X_train,
            m=model_config['seasonal_m'],
            seasonal=True,
            stepwise=True,
            suppress_warnings=True,
            error_action='ignore',
            n_jobs=-1
        )
        
        logging.info(f"Best SARIMAX model for {node_id}: {model.order} {model.seasonal_order}")
        logging.info(model.summary())
        
        if not y_test.empty:
            y_pred = model.predict(n_periods=len(y_test), exogenous=X_test)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            logging.info(f"Latency model test RMSE for {node_id}: {rmse:.4f}")
        
        model_filename = template.format(node_id=node_id) + ".joblib"
        save_model(model, os.path.join(models_dir, model_filename))
        
        logging.info(f"Latency model training complete for {node_id}.")

    except Exception as e:
        logging.error(f"Error in train_latency_model_for_node ({node_id}): {e}", exc_info=True)


def main():
    """
    Main function to run the entire model training pipeline.
    """
    try:
        config = load_config('config.yaml')
        setup_logging(config)
        logging.info("--- Starting Model Training Pipeline ---")
        
        data_path = config['processed_data_file']
        if not os.path.exists(data_path):
            logging.error(f"Processed data file not found at {data_path}. Run 'python src/features.py' or 'python data/synthetic-data.py' first.")
            return
            
        df = pd.read_csv(data_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        feature_cols = get_feature_columns(df, config)
        
        train_anomaly_model(df, feature_cols, config)
        
        train_failure_model(df, feature_cols, config)
        
        # Get unique node IDs from the dataframe
        node_ids = df['node_id'].unique()
        if len(node_ids) == 0:
             logging.warning("No node_ids found in processed data. Skipping latency models.")
        
        for node_id in node_ids:
            node_df = df[df['node_id'] == node_id].copy()
            train_latency_model_for_node(node_df, feature_cols, node_id, config)
            
        logging.info("--- Model Training Pipeline Finished ---")

    except Exception as e:
        logging.error(f"Fatal error in main training pipeline: {e}", exc_info=True)

if __name__ == "__main__":
    main()