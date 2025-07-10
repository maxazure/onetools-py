#!/usr/bin/env python3
"""
测试ConfigService的数据库连接和读取
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.config_service import get_config_service

async def test_config_service():
    """测试ConfigService"""
    print("Testing ConfigService...")
    
    config_service = get_config_service()
    
    # 测试数据库连接
    try:
        print("Testing database connection...")
        async with config_service.sqlite.get_connection() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM menu_configurations"))
            count = result.fetchone()[0]
            print(f"Menu configurations count in database: {count}")
    except Exception as e:
        print(f"Database connection error: {e}")
    
    # 测试菜单配置获取
    try:
        print("\nTesting menu configurations...")
        menu_configs = config_service.get_menu_configurations()
        print(f"Got {len(menu_configs)} menu configurations:")
        for config in menu_configs:
            print(f"  - {config.key}: {config.label} ({config.section})")
    except Exception as e:
        print(f"Menu configurations error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from sqlalchemy import text
    asyncio.run(test_config_service())