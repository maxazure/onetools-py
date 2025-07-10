#!/usr/bin/env python3
"""
数据库初始化脚本 - 包含默认菜单配置、数据库服务器配置和系统设置
用于新程序的第一次初始化
"""

import sqlite3
import json
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def get_default_data():
    """获取默认初始化数据"""
    return {
        "menu_configurations": [
            {
                "key": "/transaction-query",
                "label": "事务查询",
                "icon": "TransactionOutlined",
                "path": "/transaction-query",
                "component": "TransactionQuery",
                "position": "top",
                "section": "main",
                "order": 1,
                "enabled": True
            },
            {
                "key": "/custom-query",
                "label": "自定义查询",
                "icon": "CodeOutlined",
                "path": "/custom-query",
                "component": "CustomQuery",
                "position": "top",
                "section": "main",
                "order": 2,
                "enabled": True
            },
            {
                "key": "/saved-queries",
                "label": "保存的查询",
                "icon": "SaveOutlined",
                "path": "/saved-queries",
                "component": "SavedQueries",
                "position": "top",
                "section": "main",
                "order": 3,
                "enabled": True
            },
            {
                "key": "/user-query",
                "label": "用户查询",
                "icon": "UserOutlined",
                "path": "/user-query",
                "component": "UserQuery",
                "position": "top",
                "section": "main",
                "order": 4,
                "enabled": True
            },
            {
                "key": "/database-config",
                "label": "数据库配置",
                "icon": "DatabaseOutlined",
                "path": "/database-config",
                "component": "DatabaseConfig",
                "position": "bottom",
                "section": "system",
                "order": 1,
                "enabled": True
            },
            {
                "key": "/menu-config",
                "label": "菜单配置",
                "icon": "MenuOutlined",
                "path": "/menu-config",
                "component": "MenuConfig",
                "position": "bottom",
                "section": "system",
                "order": 2,
                "enabled": True
            },
            {
                "key": "/settings",
                "label": "系统设置",
                "icon": "SettingOutlined",
                "path": "/settings",
                "component": "Settings",
                "position": "bottom",
                "section": "system",
                "order": 3,
                "enabled": True
            },
            {
                "key": "/about",
                "label": "关于",
                "icon": "InfoCircleOutlined",
                "path": "/about",
                "component": "About",
                "position": "bottom",
                "section": "system",
                "order": 4,
                "enabled": True
            }
        ],
        "database_servers": [
            {
                "name": "localhost\\SQLEXPRESS",
                "port": 1433,
                "is_enabled": True,
                "description": "本地SQL Server Express实例",
                "order": 1
            }
        ],
        "system_settings": [
            {
                "key": "app.name",
                "value": "OneTools",
                "description": "应用程序名称"
            },
            {
                "key": "app.version",
                "value": "2.0.0",
                "description": "应用程序版本"
            },
            {
                "key": "database.max_query_history",
                "value": "1000",
                "description": "最大查询历史记录数"
            },
            {
                "key": "database.default_timeout",
                "value": "30",
                "description": "数据库查询默认超时时间(秒)"
            },
            {
                "key": "ui.theme",
                "value": "light",
                "description": "用户界面主题"
            },
            {
                "key": "ui.language",
                "value": "zh-CN",
                "description": "用户界面语言"
            }
        ]
    }

def create_tables(cursor):
    """创建数据库表"""
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

def insert_menu_configurations(cursor, menu_configs):
    """插入菜单配置数据"""
    print(f"插入 {len(menu_configs)} 个菜单配置...")
    
    now = datetime.now().isoformat()
    
    for menu in menu_configs:
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
            now,
            now
        ))
        print(f"  - 已插入菜单: {menu['label']} ({menu['key']})")

def insert_database_servers(cursor, servers):
    """插入数据库服务器配置"""
    print(f"插入 {len(servers)} 个数据库服务器配置...")
    
    now = datetime.now().isoformat()
    
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
            now,
            now
        ))
        print(f"  - 已插入服务器: {server['name']} (端口: {server['port']})")

def insert_system_settings(cursor, settings):
    """插入系统设置"""
    print(f"插入 {len(settings)} 个系统设置...")
    
    now = datetime.now().isoformat()
    
    for setting in settings:
        cursor.execute("""
            INSERT OR REPLACE INTO system_settings 
            (key, value, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            setting["key"],
            setting["value"],
            setting["description"],
            now,
            now
        ))
        print(f"  - 已插入设置: {setting['key']} = {setting['value']}")

def check_existing_data(cursor):
    """检查现有数据"""
    print("检查现有数据...")
    
    # 检查菜单配置
    cursor.execute("SELECT COUNT(*) FROM menu_configurations")
    menu_count = cursor.fetchone()[0]
    
    # 检查数据库服务器
    cursor.execute("SELECT COUNT(*) FROM database_servers")
    server_count = cursor.fetchone()[0]
    
    # 检查系统设置
    cursor.execute("SELECT COUNT(*) FROM system_settings")
    settings_count = cursor.fetchone()[0]
    
    print(f"  - 现有菜单配置: {menu_count} 个")
    print(f"  - 现有数据库服务器: {server_count} 个")
    print(f"  - 现有系统设置: {settings_count} 个")
    
    return menu_count, server_count, settings_count

def init_database_with_defaults(db_path=None, force=False):
    """初始化数据库并插入默认数据"""
    
    if db_path is None:
        db_path = project_root / "data" / "onetools.db"
    
    print(f"初始化数据库: {db_path}")
    
    # 确保数据目录存在
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 连接数据库
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # 创建表
        create_tables(cursor)
        
        # 检查现有数据
        menu_count, server_count, settings_count = check_existing_data(cursor)
        
        # 获取默认数据
        default_data = get_default_data()
        
        # 根据现有数据决定是否插入
        if force or menu_count == 0:
            insert_menu_configurations(cursor, default_data["menu_configurations"])
        else:
            print("菜单配置已存在，跳过插入")
        
        if force or server_count == 0:
            insert_database_servers(cursor, default_data["database_servers"])
        else:
            print("数据库服务器配置已存在，跳过插入")
        
        if force or settings_count == 0:
            insert_system_settings(cursor, default_data["system_settings"])
        else:
            print("系统设置已存在，跳过插入")
        
        # 提交事务
        conn.commit()
        
        print("\n数据库初始化完成!")
        
        # 显示最终统计
        check_existing_data(cursor)
        
    except Exception as e:
        print(f"初始化数据库时发生错误: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()
    
    return True

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OneTools数据库初始化脚本")
    parser.add_argument("--db-path", help="数据库文件路径")
    parser.add_argument("--force", action="store_true", help="强制重新插入数据（覆盖现有数据）")
    
    args = parser.parse_args()
    
    db_path = Path(args.db_path) if args.db_path else None
    
    success = init_database_with_defaults(db_path, args.force)
    
    if success:
        print("\n[SUCCESS] 数据库初始化成功!")
    else:
        print("\n[ERROR] 数据库初始化失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()