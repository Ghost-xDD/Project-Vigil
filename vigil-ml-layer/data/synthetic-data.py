import pandas as pd
import numpy as np
import os

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
    
    # Clip to ensure values stay within a reasonable range
    series = np.clip(series, clip_min, clip_max)
    return series, start_idx, start_idx + length

def generate_data(n_samples=2000, n_nodes=5):
    """
    Generates synthetic RPC node metrics data.
    
    Args:
        n_samples (int): Number of time steps per node.
        n_nodes (int): Number of nodes to simulate.
        
    Returns:
        pd.DataFrame: A DataFrame with synthetic metrics.
    """
    print(f"Generating synthetic data for {n_nodes} nodes, {n_samples} samples each...")
    
    data = []
    base_timestamp = pd.to_datetime('2025-10-01 00:00:00')
    time_index = pd.date_range(start=base_timestamp, periods=n_samples, freq='T') # 1-minute frequency

    agave_count = 1
    firedancer_count = 1

    for i in range(n_nodes):
        
        # Alternate client types and name nodes accordingly
        if i % 2 == 0:
            client_type = 'agave'
            node_id = f'agave{agave_count}'
            agave_count += 1
        else:
            client_type = 'firedancer'
            node_id = f'firedancer{firedancer_count}'
            firedancer_count += 1
        
        # 1. Generate baseline AR(1) processes
        # CPU: High autocorrelation
        cpu_base = generate_ar1_series(n_samples, phi=0.9, mean=0.5, std_dev=0.2)
        cpu = scale_to_range(cpu_base, 20, 60) # Normal CPU 20-60%
        
        # Memory: Very high autocorrelation
        mem_base = generate_ar1_series(n_samples, phi=0.98, mean=0.6, std_dev=0.1)
        mem = scale_to_range(mem_base, 40, 70) # Normal Mem 40-70%
        
        # Error Rate: Low autocorrelation (spiky)
        err_base = generate_ar1_series(n_samples, phi=0.3, mean=0.1, std_dev=0.3)
        err = scale_to_range(err_base, 0, 5) # Normal errors 0-5%
        err = np.clip(err, 0, 100) # Ensure no negative errors

        # Disk I/O: Spiky, medium autocorrelation
        disk_io_base = generate_ar1_series(n_samples, phi=0.4, mean=0.3, std_dev=0.4)
        disk_io = scale_to_range(disk_io_base, 5, 30) # Normal 5-30 MB/s
        disk_io = np.clip(disk_io, 0, 100)

        # Block Height Gap: Normally low, high autocorrelation
        block_gap_base = generate_ar1_series(n_samples, phi=0.6, mean=0.1, std_dev=0.2)
        block_height_gap = scale_to_range(block_gap_base, 0, 2) # Normally 0-2 blocks
        block_height_gap = np.round(block_height_gap).astype(int) # Gaps are integer
        block_height_gap = np.clip(block_height_gap, 0, 500)

        # 2. Simulate failures
        failure_label = np.zeros(n_samples, dtype=int)
        
        # Simulate one failure event per node
        failure_duration = 120 # 2-hour failure ramp
        failure_start = np.random.randint(n_samples // 4, n_samples - failure_duration - 10)
        
        print(f"  Simulating failure for {node_id} starting at index {failure_start} for {failure_duration} steps.")
        
        # Apply ramps leading to failure
        cpu, _, _ = simulate_failure_ramp(cpu, failure_start, failure_duration, ramp_max=40, clip_max=100) # Ramps to 100%
        mem, _, _ = simulate_failure_ramp(mem, failure_start, failure_duration, ramp_max=30, clip_max=100) # Ramps to 100%
        disk_io, _, _ = simulate_failure_ramp(disk_io, failure_start, failure_duration, ramp_max=20, clip_max=100) # Ramps to ~50MB/s
        block_height_gap, _, _ = simulate_failure_ramp(block_height_gap, failure_start, failure_duration, ramp_max=50, clip_min=0, clip_max=500) # Ramps to ~50 blocks
        err, fail_start_idx, fail_end_idx = simulate_failure_ramp(err, failure_start, failure_duration, ramp_max=20, clip_max=100) # Ramps to 25%
        
        # Mark the failure period
        failure_label[fail_start_idx:fail_end_idx] = 1

        # 3. Generate Latency
        # Latency is correlated with all stress indicators
        latency_base = (cpu * 0.5) + \
                       (err * 2) + \
                       (disk_io * 0.2) + \
                       (block_height_gap * 1) + \
                       np.random.normal(0, 10, n_samples)
        latency = scale_to_range(latency_base, 50, 150) # Normal latency 50-150ms
        
        # Add extra noise and spikes during failure
        failure_noise = np.zeros(n_samples)
        failure_noise[fail_start_idx:fail_end_idx] = np.random.normal(50, 20, fail_end_idx - fail_start_idx) + \
                                                    np.abs(err[fail_start_idx:fail_end_idx] * 5)
        latency = latency + failure_noise
        latency = np.clip(latency, 10, 2000) # Clip latency (min 10ms, max 2s)

        # 4. Create DataFrame
        node_df = pd.DataFrame({
            'timestamp': time_index,
            'node_id': node_id, # Updated node_id
            'client_type': client_type, # Still included for downstream scripts
            'cpu_usage': cpu,
            'memory_usage': mem,
            'disk_io': disk_io, # New
            'error_rate': err,
            'latency_ms': latency,
            'block_height_gap': block_height_gap, # New
            'failure_label': failure_label
        })
        data.append(node_df)

    final_df = pd.concat(data)
    return final_df.reset_index(drop=True)

if __name__ == "__main__":
    # Configuration
    RAW_DATA_DIR = "data/raw"
    PROCESSED_DATA_DIR = "data/processed"
    RAW_FILE_PATH = os.path.join(RAW_DATA_DIR, "synthetic_metrics.csv")
    PROCESSED_FILE_PATH = os.path.join(PROCESSED_DATA_DIR, "engineered_metrics.csv")

    # Create directories if they don't exist
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

    # Generate and save raw data
    raw_df = generate_data(n_samples=2880, n_nodes=4) # 2880 minutes = 2 days
    raw_df.to_csv(RAW_FILE_PATH, index=False)
    print(f"Raw synthetic data saved to {RAW_FILE_PATH}")
    
    # --- Feature Engineering Step ---
    # This is often a separate script, but for simplicity, we do it here.
    # In a real pipeline, `train.py` would read from the 'processed' file.
    
    # We load the "raw" data we just saved to simulate a real pipeline
    from src.features import engineer_features
    from src.utils import load_config
    
    # Set up a minimal logger for the feature engineering step
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    config = load_config()
    print("Running feature engineering...")
    features_df = engineer_features(raw_df, config=config)
    
    # Save processed data
    features_df.to_csv(PROCESSED_FILE_PATH, index=False)
    print(f"Processed data with engineered features saved to {PROCESSED_FILE_PATH}")