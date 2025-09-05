# 认证系统改进说明

## 概述

本文档说明了认证系统从中间件方式改为使用 FastAPI `Depends` 的改进，以及提供的多种认证选项。

## 改进内容

### 1. 优化的 Depends 认证

#### 主要改进：
- **更好的错误处理**：统一的 HTTP 状态码和错误消息
- **性能优化**：减少不必要的数据库查询
- **类型安全**：更好的类型提示和验证
- **灵活性**：支持多种认证场景

#### 可用的认证依赖项：

```python
# 标准认证（推荐）
current_user: User = Depends(get_current_user)

# 活跃用户认证
current_user: User = Depends(get_current_active_user)

# 超级用户认证
current_user: User = Depends(get_current_active_superuser)

# 可选认证（支持匿名访问）
current_user: Optional[User] = Depends(get_current_user_optional)

# 基于请求的认证
current_user: User = Depends(get_current_user_from_request)

# 基于中间件的认证
current_user: User = Depends(get_current_user_from_middleware)
```

### 2. 可选的中间件认证

#### 新增功能：
- **AuthenticationMiddleware**：可选的全局认证中间件
- **灵活配置**：可以跳过特定路径
- **向后兼容**：不影响现有的 Depends 认证

#### 启用中间件认证：

```python
# 在 main.py 中
add_middleware(app, enable_auth_middleware=True)
```

### 3. 错误处理改进

#### 统一的错误响应：
- **401 Unauthorized**：未认证或认证失败
- **403 Forbidden**：权限不足
- **WWW-Authenticate 头**：标准的认证挑战

#### 示例错误响应：

```json
{
  "detail": "Not authenticated"
}
```

## 使用指南

### 1. 推荐方式：使用 Depends

对于大多数应用，推荐使用 `Depends` 进行认证：

```python
from fastapi import Depends
from app.api.deps import get_current_user

@router.get("/protected")
async def protected_endpoint(
    current_user: User = Depends(get_current_user)
):
    return {"user_id": current_user.id}
```

### 2. 可选认证

对于需要支持匿名访问的端点：

```python
from app.api.deps import get_current_user_optional

@router.get("/public-or-private")
async def flexible_endpoint(
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    if current_user:
        return {"message": f"Hello {current_user.email}"}
    else:
        return {"message": "Hello anonymous user"}
```

### 3. 中间件认证

如果需要全局认证（不推荐用于大多数场景）：

```python
# 在 main.py 中启用
add_middleware(app, enable_auth_middleware=True)

# 在端点中使用
from app.api.deps import get_current_user_from_middleware

@router.get("/middleware-protected")
async def middleware_endpoint(
    current_user: User = Depends(get_current_user_from_middleware)
):
    return {"user_id": current_user.id}
```

## 性能对比

### Depends 方式（推荐）
- ✅ **按需认证**：只在需要时进行认证
- ✅ **缓存友好**：可以轻松添加缓存
- ✅ **测试友好**：易于单元测试
- ✅ **灵活性高**：每个端点可以有不同的认证要求

### 中间件方式
- ⚠️ **全局认证**：所有请求都会进行认证检查
- ⚠️ **性能开销**：即使不需要认证的端点也会检查
- ⚠️ **灵活性低**：难以实现复杂的认证逻辑

## 迁移指南

### 从中间件迁移到 Depends

1. **移除中间件认证**：
   ```python
   # 在 main.py 中
   add_middleware(app, enable_auth_middleware=False)
   ```

2. **更新端点**：
   ```python
   # 之前（中间件）
   @router.get("/protected")
   async def protected_endpoint(request: Request):
       user_id = request.state.user_id
       # ...

   # 之后（Depends）
   @router.get("/protected")
   async def protected_endpoint(
       current_user: User = Depends(get_current_user)
   ):
       # current_user 已经包含完整的用户信息
       return {"user_id": current_user.id}
   ```

3. **测试更新**：
   ```python
   # 测试时直接传递用户对象
   response = client.get("/protected", headers=auth_headers)
   ```

## 最佳实践

### 1. 选择合适的认证方式

- **标准端点**：使用 `get_current_user`
- **需要活跃用户**：使用 `get_current_active_user`
- **管理员端点**：使用 `get_current_active_superuser`
- **可选认证**：使用 `get_current_user_optional`

### 2. 错误处理

```python
from fastapi import HTTPException, status

# 在业务逻辑中处理权限
if not current_user.is_superuser:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions"
    )
```

### 3. 测试

```python
# 测试认证端点
def test_protected_endpoint(client, auth_headers):
    response = client.get("/protected", headers=auth_headers)
    assert response.status_code == 200

def test_unauthenticated_endpoint(client):
    response = client.get("/protected")
    assert response.status_code == 401
```

## 配置选项

### 环境变量

```env
# 启用中间件认证（可选）
ENABLE_AUTH_MIDDLEWARE=false

# JWT 配置
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_MINUTES=43200
ALGORITHM=HS256
```

### 中间件配置

```python
# 自定义跳过路径
custom_skip_paths = [
    "/docs",
    "/redoc",
    "/health",
    "/api/v1/public",
]

app.add_middleware(
    AuthenticationMiddleware, 
    skip_paths=custom_skip_paths
)
```

## 总结

通过这次改进，认证系统现在提供了：

1. **更好的性能**：按需认证，减少不必要的开销
2. **更高的灵活性**：支持多种认证场景
3. **更好的错误处理**：统一的错误响应格式
4. **向后兼容**：支持中间件和 Depends 两种方式
5. **更好的测试性**：易于单元测试和集成测试

推荐使用 `Depends` 方式进行认证，它提供了更好的性能、灵活性和可维护性。