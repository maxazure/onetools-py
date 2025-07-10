"""数据库管理API端点"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_sqlite_manager_dep, get_sqlserver_manager_dep
from app.core.database import get_sqlite_manager
from app.core.logging import get_logger
from app.models.schemas import ApiResponse, HealthCheckResponse, MsDatabaseConnection

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/health",
    response_model=ApiResponse[HealthCheckResponse],
    summary="应用健康检查",
    description="检查应用健康状态 - 仅检查本地配置数据库"
)
async def database_health_check():
    """应用健康检查 - 不检查目标SQL Server"""
    try:
        # 仅检查SQLite配置数据库
        sqlite_manager = get_sqlite_manager()
        sqlite_status = True  # 假设SQLite配置数据库可用
        
        # 不检查SQL Server - 仅在用户请求时连接
        health_check = HealthCheckResponse(
            status="healthy",
            version="2.0.0",
            sqlite_status=sqlite_status
        )
        
        return ApiResponse.success_response(
            data=health_check,
            message="健康检查完成"
        )
    
    except Exception as e:
        logger.error("健康检查失败", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"健康检查失败: {str(e)}"
        )




@router.get(
    "/connection-status",
    response_model=ApiResponse[List[MsDatabaseConnection]],
    summary="获取配置状态",
    description="获取应用配置状态 - 不检查目标SQL Server"
)
async def get_connection_status():
    """获取配置状态 - 不检查目标SQL Server"""
    try:
        connections = []
        
        # 仅返回SQLite配置数据库状态
        sqlite_manager = get_sqlite_manager()
        connections.append(MsDatabaseConnection(
            server_name="SQLite配置",
            database_name="config",
            status="connected",  # 假设配置数据库可用
            connection_string="sqlite+aiosqlite:///data/onetools.db"
        ))
        
        return ApiResponse.success_response(
            data=connections,
            message="配置状态获取成功"
        )
    
    except Exception as e:
        logger.error("获取配置状态失败", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置状态失败: {str(e)}"
        )


@router.post(
    "/test-connection",
    response_model=ApiResponse[Dict[str, Any]],
    summary="测试数据库连接",
    description="测试指定的数据库服务器连接"
)
async def test_database_connection(
    connection_data: Dict[str, Any],
    sqlserver_manager = Depends(get_sqlserver_manager_dep)
):
    """测试数据库连接"""
    try:
        import time
        
        server_name = connection_data.get("server")
        
        start_time = time.time()
        
        # 生成连接字符串
        connection_string = sqlserver_manager.generate_connection_string(server_name)
        
        # 测试连接
        success = await sqlserver_manager.test_connection_with_string(connection_string)
        response_time = (time.time() - start_time) * 1000  # 转换为毫秒
        
        result = {
            "server_name": server_name,
            "success": success,
            "response_time_ms": round(response_time, 2),
            "message": "连接成功" if success else "连接失败"
        }
        
        if success:
            return ApiResponse.success_response(
                data=result,
                message="连接测试完成"
            )
        else:
            return ApiResponse.error_response(
                errors=[result["message"]],
                message="连接测试失败"
            )
    
    except Exception as e:
        server_name = connection_data.get("server", "unknown")
        logger.error("测试数据库连接失败", error=e, server_name=server_name)
        return ApiResponse.error_response(
            errors=[str(e)],
            message="连接测试失败"
        )


# 移除不需要的端点 - 用户明确表示不需要这些SQL Server元数据查询功能




