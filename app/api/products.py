from fastapi import APIRouter, HTTPException, Query
from app.services.inventory_service import inventory_service
from typing import Dict, Any

router = APIRouter()

@router.get("/")
async def list_products(
    limit: int = Query(10, gt=0, le=100),
    offset: int = Query(0, ge=0)
):
    try:
        return await inventory_service.get_products(limit, offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{product_id}")
async def get_product(product_id: int):
    try:
        return await inventory_service.get_product(product_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Product not found")
