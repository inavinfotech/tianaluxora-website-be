"""
Client for the Order Management microservice.
Creates orders, fetches order history, and manages order lifecycle.
"""
from typing import Optional
from app.clients.base import BaseClient
from app.core.config import settings


class OrderClient(BaseClient):
    def __init__(self):
        super().__init__(
            base_url=settings.ORDER_SERVICE_URL,
            api_key=settings.ORDER_SERVICE_API_KEY,
            api_secret=settings.ORDER_SERVICE_API_SECRET,
            service_name="OrderPortal",
        )

    async def create_order(self, order_data: dict) -> dict:
        """Create a new order."""
        return await self.post("/api/v1/orders/", json=order_data)

    async def get_orders(self, user_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> list:
        """Fetch orders, optionally filtered by user."""
        params = {"skip": skip, "limit": limit}
        if user_id:
            params["user_id"] = user_id
        return await self.get("/api/v1/orders/", params=params)

    async def get_order(self, order_id: str) -> dict:
        """Fetch a single order by ID."""
        return await self.get(f"/api/v1/orders/{order_id}")

    async def transition_order(self, order_id: str, to_status: str, notes: str = None) -> dict:
        """Transition order to a new status."""
        payload = {"to_status": to_status}
        if notes:
            payload["notes"] = notes
        return await self.post(f"/api/v1/orders/{order_id}/transition", json=payload)


order_client = OrderClient()
