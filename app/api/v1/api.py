"""API v1 路由聚合"""

from fastapi import APIRouter

from app.api.v1.endpoints import custom, database, settings, query_forms
from app.api.routes.query_history import router as query_history_router

api_router = APIRouter()


# 自定义查询路由
api_router.include_router(
    custom.router,
    prefix="/custom",
    tags=["自定义查询"]
)

# 数据库管理路由
api_router.include_router(
    database.router,
    prefix="/database",
    tags=["数据库管理"]
)

# 查询历史路由
api_router.include_router(
    query_history_router,
    tags=["查询历史"]
)

# 系统设置路由
api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["系统设置"]
)

# 动态查询表单路由
api_router.include_router(
    query_forms.router,
    prefix="/query-forms",
    tags=["动态查询表单"]
)