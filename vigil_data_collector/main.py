import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.api.v1.router import api_router
from app.tasks.rpc_poller import poll_nodes_job

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize APScheduler
scheduler = AsyncIOScheduler()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Monitoring service for Solana RPC nodes with metrics collection and health tracking",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add rate limit state and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Initialize and start the background scheduler on application startup"""
    logger.info("=" * 60)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 60)
    logger.info(f"Poll interval: {settings.POLL_INTERVAL_SECONDS} seconds")
    logger.info(f"Request timeout: {settings.REQUEST_TIMEOUT_SECONDS} seconds")
    logger.info(f"Configured nodes: {list(settings.NODE_URLS.keys())}")
    logger.info(f"Simulated node: {settings.SIMULATED_NODE_NAME}")
    logger.info("=" * 60)
    
    # Add the polling job to the scheduler
    scheduler.add_job(
        poll_nodes_job,
        trigger=IntervalTrigger(seconds=settings.POLL_INTERVAL_SECONDS),
        id="rpc_node_polling",
        name="Poll RPC Nodes",
        replace_existing=True
    )
    
    # Start the scheduler
    scheduler.start()
    logger.info("APScheduler started successfully")
    
    # Run the first poll immediately
    logger.info("Running initial poll...")
    await poll_nodes_job()


@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully shutdown the scheduler on application shutdown"""
    logger.info("Shutting down scheduler...")
    scheduler.shutdown(wait=True)
    logger.info("Scheduler shutdown complete")


@app.get("/")
@limiter.limit("60/minute")
async def root(request: Request):
    """Root endpoint - Service information"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "endpoints": {
            "metrics": "/api/v1/metrics/latest-metrics",
            "docs": "/docs",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint (no rate limit for health checks)"""
    return {
        "status": "healthy",
        "scheduler_running": scheduler.running,
        "next_run": str(scheduler.get_jobs()[0].next_run_time) if scheduler.get_jobs() else None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
