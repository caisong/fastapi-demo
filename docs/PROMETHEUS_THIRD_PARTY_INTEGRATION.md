# Prometheus 第三方数据集成方案

## 概述

本项目实现了完整的Prometheus第三方数据集成方案，包含三个核心功能：

1. **Pushgateway服务器** - 接收第三方数据并转换为Prometheus指标
2. **查询Prometheus相关数据** - 提供完整的查询API
3. **定时任务** - 定期调用第三方API并推送数据

## 架构图

```
第三方API → 定时任务 → Pushgateway → Prometheus → Grafana
    ↓           ↓           ↓           ↓         ↓
  数据源    数据收集    指标存储    指标查询    可视化
```

## 功能详解

### 1. Pushgateway服务器

**文件位置：**
- `app/services/pushgateway.py` - Pushgateway服务
- `scripts/start_pushgateway.py` - 启动脚本

**功能：**
- 接收第三方API数据
- 转换为Prometheus指标格式
- 提供`/metrics`端点供Prometheus抓取
- 支持认证和分组

**启动方式：**
```bash
# 直接启动
python scripts/start_pushgateway.py

# Docker启动
docker-compose --profile metrics up pushgateway
```

**API端点：**
- `GET /metrics` - Prometheus指标
- `GET /health` - 健康检查
- `GET /status` - 状态查询
- `POST /metrics/job/{job_name}` - 推送指标

### 2. 第三方数据收集

**文件位置：**
- `app/tasks/third_party_collector.py` - 数据收集器
- `app/api/v1/endpoints/third_party_metrics.py` - API端点

**功能：**
- 定期调用第三方API
- 将响应数据转换为指标
- 推送到Pushgateway
- 支持多种API配置

**配置示例：**
```python
apis_config = [
    {
        "name": "weather_api",
        "url": "https://api.openweathermap.org/data/2.5/weather",
        "params": {"q": "London", "appid": "your_api_key"},
        "interval": 300,  # 5分钟
        "enabled": True
    },
    {
        "name": "crypto_api",
        "url": "https://api.coingecko.com/api/v3/simple/price",
        "params": {"ids": "bitcoin,ethereum", "vs_currencies": "usd"},
        "interval": 60,  # 1分钟
        "enabled": True
    }
]
```

### 3. 定时任务调度

**文件位置：**
- `app/core/scheduler.py` - 调度器
- `app/worker.py` - 任务执行器

**功能：**
- 基于ARQ的定时任务
- 支持cron表达式
- 任务监控和错误处理
- 可配置的间隔时间

## 使用方法

### 1. 启动服务

```bash
# 启动所有服务
docker-compose --profile metrics up

# 或者分别启动
docker-compose up fastapi_app
docker-compose up pushgateway
docker-compose up prometheus
docker-compose up grafana
```

### 2. 配置API

```bash
# 查看API配置
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/v1/third-party-metrics/config

# 启用API
curl -X PUT -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/v1/third-party-metrics/config/weather_api/enable

# 禁用API
curl -X PUT -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/v1/third-party-metrics/config/weather_api/disable
```

### 3. 手动触发收集

```bash
# 收集所有API数据
curl -X POST -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/v1/third-party-metrics/collect

# 收集特定API数据
curl -X POST -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/v1/third-party-metrics/collect/weather_api
```

### 4. 查看指标

```bash
# 查看Pushgateway指标
curl http://localhost:9091/metrics

# 查看Prometheus指标
curl http://localhost:9090/api/v1/query?query=third_party_api_requests_total
```

## 指标类型

### 1. API调用指标

- `third_party_api_requests_total` - API请求总数
- `third_party_api_request_duration_seconds` - API请求耗时
- `third_party_api_errors_total` - API错误总数

### 2. 业务指标

- `business_metrics` - 业务指标（从API响应提取）
- `data_quality_score` - 数据质量评分

### 3. 系统指标

- `pushgateway_metrics_received_total` - 接收的指标总数
- `pushgateway_jobs_active` - 活跃任务数

## 监控和告警

### 1. Grafana仪表板

访问 `http://localhost:3000` 查看可视化仪表板

### 2. 告警规则

```yaml
# prometheus/alerts.yml
groups:
  - name: third_party_api
    rules:
      - alert: APIDown
        expr: up{job="pushgateway"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Pushgateway is down"
      
      - alert: HighAPIErrorRate
        expr: rate(third_party_api_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High API error rate detected"
```

## 配置说明

### 环境变量

```bash
# Pushgateway配置
PUSHGATEWAY_URL=http://localhost:9091
PUSHGATEWAY_USERNAME=admin
PUSHGATEWAY_PASSWORD=password

# 第三方API配置
WEATHER_API_KEY=your_weather_api_key
CRYPTO_API_KEY=your_crypto_api_key

# 调度器配置
SCHEDULER_ENABLED=true
COLLECTION_INTERVAL=300
```

### Docker配置

```yaml
# docker-compose.yml
services:
  pushgateway:
    ports:
      - "9091:9091"
    environment:
      PUSHGATEWAY_PORT: 9091
    profiles:
      - metrics
```

## 故障排除

### 1. 常见问题

**问题：Pushgateway无法启动**
```bash
# 检查端口占用
netstat -tlnp | grep 9091

# 检查日志
docker logs fastapi_pushgateway
```

**问题：第三方API调用失败**
```bash
# 检查API配置
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/v1/third-party-metrics/status

# 检查任务日志
docker logs fastapi_worker
```

**问题：指标不显示**
```bash
# 检查Prometheus配置
curl http://localhost:9090/api/v1/targets

# 检查Pushgateway状态
curl http://localhost:9091/status
```

### 2. 调试模式

```bash
# 启用详细日志
export LOG_LEVEL=DEBUG

# 手动测试API调用
python -c "
import asyncio
from app.tasks.third_party_collector import collector
asyncio.run(collector.collect_all_apis())
"
```

## 扩展功能

### 1. 添加新的API

在 `app/tasks/third_party_collector.py` 中添加新的API配置：

```python
{
    "name": "new_api",
    "url": "https://api.example.com/data",
    "params": {"key": "value"},
    "interval": 600,
    "enabled": True
}
```

### 2. 自定义指标转换

在 `app/services/pushgateway.py` 中自定义转换逻辑：

```python
def _convert_api_response_to_metrics(self, api_name: str, response_data: Dict[str, Any]) -> Dict[str, Any]:
    # 自定义转换逻辑
    metrics = {}
    # ... 转换逻辑
    return metrics
```

### 3. 添加告警规则

在 `prometheus/alerts.yml` 中添加新的告警规则。

## 总结

本方案提供了完整的第三方数据集成解决方案：

1. ✅ **Pushgateway服务器** - 接收和存储第三方数据
2. ✅ **查询功能** - 完整的Prometheus查询API
3. ✅ **定时任务** - 自动化的数据收集
4. ✅ **监控告警** - 完整的监控体系
5. ✅ **可扩展性** - 易于添加新的API和指标

通过这个方案，您可以轻松地将任何第三方API数据集成到Prometheus监控体系中。