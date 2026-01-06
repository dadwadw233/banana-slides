# Super Banana Slides 商业化实施进度

## 已完成工作 ✅

### 1. 依赖包安装
- ✅ PyJWT 2.10.1 - JWT令牌生成和验证
- ✅ bcrypt 5.0.0 - 密码加密
- ✅ email-validator 2.3.0 - 邮箱验证
- ✅ Flask-SQLAlchemy 3.1.1 - ORM
- ✅ Alembic 1.17.2 - 数据库迁移

### 2. 数据模型创建
已创建4个核心商业化模型：

- **User模型** (`backend/models/user.py`)
  - 用户基本信息（邮箱、用户名、密码等）
  - 配额余额管理
  - 角色权限（user/premium/admin）
  - OAuth支持
  - 密码加密/验证方法

- **QuotaTransaction模型** (`backend/models/quota_transaction.py`)
  - 配额交易记录
  - 交易类型（purchase/consume/refund/gift）
  - 关联用户和订单
  - 附加数据支持

- **Order模型** (`backend/models/order.py`)
  - 订单管理
  - 订单号生成
  - 支付状态跟踪
  - 多支付方式支持（alipay/wechat/stripe）

- **Subscription模型** (`backend/models/subscription.py`)
  - 订阅管理
  - 月度/年度订阅支持
  - 自动续费配置
  - 订阅周期管理

### 3. 核心服务层
- **AuthService** (`backend/services/auth_service.py`)
  - 用户注册（自动赠送3次免费配额）
  - 用户登录
  - JWT生成和验证
  - 密码修改
  - Token验证和用户获取

- **QuotaService** (`backend/services/quota_service.py`)
  - 配额余额查询
  - 配额消耗（按操作类型计费）
  - 配额充值
  - 配额退款
  - 交易历史查询
  
  **配额消耗规则**：
  ```python
  'generate_outline': 0次          # 免费
  'generate_description': 0.1次   # 生成单页描述
  'generate_image': 1次           # 生成单页图片
  'edit_image': 0.5次             # 编辑图片
  'export_pptx': 0.2次           # 导出PPTX
  'export_editable_pptx': 0.5次  # 导出可编辑PPTX
  ```

## 待完成工作 🔨

### 高优先级
1. ⏳ 创建用户认证控制器 (auth_controller.py)
   - `/api/auth/register` - 注册接口
   - `/api/auth/login` - 登录接口
   - `/api/users/me` - 获取当前用户信息

2. ⏳ 创建配额管理控制器 (quota_controller.py)
   - `/api/quota/balance` - 查询配额余额
   - `/api/quota/transactions` - 配额交易历史

3. ⏳ 实现认证中间件装饰器 (@require_auth)
   - JWT验证装饰器
   - 自动注入当前用户到请求上下文

4. ⏳ 改造现有Project模型
   - 添加`user_id`外键
   - 创建数据库迁移脚本

5. ⏳ 创建数据库迁移并应用
   - 生成Alembic迁移脚本
   - 运行`alembic upgrade head`

### 中优先级
6. ⏳ 改造现有控制器
   - project_controller.py - 添加用户认证和配额检查
   - page_controller.py - 生成图片前检查配额

7. ⏳ 订单管理服务和控制器
   - order_service.py - 订单创建和管理
   - order_controller.py - 订单API接口

### 低优先级
8. ⏳ 支付集成（支付宝/微信）
9. ⏳ 邮箱验证功能
10. ⏳ 完整测试

## 数据库表结构

### users表
```sql
- id (INTEGER, PRIMARY KEY)
- email (VARCHAR(255), UNIQUE)
- password_hash (VARCHAR(255))
- username (VARCHAR(100))
- quota_balance (INTEGER, DEFAULT 0)
- role (VARCHAR(20), DEFAULT 'user')
- status (VARCHAR(20), DEFAULT 'active')
- created_at (DATETIME)
...
```

### quota_transactions表
```sql
- id (INTEGER, PRIMARY KEY)
- user_id (INTEGER, FOREIGN KEY -> users.id)
- amount (INTEGER)
- balance_after (INTEGER)
- type (VARCHAR(20))
- description (TEXT)
- created_at (DATETIME)
...
```

### orders表
```sql
- id (INTEGER, PRIMARY KEY)
- user_id (INTEGER, FOREIGN KEY -> users.id)
- order_number (VARCHAR(50), UNIQUE)
- amount (NUMERIC(10,2))
- quota_amount (INTEGER)
- status (VARCHAR(20))
- payment_method (VARCHAR(50))
- created_at (DATETIME)
...
```

### subscriptions表
```sql
- id (INTEGER, PRIMARY KEY)
- user_id (INTEGER, FOREIGN KEY -> users.id)
- type (VARCHAR(20))
- quota_per_period (INTEGER)
- price (NUMERIC(10,2))
- status (VARCHAR(20))
- current_period_start (DATETIME)
- current_period_end (DATETIME)
...
```

## 下一步行动

### 立即执行（今天完成）
1. 创建认证中间件装饰器
2. 创建用户认证控制器
3. 创建配额管理控制器
4. 更新app.py注册新的蓝图

### 本周完成
1. 改造Project模型添加user_id
2. 创建数据库迁移并应用
3. 改造现有控制器添加认证
4. 前端登录/注册页面开发

### 技术债务
- 当前使用pip安装依赖，需要生成新的uv.lock文件
- 需要添加环境变量JWT_SECRET_KEY到.env
- LSP诊断显示sqlalchemy未解析（不影响运行，仅IDE提示）

## 环境配置

需要在`.env`文件中添加：
```env
# JWT配置
SECRET_KEY=your-secret-key-change-this-in-production
JWT_EXPIRES_IN_HOURS=24

# 新用户赠送配额
NEW_USER_FREE_QUOTA=3

# 配额价格（每个配额单价）
QUOTA_PRICE_PER_UNIT=2.00
```

## API设计预览

### 认证相关
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/users/me` - 获取当前用户
- `PATCH /api/users/me` - 更新用户信息

### 配额相关
- `GET /api/quota/balance` - 查询配额余额
- `GET /api/quota/transactions` - 配额交易历史

### 订单相关（待实现）
- `POST /api/orders` - 创建订单
- `GET /api/orders/{order_id}` - 查询订单状态
- `GET /api/orders` - 订单列表

## 已知问题
1. 需要安装完整项目依赖才能运行alembic迁移
2. 需要配置JWT SECRET_KEY
3. 前端暂未适配新的认证系统

---
**更新时间**: 2026-01-05 22:49  
**当前进度**: Phase 2 - 基础设施搭建 60%完成
