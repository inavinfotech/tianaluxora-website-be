import httpx
from app.core.config import settings
from typing import List, Dict, Any, Optional
from app.core.http_client import get_async_client

class OrderService:
    def __init__(self):
        self.base_url = settings.ORDER_PORTAL_API_URL
        self.headers = {
            "X-API-KEY": settings.ORDER_PORTAL_API_KEY,
            "X-API-SECRET": settings.ORDER_PORTAL_API_SECRET
        }

    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        async with get_async_client() as client:
            try:
                # Sanitize variant_id to string to match OMS schema
                if "items" in order_data:
                    for item in order_data["items"]:
                        if item.get("variant_id") is not None:
                            item["variant_id"] = str(item["variant_id"])
                        if item.get("product_id") is not None:
                            item["product_id"] = str(item["product_id"])

                response = await client.post(
                    f"{self.base_url}/orders/",
                    headers=self.headers,
                    json=order_data
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                import logging
                logger = logging.getLogger("uvicorn.error")
                logger.error(f"Order Creation Failed in OMS ({e.response.status_code}): {e.response.text}")
                raise

    async def get_orders(self, skip: int = 0, limit: int = 100, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        async with get_async_client() as client:
            params = {"skip": skip, "limit": limit}
            if user_id:
                params["user_id"] = user_id
                
            response = await client.get(
                f"{self.base_url}/orders/",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()

    async def get_order(self, order_id: str) -> Dict[str, Any]:
        async with get_async_client() as client:
            response = await client.get(
                f"{self.base_url}/orders/{order_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def update_order(self, order_id: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        async with get_async_client() as client:
            response = await client.put(
                f"{self.base_url}/orders/{order_id}",
                headers=self.headers,
                json=order_data
            )
            response.raise_for_status()
            return response.json()

order_service = OrderService()
