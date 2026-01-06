# 配额集成实施计划

## 概述
将配额系统集成到现有PPT生成流程，确保每次操作都会检查和消耗用户配额。

## 需要修改的后端文件

### 1. backend/controllers/page_controller.py

#### 需要添加的导入
```python
from utils.auth_middleware import require_auth, get_current_user
from services.quota_service import QuotaService
```

#### 需要修改的端点

##### A. generate_page_image() - 生成单页图片
- **位置**: Line 276
- **配额消耗**: 1次
- **修改内容**:
  ```python
  @page_bp.route('/<project_id>/pages/<page_id>/generate/image', methods=['POST'])
  @require_auth  # 添加认证装饰器
  def generate_page_image(project_id, page_id):
      # 在生成图片前检查配额
      user = get_current_user()
      quota_service = QuotaService()
      
      if not quota_service.check_quota(user.id, 'generate_image'):
          return error_response('INSUFFICIENT_QUOTA', '配额不足', 402)
      
      # 原有的图片生成逻辑...
      # ...生成成功后消耗配额
      
      quota_service.consume_quota(
          user_id=user.id,
          operation_type='generate_image',
          project_id=project_id,
          description=f'生成页面 {page_id} 图片'
      )
  ```

##### B. edit_page_image() - 编辑图片
- **位置**: 需要查找
- **配额消耗**: 0.5次
- **修改内容**: 同上，operation_type='edit_image'

### 2. backend/controllers/project_controller.py

#### A. generate_images() - 批量生成图片
- **位置**: Line 650
- **配额消耗**: 每页1次
- **修改内容**:
  ```python
  @project_bp.route('/<project_id>/generate/images', methods=['POST'])
  @require_auth
  def generate_images(project_id):
      user = get_current_user()
      quota_service = QuotaService()
      
      # 获取要生成的页面数量
      data = request.get_json() or {}
      page_ids = data.get('page_ids', [])
      
      if page_ids:
          pages_count = len(page_ids)
      else:
          pages_count = Page.query.filter_by(project_id=project_id).count()
      
      # 检查配额是否足够生成所有页面
      if not quota_service.check_quota(user.id, 'generate_image', pages_count):
          return error_response(
              'INSUFFICIENT_QUOTA',
              f'配额不足。需要{pages_count}次配额，当前余额{quota_service.get_balance(user.id)}次',
              402
          )
      
      # 原有的批量生成逻辑...
      # ...在任务完成后消耗配额（需要在task_manager中集成）
  ```

#### B. generate_descriptions() - 批量生成描述
- **位置**: 需要查找
- **配额消耗**: 每页0.1次
- **修改内容**: 同上，operation_type='generate_description'

### 3. backend/controllers/page_controller.py - 生成描述

##### generate_page_description()
- **配额消耗**: 0.1次
- **operation_type**: 'generate_description'

### 4. backend/controllers/export_controller.py

#### A. export_pptx() - 导出PPTX
- **配额消耗**: 0.2次
- **operation_type**: 'export_pptx'

#### B. export_editable_pptx() - 导出可编辑PPTX
- **配额消耗**: 0.5次
- **operation_type**: 'export_editable_pptx'

### 5. backend/services/task_manager.py

需要在异步任务完成后消耗配额：

```python
def generate_single_page_image_task(task_id, ...):
    try:
        # 原有的图片生成逻辑...
        
        # 成功后消耗配额
        if user_id:  # 需要传递user_id参数
            quota_service = QuotaService()
            quota_service.consume_quota(
                user_id=user_id,
                operation_type='generate_image',
                project_id=project_id,
                description=f'异步生成页面 {page_id} 图片'
            )
    except Exception as e:
        # 失败时不消耗配额
        pass
```

## 需要修改的数据模型

### backend/models/project.py

需要添加 user_id 字段（已完成）：
```python
user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
```

## 前端集成点

### 1. 配额检查逻辑（前端）

#### frontend/src/store/useProjectStore.ts

在以下方法中添加配额检查：

```typescript
generateImages: async (pageIds?: string[]) => {
  const { currentProject, setError } = get();
  if (!currentProject) return;
  
  // 检查用户是否登录
  const { isAuthenticated } = useAuthStore.getState();
  if (!isAuthenticated) {
    setError('请先登录');
    return;
  }
  
  // 前端预检查配额（可选，后端会再次检查）
  const { getQuotaBalance } = api;
  const balance = await getQuotaBalance();
  const requiredQuota = pageIds ? pageIds.length : currentProject.pages.length;
  
  if (balance.data!.balance < requiredQuota) {
    setError(`配额不足。需要${requiredQuota}次，当前${balance.data!.balance}次`);
    return;
  }
  
  try {
    set({ isGlobalLoading: true });
    await api.generateImages(currentProject.id, undefined, pageIds);
    // 成功后刷新配额显示
    // QuotaDisplay组件会自动刷新
  } catch (error: any) {
    if (error.response?.status === 402) {
      setError('配额不足，请购买配额');
    } else {
      setError(error.response?.data?.error?.code || '生成失败');
    }
  } finally {
    set({ isGlobalLoading: false });
  }
}
```

### 2. 配额不足提示UI

在以下场景添加配额提示：

#### A. SlidePreview.tsx
```tsx
// 在生成图片按钮旁显示配额余额
<QuotaDisplay />

// 生成图片前检查
const handleGenerateImages = async () => {
  const balance = await api.getQuotaBalance();
  if (balance.data!.balance < selectedPageIds.length) {
    toast.error(`配额不足！需要${selectedPageIds.length}次，剩余${balance.data!.balance}次`);
    // 可选：显示购买配额对话框
    return;
  }
  
  await generateImages(selectedPageIds);
}
```

#### B. DetailEditor.tsx
```tsx
// 在批量生成描述按钮旁显示配额信息
<QuotaDisplay />

// 批量生成前检查
const handleGenerateDescriptions = async () => {
  const requiredQuota = pages.length * 0.1;
  const balance = await api.getQuotaBalance();
  
  if (balance.data!.balance < requiredQuota) {
    toast.error(`配额不足！需要${requiredQuota}次，剩余${balance.data!.balance}次`);
    return;
  }
  
  await generateDescriptions();
}
```

## 实施步骤

### 阶段1：后端配额检查集成 ⚡ 高优先级
1. ✅ 修改 page_controller.py - 添加 generate_page_image 配额检查
2. ✅ 修改 page_controller.py - 添加 generate_page_description 配额检查
3. ✅ 修改 page_controller.py - 添加 edit_page_image 配额检查
4. ✅ 修改 project_controller.py - 添加 generate_images 批量配额检查
5. ✅ 修改 export_controller.py - 添加 export_pptx 配额检查
6. ✅ 修改 export_controller.py - 添加 export_editable_pptx 配额检查

### 阶段2：前端配额UI集成 ⏳ 等待frontend-ui-ux-engineer完成
1. 🔄 等待 Login.tsx/Register.tsx/QuotaDisplay.tsx 创建完成
2. ⏳ 在 SlidePreview.tsx 添加配额显示
3. ⏳ 在 DetailEditor.tsx 添加配额显示
4. ⏳ 在 useProjectStore.ts 添加配额检查逻辑
5. ⏳ 添加配额不足提示UI（Toast/Modal）

### 阶段3：异步任务配额集成 🔸 中优先级
1. ⏳ 修改 task_manager.py - 传递 user_id
2. ⏳ 在异步任务成功回调中消耗配额
3. ⏳ 在异步任务失败回调中退还配额（可选）

### 阶段4：测试验证 🔸 中优先级
1. ⏳ 测试单页图片生成配额消耗
2. ⏳ 测试批量图片生成配额消耗
3. ⏳ 测试导出PPTX配额消耗
4. ⏳ 测试配额不足拦截
5. ⏳ 测试配额余额实时显示

## 配额消耗规则总结

| 操作 | operation_type | 配额消耗 | 端点 |
|------|---------------|---------|------|
| 生成大纲 | - | 0次 | POST /api/projects/{id}/generate/outline |
| 生成单页描述 | generate_description | 0.1次 | POST /api/projects/{id}/pages/{pid}/generate/description |
| 批量生成描述 | generate_description | 0.1次/页 | POST /api/projects/{id}/generate/descriptions |
| 生成单页图片 | generate_image | 1次 | POST /api/projects/{id}/pages/{pid}/generate/image |
| 批量生成图片 | generate_image | 1次/页 | POST /api/projects/{id}/generate/images |
| 编辑图片 | edit_image | 0.5次 | POST /api/projects/{id}/pages/{pid}/edit/image |
| 导出PPTX | export_pptx | 0.2次 | GET /api/projects/{id}/export/pptx |
| 导出可编辑PPTX | export_editable_pptx | 0.5次 | POST /api/projects/{id}/export/editable-pptx |

## 错误处理

### HTTP状态码
- **402 Payment Required**: 配额不足
- **401 Unauthorized**: 未登录/token无效

### 错误响应格式
```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_QUOTA",
    "message": "配额不足。需要5次配额，当前余额2次"
  }
}
```

## 注意事项

1. **配额检查位置**: 在执行操作前检查，操作成功后消耗
2. **异步任务**: 需要在任务完成回调中消耗配额，避免重复消耗
3. **失败回退**: 如果操作失败，考虑退还配额（根据业务需求）
4. **并发安全**: QuotaService 使用事务保证扣款原子性
5. **用户体验**: 前端预检查配额，避免请求到后端才发现不足
6. **配额显示**: 实时显示用户配额余额，让用户清楚知道剩余次数

## 未来优化方向

1. **配额包**: 支持不同配额包（10次/50次/100次/500次）
2. **支付集成**: 集成Stripe/支付宝支付购买配额
3. **订阅模式**: 月度/年度订阅，每月刷新配额
4. **配额赠送**: 注册送3次体验配额
5. **配额历史**: 显示配额消耗历史记录
6. **配额预警**: 配额低于阈值时提醒用户购买
