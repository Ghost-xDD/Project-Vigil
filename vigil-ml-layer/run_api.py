#!/usr/bin/env python3
"""
Startup script for the Vigil ML Prediction Service API.
"""
import os
import sys
import logging

# Ensure we're in the right directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Add the project root to Python path
sys.path.insert(0, script_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_requirements():
    """Check if all required models and artifacts exist"""
    required_paths = [
        'config.yaml',
        'models/',
        'artifacts/',
    ]
    
    missing = []
    for path in required_paths:
        if not os.path.exists(path):
            missing.append(path)
    
    if missing:
        logger.error(f"Missing required files/directories: {missing}")
        logger.error("Please ensure models are trained before starting the API.")
        logger.error("Run: python -m src.train")
        return False
    
    return True


if __name__ == "__main__":
    logger.info("Starting Vigil ML Prediction Service...")
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Start the API
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )

