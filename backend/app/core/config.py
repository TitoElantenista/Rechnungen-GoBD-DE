"""Application configuration using Pydantic Settings"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "sqlite:///./rechnungen.db"
    
    # S3 Storage
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin123"
    S3_BUCKET: str = "invoices"
    S3_REGION: str = "eu-central-1"
    S3_USE_SSL: bool = False
    
    # TSA (Time Stamping Authority)
    TSA_URL: str = "http://timestamp.digicert.com"
    TSA_USERNAME: str = ""
    TSA_PASSWORD: str = ""
    TSA_HASH_ALGORITHM: str = "SHA256"
    
    # Security
    SECRET_KEY: str = "change_this_super_secret_key_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173"
    
    def get_cors_origins(self) -> list:
        """Get CORS origins as list"""
        if isinstance(self.CORS_ORIGINS, str):
            return [i.strip() for i in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Invoice Settings
    INVOICE_NUMBER_PREFIX: str = "RE"
    INVOICE_NUMBER_START: int = 10000
    CURRENCY: str = "EUR"
    DEFAULT_TAX_RATE: float = 19.0
    
    # Company (Seller) defaults
    COMPANY_NAME: str = "Muster GmbH"
    COMPANY_STREET: str = "Musterstraße 123"
    COMPANY_ZIP: str = "12345"
    COMPANY_CITY: str = "Berlin"
    COMPANY_COUNTRY: str = "DE"
    COMPANY_TAX_ID: str = "DE123456789"
    COMPANY_EMAIL: str = "info@muster-gmbh.de"
    COMPANY_PHONE: str = "+49 30 12345678"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
