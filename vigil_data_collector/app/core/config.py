from pydantic_settings import BaseSettings
from typing import List, Dict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Vigil Collector Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "sqlite:///./vigil.db"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Solana RPC Node URLs
    ANKR_DEVNET_RPC_URL: str = "https://api.devnet.solana.com"
    SOLANA_PUBLIC_DEVNET_RPC_URL: str = "https://api.devnet.solana.com"
    HELIUS_DEVNET_RPC_URL: str = ""  # Optional placeholder
    ALCHEMY_DEVNET_RPC_URL: str = ""  # Optional placeholder
    
    # Node Configuration
    SIMULATED_NODE_NAME: str = "agave_self_hosted"
    
    # Polling Configuration
    POLL_INTERVAL_SECONDS: int = 15
    REQUEST_TIMEOUT_SECONDS: int = 8
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def NODE_URLS(self) -> Dict[str, str]:
        """Dynamically create a dictionary of node names to their URLs"""
        urls = {
            "ankr_devnet": self.ANKR_DEVNET_RPC_URL,
            "solana_public_devnet": self.SOLANA_PUBLIC_DEVNET_RPC_URL,
        }
        
        # Add optional URLs if configured
        if self.HELIUS_DEVNET_RPC_URL:
            urls["helius_devnet"] = self.HELIUS_DEVNET_RPC_URL
        if self.ALCHEMY_DEVNET_RPC_URL:
            urls["alchemy_devnet"] = self.ALCHEMY_DEVNET_RPC_URL
        
        return urls


settings = Settings()

