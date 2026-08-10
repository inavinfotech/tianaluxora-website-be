"""
Admin API routes — dashboard stats, product management, order lifecycle management, user directory.
Protected by require_admin dependency.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any
from app.middleware.auth import require_admin
from app.clients.inventory_client import inventory_client
from app.clients.order_client import order_client
from app.clients.user_portal_client import user_portal_client
from app.clients.base import ServiceError

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/stats")
async def get_admin_stats():
    """Aggregate dashboard statistics across microservices."""
    stats = {
        "total_revenue": 0,
        "total_orders": 0,
        "pending_orders": 0,
        "total_products": 0,
        "total_users": 0,
        "recent_orders": [],
        "low_stock_products": [],
    }

    # Fetch orders
    try:
        orders = await order_client.get_orders(limit=100)
        if isinstance(orders, list):
            stats["total_orders"] = len(orders)
            stats["recent_orders"] = orders[:5]
            pending_count = 0
            for o in orders:
                st = (o.get("status") or "pending").lower()
                if st in ["pending", "created", "processing"]:
                    pending_count += 1
                if st in ["paid", "delivered", "shipped", "processing", "completed"]:
                    stats["total_revenue"] += float(o.get("total_amount", 0) or 0)
            stats["pending_orders"] = pending_count
    except Exception:
        pass

    # Fetch products
    try:
        prod_res = await inventory_client.get_products(limit=100)
        if isinstance(prod_res, dict):
            items = prod_res.get("items", [])
            stats["total_products"] = prod_res.get("total", len(items))
            for p in items:
                stock = p.get("quantity", p.get("stock", 10))
                if stock <= 5:
                    stats["low_stock_products"].append({
                        "id": p.get("id"),
                        "name": p.get("name"),
                        "sku": p.get("sku"),
                        "stock": stock
                    })
        elif isinstance(prod_res, list):
            stats["total_products"] = len(prod_res)
    except Exception:
        pass

    # Fetch users count from portal
    try:
        users = await user_portal_client.list_users(limit=100)
        if isinstance(users, list):
            stats["total_users"] = len(users)
    except Exception:
        pass

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
    """Fetch detailed information for a single order."""
    try:
        return await order_client.get_order(order_id)
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
