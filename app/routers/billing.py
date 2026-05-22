# app/routers/billing.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models import User, Transaction
from app.schemas import TopUpRequest, TopUpResponse, UsageStats, TransactionResponse
from app.auth import get_current_user
from app.services import billing_service
from app.services.paypal import paypal_service
from app.services.payment import payment_service  # Stripe
from app.config import settings

router = APIRouter(prefix="/billing", tags=["Billing"])

@router.get("/balance")
async def get_balance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user balance"""
    # Check if system balance is low
    system_warning = await check_system_balance()
    
    return {
        "balance": current_user.balance,
        "currency": "USD",
        "payment_provider": settings.PAYMENT_PROVIDER,
        "system_warning": system_warning
    }

async def check_system_balance():
    """Check if DeepSeek API balance is low and return warning message"""
    if not settings.DEEPSEEK_API_KEY:
        return None
    
    # Minimum threshold: $10
    MIN_BALANCE = 10.0
    
    try:
        # Try to get DeepSeek balance (simplified check)
        # In production, you would call DeepSeek API to get actual balance
        # For now, we'll simulate based on recent transaction volume
        return None  # No warning if we can't check
    except Exception:
        return None

@router.post("/top-up", response_model=TopUpResponse)
async def create_top_up(
    top_up_data: TopUpRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a payment checkout session for top-up"""
    if top_up_data.amount < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum top-up amount is $1"
        )

    if top_up_data.amount > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum top-up amount is $1000"
        )

    # Use PayPal or Stripe based on configuration
    if settings.PAYMENT_PROVIDER == "paypal":
        try:
            # PayPal payment
            order = await paypal_service.create_order(
                amount=top_up_data.amount,
                user_id=current_user.id
            )

            return {
                "checkout_url": paypal_service.get_checkout_url(order["id"]),
                "session_id": order["id"],
                "order_id": order["id"],
                "provider": "paypal"
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PayPal payment creation failed: {str(e)}"
            )

    else:
        # Stripe payment (fallback)
        try:
            checkout_data = payment_service.create_checkout_session(
                user_id=current_user.id,
                amount=top_up_data.amount
            )

            return {
                "checkout_url": checkout_data["checkout_url"],
                "session_id": checkout_data["session_id"],
                "provider": "stripe"
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Stripe payment creation failed: {str(e)}"
            )

@router.get("/paypal/check/{order_id}")
async def check_paypal_order(
    order_id: str
):
    """Check PayPal order status"""
    try:
        order = await paypal_service.get_order(order_id)
        return {
            "status": order.get("status", "unknown").lower(),
            "order_id": order_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check order: {str(e)}"
        )

@router.get("/paypal/success")
async def paypal_success(request: Request):
    """PayPal payment success redirect page"""
    # Get token from query parameter
    token = request.query_params.get("token")
    
    # Return HTML page that redirects to frontend topup page
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Payment Successful</title>
        <script>
            // Send message to opener window if it exists
            if (window.opener) {{
                window.opener.postMessage({{ type: 'paypal_payment_success', token: '{token}' }}, '*');
            }}
            // Redirect to topup page
            setTimeout(function() {{
                window.location.href = '/#topup';
            }}, 1000);
        </script>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; padding-top: 100px; background: #1a1a2e; color: #fff; }}
            .spinner {{ width: 50px; height: 50px; border: 5px solid #3498db; border-top-color: #2ecc71; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }}
            @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        </style>
    </head>
    <body>
        <div class="spinner"></div>
        <h1>Payment Successful!</h1>
        <p>Redirecting to your account...</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/paypal/cancel")
async def paypal_cancel():
    """PayPal payment cancel redirect page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Payment Cancelled</title>
        <script>
            setTimeout(function() {
                window.location.href = '/#topup';
            }, 2000);
        </script>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding-top: 100px; background: #1a1a2e; color: #fff; }
        </style>
    </head>
    <body>
        <h1>Payment Cancelled</h1>
        <p>Redirecting to payment page...</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.post("/paypal/capture/{order_id}")
async def capture_paypal_order(
    order_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Capture PayPal order after user approval (called from frontend)"""
    print(f"=== PayPal capture called for order_id: {order_id} ===")
    try:
        # Verify order status
        print("Getting order details...")
        order = await paypal_service.get_order(order_id)
        print(f"Order status: {order.get('status')}")
        print(f"Full order: {order}")

        if order["status"] != "COMPLETED":
            # Capture the payment
            print("Order not completed, capturing...")
            capture_result = await paypal_service.capture_order(order_id)
            order = capture_result
            print(f"Capture result status: {order.get('status')}")
            print(f"Full capture result: {order}")

        # Extract amount from captured order
        user_id = None
        amount = 0.0

        print("Extracting purchase units...")
        for purchase_unit in order.get("purchase_units", []):
            print(f"Purchase unit: {purchase_unit}")
            amount = float(purchase_unit["amount"]["value"])
            if "custom_id" in purchase_unit:
                user_id = int(purchase_unit["custom_id"])
                print(f"Found custom_id (user_id): {user_id}")

        print(f"Extracted: user_id={user_id}, amount={amount}")

        if not user_id:
            print("ERROR: Missing user_id!")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid order: missing user ID"
            )

        # Credit the user's account
        print(f"Adding balance to user {user_id}...")
        try:
            await billing_service.add_balance(
                user_id=user_id,
                amount=amount,
                db=db,
                payment_reference=order_id
            )

            print("Balance added successfully!")
            return {
                "status": "success",
                "order_id": order_id,
                "amount": amount,
                "user_id": user_id
            }
        except ValueError:
            print("ERROR: User not found!")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PayPal capture failed: {str(e)}"
        )

@router.post("/webhook/paypal")
async def paypal_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle PayPal webhook events"""
    try:
        payload = await request.json()

        # Log webhook for debugging
        event_type = payload.get("event_type")
        print(f"PayPal webhook received: {event_type}")

        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            # Extract payment details
            resource = payload.get("resource", {})

            # Find user by custom_id or transaction
            amount = float(resource.get("amount", {}).get("value", 0))

            # For now, you would need to track the user_id separately
            # This requires setting up PayPal Webhooks in your PayPal Dashboard

        return {"status": "received"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PayPal webhook error: {str(e)}"
        )

@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = payment_service.construct_webhook_event(payload, sig_header)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook signature verification failed: {str(e)}"
        )

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = int(session["metadata"]["user_id"])
        amount = float(session["metadata"]["amount"])

        # Credit the user's account
        try:
            await billing_service.add_balance(
                user_id=user_id,
                amount=amount,
                db=db,
                payment_reference=session["payment_intent"]
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

    return {"status": "success"}

@router.get("/usage/stats", response_model=UsageStats)
async def get_usage_stats(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get usage statistics for the current user"""
    if days < 1 or days > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Days must be between 1 and 365"
        )

    stats = await billing_service.get_usage_stats(
        user_id=current_user.id,
        db=db,
        days=days
    )

    return stats

@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get transaction history for the current user"""
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
    )
    transactions = result.scalars().all()
    return transactions
