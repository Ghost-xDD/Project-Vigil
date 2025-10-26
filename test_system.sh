#!/bin/bash
# Test the complete Project Vigil system

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   Project Vigil - System Test             ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════╝${NC}"
echo ""

# Test 1: Service Health
echo -e "${YELLOW}1. Checking service health...${NC}"
echo -n "   Data Collector: "
if curl -s http://localhost:8000/health | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ HEALTHY${NC}"
else
    echo -e "${RED}✗ UNHEALTHY${NC}"
fi

echo -n "   ML Service:     "
if curl -s http://localhost:8001/health | jq -e '.models_loaded == true' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ HEALTHY (models loaded)${NC}"
else
    echo -e "${RED}✗ UNHEALTHY or models not loaded${NC}"
fi

echo -n "   Router:         "
if curl -s http://localhost:8080/health | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ HEALTHY${NC}"
else
    echo -e "${RED}✗ UNHEALTHY${NC}"
fi

echo ""

# Test 2: Data Collection
echo -e "${YELLOW}2. Checking data collection...${NC}"
HISTORY_COUNT=$(curl -s 'http://localhost:8000/api/v1/metrics/history?limit=20' | jq '. | length')
echo "   Historical data points: $HISTORY_COUNT"

if [ "$HISTORY_COUNT" -ge 75 ]; then
    echo -e "   ${GREEN}✓ Sufficient history for ML predictions${NC}"
else
    NEEDED=$((75 - HISTORY_COUNT))
    WAIT_TIME=$(((NEEDED / 5) * 15))
    echo -e "   ${YELLOW}⏳ Need $NEEDED more points (~$WAIT_TIME seconds)${NC}"
fi

echo ""

# Test 3: ML Models
echo -e "${YELLOW}3. Checking ML models...${NC}"
MODELS=$(curl -s http://localhost:8001/models | jq -r '.latency_models[]' 2>/dev/null)
if [ -n "$MODELS" ]; then
    echo -e "   ${GREEN}✓ Latency models loaded:${NC}"
    echo "$MODELS" | while read model; do echo "     - $model"; done
else
    echo -e "   ${RED}✗ No latency models${NC}"
fi

echo ""

# Test 4: End-to-End RPC Request
echo -e "${YELLOW}4. Testing end-to-end RPC request...${NC}"
RESPONSE=$(curl -s -X POST http://localhost:8080/rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"getSlot"}')

if echo "$RESPONSE" | jq -e '.result' > /dev/null 2>&1; then
    SLOT=$(echo "$RESPONSE" | jq -r '.result')
    echo -e "   ${GREEN}✓ RPC request successful${NC}"
    echo "   Current slot: $SLOT"
else
    echo -e "   ${RED}✗ RPC request failed${NC}"
    echo "   Response: $RESPONSE"
fi

echo ""

# Test 5: Check Routing Decision
echo -e "${YELLOW}5. Checking routing decision...${NC}"
LAST_ROUTE=$(docker compose logs intelligent-router 2>&1 | grep "Routing to recommended node" | tail -1)
if [ -z "$LAST_ROUTE" ]; then
    echo -e "   ${YELLOW}⚠️  No routing decisions found yet${NC}"
    echo "   Try sending an RPC request first"
else
    # Extract node name from the log line (format: "node":"alchemy_devnet")
    NODE=$(echo "$LAST_ROUTE" | grep -o '"node":"[^"]*"' | cut -d'"' -f4)
    if [ -z "$NODE" ] || [ "$NODE" = "" ]; then
        echo -e "   ${YELLOW}⚠️  Using FALLBACK (ML returned empty)${NC}"
    else
        echo -e "   ${GREEN}✓ ML-recommended node: $NODE${NC}"
    fi
fi

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "💡 Tips:"
echo "  - Use ./logs.sh to watch live logs"
echo "  - Wait 4-5 minutes for history to accumulate"
echo "  - Run this script again to retest"
echo ""

