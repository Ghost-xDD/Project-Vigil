#!/bin/bash
# Vigil Services Log Viewer - Readable Format

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   Project Vigil - Live Logs Viewer        ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════╝${NC}"
echo ""

# Check if service argument provided
SERVICE=$1

if [ -z "$SERVICE" ]; then
    echo -e "${YELLOW}Usage:${NC}"
    echo "  ./logs.sh <service>    # View specific service"
    echo "  ./logs.sh all          # View all services"
    echo ""
    echo -e "${GREEN}Available services:${NC}"
    echo "  - data-collector"
    echo "  - ml-service"
    echo "  - intelligent-router"
    echo "  - all"
    echo ""
    exit 1
fi

echo -e "${GREEN}Streaming logs for: ${YELLOW}${SERVICE}${NC}"
echo -e "${CYAN}Press Ctrl+C to stop${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$SERVICE" == "all" ]; then
    # Color-coded multi-service logs
    docker compose logs -f --tail=50 | while IFS= read -r line; do
        if echo "$line" | grep -q "data-collector"; then
            echo -e "${CYAN}[DATA]${NC} $line"
        elif echo "$line" | grep -q "ml-service"; then
            echo -e "${GREEN}[ML]  ${NC} $line"
        elif echo "$line" | grep -q "intelligent-router"; then
            echo -e "${YELLOW}[ROUTER]${NC} $line"
        else
            echo "$line"
        fi
    done
else
    docker compose logs -f --tail=100 "$SERVICE"
fi

