"""
第三方API数据收集定时任务
定期调用第三方API，将响应数据转换为Prometheus指标
"""
import asyncio
import logging
import aiohttp
from typing import Dict, Any, List
from datetime import datetime

from app.services.pushgateway import pushgateway_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class ThirdPartyAPICollector:
    """第三方API数据收集器"""
    
    def __init__(self):
        self.session: aiohttp.ClientSession = None
        self.apis_config = self._load_apis_config()
    
    def _load_apis_config(self) -> List[Dict[str, Any]]:
        """加载API配置"""
        return [
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
            },
            {
                "name": "stock_api",
                "url": "https://api.example.com/stock/price",
                "params": {"symbols": "AAPL,GOOGL,MSFT"},
                "interval": 300,  # 5分钟
                "enabled": False  # 示例API，默认禁用
            }
        ]
    
    async def start_session(self):
        """启动HTTP会话"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close_session(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def collect_api_data(self, api_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        收集单个API的数据
        
        Args:
            api_config: API配置
            
        Returns:
            收集到的数据
        """
        if not api_config.get("enabled", False):
            logger.info(f"API {api_config['name']} is disabled, skipping")
            return {}
        
        start_time = datetime.now()
        
        try:
            logger.info(f"Collecting data from {api_config['name']}")
            
            # 调用API
            async with self.session.get(
                api_config["url"], 
                params=api_config.get("params", {})
            ) as response:
                
                response_time = (datetime.now() - start_time).total_seconds()
                
                if response.status == 200:
                    data = await response.json()
                    
                    result = {
                        "api_name": api_config["name"],
                        "status": "success",
                        "response_time": response_time,
                        "data": data,
                        "timestamp": start_time.isoformat(),
                        "quality_score": self._calculate_quality_score(data)
                    }
                    
                    logger.info(f"Successfully collected data from {api_config['name']}")
                    return result
                
                else:
                    logger.error(f"API {api_config['name']} returned status {response.status}")
                    return {
                        "api_name": api_config["name"],
                        "status": "error",
                        "response_time": response_time,
                        "error": f"HTTP {response.status}",
                        "timestamp": start_time.isoformat(),
                        "quality_score": 0.0
                    }
        
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error collecting data from {api_config['name']}: {str(e)}")
            
            return {
                "api_name": api_config["name"],
                "status": "error",
                "response_time": response_time,
                "error": str(e),
                "timestamp": start_time.isoformat(),
                "quality_score": 0.0
            }
    
    def _calculate_quality_score(self, data: Any) -> float:
        """
        计算数据质量评分
        
        Args:
            data: API响应数据
            
        Returns:
            质量评分 (0.0 - 1.0)
        """
        try:
            if not data:
                return 0.0
            
            score = 1.0
            
            # 检查数据完整性
            if isinstance(data, dict):
                if not data:
                    score -= 0.5
                else:
                    # 检查是否有空值
                    empty_values = sum(1 for v in data.values() if v is None or v == "")
                    if empty_values > 0:
                        score -= (empty_values / len(data)) * 0.3
            
            elif isinstance(data, list):
                if not data:
                    score -= 0.5
                else:
                    # 检查列表中的空值
                    empty_items = sum(1 for item in data if not item)
                    if empty_items > 0:
                        score -= (empty_items / len(data)) * 0.3
            
            return max(0.0, min(1.0, score))
            
        except Exception:
            return 0.0
    
    async def collect_all_apis(self) -> List[Dict[str, Any]]:
        """
        收集所有启用的API数据
        
        Returns:
            所有API的收集结果
        """
        await self.start_session()
        
        try:
            results = []
            
            # 并发收集所有API数据
            tasks = [
                self.collect_api_data(api_config) 
                for api_config in self.apis_config 
                if api_config.get("enabled", False)
            ]
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 过滤异常结果
                results = [r for r in results if isinstance(r, dict)]
            
            return results
            
        finally:
            await self.close_session()
    
    async def push_metrics_to_prometheus(self, results: List[Dict[str, Any]]) -> bool:
        """
        将收集的数据推送到Prometheus
        
        Args:
            results: 收集到的数据结果
            
        Returns:
            是否推送成功
        """
        try:
            success_count = 0
            
            for result in results:
                if result.get("status") == "success":
                    # 推送到Pushgateway
                    job_name = f"third_party_{result['api_name']}"
                    success = await pushgateway_service.push_third_party_data(
                        job_name=job_name,
                        api_name=result['api_name'],
                        response_data=result
                    )
                    
                    if success:
                        success_count += 1
                        logger.info(f"Metrics pushed for {result['api_name']}")
                    else:
                        logger.error(f"Failed to push metrics for {result['api_name']}")
            
            logger.info(f"Successfully pushed metrics for {success_count}/{len(results)} APIs")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error pushing metrics to Prometheus: {str(e)}")
            return False


# 创建收集器实例
collector = ThirdPartyAPICollector()


async def collect_third_party_metrics_task(ctx: Dict[str, Any]) -> str:
    """
    定时任务：收集第三方API数据并推送到Prometheus
    
    Args:
        ctx: ARQ上下文
        
    Returns:
        任务执行结果
    """
    logger.info("Starting third party metrics collection task")
    
    try:
        # 收集所有API数据
        results = await collector.collect_all_apis()
        
        if not results:
            logger.warning("No API data collected")
            return "No API data collected"
        
        # 推送到Prometheus
        success = await collector.push_metrics_to_prometheus(results)
        
        if success:
            logger.info("Third party metrics collection completed successfully")
            return f"Successfully collected and pushed metrics for {len(results)} APIs"
        else:
            logger.error("Failed to push metrics to Prometheus")
            return "Failed to push metrics to Prometheus"
    
    except Exception as e:
        logger.error(f"Error in third party metrics collection task: {str(e)}")
        return f"Error: {str(e)}"


async def collect_specific_api_task(ctx: Dict[str, Any], api_name: str) -> str:
    """
    收集特定API的数据
    
    Args:
        ctx: ARQ上下文
        api_name: API名称
        
    Returns:
        任务执行结果
    """
    logger.info(f"Starting collection for specific API: {api_name}")
    
    try:
        # 查找API配置
        api_config = None
        for config in collector.apis_config:
            if config["name"] == api_name:
                api_config = config
                break
        
        if not api_config:
            logger.error(f"API configuration not found for: {api_name}")
            return f"API configuration not found for: {api_name}"
        
        # 收集数据
        await collector.start_session()
        result = await collector.collect_api_data(api_config)
        await collector.close_session()
        
        if result.get("status") == "success":
            # 推送到Prometheus
            success = await collector.push_metrics_to_prometheus([result])
            
            if success:
                logger.info(f"Successfully collected and pushed metrics for {api_name}")
                return f"Successfully collected and pushed metrics for {api_name}"
            else:
                logger.error(f"Failed to push metrics for {api_name}")
                return f"Failed to push metrics for {api_name}"
        else:
            logger.error(f"Failed to collect data for {api_name}: {result.get('error', 'Unknown error')}")
            return f"Failed to collect data for {api_name}: {result.get('error', 'Unknown error')}"
    
    except Exception as e:
        logger.error(f"Error collecting data for {api_name}: {str(e)}")
        return f"Error: {str(e)}"