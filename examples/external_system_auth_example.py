#!/usr/bin/env python3
"""
外部系统认证使用示例
演示如何使用外部系统认证管理模块
"""
import asyncio
import sys
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, '/home/caisong/fastapi-demo')

from app.db.database import SessionLocal
from app.services.external_system import external_system_service
from app.schemas.external_system import ExternalSystemCreate


async def setup_example_systems():
    """设置示例外部系统"""
    db = SessionLocal()
    
    try:
        print("🚀 设置示例外部系统...")
        
        # 示例1: 天气API系统
        weather_system = ExternalSystemCreate(
            name="weather_api",
            display_name="天气预报API",
            base_url="https://api.openweathermap.org/data/2.5",
            auth_url="/auth/token",  # 假设的认证端点
            username="weather_user",
            password="weather_password_123",
            auth_type="username_password",
            session_timeout=7200,  # 2小时
            max_retry_count=3,
            is_active=True,
            extra_config={
                "api_key": "your_openweather_api_key",
                "default_city": "Beijing"
            }
        )
        
        # 创建天气API配置
        weather_db_system = await external_system_service.create_system(db, system_in=weather_system)
        print(f"✅ 成功创建天气API配置: {weather_db_system.name}")
        
        # 示例2: 支付系统
        payment_system = ExternalSystemCreate(
            name="payment_gateway",
            display_name="支付网关",
            base_url="https://api.payment-gateway.com",
            auth_url="/api/v1/auth/login",
            username="payment_user",
            password="payment_password_123",
            auth_type="username_password",
            session_timeout=1800,  # 30分钟
            max_retry_count=2,
            is_active=True,
            extra_config={
                "merchant_id": "merchant_12345",
                "currency": "CNY"
            }
        )
        
        # 创建支付系统配置
        payment_db_system = await external_system_service.create_system(db, system_in=payment_system)
        print(f"✅ 成功创建支付系统配置: {payment_db_system.name}")
        
        return [weather_db_system, payment_db_system]
        
    except Exception as e:
        print(f"❌ 设置外部系统时发生错误: {str(e)}")
        raise
    finally:
        await db.close()


async def demonstrate_authentication():
    """演示外部系统认证"""
    db = SessionLocal()
    
    try:
        print("\n🔐 演示外部系统认证...")
        
        # 认证单个系统
        print("  认证天气API系统...")
        weather_auth_result = await external_system_service.authenticate_system(db, system_name="weather_api")
        print(f"    天气API认证结果: {'✅ 成功' if weather_auth_result.success else '❌ 失败'} - {weather_auth_result.message}")
        
        # 认证所有系统
        print("  批量认证所有系统...")
        batch_result = await external_system_service.authenticate_all_systems(db)
        print(f"    批量认证结果: {batch_result.success_count}/{batch_result.total_systems} 个系统认证成功")
        
        for result in batch_result.results:
            status = "✅" if result.success else "❌"
            print(f"    {status} {result.system_name}: {result.message}")
            
    except Exception as e:
        print(f"❌ 认证外部系统时发生错误: {str(e)}")
        raise
    finally:
        await db.close()


async def demonstrate_status_check():
    """演示系统状态检查"""
    db = SessionLocal()
    
    try:
        print("\n📋 演示系统状态检查...")
        
        # 检查单个系统状态
        weather_status = await external_system_service.get_system_status(db, system_name="weather_api")
        if weather_status:
            print(f"  天气API状态: {weather_status.status}")
            print(f"  会话有效: {'是' if weather_status.is_session_valid else '否'}")
            if weather_status.last_error:
                print(f"  最后错误: {weather_status.last_error}")
        
        # 检查所有系统状态
        print("  所有系统状态:")
        all_statuses = await external_system_service.get_all_systems_status(db)
        for status in all_statuses:
            session_status = "有效" if status.is_session_valid else "无效"
            print(f"    {status.system_name}: {status.status} (会话{session_status})")
            
    except Exception as e:
        print(f"❌ 检查系统状态时发生错误: {str(e)}")
        raise
    finally:
        await db.close()


async def demonstrate_api_call():
    """演示调用外部系统API"""
    db = SessionLocal()
    
    try:
        print("\n🌐 演示调用外部系统API...")
        
        # 模拟调用天气API获取数据
        print("  调用天气API获取北京天气...")
        try:
            # 注意：这会失败，因为我们没有真实的API端点
            # 但在实际应用中，这会成功调用外部API
            response = await external_system_service.call_external_api(
                db,
                system_name="weather_api",
                method="GET",
                endpoint="/weather",
                params={"q": "Beijing", "appid": "your_api_key"}
            )
            print(f"    API调用成功: {response}")
        except Exception as e:
            print(f"    API调用模拟结果: {str(e)} (这是预期的，因为我们没有真实的API)")
            
    except Exception as e:
        print(f"❌ 调用外部API时发生错误: {str(e)}")
        raise
    finally:
        await db.close()


async def main():
    """主函数"""
    print("🚀 外部系统认证管理示例程序")
    print("=" * 50)
    
    try:
        # 1. 设置示例外部系统
        systems = await setup_example_systems()
        
        # 2. 演示认证功能
        await demonstrate_authentication()
        
        # 3. 演示状态检查
        await demonstrate_status_check()
        
        # 4. 演示API调用
        await demonstrate_api_call()
        
        print("\n✨ 示例程序执行完成!")
        print("\n📝 下一步建议:")
        print("  1. 查看文档: docs/EXTERNAL_SYSTEM_AUTH.md")
        print("  2. 运行测试: python -m pytest tests/test_external_system.py")
        print("  3. 使用API: 访问 /docs 查看API文档")
        
    except Exception as e:
        print(f"\n❌ 示例程序执行失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())