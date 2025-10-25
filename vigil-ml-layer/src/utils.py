import yaml
import logging
import os
import joblib
from typing import Any

def load_config(config_path='./sentry-ml-layer/config.yaml'):
    """
    Loads the YAML configuration file.
    
    Args:
        config_path (str): Path to the config.yaml file.
        
    Returns:
        dict: Configuration dictionary.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")
        
    with open(config_path, 'r') as f:
        try:
            config = yaml.safe_load(f)
            return config
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML file: {e}")
            raise
    
def setup_logging(config):
    """
    Sets up the application-wide logger.
    
    Args:
        config (dict): Configuration dictionary.
    """
    log_file = config.get('log_file', 'logs/app.log')
    log_level_str = config.get('log_level', 'INFO').upper()
    
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler() # Also log to console
        ]
    )
    
    logging.info(f"Logging setup complete. Level: {log_level_str}, File: {log_file}")

def save_model(model: Any, filepath: str) -> None:
    """
    Saves a model (joblib or Keras) to the specified path.
    Ensures the directory exists.

    Args:
        model: The model object to save.
        filepath (str): The full path to save the model.
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(model, filepath)
        logging.info(f"Joblib model saved to {filepath}")
            
    except Exception as e:
        logging.error(f"Error saving model to {filepath}: {e}")
        raise

def load_model(filepath: str) -> Any:
    """
    Loads a model from the specified path.

    Args:
        filepath (str): The full path to the model file.

    Returns:
        Any: The loaded model object.
    """
    try:
        model = joblib.load(filepath)
        logging.info(f"Joblib model loaded from {filepath}")
        return model
    except FileNotFoundError:
        logging.error(f"Model file not found: {filepath}")
        raise
    except Exception as e:
        logging.error(f"Error loading model from {filepath}: {e}")
        raise
