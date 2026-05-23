# app/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os

from app.config import settings
from app.database import engine, Base
from app.models import User, APIKey, UsageLog, Transaction, PricingTier
from app.routers import auth_router, api_keys_router, billing_router, gateway_router, admin_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting DeepSeek API Resale Platform...")

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"DB init failed (app will start anyway): {e}")

    yield

    logger.info("Shutting down...")
    await engine.dispose()

app = FastAPI(
    title="DeepSeek API Resale Platform",
    description="OpenAI-compatible API gateway for reselling DeepSeek API tokens",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(api_keys_router)
app.include_router(billing_router)
app.include_router(gateway_router)
app.include_router(admin_router)

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

# Mount static assets for SPA frontend
if os.path.exists(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="static_assets")

@app.get("/")
async def root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"name": "DeepSeek API Resale Platform", "version": "1.0.0", "status": "operational"}

@app.get("/favicon.svg")
async def favicon():
    path = os.path.join(STATIC_DIR, "favicon.svg")
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404)

@app.get("/icons.svg")
async def icons():
    path = os.path.join(STATIC_DIR, "icons.svg")
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2026-05-21T00:00:00Z"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
