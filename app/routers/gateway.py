# app/routers/gateway.py
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import time
import logging
from collections import defaultdict
from datetime import datetime
from app.database import get_db
from app.models import User, APIKey
from app.auth import verify_api_key, verify_api_key_anthropic

logger = logging.getLogger("gateway")
from app.services import deepseek_service, billing_service

router = APIRouter(tags=["API Gateway"])


def _extract_api_key_str(auth_header: str) -> str:
    return auth_header.replace("Bearer ", "").strip()


async def _get_api_key_record(api_key_str: str, db: AsyncSession):
    result = await db.execute(
        select(APIKey).where(APIKey.key == api_key_str)
    )
    return result.scalar_one_or_none()


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

    auth_header = request.headers.get("authorization")
    user = await verify_api_key(auth_header, db)

    try:
        request_data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body"
        )

    if "messages" not in request_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'messages' field"
        )

    model = request_data.get("model", "deepseek-v4-flash")
    msg_count = len(request_data.get("messages", []))
    has_tools = "tools" in request_data
    logger.info(f"[REQ] model={model} messages={msg_count} has_tools={has_tools}")

    total_text = ""
    for msg in request_data["messages"]:
        if isinstance(msg, dict):
            total_text += str(msg.get("content", ""))

    estimated_input_tokens = deepseek_service.estimate_token_count(total_text, model)
    estimated_cost = deepseek_service.calculate_cost(
        estimated_input_tokens,
        request_data.get("max_tokens", 1000)
    )

    has_balance = await billing_service.check_balance(user.id, estimated_cost, db)
    if not has_balance:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient balance. Required: ${estimated_cost:.4f}, Available: ${user.balance:.4f}"
        )

    try:
        response = await deepseek_service.chat_completions(request_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"DeepSeek API error: {str(e)}"
        )

    chat_content = ""
    for choice in response.get("choices", []):
        chat_content += str(choice.get("message", {}).get("content", ""))
    logger.info(f"[CHAT] model={model} tokens=in:{response.get('usage',{}).get('prompt_tokens',0)}/out:{response.get('usage',{}).get('completion_tokens',0)} content_preview={chat_content[:200]}")

    usage = response.get("usage", {})
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    actual_cost = deepseek_service.calculate_cost(input_tokens, output_tokens)

    await billing_service.deduct_balance(user.id, actual_cost, db)

    response_time_ms = int((time.time() - start_time) * 1000)

    api_key_str = _extract_api_key_str(auth_header)
    api_key = await _get_api_key_record(api_key_str, db)

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


@router.api_route("/anthropic/v1/messages", methods=["POST", "OPTIONS"])
async def anthropic_messages(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Anthropic-compatible messages endpoint.
    Proxies requests to DeepSeek Anthropic API with billing.
    Use x-api-key or Authorization: Bearer header for authentication.
    """
    start_time = time.time()

    user = await verify_api_key_anthropic(request, db)

    try:
        request_data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body"
        )

    model = request_data.get("model", "deepseek-v4-flash")
    max_tokens = request_data.get("max_tokens", 1000)

    estimated_input_tokens = deepseek_service.estimate_anthropic_tokens(request_data)
    estimated_cost = deepseek_service.calculate_cost(
        estimated_input_tokens,
        max_tokens
    )

    has_balance = await billing_service.check_balance(user.id, estimated_cost, db)
    if not has_balance:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient balance. Required: ${estimated_cost:.4f}, Available: ${user.balance:.4f}"
        )

    try:
        response = await deepseek_service.anthropic_messages(request_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"DeepSeek API error: {str(e)}"
        )

    usage = response.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    actual_cost = deepseek_service.calculate_cost(input_tokens, output_tokens)

    await billing_service.deduct_balance(user.id, actual_cost, db)

    response_time_ms = int((time.time() - start_time) * 1000)

    api_key_str = request.headers.get("x-api-key", "").strip()
    if not api_key_str:
        auth_header = request.headers.get("authorization", "")
        api_key_str = _extract_api_key_str(auth_header)
    api_key = await _get_api_key_record(api_key_str, db)

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


# ===== Playground: rate-limited demo for unauthenticated users =====

_playground_quota = defaultdict(lambda: {"count": 0, "reset_at": 0})

@router.post("/playground/chat")
async def playground_chat(request: Request):
    """Free trial chat — rate limited per IP (max 20/day). No auth required."""
    import time as _time
    now = _time.time()
    ip = request.client.host if request.client else "unknown"
    quota = _playground_quota[ip]

    if now > quota["reset_at"]:
        quota["count"] = 0
        quota["reset_at"] = now + 86400

    if quota["count"] >= 20:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Free trial limit reached (20/day). Please sign up for unlimited access."
        )

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

    msg = body.get("message", "")
    if not msg or len(msg) > 4000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message required (max 4000 chars)")

    model = body.get("model", "deepseek-v4-flash")
    if model not in ("deepseek-v4-flash", "deepseek-v4-pro"):
        model = "deepseek-v4-flash"

    try:
        response = await deepseek_service.chat_completions({
            "model": model,
            "messages": [{"role": "user", "content": msg}],
            "max_tokens": 1024
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"DeepSeek API error: {str(e)}"
        )

    quota["count"] += 1
    content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
    remaining = max(0, 20 - quota["count"])

    return {"reply": content, "model": model, "remaining": remaining}

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
