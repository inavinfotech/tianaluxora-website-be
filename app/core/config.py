import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    USER_PORTAL_API_URL: str
    USER_PORTAL_API_KEY: str
    USER_PORTAL_API_SECRET: str

    INVENTORY_PORTAL_API_URL: str
    INVENTORY_PORTAL_API_KEY: str
    INVENTORY_PORTAL_API_SECRET: str

    ORDER_PORTAL_API_URL: str
    ORDER_PORTAL_API_KEY: str
    ORDER_PORTAL_API_SECRET: str

    PAYMENT_PORTAL_API_URL: str
    PAYMENT_PORTAL_API_KEY: str
    PAYMENT_PORTAL_API_SECRET: str

    class Config:
        env_file = ".env"

settings = Settings()
