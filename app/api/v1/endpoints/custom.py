"""自定义查询API端点"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_query_service_dep
from app.services.query_service import get_query_service
from app.utils.schema_analyzer import get_schema_analyzer
from app.core.logging import get_logger
from app.models.schemas import ApiResponse, QueryRequest, QueryResponse, QueryType
from app.services.query_service import QueryService

logger = get_logger(__name__)
router = APIRouter()


class CustomQueryRequest(BaseModel):
    """自定义查询请求"""
    sql: str
    server_name: Optional[str] = None


class SQLValidationRequest(BaseModel):
    """SQL验证请求"""
    sql: str


class SaveQueryRequest(BaseModel):
    """保存查询请求"""
    name: str
    sql: str
    description: str = ""


class SchemaAnalysisRequest(BaseModel):
    """表结构分析请求"""
    sql: str
    server_name: Optional[str] = None


@router.post(
    "/execute",
    response_model=ApiResponse[Dict[str, Any]],
    summary="执行自定义SQL查询",
    description="执行用户提供的自定义SQL查询"
)
async def execute_custom_query(
    query_request: CustomQueryRequest,
    query_service: QueryService = Depends(get_query_service_dep)
):
    """执行自定义SQL查询"""
    try:
        # 验证SQL查询
        if not query_request.sql or not query_request.sql.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SQL查询不能为空"
            )
        
        logger.info(f"执行自定义查询", sql=query_request.sql[:100], server=query_request.server_name)
        
        # 使用查询服务执行查询
        result = await query_service.execute_query(
            query_request.sql, 
            server_name=query_request.server_name
        )
        
        # 构建响应 
        response_data = {
            "columns": result.columns,
            "data": result.data,
            "total": result.total,
            "execution_time": result.execution_time,
            "sql": result.sql,
            "is_multiple": getattr(result, 'is_multiple', False)
        }
        
        # 根据是否为多结果集调整消息
        if getattr(result, 'is_multiple', False):
            message_text = f"查询执行成功，返回 {result.total} 个结果集"
        else:
            message_text = f"查询执行成功，返回 {result.total} 条记录"
        
        return ApiResponse.success_response(
            data=response_data,
            message=message_text
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("自定义查询参数错误", error=e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("自定义查询执行失败", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询执行失败: {str(e)}"
        )


@router.post(
    "/validate",
    response_model=ApiResponse[Dict[str, Any]],
    summary="验证SQL查询",
    description="验证SQL查询的语法和安全性"
)
async def validate_sql(
    validation_request: SQLValidationRequest
):
    """验证SQL查询"""
    try:
        service = get_query_service()
        validation_result = await service.validate_sql_safety(validation_request.sql)
        
        return ApiResponse.success_response(
            data=validation_result,
            message="SQL验证完成"
        )
    
    except Exception as e:
        logger.error("SQL验证失败", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SQL验证失败: {str(e)}"
        )


@router.post(
    "/save",
    response_model=ApiResponse[Dict[str, Any]],
    summary="保存查询",
    description="保存自定义查询以便后续使用"
)
async def save_query(
    save_request: SaveQueryRequest
):
    """保存查询"""
    try:
        service = get_query_service()
        
        saved_query = await service.save_query(
            name=save_request.name,
            description=save_request.description,
            query_type=QueryType.CUSTOM,
            sql=save_request.sql
        )
        
        return ApiResponse.success_response(
            data=saved_query,
            message="查询保存成功"
        )
    
    except ValueError as e:
        logger.warning("保存查询参数错误", error=e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("保存查询失败", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存查询失败: {str(e)}"
        )


@router.get(
    "/saved",
    response_model=ApiResponse[List[Dict[str, Any]]],
    summary="获取保存的查询",
    description="获取用户保存的查询列表"
)
async def get_saved_queries():
    """获取保存的查询"""
    try:
        service = get_query_service()
        saved_queries = await service.get_saved_queries()
        
        return ApiResponse.success_response(
            data=saved_queries,
            message="获取保存的查询成功"
        )
    
    except Exception as e:
        logger.error("获取保存的查询失败", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取保存的查询失败: {str(e)}"
        )


@router.get(
    "/parameters",
    response_model=ApiResponse[List[Dict[str, Any]]],
    summary="获取自定义查询参数",
    description="获取自定义查询可用的参数定义"
)
async def get_custom_query_parameters():
    """获取自定义查询参数定义"""
    try:
        service = get_query_service()
        parameters = await service.get_query_parameters(QueryType.CUSTOM)
        
        params_dict = [param.dict() for param in parameters]
        
        return ApiResponse.success_response(
            data=params_dict,
            message="自定义查询参数获取成功"
        )
    
    except Exception as e:
        logger.error("获取自定义查询参数失败", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取查询参数失败: {str(e)}"
        )


@router.post(
    "/analyze-schema",
    response_model=ApiResponse[Dict[str, Any]],
    summary="分析SQL语句中的表结构",
    description="分析SQL语句中包含的所有表和视图的结构信息，支持视图递归分析"
)
async def analyze_sql_schema(
    analysis_request: SchemaAnalysisRequest
):
    """分析SQL语句中的表结构"""
    try:
        # 验证SQL查询
        if not analysis_request.sql or not analysis_request.sql.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SQL查询不能为空"
            )
        
        logger.info(f"开始分析SQL表结构", sql=analysis_request.sql[:100], server=analysis_request.server_name)
        
        # 使用表结构分析器
        query_service = get_query_service()
        analyzer = get_schema_analyzer(query_service)
        schema_create_statements = await analyzer.analyze_sql_schema(
            analysis_request.sql,
            analysis_request.server_name
        )
        
        # 获取分析的表名列表
        table_names = analyzer.extract_table_names(analysis_request.sql)
        
        # 构建响应数据
        response_data = {
            "sql": analysis_request.sql,
            "server_name": analysis_request.server_name,
            "tables_found": list(table_names),
            "create_statements": schema_create_statements,
            "table_count": len(table_names)
        }
        
        return ApiResponse.success_response(
            data=response_data,
            message=f"表结构分析完成，发现 {len(table_names)} 个数据库对象"
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("表结构分析参数错误", error=e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("表结构分析失败", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"表结构分析失败: {str(e)}"
        )