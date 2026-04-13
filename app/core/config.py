import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    USER_PORTAL_API_URL: str = "http://localhost:8000/api/v1"
    USER_PORTAL_API_KEY: str = ""
    USER_PORTAL_API_SECRET: str = ""

    INVENTORY_PORTAL_API_URL: str = "http://localhost:8000/api/v1"
    INVENTORY_PORTAL_API_KEY: str = ""
    INVENTORY_PORTAL_API_SECRET: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
