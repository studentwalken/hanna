"""
Application configuration settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
from datetime import timedelta


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "SMS Gateway System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "local"  # local, cloud
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/sms_gateway"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Rate Limiting
    DEFAULT_RATE_LIMIT: int = 100  # messages per hour
    ADMIN_RATE_LIMIT: int = 1000  # messages per hour for admins
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["csv", "xlsx", "xls"]
    
    # Redis (for Celery and caching)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Telegram Bot (optional)
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    TELEGRAM_ENABLED: bool = False
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds
    
    # SMS Settings
    DEFAULT_SEND_DELAY_MIN: int = 1  # seconds
    DEFAULT_SEND_DELAY_MAX: int = 3  # seconds
    MAX_BULK_MESSAGES: int = 10000  # maximum messages per bulk operation
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 500
    
    # Log retention (days)
    LOG_RETENTION_DAYS: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
