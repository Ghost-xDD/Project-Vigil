import pandas as pd
import numpy as np
import os
import logging
from typing import List, Dict

from src.utils import load_config, setup_logging

# Get a logger
logger = logging.getLogger(__name__)

def engineer_interaction_features(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    """
    Creates interaction features based on the config.
    e.g., cpu_usage * error_rate
    """
    try:
        interaction_pairs = config.get('feature_engineering', {}).get('interaction_pairs', [])
        if not interaction_pairs:
            return df
            
        logger.info(f"Engineering {len(interaction_pairs)} interaction features...")
        for pair in interaction_pairs:
            if len(pair) == 2 and pair[0] in df.columns and pair[1] in df.columns:
                col_a = pair[0]
                col_b = pair[1]
                new_col_name = f"{col_a}_x_{col_b}"
                df[new_col_name] = df[col_a] * df[col_b]
            else:
                logger.warning(f"Skipping interaction feature for invalid pair: {pair}")
                
    except Exception as e:
        logger.error(f"Error engineering interaction features: {e}", exc_info=True)
    
    return df

def engineer_threshold_features(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    """
    Creates binary threshold features based on the config.
    e.g., is_high_cpu = (cpu_usage > 80).astype(int)
    """
    try:
        thresholds = config.get('feature_engineering', {}).get('thresholds', {})
        if not thresholds:
            return df
            
        logger.info(f"Engineering {len(thresholds)} threshold features...")
        for col, threshold_val in thresholds.items():
            if col in df.columns:
                new_col_name = f"is_high_{col}"
                df[new_col_name] = (df[col] > threshold_val).astype(int)
            else:
                logger.warning(f"Skipping threshold feature for missing column: {col}")
                
    except Exception as e:
        logger.error(f"Error engineering threshold features: {e}", exc_info=True)
        
    return df

def engineer_features(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
    """
    Main feature engineering pipeline.
    
    Args:
        df (pd.DataFrame): Raw data.
        config (Dict): Configuration dictionary.
        
    Returns:
        pd.DataFrame: Data with engineered features.
    """
    try:
        logger.info(f"Starting feature engineering on dataframe with {len(df)} rows.")
        
        # Ensure timestamp is datetime and df is sorted
        if 'timestamp' not in df.columns:
             logger.error("Missing 'timestamp' column.")
             raise KeyError("Missing 'timestamp' column.")
        if 'node_id' not in df.columns:
            logger.error("Missing 'node_id' column.")
            raise KeyError("Missing 'node_id' column.")
        
        # CRITICAL: Preserve node_id as string BEFORE any operations
        df['node_id'] = df['node_id'].astype(str)
        logger.info(f"Unique node_ids at start: {df['node_id'].unique()}")
            
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values(by=["node_id", "timestamp"])

        # Fill missing features with defaults from config
        fe_config = config.get('feature_engineering', {})
        feature_defaults = fe_config.get('feature_defaults', {})
        
        for feature, default_value in feature_defaults.items():
            if feature in df.columns:
                # Fill null values with default
                null_count = df[feature].isna().sum()
                if null_count > 0:
                    logger.info(f"Filling {null_count} null values in '{feature}' with default: {default_value}")
                    df[feature] = df[feature].fillna(default_value)
            else:
                # Feature doesn't exist, create it with default value
                logger.info(f"Creating missing feature '{feature}' with default value: {default_value}")
                df[feature] = default_value

        # --- New Feature Types ---
        # 1. Engineer Interaction features (e.g., cpu * error)
        df = engineer_interaction_features(df, config)
        
        # 2. Engineer Threshold features (e.g., is_high_cpu)
        df = engineer_threshold_features(df, config)
        # --- End New Features ---

        # 3. Engineer Rolling/Lag features
        fe_config = config.get('feature_engineering', {})
        metrics_to_engineer = fe_config.get('metrics_to_engineer', [])
        # Also include our new interaction features in the rolling/lag calculations
        interaction_cols = [f"{p[0]}_x_{p[1]}" for p in fe_config.get('interaction_pairs', []) if len(p) == 2]
        threshold_cols = [f"is_high_{c}" for c in fe_config.get('thresholds', {})]
        
        all_metrics_to_process = list(set(metrics_to_engineer + interaction_cols + threshold_cols))
        
        rolling_windows = fe_config.get('rolling_windows', [])
        lag_periods = fe_config.get('lag_periods', [])
        
        logger.info(f"Engineering rolling/lag features for {len(all_metrics_to_process)} base metrics.")

        # Group by node for correct calculations
        grouped = df.groupby('node_id')

        for metric in all_metrics_to_process:
            if metric not in df.columns:
                logger.warning(f"Column '{metric}' not found for rolling/lag engineering. Skipping.")
                continue
            
            # a. Trends (Difference)
            df[f'{metric}_trend'] = grouped[metric].transform(lambda x: x.diff())

            # b. Rolling Statistics
            for window in rolling_windows:
                # Rolling Mean
                df[f'{metric}_rolling_mean_{window}'] = grouped[metric].transform(
                    lambda x: x.rolling(window=window, min_periods=1).mean()
                )
                # Rolling Std Dev
                df[f'{metric}_rolling_std_{window}'] = grouped[metric].transform(
                    lambda x: x.rolling(window=window, min_periods=1).std()
                )

            # c. Lag Features
            for lag in lag_periods:
                df[f'{metric}_lag_{lag}'] = grouped[metric].shift(lag)

        # Fill NaNs created by rolling/lag/trend
        # Using 0 is a simple strategy. ffill might be better but 0 is okay for now.
        # IMPORTANT: Don't fill metadata columns (node_id, client_type, timestamp)
        metadata_cols = ['timestamp', 'node_id', 'client_type']
        numeric_cols = [col for col in df.columns if col not in metadata_cols]
        df[numeric_cols] = df[numeric_cols].fillna(0)
        
        # Ensure node_id remains as string (critical!)
        df['node_id'] = df['node_id'].astype(str)
        
        logger.info(f"Feature engineering complete. DataFrame now has {len(df.columns)} columns.")
        return df

    except KeyError as e:
        logger.error(f"Missing required column in dataframe: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Error in feature engineering pipeline: {e}", exc_info=True)
        # Return the original df to avoid crashing the whole pipeline
        return df

def main():
    """
    Main function to load raw data, engineer features, and save processed data.
    This is typically called by the data generation script or a separate prep script.
    """
    try:
        config = load_config('config.yaml')
        setup_logging(config)
        
        raw_path = config.get('raw_data_file')
        processed_path = config.get('processed_data_file')
        
        if not raw_path or not os.path.exists(raw_path):
            logger.error(f"Raw data file not found at {raw_path}. Run 'python data/synthetic-data.py' first.")
            return

        logger.info(f"Loading raw data from {raw_path}...")
        df_raw = pd.read_csv(raw_path)
        
        df_engineered = engineer_features(df_raw, config)
        
        # Ensure processed data directory exists
        os.makedirs(os.path.dirname(processed_path), exist_ok=True)
        
        df_engineered.to_csv(processed_path, index=False)
        logger.info(f"Engineered features saved to {processed_path}")

    except Exception as e:
        logger.error(f"Error in main feature engineering function: {e}", exc_info=True)

# if __name__ == "__main__":
#     main()
