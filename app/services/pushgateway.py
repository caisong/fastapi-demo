"""
Prometheus Pushgateway Service
接收第三方数据并转换为Prometheus指标格式
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, push_to_gateway
from prometheus_client.exposition import basic_auth_handler

from app.core.config import settings

logger = logging.getLogger(__name__)


class PushgatewayService:
    """Prometheus Pushgateway服务"""
    
    def __init__(self):
        self.pushgateway_url = getattr(settings, 'PUSHGATEWAY_URL', 'http://localhost:9091')
        self.username = getattr(settings, 'PUSHGATEWAY_USERNAME', None)
        self.password = getattr(settings, 'PUSHGATEWAY_PASSWORD', None)
        
        # 创建指标注册表
        self.registry = CollectorRegistry()
        
        # 定义常用指标
        self._setup_metrics()
    
    def _setup_metrics(self):
        """设置常用指标"""
        # 第三方API调用指标
        self.api_request_total = Counter(
            'third_party_api_requests_total',
            'Total number of third party API requests',
            ['api_name', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.api_request_duration = Histogram(
            'third_party_api_request_duration_seconds',
            'Duration of third party API requests',
            ['api_name', 'endpoint'],
            registry=self.registry
        )
        
        # 业务指标
        self.business_metrics = Gauge(
            'business_metrics',
            'Business metrics from third party APIs',
            ['metric_name', 'source', 'category'],
            registry=self.registry
        )
        
        # 数据质量指标
        self.data_quality_score = Gauge(
            'data_quality_score',
            'Data quality score from third party sources',
            ['source', 'data_type'],
            registry=self.registry
        )
    
    def _get_auth_handler(self):
        """获取认证处理器"""
        if self.username and self.password:
            def auth_handler(url, method, timeout, headers, data):
                return basic_auth_handler(url, method, timeout, headers, data, self.username, self.password)
            return auth_handler
        return None
    
    async def push_metrics(self, job_name: str, metrics_data: Dict[str, Any], 
                          grouping_key: Optional[Dict[str, str]] = None) -> bool:
        """
        推送指标到Pushgateway
        
        Args:
            job_name: 任务名称
            metrics_data: 指标数据
            grouping_key: 分组键
        """
        try:
            # 更新指标值
            self._update_metrics(metrics_data)
            
            # 推送到Pushgateway
            auth_handler = self._get_auth_handler()
            push_to_gateway(
                gateway=self.pushgateway_url,
                job=job_name,
                registry=self.registry,
                handler=auth_handler,
                grouping_key=grouping_key or {}
            )
            
            logger.info(f"Metrics pushed successfully for job: {job_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to push metrics for job {job_name}: {str(e)}")
            return False
    
    def _update_metrics(self, metrics_data: Dict[str, Any]):
        """更新指标值"""
        for metric_name, value in metrics_data.items():
            if metric_name.startswith('api_request_total'):
                # API请求总数
                parts = metric_name.split('_')
                if len(parts) >= 4:
                    api_name = parts[3]
                    endpoint = parts[4] if len(parts) > 4 else 'unknown'
                    status = parts[5] if len(parts) > 5 else 'success'
                    self.api_request_total.labels(
                        api_name=api_name,
                        endpoint=endpoint,
                        status=status
                    ).inc(value)
            
            elif metric_name.startswith('api_request_duration'):
                # API请求耗时
                parts = metric_name.split('_')
                if len(parts) >= 4:
                    api_name = parts[3]
                    endpoint = parts[4] if len(parts) > 4 else 'unknown'
                    self.api_request_duration.labels(
                        api_name=api_name,
                        endpoint=endpoint
                    ).observe(value)
            
            elif metric_name.startswith('business_'):
                # 业务指标
                source = metrics_data.get('source', 'unknown')
                category = metrics_data.get('category', 'general')
                self.business_metrics.labels(
                    metric_name=metric_name,
                    source=source,
                    category=category
                ).set(value)
            
            elif metric_name.startswith('data_quality'):
                # 数据质量指标
                source = metrics_data.get('source', 'unknown')
                data_type = metrics_data.get('data_type', 'unknown')
                self.data_quality_score.labels(
                    source=source,
                    data_type=data_type
                ).set(value)
    
    async def push_third_party_data(self, job_name: str, api_name: str, 
                                   response_data: Dict[str, Any]) -> bool:
        """
        推送第三方API数据作为指标
        
        Args:
            job_name: 任务名称
            api_name: API名称
            response_data: API响应数据
        """
        try:
            # 转换API响应为指标数据
            metrics_data = self._convert_api_response_to_metrics(api_name, response_data)
            
            # 推送到Pushgateway
            grouping_key = {
                'api_name': api_name,
                'timestamp': datetime.now().isoformat()
            }
            
            return await self.push_metrics(job_name, metrics_data, grouping_key)
            
        except Exception as e:
            logger.error(f"Failed to push third party data for {api_name}: {str(e)}")
            return False
    
    def _convert_api_response_to_metrics(self, api_name: str, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将API响应转换为Prometheus指标格式
        
        Args:
            api_name: API名称
            response_data: API响应数据
            
        Returns:
            转换后的指标数据
        """
        metrics = {}
        
        # 基础API调用指标
        metrics['api_request_total'] = 1
        metrics['api_request_duration'] = response_data.get('response_time', 0)
        
        # 根据API响应内容提取业务指标
        if 'data' in response_data:
            data = response_data['data']
            
            # 如果是列表，计算数量
            if isinstance(data, list):
                metrics['business_data_count'] = len(data)
                metrics['source'] = api_name
                metrics['category'] = 'count'
            
            # 如果是字典，提取数值字段
            elif isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        metrics[f'business_{key}'] = value
                        metrics['source'] = api_name
                        metrics['category'] = 'value'
        
        # 数据质量评分
        metrics['data_quality_score'] = response_data.get('quality_score', 1.0)
        metrics['source'] = api_name
        metrics['data_type'] = 'api_response'
        
        return metrics


# 创建服务实例
pushgateway_service = PushgatewayService()