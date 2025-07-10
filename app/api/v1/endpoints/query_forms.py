"""动态查询表单API endpoints"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.models.schemas import (
    QueryFormCreate,
    QueryFormUpdate,
    QueryFormResponse,
    QueryFormExecuteRequest,
    QueryFormHistory,
    SQLParseResult,
    DataSourceTestRequest,
    DataSourceTestResponse,
    QueryResponse,
    ApiResponse
)
from app.services.query_form_service import get_query_form_service
from app.services.query_service import get_query_service

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=ApiResponse[List[QueryFormResponse]])
async def get_query_forms(
    active_only: bool = Query(default=True, description="只显示激活的表单"),
    query_form_service = Depends(get_query_form_service)
):
    """获取所有查询表单"""
    try:
        forms = await query_form_service.get_all_forms(active_only=active_only)
        return ApiResponse.success_response(
            data=forms,
            message=f"成功获取{len(forms)}个查询表单"
        )
    except Exception as e:
        logger.error(f"获取查询表单失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取查询表单失败: {str(e)}")


@router.get("/{form_id}", response_model=ApiResponse[QueryFormResponse])
async def get_query_form(
    form_id: int,
    query_form_service = Depends(get_query_form_service)
):
    """根据ID获取查询表单"""
    try:
        form = await query_form_service.get_form_by_id(form_id)
        if not form:
            raise HTTPException(status_code=404, detail=f"查询表单不存在: {form_id}")
        
        return ApiResponse.success_response(
            data=form,
            message="成功获取查询表单"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取查询表单失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取查询表单失败: {str(e)}")


@router.post("/", response_model=ApiResponse[QueryFormResponse])
async def create_query_form(
    form_data: QueryFormCreate,
    query_form_service = Depends(get_query_form_service)
):
    """创建查询表单"""
    try:
        form = await query_form_service.create_form(form_data)
        if not form:
            raise HTTPException(status_code=400, detail="创建查询表单失败")
        
        return ApiResponse.success_response(
            data=form,
            message=f"成功创建查询表单: {form.form_name}"
        )
    except Exception as e:
        logger.error(f"创建查询表单失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建查询表单失败: {str(e)}")


@router.put("/{form_id}", response_model=ApiResponse[QueryFormResponse])
async def update_query_form(
    form_id: int,
    form_data: QueryFormUpdate,
    query_form_service = Depends(get_query_form_service)
):
    """更新查询表单"""
    try:
        form = await query_form_service.update_form(form_id, form_data)
        if not form:
            raise HTTPException(status_code=404, detail=f"查询表单不存在: {form_id}")
        
        return ApiResponse.success_response(
            data=form,
            message=f"成功更新查询表单: {form.form_name}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新查询表单失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新查询表单失败: {str(e)}")


@router.delete("/{form_id}")
async def delete_query_form(
    form_id: int,
    soft_delete: bool = Query(default=True, description="是否软删除"),
    query_form_service = Depends(get_query_form_service)
):
    """删除查询表单"""
    try:
        success = await query_form_service.delete_form(form_id, soft_delete=soft_delete)
        if not success:
            raise HTTPException(status_code=404, detail=f"查询表单不存在: {form_id}")
        
        delete_type = "软删除" if soft_delete else "永久删除"
        return ApiResponse.success_response(
            data=None,
            message=f"成功{delete_type}查询表单: {form_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除查询表单失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除查询表单失败: {str(e)}")


@router.post("/parse-sql", response_model=ApiResponse[SQLParseResult])
async def parse_sql_template(
    request: dict,
    query_form_service = Depends(get_query_form_service)
):
    """解析SQL模板并生成字段建议"""
    try:
        sql_template = request.get('sql_template', '')
        if not sql_template.strip():
            raise HTTPException(status_code=400, detail="SQL模板不能为空")
        
        result = await query_form_service.parse_sql_template(sql_template)
        return ApiResponse.success_response(
            data=result,
            message=f"成功解析SQL模板，发现{len(result.parameters)}个参数"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解析SQL模板失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"解析SQL模板失败: {str(e)}")


@router.post("/test-data-source", response_model=ApiResponse[DataSourceTestResponse])
async def test_data_source(
    request: DataSourceTestRequest,
    query_form_service = Depends(get_query_form_service)
):
    """测试数据源配置"""
    try:
        result = await query_form_service.test_data_source(request)
        return ApiResponse.success_response(
            data=result,
            message="数据源测试完成"
        )
    except Exception as e:
        logger.error(f"测试数据源失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"测试数据源失败: {str(e)}")


@router.post("/execute", response_model=ApiResponse[QueryResponse])
async def execute_query_form(
    request: QueryFormExecuteRequest,
    query_form_service = Depends(get_query_form_service)
):
    """执行动态表单查询"""
    try:
        result = await query_form_service.execute_form_query(request)
        return ApiResponse.success_response(
            data=result,
            message=f"查询执行成功，返回{result.total}条记录"
        )
    except Exception as e:
        logger.error(f"执行查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"执行查询失败: {str(e)}")


@router.get("/history/", response_model=ApiResponse[List[QueryFormHistory]])
async def get_query_form_history(
    form_id: Optional[int] = Query(default=None, description="表单ID，不指定则获取所有表单的历史"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回记录数限制"),
    query_form_service = Depends(get_query_form_service)
):
    """获取查询表单执行历史"""
    try:
        history = await query_form_service.get_form_history(form_id=form_id, limit=limit)
        return ApiResponse.success_response(
            data=history,
            message=f"成功获取{len(history)}条执行历史"
        )
    except Exception as e:
        logger.error(f"获取执行历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取执行历史失败: {str(e)}")


@router.get("/{form_id}/preview", response_model=ApiResponse[dict])
async def preview_query_form(
    form_id: int,
    query_form_service = Depends(get_query_form_service)
):
    """预览查询表单配置"""
    try:
        form = await query_form_service.get_form_by_id(form_id)
        if not form:
            raise HTTPException(status_code=404, detail=f"查询表单不存在: {form_id}")
        
        # 解析SQL模板获取参数信息
        parse_result = await query_form_service.parse_sql_template(form.sql_template)
        
        preview_data = {
            "form_info": {
                "id": form.id,
                "name": form.form_name,
                "description": form.form_description,
                "target_database": form.target_database,
                "is_active": form.is_active
            },
            "sql_template": form.sql_template,
            "form_config": form.form_config,
            "parameters": parse_result.parameters,
            "warnings": parse_result.warnings
        }
        
        return ApiResponse.success_response(
            data=preview_data,
            message="成功获取表单预览"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览查询表单失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"预览查询表单失败: {str(e)}")


@router.post("/{form_id}/duplicate", response_model=ApiResponse[QueryFormResponse])
async def duplicate_query_form(
    form_id: int,
    new_name: str = Query(..., description="新表单名称"),
    query_form_service = Depends(get_query_form_service)
):
    """复制查询表单"""
    try:
        # 获取原表单
        original_form = await query_form_service.get_form_by_id(form_id)
        if not original_form:
            raise HTTPException(status_code=404, detail=f"查询表单不存在: {form_id}")
        
        # 创建新表单
        new_form_data = QueryFormCreate(
            form_name=new_name,
            form_description=f"复制自: {original_form.form_name}",
            sql_template=original_form.sql_template,
            form_config=original_form.form_config,
            target_database=original_form.target_database
        )
        
        new_form = await query_form_service.create_form(new_form_data)
        if not new_form:
            raise HTTPException(status_code=400, detail="复制查询表单失败")
        
        return ApiResponse.success_response(
            data=new_form,
            message=f"成功复制查询表单: {new_form.form_name}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"复制查询表单失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"复制查询表单失败: {str(e)}")


@router.post("/{form_id}/toggle-status")
async def toggle_query_form_status(
    form_id: int,
    query_form_service = Depends(get_query_form_service)
):
    """切换查询表单激活状态"""
    try:
        # 获取当前表单
        form = await query_form_service.get_form_by_id(form_id)
        if not form:
            raise HTTPException(status_code=404, detail=f"查询表单不存在: {form_id}")
        
        # 切换状态
        update_data = QueryFormUpdate(is_active=not form.is_active)
        updated_form = await query_form_service.update_form(form_id, update_data)
        
        status_text = "激活" if updated_form.is_active else "禁用"
        return ApiResponse.success_response(
            data={"is_active": updated_form.is_active},
            message=f"成功{status_text}查询表单: {updated_form.form_name}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换表单状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"切换表单状态失败: {str(e)}")