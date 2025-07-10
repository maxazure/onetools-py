#!/usr/bin/env python3
"""
直接测试ConfigService的异步方法
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.config_service import get_config_service

async def test_async_config():
    """测试异步配置服务"""
    print("Testing async ConfigService...")
    
    config_service = get_config_service()
    
    try:
        # 直接调用异步方法
        menu_configs = await config_service._get_menu_configurations_async()
        print(f"Got {len(menu_configs)} menu configurations from async method:")
        for config in menu_configs:
            print(f"  - {config.key}: {config.label} ({config.section})")
    
    except Exception as e:
        print(f"Error in async method: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_async_config())