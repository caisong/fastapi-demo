# FastAPI 开发服务器使用指南

## 🚀 开发服务器选项

项目提供了多种启动开发服务器的方式，根据不同的开发需求选择合适的方式：

### 1. 单纯 API 开发 (推荐)

```bash
make dev
```

**适用场景**：
- 🎯 纯 API 开发和测试
- 📚 查看和测试 API 文档
- 🔍 调试单个端点
- ⚡ 快速启动，专注于 API 逻辑

**特性**：
- ✅ 自动重载 (文件变更时自动重启)
- ✅ 完整的 API 文档支持
- ✅ 交互式 API 测试界面
- ✅ 管理界面支持
- ✅ 使用虚拟环境
- ✅ 绑定到所有网络接口 (0.0.0.0:8000)

**访问地址**：
- 🌐 **API 服务**: http://localhost:8000
- 📝 **Swagger 文档**: http://localhost:8000/docs
- 🔍 **ReDoc 文档**: http://localhost:8000/redoc
- 🔴 **管理界面**: http://localhost:8000/admin

### 2. 快速启动

```bash
make dev-quick
```

**适用场景**：
- ⚡ 最快速的服务器启动
- 🔇 minimal 输出，专注于代码
- 📱 默认配置 (127.0.0.1:8000)

### 3. 完整开发环境

```bash
make start-dev
```

**适用场景**：
- 🔄 需要后台任务处理 (ARQ Worker)
- 📊 需要监控和指标收集
- 🗄️ 需要 Redis 缓存
- 🏗️ 全栈开发和集成测试

**包含服务**：
- FastAPI Web 服务器
- ARQ 异步任务 Worker
- Prometheus 指标服务
- Pushgateway 指标推送
- Redis 缓存服务

## 📊 对比表

| 启动方式 | 启动速度 | 功能完整性 | 资源占用 | 适用场景 |
|----------|----------|------------|----------|----------|
| `make dev` | ⚡⚡⚡ | API + 文档 | 低 | API 开发、文档查看 |
| `make dev-quick` | ⚡⚡⚡⚡ | 基础 API | 最低 | 快速测试 |
| `make start-dev` | ⚡⚡ | 完整环境 | 高 | 全栈开发 |

## 🛠️ FastAPI CLI 功能

使用 `fastapi dev` 的优势：

### 自动重载
```
✅ 检测文件变更并自动重启
✅ 支持 Python 文件、配置文件等
✅ 无需手动重启服务器
```

### 开发者友好的输出
```
FastAPI  Starting development server 🚀

Server started at http://0.0.0.0:8000
Documentation at http://0.0.0.0:8000/docs

Logs:
INFO   Uvicorn running on http://0.0.0.0:8000
```

### 内置文档服务
- **Swagger UI**: 交互式 API 测试界面
- **ReDoc**: 美观的 API 文档展示
- **OpenAPI Schema**: 标准的 API 规范

## 🔧 自定义配置

### 修改端口
```bash
# 在 Makefile 中修改 dev 目标
fastapi dev main.py --host 0.0.0.0 --port 3000
```

### 修改主机
```bash
# 仅本地访问
fastapi dev main.py --host 127.0.0.1 --port 8000

# 允许外部访问
fastapi dev main.py --host 0.0.0.0 --port 8000
```

### 环境变量配置
```bash
# 设置开发环境
export ENVIRONMENT=development

# 启用调试模式
export DEBUG=true

# 自定义数据库URL
export DATABASE_URL=postgresql://user:pass@localhost/dev_db
```

## 📱 API 文档使用指南

### Swagger UI (推荐)
访问: http://localhost:8000/docs

**功能**：
- 🧪 **Try it out**: 直接在浏览器中测试 API
- 📋 **Request/Response**: 查看请求和响应示例
- 🔐 **Authorization**: 测试需要认证的端点
- 📄 **Schema**: 查看数据模型定义

**使用步骤**：
1. 打开 http://localhost:8000/docs
2. 找到想要测试的端点
3. 点击 "Try it out"
4. 填入参数
5. 点击 "Execute"
6. 查看响应结果

### ReDoc
访问: http://localhost:8000/redoc

**特点**：
- 📖 更适合阅读的文档格式
- 🎨 美观的界面设计
- 📱 响应式布局
- 🔍 强大的搜索功能

## 🔐 管理界面

访问: http://localhost:8000/admin

**功能**：
- 👥 用户管理
- 📦 数据项管理
- 🗄️ 数据库直接操作
- 📊 数据统计查看

**登录凭据**（开发环境）：
- 用户名: admin@example.com
- 密码: admin123

⚠️ **注意**: 生产环境必须修改默认密码！

## 🎯 开发工作流建议

### 日常 API 开发
```bash
# 1. 启动开发服务器
make dev

# 2. 在另一个终端运行测试
make test

# 3. 查看 API 文档
open http://localhost:8000/docs
```

### 需要后台任务时
```bash
# 1. 启动完整环境
make start-dev

# 2. 测试异步任务
# 在 API 文档中测试 /api/v1/tasks/ 端点
```

### 数据库开发
```bash
# 1. 初始化数据库
make db-init

# 2. 启动服务器
make dev

# 3. 使用管理界面查看数据
open http://localhost:8000/admin
```

## 🔍 调试技巧

### 查看日志
```bash
# 实时查看应用日志
tail -f logs/app.log

# 如果使用 start-dev，查看所有服务日志
make logs
```

### 网络问题调试
```bash
# 检查端口占用
lsof -i :8000

# 检查服务状态
make health-check
```

### API 测试
```bash
# 使用 curl 测试
curl -X GET "http://localhost:8000/api/v1/users/" \
     -H "Authorization: Bearer YOUR_TOKEN"

# 使用 httpx (Python)
# 项目已安装 httpx，可以在代码中使用
```

## 📝 最佳实践

1. **优先使用 `make dev`** 进行 API 开发
2. **利用自动重载** 提高开发效率
3. **经常查看 API 文档** 确保接口正确性
4. **使用管理界面** 进行数据管理和调试
5. **定期运行测试** 确保代码质量
6. **合理选择启动方式** 根据需求选择合适的环境

## 🚀 生产环境部署

开发完成后，使用以下命令部署到生产环境：

```bash
# 生产环境启动
fastapi run main.py --host 0.0.0.0 --port 8000

# 或使用 Docker
docker-compose up --build
```

⚠️ **注意**: 生产环境不要使用 `fastapi dev`，应该使用 `fastapi run`。