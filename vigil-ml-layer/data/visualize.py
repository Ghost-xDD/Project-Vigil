import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

def plot_full_timeseries(df: pd.DataFrame, node_id: str, output_dir: str):
    """Plots key metrics over the entire duration for a single node."""
    
    node_df = df[df['node_id'] == node_id].set_index('timestamp')
    if node_df.empty:
        print(f"No data found for node_id: {node_id}")
        return

    print(f"Plotting full timeseries for {node_id}...")
    
    fig, axes = plt.subplots(4, 1, figsize=(15, 12), sharex=True)
    
    # Plot key metrics
    node_df['cpu_usage'].plot(ax=axes[0], title='CPU Usage')
    node_df['latency_ms'].plot(ax=axes[1], title='RPC Latency (ms)')
    node_df['error_rate'].plot(ax=axes[2], title='Error Rate (%)')
    node_df['block_height_gap'].plot(ax=axes[3], title='Block Height Gap')
    
    for ax in axes:
        ax.set_ylabel('Metric Value')
    
    # Shade the failure region
    failure_periods = node_df[node_df['failure_label'] == 1].index
    for start in failure_periods:
        for ax in axes:
            ax.axvspan(start, start + pd.Timedelta(minutes=1), color='red', alpha=0.1)

    fig.suptitle(f'Full Timeseries for {node_id}', fontsize=16, y=1.02)
    plt.tight_layout()
    output_path = os.path.join(output_dir, f"{node_id}_full_timeseries.png")
    fig.savefig(output_path)
    print(f"Saved full timeseries plot to {output_path}")
    plt.close(fig)

def plot_failure_event(df: pd.DataFrame, node_id: str, output_dir: str):
    """Zooms in on the first failure event for a node and plots all metrics."""
    
    node_df = df[df['node_id'] == node_id].set_index('timestamp')
    if node_df.empty:
        print(f"No data found for node_id: {node_id}")
        return

    failure_start_time = node_df[node_df['failure_label'] == 1].index.min()
    
    if pd.isna(failure_start_time):
        print(f"No failure event found for {node_id}. Skipping plot.")
        return

    print(f"Plotting failure event for {node_id} around {failure_start_time}...")
    
    # Define a window around the failure
    plot_start = failure_start_time - pd.Timedelta(minutes=30)
    plot_end = failure_start_time + pd.Timedelta(minutes=150) # 120min ramp + 30min after
    
    event_df = node_df[plot_start:plot_end]
    
    metrics = ['cpu_usage', 'memory_usage', 'disk_io', 'error_rate', 'latency_ms', 'block_height_gap']
    
    fig, axes = plt.subplots(len(metrics), 1, figsize=(15, 18), sharex=True)
    
    for i, metric in enumerate(metrics):
        event_df[metric].plot(ax=axes[i], title=metric.replace('_', ' ').title())
        axes[i].set_ylabel('Metric Value')
        
        # Shade the failure region
        failure_periods = event_df[event_df['failure_label'] == 1].index
        for start in failure_periods:
            axes[i].axvspan(start, start + pd.Timedelta(minutes=1), color='red', alpha=0.05)

    fig.suptitle(f'Failure Event Analysis for {node_id}', fontsize=16, y=1.02)
    plt.xlabel('Timestamp')
    plt.tight_layout()
    output_path = os.path.join(output_dir, f"{node_id}_failure_event.png")
    fig.savefig(output_path)
    print(f"Saved failure event plot to {output_path}")
    plt.close(fig)

def plot_client_comparison(df: pd.DataFrame, output_dir: str):
    """Compares baseline 'healthy' latency between client types."""
    
    print("Plotting client comparison...")
    
    # Filter for healthy data only
    healthy_df = df[df['failure_label'] == 0].copy()
    
    if healthy_df.empty:
        print("No healthy data found for client comparison.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=healthy_df, x='client_type', y='latency_ms', ax=ax)
    
    ax.set_title('Baseline Healthy Latency by Client Type')
    ax.set_ylabel('Latency (ms)')
    ax.set_xlabel('Client Type')
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, "client_latency_comparison.png")
    fig.savefig(output_path)
    print(f"Saved client comparison plot to {output_path}")
    plt.close(fig)

def main():
    """Main function to load data and generate all plots."""
    
    # Get config from the root directory
    config_path = 'config.yaml'
    
    # This is a simple way to load the data file path
    # A full solution would use utils.load_config
    RAW_FILE_PATH = "sentry-ml-layer/data/raw/synthetic_metrics.csv"
    OUTPUT_DIR = "sentry-ml-layer/data"

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Set a nice style
    plt.style.use('seaborn-v0_8-darkgrid')

    # Check if data file exists
    if not os.path.exists(RAW_FILE_PATH):
        print(f"Error: Raw data file not found at {RAW_FILE_PATH}")
        print("Please run 'python data/synthetic-data.py' first to generate the data.")
        sys.exit(1)
        
    print(f"Loading data from {RAW_FILE_PATH}...")
    df = pd.read_csv(RAW_FILE_PATH)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Get a list of nodes
    node_ids = df['node_id'].unique()
    
    if len(node_ids) == 0:
        print("Error: No node_ids found in the data.")
        sys.exit(1)

    # --- Generate Plots ---
    
    # Plot full timeseries for one Agave and one Firedancer node
    agave_node = next((n for n in node_ids if 'agave' in n), node_ids[0])
    firedancer_node = next((n for n in node_ids if 'firedancer' in n), node_ids[0])

    plot_full_timeseries(df, agave_node, OUTPUT_DIR)
    plot_failure_event(df, agave_node, OUTPUT_DIR)
    
    if firedancer_node != agave_node:
        plot_full_timeseries(df, firedancer_node, OUTPUT_DIR)
        plot_failure_event(df, firedancer_node, OUTPUT_DIR)

    # Plot comparison
    plot_client_comparison(df, OUTPUT_DIR)
    
    print("\nVisualization script finished.")
    print(f"Plots saved in '{OUTPUT_DIR}' directory.")

if __name__ == "__main__":
    main()
