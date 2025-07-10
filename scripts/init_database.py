#!/usr/bin/env python3
"""
数据库初始化脚本
创建必要的表并插入初始数据
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_sqlite_manager
from app.models.tables import Base
from app.core.config import settings
from sqlalchemy import text

async def create_tables():
    """创建数据库表"""
    sqlite_manager = get_sqlite_manager()
    
    # 创建表的SQL语句
    create_tables_sql = [
        """
        CREATE TABLE IF NOT EXISTS database_servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL UNIQUE,
            "order" INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS menu_configurations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key VARCHAR(100) NOT NULL UNIQUE,
            label VARCHAR(100) NOT NULL,
            icon VARCHAR(50) NOT NULL,
            path VARCHAR(255) NOT NULL,
            component VARCHAR(100) NOT NULL,
            position VARCHAR(20) DEFAULT 'top',
            section VARCHAR(20) DEFAULT 'main',
            "order" INTEGER DEFAULT 1,
            enabled BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key VARCHAR(100) NOT NULL UNIQUE,
            value TEXT,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_type VARCHAR(50) NOT NULL,
            sql TEXT NOT NULL,
            params TEXT DEFAULT '{}',
            execution_time REAL NOT NULL,
            row_count INTEGER NOT NULL,
            success BOOLEAN NOT NULL,
            error_message TEXT,
            user_id VARCHAR(100) DEFAULT 'system',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS saved_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            query_type VARCHAR(50) NOT NULL,
            sql TEXT NOT NULL,
            params TEXT DEFAULT '{}',
            is_public BOOLEAN DEFAULT 0,
            tags TEXT DEFAULT '[]',
            is_favorite BOOLEAN DEFAULT 0,
            user_id VARCHAR(100) DEFAULT 'system',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS database_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_name VARCHAR(255) NOT NULL,
            database_name VARCHAR(255),
            status VARCHAR(50) NOT NULL,
            last_error TEXT,
            connected_at DATETIME,
            response_time REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS query_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_hash VARCHAR(64) NOT NULL UNIQUE,
            sql_text TEXT NOT NULL,
            execution_count INTEGER DEFAULT 0,
            total_duration REAL DEFAULT 0.0,
            avg_duration REAL DEFAULT 0.0,
            max_duration REAL DEFAULT 0.0,
            min_duration REAL DEFAULT 0.0,
            total_rows INTEGER DEFAULT 0,
            avg_rows REAL DEFAULT 0.0,
            error_count INTEGER DEFAULT 0,
            last_execution DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    ]
    
    async with sqlite_manager.get_connection() as conn:
        for sql in create_tables_sql:
            await conn.execute(text(sql))
            print(f"Created table: {sql.split('TABLE IF NOT EXISTS')[1].split('(')[0].strip()}")

async def insert_initial_data():
    """插入初始数据"""
    sqlite_manager = get_sqlite_manager()
    
    # 菜单配置初始数据
    menu_configs = [
        # 功能菜单
        {
            'key': '/custom-query',
            'label': '自定义查询',
            'icon': 'CodeOutlined',
            'path': '/custom-query',
            'component': 'CustomQuery',
            'position': 'top',
            'section': 'main',
            'order': 1,
            'enabled': True
        },
        {
            'key': '/query-history',
            'label': '查询历史',
            'icon': 'HistoryOutlined',
            'path': '/query-history',
            'component': 'QueryHistory',
            'position': 'top',
            'section': 'main',
            'order': 2,
            'enabled': True
        },
        {
            'key': '/saved-queries',
            'label': '保存的查询',
            'icon': 'SaveOutlined',
            'path': '/saved-queries',
            'component': 'SavedQueries',
            'position': 'top',
            'section': 'main',
            'order': 3,
            'enabled': True
        },
        {
            'key': '/query-stats',
            'label': '查询统计',
            'icon': 'BarChartOutlined',
            'path': '/query-stats',
            'component': 'QueryStats',
            'position': 'top',
            'section': 'main',
            'order': 4,
            'enabled': True
        },
        # 系统菜单
        {
            'key': '/database-config',
            'label': '数据库配置',
            'icon': 'DatabaseOutlined',
            'path': '/database-config',
            'component': 'DatabaseConfig',
            'position': 'bottom',
            'section': 'system',
            'order': 1,
            'enabled': True
        },
        {
            'key': '/menu-config',
            'label': '菜单配置',
            'icon': 'MenuOutlined',
            'path': '/menu-config',
            'component': 'MenuConfig',
            'position': 'bottom',
            'section': 'system',
            'order': 2,
            'enabled': True
        },
        {
            'key': '/settings',
            'label': '系统设置',
            'icon': 'SettingOutlined',
            'path': '/settings',
            'component': 'Settings',
            'position': 'bottom',
            'section': 'system',
            'order': 3,
            'enabled': True
        },
        {
            'key': '/about',
            'label': '关于',
            'icon': 'InfoCircleOutlined',
            'path': '/about',
            'component': 'About',
            'position': 'bottom',
            'section': 'system',
            'order': 4,
            'enabled': True
        }
    ]
    
    # 数据库服务器初始数据
    database_servers = [
        {
            'name': '示例服务器',
            'order': 1
        }
    ]
    
    # 系统设置初始数据
    system_settings = [
        {
            'key': 'current_server_selection',
            'value': '示例服务器',
            'description': '当前选择的数据库服务器名称'
        },
        {
            'key': 'app_version',
            'value': '1.0.0',
            'description': 'SQL查询管理器版本'
        },
        {
            'key': 'max_query_history',
            'value': '1000',
            'description': '最大查询历史记录数'
        }
    ]
    
    async with sqlite_manager.get_connection() as conn:
        # 清空现有数据
        await conn.execute(text("DELETE FROM menu_configurations"))
        await conn.execute(text("DELETE FROM database_servers"))
        await conn.execute(text("DELETE FROM system_settings"))
        
        # 插入菜单配置
        for menu in menu_configs:
            await conn.execute(text("""
                INSERT INTO menu_configurations (key, label, icon, path, component, position, section, "order", enabled)
                VALUES (:key, :label, :icon, :path, :component, :position, :section, :order, :enabled)
            """), menu)
        
        # 插入数据库服务器
        for server in database_servers:
            await conn.execute(text("""
                INSERT INTO database_servers (name, "order")
                VALUES (:name, :order)
            """), server)
        
        # 插入系统设置
        for setting in system_settings:
            await conn.execute(text("""
                INSERT INTO system_settings (key, value, description)
                VALUES (:key, :value, :description)
            """), setting)
        
        print("Inserted initial data successfully!")

async def main():
    """主函数"""
    print("Starting database initialization...")
    print(f"Database path: {settings.database.sqlite_path}")
    print(f"Database connection string: {settings.database.sqlite_connection_string}")
    
    try:
        await create_tables()
        await insert_initial_data()
        print("Database initialization completed successfully!")
    except Exception as e:
        print(f"Error during database initialization: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())