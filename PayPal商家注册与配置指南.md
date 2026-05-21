# PayPal 商家注册与配置指南

## 为什么选择 PayPal？

### ✅ PayPal 的优势

| 对比项 | PayPal | Stripe | 备注 |
|--------|--------|--------|------|
| **中国商家支持** | ✅ 完全支持 | ❌ 不支持大陆 | PayPal 完胜 |
| **注册难度** | ⭐ 简单 | ⭐⭐⭐⭐⭐ | PayPal 30分钟完成 |
| **手续费** | 0.5% | 2.9% + $0.30 | PayPal 低 80% |
| **全球覆盖** | 135+ 国家 | 46 国家 | PayPal 广 |
| **开发者友好** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 都很友好 |

### 📊 费用对比

| 支付平台 | 每笔费用 | $100 订单费用 |
|---------|---------|--------------|
| **PayPal** | 0.5% + $0 | $0.50 |
| **Stripe** | 2.9% + $0.30 | $3.20 |
| **Paddle** | 5% + $0 | $5.00 |

**结论**：PayPal 不仅对中国商家更友好，**手续费还最低**！

---

## 第一部分：注册 PayPal 商家账户

### 步骤 1：访问注册页面

1. 打开浏览器访问：**https://www.paypal.cn/portal/account-selection**
2. 选择 **"个人商家"** 或 **"企业商家"**
3. 点击 "注册" 或 "Sign up"

### 步骤 2：创建账户

1. **输入邮箱**（建议使用 Gmail / Outlook / QQ 国际版）
   ```
   ✅ yourname@gmail.com
   ✅ yourname@outlook.com
   ✅ yourname@qq.com
   ❌ 不建议使用企业邮箱
   ```

2. **设置密码**
   ```
   要求：
   - 至少 8 位
   - 包含大小写字母
   - 包含数字
   - 包含特殊字符
   ```

3. **验证邮箱**
   - 登录邮箱，点击 PayPal 发送的验证链接

### 步骤 3：完成身份认证

1. **手机号码验证**
   - 输入中国手机号
   - 接收短信验证码
   - 输入验证码完成验证

2. **身份证认证**
   - 上传身份证正反面照片
   - 或使用手机拍照
   - 进行人脸识别

3. **等待审核**
   - 通常 **30 分钟内** 完成
   - 可能需要 1-2 个工作日

### 步骤 4：填写商业信息

1. **职业信息**
   ```yaml
   职业: 工程技术人员
   行业: 计算机软件开发服务
   ```

2. **业务描述**（英文）
   ```yaml
   提供 AI API 服务，销售 DeepSeek 模型访问额度
   Provide AI API services, selling DeepSeek model access credits
   ```

3. **网站信息**（可选）
   ```
   如果有网站，填入网站 URL
   如果没有，可以填写社交媒体链接或留空
   ```

### 步骤 5：绑定银行账户（收款）

1. 进入 **"账户设置"** → **"银行账户"**
2. 添加你的中国大陆银行卡
   ```yaml
   银行名称: 中国工商银行 / 招商银行 / 等
   账户号码: 你的银行卡号
   开户姓名: 必须与 PayPal 账户姓名一致
   ```
3. PayPal 会进行小额验证（几分钱）
4. 输入验证金额完成绑定

### 步骤 6：配置提现设置

1. **自动提现**
   - 设置自动提现频率（每日/每周/每月）
   - 或手动提现

2. **提现到账时间**
   ```yaml
   - 即时到账（中国工商银行）: 即时
   - 1-3 个工作日: 其他银行
   ```

---

## 第二部分：获取 API 凭证

### 步骤 1：注册 PayPal 开发者账户

1. 访问：**https://developer.paypal.com**
2. 使用刚注册的 PayPal 账户登录
3. 首次登录会自动创建开发者账户

### 步骤 2：创建应用

1. 进入 **"My Apps & Credentials"**
2. 点击 **"Create App"**
3. 填写应用信息：
   ```yaml
   App Name: DeepSeek API Resale (你的应用名)
   Environment: Sandbox (测试) / Live (生产)
   ```
4. 点击 "Create App"

### 步骤 3：获取凭证

在应用详情页面，你会看到：

```
Client ID:    AWxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Secret:       xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**重要**：
- ✅ **Sandbox Client ID / Secret**：用于测试
- ✅ **Live Client ID / Secret**：用于生产环境

### 步骤 4：测试环境 vs 生产环境

| 环境 | 用途 | 凭证类型 |
|------|------|---------|
| **Sandbox** | 开发测试 | Sandbox Client ID / Secret |
| **Live** | 正式运营 | Live Client ID / Secret |

**切换方法**：
- 开发时使用 Sandbox
- 上线前切换到 Live

---

## 第三部分：配置 Webhooks

### 为什么需要 Webhooks？

Webhook 允许 PayPal 在支付完成后自动通知你的系统，实现：
- ✅ 自动充值余额
- ✅ 发送收据
- ✅ 更新订单状态

### 步骤 1：配置 Webhook URL

1. 进入 **Developer Dashboard** → **My Apps & Credentials**
2. 选择你的应用
3. 点击 **"Webhooks"**
4. 点击 **"Add Webhook"**

5. 配置 Webhook：
   ```yaml
   URL: https://yourdomain.com/billing/webhook/paypal

   Events to receive:
   ✅ PAYMENT.CAPTURE.COMPLETED
   ✅ PAYMENT.CAPTURE.DENIED
   ✅ CHECKOUT.ORDER.APPROVED
   ```

### 步骤 2：验证 Webhook（可选）

1. 安装 PayPal Webhook Simulator
2. 测试 webhook 是否正常工作

---

## 第四部分：集成到代码

### 配置环境变量

在 `.env` 文件中添加：

```env
# PayPal Configuration
PAYPAL_CLIENT_ID=AWxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
PAYPAL_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
PAYPAL_SANDBOX=false  # 生产环境设为 false

# Payment Provider
PAYMENT_PROVIDER=paypal
```

### 测试流程

#### 1. 使用 Sandbox 测试

```bash
# 在 .env 中设置
PAYPAL_SANDBOX=true

# Sandbox 访问地址
https://www.sandbox.paypal.com
```

#### 2. 切换到生产环境

```bash
# 在 .env 中设置
PAYPAL_SANDBOX=false

# 生产环境访问地址
https://www.paypal.com
```

### 常见问题

#### Q1: Sandbox 和 Live 有什么区别？

| 环境 | 交易资金 | 账户余额 | 用途 |
|------|---------|---------|------|
| **Sandbox** | 模拟资金 | 模拟余额 | 开发测试 |
| **Live** | 真实资金 | 真实余额 | 正式运营 |

#### Q2: 如何从 Sandbox 切换到 Live？

1. 在 PayPal 开发者后台获取 Live 凭证
2. 更新 `.env` 文件
3. 将 `PAYPAL_SANDBOX` 设为 `false`
4. 重新部署

#### Q3: 支付完成后如何自动充值？

代码中已实现自动充值逻辑：
```python
# 在 capture_paypal_order 函数中
async def capture_paypal_order(order_id: str, db: AsyncSession):
    # 1. 验证订单
    order = await paypal_service.get_order(order_id)

    # 2. 提取用户 ID 和金额
    user_id = order["purchase_units"][0]["custom_id"]
    amount = float(order["purchase_units"][0]["amount"]["value"])

    # 3. 自动充值余额
    await billing_service.add_balance(user_id, amount, db)
```

---

## 第五部分：测试支付流程

### 测试步骤

#### 1. 启动应用

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. 注册测试用户

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123","full_name":"Test User"}'
```

#### 3. 登录获取 Token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'
```

#### 4. 创建充值订单

```bash
curl -X POST http://localhost:8000/billing/top-up \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 10.00}'
```

#### 5. 访问 PayPal 结账页面

响应会包含 `checkout_url`：
```json
{
  "checkout_url": "https://www.sandbox.paypal.com/checkoutnow?token=XXX",
  "order_id": "XXX",
  "provider": "paypal"
}
```

#### 6. 完成测试支付

1. 访问返回的 checkout_url
2. 使用 Sandbox 测试账户登录
3. 完成支付
4. 验证余额是否增加

### Sandbox 测试账户

在 https://developer.paypal.com/developer/accounts 可以找到：

- **Business Account**：商家测试账户
- **Personal Account**：买家测试账户

---

## 第六部分：上线检查清单

### 上线前必须完成

- [ ] PayPal 商家账户已通过审核
- [ ] 身份认证已完成
- [ ] 银行账户已绑定
- [ ] Live API 凭证已获取
- [ ] `.env` 配置已更新
- [ ] `PAYPAL_SANDBOX=false` 已设置
- [ ] Webhook 已配置
- [ ] 测试支付流程已完成
- [ ] 余额自动充值已验证

### 上线后监控

1. **检查支付通知**
   ```bash
   # 查看日志
   tail -f logs/app.log

   # 检查 webhook 请求
   ```

2. **监控账户余额**
   - 定期检查 PayPal 账户
   - 确保提现正常

3. **处理异常**
   - 支付失败
   - 退款请求
   - 争议处理

---

## 费用详解

### PayPal 手续费

| 交易类型 | 费率 |
|---------|------|
| **国内交易** | 0.5% + ¥0 (限时优惠) |
| **国际交易** | 1.5% + ¥0 |
| **跨境电商** | 2.5% + ¥0 |

**注意**：
- 原价国内交易为 1.0%，目前有 0.5% 限时优惠
- 优惠截止时间请查看 PayPal 官网

### 提现费用

| 提现方式 | 费用 |
|---------|------|
| **提现到银行账户** | 免费 |
| **电汇到银行** | $15/笔 |
| **PayPal 余额** | 免费 |

---

## 常见问题解答

### Q1: PayPal 账户被冻结怎么办？

**原因**：
- 异常交易
- 账户信息不完整
- 大量退款/争议

**解决方法**：
1. 登录 PayPal 后台查看原因
2. 提交所需材料
3. 联系 PayPal 客服
4. 保持良好的交易记录

### Q2: 如何降低风险避免账户被封？

**最佳实践**：
- ✅ 提供清晰的商品描述
- ✅ 及时发货/提供服务
- ✅ 保持充足的账户余额
- ✅ 响应客户查询
- ✅ 避免高退款率
- ✅ 使用真实的物流信息

### Q3: PayPal 支持哪些货币？

```yaml
支持货币：
- USD (美元)
- EUR (欧元)
- GBP (英镑)
- CNY (人民币)
- HKD (港币)
- JPY (日元)
- 以及 20+ 种其他货币
```

### Q4: 资金多久到账？

```yaml
提现到账时间：
- 中国工商银行: 即时到账
- 其他银行: 1-3 个工作日
```

---

## 客户支持

### PayPal 商家支持

- **电话**: 400-921-1000 (中国)
- **邮箱**: merchant@paypal.com
- **在线客服**: PayPal 后台右下角聊天图标

### 开发者支持

- **文档**: https://developer.paypal.com/docs
- **社区**: https://www.paypal-community.com/
- **API 状态**: https://www.paypal-status.com/

---

## 总结

**PayPal 是中国大陆用户最好的选择**：

1. ✅ **注册简单**：30 分钟完成
2. ✅ **支持大陆**：身份证 + 银行卡
3. ✅ **费用低**：0.5% 手续费
4. ✅ **覆盖广**：135+ 国家
5. ✅ **自动充值**：Webhook 实现

**下一步**：
1. 注册 PayPal 商家账户
2. 获取 API 凭证
3. 配置到代码中
4. 测试支付流程
5. 上线运营！

---

**祝你创业成功！💰**
