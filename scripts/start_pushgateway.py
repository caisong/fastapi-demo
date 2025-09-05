#!/usr/bin/env python3
"""
Prometheus Pushgateway Server
接收第三方数据并转换为Prometheus指标格式
"""
import sys
import os
import time
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, generate_latest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings


class PushgatewayHandler(BaseHTTPRequestHandler):
    """Pushgateway HTTP处理器"""
    
    def __init__(self, *args, **kwargs):
        # 存储指标的字典
        self.metrics_store = {}
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/metrics':
            self._handle_metrics()
        elif parsed_path.path == '/health':
            self._handle_health()
        elif parsed_path.path == '/status':
            self._handle_status()
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """处理POST请求 - 接收推送的指标"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path.startswith('/metrics/job/'):
            self._handle_push_metrics(parsed_path)
        else:
            self.send_error(404, "Not Found")
    
    def _handle_metrics(self):
        """处理/metrics端点"""
        try:
            # 生成Prometheus格式的指标
            registry = CollectorRegistry()
            
            # 从存储中恢复指标
            for job_name, job_metrics in self.metrics_store.items():
                for metric_name, metric_data in job_metrics.items():
                    if metric_name.startswith('counter_'):
                        counter = Counter(
                            metric_name[8:],  # 移除'counter_'前缀
                            metric_data.get('help', ''),
                            metric_data.get('labels', []),
                            registry=registry
                        )
                        counter._value._value = metric_data.get('value', 0)
                    
                    elif metric_name.startswith('gauge_'):
                        gauge = Gauge(
                            metric_name[6:],  # 移除'gauge_'前缀
                            metric_data.get('help', ''),
                            metric_data.get('labels', []),
                            registry=registry
                        )
                        gauge.set(metric_data.get('value', 0))
                    
                    elif metric_name.startswith('histogram_'):
                        histogram = Histogram(
                            metric_name[10:],  # 移除'histogram_'前缀
                            metric_data.get('help', ''),
                            metric_data.get('labels', []),
                            registry=registry
                        )
                        # 简化处理，只设置总和
                        histogram._sum._value = metric_data.get('sum', 0)
                        histogram._count._value = metric_data.get('count', 0)
            
            # 生成指标内容
            content = generate_latest(registry)
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            self.send_error(500, f"Error generating metrics: {str(e)}")
    
    def _handle_health(self):
        """处理健康检查"""
        response = {
            "status": "healthy",
            "service": "pushgateway",
            "timestamp": time.time(),
            "metrics_count": sum(len(job_metrics) for job_metrics in self.metrics_store.values())
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def _handle_status(self):
        """处理状态查询"""
        status = {
            "jobs": list(self.metrics_store.keys()),
            "total_jobs": len(self.metrics_store),
            "total_metrics": sum(len(job_metrics) for job_metrics in self.metrics_store.values()),
            "timestamp": time.time()
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(status).encode())
    
    def _handle_push_metrics(self, parsed_path):
        """处理推送的指标"""
        try:
            # 解析路径获取job名称
            path_parts = parsed_path.path.split('/')
            if len(path_parts) < 4:
                self.send_error(400, "Invalid path format")
                return
            
            job_name = path_parts[3]
            
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                
                # 解析指标数据
                metrics_data = json.loads(post_data.decode('utf-8'))
                
                # 存储指标
                if job_name not in self.metrics_store:
                    self.metrics_store[job_name] = {}
                
                # 更新指标
                for metric_name, metric_value in metrics_data.items():
                    self.metrics_store[job_name][metric_name] = metric_value
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "message": f"Metrics pushed for job: {job_name}",
                    "metrics_count": len(metrics_data)
                }).encode())
            else:
                self.send_error(400, "No data provided")
        
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON data")
        except Exception as e:
            self.send_error(500, f"Error processing metrics: {str(e)}")
    
    def log_message(self, format, *args):
        """记录日志消息"""
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Pushgateway: {format % args}")


def start_pushgateway_server():
    """启动Pushgateway服务器"""
    try:
        port = int(getattr(settings, 'PUSHGATEWAY_PORT', 9091))
        print(f"Starting Prometheus Pushgateway server on port {port}...")
        print(f"Pushgateway available at http://0.0.0.0:{port}")
        print(f"Health check available at http://0.0.0.0:{port}/health")
        print(f"Status available at http://0.0.0.0:{port}/status")
        print(f"Metrics available at http://0.0.0.0:{port}/metrics")
        
        server = HTTPServer(('', port), PushgatewayHandler)
        server.serve_forever()
    
    except KeyboardInterrupt:
        print("\nPushgateway server stopped.")
    except Exception as e:
        print(f"Error starting Pushgateway server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    start_pushgateway_server()