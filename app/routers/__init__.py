# app/routers/__init__.py
from app.routers.auth import router as auth_router
from app.routers.api_keys import router as api_keys_router
from app.routers.billing import router as billing_router
from app.routers.gateway import router as gateway_router
from app.routers.admin import router as admin_router

__all__ = ["auth_router", "api_keys_router", "billing_router", "gateway_router", "admin_router"]
