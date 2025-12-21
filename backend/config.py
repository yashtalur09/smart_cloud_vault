"""Configuration management for SmartCloud Vault."""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "smartcloud_vault"
    
    # JWT
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Storage
    upload_dir: str = "./storage/uploads"
    protected_dir: str = "./storage/protected"
    temp_dir: str = "./storage/temp"
    
    # AI Models
    spacy_model: str = "en_core_web_sm"
    huggingface_model: str = "dslim/bert-base-NER"
    
    # Application
    debug: bool = True
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    max_file_size: int = 10485760  # 10MB
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Create settings instance
def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


settings = get_settings()

# Ensure storage directories exist
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.protected_dir, exist_ok=True)
os.makedirs(settings.temp_dir, exist_ok=True)
