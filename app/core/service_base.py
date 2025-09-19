"""
Base service class for all services
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from .logging import LoggerMixin
from .dependency_injection import Injectable
from .exceptions import NotFoundError, ValidationError, DatabaseError

T = TypeVar('T', bound=DeclarativeBase)


class BaseService(ABC, LoggerMixin, Injectable):
    """Base service class for all services"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        super().__init__()
    
    @abstractmethod
    async def get_by_id(self, id: Any) -> Optional[T]:
        """Get entity by ID"""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities"""
        pass
    
    @abstractmethod
    async def create(self, obj_in: Dict[str, Any]) -> T:
        """Create new entity"""
        pass
    
    @abstractmethod
    async def update(self, id: Any, obj_in: Dict[str, Any]) -> Optional[T]:
        """Update entity"""
        pass
    
    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """Delete entity"""
        pass
    
    async def exists(self, id: Any) -> bool:
        """Check if entity exists"""
        entity = await self.get_by_id(id)
        return entity is not None
    
    async def count(self) -> int:
        """Count total entities"""
        # This should be implemented by subclasses
        raise NotImplementedError


class CRUDService(BaseService, Generic[T]):
    """CRUD service with common operations"""
    
    def __init__(self, db: AsyncSession, model: Type[T]):
        super().__init__(db)
        self.model = model
    
    async def get_by_id(self, id: Any) -> Optional[T]:
        """Get entity by ID"""
        try:
            result = await self.db.get(self.model, id)
            return result
        except Exception as e:
            self.logger.error(f"Error getting {self.model.__name__} by ID {id}: {str(e)}")
            raise DatabaseError(f"Failed to get {self.model.__name__} by ID")
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities"""
        try:
            from sqlalchemy import select
            stmt = select(self.model).offset(skip).limit(limit)
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            self.logger.error(f"Error getting all {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to get all {self.model.__name__}")
    
    async def create(self, obj_in: Dict[str, Any]) -> T:
        """Create new entity"""
        try:
            db_obj = self.model(**obj_in)
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
            return db_obj
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to create {self.model.__name__}")
    
    async def update(self, id: Any, obj_in: Dict[str, Any]) -> Optional[T]:
        """Update entity"""
        try:
            db_obj = await self.get_by_id(id)
            if not db_obj:
                raise NotFoundError(f"{self.model.__name__} not found")
            
            for field, value in obj_in.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            await self.db.commit()
            await self.db.refresh(db_obj)
            return db_obj
        except NotFoundError:
            raise
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Error updating {self.model.__name__} {id}: {str(e)}")
            raise DatabaseError(f"Failed to update {self.model.__name__}")
    
    async def delete(self, id: Any) -> bool:
        """Delete entity"""
        try:
            db_obj = await self.get_by_id(id)
            if not db_obj:
                raise NotFoundError(f"{self.model.__name__} not found")
            
            await self.db.delete(db_obj)
            await self.db.commit()
            return True
        except NotFoundError:
            raise
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Error deleting {self.model.__name__} {id}: {str(e)}")
            raise DatabaseError(f"Failed to delete {self.model.__name__}")
    
    async def count(self) -> int:
        """Count total entities"""
        try:
            from sqlalchemy import select, func
            stmt = select(func.count(self.model.id))
            result = await self.db.execute(stmt)
            return result.scalar()
        except Exception as e:
            self.logger.error(f"Error counting {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Failed to count {self.model.__name__}")
    
    async def get_by_field(self, field: str, value: Any) -> Optional[T]:
        """Get entity by field value"""
        try:
            from sqlalchemy import select
            stmt = select(self.model).where(getattr(self.model, field) == value)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Error getting {self.model.__name__} by {field}: {str(e)}")
            raise DatabaseError(f"Failed to get {self.model.__name__} by {field}")
    
    async def get_many_by_field(self, field: str, value: Any, skip: int = 0, limit: int = 100) -> List[T]:
        """Get entities by field value"""
        try:
            from sqlalchemy import select
            stmt = select(self.model).where(getattr(self.model, field) == value).offset(skip).limit(limit)
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            self.logger.error(f"Error getting {self.model.__name__} by {field}: {str(e)}")
            raise DatabaseError(f"Failed to get {self.model.__name__} by {field}")


class CacheService(LoggerMixin, Injectable):
    """Base cache service"""
    
    def __init__(self):
        super().__init__()
        self.cache: Dict[str, Any] = {}
        self.ttl: Dict[str, float] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            # Check TTL
            if key in self.ttl and self.ttl[key] < self._current_time():
                self.delete(key)
                return None
            return self.cache[key]
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in cache"""
        self.cache[key] = value
        self.ttl[key] = self._current_time() + ttl
    
    async def delete(self, key: str) -> None:
        """Delete value from cache"""
        self.cache.pop(key, None)
        self.ttl.pop(key, None)
    
    async def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()
        self.ttl.clear()
    
    def _current_time(self) -> float:
        """Get current time"""
        import time
        return time.time()


class ExternalAPIService(LoggerMixin, Injectable):
    """Base service for external API calls"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        super().__init__()
        self.base_url = base_url.rstrip('/')  # 移除末尾的斜杠
        self.timeout = timeout
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request"""
        import aiohttp
        import time
        
        # 构建完整URL
        url = f"{self.base_url}{endpoint}" if not endpoint.startswith('http') else endpoint
        
        # 合并默认头和自定义头
        default_headers = {
            "Content-Type": "application/json",
            "User-Agent": "FastAPI-External-Client/1.0"
        }
        if headers:
            default_headers.update(headers)
        
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # 根据方法选择适当的请求
                if method.upper() == "GET":
                    async with session.get(url, params=params, headers=default_headers) as response:
                        response.raise_for_status()
                        result = await response.json()
                elif method.upper() == "POST":
                    async with session.post(url, params=params, json=data, headers=default_headers) as response:
                        response.raise_for_status()
                        result = await response.json()
                elif method.upper() == "PUT":
                    async with session.put(url, params=params, json=data, headers=default_headers) as response:
                        response.raise_for_status()
                        result = await response.json()
                elif method.upper() == "DELETE":
                    async with session.delete(url, params=params, headers=default_headers) as response:
                        response.raise_for_status()
                        result = await response.json()
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response_time = (time.time() - start_time) * 1000  # 转换为毫秒
                self.logger.info(f"{method} {url} - {response.status} - {response_time:.2f}ms")
                
                return {
                    "status_code": response.status,
                    "data": result,
                    "response_time": response_time,
                    "headers": dict(response.headers)
                }
                
        except aiohttp.ClientResponseError as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"{method} {url} - {e.status} - {response_time:.2f}ms - {str(e)}")
            raise Exception(f"HTTP {e.status}: {e.message}")
        except aiohttp.ClientError as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"{method} {url} - ERROR - {response_time:.2f}ms - {str(e)}")
            raise Exception(f"Client error: {str(e)}")
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"{method} {url} - ERROR - {response_time:.2f}ms - {str(e)}")
            raise
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make GET request"""
        return await self._make_request("GET", endpoint, params=params, headers=headers)
    
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make POST request"""
        return await self._make_request("POST", endpoint, data=data, headers=headers)
    
    async def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make PUT request"""
        return await self._make_request("PUT", endpoint, data=data, headers=headers)
    
    async def delete(self, endpoint: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make DELETE request"""
        return await self._make_request("DELETE", endpoint, headers=headers)
