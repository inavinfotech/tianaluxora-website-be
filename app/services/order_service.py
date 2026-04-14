import httpx
from app.core.config import settings
from typing import List, Dict, Any, Optional

class OrderService:
    def __init__(self):
        self.base_url = settings.ORDER_PORTAL_API_URL
        self.headers = {
            "X-API-KEY": settings.ORDER_PORTAL_API_KEY,
            "X-API-SECRET": settings.ORDER_PORTAL_API_SECRET
        }

    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/orders/",
                headers=self.headers,
                json=order_data
            )
            response.raise_for_status()
            return response.json()

    async def get_orders(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/orders/",
                headers=self.headers,
                params={"skip": skip, "limit": limit}
            )
            response.raise_for_status()
            return response.json()

    async def get_order(self, order_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/orders/{order_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def update_order(self, order_id: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/orders/{order_id}",
                headers=self.headers,
                json=order_data
            )
            response.raise_for_status()
            return response.json()

order_service = OrderService()
