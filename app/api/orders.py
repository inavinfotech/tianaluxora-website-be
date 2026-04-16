from fastapi import APIRouter, HTTPException, Query, Depends
from app.services.order_service import order_service
from app.services.payment_service import payment_service
from typing import List, Dict, Any

router = APIRouter()

from app.api.deps import get_current_user
from app.services.inventory_service import inventory_service

@router.post("/")
async def create_order(order_data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    try:
        # Override user_id with the authenticated user's ID
        order_data["user_id"] = str(current_user["user_id"])
        return await order_service.create_order(order_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")

@router.post("/checkout")
async def checkout(order_data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Unified checkout flow:
    1. Validate and reserve stock
    2. Create order in OMS
    3. Initiate payment via Payment Portal
    """
    reservations = []
    items = order_data.get("items", [])
    
    try:
        # 1. Reserve Stock for all items
        for item in items:
            product_id = item.get("product_id") or item.get("id")
            if not product_id:
                raise ValueError("Missing product_id for item")
            
            res = await inventory_service.reserve_stock(product_id, item["quantity"])
            reservations.append(res["id"])
            
        # 2. Create Order
        order_data["user_id"] = str(current_user["user_id"])
        order = await order_service.create_order(order_data)
        
        # 3. Initiate Payment
        payment_order = await payment_service.create_payment_order(
            order_id=order["id"],
            amount=int(order["total_amount"] * 100), # to paisa
            currency="INR",
            user_id=order_data["user_id"]
        )
            
        return {
            "order": order,
            "payment": payment_order
        }
        
    except Exception as e:
        # Rollback: Release any reservations made
        for res_id in reservations:
            try:
                await inventory_service.release_reservation(res_id)
            except:
                pass
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify-payment")
async def verify_payment(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Verifies payment with Payment Portal and updates Order Status.
    """
    try:
        # 1. Verify with Payment Portal
        await payment_service.verify_payment(
            razorpay_order_id=data["razorpay_order_id"],
            razorpay_payment_id=data["razorpay_payment_id"],
            razorpay_signature=data["razorpay_signature"]
        )
        
        # 2. Update Order Status in OMS
        await order_service.update_order(data["order_id"], {"status": "Processing"})
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Payment verification failed: {str(e)}")

@router.get("/")
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, gt=0, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    try:
        # For now, we fetch all orders, but we should probably filter by user_id
        # The OMS service get_orders doesn't support user_id filter yet in its params
        # But we can pass it if we update the service
        return await order_service.get_orders(skip, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")

@router.get("/{order_id}")
async def get_order(order_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    try:
        return await order_service.get_order(order_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Order not found: {str(e)}")

@router.put("/{order_id}")
async def update_order(order_id: str, order_data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    try:
        return await order_service.update_order(order_id, order_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update order: {str(e)}")
