#!/usr/bin/env python3
"""
Fix node IDs in the processed data to match real node names from Data Collector
"""
import pandas as pd
import sys

# Real node IDs from your Data Collector
REAL_NODE_IDS = [
    'ankr_devnet',
    'helius_devnet', 
    'alchemy_devnet',
    'solana_public_devnet',
    'agave_self_hosted'
]

def main():
    print("🔧 Fixing node IDs in processed data...")
    
    # Load processed data
    try:
        df = pd.read_csv('data/processed/engineered_metrics.csv')
        print(f"✓ Loaded {len(df)} rows")
    except FileNotFoundError:
        print("❌ engineered_metrics.csv not found!")
        sys.exit(1)
    
    # Get current unique node IDs
    current_nodes = sorted(df['node_id'].unique())
    print(f"\n📊 Current node IDs: {current_nodes}")
    print(f"📊 Real node IDs:    {sorted(REAL_NODE_IDS)}")
    
    # Create mapping (oldest to newest mapping)
    if len(current_nodes) != len(REAL_NODE_IDS):
        print(f"⚠️  Warning: Node count mismatch! {len(current_nodes)} != {len(REAL_NODE_IDS)}")
        # Adjust
        n = min(len(current_nodes), len(REAL_NODE_IDS))
        current_nodes = current_nodes[:n]
        real_nodes = sorted(REAL_NODE_IDS)[:n]
    else:
        real_nodes = sorted(REAL_NODE_IDS)
    
    node_mapping = {old: new for old, new in zip(current_nodes, real_nodes)}
    
    print(f"\n🔄 Mapping:")
    for old, new in node_mapping.items():
        print(f"   {old:20s} → {new}")
    
    # Apply mapping
    df['node_id'] = df['node_id'].map(node_mapping)
    
    # Update client_type based on node name
    def infer_client_type(node_id):
        if 'agave' in node_id.lower():
            return 'agave'
        # Most providers run Agave
        return 'agave'
    
    df['client_type'] = df['node_id'].apply(infer_client_type)
    
    # Save updated data
    df.to_csv('data/processed/engineered_metrics.csv', index=False)
    print(f"\n✓ Updated data saved!")
    print(f"✓ New unique nodes: {sorted(df['node_id'].unique())}")
    
    # Also update raw data if it exists
    try:
        raw_df = pd.read_csv('data/raw/synthetic_metrics.csv')
        raw_current_nodes = sorted(raw_df['node_id'].unique())
        raw_mapping = {old: new for old, new in zip(raw_current_nodes, real_nodes)}
        raw_df['node_id'] = raw_df['node_id'].map(raw_mapping)
        raw_df['client_type'] = raw_df['node_id'].apply(infer_client_type)
        raw_df.to_csv('data/raw/synthetic_metrics.csv', index=False)
        print(f"✓ Raw data also updated!")
    except FileNotFoundError:
        pass
    
    print("\n✅ Node IDs fixed! Now retrain models with: python -m src.train")

if __name__ == "__main__":
    main()

