#!/usr/bin/env python3
"""
Train ML models using real node IDs from production data
"""
import pandas as pd
import numpy as np
import sys
import os

# Add current directory to path
sys.path.insert(0, '/app' if os.path.exists('/app') else '.')

from src.features import engineer_features
from src.utils import load_config
from src.train import main as train_models

# Real node IDs from your system (excluding agave_self_hosted)
REAL_NODES = ['ankr_devnet', 'helius_devnet', 'alchemy_devnet', 'solana_public_devnet']

def generate_ar1_series(n_samples, phi, mean=0.0, std_dev=1.0):
    """Generates an AR(1) time series."""
    ar = np.zeros(n_samples)
    ar[0] = np.random.normal(mean, std_dev)
    for t in range(1, n_samples):
        ar[t] = phi * ar[t-1] + np.random.normal(mean, std_dev)
    return ar

def scale_to_range(series, min_val, max_val):
    """Scales a series to a specified [min_val, max_val] range."""
    return np.interp(series, (series.min(), series.max()), (min_val, max_val))

def simulate_failure_ramp(series, start_idx, length, ramp_max, clip_min=0, clip_max=100):
    """Overlays a linear ramp on a time series to simulate failure."""
    series = series.copy()
    if start_idx + length > len(series):
        length = len(series) - start_idx
        
    ramp = np.linspace(0, ramp_max, length)
    series[start_idx : start_idx + length] = series[start_idx : start_idx + length].astype(float) + ramp
    series = np.clip(series, clip_min, clip_max)
    return series, start_idx, start_idx + length

def generate_data_for_real_nodes(n_samples=2880, nodes=None):
    """
    Generate synthetic training data with real node IDs.
    
    Args:
        n_samples: Number of samples per node (default 2880 = 2 days at 1min intervals)
        nodes: List of node IDs to generate data for
    
    Returns:
        pd.DataFrame with synthetic metrics
    """
    if nodes is None:
        nodes = REAL_NODES
    
    n_nodes = len(nodes)
    print(f"🔄 Generating synthetic data for {n_nodes} nodes: {nodes}")
    print(f"   Samples per node: {n_samples}")
    
    data = []
    base_timestamp = pd.to_datetime('2025-10-01 00:00:00')
    time_index = pd.date_range(start=base_timestamp, periods=n_samples, freq='min')
    
    for i, node_id in enumerate(nodes):
        print(f"   Generating data for {node_id}...")
        
        # Determine client type
        client_type = 'agave'  # All devnet nodes typically run Agave
        
        # Generate base metrics with AR(1) processes
        cpu = scale_to_range(generate_ar1_series(n_samples, phi=0.9, std_dev=5), 30, 80)
        memory = scale_to_range(generate_ar1_series(n_samples, phi=0.85, std_dev=3), 40, 75)
        disk_io = scale_to_range(generate_ar1_series(n_samples, phi=0.7, std_dev=10), 10, 60)
        
        # Latency with some variation per node
        base_latency = 50 + (i * 20)  # Different base latency per node
        latency = scale_to_range(
            generate_ar1_series(n_samples, phi=0.8, std_dev=15), 
            base_latency, 
            base_latency + 100
        )
        
        # Block height gap (mostly 0-2, occasional spikes)
        block_gap = np.random.choice([0, 1, 2], size=n_samples, p=[0.7, 0.2, 0.1])
        
        # Error rate (mostly low)
        error_rate = np.random.exponential(scale=2, size=n_samples)
        error_rate = np.clip(error_rate, 0, 20)
        
        # Health status (1 = healthy, 0 = unhealthy)
        is_healthy = np.ones(n_samples, dtype=int)
        
        # Inject a few failure periods (~3% of time)
        n_failures = max(1, int(n_samples * 0.03 / 50))  # 3% of samples in 50-sample chunks
        for _ in range(n_failures):
            fail_start = np.random.randint(100, n_samples - 100)
            fail_length = np.random.randint(30, 70)
            
            # Mark as unhealthy
            is_healthy[fail_start:fail_start + fail_length] = 0
            
            # Ramp up stress indicators
            cpu, _, _ = simulate_failure_ramp(cpu, fail_start, fail_length, 20, 0, 100)
            memory, _, _ = simulate_failure_ramp(memory, fail_start, fail_length, 25, 0, 100)
            latency, _, _ = simulate_failure_ramp(latency, fail_start, fail_length, 300, 0, 2000)
            error_rate, _, _ = simulate_failure_ramp(error_rate, fail_start, fail_length, 50, 0, 100)
        
        # Create dataframe for this node
        for t in range(n_samples):
            data.append({
                'timestamp': time_index[t],
                'node_id': node_id,
                'client_type': client_type,
                'cpu_usage': cpu[t],
                'memory_usage': memory[t],
                'disk_io': disk_io[t],
                'latency_ms': latency[t],
                'block_height_gap': int(block_gap[t]),
                'error_rate': error_rate[t],
                'is_healthy': is_healthy[t]
            })
    
    df = pd.DataFrame(data)
    
    # Add failure_label column (0 = healthy, 1 = failure/unhealthy)
    # This is the inverse of is_healthy
    df['failure_label'] = (1 - df['is_healthy']).astype(int)
    
    print(f"✓ Generated {len(df)} total samples")
    print(f"✓ Node distribution: {df['node_id'].value_counts().to_dict()}")
    print(f"✓ Healthy samples: {(df['failure_label'] == 0).sum()}, Unhealthy: {(df['failure_label'] == 1).sum()}")
    
    return df

def main():
    """Main training pipeline"""
    print("=" * 60)
    print("Training ML Models with Real Node IDs")
    print("=" * 60)
    print()
    
    # Load config
    config = load_config('config.yaml')
    
    # Create directories
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    
    # Generate synthetic data with real node IDs
    raw_df = generate_data_for_real_nodes(n_samples=2880, nodes=REAL_NODES)
    
    # Save raw data
    raw_path = 'data/raw/synthetic_metrics.csv'
    raw_df.to_csv(raw_path, index=False)
    print(f"✓ Raw data saved to {raw_path}")
    print()
    
    # Engineer features
    print("🔧 Engineering features...")
    features_df = engineer_features(raw_df, config)
    
    processed_path = 'data/processed/engineered_metrics.csv'
    features_df.to_csv(processed_path, index=False)
    print(f"✓ Processed data saved to {processed_path}")
    print(f"✓ Feature columns: {len(features_df.columns)}")
    print()
    
    # Train models
    print("🤖 Training ML models...")
    print("=" * 60)
    train_models()
    
    print()
    print("=" * 60)
    print("✅ Training complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()

