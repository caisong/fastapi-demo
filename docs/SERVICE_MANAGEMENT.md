# 服务管理指南

本项目支持通过多种方式启动和管理服务，包括honcho进程管理器和Makefile命令。

## 快速开始

### 1. 安装依赖

```bash
# 安装所有依赖（包括honcho）
make install-dev

# 或者手动安装
pip install -r requirements.txt
```

### 2. 启动服务

```bash
# 开发环境（包含Redis）
make start-dev

# 生产环境
make start

# 监控环境（包含所有监控服务）
make start-monitoring
```

## 服务说明

### 核心服务

- **web**: FastAPI主应用服务器 (端口: 8000)
- **worker**: ARQ异步任务处理器
- **prometheus**: Prometheus指标代理服务器 (端口: 9090)
- **pushgateway**: Prometheus Pushgateway服务器 (端口: 9091)
- **redis**: Redis服务器 (端口: 6379)

### 服务端口

| 服务 | 端口 | 描述 |
|------|------|------|
| web | 8000 | FastAPI应用 |
| worker | - | 后台任务处理器 |
| prometheus | 9090 | 指标代理 |
| pushgateway | 9091 | 指标推送网关 |
| redis | 6379 | 缓存数据库 |

## 使用方法

### 1. Makefile命令

```bash
# 查看所有可用命令
make help

# 启动服务
make start                # 生产环境
make start-dev            # 开发环境（包含Redis）
make start-monitoring     # 监控环境

# 停止服务
make stop

# 查看状态
make status

# 查看日志
make logs                 # 所有服务日志
make logs-web             # Web服务日志
make logs-worker          # Worker服务日志
make logs-prometheus      # Prometheus服务日志
make logs-pushgateway     # Pushgateway服务日志

# 健康检查
make health-check

# 启动单个服务
make start-web
make start-worker
make start-prometheus
make start-pushgateway
```

### 2. 启动脚本

```bash
# 使用启动脚本
./scripts/start_services.sh start              # 启动所有服务
./scripts/start_services.sh start-dev          # 开发环境
./scripts/start_services.sh start-monitoring   # 监控环境
./scripts/start_services.sh stop               # 停止服务
./scripts/start_services.sh status             # 查看状态
./scripts/start_services.sh logs               # 查看日志
./scripts/start_services.sh health             # 健康检查
./scripts/start_services.sh help               # 帮助信息

# 启动特定服务
./scripts/start_services.sh start web worker
./scripts/start_services.sh start prometheus pushgateway
```

### 3. Honcho命令

```bash
# 直接使用honcho
honcho start                                    # 使用默认Procfile
honcho start -f Procfile.dev                    # 使用开发环境配置
honcho start -f Procfile.monitoring             # 使用监控环境配置

# 启动特定服务
honcho start web worker                         # 只启动web和worker
honcho start prometheus pushgateway             # 只启动监控服务

# 查看日志
honcho logs                                     # 所有服务日志
honcho logs web                                 # 特定服务日志

# 停止服务
honcho stop                                     # 停止所有服务
```

## 配置文件

### Procfile

```bash
# 生产环境配置
web: python scripts/dev.py
worker: python scripts/start_worker.py
prometheus: python scripts/start_prometheus.py
pushgateway: python scripts/start_pushgateway.py
```

### Procfile.dev

```bash
# 开发环境配置（包含Redis）
web: python scripts/dev.py
worker: python scripts/start_worker.py
prometheus: python scripts/start_prometheus.py
pushgateway: python scripts/start_pushgateway.py
redis: redis-server --port 6379 --loglevel warning
```

### Procfile.monitoring

```bash
# 监控环境配置（包含Redis监控）
web: python scripts/dev.py
worker: python scripts/start_worker.py
prometheus: python scripts/start_prometheus.py
pushgateway: python scripts/start_pushgateway.py
redis: redis-server --port 6379 --loglevel warning
monitor: redis-cli monitor
```

## 环境变量

### 服务配置

```bash
# 端口配置
PORT=8000                    # FastAPI端口
PROMETHEUS_PORT=9090         # Prometheus端口
PUSHGATEWAY_PORT=9091        # Pushgateway端口
REDIS_PORT=6379              # Redis端口

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost/dbname
REDIS_URL=redis://localhost:6379

# 监控配置
ENABLE_METRICS=true
PROMETHEUS_SERVER_URL=http://localhost:9090
PUSHGATEWAY_URL=http://localhost:9091
```

## 故障排除

### 1. 常见问题

**问题：服务启动失败**
```bash
# 检查端口占用
netstat -tlnp | grep :8000
netstat -tlnp | grep :9090
netstat -tlnp | grep :9091

# 检查进程
ps aux | grep python
ps aux | grep redis
```

**问题：honcho命令不存在**
```bash
# 安装honcho
pip install honcho

# 或者使用make命令
make install-honcho
```

**问题：Redis连接失败**
```bash
# 检查Redis是否运行
redis-cli ping

# 启动Redis
redis-server --port 6379 --daemonize yes
```

### 2. 日志查看

```bash
# 查看所有服务日志
make logs

# 查看特定服务日志
make logs-web
make logs-worker
make logs-prometheus
make logs-pushgateway

# 使用honcho查看日志
honcho logs
honcho logs web
```

### 3. 健康检查

```bash
# 检查服务健康状态
make health-check

# 手动检查各个服务
curl http://localhost:8000/health          # FastAPI健康检查
curl http://localhost:9090/metrics         # Prometheus指标
curl http://localhost:9091/health          # Pushgateway健康检查
redis-cli ping                             # Redis健康检查
```

## 开发工作流

### 1. 日常开发

```bash
# 启动开发环境
make start-dev

# 在另一个终端查看日志
make logs

# 停止服务
make stop
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
make start

# 检查服务状态
make status

# 健康检查
make health-check
```

## 高级用法

### 1. 自定义服务配置

创建自定义Procfile：

```bash
# Procfile.custom
web: python scripts/dev.py --host 0.0.0.0 --port 8000
worker: python scripts/start_worker.py --workers 4
prometheus: python scripts/start_prometheus.py --port 9090
```

使用自定义配置：

```bash
honcho start -f Procfile.custom
```

### 2. 环境变量覆盖

```bash
# 设置环境变量
export PORT=9000
export PROMETHEUS_PORT=9091

# 启动服务（会使用新的端口）
make start
```

### 3. 服务监控

```bash
# 启动监控环境
make start-monitoring

# 查看服务状态
make status

# 健康检查
make health-check
```

## 总结

本项目提供了完整的服务管理解决方案：

1. **多种启动方式** - Makefile、启动脚本、honcho
2. **灵活配置** - 支持不同环境的配置文件
3. **完整监控** - 包含Prometheus和Pushgateway
4. **易于使用** - 简单的命令和清晰的文档
5. **故障排除** - 完整的日志和健康检查功能

选择最适合您需求的方式来管理服务，推荐使用Makefile命令进行日常开发。