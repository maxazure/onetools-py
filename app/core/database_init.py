"""数据库初始化模块"""

from sqlalchemy import text
from app.core.database import get_sqlite_manager
from app.core.logging import get_logger

logger = get_logger(__name__)


async def init_database():
    """初始化数据库表"""
    try:
        sqlite_manager = get_sqlite_manager()
        
        # 创建菜单配置表
        await sqlite_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS menu_configurations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                label TEXT NOT NULL,
                icon TEXT NOT NULL,
                path TEXT NOT NULL,
                component TEXT NOT NULL,
                position TEXT DEFAULT 'top',
                section TEXT DEFAULT 'main',
                "order" INTEGER DEFAULT 1,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建系统设置表
        await sqlite_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                value TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建数据库服务器配置表（如果不存在）
        await sqlite_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS database_servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                port INTEGER DEFAULT 1433,
                is_enabled BOOLEAN DEFAULT TRUE,
                description TEXT,
                "order" INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建保存的查询表
        await sqlite_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS saved_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                query_type TEXT NOT NULL,
                sql TEXT NOT NULL,
                params TEXT DEFAULT '{}',
                is_public BOOLEAN DEFAULT FALSE,
                tags TEXT DEFAULT '[]',
                is_favorite BOOLEAN DEFAULT FALSE,
                user_id TEXT DEFAULT 'system',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建查询历史表
        await sqlite_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS query_history (
                id TEXT PRIMARY KEY,
                query_type TEXT NOT NULL,
                sql TEXT NOT NULL,
                params TEXT DEFAULT '{}',
                execution_time REAL NOT NULL,
                row_count INTEGER NOT NULL,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                user_id TEXT DEFAULT 'system',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        logger.info("Database tables created successfully")
        
        # 初始化默认菜单配置
        await init_default_menu_config()
        
        # 初始化默认数据库服务器配置
        await init_default_database_servers()
        
    except Exception as e:
        logger.error("Failed to initialize database", error=e)
        raise


async def init_default_menu_config():
    """初始化默认菜单配置"""
    try:
        sqlite_manager = get_sqlite_manager()
        
        # 检查是否已有菜单配置
        async with sqlite_manager.get_connection() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM menu_configurations"))
            count = result.scalar()
            
            if count > 0:
                logger.info("Menu configurations already exist, skipping initialization")
                return
        
        # 插入默认菜单配置
        default_menus = [
            {
                "key": "/custom-query",
                "label": "自定义查询",
                "icon": "CodeOutlined",
                "path": "/custom-query",
                "component": "CustomQuery",
                "position": "top",
                "section": "main",
                "order": 1,
                "enabled": True
            },
            {
                "key": "/query-history",
                "label": "查询历史",
                "icon": "HistoryOutlined",
                "path": "/query-history",
                "component": "QueryHistory",
                "position": "top",
                "section": "main",
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
                "order": 1,
                "enabled": True
            }
        ]
        
        async with sqlite_manager.get_connection() as conn:
            for menu in default_menus:
                await conn.execute(text("""
                    INSERT INTO menu_configurations (key, label, icon, path, component, position, section, "order", enabled)
                    VALUES (:key, :label, :icon, :path, :component, :position, :section, :order, :enabled)
                """), menu)
        
        logger.info("Default menu configurations initialized")
        
    except Exception as e:
        logger.error("Failed to initialize default menu configurations", error=e)
        raise


async def init_default_database_servers():
    """初始化默认数据库服务器配置 - 不插入示例数据，由用户自行配置"""
    try:
        sqlite_manager = get_sqlite_manager()
        
        # 检查是否已有数据库服务器配置
        async with sqlite_manager.get_connection() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM database_servers"))
            count = result.scalar()
            
            if count > 0:
                logger.info("Database servers already exist, skipping initialization")
                return
        
        # 不插入示例数据，让用户通过界面自行配置数据库服务器
        logger.info("Database servers table is empty, users can configure servers through the UI")
        
    except Exception as e:
        logger.error("Failed to initialize default database server configurations", error=e)
        raise