# app/services/paypal.py
import httpx
import base64
from typing import Optional, Dict, Any
from app.config import settings

class PayPalService:
    def __init__(self):
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self.base_url = "https://api-m.sandbox.paypal.com" if settings.PAYPAL_SANDBOX else "https://api-m.paypal.com"
        self.access_token = None

    async def get_access_token(self) -> str:
        """Get PayPal access token"""
        if self.access_token:
            return self.access_token

        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/oauth2/token",
                headers={
                    "Authorization": f"Basic {auth}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={"grant_type": "client_credentials"}
            )

            if response.status_code == 200:
                self.access_token = response.json()["access_token"]
                return self.access_token
            else:
                raise Exception(f"PayPal auth failed: {response.text}")

    async def create_order(self, amount: float, currency: str = "USD", user_id: int = None) -> Dict[str, Any]:
        """Create a PayPal order"""
        access_token = await self.get_access_token()

        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": currency,
                    "value": f"{amount:.2f}"
                },
                "description": "DeepSeek API Credits",
                "custom_id": str(user_id) if user_id else None
            }],
            "application_context": {
                "brand_name": "DeepSeek API Resale",
                "landing_page": "LOGIN",
                "shipping_preference": "NO_SHIPPING",
                "user_action": "PAY_NOW"
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v2/checkout/orders",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json=order_data
            )

            if response.status_code in [200, 201]:
                return response.json()
            else:
                raise Exception(f"PayPal order creation failed: {response.text}")

    async def capture_order(self, order_id: str) -> Dict[str, Any]:
        """Capture a PayPal order after approval"""
        access_token = await self.get_access_token()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v2/checkout/orders/{order_id}/capture",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
            )

            if response.status_code == 201:
                return response.json()
            else:
                raise Exception(f"PayPal capture failed: {response.text}")

    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get order details"""
        access_token = await self.get_access_token()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/v2/checkout/orders/{order_id}",
                headers={
                    "Authorization": f"Bearer {access_token}"
                }
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"PayPal get order failed: {response.text}")

    def get_checkout_url(self, order_id: str) -> str:
        """Get PayPal checkout URL"""
        if settings.PAYPAL_SANDBOX:
            return f"https://www.sandbox.paypal.com/checkoutnow?token={order_id}"
        else:
            return f"https://www.paypal.com/checkoutnow?token={order_id}"

paypal_service = PayPalService()
