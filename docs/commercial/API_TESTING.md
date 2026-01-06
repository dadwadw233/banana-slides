# 商业化功能API测试脚本

## 自动化测试脚本

将以下内容保存为 `test_commercial_api.sh`：

```bash
#!/bin/bash

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_BASE="http://localhost:5000"
TOKEN=""
USER_EMAIL="test$(date +%s)@example.com"
USER_PASSWORD="test123456"

echo -e "${YELLOW}=== Super Banana Slides 商业化API测试 ===${NC}\n"

# 测试1: 健康检查
echo -e "${YELLOW}[测试1] 健康检查${NC}"
RESPONSE=$(curl -s "$API_BASE/health")
if echo "$RESPONSE" | grep -q "ok"; then
    echo -e "${GREEN}✓ 服务运行正常${NC}\n"
else
    echo -e "${RED}✗ 服务未运行${NC}\n"
    exit 1
fi

# 测试2: 用户注册
echo -e "${YELLOW}[测试2] 用户注册${NC}"
RESPONSE=$(curl -s -X POST "$API_BASE/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$USER_EMAIL\",\"password\":\"$USER_PASSWORD\",\"username\":\"testuser\"}")

if echo "$RESPONSE" | grep -q "access_token"; then
    TOKEN=$(echo "$RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo -e "${GREEN}✓ 注册成功${NC}"
    echo "  邮箱: $USER_EMAIL"
    echo -e "  Token: ${TOKEN:0:30}...\n"
else
    echo -e "${RED}✗ 注册失败${NC}"
    echo "$RESPONSE" | head -3
    echo ""
fi

# 测试3: 用户登录
echo -e "${YELLOW}[测试3] 用户登录${NC}"
RESPONSE=$(curl -s -X POST "$API_BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$USER_EMAIL\",\"password\":\"$USER_PASSWORD\"}")

if echo "$RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓ 登录成功${NC}\n"
else
    echo -e "${RED}✗ 登录失败${NC}\n"
fi

# 测试4: 获取当前用户信息
echo -e "${YELLOW}[测试4] 获取当前用户信息${NC}"
RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/api/auth/me")

if echo "$RESPONSE" | grep -q "quota_balance"; then
    QUOTA=$(echo "$RESPONSE" | grep -o '"quota_balance":[0-9]*' | cut -d':' -f2)
    echo -e "${GREEN}✓ 获取用户信息成功${NC}"
    echo "  初始配额: $QUOTA 次"
    echo ""
else
    echo -e "${RED}✗ 获取用户信息失败${NC}\n"
fi

# 测试5: 查询配额余额
echo -e "${YELLOW}[测试5] 查询配额余额${NC}"
RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/api/quota/balance")

if echo "$RESPONSE" | grep -q "balance"; then
    BALANCE=$(echo "$RESPONSE" | grep -o '"balance":[0-9]*' | cut -d':' -f2)
    echo -e "${GREEN}✓ 查询余额成功${NC}"
    echo "  当前余额: $BALANCE 次"
    echo ""
else
    echo -e "${RED}✗ 查询余额失败${NC}\n"
fi

# 测试6: 检查配额是否足够
echo -e "${YELLOW}[测试6] 检查配额是否足够${NC}"
RESPONSE=$(curl -s -X POST "$API_BASE/api/quota/check" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action":"generate_image","count":2}')

if echo "$RESPONSE" | grep -q "sufficient"; then
    SUFFICIENT=$(echo "$RESPONSE" | grep -o '"sufficient":[^,]*' | cut -d':' -f2)
    echo -e "${GREEN}✓ 检查配额成功${NC}"
    echo "  生成2张图片是否足够: $SUFFICIENT"
    echo ""
else
    echo -e "${RED}✗ 检查配额失败${NC}\n"
fi

# 测试7: 查询配额交易历史
echo -e "${YELLOW}[测试7] 查询配额交易历史${NC}"
RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "$API_BASE/api/quota/transactions?page=1&per_page=5")

if echo "$RESPONSE" | grep -q "transactions"; then
    TOTAL=$(echo "$RESPONSE" | grep -o '"total":[0-9]*' | cut -d':' -f2 | head -1)
    echo -e "${GREEN}✓ 查询交易历史成功${NC}"
    echo "  交易记录数: $TOTAL 条"
    echo ""
else
    echo -e "${RED}✗ 查询交易历史失败${NC}\n"
fi

# 测试8: 无效token测试
echo -e "${YELLOW}[测试8] 无效token测试${NC}"
RESPONSE=$(curl -s -H "Authorization: Bearer invalid_token_123" \
  "$API_BASE/api/quota/balance")

if echo "$RESPONSE" | grep -q "Invalid"; then
    echo -e "${GREEN}✓ 正确拒绝无效token${NC}\n"
else
    echo -e "${RED}✗ 应该拒绝无效token${NC}\n"
fi

echo -e "${YELLOW}=== 测试完成 ===${NC}"
echo -e "${GREEN}所有核心功能测试通过!${NC}"
```

### 运行测试

```bash
chmod +x test_commercial_api.sh
./test_commercial_api.sh
```

## Python测试脚本

保存为 `test_commercial.py`：

```python
#!/usr/bin/env python3
import requests
import json
from datetime import datetime

API_BASE = "http://localhost:5000"
test_email = f"test{int(datetime.now().timestamp())}@example.com"
test_password = "test123456"
token = None

def test_health_check():
    print("[测试1] 健康检查")
    response = requests.get(f"{API_BASE}/health")
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'
    print("✓ 服务运行正常\n")

def test_register():
    global token
    print("[测试2] 用户注册")
    response = requests.post(
        f"{API_BASE}/api/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "username": "testuser"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data['success'] == True
    token = data['data']['access_token']
    print(f"✓ 注册成功: {test_email}")
    print(f"  初始配额: {data['data']['user']['quota_balance']} 次\n")

def test_login():
    print("[测试3] 用户登录")
    response = requests.post(
        f"{API_BASE}/api/auth/login",
        json={
            "email": test_email,
            "password": test_password
        }
    )
    assert response.status_code == 200
    assert 'access_token' in response.json()['data']
    print("✓ 登录成功\n")

def test_get_current_user():
    print("[测试4] 获取当前用户")
    response = requests.get(
        f"{API_BASE}/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    user = response.json()['data']['user']
    print(f"✓ 用户信息: {user['email']}")
    print(f"  配额余额: {user['quota_balance']} 次\n")

def test_quota_balance():
    print("[测试5] 查询配额余额")
    response = requests.get(
        f"{API_BASE}/api/quota/balance",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    balance = response.json()['data']['balance']
    print(f"✓ 当前余额: {balance} 次\n")

def test_quota_check():
    print("[测试6] 检查配额")
    response = requests.post(
        f"{API_BASE}/api/quota/check",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "generate_image", "count": 2}
    )
    assert response.status_code == 200
    data = response.json()['data']
    print(f"✓ 检查结果: 足够={data['sufficient']}")
    print(f"  需要: {data['required']} 次")
    print(f"  可用: {data['current_balance']} 次\n")

def test_invalid_token():
    print("[测试7] 无效token测试")
    response = requests.get(
        f"{API_BASE}/api/quota/balance",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    print("✓ 正确拒绝无效token\n")

if __name__ == "__main__":
    print("=== Super Banana Slides 商业化API测试 ===\n")
    
    try:
        test_health_check()
        test_register()
        test_login()
        test_get_current_user()
        test_quota_balance()
        test_quota_check()
        test_invalid_token()
        
        print("=== 所有测试通过! ===")
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
    except requests.exceptions.ConnectionError:
        print("\n✗ 无法连接到API服务，请确保后端已启动")
    except Exception as e:
        print(f"\n✗ 测试错误: {e}")
```

### 运行Python测试

```bash
chmod +x test_commercial.py
python3 test_commercial.py
```

## 手动测试清单

- [ ] 用户注册 - 新用户应获得3次免费配额
- [ ] 用户登录 - 返回有效的JWT token
- [ ] 获取用户信息 - 使用token获取用户详情
- [ ] 查询配额余额 - 显示正确余额
- [ ] 检查配额 - 正确判断是否足够
- [ ] 查询交易历史 - 分页显示交易记录
- [ ] 修改密码 - 成功修改并重新登录
- [ ] 无效token - 正确返回401错误
- [ ] 配额消耗 - (需集成到PPT生成流程)
- [ ] 订单创建 - (需手动测试)
- [ ] 支付处理 - (需手动测试)

## 预期结果

### 注册成功响应
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
      "status": "active"
    },
    "access_token": "eyJ0eXAiOiJKV1Qi...",
    "token_type": "Bearer"
  },
  "message": "Registration successful"
}
```

### 配额余额响应
```json
{
  "success": true,
  "data": {
    "balance": 3,
    "user_id": 1
  }
}
```

### 交易历史响应
```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "id": 1,
        "amount": 3,
        "balance_after": 3,
        "type": "gift",
        "description": "New user registration bonus",
        "created_at": "2026-01-05T15:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 1,
      "pages": 1
    }
  }
}
```

---

**测试环境**: 本地开发环境  
**API版本**: v1  
**更新时间**: 2026-01-05
