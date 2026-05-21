# DeepSeek API Resale Platform

OpenAI-compatible API gateway for reselling DeepSeek API tokens to overseas users.

## Features

- 🔐 User authentication and API key management
- 💳 Stripe payment integration
- 📊 Usage tracking and billing
- 🚀 OpenAI-compatible API endpoints
- 🔄 DeepSeek API proxy
- 💰 Multi-currency support

## Tech Stack

- **Backend**: Python FastAPI
- **Database**: PostgreSQL + Redis
- **Frontend**: Next.js (optional)
- **Payments**: Stripe
- **Deployment**: Docker, Railway, or any cloud provider

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Initialize Database

```bash
alembic upgrade head
```

### 4. Run Server

```bash
uvicorn app.main:app --reload
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/deepseek_api

# Redis
REDIS_URL=redis://localhost:6379

# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key

# Stripe
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx

# JWT
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# App
DEBUG=True
BASE_URL=http://localhost:8000
```

## License

MIT License
