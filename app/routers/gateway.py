# app/routers/gateway.py
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import time
from datetime import datetime
from app.database import get_db
from app.models import User, APIKey
from app.auth import verify_api_key
from app.services import deepseek_service, billing_service

router = APIRouter(tags=["API Gateway"])

@router.api_route("/v1/chat/completions", methods=["POST", "OPTIONS"])
async def chat_completions(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    OpenAI-compatible chat completions endpoint.
    Proxies requests to DeepSeek API with billing.
    """
    start_time = time.time()

    # 1. Verify API key
    auth_header = request.headers.get("authorization")
    user = await verify_api_key(auth_header, db)

    # 2. Get request body
    try:
        request_data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body"
        )

    # 3. Validate request
    if "messages" not in request_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'messages' field"
        )

    model = request_data.get("model", "deepseek-v4-flash")

    # 4. Estimate cost before request
    total_text = ""
    for msg in request_data["messages"]:
        if isinstance(msg, dict):
            total_text += str(msg.get("content", ""))

    estimated_input_tokens = deepseek_service.estimate_token_count(total_text, model)
    estimated_cost = deepseek_service.calculate_cost(
        estimated_input_tokens,
        request_data.get("max_tokens", 1000)
    )

    # 5. Check balance
    has_balance = await billing_service.check_balance(user.id, estimated_cost, db)
    if not has_balance:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient balance. Required: ${estimated_cost:.4f}, Available: ${user.balance:.4f}"
        )

    # 6. Call DeepSeek API
    try:
        response = await deepseek_service.chat_completions(request_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"DeepSeek API error: {str(e)}"
        )

    # 7. Calculate actual cost from response
    usage = response.get("usage", {})
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    actual_cost = deepseek_service.calculate_cost(input_tokens, output_tokens)

    # 8. Deduct balance
    await billing_service.deduct_balance(user.id, actual_cost, db)

    # 9. Record usage
    response_time_ms = int((time.time() - start_time) * 1000)

    # Get API key ID
    result = await db.execute(
        select(APIKey).where(
            APIKey.key == auth_header.replace("Bearer ", "")
        )
    )
    api_key = result.scalar_one_or_none()

    await billing_service.record_usage(
        user_id=user.id,
        api_key_id=api_key.id if api_key else 0,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost=actual_cost,
        request_data=json.dumps(request_data),
        response_time_ms=response_time_ms,
        db=db
    )

    return response

@router.get("/v1/models")
async def list_models():
    """List available models (OpenAI-compatible endpoint)"""
    return {
        "object": "list",
        "data": [
            {
                "id": "deepseek-v4-flash",
                "object": "model",
                "created": 1700000000,
                "owned_by": "deepseek"
            },
            {
                "id": "deepseek-v4-pro",
                "object": "model",
                "created": 1700000000,
                "owned_by": "deepseek"
            }
        ]
    }

@router.get("/v1/usage")
async def get_usage(
    start_date: str = None,
    end_date: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(__import__("app.auth", fromlist=["get_current_user"]).get_current_user)
):
    """Get usage statistics (OpenAI-compatible endpoint)"""
    from datetime import datetime, timedelta

    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.utcnow().strftime("%Y-%m-%d")

    stats = await billing_service.get_usage_stats(
        user_id=current_user.id,
        db=db,
        days=7
    )

    return {
        "object": "list",
        "data": [
            {
                "id": f"usage-{start_date}-{end_date}",
                "object": "usage",
                "start_date": start_date,
                "end_date": end_date,
                "total_tokens": stats["total_input_tokens"] + stats["total_output_tokens"],
                "prompt_tokens": stats["total_input_tokens"],
                "completion_tokens": stats["total_output_tokens"],
                "total_cost": stats["total_cost"]
            }
        ]
    }
