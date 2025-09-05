"""
Dependency injection system
"""
from typing import Any, Dict, Type, TypeVar, Optional, Callable, Union
from functools import wraps
import inspect
from abc import ABC, abstractmethod

from .logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class ServiceContainer:
    """Service container for dependency injection"""
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._singletons: Dict[Type, Any] = {}
        self._transients: Dict[Type, Type] = {}
        self.logger = get_logger("service_container")
    
    def register_singleton(self, service_type: Type[T], instance: T) -> None:
        """Register singleton instance"""
        self._services[service_type] = instance
        self._singletons[service_type] = instance
        self.logger.debug(f"Registered singleton: {service_type.__name__}")
    
    def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """Register factory function"""
        self._factories[service_type] = factory
        self.logger.debug(f"Registered factory: {service_type.__name__}")
    
    def register_transient(self, service_type: Type[T], implementation: Type[T]) -> None:
        """Register transient service"""
        self._transients[service_type] = implementation
        self.logger.debug(f"Registered transient: {service_type.__name__}")
    
    def get(self, service_type: Type[T]) -> T:
        """Get service instance"""
        # Check singletons first
        if service_type in self._singletons:
            return self._singletons[service_type]
        
        # Check factories
        if service_type in self._factories:
            instance = self._factories[service_type]()
            self._singletons[service_type] = instance
            return instance
        
        # Check transients
        if service_type in self._transients:
            implementation = self._transients[service_type]
            instance = self._create_instance(implementation)
            return instance
        
        # Check if service type is instantiable
        try:
            instance = self._create_instance(service_type)
            self._singletons[service_type] = instance
            return instance
        except Exception as e:
            self.logger.error(f"Failed to create instance of {service_type.__name__}: {str(e)}")
            raise ValueError(f"Service {service_type.__name__} not registered")
    
    def _create_instance(self, service_type: Type[T]) -> T:
        """Create instance with dependency injection"""
        constructor = service_type.__init__
        sig = inspect.signature(constructor)
        
        # Get parameters
        params = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            param_type = param.annotation
            if param_type == inspect.Parameter.empty:
                continue
            
            # Try to resolve dependency
            try:
                params[param_name] = self.get(param_type)
            except ValueError:
                if param.default != inspect.Parameter.empty:
                    continue
                raise ValueError(f"Cannot resolve dependency {param_name} of type {param_type}")
        
        return service_type(**params)
    
    def is_registered(self, service_type: Type) -> bool:
        """Check if service is registered"""
        return (service_type in self._services or 
                service_type in self._factories or 
                service_type in self._transients)
    
    def clear(self) -> None:
        """Clear all services"""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        self._transients.clear()
        self.logger.info("Cleared all services")


class ServiceProvider:
    """Service provider interface"""
    
    def __init__(self, container: ServiceContainer):
        self.container = container
    
    def get_service(self, service_type: Type[T]) -> T:
        """Get service from container"""
        return self.container.get(service_type)


class Injectable:
    """Mixin for injectable services"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._container: Optional[ServiceContainer] = None
    
    def set_container(self, container: ServiceContainer) -> None:
        """Set service container"""
        self._container = container
    
    def get_service(self, service_type: Type[T]) -> T:
        """Get service from container"""
        if not self._container:
            raise ValueError("Service container not set")
        return self._container.get(service_type)


def injectable(cls: Type[T]) -> Type[T]:
    """Decorator for injectable classes"""
    original_init = cls.__init__
    
    @wraps(original_init)
    def new_init(self, *args, **kwargs):
        # Get service container from global registry
        container = get_container()
        if container:
            self.set_container(container)
        original_init(self, *args, **kwargs)
    
    cls.__init__ = new_init
    cls.set_container = Injectable.set_container
    cls.get_service = Injectable.get_service
    return cls


def inject(service_type: Type[T]) -> T:
    """Inject service dependency"""
    container = get_container()
    if not container:
        raise ValueError("Service container not available")
    return container.get(service_type)


# Global service container
_container: Optional[ServiceContainer] = None


def get_container() -> Optional[ServiceContainer]:
    """Get global service container"""
    return _container


def set_container(container: ServiceContainer) -> None:
    """Set global service container"""
    global _container
    _container = container


def create_container() -> ServiceContainer:
    """Create new service container"""
    return ServiceContainer()


def register_service(service_type: Type[T], instance: T) -> None:
    """Register service instance"""
    if not _container:
        raise ValueError("Service container not initialized")
    _container.register_singleton(service_type, instance)


def register_factory(service_type: Type[T], factory: Callable[[], T]) -> None:
    """Register service factory"""
    if not _container:
        raise ValueError("Service container not initialized")
    _container.register_factory(service_type, factory)


def register_transient(service_type: Type[T], implementation: Type[T]) -> None:
    """Register transient service"""
    if not _container:
        raise ValueError("Service container not initialized")
    _container.register_transient(service_type, implementation)


def get_service(service_type: Type[T]) -> T:
    """Get service instance"""
    if not _container:
        raise ValueError("Service container not initialized")
    return _container.get(service_type)


def dependency(service_type: Type[T]) -> T:
    """Dependency injection decorator"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Inject service if not provided
            if service_type not in kwargs:
                kwargs[service_type.__name__.lower()] = get_service(service_type)
            return func(*args, **kwargs)
        return wrapper
    return decorator


class ServiceRegistry:
    """Service registry for managing service lifecycle"""
    
    def __init__(self):
        self.container = create_container()
        set_container(self.container)
        self.logger = get_logger("service_registry")
    
    def register_services(self) -> None:
        """Register all application services"""
        # This method should be overridden to register specific services
        pass
    
    def initialize_services(self) -> None:
        """Initialize all services"""
        self.register_services()
        self.logger.info("Initialized service registry")
    
    def cleanup_services(self) -> None:
        """Cleanup all services"""
        self.container.clear()
        self.logger.info("Cleaned up service registry")


# Global service registry
service_registry = ServiceRegistry()


def init_dependency_injection() -> None:
    """Initialize dependency injection system"""
    service_registry.initialize_services()


def cleanup_dependency_injection() -> None:
    """Cleanup dependency injection system"""
    service_registry.cleanup_services()