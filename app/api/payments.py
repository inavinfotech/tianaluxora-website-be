"""
Payment API routes — creates and verifies payments through the payment portal.
All payment routes require authentication.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.payment_service import payment_service
from app.middleware.auth import get_current_user
from app.clients.base import ServiceError

router = APIRouter(prefix="/payments", tags=["payments"])


class CreatePaymentRequest(BaseModel):
    amount: int
    currency: str = "INR"
    plan_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@router.post("/create-order")
async def create_payment_order(
    request: CreatePaymentRequest,
    user: dict = Depends(get_current_user),
):
    """Create a Razorpay payment order via payment portal."""
    try:
        return await payment_service.create_payment_order(
            user_id=user.get("sub"),
            amount=request.amount,
            currency=request.currency,
            plan_type=request.plan_type,
            metadata=request.metadata,
        )
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/verify")
async def verify_payment(
    request: VerifyPaymentRequest,
    user: dict = Depends(get_current_user),
):
    """Verify Razorpay payment signature via payment portal."""
    try:
        return await payment_service.verify_payment(
            razorpay_order_id=request.razorpay_order_id,
            razorpay_payment_id=request.razorpay_payment_id,
            razorpay_signature=request.razorpay_signature,
        )
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/status/{order_id}")
async def get_payment_status(
    order_id: str,
    user: dict = Depends(get_current_user),
):
    """Check payment status."""
    try:
        return await payment_service.get_status(order_id)
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
