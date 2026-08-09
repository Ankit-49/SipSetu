import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "SipSetu"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # Security
    JWT_SECRET_KEY: str = os.environ.get(
        'JWT_SECRET_KEY',
        'sipsetu-dev-jwt-secret-change-in-production'
    )
    JWT_ALGORITHM: str = 'HS256'
    JWT_EXPIRATION_HOURS: int = 24
    
    # Database
    DATABASE_URL: str = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/sipsetu'
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 300
    
    # Redis
    REDIS_URL: Optional[str] = os.environ.get('REDIS_URL')
    
    # CORS
    FRONTEND_URL: str = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    
    # Email (SMTP)
    SMTP_HOST: Optional[str] = os.environ.get('SMTP_HOST')
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = os.environ.get('SMTP_USER')
    SMTP_PASSWORD: Optional[str] = os.environ.get('SMTP_PASSWORD')
    SMTP_USE_TLS: bool = True
    SMTP_FROM: str = os.environ.get('SMTP_FROM', 'noreply@sipsetu.com')
    
    # Storage
    STORAGE_PROVIDER: str = os.environ.get('STORAGE_PROVIDER', 'local')  # local, s3, minio
    STORAGE_BUCKET: str = os.environ.get('STORAGE_BUCKET', 'sipsetu-uploads')
    STORAGE_REGION: str = os.environ.get('STORAGE_REGION', 'us-east-1')
    STORAGE_ENDPOINT_URL: Optional[str] = os.environ.get('STORAGE_ENDPOINT_URL')
    STORAGE_ACCESS_KEY: Optional[str] = os.environ.get('STORAGE_ACCESS_KEY')
    STORAGE_SECRET_KEY: Optional[str] = os.environ.get('STORAGE_SECRET_KEY')
    LOCAL_STORAGE_PATH: str = os.environ.get('LOCAL_STORAGE_PATH', '/tmp/sipsetu-uploads')
    
    # Rate Limiting
    RATE_LIMIT_DEFAULT: str = "200 per minute"
    RATE_LIMIT_AUTH: str = "10 per minute"
    
    # ML Model
    ML_MODEL_DIR: str = os.environ.get('ML_MODEL_DIR', 'ml_artifacts')
    ML_MIN_TRAINING_ROWS: int = 15
    ML_MAX_ALPHA: float = 0.8
    
    # File Upload
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_EXTENSIONS: list = ['.pdf', '.docx', '.txt']
    
    # Monitoring
    SENTRY_DSN: Optional[str] = os.environ.get('SENTRY_DSN')
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json, text
    
    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse SMTP_PORT if set
        smtp_port = os.environ.get('SMTP_PORT')
        if smtp_port:
            self.SMTP_PORT = int(smtp_port)
        
        # Set Celery URLs from Redis if not explicitly set
        if self.REDIS_URL and not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if self.REDIS_URL and not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL


# Global settings instance
settings = Settings()


# Backward compatibility class for existing code
class Config:
    SECRET_KEY = settings.JWT_SECRET_KEY
    JWT_ALGORITHM = settings.JWT_ALGORITHM
    JWT_EXPIRATION_HOURS = settings.JWT_EXPIRATION_HOURS
    DATABASE_URL = settings.DATABASE_URL
    RESET_TOKEN_EXPIRY_HOURS = 1
    FRONTEND_URL = settings.FRONTEND_URL