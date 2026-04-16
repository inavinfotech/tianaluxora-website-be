import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    USER_PORTAL_API_URL: str = "http://localhost:8000/api/v1"
    USER_PORTAL_API_KEY: str = ""
    USER_PORTAL_API_SECRET: str = ""

    INVENTORY_PORTAL_API_URL: str = "http://localhost:8000/api/v1"
    INVENTORY_PORTAL_API_KEY: str = ""
    INVENTORY_PORTAL_API_SECRET: str = ""

    ORDER_PORTAL_API_URL: str = "http://localhost:8003"
    ORDER_PORTAL_API_KEY: str = ""
    ORDER_PORTAL_API_SECRET: str = ""

    PAYMENT_PORTAL_API_URL: str = "http://localhost:8004"
    PAYMENT_PORTAL_API_KEY: str = "tiana_web_key_12345" # Placeholder
    PAYMENT_PORTAL_API_SECRET: str = "tiana_web_secret_67890" # Placeholder

    class Config:
        env_file = ".env"

settings = Settings()
