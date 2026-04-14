from fastapi import APIRouter, HTTPException, Query
from app.services.order_service import order_service
from typing import List, Dict, Any

router = APIRouter()

@router.post("/")
async def create_order(order_data: Dict[str, Any]):
    try:
        return await order_service.create_order(order_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")

@router.get("/")
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, gt=0, le=100)
):
    try:
        return await order_service.get_orders(skip, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")

@router.get("/{order_id}")
async def get_order(order_id: str):
    try:
        return await order_service.get_order(order_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Order not found: {str(e)}")

@router.put("/{order_id}")
async def update_order(order_id: str, order_data: Dict[str, Any]):
    try:
        return await order_service.update_order(order_id, order_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update order: {str(e)}")
