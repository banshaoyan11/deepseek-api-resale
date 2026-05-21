# app/services/billing.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional
import redis.asyncio as redis
from app.config import settings
from app.models import User, UsageLog, Transaction, APIKey

class BillingService:
    def __init__(self):
        self.redis_client = None

    async def get_redis(self):
        if self.redis_client is None:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self.redis_client

    async def check_balance(self, user_id: int, required_amount: float, db: AsyncSession) -> bool:
        """Check if user has sufficient balance"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return user and user.balance >= required_amount

    async def deduct_balance(self, user_id: int, amount: float, db: AsyncSession) -> bool:
        """Deduct balance from user account"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or user.balance < amount:
            return False

        user.balance -= amount

        # Record transaction
        transaction = Transaction(
            user_id=user_id,
            amount=-amount,
            transaction_type="charge",
            description=f"API usage charge: ${amount:.4f}"
        )
        db.add(transaction)

        await db.commit()
        return True

    async def add_balance(self, user_id: int, amount: float, db: AsyncSession, stripe_payment_id: Optional[str] = None):
        """Add balance to user account"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        user.balance += amount

        # Record transaction
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            transaction_type="deposit",
            stripe_payment_id=stripe_payment_id,
            description=f"Balance top-up via Stripe: ${amount:.2f}"
        )
        db.add(transaction)

        await db.commit()

    async def record_usage(
        self,
        user_id: int,
        api_key_id: int,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        request_data: str,
        response_time_ms: int,
        db: AsyncSession
    ):
        """Record API usage"""
        usage_log = UsageLog(
            user_id=user_id,
            api_key_id=api_key_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            request_data=request_data,
            response_time_ms=response_time_ms
        )
        db.add(usage_log)

        # Update API key last used time
        result = await db.execute(select(APIKey).where(APIKey.id == api_key_id))
        api_key = result.scalar_one_or_none()
        if api_key:
            api_key.last_used_at = datetime.utcnow()

        await db.commit()

    async def get_usage_stats(self, user_id: int, db: AsyncSession, days: int = 30) -> dict:
        """Get usage statistics for user"""
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=days)

        result = await db.execute(
            select(UsageLog).where(
                UsageLog.user_id == user_id,
                UsageLog.created_at >= start_date
            )
        )
        logs = result.scalars().all()

        total_input_tokens = sum(log.input_tokens for log in logs)
        total_output_tokens = sum(log.output_tokens for log in logs)
        total_cost = sum(log.cost for log in logs)

        return {
            "period_days": days,
            "total_requests": len(logs),
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_cost": total_cost,
            "average_cost_per_request": total_cost / len(logs) if logs else 0
        }

billing_service = BillingService()
