"""
Centralized configuration from environment variables.
All secrets, URLs, and credentials loaded here — never hardcoded.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import List, Any


class Settings(BaseSettings):
    # ─── Server ───
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # ─── Security / JWT ───
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ─── Microservice URLs ───
    INVENTORY_SERVICE_URL: str = "http://localhost:5002"
    ORDER_SERVICE_URL: str = "http://localhost:5003"
    PAYMENT_SERVICE_URL: str = "http://localhost:5001"
    COUPON_SERVICE_URL: str = "http://localhost:5007"

    # ─── User Portal ───
    USER_PORTAL_URL: str = "http://localhost:5004"
    USER_PORTAL_API_KEY: str = ""
    USER_PORTAL_API_SECRET: str = ""

    # ─── Service API Credentials ───
    INVENTORY_SERVICE_API_KEY: str = ""
    INVENTORY_SERVICE_API_SECRET: str = ""
    PAYMENT_SERVICE_API_KEY: str = ""
    PAYMENT_SERVICE_API_SECRET: str = ""
    ORDER_SERVICE_API_KEY: str = ""
    ORDER_SERVICE_API_SECRET: str = ""
    COUPON_SERVICE_API_KEY: str = ""
    COUPON_SERVICE_API_SECRET: str = ""

    # ─── CORS ───
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "*"]

    # ─── Rate Limiting ───
    RATE_LIMIT: str = "100/minute"

    # ─── Project Meta ───
    PROJECT_NAME: str = "Tianaluxora Website BFF"
    API_V1_STR: str = "/api"

    @model_validator(mode="before")
    @classmethod
    def map_legacy_env_vars(cls, values: Any) -> Any:
        if isinstance(values, dict):
            # User Portal
            if values.get("USER_PORTAL_API_URL") and not values.get("USER_PORTAL_URL"):
                values["USER_PORTAL_URL"] = values["USER_PORTAL_API_URL"]

            # Inventory Service
            if values.get("INVENTORY_PORTAL_API_URL") and not values.get("INVENTORY_SERVICE_URL"):
                values["INVENTORY_SERVICE_URL"] = values["INVENTORY_PORTAL_API_URL"]
            if values.get("INVENTORY_PORTAL_API_KEY") and not values.get("INVENTORY_SERVICE_API_KEY"):
                values["INVENTORY_SERVICE_API_KEY"] = values["INVENTORY_PORTAL_API_KEY"]
            if values.get("INVENTORY_PORTAL_API_SECRET") and not values.get("INVENTORY_SERVICE_API_SECRET"):
                values["INVENTORY_SERVICE_API_SECRET"] = values["INVENTORY_PORTAL_API_SECRET"]

            # Order Service
            if values.get("ORDER_PORTAL_API_URL") and not values.get("ORDER_SERVICE_URL"):
                values["ORDER_SERVICE_URL"] = values["ORDER_PORTAL_API_URL"]
            if values.get("ORDER_PORTAL_API_KEY") and not values.get("ORDER_SERVICE_API_KEY"):
                values["ORDER_SERVICE_API_KEY"] = values["ORDER_PORTAL_API_KEY"]
            if values.get("ORDER_PORTAL_API_SECRET") and not values.get("ORDER_SERVICE_API_SECRET"):
                values["ORDER_SERVICE_API_SECRET"] = values["ORDER_PORTAL_API_SECRET"]

            # Payment Service
            if values.get("PAYMENT_PORTAL_API_URL") and not values.get("PAYMENT_SERVICE_URL"):
                values["PAYMENT_SERVICE_URL"] = values["PAYMENT_PORTAL_API_URL"]
            if values.get("PAYMENT_PORTAL_API_KEY") and not values.get("PAYMENT_SERVICE_API_KEY"):
                values["PAYMENT_SERVICE_API_KEY"] = values["PAYMENT_PORTAL_API_KEY"]
            if values.get("PAYMENT_PORTAL_API_SECRET") and not values.get("PAYMENT_SERVICE_API_SECRET"):
                values["PAYMENT_SERVICE_API_SECRET"] = values["PAYMENT_PORTAL_API_SECRET"]

            # Coupon Service
            if values.get("COUPON_PORTAL_API_URL") and not values.get("COUPON_SERVICE_URL"):
                values["COUPON_SERVICE_URL"] = values["COUPON_PORTAL_API_URL"]
            if values.get("COUPON_PORTAL_API_KEY") and not values.get("COUPON_SERVICE_API_KEY"):
                values["COUPON_SERVICE_API_KEY"] = values["COUPON_PORTAL_API_KEY"]
            if values.get("COUPON_PORTAL_API_SECRET") and not values.get("COUPON_SERVICE_API_SECRET"):
                values["COUPON_SERVICE_API_SECRET"] = values["COUPON_PORTAL_API_SECRET"]

        return values

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
