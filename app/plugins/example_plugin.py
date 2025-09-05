"""
Example plugin demonstrating the plugin system
"""
from typing import Any, Dict
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from app.core.plugins import RoutePlugin, MiddlewarePlugin, ServicePlugin
from app.core.logging import get_logger

logger = get_logger(__name__)


class ExampleRoutePlugin(RoutePlugin):
    """Example route plugin"""
    
    def __init__(self):
        super().__init__("example_routes", "1.0.0")
    
    def create_router(self) -> APIRouter:
        """Create example routes"""
        router = APIRouter(prefix="/example", tags=["example"])
        
        @router.get("/")
        async def example_root():
            """Example root endpoint"""
            return {"message": "Hello from example plugin!", "plugin": self.name}
        
        @router.get("/info")
        async def example_info():
            """Example info endpoint"""
            return {
                "plugin_name": self.name,
                "version": self.version,
                "enabled": self.enabled
            }
        
        return router


class ExampleMiddlewarePlugin(MiddlewarePlugin):
    """Example middleware plugin"""
    
    def __init__(self):
        super().__init__("example_middleware", "1.0.0")
    
    def create_middleware(self):
        """Create example middleware"""
        async def example_middleware(request: Request, call_next):
            # Add custom header
            response = await call_next(request)
            response.headers["X-Example-Plugin"] = "enabled"
            return response
        
        return example_middleware


class ExampleServicePlugin(ServicePlugin):
    """Example service plugin"""
    
    def __init__(self):
        super().__init__("example_service", "1.0.0")
        self.data: Dict[str, Any] = {}
    
    def create_service(self) -> Any:
        """Create example service"""
        class ExampleService:
            def __init__(self):
                self.data = {}
            
            def set_data(self, key: str, value: Any) -> None:
                """Set data"""
                self.data[key] = value
                logger.info(f"Set data: {key} = {value}")
            
            def get_data(self, key: str) -> Any:
                """Get data"""
                return self.data.get(key)
            
            def get_all_data(self) -> Dict[str, Any]:
                """Get all data"""
                return self.data.copy()
        
        return ExampleService()


# Plugin instances
example_route_plugin = ExampleRoutePlugin()
example_middleware_plugin = ExampleMiddlewarePlugin()
example_service_plugin = ExampleServicePlugin()