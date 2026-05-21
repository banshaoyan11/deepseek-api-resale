# Git 初始化和部署脚本

## 第一步：初始化 Git 仓库

打开 PowerShell 或 Git Bash，运行以下命令：

```powershell
# 进入项目目录
cd D:\DeepSeek_API_Resale_Platform

# 初始化 Git 仓库
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit - DeepSeek API Resale Platform"

# 创建 .gitignore 文件（重要）
@"
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment files (NEVER commit these!)
.env
.env.local
.env.production

# Logs
*.log
logs/

# Database
*.db
*.sqlite

# OS files
.DS_Store
Thumbs.db
"@ | Out-File -FilePath ".gitignore" -Encoding UTF8

# 重新添加文件（排除 .gitignore 中的）
git add .
git commit -m "Add .gitignore and recommit"
```

## 第二步：创建 GitHub 仓库

1. 打开浏览器访问：https://github.com/new
2. 仓库名称：`deepseek-api-resale`（或你喜欢的名字）
3. 选择 Private（私有）
4. **不要**勾选 "Initialize this repository with a README"
5. 点击 "Create repository"
6. 复制仓库 URL

## 第三步：推送到 GitHub

```powershell
# 添加远程仓库（替换 YOUR_USERNAME 为你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/deepseek-api-resale.git

# 推送代码
git branch -M main
git push -u origin main
```

## 第四步：Railway 部署

### 4.1 创建 Railway 项目

1. 访问 https://railway.app
2. 点击 "New Project" → "Deploy from GitHub repo"
3. 连接你的 GitHub 账户
4. 选择刚创建的仓库 `deepseek-api-resale`

### 4.2 添加数据库

在 Railway 项目中：
1. 点击 "New" → "Database" → "PostgreSQL"
2. 等待数据库创建完成
3. 点击数据库 → 复制 "DATABASE_URL"

### 4.3 配置环境变量

在你的服务 → Variables 中添加：

```
# DeepSeek API
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# Stripe
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxx

# Security
SECRET_KEY=<运行: python -c "import secrets; print(secrets.token_urlsafe(32))">

# Your Domain
BASE_URL=https://api.yourdomain.com

# App Settings
DEBUG=false
```

### 4.4 生成 SECRET_KEY

在 PowerShell 中运行：
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

复制输出结果，添加到 Railway 环境变量。

## 第五步：配置 Stripe Webhook

1. 登录 Stripe Dashboard：https://dashboard.stripe.com
2. 进入 Developers → Webhooks
3. 点击 "Add endpoint"
4. Endpoint URL: `https://api.yourdomain.com/billing/webhook/stripe`
5. Select events:
   - ✅ `checkout.session.completed`
   - ✅ `payment_intent.succeeded`
6. 点击 "Add endpoint"
7. 复制 Webhook Secret (whsec_xxx) 到 Railway

## 第六步：配置域名

### 在 Railway 中：
1. 进入你的服务 → Networking
2. 点击 "Custom Domains"
3. 添加你的域名（如 `api.yourdomain.com`）

### 在域名服务商处配置 DNS：

**Cloudflare 示例：**
```
Type: CNAME
Name: api
Content: your-railway-app.railway.app
Proxy: ✅ (橙色云朵)
```

**Namecheap 示例：**
```
Host: api
Value: your-railway-app.railway.app
Type: CNAME
TTL: Automatic
```

## 第七步：验证部署

### 测试健康检查：
```powershell
# 等待几分钟让 Railway 完成部署
curl https://api.yourdomain.com/health
```

预期响应：
```json
{"status":"healthy","timestamp":"2026-05-21T00:00:00Z"}
```

### 测试 API：
```powershell
# 1. 注册用户
Invoke-RestMethod -Method Post -Uri "https://api.yourdomain.com/auth/register" `
  -ContentType "application/json" `
  -Body '{"email":"test@example.com","password":"testpass123","full_name":"Test User"}'

# 2. 登录获取 token
$tokenResponse = Invoke-RestMethod -Method Post -Uri "https://api.yourdomain.com/auth/login" `
  -ContentType "application/json" `
  -Body '{"email":"test@example.com","password":"testpass123"}'

$token = $tokenResponse.access_token

# 3. 创建 API Key
Invoke-RestMethod -Method Post -Uri "https://api.yourdomain.com/api-keys/" `
  -Headers @{Authorization="Bearer $token"} `
  -ContentType "application/json" `
  -Body '{"name":"Test Key"}'
```

## 常见问题

### Q: Railway 显示部署失败？
A: 检查日志：
1. Railway Dashboard → Deployments → 查看最新日志
2. 常见错误：
   - 缺少环境变量
   - 数据库连接失败
   - 端口配置错误

### Q: 数据库连接失败？
A: 确保 DATABASE_URL 格式正确：
```
postgresql://user:password@host:5432/database
```

### Q: Stripe Webhook 不工作？
A: 验证步骤：
1. Webhook URL 是否可访问？
2. 是否选择了正确的事件？
3. Webhook Secret 是否正确？

### Q: 域名无法访问？
A: DNS 传播需要时间（最长 48 小时）。可以尝试：
1. 使用浏览器隐私模式
2. 刷新 DNS 缓存：`ipconfig /flushdns`
3. 检查 DNS 配置是否正确

## 🎉 完成！

部署成功后，你可以通过以下地址访问：

- **API 文档**: https://api.yourdomain.com/docs
- **管理面板**: https://api.yourdomain.com/dashboard (需要前端)
- **健康检查**: https://api.yourdomain.com/health

---

**下一步：**
1. 构建前端界面
2. 设置监控和告警
3. 配置支付测试
4. 上线运营！

需要我帮你完成哪一步吗？
