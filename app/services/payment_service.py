"""
Payment service — orchestrates payment creation and verification through the payment portal.
"""
from app.clients.payment_client import payment_client


class PaymentService:
    async def create_payment_order(self, user_id: str, amount: int, currency: str = "INR", plan_type: str = None, metadata: dict = None) -> dict:
        """Create a payment order via the payment portal."""
        return await payment_client.create_order(
            user_id=user_id,
            amount=amount,
            currency=currency,
            plan_type=plan_type,
            metadata=metadata,
        )

    async def verify_payment(self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> dict:
        """Verify payment signature through the payment portal."""
        return await payment_client.verify_payment(
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
        )

    async def get_status(self, order_id: str) -> dict:
        """Check payment status."""
        return await payment_client.get_payment_status(order_id)

    async def fail_payment(self, razorpay_order_id: str, reason: str = None) -> dict:
        """Mark a payment as failed."""
        return await payment_client.fail_payment(razorpay_order_id, reason)


payment_service = PaymentService()
