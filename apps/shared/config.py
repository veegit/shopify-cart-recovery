import os
from typing import Optional
from pydantic import BaseSettings, validator


class RedisConfig(BaseSettings):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    
    class Config:
        env_prefix = "REDIS_"


class ShopifyConfig(BaseSettings):
    api_key: str
    api_secret: str
    webhook_secret: str
    app_url: str
    
    class Config:
        env_prefix = "SHOPIFY_"
    
    @validator('api_key', 'api_secret', 'webhook_secret', 'app_url')
    def validate_required_fields(cls, v):
        if not v:
            raise ValueError('This field is required')
        return v


class AppConfig(BaseSettings):
    env: str = "development"
    port: int = 8000
    host: str = "0.0.0.0"
    
    class Config:
        env_prefix = "APP_"


class LoggingConfig(BaseSettings):
    level: str = "INFO"
    format: str = "json"
    
    class Config:
        env_prefix = "LOG_"


class WebPixelsConfig(BaseSettings):
    endpoint: str
    
    class Config:
        env_prefix = "WEB_PIXELS_"
    
    @validator('endpoint')
    def validate_endpoint(cls, v):
        if not v:
            raise ValueError('Web Pixels endpoint is required')
        return v


class Settings:
    def __init__(self):
        self.redis = RedisConfig()
        self.shopify = ShopifyConfig()
        self.app = AppConfig()
        self.logging = LoggingConfig()
        self.web_pixels = WebPixelsConfig()
    
    def validate_all(self):
        try:
            self.shopify.dict()
            self.web_pixels.dict()
            return True
        except Exception as e:
            raise ValueError(f"Configuration validation failed: {e}")


def get_settings() -> Settings:
    from dotenv import load_dotenv
    load_dotenv()
    
    settings = Settings()
    settings.validate_all()
    return settings