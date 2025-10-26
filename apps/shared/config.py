import os
from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None


class ShopifyConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SHOPIFY_")

    api_key: str
    api_secret: str
    webhook_secret: str
    app_url: str

    @field_validator('api_key', 'api_secret', 'webhook_secret', 'app_url')
    @classmethod
    def validate_required_fields(cls, v):
        if not v:
            raise ValueError('This field is required')
        return v


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    env: str = "development"
    port: int = 8000
    host: str = "0.0.0.0"


class LoggingConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOG_")

    level: str = "INFO"
    format: str = "json"


class WebPixelsConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WEB_PIXELS_")

    endpoint: str

    @field_validator('endpoint')
    @classmethod
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
            self.shopify.model_dump()
            self.web_pixels.model_dump()
            return True
        except Exception as e:
            raise ValueError(f"Configuration validation failed: {e}")


def get_settings() -> Settings:
    from dotenv import load_dotenv
    load_dotenv()
    
    settings = Settings()
    settings.validate_all()
    return settings