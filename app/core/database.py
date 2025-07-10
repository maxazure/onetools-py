"""数据库管理 - 直接导出独立的管理器"""

# 直接导出各个独立的数据库管理器
from app.core.sqlserver_manager import SQLServerQueryManager
from app.core.sqlite_manager import SQLiteConfigManager
from app.core.config import settings

# SQL Server查询管理器 - 用于用户的动态查询
def get_sqlserver_manager() -> SQLServerQueryManager:
    """获取SQL Server查询管理器实例"""
    return SQLServerQueryManager(settings.database)

# SQLite配置管理器 - 用于软件配置存储
def get_sqlite_manager() -> SQLiteConfigManager:
    """获取SQLite配置管理器实例"""
    return SQLiteConfigManager(settings.database)

# 全局实例
sqlserver_manager = get_sqlserver_manager()
sqlite_manager = get_sqlite_manager()

# 为了向后兼容，保留一些常用的函数
async def execute_query(sql: str, parameters: dict = None):
    """执行SQL Server查询 - 向后兼容"""
    return await sqlserver_manager.execute_query(sql, parameters)

async def test_connection_with_string(connection_string: str):
    """测试SQL Server连接 - 向后兼容"""
    return await sqlserver_manager.test_connection_with_string(connection_string)