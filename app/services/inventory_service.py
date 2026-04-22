import httpx
from app.core.config import settings
from typing import List, Dict, Any, Optional

class InventoryService:
    def __init__(self):
        self.base_url = settings.INVENTORY_PORTAL_API_URL
        self.headers = {
            "X-API-Key": settings.INVENTORY_PORTAL_API_KEY,
            "X-API-Secret": settings.INVENTORY_PORTAL_API_SECRET
        }

    async def get_products(self, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/products/",
                headers=self.headers,
                params={"limit": limit, "offset": offset}
            )
            response.raise_for_status()
            data = response.json()
            
            # Enrich with frontend-specific fields
            for item in data.get("items", []):
                # Use actual image from inventory if available
                images = item.get("images", [])
                if images and isinstance(images, list) and len(images) > 0:
                    image_path = images[0]
                    if image_path.startswith("/"):
                        item["image"] = f"{settings.INVENTORY_PORTAL_BASE_URL}{image_path}"
                    else:
                        item["image"] = image_path
                else:
                    item["image"] = "/images/small-bottle.webp" # Default image
                
                item["tag"] = "New Arrival"
                
                # Map variants to sizes for the frontend
                variants = item.get("variants", [])
                if isinstance(variants, str):
                    import json
                    variants = json.loads(variants)
                
                if variants:
                    item["sizes"] = [v.get("weight") for v in variants if v.get("weight")]
                    item["real_variants"] = variants
            
            return data

    async def get_product(self, product_id: int) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/products/{product_id}",
                headers=self.headers
            )
            response.raise_for_status()
            item = response.json()
            
            # Enrich with frontend-specific fields
            images = item.get("images", [])
            if images and isinstance(images, list) and len(images) > 0:
                image_path = images[0]
                if image_path.startswith("/"):
                    item["image"] = f"{settings.INVENTORY_PORTAL_BASE_URL}{image_path}"
                else:
                    item["image"] = image_path
            else:
                item["image"] = "/images/small-bottle.webp" # Default image
            
            item["tag"] = "New Arrival"
            
            # Map variants to sizes for the frontend if they exist
            variants = item.get("variants", [])
            if isinstance(variants, str):
                import json
                variants = json.loads(variants)
            
            if variants:
                item["sizes"] = [v.get("weight") for v in variants if v.get("weight")]
                # Store variants for frontend use
                item["real_variants"] = variants
                
            return item

    async def reserve_stock(self, product_id: int, quantity: int, variant_id: Optional[int] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/inventory/reserve",
                headers=self.headers,
                json={"product_id": product_id, "quantity": quantity, "variant_id": variant_id}
            )
            response.raise_for_status()
            return response.json()

    async def confirm_reservation(self, reservation_id: int) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/inventory/confirm/{reservation_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def release_reservation(self, reservation_id: int) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/inventory/release/{reservation_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

inventory_service = InventoryService()
