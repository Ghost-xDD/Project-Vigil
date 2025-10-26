# Vigil Dashboard - Development Guide

## Project Overview

Build a real-time web dashboard that visualizes Project Vigil's ML-powered intelligent RPC routing system. The dashboard should demonstrate how ML predictions optimize node selection for Solana RPC requests.

---

## Core Objective

**Show the power of ML-driven routing vs traditional round-robin routing**

The dashboard must make it immediately obvious that:

1. ML is making intelligent decisions (not random)
2. Predictions are accurate and fast
3. System avoids degraded nodes proactively
4. Business impact is measurable (faster, more reliable, cheaper)

---

## Technical Stack (Recommended)

**Frontend:**

- React 18+ with TypeScript
- Recharts or Chart.js for visualizations
- Tailwind CSS for styling
- shadcn/ui for components (optional, for polish)

**Backend:**

- Use existing FastAPI endpoints (already built)
- WebSockets or SSE for real-time updates (optional)
- Polling every 2-3 seconds is acceptable

**Deployment:**

- Docker container (add to existing docker-compose.yml)
- Nginx to serve static files
- Port 3000

---

## Page Layout

### Single-Page Dashboard (Split into 4 Quadrants)

```
┌─────────────────────┬─────────────────────┐
│   Routing Engine    │   Node Health       │
│   (Main Decision)   │   (5 Node Cards)    │
│                     │                     │
├─────────────────────┼─────────────────────┤
│   Prediction Chart  │   Feature           │
│   (Accuracy)        │   Importance        │
└─────────────────────┴─────────────────────┘
```

---

## Components to Build

### 1. Routing Engine Panel (Top-Left)

**Purpose:** Show the ML decision in action

**Display:**

- Large recommended node name (e.g., "ankr_devnet")
- Predicted latency with confidence
- Failure probability percentage
- Cost score
- Simple animation when decision updates

**Data Source:**

- Poll router logs or create new endpoint: `GET /api/current-recommendation`
- Update every 2-3 seconds

**Visual:**

- Card with large text
- Green checkmark for healthy recommendation
- Pulse animation on update

---

### 2. Node Health Grid (Top-Right)

**Purpose:** Show all 5 nodes at a glance

**For Each Node Display:**

- Node name
- Health status (🟢 healthy, 🟡 degraded, 🔴 failing)
- Current latency (from data collector)
- Predicted next latency (from ML)
- Simple health bar (0-100 score)

**Data Source:**

- `GET http://localhost:8000/api/v1/metrics/latest-metrics` (data collector)
- `POST http://localhost:8001/predict` (ML predictions)

**Visual:**

- 5 cards in grid
- Color-coded borders
- Small sparkline showing latency trend (optional)

---

### 3. Prediction Accuracy Chart (Bottom-Left)

**Purpose:** Prove ML predictions are accurate

**Display:**

- Line chart: last 30-50 data points
- Two lines: "Predicted Latency" (solid) vs "Actual Latency" (dotted)
- Show MAE and MAPE metrics below chart
- Time on x-axis, latency (ms) on y-axis

**Data Source:**

- Store predictions and actual outcomes in memory/database
- Simple approach: Local state array of last 50 predictions

**Visual:**

- Recharts LineChart with two series
- Tooltip showing exact values on hover
- Legend showing which line is which

---

### 4. Feature Importance Panel (Bottom-Right)

**Purpose:** Show what's driving ML decisions

**Display:**

- Horizontal bar chart of top 10 features
- Percentage importance for each
- Label showing if it's "Temporal" or "Current"
- Optional: Real-time highlight of features currently "firing"

**Data Source:**

- Static data from model training (feature*importances*)
- Or create endpoint: `GET /api/feature-importance`

**Visual:**

- Simple horizontal bars
- Color-coded by feature type
- Text showing insight (e.g., "Error rate is top predictor")

---

## Key Features to Implement

### Must-Have (MVP)

1. **Real-time updates** - Poll every 2-3 seconds
2. **Routing decision display** - Clear which node is selected
3. **Health indicators** - Visual status for each node
4. **Prediction chart** - Show ML is accurate

### Nice-to-Have (Phase 2)

1. **Chaos mode button** - Simulate node failure, watch ML react
2. **Time slider** - Replay last 24 hours of decisions
3. **A/B comparison toggle** - With ML vs Without ML side-by-side
4. **Export metrics** - Download CSV of routing decisions

### Future Enhancements

1. **WebSocket support** - True real-time updates
2. **Historical analytics** - Weekly/monthly views
3. **Alerting** - Notify when degradation detected
4. **Multi-tenant** - Dashboard per customer

---

## API Endpoints Needed

### Already Exist ✅

- `GET http://localhost:8000/api/v1/metrics/latest-metrics` - Node metrics
- `GET http://localhost:8000/api/v1/metrics/history?limit=50` - Historical data
- `POST http://localhost:8001/predict` - ML predictions
- `GET http://localhost:8001/models` - Model info
- `POST http://localhost:8080/rpc` - Actual RPC routing

### To Create (Optional)

- `GET /api/current-decision` - Latest routing decision with details
- `GET /api/feature-importance` - Top features for current decision
- `GET /api/stats` - Aggregated performance stats

---

## Design Guidelines

### Style

- **Dark theme** preferred (looks more sophisticated for ML/data)
- **Neon accents** for key metrics (green for good, amber for warning)
- **Monospace fonts** for numbers/latencies
- **Clean, minimal** - focus on data, not decoration

### Colors

- 🟢 Green: Healthy nodes, good predictions
- 🟡 Amber: Warning/degraded
- 🔴 Red: Failures/critical
- 🔵 Blue: ML insights/information
- 🟣 Purple: Feature importance/technical details

### Animation

- **Subtle** - fade transitions between states
- **Purposeful** - pulse when new decision made
- **Not distracting** - no constant motion

---

## Example User Flow

1. **Dashboard loads** → Shows current state of all 5 nodes
2. **Every 2 seconds** → Poll for updates, smooth transition
3. **New request comes in** → Routing panel pulses, shows decision
4. **User can see:**
   - Which node was chosen (e.g., ankr_devnet)
   - Why it was chosen (lowest cost score)
   - How accurate past predictions were (chart)
   - What features matter most (bar chart)

---

## Success Criteria

The dashboard should make a non-technical viewer say:

> "Oh wow, it's actually predicting and choosing the best node in real-time!"

The dashboard should make a technical viewer say:

> "The ML is clearly working - predictions track actuals closely,
> and it's using temporal features intelligently."

---

## Development Approach

### Phase 1: Static Mock (Day 1)

- Build UI with fake data
- Get design/layout approved
- No API calls yet

### Phase 2: Live Data (Day 2)

- Connect to real APIs
- Real-time polling
- Actual predictions flowing through

### Phase 3: Polish (Day 3)

- Animations and transitions
- Error handling
- Responsive design
- Deploy to Docker

---

## API Data Structure Reference

### Latest Metrics Response

```json
[
  {
    "timestamp": "2025-10-26T14:00:00Z",
    "node_name": "ankr_devnet",
    "latency_ms": 92.5,
    "is_healthy": 1,
    "cpu_usage": 72.0,
    "memory_usage": 65.0,
    "error_rate": 1.2
  }
]
```

### Prediction Response

```json
{
  "recommended_node": "ankr_devnet",
  "explanation": "Recommending ankr_devnet (Cost: 0.064)...",
  "all_predictions": [
    {
      "node_id": "ankr_devnet",
      "predicted_latency_ms": 92.4,
      "failure_prob": 0.0016,
      "cost_score": 0.064
    }
  ]
}
```

---

## Deployment

Add to `docker-compose.yml`:

```yaml
dashboard:
  build: ./vigil-dashboard
  ports:
    - '3000:80'
  depends_on:
    - data-collector
    - ml-service
    - intelligent-router
  environment:
    - API_DATA_COLLECTOR=http://data-collector:8000
    - API_ML_SERVICE=http://ml-service:8001
    - API_ROUTER=http://intelligent-router:8080
```

---

## File Structure

```
vigil-dashboard/
├── Dockerfile
├── nginx.conf
├── public/
│   └── index.html
├── src/
│   ├── App.tsx
│   ├── components/
│   │   ├── RoutingEngine.tsx
│   │   ├── NodeHealthGrid.tsx
│   │   ├── PredictionChart.tsx
│   │   └── FeatureImportance.tsx
│   ├── hooks/
│   │   ├── useNodeMetrics.ts
│   │   └── usePredictions.ts
│   └── utils/
│       └── api.ts
├── package.json
└── README.md
```

---

## Success Metrics

After building, the dashboard should:

✅ **Update in real-time** - New data every 2-3 seconds  
✅ **Show ML intelligence** - Clear that predictions drive routing  
✅ **Be visually appealing** - Professional, modern UI  
✅ **Tell the story** - "ML makes better routing decisions"  
✅ **Work on mobile** - Responsive design (bonus)

---

## 🚀 Quick-Win MVP (Build This First)

### **Minimal Viable Demo** (2-3 hours to build)

**Single HTML page with:**

1. **Header**

   - Logo/title: "ML-Powered RPC Routing"
   - Live status indicator

2. **Main Panel: Live Routing Decision**

   - Updates every 2 seconds
   - Show recommended node in large text
   - Show predicted latency
   - Pulse animation when new decision made

3. **Node Grid: 5 Boxes**

   - One card per node
   - Color-coded by health (🟢 green / 🟡 yellow / 🔴 red)
   - Display current latency

4. **Simple Line Chart**

   - Last 20 predictions vs actual
   - Two-line graph (predicted vs reality)

5. **Stats Footer**
   - Total requests today
   - Success rate percentage
   - Average latency

**Tech Stack:**

- Single HTML file (no build step)
- Vanilla JavaScript (no frameworks)
- Chart.js for graphs
- Fetch API for data (every 2 sec)
- CSS Grid for layout

**Why This First:**

- ✅ **Impressive** - Shows live ML in action
- ✅ **Fast** - 2-3 hours total build time
- ✅ **No dependencies** - Just HTML/JS/CSS
- ✅ **Easy deploy** - Serve from Nginx, add to docker-compose

---

## 🎯 Recommended: "Comparison Demo"

### **Why Build This Second:**

1. **Clear value proposition** - "40% faster, 100% more reliable"
2. **Visual impact** - Side-by-side is powerful for sales
3. **Sales-ready** - Perfect for B2B pitch to RPC providers
4. **Simple to build** - Two panels, same data, different logic

### **Layout:**

```
┌─────────────────────────────────────────────────────────┐
│         WITHOUT VIGIL    vs    WITH VIGIL               │
├───────────────────────────┬─────────────────────────────┤
│ 🔀 Random Routing         │ 🎯 ML-Powered Routing       │
│                           │                             │
│ Avg Latency: 156ms        │ Avg Latency: 94ms ⚡        │
│ Failures: 3/100           │ Failures: 0/100 ✅          │
│ P95: 280ms                │ P95: 125ms                  │
│ Success: 97%              │ Success: 100% 🎯            │
│                           │                             │
│ [Live chart with delays]  │ [Live chart optimized]      │
│                           │                             │
│ Cost: $1,200/mo           │ Cost: $840/mo 💰            │
└───────────────────────────┴─────────────────────────────┘

          [Switch to Live View →]
```

**Implementation:**

- Simulate "random routing" by picking random nodes
- Compare against actual ML routing
- Show metrics updating in real-time
- Calculate cost savings based on request volume

---

## 🎪 Phase 2 Enhancements

### **1. Chaos Mode Button** 🔥

**Feature:**

```
[Simulate Node Failure] button
```

**Behavior:**

- Inject fake high error rate / CPU spike into one node
- Watch dashboard show degradation (yellow → red)
- ML automatically reroutes traffic away
- Display: "Failure detected in 12s, traffic rerouted ✅"
- Auto-recover after 30 seconds

**Impact:** Shows proactive detection vs reactive

### **2. Historical Replay Slider** ⏰

**Feature:**

```
[◄◄] [▶] [►►]  [====•========] 00:00 → 24:00
```

**Behavior:**

- Scrub through last 24 hours of data
- See how ML adapted to changing conditions
- Highlight key events: "14:32 - Detected alchemy degradation"
- Speed controls (1x, 5x, 10x playback)

**Impact:** Shows learning and adaptation over time

### **3. Feature Importance Panel** 📊

**Feature:**

```
Top Drivers Right Now:
🔴 error_rate_rolling    ████████ 8.2%
🟡 cpu_usage_mean        ██████   5.8%
🟢 memory_pressure       ████     4.1%
```

**Behavior:**

- Updates based on current decision
- Highlights which features are "firing"
- Tooltip explains what each feature means

**Impact:** Shows ML intelligence and interpretability

---

## Timeline Estimate

**MVP (Quick-Win):**

- Day 1: Build basic dashboard (2-3 hours)
- Deploy and demo ✅

**Comparison Demo:**

- Day 2: Add side-by-side view (3-4 hours)
- Polish for sales demos ✅

**Phase 2 Enhancements:**

- Week 2: Chaos mode + Historical replay (6-8 hours)
- Week 3: Feature importance + polish (4-6 hours)

**Total: 2-3 weeks for fully-featured demo dashboard**

---

## Delivery Checklist

Before showing to investors/customers:

- [ ] Dashboard updates in real-time (< 3 sec latency)
- [ ] ML routing decision is clear and prominent
- [ ] Comparison view shows measurable improvement
- [ ] All 5 nodes visible with health status
- [ ] Chart shows prediction accuracy
- [ ] No errors in console
- [ ] Mobile responsive
- [ ] Professional dark theme
- [ ] Works in demo mode (even without live data)

---

**This dashboard will be your killer demo - simple, powerful, and tells the complete story of ML-powered routing.**
