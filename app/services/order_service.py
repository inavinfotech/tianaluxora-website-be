"""
Order service — orchestrates order creation and tracking through the order portal.
"""
from app.clients.order_client import order_client


class OrderService:
    async def create_order(self, user_id: str, order_data: dict) -> dict:
        """Create order in the OMS."""
        order_data["user_id"] = user_id
        return await order_client.create_order(order_data)

    async def get_orders(self, user_id: str, skip: int = 0, limit: int = 50) -> list:
        """Fetch user's order history."""
        return await order_client.get_orders(user_id=user_id, skip=skip, limit=limit)

    async def get_order(self, order_id: str) -> dict:
        """Get a single order."""
        return await order_client.get_order(order_id)


order_service = OrderService()
