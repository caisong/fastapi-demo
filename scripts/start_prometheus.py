#!/usr/bin/env python3
"""
Prometheus metrics scraper and server
This script provides a dedicated metrics endpoint that can scrape metrics from the main app
"""
import sys
import os
import time
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for Prometheus metrics"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/metrics':
            try:
                # Try to get metrics from the main FastAPI application
                main_app_url = f"http://localhost:{settings.PORT}/metrics"
                response = requests.get(main_app_url, timeout=5)
                
                if response.status_code == 200:
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
                    self.send_header('Content-Length', str(len(response.content)))
                    self.end_headers()
                    self.wfile.write(response.content)
                else:
                    self.send_error(502, f"Failed to get metrics from main app: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.send_error(503, f"Error connecting to main app: {str(e)}")
            except Exception as e:
                self.send_error(500, f"Error generating metrics: {str(e)}")
                
        elif self.path == '/health':
            # Health check endpoint
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "healthy", "service": "prometheus-proxy"}')
        else:
            self.send_error(404, "Not Found")
    
    def log_message(self, format, *args):
        """Log messages with timestamp"""
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Prometheus: {format % args}")


def start_prometheus_server():
    """Start the Prometheus metrics proxy server"""
    try:
        port = int(getattr(settings, 'PROMETHEUS_PORT', 9090))
        print(f"Starting Prometheus metrics proxy server on port {port}...")
        print(f"Proxying metrics from http://localhost:{settings.PORT}/metrics")
        
        server = HTTPServer(('', port), MetricsHandler)
        print(f"Prometheus metrics server running at http://0.0.0.0:{port}/metrics")
        print(f"Health check available at http://0.0.0.0:{port}/health")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nPrometheus metrics server stopped.")
    except Exception as e:
        print(f"Error starting Prometheus server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    start_prometheus_server()