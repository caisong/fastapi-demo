# 外部系统认证管理指南

## 概述

本文档介绍了如何使用外部系统认证管理模块来实现类似单点登录的效果，统一管理多个需要用户名密码登录的外部系统。

## 功能特性

1. **统一认证管理** - 集中管理多个外部系统的认证信息
2. **自动会话维护** - 自动处理外部系统的登录会话
3. **透明API调用** - 对业务代码透明的外部API调用
4. **认证状态监控** - 实时监控外部系统认证状态
5. **日志记录** - 完整的调用日志记录

## 架构设计

```
┌─────────────────┐
│   业务服务层     │
└─────────┬───────┘
          │
┌─────────▼───────┐
│ 外部系统服务层   │
├─────────────────┤
│ - 认证管理      │
│ - 会话维护      │
│ - API调用       │
└─────────┬───────┘
          │
┌─────────▼───────┐
│ 外部系统模型层   │
├─────────────────┤
│ - 系统配置      │
│ - 会话管理      │
│ - 调用日志      │
└─────────────────┘
```

## 快速开始

### 1. 创建外部系统配置

```python
from app.services.external_system import external_system_service
from app.schemas.external_system import ExternalSystemCreate

# 创建外部系统配置
system_data = ExternalSystemCreate(
    name="weather_api",
    display_name="天气API",
    base_url="https://api.weather.com",
    auth_url="/v1/auth/login",
    username="your_username",
    password="your_password",
    auth_type="username_password",
    session_timeout=3600,  # 1小时
    max_retry_count=3,
    is_active=True
)

# 保存配置
system = await external_system_service.create_system(db, system_in=system_data)
```

### 2. 认证外部系统

```python
# 对单个系统进行认证
result = await external_system_service.authenticate_system(db, system_name="weather_api")
if result.success:
    print(f"认证成功: {result.message}")
else:
    print(f"认证失败: {result.message}")

# 批量认证所有启用的系统
batch_result = await external_system_service.authenticate_all_systems(db)
print(f"成功认证 {batch_result.success_count}/{batch_result.total_systems} 个系统")
```

### 3. 在业务逻辑中调用外部系统API

```python
# 直接在业务服务中调用外部API，无需通过API端点
response = await external_system_service.call_external_api(
    db,
    system_name="weather_api",
    method="GET",
    endpoint="/v1/weather/forecast",
    params={"city": "Beijing"},
    headers={"Custom-Header": "value"}
)

print(f"响应状态: {response['status_code']}")
print(f"响应数据: {response['data']}")
```

## API端点

### 系统管理

- `POST /api/v1/external-systems/` - 创建外部系统配置（仅超级用户）
- `GET /api/v1/external-systems/` - 获取系统列表（仅超级用户）
- `GET /api/v1/external-systems/{system_id}` - 获取系统详情（仅超级用户）
- `PUT /api/v1/external-systems/{system_id}` - 更新系统配置（仅超级用户）
- `DELETE /api/v1/external-systems/{system_id}` - 删除系统配置（仅超级用户）

### 认证管理

- `POST /api/v1/external-systems/{system_name}/authenticate` - 认证特定系统（仅超级用户）
- `POST /api/v1/external-systems/authenticate-all` - 批量认证所有系统（仅超级用户）
- `GET /api/v1/external-systems/{system_name}/status` - 获取系统认证状态
- `GET /api/v1/external-systems/status` - 获取所有系统认证状态

## 使用示例

### 在业务逻辑中直接使用

```python
from app.services.external_system import external_system_service

class WeatherService:
    """天气服务"""
    
    async def get_weather_forecast(self, db, city: str):
        """获取天气预报"""
        try:
            response = await external_system_service.call_external_api(
                db,
                system_name="weather_api",
                method="GET",
                endpoint="/v1/weather/forecast",
                params={"city": city}
            )
            
            if response["status_code"] == 200:
                return response["data"]
            else:
                raise Exception(f"API调用失败: {response['status_code']}")
                
        except Exception as e:
            # 处理错误
            raise Exception(f"获取天气预报失败: {str(e)}")

# 使用示例
weather_service = WeatherService()
forecast = await weather_service.get_weather_forecast(db, "Beijing")
```

### 在API端点中使用

```python
from fastapi import APIRouter, Depends
from app.api import deps
from app.services.external_system import external_system_service

router = APIRouter()

@router.get("/weather/{city}")
async def get_weather(
    city: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """获取城市天气"""
    try:
        response = await external_system_service.call_external_api(
            db,
            system_name="weather_api",
            method="GET",
            endpoint="/v1/weather/current",
            params={"city": city}
        )
        
        return {
            "city": city,
            "weather": response["data"],
            "updated_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取天气信息失败: {str(e)}"
        )
```

## 中间件使用

### 启用外部系统认证中间件

在 `app/core/application.py` 中添加中间件：

```python
from app.core.middleware.external_auth import ExternalSystemAuthMiddleware

def setup_middlewares(app: FastAPI) -> None:
    """Setup application middlewares"""
    # 添加外部系统认证中间件
    app.add_middleware(ExternalSystemAuthMiddleware)
```

### 在路由中检查认证状态

```python
from app.core.middleware.external_auth import check_external_system_auth

@router.get("/protected-external-data")
async def get_protected_data(request: Request):
    """获取受保护的外部数据"""
    # 检查天气API是否已认证
    if not await check_external_system_auth(request, "weather_api"):
        raise HTTPException(
            status_code=401,
            detail="天气API未认证"
        )
    
    # 继续处理业务逻辑
    return {"message": "可以访问外部数据"}
```

## 配置说明

### 外部系统配置字段

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| name | string | 是 | 系统唯一标识名 |
| display_name | string | 否 | 系统显示名称 |
| base_url | string | 是 | 系统基础URL |
| auth_url | string | 否 | 认证端点URL |
| username | string | 是 | 登录用户名 |
| password | string | 是 | 登录密码 |
| auth_type | string | 否 | 认证类型，默认username_password |
| session_timeout | integer | 否 | 会话超时时间(秒)，默认3600 |
| max_retry_count | integer | 否 | 最大重试次数，默认3 |
| is_active | boolean | 否 | 是否启用，默认true |
| extra_config | JSON | 否 | 扩展配置信息 |

## 最佳实践

### 1. 安全性考虑

- 密码在数据库中加密存储
- 敏感信息不记录在日志中
- 使用HTTPS连接外部系统
- 定期轮换认证凭据

### 2. 性能优化

- 合理设置会话超时时间
- 使用连接池管理HTTP连接
- 缓存频繁访问的数据
- 实施调用频率限制

### 3. 错误处理

- 实现重试机制
- 记录详细的错误日志
- 提供友好的错误信息
- 实施熔断机制

### 4. 监控和维护

- 定期检查系统认证状态
- 监控API调用成功率
- 设置告警机制
- 定期清理过期会话

## 故障排除

### 常见问题

1. **认证失败**
   - 检查用户名密码是否正确
   - 确认外部系统是否可用
   - 查看认证日志获取详细错误信息

2. **API调用超时**
   - 增加超时时间配置
   - 检查网络连接
   - 确认外部系统响应时间

3. **会话过期**
   - 系统会自动重新认证
   - 可手动触发重新认证
   - 检查会话超时配置

### 日志查看

```bash
# 查看外部系统调用日志
SELECT * FROM external_system_logs ORDER BY created_at DESC LIMIT 10;

# 查看系统状态
SELECT name, auth_status, last_login_time FROM external_systems;
```

## 扩展功能

### 添加新的认证类型

```python
# 在ExternalSystem模型中扩展auth_type字段
# 支持API Key、OAuth等认证方式
```

### 实现负载均衡

```python
# 支持多个实例的外部系统
# 实现轮询或权重分配策略
```

### 添加缓存层

```python
# 对频繁访问的数据实施缓存
# 减少对外部系统的调用次数
```