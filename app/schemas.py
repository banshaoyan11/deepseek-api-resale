# app/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# Auth Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    is_verified: bool
    balance: float
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# API Key Schemas
class APIKeyCreate(BaseModel):
    name: str = "Default Key"

class APIKeyResponse(BaseModel):
    id: int
    key: str
    name: str
    is_active: bool
    rate_limit: int
    created_at: datetime
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True

# Billing Schemas
class TopUpRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount in USD")

class TopUpResponse(BaseModel):
    checkout_url: str
    session_id: str

class UsageStats(BaseModel):
    period_days: int
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost: float
    average_cost_per_request: float

class TransactionResponse(BaseModel):
    id: int
    amount: float
    transaction_type: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# DeepSeek API Schemas (OpenAI Compatible)
class ChatMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str = "deepseek-v4-flash"
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None

class UsageInfo(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: UsageInfo
