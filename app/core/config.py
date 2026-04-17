from pydantic_settings import BaseSettings, SettingsConfigDict
import os
import logging

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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra="ignore")

    def __init__(self, **values):
        super().__init__(**values)
        logger = logging.getLogger("uvicorn.error")
        if not os.path.exists(".env"):
             logger.warning(f"CRITICAL: .env file NOT FOUND in website/backend current directory: {os.getcwd()}.")
        else:
             logger.info(f"Successfully loaded website configuration from {os.path.abspath('.env')}")

settings = Settings()
