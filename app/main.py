"""OneTools Python - 主应用入口"""

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import get_sqlite_manager
from app.core.logging import setup_logging, get_logger
from app.models.schemas import ApiResponse


# 自定义JSON编码器处理datetime对象
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


# 自定义JSONResponse类
class CustomJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            cls=CustomJSONEncoder
        ).encode("utf-8")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger = get_logger(__name__)
    logger.info("OneTools Python应用启动中...")
    
    # 设置日志
    setup_logging(settings.logging)
    
    # 初始化SQLite配置数据库
    sqlite_manager = get_sqlite_manager()
    
    try:
        # 初始化数据库表
        from app.core.database_init import init_database
        await init_database()
        logger.info("SQLite配置数据库已初始化")
        
    except Exception as e:
        logger.error("SQLite配置数据库初始化失败", error=e)
    
    # 初始化查询服务
    try:
        from app.services.query_service import get_query_service
        query_service = get_query_service()
        logger.info("查询服务初始化完成")
    except Exception as e:
        logger.error("查询服务初始化失败", error=e)
    
    logger.info("OneTools Python应用启动完成")
    
    yield
    
    # 关闭时清理
    logger.info("OneTools Python应用关闭中...")
    
    try:
        # 仅关闭SQLite配置数据库连接
        # SQL Server连接由查询服务按需管理
        logger.info("应用清理完成")
    except Exception as e:
        logger.error("应用清理失败", error=e)
    
    logger.info("OneTools Python应用已关闭")


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="OneTools Python - 数据库运维工具",
        openapi_url="/api/openapi.json" if settings.debug else None,
        docs_url="/api/docs" if settings.debug else None,
        redoc_url="/api/redoc" if settings.debug else None,
        lifespan=lifespan,
        default_response_class=CustomJSONResponse
    )
    
    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.server.cors_origins,
        allow_credentials=True,
        allow_methods=settings.server.cors_methods,
        allow_headers=settings.server.cors_headers,
    )
    
    # 注册API路由
    app.include_router(api_router, prefix="/api/v1")
    
    # 根路径
    @app.get("/")
    async def root():
        """根路径"""
        return ApiResponse.success_response(
            data={
                "name": settings.app_name,
                "version": settings.app_version,
                "environment": settings.environment,
                "status": "running"
            },
            message="OneTools Python API服务正在运行"
        )
    
    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查"""
        return ApiResponse.success_response(
                message="服务健康"
            )
            
    
    # 全局异常处理
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        """HTTP异常处理"""
        return CustomJSONResponse(
            status_code=exc.status_code,
            content=ApiResponse.error_response(
                errors=[exc.detail],
                message="请求处理失败"
            ).model_dump()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        """通用异常处理"""
        logger = get_logger(__name__)
        logger.error("未处理的异常", error=exc, path=request.url.path)
        
        return CustomJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ApiResponse.error_response(
                errors=["内部服务器错误"],
                message="服务器处理请求时发生错误"
            ).model_dump()
        )
    
    return app


# 创建应用实例
app = create_app()


def main():
    """主函数 - 生产环境启动"""
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        workers=settings.server.workers,
        reload=False,
        log_level=settings.logging.level.lower()
    )


def dev_main():
    """开发环境启动"""
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=True,
        log_level="debug"
    )


if __name__ == "__main__":
    if settings.environment == "development":
        dev_main()
    else:
        main()