# Vigil Collector Service

A FastAPI-based monitoring service for Solana RPC nodes that collects and provides real-time metrics via REST API. This service monitors both public RPC nodes and self-hosted nodes, tracking health, latency, slot numbers, and OS metrics.

## 🚀 Features

- **Asynchronous RPC Polling**: Concurrent monitoring of multiple Solana RPC nodes
- **Real-time Metrics Collection**: Latency, slot height, and health status tracking
- **OS Metrics Simulation**: CPU, memory, and disk I/O metrics for self-hosted nodes
- **Background Scheduling**: Automated polling using APScheduler
- **RESTful API**: Clean API for downstream analysis and routing components
- **Auto-generated Documentation**: Interactive Swagger UI and ReDoc
- **Configurable**: Environment-based configuration with Pydantic

## 📊 Monitored Metrics

### RPC Node Metrics

- **Latency** (ms): Round-trip time for RPC requests
- **Slot Number**: Current blockchain slot from the node
- **Health Status**: Binary indicator (1 = healthy, 0 = unhealthy)
- **Block Height Gap**: Slots behind the highest observed slot

### Node OS Metrics

- **CPU Usage** (%): CPU utilization (70-95%)
- **Memory Usage** (%): Memory consumption (60-85%)
- **Disk I/O** (%): Disk activity (5-25%, spikes to 60%)

## 🏗️ Project Structure

```
data_collector/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── metrics.py      # Metrics API endpoint
│   │       │   ├── users.py        # User endpoints (legacy)
│   │       │   └── items.py        # Item endpoints (legacy)
│   │       └── router.py           # API router configuration
│   ├── core/
│   │   └── config.py              # Configuration with Pydantic Settings
│   ├── schemas/
│   │   ├── metric.py              # NodeMetrics Pydantic model
│   │   ├── user.py                # User schemas (legacy)
│   │   └── item.py                # Item schemas (legacy)
│   └── tasks/
│       └── rpc_poller.py          # Background polling logic
├── main.py                        # FastAPI application & scheduler setup
├── requirements.txt               # Python dependencies
├── Procfile                       # Deployment configuration
├── .env.example                   # Example environment variables
└── README.md                      # This file
```

## ⚙️ Setup

### 1. Prerequisites

- Python 3.9+
- pip and venv

### 2. Clone and Navigate

```bash
cd data_collector
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

Edit `.env` with your RPC node URLs and configuration:

```env
# Solana RPC URLs
QUICKNODE_TESTNET_RPC_URL=https://your-quicknode-url.com
SOLANA_PUBLIC_TESTNET_RPC_URL=https://api.testnet.solana.com

# Polling Configuration
POLL_INTERVAL_SECONDS=15
REQUEST_TIMEOUT_SECONDS=8

# Node
NODE_NAME=agave_self_hosted
```

### 6. Run the Application

```bash
python3 main.py
```

Or using Uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📡 API Endpoints

### Primary Endpoints

#### Get Latest Metrics

```
GET /api/v1/metrics/latest-metrics
```

Returns the most recent metrics for all monitored nodes.

**Response Example:**

```json
[
  {
    "timestamp": "2023-10-15T12:30:00Z",
    "node_name": "quicknode_testnet",
    "latency_ms": 125.5,
    "slot": 234567890,
    "is_healthy": 1,
    "block_height_gap": 0,
    "cpu_usage": null,
    "memory_usage": null,
    "disk_io": null,
    "failure_imminent": null
  },
  {
    "timestamp": "2023-10-15T12:30:00Z",
    "node_name": "agave_self_hosted",
    "latency_ms": null,
    "slot": null,
    "is_healthy": 1,
    "block_height_gap": null,
    "cpu_usage": 82.5,
    "memory_usage": 73.2,
    "disk_io": 15.8,
    "failure_imminent": null
  }
]
```

### Service Endpoints

#### Root Endpoint

```
GET /
```

Returns service information and available endpoints.

#### Health Check

```
GET /health
```

Returns service health status and scheduler information.

### Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Configuration

All configuration is managed through environment variables loaded from `.env`:

| Variable                        | Description               | Default                       |
| ------------------------------- | ------------------------- | ----------------------------- |
| `APP_NAME`                      | Service name              | "Vigil Collector Service"     |
| `APP_VERSION`                   | Service version           | "1.0.0"                       |
| `HOST`                          | Server host               | "0.0.0.0"                     |
| `PORT`                          | Server port               | 8000                          |
| `QUICKNODE_TESTNET_RPC_URL`     | QuickNode RPC endpoint    | Required                      |
| `SOLANA_PUBLIC_TESTNET_RPC_URL` | Public Solana RPC         | Required                      |
| `HELIUS_TESTNET_RPC_URL`        | Helius RPC (optional)     | ""                            |
| `ALCHEMY_TESTNET_RPC_URL`       | Alchemy RPC (optional)    | ""                            |
| `NODE_NAME`           | Node identifier | "agave_self_hosted" |
| `POLL_INTERVAL_SECONDS`         | Polling frequency         | 15                            |
| `REQUEST_TIMEOUT_SECONDS`       | RPC request timeout       | 8                             |

## 🔄 How It Works

1. **Startup**: On application startup, APScheduler initializes and runs the first poll immediately
2. **Scheduled Polling**: Background job runs every `POLL_INTERVAL_SECONDS`
3. **Concurrent Queries**: All RPC nodes are queried concurrently using `httpx.AsyncClient`
4. **Metric Calculation**:
   - Latency is measured for each request
   - Highest slot number is determined across all healthy nodes
   - Block height gap is calculated for each node
   - OS metrics for the self-hosted node
5. **Caching**: All metrics are stored in an in-memory cache
6. **API Access**: Latest metrics are available via REST API

## 📝 Logging

The service provides comprehensive logging:

- **INFO**: Successful polls, node status, scheduler events
- **WARNING**: Non-200 responses, timeouts
- **ERROR**: Connection errors, parsing failures, exceptions

Logs include timestamps, node names, and detailed error information.

## 🚀 Deployment

### Using Procfile (Heroku, Render, etc.)

The included `Procfile` is configured for platform deployment:

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t vigil-collector .
docker run -p 8000:8000 --env-file .env vigil-collector
```

## 🧪 Testing

### Manual Testing

1. Start the service
2. Visit http://localhost:8000/docs
3. Try the `/api/v1/metrics/latest-metrics` endpoint
4. Monitor logs for polling activity

### Sample cURL Request

```bash
curl http://localhost:8000/api/v1/metrics/latest-metrics | jq
```

## 🛠️ Development

### Adding New RPC Nodes

Edit `.env` and add new URLs:

```env
HELIUS_TESTNET_RPC_URL=https://your-helius-url.com
```

The service will automatically include them in polling.

### Adjusting Polling Frequency

Change `POLL_INTERVAL_SECONDS` in `.env`:

```env
POLL_INTERVAL_SECONDS=30  # Poll every 30 seconds
```

### Modifying Simulation Logic

Edit `app/tasks/rpc_poller.py` in the `simulate_os_metrics()` function to adjust ranges or add new metrics.

## 🐛 Troubleshooting

### Service won't start

- Check that all dependencies are installed
- Verify `.env` file exists and has valid values
- Ensure port 8000 is not in use

### No metrics returned

- Wait for first poll to complete (check logs)
- Verify RPC URLs are accessible
- Check REQUEST_TIMEOUT_SECONDS isn't too low

### High error rates

- Increase REQUEST_TIMEOUT_SECONDS
- Verify RPC endpoints are operational
- Check network connectivity

## 📚 API Documentation

Full API documentation is available when the service is running:

- **Interactive docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

## 🤝 Contributing

1. Follow the existing code structure
2. Add type hints for all functions
3. Update documentation for new features
4. Test changes locally before deploying

## 📄 License

MIT License - Feel free to use this project as you wish!

## 🔗 Related Services

This collector service is designed to work with:

- **Analysis Service**: Processes collected metrics
- **Routing Service**: Makes routing decisions based on metrics
- **ML Service**: Predicts node failures

## 📞 Support

For issues or questions:

- Check the logs for detailed error messages
- Review the configuration in `.env`
- Consult the API documentation at `/docs`
