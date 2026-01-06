# 商业化功能快速启动指南

## 前置准备

### 1. 安装依赖

确保已安装商业化所需的Python包：

```bash
pip install pyjwt bcrypt email-validator flask-sqlalchemy alembic flask-migrate
```

### 2. 配置环境变量

在项目根目录的`.env`文件中添加：

```env
# JWT配置（必需）
SECRET_KEY=change-this-to-a-random-secret-key-in-production

# 新用户赠送配额（可选，默认3次）
NEW_USER_FREE_QUOTA=3
```

生成安全的SECRET_KEY：
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3. 数据库迁移

创建商业化数据表：

```bash
cd backend

# 方式1: 使用Alembic自动迁移（推荐）
python3 -m alembic revision --autogenerate -m "Add commercial models"
python3 -m alembic upgrade head

# 方式2: 如果遇到依赖问题，手动创建表
python3 << 'EOF'
from app import create_app
from models import db
from models.user import User
from models.quota_transaction import QuotaTransaction
from models.order import Order
from models.subscription import Subscription

app = create_app()
with app.app_context():
    db.create_all()
    print("✅ Commercial tables created successfully!")
EOF
```

## 快速测试

### 步骤1: 启动后端服务

```bash
cd backend
python3 app.py
```

服务应在 `http://localhost:5000` 启动。

### 步骤2: 测试用户注册

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "123456",
    "username": "testuser"
  }'
```

**预期响应**：
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "email": "test@example.com",
      "username": "testuser",
      "quota_balance": 3,
      "role": "user",
      ...
    },
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "Bearer"
  },
  "message": "Registration successful"
}
```

**注意**：新用户自动获得3次免费配额！

### 步骤3: 测试用户登录

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "123456"
  }'
```

保存返回的`access_token`，后续请求需要使用。

### 步骤4: 查询配额余额

```bash
# 替换YOUR_TOKEN为上一步获得的access_token
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5000/api/quota/balance
```

**预期响应**：
```json
{
  "success": true,
  "data": {
    "balance": 3,
    "user_id": 1
  }
}
```

### 步骤5: 查看配额交易历史

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5000/api/quota/transactions?page=1&per_page=10
```

### 步骤6: 检查配额是否足够

```bash
curl -X POST http://localhost:5000/api/quota/check \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "generate_image",
    "count": 2
  }'
```

**预期响应**：
```json
{
  "success": true,
  "data": {
    "sufficient": true,
    "current_balance": 3,
    "required": 2,
    "action": "generate_image",
    "count": 2
  }
}
```

## 配额消耗测试

配额消耗会在实际使用PPT生成功能时自动触发。消耗规则：

| 操作 | 消耗配额 |
|------|---------|
| 生成大纲 | 0次（免费） |
| 生成单页描述 | 0.1次 |
| 生成单页图片 | 1次 |
| 编辑图片 | 0.5次 |
| 导出PPTX | 0.2次 |
| 导出可编辑PPTX | 0.5次 |

### 手动测试配额消耗

```python
# 在backend目录下运行Python交互环境
python3

>>> from app import create_app
>>> from models import db
>>> from models.user import User
>>> from services.quota_service import QuotaService
>>> 
>>> app = create_app()
>>> with app.app_context():
...     user = User.query.filter_by(email='test@example.com').first()
...     
...     # 消耗1次配额（生成图片）
...     transaction = QuotaService.consume(
...         user=user,
...         action='generate_image',
...         count=1,
...         description='Test image generation'
...     )
...     
...     print(f"消耗前余额: {transaction.balance_after + 1}")
...     print(f"消耗配额: 1")
...     print(f"消耗后余额: {transaction.balance_after}")
```

## 订单管理测试

### 创建订单

```python
python3 << 'EOF'
from app import create_app
from models import db
from models.user import User
from services.order_service import OrderService

app = create_app()
with app.app_context():
    user = User.query.filter_by(email='test@example.com').first()
    
    # 创建10次套餐订单
    order = OrderService.create_order(user, '10_pack')
    
    print(f"订单号: {order.order_number}")
    print(f"订单金额: ¥{order.amount}")
    print(f"购买配额: {order.quota_amount}次")
    print(f"订单状态: {order.status}")
EOF
```

### 模拟支付完成

```python
python3 << 'EOF'
from app import create_app
from models.order import Order
from services.order_service import OrderService

app = create_app()
with app.app_context():
    # 获取最新的待支付订单
    order = Order.query.filter_by(status='pending').order_by(Order.created_at.desc()).first()
    
    if order:
        # 模拟支付成功
        completed_order = OrderService.process_payment(
            order_id=order.id,
            payment_method='test',
            payment_id='TEST_PAYMENT_12345'
        )
        
        print(f"✅ 订单支付成功!")
        print(f"订单号: {completed_order.order_number}")
        print(f"支付方式: {completed_order.payment_method}")
        print(f"已充值配额: {completed_order.quota_amount}次")
    else:
        print("没有待支付的订单")
EOF
```

## 常见问题

### Q1: 数据库迁移失败

**问题**：运行alembic时提示模块找不到

**解决**：
```bash
# 确保安装了所有依赖
pip install flask flask-sqlalchemy flask-cors python-dotenv pillow \
    reportlab python-pptx pyjwt bcrypt email-validator alembic flask-migrate

# 如果还是失败，尝试手动创建表（方式2）
```

### Q2: JWT token无效

**问题**：请求返回"Invalid or expired token"

**解决**：
1. 检查`.env`中是否配置了`SECRET_KEY`
2. 确保请求头格式正确：`Authorization: Bearer YOUR_TOKEN`
3. Token有效期24小时，过期需重新登录

### Q3: 配额余额不更新

**问题**：支付订单后配额没有增加

**解决**：
1. 检查订单状态是否为`paid`
2. 查看`quota_transactions`表确认是否有充值记录
3. 检查后端日志是否有错误

### Q4: 注册时报错

**问题**：注册用户时提示邮箱格式错误

**解决**：
- 确保安装了`email-validator`包
- 邮箱格式必须包含`@`符号

## 数据库表结构查询

查看已创建的商业化表：

```bash
# 进入SQLite数据库
sqlite3 backend/instance/database.db

# 查看所有表
.tables

# 查看users表结构
.schema users

# 查看quota_transactions表结构
.schema quota_transactions

# 查看orders表结构
.schema orders

# 退出
.exit
```

## API端点完整列表

### 认证相关
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息
- `POST /api/auth/change-password` - 修改密码

### 配额相关
- `GET /api/quota/balance` - 查询配额余额
- `GET /api/quota/transactions` - 配额交易历史
- `POST /api/quota/check` - 检查配额是否足够

### 通用
- `GET /health` - 健康检查

## 下一步

1. **前端集成** - 开发登录/注册页面
2. **支付集成** - 接入支付宝/微信支付
3. **邮箱验证** - 添加邮箱验证功能
4. **生产部署** - 配置生产环境

---

**文档更新时间**: 2026-01-05  
**支持**: 如有问题请查看 `docs/commercial/` 目录下的其他文档
