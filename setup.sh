#!/bin/bash
# Setup script for Project Vigil - Creates .env files from examples

set -e

echo "====================================="
echo "  Project Vigil - Setup Script"
echo "====================================="
echo ""

# Function to create .env from .env.example if it doesn't exist
create_env_file() {
    local dir=$1
    local service=$2
    
    if [ -f "$dir/.env" ]; then
        echo "✓ $service: .env already exists (skipping)"
    else
        if [ -f "$dir/.env.example" ]; then
            cp "$dir/.env.example" "$dir/.env"
            echo "✓ $service: Created .env from .env.example"
            echo "  → Please edit $dir/.env with your API keys"
        else
            echo "✗ $service: .env.example not found"
        fi
    fi
}

# Create .env files for each service
echo "Creating .env files from templates..."
echo ""

create_env_file "data_collector" "Data Collector"
create_env_file "vigil-intelligent-router" "Intelligent Router"

echo ""
echo "====================================="
echo "  Setup Complete!"
echo "====================================="
echo ""
echo "⚠️  IMPORTANT: Update the following .env files with your real API keys:"
echo ""
echo "1. data_collector/.env"
echo "   - ANKR_DEVNET_RPC_URL"
echo "   - HELIUS_DEVNET_RPC_URL"
echo "   - ALCHEMY_DEVNET_RPC_URL"
echo ""
echo "2. vigil-intelligent-router/.env"
echo "   - ANKR_DEVNET_RPC_URL"
echo "   - HELIUS_DEVNET_RPC_URL"
echo "   - ALCHEMY_DEVNET_RPC_URL"
echo ""
echo "⚠️  NEVER commit .env files to version control!"
echo ""
echo "Next steps:"
echo "  1. Edit the .env files with your API keys"
echo "  2. Start services: docker-compose up -d"
echo "  3. Check logs: docker-compose logs -f"
echo ""

