"""
Product API routes — fetches products from inventory portal.
Public endpoints (no auth required for browsing).
"""
from fastapi import APIRouter, HTTPException, Query
from app.services.inventory_service import product_service
from app.clients.base import ServiceError

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/")
async def list_products(
    limit: int = Query(50, gt=0, le=100),
    offset: int = Query(0, ge=0),
):
    """Fetch paginated product list from inventory portal."""
    try:
        return await product_service.get_products(limit=limit, offset=offset)
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/search")
async def search_products(q: str = Query(..., min_length=1)):
    """Search products by name/description."""
    try:
        results = await product_service.search_products(q)
        return {"items": results, "total": len(results)}
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/{product_id}")
async def get_product(product_id: str):
    """Fetch single product with stock info."""
    try:
        return await product_service.get_product(product_id)
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
