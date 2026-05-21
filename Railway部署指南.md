# Railway Deployment Guide

## Prerequisites
- Railway account (https://railway.app)
- GitHub account
- DeepSeek API key
- Stripe account with API keys
- Purchased domain name

## Step 1: Push to GitHub

1. Initialize git repository
```bash
cd D:\DeepSeek_API_Resale_Platform
git init
git add .
git commit -m "Initial commit"
```

2. Create GitHub repository
- Go to https://github.com/new
- Create a new repository (e.g., "deepseek-api-resale")
- Push your code:
```bash
git remote add origin https://github.com/YOUR_USERNAME/deepseek-api-resale.git
git push -u origin main
```

## Step 2: Deploy to Railway

### 2.1 Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account
5. Select your repository

### 2.2 Add Services

Railway will automatically detect and deploy from Dockerfile. You'll need to add:

#### Database (PostgreSQL)
1. Click "New" → "Database" → "PostgreSQL"
2. Railway will provision a PostgreSQL instance
3. Copy the connection string (DATABASE_URL)

#### Redis (Optional - for caching)
1. Click "New" → "Database" → "Redis"
2. Railway will provision a Redis instance
3. Copy the connection string (REDIS_URL)

### 2.3 Configure Environment Variables

In Railway dashboard, go to your service → "Variables" tab and add:

```
# Required Variables
DEEPSEEK_API_KEY=your_deepseek_api_key_here
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxx
SECRET_KEY=generate_a_secure_random_string_here

# Auto-filled by Railway
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379
PORT=8000

# Your domain
BASE_URL=https://yourdomain.com

# Pricing (optional)
API_PRICING_INPUT=0.30
API_PRICING_OUTPUT=0.50
DEBUG=false
```

### 2.4 Generate Secret Key

Generate a secure random key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2.5 Configure Stripe Webhook

1. Go to Stripe Dashboard → Developers → Webhooks
2. Click "Add endpoint"
3. Endpoint URL: `https://yourdomain.com/billing/webhook/stripe`
4. Select events:
   - `checkout.session.completed`
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
5. Copy the webhook signing secret

## Step 3: Domain Configuration

### 3.1 Add Domain in Railway

1. Go to your service settings
2. Click "Networking" → "Custom Domains"
3. Add your domain (e.g., `api.yourdomain.com`)
4. Verify domain ownership

### 3.2 Configure DNS

In your domain registrar (Cloudflare/Namecheap):

**Option A: CNAME (if Railway provides a domain)**
```
Type: CNAME
Name: api (or www)
Value: your-railway-app.railway.app
TTL: Auto
```

**Option B: A Record (direct IP)**
```
Type: A
Name: api
Value: [Railway provided IP]
TTL: Auto
```

### 3.3 Enable HTTPS

Railway automatically provisions SSL certificates. Make sure to:
- Enable "Always Use HTTPS" in Railway settings
- Or configure in Cloudflare to force HTTPS

## Step 4: Verify Deployment

### 4.1 Check Health
```bash
curl https://yourdomain.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-05-21T00:00:00Z"
}
```

### 4.2 Test Stripe Integration

1. Create a test user via API
2. Attempt a top-up
3. Check if Stripe checkout session is created
4. Complete test payment
5. Verify balance is credited

## Step 5: Monitor and Debug

### View Logs
```bash
railway logs -t
```

### Connect to Database
```bash
railway run psql $DATABASE_URL
```

### Shell Access
```bash
railway shell
```

## Cost Estimation

| Resource | Free Tier | Paid |
|----------|-----------|------|
| Compute | 500 hours/month | ~$5/100 hours |
| PostgreSQL | 1GB storage | ~$5/GB |
| Redis | 30MB | ~$5/GB |
| Bandwidth | 100GB/month | $0.10/GB |
| Domain | $10-15/year | - |

**Total estimated cost**: $10-30/month (depending on usage)

## Troubleshooting

### Common Issues

1. **Database connection error**
   - Verify DATABASE_URL is set correctly
   - Check if PostgreSQL is in the same project

2. **Stripe webhook not working**
   - Verify webhook URL is accessible
   - Check webhook signature
   - Enable webhook logging in Stripe dashboard

3. **API returning 500 errors**
   - Check Railway logs
   - Verify all environment variables are set
   - Test locally first

4. **Domain not resolving**
   - Wait for DNS propagation (up to 48 hours)
   - Check DNS settings
   - Verify SSL certificate is provisioned

## Next Steps

1. ✅ Set up monitoring (UptimeRobot, Pingdom)
2. ✅ Configure email notifications
3. ✅ Set up error tracking (Sentry)
4. ✅ Build frontend dashboard
5. ✅ Implement rate limiting
6. ✅ Add support for multiple pricing tiers
7. ✅ Set up automated backups

## Useful Commands

```bash
# Railway CLI installation
npm install -g @railway/cli

# Login
railway login

# Link project
railway init
railway link

# Deploy
railway up

# View logs
railway logs

# Open dashboard
railway open

# Check environment variables
railway variables
```

---

**Congratulations!** Your platform should now be live at `https://yourdomain.com`

For support, check Railway docs: https://docs.railway.app
