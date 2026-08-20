"""
Order API routes — creates orders and fetches order history through the OMS portal.
All order routes require authentication.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, model_validator
from typing import List, Optional, Any
from app.services.order_service import order_service
from app.services.payment_service import payment_service
from app.middleware.auth import get_current_user
from app.clients.base import ServiceError
from app.clients.inventory_client import inventory_client
from app.clients.coupon_client import coupon_client

logger = logging.getLogger("tiana-bff")

router = APIRouter(prefix="/orders", tags=["orders"])


class OrderItem(BaseModel):
    product_id: Any
    variant_id: Optional[Any] = None
    name: Optional[str] = "Product"
    product_name: Optional[str] = None
    quantity: int = 1
    price: Optional[float] = 0.0
    unit_price: Optional[float] = 0.0
    image: Optional[str] = None
    variant_name: Optional[str] = None
    sku: Optional[str] = None

    @model_validator(mode="after")
    def sync_item_fields(self):
        if self.product_name and (not self.name or self.name == "Product"):
            self.name = self.product_name
        elif self.name and not self.product_name:
            self.product_name = self.name

        if self.unit_price is not None and self.unit_price != 0.0 and (self.price is None or self.price == 0.0):
            self.price = float(self.unit_price)
        elif self.price is not None and self.price != 0.0 and (self.unit_price is None or self.unit_price == 0.0):
            self.unit_price = float(self.price)

        if self.price is None:
            self.price = 0.0
        if self.unit_price is None:
            self.unit_price = 0.0

        return self


class OrderCreate(BaseModel):
    items: List[OrderItem]
    total_amount: float
    currency: str = "INR"


class CheckoutRequest(BaseModel):
    items: List[OrderItem]
    total_amount: float
    currency: str = "INR"


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    reservation_ids: List[Any] = []
    order_data: Optional[dict] = None
    coupon_id: Optional[str] = None
    coupon_code: Optional[str] = None


@router.post("/checkout")
async def checkout(request: CheckoutRequest, user: dict = Depends(get_current_user)):
    """
    Step 1 of checkout flow:
    1. Validate and reserve stock
    2. Initiate payment session
    """
    reservation_ids = []

    try:
        # 1. Reserve Stock
        for item in request.items:
            product_id = item.product_id
            variant_id = item.variant_id
            if not product_id:
                raise ValueError("Missing product_id for item")

            res = await inventory_client.reserve_stock(product_id, item.quantity, variant_id)
            reservation_ids.append(res["id"])

        # 2. Initiate Payment
        payment_order = await payment_service.create_payment_order(
            user_id=user.get("sub"),
            amount=int(request.total_amount * 100),
            currency=request.currency,
            metadata={"source": "tianaluxora-website"}
        )

        return {
            "payment": payment_order,
            "reservation_ids": reservation_ids
        }

    except ServiceError as e:
        # Release any reservations made
        for res_id in reservation_ids:
            try:
                await inventory_client.release_reservation(res_id)
            except Exception:
                pass
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"Checkout failed: {str(e)}", exc_info=True)
        for res_id in reservation_ids:
            try:
                await inventory_client.release_reservation(res_id)
            except Exception:
                pass
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify-payment")
async def verify_payment(data: VerifyPaymentRequest, user: dict = Depends(get_current_user)):
    """
    Step 2 of checkout flow:
    1. Verify payment
    2. Create order (ONLY NOW)
    3. Confirm stock reservations
    4. Claim coupon if applicable
    """
    try:
        # 1. Verify Payment
        await payment_service.verify_payment(
            razorpay_order_id=data.razorpay_order_id,
            razorpay_payment_id=data.razorpay_payment_id,
            razorpay_signature=data.razorpay_signature
        )

        # 2. Create Order in OMS
        order_data = data.order_data
        if not order_data:
            raise ValueError("Missing order_data for finalized order")

        # Sanitize item IDs to strings for OMS
        if "items" in order_data:
            for item in order_data["items"]:
                if item.get("variant_id") is not None:
                    item["variant_id"] = str(item["variant_id"])
                if item.get("product_id") is not None:
                    item["product_id"] = str(item["product_id"])

        order_data["status"] = "processing"
        order = await order_service.create_order(user.get("sub"), order_data)

        # 3. Confirm Reservations in Inventory
        for res_id in data.reservation_ids:
            try:
                await inventory_client.confirm_reservation(res_id)
            except Exception as e:
                logger.error(f"Failed to confirm reservation {res_id}: {e}")

        # 4. Claim coupon in Coupon Portal if coupon_id was attached
        coupon_id = data.coupon_id or order_data.get("coupon_id")
        if coupon_id:
            try:
                await coupon_client.claim_coupon({
                    "coupon_id": str(coupon_id),
                    "user_id": user.get("sub"),
                    "order_id": str(order.get("id") or order.get("_id") or ""),
                    "payment_verified": True
                })
            except Exception as claim_err:
                logger.error(f"Failed to claim coupon in coupon portal: {claim_err}", exc_info=True)

        return {"status": "success", "order": order}

    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"Order verification failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment verification or order creation failed: {str(e)}")


@router.post("/")
async def create_order(request: OrderCreate, user: dict = Depends(get_current_user)):
    """Create a new order via the OMS portal."""
    try:
        customer_name = user.get("name") or user.get("email") or "Customer"
        first_product_name = request.items[0].name if request.items else "Unknown Product"
        total_quantity = sum(item.quantity for item in request.items)

        formatted_items = []
        for item in request.items:
            formatted_items.append({
                "product_id": str(item.product_id),
                "variant_id": str(item.variant_id) if item.variant_id is not None else None,
                "variant_name": None,
                "product_name": item.name,
                "quantity": item.quantity,
                "unit_price": float(item.price),
                "image": item.image
            })

        order_data = {
            "customer_name": customer_name,
            "product_name": first_product_name,
            "quantity": total_quantity,
            "total_amount": float(request.total_amount),
            "currency": request.currency,
            "items": formatted_items,
        }
        return await order_service.create_order(user.get("sub"), order_data)
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/")
async def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, gt=0, le=100),
    user: dict = Depends(get_current_user),
):
    """Fetch user's order history from OMS portal."""
    try:
        return await order_service.get_orders(user.get("sub"), skip=skip, limit=limit)
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/{order_id}")
async def get_order(order_id: str, user: dict = Depends(get_current_user)):
    """Fetch single order detail."""
    try:
        return await order_service.get_order(order_id)
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
