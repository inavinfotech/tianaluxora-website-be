"""
Client for the Inventory Portal microservice.
Fetches products, stock levels, and manages reservations for the storefront.
"""
from typing import Optional
from app.clients.base import BaseClient
from app.core.config import settings


class InventoryClient(BaseClient):
    def __init__(self):
        super().__init__(
            base_url=settings.INVENTORY_SERVICE_URL,
            api_key=settings.INVENTORY_SERVICE_API_KEY,
            api_secret=settings.INVENTORY_SERVICE_API_SECRET,
            service_name="InventoryPortal",
        )

    async def get_products(self, limit: int = 50, offset: int = 0) -> dict:
        """Fetch paginated product list."""
        return await self.get(
            "/api/v1/products/",
            params={"limit": limit, "offset": offset},
        )

    async def get_product(self, product_id: str) -> dict:
        """Fetch a single product by ID."""
        return await self.get(f"/api/v1/products/{product_id}")

    async def get_stock(self, product_id: str, variant_id: Optional[str] = None) -> dict:
        """Check stock level for a product."""
        params = {}
        if variant_id:
            params["variant_id"] = variant_id
        return await self.get(
            f"/api/v1/inventory/{product_id}",
            params=params,
        )

    async def reserve_stock(self, product_id, quantity: int, variant_id=None) -> dict:
        """Reserve stock for checkout."""
        return await self.post(
            "/api/v1/inventory/reserve",
            json={"product_id": str(product_id), "quantity": quantity, "variant_id": str(variant_id) if variant_id else None},
        )

    async def confirm_reservation(self, reservation_id) -> dict:
        """Confirm a stock reservation after payment."""
        return await self.post(f"/api/v1/inventory/confirm/{reservation_id}")

    async def release_reservation(self, reservation_id) -> dict:
        """Release a stock reservation."""
        return await self.post(f"/api/v1/inventory/release/{reservation_id}")


inventory_client = InventoryClient()
