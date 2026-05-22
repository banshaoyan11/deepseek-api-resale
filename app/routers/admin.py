# app/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from app.database import get_db
from app.models import User, Transaction
from app.auth import get_current_user
from app.config import settings
import httpx

router = APIRouter(prefix="/admin", tags=["Admin"])

# Admin email list (hardcoded for now)
ADMIN_EMAILS = ["admin@deepseek-api-resale.com", "banshaoyan11@qq.com"]

async def get_admin_user(current_user=Depends(get_current_user)):
    """Check if current user is an admin"""
    if current_user.email not in ADMIN_EMAILS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@router.get("/system-status")
async def get_system_status(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_admin_user)
):
    """Get system status including DeepSeek API balance and warnings"""
    
    # Get total users
    total_users = await db.execute(select(func.count(User.id)))
    total_users = total_users.scalar_one()
    
    # Get total transactions
    total_transactions = await db.execute(select(func.count(Transaction.id)))
    total_transactions = total_transactions.scalar_one()
    
    # Get total revenue
    revenue = await db.execute(select(func.sum(Transaction.amount)))
    revenue = revenue.scalar_one() or 0.0
    
    # Get total user balances
    total_balances = await db.execute(select(func.sum(User.balance)))
    total_balances = total_balances.scalar_one() or 0.0
    
    # Check DeepSeek API balance
    deepseek_balance = await check_deepseek_balance()
    deepseek_warning = None
    if deepseek_balance is not None and deepseek_balance < 10.0:
        deepseek_warning = f"DeepSeek balance is low: ${deepseek_balance:.2f}"
    
    return {
        "status": "operational" if not deepseek_warning else "warning",
        "warnings": [deepseek_warning] if deepseek_warning else [],
        "metrics": {
            "total_users": total_users,
            "total_transactions": total_transactions,
            "total_revenue": revenue,
            "total_user_balances": total_balances,
            "deepseek_balance": deepseek_balance
        }
    }

@router.get("/users")
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_admin_user)
):
    """Get all users (admin only)"""
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [{
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "balance": user.balance,
        "created_at": user.created_at.isoformat()
    } for user in users]

@router.get("/transactions")
async def get_all_transactions(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_admin_user)
):
    """Get all transactions (admin only)"""
    result = await db.execute(select(Transaction).order_by(Transaction.created_at.desc()))
    transactions = result.scalars().all()
    return [{
        "id": t.id,
        "user_id": t.user_id,
        "type": t.transaction_type.value if hasattr(t.transaction_type, 'value') else t.transaction_type,
        "amount": t.amount,
        "description": t.description,
        "created_at": t.created_at.isoformat()
    } for t in transactions]

async def check_deepseek_balance():
    """Check DeepSeek API balance using their API"""
    if not settings.DEEPSEEK_API_KEY:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Try DeepSeek API balance endpoint
            response = await client.post(
                f"{settings.DEEPSEEK_BASE_URL}/v1/models",
                headers={
                    "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={}
            )
            
            if response.status_code == 402:
                # Payment required - balance is zero or insufficient
                return 0.0
            elif response.status_code == 200:
                # Extract balance from response headers if available
                balance_str = response.headers.get('x-remaining-balance')
                if balance_str:
                    return float(balance_str)
                
                # Try alternative approach - get usage info
                try:
                    usage_response = await client.post(
                        f"{settings.DEEPSEEK_BASE_URL}/v1/dashboard/usage",
                        headers={
                            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={"start_time": "2024-01-01", "end_time": "2030-01-01"}
                    )
                    if usage_response.status_code == 200:
                        data = usage_response.json()
                        # Try different possible fields
                        if 'balance' in data:
                            return float(data['balance'])
                        elif 'remaining_balance' in data:
                            return float(data['remaining_balance'])
                        elif 'total_available' in data:
                            return float(data['total_available'])
                except:
                    pass
                
                # If we can't get exact balance, return None (will show N/A)
                return None
            elif response.status_code == 401:
                # Unauthorized - invalid API key
                return None
            else:
                return None
    except Exception as e:
        print(f"Error checking DeepSeek balance: {e}")
        return None
