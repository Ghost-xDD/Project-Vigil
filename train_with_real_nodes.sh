#!/bin/bash
# Train ML models using real node IDs from the Data Collector

set -e

echo "╔════════════════════════════════════════════════════╗"
echo "║  Training ML Models with Real Node IDs             ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Get current node IDs from Data Collector
echo "📊 Fetching current node IDs from Data Collector..."
NODES=$(curl -s http://localhost:8000/api/v1/metrics/latest-metrics | jq -r '.[].node_name' | sort -u)

if [ -z "$NODES" ]; then
    echo "❌ Could not fetch node IDs. Is Data Collector running?"
    exit 1
fi

echo "✓ Found nodes:"
echo "$NODES" | while read node; do echo "  - $node"; done
echo ""

# Copy training script into container and run it
echo "🔧 Training models in ML service container..."
echo ""

docker compose cp vigil-ml-layer/train_real_nodes.py ml-service:/app/train_real_nodes.py

docker compose exec ml-service bash -c "
cd /app
python train_real_nodes.py
"

echo ""
echo "🔄 Restarting ML service to load new models..."
docker compose restart ml-service

echo ""
echo "⏳ Waiting for ML service to start..."
sleep 10

# Verify
echo ""
echo "✅ Checking model status..."
curl -s http://localhost:8001/models | jq .

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║  ✓ Models retrained with real node IDs!           ║"
echo "╚════════════════════════════════════════════════════╝"

