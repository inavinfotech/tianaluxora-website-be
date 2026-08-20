"""
Tianaluxora Website BFF Coupon API Routes.
Exposes validate endpoints to the Tianaluxora frontend.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from app.middleware.auth import get_current_user
from app.clients.coupon_client import coupon_client
from app.clients.base import ServiceError

router = APIRouter(prefix="/coupons", tags=["coupons"])


class CartItemSchema(BaseModel):
    id: str
    price: float
    quantity: int = 1


class ValidateCouponBffRequest(BaseModel):
    code: str
    subtotal: float
    items: Optional[List[CartItemSchema]] = None


@router.post("/validate")
async def validate_coupon(
    request: ValidateCouponBffRequest,
    user: dict = Depends(get_current_user)
):
    """
    Validates a coupon code for the active customer checkout session.
    """
    try:
        payload = {
            "code": request.code.strip().upper() if request.code else "",
            "user_id": user.get("sub"),
            "subtotal": float(request.subtotal),
            "items": [item.model_dump() if hasattr(item, "model_dump") else item.dict() for item in request.items] if request.items else []
        }
        result = await coupon_client.validate_coupon(payload)
        return result
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
