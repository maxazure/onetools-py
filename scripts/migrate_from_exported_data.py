#!/usr/bin/env python3
"""
从导出的数据文件迁移到新数据库
使用 export_current_data.py 导出的 exported_data.json 文件
"""

import sqlite3
import json
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def load_exported_data(export_file_path):
    """加载导出的数据"""
    if not export_file_path.exists():
        print(f"导出文件不存在: {export_file_path}")
        return None
    
    print(f"加载导出数据: {export_file_path}")
    
    with open(export_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"导出时间: {data['export_time']}")
    print(f"  - 菜单配置: {len(data['menu_configurations'])} 项")
    print(f"  - 数据库服务器: {len(data['database_servers'])} 项")
    print(f"  - 系统设置: {len(data['system_settings'])} 项")
    
    return data

def create_tables(cursor):
    """创建数据库表（与初始化脚本相同）"""
    print("创建数据库表...")
    
    # 创建菜单配置表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu_configurations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            label TEXT NOT NULL,
            icon TEXT,
            path TEXT NOT NULL,
            component TEXT,
            position TEXT DEFAULT 'top',
            section TEXT DEFAULT 'main',
            "order" INTEGER DEFAULT 1,
            enabled BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建数据库服务器配置表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS database_servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            port INTEGER DEFAULT 1433,
            is_enabled BOOLEAN DEFAULT TRUE,
            description TEXT,
            "order" INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建系统设置表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value TEXT,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    print("数据库表创建完成")

def migrate_menu_configurations(cursor, menu_configs):
    """迁移菜单配置数据"""
    print(f"迁移 {len(menu_configs)} 个菜单配置...")
    
    for menu in menu_configs:
        # 保持原有的created_at，更新updated_at为当前时间
        cursor.execute("""
            INSERT OR REPLACE INTO menu_configurations 
            (key, label, icon, path, component, position, section, "order", enabled, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            menu["key"],
            menu["label"],
            menu["icon"],
            menu["path"],
            menu["component"],
            menu["position"],
            menu["section"],
            menu["order"],
            menu["enabled"],
            menu["created_at"],  # 保持原创建时间
            datetime.now().isoformat()  # 更新为当前时间
        ))
        print(f"  - 已迁移菜单: {menu['label']} ({menu['key']})")

def migrate_database_servers(cursor, servers):
    """迁移数据库服务器配置"""
    print(f"迁移 {len(servers)} 个数据库服务器配置...")
    
    for server in servers:
        cursor.execute("""
            INSERT OR REPLACE INTO database_servers 
            (name, port, is_enabled, description, "order", created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            server["name"],
            server["port"],
            server["is_enabled"],
            server["description"],
            server["order"],
            server["created_at"],  # 保持原创建时间
            datetime.now().isoformat()  # 更新为当前时间
        ))
        print(f"  - 已迁移服务器: {server['name']} (端口: {server['port']})")

def migrate_system_settings(cursor, settings):
    """迁移系统设置"""
    print(f"迁移 {len(settings)} 个系统设置...")
    
    for setting in settings:
        cursor.execute("""
            INSERT OR REPLACE INTO system_settings 
            (key, value, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            setting["key"],
            setting["value"],
            setting["description"],
            setting["created_at"],  # 保持原创建时间
            datetime.now().isoformat()  # 更新为当前时间
        ))
        print(f"  - 已迁移设置: {setting['key']} = {setting['value']}")

def migrate_from_exported_data(export_file_path, target_db_path=None, force=False):
    """从导出的数据迁移到新数据库"""
    
    # 加载导出的数据
    exported_data = load_exported_data(export_file_path)
    if not exported_data:
        return False
    
    # 设置目标数据库路径
    if target_db_path is None:
        target_db_path = project_root / "data" / "onetools_migrated.db"
    
    print(f"\n目标数据库: {target_db_path}")
    
    # 确保目标目录存在
    target_db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 如果目标数据库已存在且不强制覆盖，则询问用户
    if target_db_path.exists() and not force:
        response = input(f"目标数据库已存在: {target_db_path}\n是否覆盖? (y/N): ")
        if response.lower() != 'y':
            print("迁移取消")
            return False
    
    # 连接目标数据库
    conn = sqlite3.connect(str(target_db_path))
    cursor = conn.cursor()
    
    try:
        # 创建表
        create_tables(cursor)
        
        # 迁移数据
        migrate_menu_configurations(cursor, exported_data["menu_configurations"])
        migrate_database_servers(cursor, exported_data["database_servers"])
        migrate_system_settings(cursor, exported_data["system_settings"])
        
        # 提交事务
        conn.commit()
        
        print(f"\n[SUCCESS] 数据迁移完成: {target_db_path}")
        
        # 显示迁移统计
        cursor.execute("SELECT COUNT(*) FROM menu_configurations")
        menu_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM database_servers")
        server_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM system_settings")
        settings_count = cursor.fetchone()[0]
        
        print(f"迁移统计:")
        print(f"  - 菜单配置: {menu_count} 个")
        print(f"  - 数据库服务器: {server_count} 个")
        print(f"  - 系统设置: {settings_count} 个")
        
    except Exception as e:
        print(f"迁移数据时发生错误: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()
    
    return True

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OneTools数据迁移脚本")
    parser.add_argument("--export-file", default="scripts/exported_data.json", help="导出数据文件路径")
    parser.add_argument("--target-db", help="目标数据库文件路径")
    parser.add_argument("--force", action="store_true", help="强制覆盖现有数据库")
    
    args = parser.parse_args()
    
    export_file_path = Path(args.export_file)
    target_db_path = Path(args.target_db) if args.target_db else None
    
    success = migrate_from_exported_data(export_file_path, target_db_path, args.force)
    
    if success:
        print("\n[SUCCESS] 数据迁移成功!")
    else:
        print("\n[ERROR] 数据迁移失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()