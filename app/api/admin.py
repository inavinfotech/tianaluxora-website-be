"""
Admin API routes — dashboard stats, product management, order lifecycle management, user directory.
Protected by require_admin dependency.
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any, List
from app.middleware.auth import require_admin
from app.clients.inventory_client import inventory_client
from app.clients.order_client import order_client
from app.clients.user_portal_client import user_portal_client
from app.clients.base import ServiceError

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/stats")
async def get_admin_stats():
    """Aggregate dashboard statistics across microservices concurrently."""
    stats = {
        "total_revenue": 0,
        "total_orders": 0,
        "pending_orders": 0,
        "total_products": 0,
        "total_users": 0,
        "recent_orders": [],
        "low_stock_products": [],
        "trends": {
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "revenue": [0, 0, 0, 0, 0, 0, 0],
            "orders": [0, 0, 0, 0, 0, 0, 0],
        }
    }

    async def fetch_orders():
        try:
            return await order_client.get_orders(limit=100)
        except Exception:
            return []

    async def fetch_products():
        try:
            return await inventory_client.get_products(limit=100)
        except Exception:
            return {}

    async def fetch_users():
        try:
            return await user_portal_client.list_users(limit=100)
        except Exception:
            return []

    orders, prod_res, users = await asyncio.gather(
        fetch_orders(),
        fetch_products(),
        fetch_users(),
        return_exceptions=True
    )

    # Process Orders
    if isinstance(orders, list):
        stats["total_orders"] = len(orders)
        stats["recent_orders"] = orders[:5]
        pending_count = 0
        total_rev = 0
        for o in orders:
            st = (o.get("status") or "pending").lower()
            if st in ["pending", "created", "processing"]:
                pending_count += 1
            amt = float(o.get("total_amount", 0) or 0)
            if st in ["paid", "delivered", "shipped", "processing", "completed"]:
                total_rev += amt
        stats["pending_orders"] = pending_count
        stats["total_revenue"] = total_rev

        # Real day-of-week & month trend calculation
        stats["trends"] = {
            "weekly": {
                "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                "revenue": [0.0] * 7,
                "orders": [0] * 7,
            },
            "monthly": {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                "revenue": [0.0] * 12,
                "orders": [0] * 12,
            }
        }
        from datetime import datetime

        for o in orders:
            st = (o.get("status") or "pending").lower()
            amt = float(o.get("total_amount", 0) or 0)
            created = o.get("created_at")
            day_idx = 6  # Default to Sunday if not parseable
            month_idx = datetime.now().month - 1

            if created:
                try:
                    if isinstance(created, str):
                        clean_str = created.replace("Z", "+00:00")
                        dt = datetime.fromisoformat(clean_str)
                        day_idx = dt.weekday()
                        month_idx = dt.month - 1
                    elif hasattr(created, "weekday"):
                        day_idx = created.weekday()
                        month_idx = created.month - 1
                except Exception:
                    pass

            stats["trends"]["weekly"]["orders"][day_idx] += 1
            stats["trends"]["monthly"]["orders"][month_idx] += 1
            if st in ["paid", "delivered", "shipped", "processing", "completed"]:
                stats["trends"]["weekly"]["revenue"][day_idx] = round(stats["trends"]["weekly"]["revenue"][day_idx] + amt, 2)
                stats["trends"]["monthly"]["revenue"][month_idx] = round(stats["trends"]["monthly"]["revenue"][month_idx] + amt, 2)

    # Process Products & Low Stock Alerts
    if isinstance(prod_res, dict):
        items = prod_res.get("items", [])
        stats["total_products"] = prod_res.get("total", len(items))
        for p in items:
            p_stock = p.get("stock_quantity", p.get("stock", p.get("quantity", 0)))
            variants = p.get("variants") or p.get("real_variants") or []
            if variants and isinstance(variants, list):
                total_variant_stock = sum([v.get("stock", 0) for v in variants])
                effective_stock = max(p_stock, total_variant_stock)
            else:
                effective_stock = p_stock

            if effective_stock <= 5:
                stats["low_stock_products"].append({
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "sku": p.get("sku"),
                    "stock": effective_stock
                })
    elif isinstance(prod_res, list):
        stats["total_products"] = len(prod_res)

    # Process Users
    if isinstance(users, list):
        stats["total_users"] = len(users)

    return stats


@router.get("/products")
async def list_admin_products(
    limit: int = Query(50, gt=0, le=200),
    offset: int = Query(0, ge=0),
):
    """Fetch all products with details for admin management."""
    try:
        return await inventory_client.get_products(limit=limit, offset=offset)
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/products")
async def create_product(product_data: Dict[str, Any]):
    """Create a new product in the inventory microservice."""
    try:
        from app.clients.inventory_client import inventory_client as inv
        return await inv.post("/api/v1/products/", json=product_data)
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.put("/products/{product_id}")
async def update_product(product_id: str, product_data: Dict[str, Any]):
    """Update product details in inventory microservice."""
    try:
        from app.clients.inventory_client import inventory_client as inv
        return await inv.put(f"/api/v1/products/{product_id}", json=product_data)
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/products/{product_id}/stock")
async def update_product_stock(product_id: str, payload: Dict[str, Any]):
    """Update stock quantity for product or variant in inventory microservice."""
    try:
        from app.clients.inventory_client import inventory_client as inv
        stock_qty = payload.get("stock", payload.get("quantity", 0))
        return await inv.put(f"/api/v1/products/{product_id}", json={"stock": stock_qty})
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orders")
async def list_admin_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, gt=0, le=200),
    user_id: Optional[str] = None
):
    """Fetch paginated store orders across all users."""
    try:
        return await order_client.get_orders(user_id=user_id, skip=skip, limit=limit)
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/orders/{order_id}")
async def get_admin_order(order_id: str):
    """Fetch detailed information for a single order enriched with customer user details."""
    try:
        order = await order_client.get_order(order_id)
        if isinstance(order, dict) and order.get("user_id"):
            try:
                user_info = await user_portal_client.get_user(order["user_id"])
                if isinstance(user_info, dict):
                    order["customer_email"] = user_info.get("email", order.get("customer_email"))
                    order["customer_phone"] = user_info.get("phone", order.get("customer_phone", "+91 98765 43210"))
                    order["customer_name"] = user_info.get("full_name", order.get("customer_name"))
                    order["shipping_address"] = user_info.get("address", order.get("shipping_address"))
            except Exception:
                pass
        return order
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.put("/orders/{order_id}/status")
async def transition_order_status(order_id: str, payload: Dict[str, Any]):
    """Transition an order status."""
    to_status = payload.get("to_status")
    notes = payload.get("notes")
    if not to_status:
        raise HTTPException(status_code=400, detail="to_status is required")
    try:
        return await order_client.transition_order(order_id, to_status=to_status, notes=notes)
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/users")
async def list_admin_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, gt=0, le=200),
    search: Optional[str] = None
):
    """List users from Central User Portal."""
    try:
        return await user_portal_client.list_users(skip=skip, limit=limit, search=search)
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
