from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class NodeMetrics(BaseModel):
    """Schema for node metrics data"""
    
    timestamp: datetime = Field(..., description="UTC timestamp of collection")
    node_name: str = Field(..., description="Identifier for the node (e.g., quicknode_testnet)")
    latency_ms: Optional[float] = Field(None, description="Measured RPC request latency in milliseconds")
    slot: Optional[int] = Field(None, description="Reported slot number from the node")
    is_healthy: int = Field(..., description="1 for successful query, 0 for failure/timeout")
    block_height_gap: Optional[int] = Field(None, description="Slots behind the highest observed slot")
    cpu_usage: Optional[float] = Field(None, description="CPU usage percentage")
    memory_usage: Optional[float] = Field(None, description="Memory usage percentage")
    disk_io: Optional[float] = Field(None, description="Disk I/O busy percentage")
    failure_imminent: Optional[bool] = Field(None, description="Placeholder for downstream ML prediction")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "timestamp": "2023-10-15T12:30:00Z",
                "node_name": "quicknode_testnet",
                "latency_ms": 125.5,
                "slot": 234567890,
                "is_healthy": 1,
                "block_height_gap": 0,
                "cpu_usage": None,
                "memory_usage": None,
                "disk_io": None,
                "failure_imminent": None
            }
        }

