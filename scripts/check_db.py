#!/usr/bin/env python3
"""
Check PostgreSQL database connectivity and driver availability
"""
import sys
from typing import Dict, Any

def check_postgresql_driver() -> Dict[str, Any]:
    """Check if PostgreSQL drivers are available"""
    results = {
        "psycopg2": False,
        "psycopg2_binary": False,
        "asyncpg": False,
        "recommendations": []
    }
    
    # Check psycopg2
    try:
        import psycopg2
        results["psycopg2"] = True
        print("✓ psycopg2 is available")
    except ImportError:
        print("✗ psycopg2 is not available")
        results["recommendations"].append("Install psycopg2: pip install psycopg2")
    
    # Check psycopg2-binary
    try:
        import psycopg2
        if hasattr(psycopg2, '__version__'):
            results["psycopg2_binary"] = True
            print("✓ psycopg2-binary is available")
    except ImportError:
        print("✗ psycopg2-binary is not available")
        results["recommendations"].append("Install psycopg2-binary: pip install psycopg2-binary")
    
    # Check asyncpg
    try:
        import asyncpg
        results["asyncpg"] = True
        print("✓ asyncpg is available")
    except ImportError:
        print("✗ asyncpg is not available")
        results["recommendations"].append("Install asyncpg: pip install asyncpg")
    
    return results

def check_database_connectivity():
    """Check PostgreSQL database connectivity"""
    try:
        from app.core.config import settings
        print(f"\nCurrent database URL: {settings.DATABASE_URL}")
        
        if settings.DATABASE_URL.startswith("postgresql"):
            print("Using PostgreSQL database")
            try:
                from app.db.database import engine
                with engine.connect() as conn:
                    print("✓ PostgreSQL connection successful")
                    return True
            except Exception as e:
                print(f"✗ PostgreSQL connection failed: {e}")
                print("Recommendation: Check if PostgreSQL server is running and credentials are correct")
                print(f"Connection details: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}")
                return False
        else:
            print("✗ Database URL is not configured for PostgreSQL")
            return False
        
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

def main():
    """Main check function"""
    print("FastAPI PostgreSQL Database Check")
    print("=" * 40)
    
    print("\n1. Checking PostgreSQL drivers:")
    pg_results = check_postgresql_driver()
    
    print("\n2. Checking database connectivity:")
    conn_ok = check_database_connectivity()
    
    print("\n" + "=" * 40)
    print("Summary:")
    
    if any(pg_results.values()):
        print("✓ PostgreSQL drivers are available")
    else:
        print("✗ No PostgreSQL drivers found")
        print("\nRecommendations:")
        for rec in pg_results["recommendations"]:
            print(f"  - {rec}")
    
    if conn_ok:
        print("✓ Database connection is working")
    else:
        print("✗ Database connection failed")
        print("Check your .env configuration and PostgreSQL server status")

if __name__ == "__main__":
    main()