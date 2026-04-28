import httpx
import logging
from app.core.config import settings
from app.core.http_client import get_async_client

logger = logging.getLogger("tiana-bff")

class PaymentService:
    def __init__(self):
        self.base_url = f"{settings.PAYMENT_PORTAL_API_URL}/payments"
        self.api_key = settings.PAYMENT_PORTAL_API_KEY
        self.api_secret = settings.PAYMENT_PORTAL_API_SECRET

    async def create_payment_order(self, order_id: str, amount: int, currency: str, user_id: str):
        """
        Creates a payment order in the Payment Portal (Razorpay Order).
        amount: In lowest currency unit (e.g. paisa for INR)
        """
        async with get_async_client() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/create-order",
                    headers={
                        "X-APP-KEY": self.api_key,
                        "X-APP-SECRET": self.api_secret
                    },
                    json={
                        "amount": amount,
                        "currency": currency,
                        "user_id": user_id,
                        "metadata_info": {"order_id": order_id}
                    }
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Payment Portal Error ({e.response.status_code}): {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Payment Portal Connection Error: {e}")
                raise

    async def verify_payment(self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str):
        """
        Verifies the payment signature via the Payment Portal.
        """
        async with get_async_client() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/verify-payment",
                    headers={
                        "X-APP-KEY": self.api_key,
                        "X-APP-SECRET": self.api_secret
                    },
                    json={
                        "razorpay_order_id": razorpay_order_id,
                        "razorpay_payment_id": razorpay_payment_id,
                        "razorpay_signature": razorpay_signature
                    }
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Payment Verification Portal Error ({e.response.status_code}): {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Payment Verification Connection Error: {e}")
                raise 

payment_service = PaymentService()
