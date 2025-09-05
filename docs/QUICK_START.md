# 快速开始指南

本指南将帮助您快速上手优化后的FastAPI框架。

## 🚀 快速启动

### 1. 环境准备

```bash
# 激活虚拟环境
source /data/fastapi/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动应用

```bash
# 使用快速启动脚本（推荐）
bash start.sh

# 或使用Makefile
make start-dev

# 或使用honcho
honcho start -f Procfile.dev
```

### 3. 访问应用

- **API文档**: http://localhost:8000/docs
- **ReDoc文档**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health
- **Prometheus指标**: http://localhost:9090/metrics
- **Pushgateway**: http://localhost:9091/health

## 📝 开发指南

### 1. 创建新服务

```python
# app/services/my_service.py
from app.core.service_base import CRUDService
from app.models.my_model import MyModel
from sqlalchemy.ext.asyncio import AsyncSession

class MyService(CRUDService[MyModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, MyModel)
    
    async def get_by_name(self, name: str):
        return await self.get_by_field("name", name)
```

### 2. 创建API端点

```python
# app/api/v1/endpoints/my_endpoints.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.services.my_service import MyService
from app.core.response import create_response, create_created_response

router = APIRouter()

@router.get("/")
async def get_items(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取所有项目"""
    service = MyService(db)
    items = await service.get_all(skip=skip, limit=limit)
    return create_response(data=items)

@router.post("/")
async def create_item(
    item_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """创建新项目"""
    service = MyService(db)
    item = await service.create(item_data)
    return create_created_response(data=item)
```

### 3. 创建插件

```python
# app/plugins/my_plugin.py
from app.core.plugins import RoutePlugin
from fastapi import APIRouter

class MyPlugin(RoutePlugin):
    def __init__(self):
        super().__init__("my_plugin", "1.0.0")
    
    def create_router(self) -> APIRouter:
        router = APIRouter(prefix="/my-plugin", tags=["my-plugin"])
        
        @router.get("/")
        async def my_endpoint():
            return {"message": "Hello from my plugin!"}
        
        return router

# 注册插件
my_plugin = MyPlugin()
```

### 4. 使用依赖注入

```python
# app/services/cache_service.py
from app.core.dependency_injection import injectable, inject
from app.core.service_base import CacheService

@injectable
class MyCachedService:
    def __init__(self):
        self.cache = inject(CacheService)
    
    async def get_data(self, key: str):
        # 先尝试从缓存获取
        cached_data = await self.cache.get(key)
        if cached_data:
            return cached_data
        
        # 缓存未命中，从数据库获取
        data = await self._fetch_from_database(key)
        await self.cache.set(key, data, ttl=300)
        return data
```

### 5. 编写测试

```python
# tests/test_my_service.py
import pytest
from app.core.testing import async_test_client, test_data_manager

@pytest.mark.asyncio
async def test_get_items(async_test_client):
    """测试获取项目列表"""
    async with async_test_client as client:
        response = await client.get("/api/v1/items/")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "success" in data

@pytest.mark.asyncio
async def test_create_item(async_test_client, test_user):
    """测试创建项目"""
    async with async_test_client as client:
        item_data = {
            "title": "Test Item",
            "description": "Test Description",
            "owner_id": test_user.id
        }
        response = await client.post("/api/v1/items/", json=item_data)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "data" in data
```

## 🔧 配置说明

### 1. 环境变量

```bash
# 基本配置
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost/dbname
REDIS_URL=redis://localhost:6379

# API配置
API_TITLE=My FastAPI App
API_VERSION=1.0.0
API_DESCRIPTION=My FastAPI Application

# 监控配置
ENABLE_METRICS=true
PROMETHEUS_SERVER_URL=http://localhost:9090
PUSHGATEWAY_URL=http://localhost:9091

# 插件配置
ENABLE_PLUGINS=true
PLUGIN_DIRECTORY=app/plugins

# 中间件配置
ENABLE_CORS=true
ENABLE_RATE_LIMIT=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### 2. 配置文件

```python
# app/core/config.py
class Settings(BaseSettings):
    # 基本配置
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://user:password@localhost/dbname"
    REDIS_URL: str = "redis://localhost:6379"
    
    # API配置
    API_TITLE: str = "My FastAPI App"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "My FastAPI Application"
    
    # 监控配置
    ENABLE_METRICS: bool = True
    PROMETHEUS_SERVER_URL: str = "http://localhost:9090"
    PUSHGATEWAY_URL: str = "http://localhost:9091"
    
    # 插件配置
    ENABLE_PLUGINS: bool = True
    PLUGIN_DIRECTORY: str = "app/plugins"
    
    # 中间件配置
    ENABLE_CORS: bool = True
    ENABLE_RATE_LIMIT: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60
```

## 🧪 测试指南

### 1. 运行测试

```bash
# 运行所有测试
make test

# 运行特定测试
make test-auth
make test-api

# 运行测试并生成覆盖率报告
make test-coverage

# 运行测试并生成HTML报告
make test-report
```

### 2. 测试配置

```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=app
    --cov-report=html
    --cov-report=term-missing
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow tests
```

## 📊 监控和日志

### 1. 日志查看

```bash
# 查看所有服务日志
make logs

# 查看特定服务日志
make logs-web
make logs-worker
make logs-prometheus
make logs-pushgateway
```

### 2. 健康检查

```bash
# 检查服务健康状态
make health-check

# 手动检查各个服务
curl http://localhost:8000/health
curl http://localhost:9090/metrics
curl http://localhost:9091/health
redis-cli ping
```

### 3. 监控指标

```bash
# 查看Prometheus指标
curl http://localhost:9090/metrics

# 查看Pushgateway指标
curl http://localhost:9091/metrics

# 查询特定指标
curl "http://localhost:9090/api/v1/query?query=up"
```

## 🚀 部署指南

### 1. 生产环境配置

```bash
# 设置环境变量
export ENVIRONMENT=production
export DEBUG=false
export LOG_LEVEL=INFO
export ENABLE_METRICS=true

# 启动生产环境
make start
```

### 2. Docker部署

```bash
# 构建镜像
docker build -t my-fastapi-app .

# 运行容器
docker run -p 8000:8000 my-fastapi-app

# 使用docker-compose
docker-compose up -d
```

### 3. 服务管理

```bash
# 启动服务
bash start.sh start

# 停止服务
bash start.sh stop

# 查看状态
bash start.sh status

# 重启服务
bash start.sh restart
```

## 🔍 故障排除

### 1. 常见问题

**问题**: 服务启动失败
```bash
# 检查端口占用
netstat -tlnp | grep :8000

# 检查日志
make logs-web
```

**问题**: 数据库连接失败
```bash
# 检查数据库状态
psql -h localhost -U username -d dbname

# 检查连接字符串
echo $DATABASE_URL
```

**问题**: Redis连接失败
```bash
# 检查Redis状态
redis-cli ping

# 检查Redis配置
redis-cli config get bind
```

### 2. 调试模式

```bash
# 启用调试模式
export DEBUG=true
export LOG_LEVEL=DEBUG

# 启动应用
bash start.sh start-dev
```

### 3. 性能分析

```bash
# 运行性能测试
make test-performance

# 生成性能报告
make benchmark
```

## 📚 更多资源

### 1. 文档
- [框架优化总结](FRAMEWORK_OPTIMIZATION.md)
- [服务管理指南](SERVICE_MANAGEMENT.md)
- [Prometheus集成](PROMETHEUS_THIRD_PARTY_INTEGRATION.md)
- [认证系统改进](AUTHENTICATION_IMPROVEMENTS.md)

### 2. 示例代码
- [插件示例](app/plugins/example_plugin.py)
- [服务示例](app/services/)
- [测试示例](tests/)
- [API示例](app/api/v1/endpoints/)

### 3. 工具和脚本
- [启动脚本](start.sh)
- [服务管理脚本](scripts/start_services.sh)
- [Makefile](Makefile)
- [Docker配置](docker-compose.yml)

## 🤝 贡献指南

### 1. 开发流程
1. Fork项目
2. 创建功能分支
3. 编写代码和测试
4. 提交Pull Request

### 2. 代码规范
- 使用Black格式化代码
- 使用isort排序导入
- 使用flake8检查代码
- 使用mypy类型检查

### 3. 测试要求
- 编写单元测试
- 编写集成测试
- 保持测试覆盖率
- 更新文档

## 🎉 开始使用

现在您已经了解了框架的基本使用方法，可以开始开发您的应用了！

1. 阅读[框架优化总结](FRAMEWORK_OPTIMIZATION.md)了解详细功能
2. 查看[示例代码](app/plugins/example_plugin.py)学习最佳实践
3. 编写您的第一个服务或插件
4. 运行测试确保代码质量
5. 部署到生产环境

祝您开发愉快！🚀