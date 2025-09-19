#!/usr/bin/env python3
"""
业务服务中使用外部系统认证的示例
演示如何在业务逻辑中直接使用外部系统服务，而不是通过API端点
"""
import asyncio
import sys
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, '/home/caisong/fastapi-demo')

from app.db.database import SessionLocal
from app.services.external_system import external_system_service
from app.schemas.external_system import ExternalSystemCreate


class WeatherService:
    """天气服务示例"""
    
    def __init__(self):
        self.db = None
    
    async def __aenter__(self):
        self.db = SessionLocal()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            await self.db.close()
    
    async def get_weather_forecast(self, city: str = "Beijing") -> Dict[str, Any]:
        """获取天气预报"""
        try:
            # 直接调用外部系统API，无需通过API端点
            response = await external_system_service.call_external_api(
                self.db,
                system_name="weather_api",
                method="GET",
                endpoint="/forecast",
                params={"city": city, "units": "metric"}
            )
            
            return {
                "city": city,
                "forecast": response.get("data", {}),
                "status_code": response.get("status_code"),
                "response_time": response.get("response_time")
            }
            
        except Exception as e:
            # 处理调用失败的情况
            return {
                "city": city,
                "error": f"获取天气预报失败: {str(e)}",
                "status_code": 500
            }
    
    async def get_current_weather(self, city: str = "Beijing") -> Dict[str, Any]:
        """获取当前天气"""
        try:
            # 直接调用外部系统API
            response = await external_system_service.call_external_api(
                self.db,
                system_name="weather_api",
                method="GET",
                endpoint="/weather",
                params={"city": city, "units": "metric"}
            )
            
            return {
                "city": city,
                "current": response.get("data", {}),
                "status_code": response.get("status_code"),
                "response_time": response.get("response_time")
            }
            
        except Exception as e:
            return {
                "city": city,
                "error": f"获取当前天气失败: {str(e)}",
                "status_code": 500
            }


class PaymentService:
    """支付服务示例"""
    
    def __init__(self):
        self.db = None
    
    async def __aenter__(self):
        self.db = SessionLocal()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            await self.db.close()
    
    async def process_payment(self, amount: float, currency: str = "CNY") -> Dict[str, Any]:
        """处理支付"""
        try:
            # 直接调用支付网关API
            response = await external_system_service.call_external_api(
                self.db,
                system_name="payment_gateway",
                method="POST",
                endpoint="/payments",
                data={
                    "amount": amount,
                    "currency": currency,
                    "description": "商品购买"
                }
            )
            
            return {
                "success": response.get("status_code") == 200,
                "payment_id": response.get("data", {}).get("payment_id"),
                "status_code": response.get("status_code"),
                "response_time": response.get("response_time")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"支付处理失败: {str(e)}",
                "status_code": 500
            }


async def setup_example_systems():
    """设置示例外部系统"""
    db = SessionLocal()
    
    try:
        print("🚀 设置示例外部系统...")
        
        # 天气API系统
        weather_system = ExternalSystemCreate(
            name="weather_api",
            display_name="天气预报API",
            base_url="https://api.openweathermap.org/data/2.5",
            auth_url="/auth/token",
            username="weather_user",
            password="weather_password_123",
            auth_type="username_password",
            session_timeout=7200,
            max_retry_count=3,
            is_active=True,
            extra_config={"api_key": "your_openweather_api_key"}
        )
        
        weather_db_system = await external_system_service.create_system(db, system_in=weather_system)
        print(f"✅ 成功创建天气API配置: {weather_db_system.name}")
        
        # 支付系统
        payment_system = ExternalSystemCreate(
            name="payment_gateway",
            display_name="支付网关",
            base_url="https://api.payment-gateway.com",
            auth_url="/api/v1/auth/login",
            username="payment_user",
            password="payment_password_123",
            auth_type="username_password",
            session_timeout=1800,
            max_retry_count=2,
            is_active=True,
            extra_config={"merchant_id": "merchant_12345"}
        )
        
        payment_db_system = await external_system_service.create_system(db, system_in=payment_system)
        print(f"✅ 成功创建支付系统配置: {payment_db_system.name}")
        
        # 认证所有系统
        print("🔐 认证所有外部系统...")
        batch_result = await external_system_service.authenticate_all_systems(db)
        print(f"📊 认证结果: {batch_result.success_count}/{batch_result.total_systems} 个系统认证成功")
        
        return [weather_db_system, payment_db_system]
        
    except Exception as e:
        print(f"❌ 设置外部系统时发生错误: {str(e)}")
        raise
    finally:
        await db.close()


async def demonstrate_business_usage():
    """演示在业务服务中使用外部系统"""
    print("\n💼 演示在业务服务中使用外部系统...")
    
    # 使用天气服务
    print("\n🌤️  使用天气服务...")
    async with WeatherService() as weather_service:
        # 获取北京天气预报
        forecast = await weather_service.get_weather_forecast("Beijing")
        print(f"  北京天气预报: {forecast}")
        
        # 获取上海当前天气
        current = await weather_service.get_current_weather("Shanghai")
        print(f"  上海当前天气: {current}")
    
    # 使用支付服务
    print("\n💳 使用支付服务...")
    async with PaymentService() as payment_service:
        # 处理支付
        payment_result = await payment_service.process_payment(99.99, "CNY")
        print(f"  支付处理结果: {payment_result}")


async def check_system_status():
    """检查系统状态"""
    db = SessionLocal()
    
    try:
        print("\n📋 检查外部系统状态...")
        statuses = await external_system_service.get_all_systems_status(db)
        for status in statuses:
            session_status = "有效" if status.is_session_valid else "无效"
            print(f"  {status.system_name}: {status.status} (会话{session_status})")
    except Exception as e:
        print(f"❌ 检查系统状态时发生错误: {str(e)}")
    finally:
        await db.close()


async def main():
    """主函数"""
    print("🚀 外部系统在业务服务中的使用示例")
    print("=" * 50)
    
    try:
        # 1. 设置示例外部系统
        systems = await setup_example_systems()
        
        # 2. 演示在业务服务中使用
        await demonstrate_business_usage()
        
        # 3. 检查系统状态
        await check_system_status()
        
        print("\n✨ 示例程序执行完成!")
        print("\n📝 关键优势:")
        print("  1. 业务逻辑直接调用服务方法，无需通过API端点")
        print("  2. 自动处理认证和会话管理")
        print("  3. 统一的错误处理和日志记录")
        print("  4. 透明的重试机制")
        
    except Exception as e:
        print(f"\n❌ 示例程序执行失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())