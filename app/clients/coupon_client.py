"""
Client for the Coupon/Discount microservice.
Validates coupon codes and logs successful claims.
"""
from typing import Optional, List
from app.clients.base import BaseClient
from app.core.config import settings


class CouponClient(BaseClient):
    def __init__(self):
        super().__init__(
            base_url=settings.COUPON_SERVICE_URL,
            api_key=settings.COUPON_SERVICE_API_KEY,
            api_secret=settings.COUPON_SERVICE_API_SECRET,
            service_name="CouponPortal",
        )

    async def validate_coupon(self, payload: dict) -> dict:
        """
        Validate a coupon code against a subtotal and cart items.
        payload keys: code, user_id, app, subtotal, items
        """
        return await self.post("/api/v1/coupons/validate", json=payload)

    async def claim_coupon(self, payload: dict) -> dict:
        """
        Seal/claim a coupon after payment is successfully verified.
        payload keys: coupon_id, user_id, order_id, payment_verified
        """
        return await self.post("/api/v1/coupons/claim", json=payload)


coupon_client = CouponClient()
