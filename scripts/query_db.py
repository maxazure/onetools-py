#!/usr/bin/env python3
"""
直接查询数据库内容
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_sqlite_manager
from app.core.config import settings
from sqlalchemy import text

async def query_database():
    """查询数据库内容"""
    sqlite_manager = get_sqlite_manager()
    
    print("Querying database...")
    print(f"Database path: {settings.database.sqlite_path}")
    print(f"Database connection string: {settings.database.sqlite_connection_string}")
    
    try:
        async with sqlite_manager.get_connection() as conn:
            # 查询菜单配置
            result = await conn.execute(text("SELECT * FROM menu_configurations ORDER BY section, \"order\", id"))
            rows = result.fetchall()
            
            print(f"Found {len(rows)} menu configurations:")
            for row in rows:
                print(f"  {row[0]}: {row[1]} - {row[2]} (section: {row[7]}, order: {row[8]})")
            
            # 查询系统设置
            result = await conn.execute(text("SELECT * FROM system_settings"))
            rows = result.fetchall()
            
            print(f"\nFound {len(rows)} system settings:")
            for row in rows:
                print(f"  {row[1]}: {row[2]}")
    
    except Exception as e:
        print(f"Error querying database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(query_database())