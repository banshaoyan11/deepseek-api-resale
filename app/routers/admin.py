# app/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from datetime import datetime
from app.database import get_db
from app.models import User, Transaction, SystemSetting
from app.auth import get_current_user
from app.config import settings
import httpx
import asyncio

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
    
    # Get cached DeepSeek balance
    deepseek_balance = await get_cached_deepseek_balance(db)
    deepseek_balance_updated = await get_deepseek_balance_updated_at(db)
    
    # Check if balance is low
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
            "deepseek_balance": deepseek_balance,
            "deepseek_balance_updated": deepseek_balance_updated
        }
    }

@router.post("/refresh-balance")
async def refresh_deepseek_balance(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_admin_user)
):
    """Manually refresh DeepSeek API balance"""
    balance = await check_deepseek_balance()
    
    if balance is not None:
        await save_deepseek_balance(db, balance)
        return {
            "success": True,
            "balance": balance,
            "message": f"Balance updated to ${balance:.2f}"
        }
    else:
        return {
            "success": False,
            "balance": None,
            "message": "Failed to fetch balance from DeepSeek API"
        }

@router.post("/set-balance")
async def set_deepseek_balance(
    balance: float,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_admin_user)
):
    """Manually set DeepSeek API balance"""
    if balance < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Balance cannot be negative"
        )
    
    await save_deepseek_balance(db, balance)
    
    return {
        "success": True,
        "balance": balance,
        "message": f"Balance manually set to ${balance:.2f}"
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
    import logging
    logger = logging.getLogger(__name__)
    
    if not settings.DEEPSEEK_API_KEY:
        logger.warning("DEEPSEEK_API_KEY not configured")
        return None
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Try DeepSeek's balance endpoint - common format
            endpoints = [
                (f"{settings.DEEPSEEK_BASE_URL}/v1/balance", "GET"),
                (f"{settings.DEEPSEEK_BASE_URL}/v1/user/balance", "GET"),
                (f"{settings.DEEPSEEK_BASE_URL}/v1/dashboard/billing/subscription", "GET"),
                (f"{settings.DEEPSEEK_BASE_URL}/v1/balance", "POST"),
            ]
            
            for endpoint, method in endpoints:
                try:
                    logger.info(f"Trying endpoint: {endpoint} ({method})")
                    
                    if method == "GET":
                        response = await client.get(
                            endpoint,
                            headers={
                                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                                "Content-Type": "application/json"
                            }
                        )
                    else:
                        response = await client.post(
                            endpoint,
                            headers={
                                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                                "Content-Type": "application/json"
                            },
                            json={}
                        )
                    
                    logger.info(f"Response from {endpoint}: status={response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"Response data: {data}")
                        
                        # Try different possible response formats
                        balance = None
                        if isinstance(data, dict):
                            for key in ['balance', 'total_balance', 'available_balance', 
                                       'amount', 'remaining', 'credit_balance']:
                                if key in data:
                                    try:
                                        balance = float(data[key])
                                        logger.info(f"Found balance in '{key}': {balance}")
                                        return balance
                                    except (ValueError, TypeError):
                                        continue
                        
                        # If balance found in response
                        if balance is not None:
                            return balance
                            
                    elif response.status_code == 402:
                        # Payment required - balance is zero
                        logger.info("Got 402 - balance is zero")
                        return 0.0
                    elif response.status_code == 401:
                        logger.error("Invalid DeepSeek API key")
                        return None
                    elif response.status_code == 404:
                        logger.info(f"Endpoint not found: {endpoint}")
                        continue
                    else:
                        logger.info(f"Unexpected status: {response.status_code}")
                        continue
                        
                except Exception as e:
                    logger.warning(f"Error with {endpoint}: {str(e)}")
                    continue
            
            logger.warning("All balance endpoints failed")
            return None
            
    except httpx.TimeoutException:
        logger.error("Timeout while checking DeepSeek balance")
        return None
    except Exception as e:
        logger.error(f"Error checking DeepSeek balance: {str(e)}", exc_info=True)
        return None

async def save_deepseek_balance(db: AsyncSession, balance: float):
    """Save DeepSeek balance to database"""
    try:
        result = await db.execute(
            select(SystemSetting).where(SystemSetting.key == "deepseek_balance")
        )
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = str(balance)
            setting.updated_at = datetime.utcnow()
        else:
            setting = SystemSetting(
                key="deepseek_balance",
                value=str(balance)
            )
            db.add(setting)
        
        await db.commit()
    except Exception as e:
        print(f"Error saving DeepSeek balance: {e}")
        await db.rollback()

async def get_cached_deepseek_balance(db: AsyncSession) -> float | None:
    """Get cached DeepSeek balance from database"""
    try:
        result = await db.execute(
            select(SystemSetting).where(SystemSetting.key == "deepseek_balance")
        )
        setting = result.scalar_one_or_none()
        if setting and setting.value:
            return float(setting.value)
        return None
    except Exception as e:
        print(f"Error getting cached balance: {e}")
        return None

async def get_deepseek_balance_updated_at(db: AsyncSession) -> str | None:
    """Get last update time of DeepSeek balance"""
    try:
        result = await db.execute(
            select(SystemSetting).where(SystemSetting.key == "deepseek_balance")
        )
        setting = result.scalar_one_or_none()
        if setting and setting.updated_at:
            return setting.updated_at.isoformat()
        return None
    except Exception as e:
        print(f"Error getting balance update time: {e}")
        return None
