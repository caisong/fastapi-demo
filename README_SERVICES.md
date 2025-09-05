# 服务启动指南

本项目支持多种方式启动和管理服务，包括honcho进程管理器、Makefile命令和快速启动脚本。

## 🚀 快速开始

### 方法1：快速启动脚本（推荐）

```bash
# 启动开发环境（包含Redis）
bash start.sh

# 启动生产环境
bash start.sh start

# 启动监控环境
bash start.sh start-monitoring

# 停止所有服务
bash start.sh stop

# 查看服务状态
bash start.sh status

# 查看帮助
bash start.sh help
```

### 方法2：Makefile命令

```bash
# 激活虚拟环境
source /data/fastapi/bin/activate

# 启动开发环境
make start-dev

# 启动生产环境
make start

# 启动监控环境
make start-monitoring

# 停止服务
make stop

# 查看状态
make status

# 查看日志
make logs
```

### 方法3：启动脚本

```bash
# 激活虚拟环境
source /data/fastapi/bin/activate

# 启动开发环境
./scripts/start_services.sh start-dev

# 启动生产环境
./scripts/start_services.sh start

# 停止服务
./scripts/start_services.sh stop

# 查看状态
./scripts/start_services.sh status
```

### 方法4：Honcho命令

```bash
# 激活虚拟环境
source /data/fastapi/bin/activate

# 启动开发环境
honcho start -f Procfile.dev

# 启动生产环境
honcho start

# 启动监控环境
honcho start -f Procfile.monitoring

# 查看日志
honcho logs
```

## 📋 服务说明

| 服务 | 端口 | 描述 | 启动命令 |
|------|------|------|----------|
| web | 8000 | FastAPI主应用 | `python scripts/dev.py` |
| worker | - | ARQ任务处理器 | `python scripts/start_worker.py` |
| prometheus | 9090 | 指标代理服务器 | `python scripts/start_prometheus.py` |
| pushgateway | 9091 | 指标推送网关 | `python scripts/start_pushgateway.py` |
| redis | 6379 | 缓存数据库 | `redis-server --port 6379` |

## 🔧 配置文件

### Procfile（生产环境）
```bash
web: python scripts/dev.py
worker: python scripts/start_worker.py
prometheus: python scripts/start_prometheus.py
pushgateway: python scripts/start_pushgateway.py
```

### Procfile.dev（开发环境）
```bash
web: python scripts/dev.py
worker: python scripts/start_worker.py
prometheus: python scripts/start_prometheus.py
pushgateway: python scripts/start_pushgateway.py
redis: redis-server --port 6379 --loglevel warning
```

### Procfile.monitoring（监控环境）
```bash
web: python scripts/dev.py
worker: python scripts/start_worker.py
prometheus: python scripts/start_prometheus.py
pushgateway: python scripts/start_pushgateway.py
redis: redis-server --port 6379 --loglevel warning
monitor: redis-cli monitor
```

## 🛠️ 常用命令

### 服务管理
```bash
# 启动所有服务
make start-dev

# 停止所有服务
make stop

# 查看服务状态
make status

# 查看所有日志
make logs

# 查看特定服务日志
make logs-web
make logs-worker
make logs-prometheus
make logs-pushgateway

# 健康检查
make health-check
```

### 单个服务
```bash
# 启动单个服务
make start-web
make start-worker
make start-prometheus
make start-pushgateway

# 启动特定服务组合
honcho start web worker
honcho start prometheus pushgateway
```

## 🔍 故障排除

### 1. 虚拟环境问题
```bash
# 检查虚拟环境
ls -la /data/fastapi/bin/activate

# 激活虚拟环境
source /data/fastapi/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 端口占用问题
```bash
# 检查端口占用
netstat -tlnp | grep :8000
netstat -tlnp | grep :9090
netstat -tlnp | grep :9091

# 杀死占用端口的进程
sudo kill -9 <PID>
```

### 3. 服务启动失败
```bash
# 查看详细日志
make logs-web
make logs-worker

# 检查服务状态
make status

# 健康检查
make health-check
```

### 4. Redis连接问题
```bash
# 检查Redis是否运行
redis-cli ping

# 启动Redis
redis-server --port 6379 --daemonize yes
```

## 📊 监控和健康检查

### 服务端点
- **FastAPI应用**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **Prometheus指标**: http://localhost:9090/metrics
- **Pushgateway**: http://localhost:9091/health

### 健康检查命令
```bash
# 使用Makefile
make health-check

# 使用启动脚本
./scripts/start_services.sh health

# 手动检查
curl http://localhost:8000/health
curl http://localhost:9090/metrics
curl http://localhost:9091/health
redis-cli ping
```

## 🚀 开发工作流

### 1. 日常开发
```bash
# 启动开发环境
bash start.sh

# 在另一个终端查看日志
make logs

# 停止服务
bash start.sh stop
```

### 2. 测试
```bash
# 运行测试
make test

# 运行特定测试
make test-auth
make test-api

# 查看测试覆盖率
make test-coverage
```

### 3. 部署
```bash
# 生产环境启动
bash start.sh start

# 检查服务状态
bash start.sh status

# 健康检查
bash start.sh health
```

## 📝 环境变量

### 服务配置
```bash
# 端口配置
export PORT=8000
export PROMETHEUS_PORT=9090
export PUSHGATEWAY_PORT=9091
export REDIS_PORT=6379

# 数据库配置
export DATABASE_URL=postgresql://user:password@localhost/dbname
export REDIS_URL=redis://localhost:6379

# 监控配置
export ENABLE_METRICS=true
export PROMETHEUS_SERVER_URL=http://localhost:9090
export PUSHGATEWAY_URL=http://localhost:9091
```

## 🎯 推荐使用方式

### 开发环境
```bash
# 使用快速启动脚本（推荐）
bash start.sh

# 或者使用Makefile
source /data/fastapi/bin/activate
make start-dev
```

### 生产环境
```bash
# 使用快速启动脚本
bash start.sh start

# 或者使用Makefile
source /data/fastapi/bin/activate
make start
```

### 监控环境
```bash
# 使用快速启动脚本
bash start.sh start-monitoring

# 或者使用Makefile
source /data/fastapi/bin/activate
make start-monitoring
```

## 📚 更多信息

- [服务管理详细指南](docs/SERVICE_MANAGEMENT.md)
- [Prometheus第三方数据集成](docs/PROMETHEUS_THIRD_PARTY_INTEGRATION.md)
- [认证系统改进](docs/AUTHENTICATION_IMPROVEMENTS.md)

## 🤝 支持

如果遇到问题，请：

1. 检查虚拟环境是否正确激活
2. 查看服务日志：`make logs`
3. 检查服务状态：`make status`
4. 运行健康检查：`make health-check`
5. 查看详细文档：`docs/SERVICE_MANAGEMENT.md`