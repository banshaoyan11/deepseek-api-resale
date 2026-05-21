# app/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/deepseek_api"
    REDIS_URL: str = "redis://localhost:6379"

    # DeepSeek API
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # PayPal
    PAYPAL_CLIENT_ID: str = ""
    PAYPAL_CLIENT_SECRET: str = ""
    PAYPAL_SANDBOX: bool = True

    # Stripe (备选)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""

    # Payment Provider
    PAYMENT_PROVIDER: str = "paypal"  # "paypal" or "stripe"

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # App
    DEBUG: bool = False
    BASE_URL: str = "http://localhost:8000"

    # Pricing (USD per million tokens)
    API_PRICING_INPUT: float = 0.30
    API_PRICING_OUTPUT: float = 0.50

    class Config:
        env_file = ".env"

settings = Settings()
