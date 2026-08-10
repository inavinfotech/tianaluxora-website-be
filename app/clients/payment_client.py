"""
Client for the Payment Portal microservice.
Creates payment orders and verifies payment signatures via Razorpay through the payment service.
"""
from app.clients.base import BaseClient
from app.core.config import settings


class PaymentClient(BaseClient):
    def __init__(self):
        super().__init__(
            base_url=settings.PAYMENT_SERVICE_URL,
            api_key=settings.PAYMENT_SERVICE_API_KEY,
            api_secret=settings.PAYMENT_SERVICE_API_SECRET,
            service_name="PaymentPortal",
        )

    def _auth_headers(self, bearer_token: str = None) -> dict:
        """Override to use x-app-key and x-app-secret for the payment portal."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-app-key"] = self.api_key
        if self.api_secret:
            headers["x-app-secret"] = self.api_secret
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"
        return headers

    async def create_order(self, user_id: str, amount: int, currency: str = "INR", plan_type: str = None, metadata: dict = None) -> dict:
        """Create a Razorpay payment order."""
        payload = {
            "user_id": user_id,
            "amount": amount,
            "currency": currency,
        }
        if plan_type:
            payload["plan_type"] = plan_type
        if metadata:
            payload["metadata_info"] = metadata
        return await self.post("/api/v1/payments/create-order", json=payload)

    async def verify_payment(self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> dict:
        """Verify payment signature after checkout."""
        return await self.post(
            "/api/v1/payments/verify-payment",
            json={
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            },
        )

    async def get_payment_status(self, order_id: str) -> dict:
        """Check payment status by Razorpay order ID."""
        return await self.get(f"/api/v1/payments/payment-status/{order_id}")

    async def fail_payment(self, razorpay_order_id: str, reason: str = None) -> dict:
        """Mark a payment as failed."""
        return await self.post(
            "/api/v1/payments/fail",
            json={"razorpay_order_id": razorpay_order_id, "reason": reason},
        )


payment_client = PaymentClient()
