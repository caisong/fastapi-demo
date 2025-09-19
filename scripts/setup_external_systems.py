#!/usr/bin/env python3
"""
外部系统配置设置脚本
用于初始化外部系统配置的示例脚本
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession

# 添加项目根目录到路径
sys.path.insert(0, '/home/caisong/fastapi-demo')

from app.db.database import SessionLocal
from app.services.external_system import external_system_service
from app.schemas.external_system import ExternalSystemCreate


async def setup_external_systems():
    """设置示例外部系统"""
    db: AsyncSession = SessionLocal()
    
    try:
        # 示例1: 配置天气API
        weather_system = ExternalSystemCreate(
            name="weather_api",
            display_name="天气预报API",
            base_url="https://api.openweathermap.org/data/2.5",
            auth_url="/auth/token",
            username="your_weather_api_username",
            password="your_weather_api_password",
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
        try:
            weather_db_system = await external_system_service.create_system(db, system_in=weather_system)
            print(f"✅ 成功创建天气API配置: {weather_db_system.name}")
        except Exception as e:
            print(f"❌ 创建天气API配置失败: {str(e)}")
        
        # 示例2: 配置支付系统
        payment_system = ExternalSystemCreate(
            name="payment_gateway",
            display_name="支付网关",
            base_url="https://api.payment-gateway.com",
            auth_url="/api/v1/auth/login",
            username="your_payment_username",
            password="your_payment_password",
            auth_type="username_password",
            session_timeout=1800,  # 30分钟
            max_retry_count=2,
            is_active=True,
            extra_config={
                "merchant_id": "your_merchant_id",
                "currency": "CNY"
            }
        )
        
        # 创建支付系统配置
        try:
            payment_db_system = await external_system_service.create_system(db, system_in=payment_system)
            print(f"✅ 成功创建支付系统配置: {payment_db_system.name}")
        except Exception as e:
            print(f"❌ 创建支付系统配置失败: {str(e)}")
        
        # 示例3: 配置用户管理系统
        user_system = ExternalSystemCreate(
            name="user_management",
            display_name="用户管理系统",
            base_url="https://api.user-management.com",
            auth_url="/auth/login",
            username="your_user_mgmt_username",
            password="your_user_mgmt_password",
            auth_type="username_password",
            session_timeout=3600,  # 1小时
            max_retry_count=3,
            is_active=True,
            extra_config={
                "client_id": "your_client_id",
                "client_secret": "your_client_secret"
            }
        )
        
        # 创建用户管理系统配置
        try:
            user_db_system = await external_system_service.create_system(db, system_in=user_system)
            print(f"✅ 成功创建用户管理系统配置: {user_db_system.name}")
        except Exception as e:
            print(f"❌ 创建用户管理系统配置失败: {str(e)}")
        
        # 显示所有已配置的系统
        print("\n📋 当前配置的外部系统:")
        systems = await external_system_service.get_systems(db)
        for system in systems:
            print(f"  - {system.name} ({system.display_name}) - 状态: {system.auth_status}")
        
    except Exception as e:
        print(f"❌ 设置外部系统时发生错误: {str(e)}")
    finally:
        await db.close()


async def authenticate_all_systems():
    """认证所有外部系统"""
    db: AsyncSession = SessionLocal()
    
    try:
        print("\n🔐 开始认证所有外部系统...")
        result = await external_system_service.authenticate_all_systems(db)
        
        print(f"📊 认证结果: {result.success_count}/{result.total_systems} 个系统认证成功")
        for auth_result in result.results:
            status = "✅" if auth_result.success else "❌"
            print(f"  {status} {auth_result.system_name}: {auth_result.message}")
            
    except Exception as e:
        print(f"❌ 认证外部系统时发生错误: {str(e)}")
    finally:
        await db.close()


async def main():
    """主函数"""
    print("🚀 开始设置外部系统配置...")
    
    # 设置外部系统
    await setup_external_systems()
    
    # 认证所有系统
    await authenticate_all_systems()
    
    print("\n✨ 外部系统配置设置完成!")


if __name__ == "__main__":
    asyncio.run(main())