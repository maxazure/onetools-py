"""API dependencies and common utilities"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status

from app.core.database import get_sqlite_manager, get_sqlserver_manager
from app.core.logging import get_logger
from app.services.query_service import QueryService, get_query_service

logger = get_logger(__name__)


def get_query_service_dep() -> QueryService:
    """获取查询服务依赖"""
    return get_query_service()


def get_sqlite_manager_dep():
    """获取SQLite配置管理器依赖"""
    return get_sqlite_manager()


def get_sqlserver_manager_dep():
    """获取SQL Server管理器依赖"""
    return get_sqlserver_manager()


# 移除数据库连接验证 - 不对SQL Server进行自动健康检查


# 分页参数已移除 - 不需要分页功能


# 已移除 get_module_by_name，使用 QueryService 替代