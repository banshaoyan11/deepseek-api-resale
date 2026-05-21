# app/services/payment.py
import stripe
from typing import Optional
from app.config import settings

class PaymentService:
    def __init__(self):
        self.base_url = settings.BASE_URL
        self._stripe_initialized = False

    def _init_stripe(self):
        if not self._stripe_initialized and settings.STRIPE_SECRET_KEY:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            self._stripe_initialized = True

    def create_checkout_session(
        self,
        user_id: int,
        amount: float,
        currency: str = "usd"
    ) -> dict:
        """Create a Stripe checkout session for top-up"""
        self._init_stripe()
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": currency,
                    "product_data": {
                        "name": "DeepSeek API Credits",
                        "description": f"${amount:.2f} credit for DeepSeek API usage"
                    },
                    "unit_amount": int(amount * 100),  # Convert to cents
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{self.base_url}/dashboard/billing?success=true&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{self.base_url}/dashboard/billing?canceled=true",
            metadata={
                "user_id": str(user_id),
                "amount": str(amount)
            },
            allow_promotion_codes=True,
        )

        return {
            "session_id": session.id,
            "checkout_url": session.url
        }

    def retrieve_checkout_session(self, session_id: str) -> dict:
        """Retrieve checkout session details"""
        self._init_stripe()
        session = stripe.checkout.Session.retrieve(session_id)
        return {
            "payment_status": session.payment_status,
            "amount_total": session.amount_total / 100,
            "metadata": session.metadata,
            "customer_email": session.customer_details.email if session.customer_details else None
        }

    def create_refund(self, payment_intent_id: str, amount: Optional[float] = None) -> dict:
        """Create a refund for a payment"""
        self._init_stripe()
        refund_params = {
            "payment_intent": payment_intent_id,
        }

        if amount:
            refund_params["amount"] = int(amount * 100)  # Convert to cents

        refund = stripe.Refund.create(**refund_params)

        return {
            "refund_id": refund.id,
            "status": refund.status,
            "amount": refund.amount / 100
        }

    def construct_webhook_event(self, payload: bytes, sig_header: str) -> stripe.Event:
        """Construct and verify Stripe webhook event"""
        self._init_stripe()
        return stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )

payment_service = PaymentService()
