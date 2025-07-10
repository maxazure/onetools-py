#!/usr/bin/env python3
"""
检查当前菜单配置
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_sqlite_manager
from sqlalchemy import text


async def check_menu_config():
    """检查当前菜单配置"""
    try:
        sqlite_manager = get_sqlite_manager()
        
        print("当前菜单配置:")
        print("=" * 60)
        
        async with sqlite_manager.get_connection() as conn:
            # 检查表是否存在
            result = await conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='menu_configurations'
            """))
            if not result.fetchone():
                print("❌ menu_configurations表不存在")
                return False
            
            # 获取菜单配置
            result = await conn.execute(text("""
                SELECT key, label, path, enabled, section, 'order' as order_col
                FROM menu_configurations 
                ORDER BY section, 'order'
            """))
            
            rows = result.fetchall()
            if not rows:
                print("⚠️  没有找到菜单配置")
                return False
            
            for row in rows:
                key, label, path, enabled, section, order = row
                status = "✅" if enabled else "❌"
                print(f"{status} [{section}] {key} - {label} - {path}")
        
        print("=" * 60)
        print(f"总计: {len(rows)} 个菜单项")
        return True
        
    except Exception as e:
        print(f"❌ 检查菜单配置失败: {e}")
        return False


async def add_query_forms_menu():
    """添加动态查询表单菜单项"""
    try:
        sqlite_manager = get_sqlite_manager()
        
        print("\n正在添加动态查询表单菜单项...")
        
        async with sqlite_manager.get_connection() as conn:
            # 检查是否已存在
            result = await conn.execute(text("""
                SELECT id FROM menu_configurations 
                WHERE key = 'query-forms'
            """))
            if result.fetchone():
                print("✅ 动态查询表单菜单项已存在")
                return True
            
            # 添加菜单项
            await conn.execute(text("""
                INSERT INTO menu_configurations 
                (key, label, icon, path, component, position, section, 'order', enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """), (
                'query-forms',
                '动态表单',
                'FormOutlined',
                '/query-forms',
                'QueryFormManagement',
                'top',
                'main',
                3,  # 放在自定义查询后面
                True
            ))
            
            await conn.commit()
            print("✅ 成功添加动态查询表单菜单项")
            return True
        
    except Exception as e:
        print(f"❌ 添加菜单项失败: {e}")
        return False


async def main():
    """主函数"""
    print("🔍 检查和配置菜单系统")
    print("=" * 60)
    
    # 检查当前配置
    await check_menu_config()
    
    # 添加动态查询表单菜单
    await add_query_forms_menu()
    
    print("\n🔍 更新后的菜单配置:")
    await check_menu_config()


if __name__ == "__main__":
    asyncio.run(main())