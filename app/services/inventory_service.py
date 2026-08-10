"""
Product service — fetches and aggregates product data from the inventory portal.
Includes in-memory caching to reduce downstream load.
"""
from cachetools import TTLCache
from app.clients.inventory_client import inventory_client

# Cache products with 5s TTL to ensure real-time inventory stock synchronization
_product_cache = TTLCache(maxsize=500, ttl=5)


class ProductService:
    def _transform_product(self, product: dict) -> dict:
        """Enrich and normalize product data for frontend compatibility."""
        if not product:
            return product

        if "variants" in product and "real_variants" not in product:
            product["real_variants"] = product["variants"]

        from app.core.config import settings
        base_url = settings.INVENTORY_SERVICE_URL.replace("/api/v1", "").rstrip("/")

        if "images" in product and isinstance(product["images"], list):
            new_images = []
            for img in product["images"]:
                if img and img.startswith("/uploads/"):
                    new_images.append(f"{base_url}{img}")
                else:
                    new_images.append(img)
            product["images"] = new_images

        # Also copy first image to 'image' field if not present
        if "image" not in product and product.get("images"):
            product["image"] = product["images"][0]

        # Normalize variant images as well if they exist
        if "real_variants" in product and isinstance(product["real_variants"], list):
            for v in product["real_variants"]:
                if "images" in v and isinstance(v["images"], list):
                    new_v_images = []
                    for img in v["images"]:
                        if img and img.startswith("/uploads/"):
                            new_v_images.append(f"{base_url}{img}")
                        else:
                            new_v_images.append(img)
                    v["images"] = new_v_images
                if "image" not in v and v.get("images"):
                    v["image"] = v["images"][0]
                
                v_mrp = v.get("mrp") or product.get("mrp") or product.get("base_price")
                v_price = v.get("price")
                if v_mrp and v_price and float(v_mrp) > float(v_price):
                    v["oldPrice"] = f"₹{int(v_mrp) if float(v_mrp).is_integer() else v_mrp}"
                    pct = round((1 - float(v_price) / float(v_mrp)) * 100)
                    v["discount"] = f"{pct}% OFF"
                else:
                    v["oldPrice"] = None
                    v["discount"] = None

        # Fallback: if product has no cover image, use first variant image
        has_prod_image = bool(product.get("image")) or (bool(product.get("images")) and len(product["images"]) > 0 and bool(product["images"][0]))
        if not has_prod_image:
            first_v_img = None
            if "real_variants" in product and isinstance(product["real_variants"], list):
                for v in product["real_variants"]:
                    if v.get("images") and isinstance(v["images"], list) and len(v["images"]) > 0 and v["images"][0]:
                        first_v_img = v["images"][0]
                        break
                    elif v.get("image"):
                        first_v_img = v["image"]
                        break
            if first_v_img:
                product["image"] = first_v_img
                if not product.get("images") or len(product.get("images", [])) == 0:
                    product["images"] = [first_v_img]

        # Calculate pricing fields
        mrp = product.get("base_price") or product.get("price") or 0
        discounted = product.get("discounted_price")
        if discounted and float(discounted) > 0 and float(discounted) < float(mrp):
            product["price"] = float(discounted)
            product["mrp"] = float(mrp)
            product["oldPrice"] = f"₹{int(mrp) if float(mrp).is_integer() else mrp}"
            pct = round((1 - float(discounted) / float(mrp)) * 100)
            product["discount"] = f"{pct}% OFF"
        else:
            product["price"] = float(mrp) if mrp else product.get("price")
            product["mrp"] = float(mrp) if mrp else None
            product["oldPrice"] = None
            product["discount"] = None

        # Add tag for frontend
        product.setdefault("tag", "New Arrival")

        # Map variants to sizes/options for the frontend
        variants = product.get("real_variants", []) or product.get("variants", [])
        if isinstance(variants, list) and len(variants) > 0:
            extracted_sizes = []
            default_placeholders = ["50 ml", "100 ml", "250 ml", "500 ml"]
            
            for idx, v in enumerate(variants):
                label = None
                if isinstance(v, dict):
                    # 1. Check dynamic attributes dictionary from inventory portal
                    attrs = v.get("attributes")
                    if isinstance(attrs, dict) and attrs:
                        label = (
                            attrs.get("Size") or
                            attrs.get("size") or
                            attrs.get("Volume") or
                            attrs.get("volume") or
                            attrs.get("Weight") or
                            attrs.get("weight") or
                            " / ".join([str(val) for val in attrs.values() if val and not (len(str(val)) > 20 or "INV-" in str(val))])
                        )

                    # 2. Check direct properties
                    if not label:
                        for key in ["weight", "size", "name", "title", "volume", "label"]:
                            cand = v.get(key)
                            if cand and isinstance(cand, str) and not (len(cand) > 20 or "INV-" in cand):
                                label = cand
                                break

                    # 3. Fallback to clean size choice if candidate is empty or an ID
                    if not label:
                        label = default_placeholders[idx] if idx < len(default_placeholders) else f"Option {idx + 1}"

                    v["weight"] = label
                    v["size"] = label
                    extracted_sizes.append(label)
                elif isinstance(v, str):
                    if not (len(v) > 20 or "INV-" in v):
                        extracted_sizes.append(v)
                    else:
                        extracted_sizes.append(default_placeholders[idx] if idx < len(default_placeholders) else f"Option {idx + 1}")

            if extracted_sizes:
                product["sizes"] = extracted_sizes

        return product

    async def get_products(self, limit: int = 50, offset: int = 0) -> dict:
        """Fetch paginated products from inventory portal (with cache)."""
        cache_key = f"products:{limit}:{offset}"
        if cache_key in _product_cache:
            return _product_cache[cache_key]

        data = await inventory_client.get_products(limit=limit, offset=offset)

        # Transform each product
        if data and "items" in data:
            data["items"] = [self._transform_product(p) for p in data["items"]]

        _product_cache[cache_key] = data
        return data

    async def get_product(self, product_id: str) -> dict:
        """Fetch single product with stock info."""
        cache_key = f"product:{product_id}"
        if cache_key in _product_cache:
            return _product_cache[cache_key]

        product = await inventory_client.get_product(product_id)

        # Enrich with stock data
        try:
            stock = await inventory_client.get_stock(product_id)
            product["stock_quantity"] = stock.get("quantity", 0)
        except Exception:
            product["stock_quantity"] = None

        # Transform product
        product = self._transform_product(product)

        _product_cache[cache_key] = product
        return product

    async def search_products(self, query: str, limit: int = 50) -> list:
        """Search products by name/description (client-side filter for now)."""
        data = await self.get_products(limit=100, offset=0)
        items = data.get("items", [])
        q = query.lower()
        return [
            p for p in items
            if q in p.get("name", "").lower()
            or q in p.get("description", "").lower()
            or q in p.get("sku", "").lower()
        ]


product_service = ProductService()
