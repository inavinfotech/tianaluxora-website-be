import logging
import hmac
import hashlib
import json
from fastapi import APIRouter, Request, HTTPException, status
from app.services.order_service import order_service
from app.services.payment_service import payment_service
from app.core.config import settings

logger = logging.getLogger("tiana-bff.webhooks")

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/payment")
async def payment_webhook(request: Request):
    """
    Asynchronous payment webhook endpoint for portal-payment events.
    Handles payment.success and payment.failed events even if user closes app.
    """
    body_bytes = await request.body()
    signature = request.headers.get("X-Webhook-Signature")
    
    # Optional HMAC Verification if secret is configured
    webhook_secret = getattr(settings, "WEBHOOK_SECRET", "default_webhook_secret")
    if signature and webhook_secret:
        expected_sig = hmac.new(webhook_secret.encode('utf-8'), body_bytes, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            logger.warning("Invalid webhook signature received")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    try:
        payload = json.loads(body_bytes)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON body")

    event = payload.get("event")
    data = payload.get("data", {})
    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")

    if event == "payment.success" and razorpay_order_id:
        logger.info(f"Processing payment.success webhook for razorpay_order_id={razorpay_order_id}")
        try:
            # Idempotently verify and punch order in OMS
            metadata = data.get("metadata") or {}
            order_data = metadata.get("order_data")
            reservation_ids = metadata.get("reservation_ids", [])
            coupon_id = metadata.get("coupon_id")
            coupon_code = metadata.get("coupon_code")

            if order_data:
                await order_service.verify_and_punch_order(
                    razorpay_order_id=razorpay_order_id,
                    razorpay_payment_id=razorpay_payment_id,
                    razorpay_signature=data.get("razorpay_signature", "webhook_verified"),
                    order_data=order_data,
                    reservation_ids=reservation_ids,
                    coupon_id=coupon_id,
                    coupon_code=coupon_code
                )
        except Exception as e:
            logger.error(f"Error handling payment.success webhook: {e}")
            # Still return 200 to acknowledge webhook receipt
            return {"status": "error", "detail": str(e)}

    return {"status": "success"}
