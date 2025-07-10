"""系统设置API端点"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import get_sqlite_manager_dep
from app.core.logging import get_logger
from app.models.schemas import (
    ApiResponse,
    MsDatabaseServerConfigCreate,
    MsDatabaseServerConfigUpdate,
    MsDatabaseServerConfigResponse,
    MenuConfigurationCreate,
    MenuConfigurationUpdate,
    MenuConfigurationResponse
)
from app.services.config_service import config_service

logger = get_logger(__name__)
router = APIRouter()

# 系统设置模型
class SystemSettings(BaseModel):
    databaseServers: List[MsDatabaseServerConfigResponse] = []
    menuConfiguration: List[MenuConfigurationResponse] = []
    version: str = "2.0.0"
    lastUpdated: Optional[str] = None

@router.get(
    "/",
    response_model=ApiResponse[SystemSettings],
    summary="获取系统设置",
    description="获取完整的系统设置配置"
)
async def get_system_settings():
    """获取系统设置"""
    try:
        # 获取数据库服务器配置
        database_servers = config_service.get_database_servers()
        
        # 获取菜单配置
        menu_configuration = await config_service.get_menu_configurations_async()
        
        settings = SystemSettings(
            databaseServers=database_servers,
            menuConfiguration=menu_configuration,
            version="2.0.0"
        )
        
        return ApiResponse.success_response(
            data=settings,
            message="系统设置获取成功"
        )
    
    except Exception as e:
        logger.error("获取系统设置失败", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统设置失败: {str(e)}"
        )

@router.put(
    "/",
    response_model=ApiResponse[Dict[str, Any]],
    summary="更新系统设置",
    description="更新系统设置配置"
)
async def update_system_settings(
    settings: SystemSettings
):
    """更新系统设置"""
    try:
        # 这里可以实现批量更新逻辑
        # 目前主要通过各个子端点单独更新
        logger.info("更新系统设置", settings=settings.dict())
        
        return ApiResponse.success_response(
            data={"updated": True},
            message="系统设置更新成功"
        )
    
    except Exception as e:
        logger.error("更新系统设置失败", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新系统设置失败: {str(e)}"
        )

@router.get(
    "/database-servers",
    response_model=ApiResponse[List[MsDatabaseServerConfigResponse]],
    summary="获取数据库服务器列表",
    description="获取所有数据库服务器配置"
)
async def get_database_servers():
    """获取数据库服务器列表"""
    try:
        servers = await config_service.get_database_servers_async()
        
        return ApiResponse.success_response(
            data=servers,
            message="数据库服务器列表获取成功"
        )
    
    except Exception as e:
        logger.error("获取数据库服务器列表失败", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取数据库服务器列表失败: {str(e)}"
        )

@router.post(
    "/database-servers",
    response_model=ApiResponse[MsDatabaseServerConfigResponse],
    summary="创建数据库服务器",
    description="创建新的数据库服务器配置"
)
async def create_database_server(
    server: MsDatabaseServerConfigCreate
):
    """创建数据库服务器"""
    try:
        created_server = await config_service.create_database_server_async(server)
        if not created_server:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="创建数据库服务器失败"
            )
        
        return ApiResponse.success_response(
            data=created_server,
            message="数据库服务器创建成功"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("创建数据库服务器失败", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建数据库服务器失败: {str(e)}"
        )

@router.put(
    "/database-servers/{server_id}",
    response_model=ApiResponse[MsDatabaseServerConfigResponse],
    summary="更新数据库服务器",
    description="更新指定的数据库服务器配置"
)
async def update_database_server(
    server_id: int,
    server: MsDatabaseServerConfigUpdate
):
    """更新数据库服务器"""
    try:
        updated_server = await config_service.update_database_server_async(server_id, server)
        if not updated_server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="数据库服务器不存在"
            )
        
        return ApiResponse.success_response(
            data=updated_server,
            message="数据库服务器更新成功"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("更新数据库服务器失败", error=e, server_id=server_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新数据库服务器失败: {str(e)}"
        )

@router.delete(
    "/database-servers/{server_id}",
    response_model=ApiResponse[Dict[str, Any]],
    summary="删除数据库服务器",
    description="删除指定的数据库服务器配置"
)
async def delete_database_server(
    server_id: int
):
    """删除数据库服务器"""
    try:
        success = await config_service.delete_database_server_async(server_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="数据库服务器不存在或无法删除"
            )
        
        return ApiResponse.success_response(
            data={"deleted": True, "id": server_id},
            message="数据库服务器删除成功"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("删除数据库服务器失败", error=e, server_id=server_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除数据库服务器失败: {str(e)}"
        )


@router.get(
    "/menu",
    response_model=ApiResponse[List[MenuConfigurationResponse]],
    summary="获取菜单配置",
    description="获取系统菜单配置"
)
async def get_menu_configuration():
    """获取菜单配置"""
    try:
        menu_config = await config_service.get_menu_configurations_async()
        
        return ApiResponse.success_response(
            data=menu_config,
            message="菜单配置获取成功"
        )
    
    except Exception as e:
        logger.error("获取菜单配置失败", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取菜单配置失败: {str(e)}"
        )

@router.put(
    "/menu",
    response_model=ApiResponse[List[MenuConfigurationResponse]],
    summary="更新菜单配置",
    description="更新系统菜单配置"
)
async def update_menu_configuration(
    menu_config: List[MenuConfigurationUpdate]
):
    """更新菜单配置"""
    try:
        updated_configs = []
        for menu_item in menu_config:
            if hasattr(menu_item, 'id') and menu_item.id:
                updated_config = config_service.update_menu_configuration(menu_item.id, menu_item)
                if updated_config:
                    updated_configs.append(updated_config)
        
        return ApiResponse.success_response(
            data=updated_configs,
            message="菜单配置更新成功"
        )
    
    except Exception as e:
        logger.error("更新菜单配置失败", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新菜单配置失败: {str(e)}"
        )

@router.post(
    "/menu",
    response_model=ApiResponse[MenuConfigurationResponse],
    summary="创建菜单项",
    description="创建新的菜单项"
)
async def create_menu_item(
    menu_item: MenuConfigurationCreate
):
    """创建菜单项"""
    try:
        created_menu = await config_service.create_menu_configuration_async(menu_item)
        if not created_menu:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="创建菜单项失败"
            )
        
        return ApiResponse.success_response(
            data=created_menu,
            message="菜单项创建成功"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("创建菜单项失败", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建菜单项失败: {str(e)}"
        )

@router.put(
    "/menu/{menu_id}",
    response_model=ApiResponse[MenuConfigurationResponse],
    summary="更新菜单项",
    description="更新指定的菜单项"
)
async def update_menu_item(
    menu_id: int,
    menu_item: MenuConfigurationUpdate
):
    """更新菜单项"""
    try:
        updated_menu = await config_service.update_menu_configuration_async(menu_id, menu_item)
        if not updated_menu:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="菜单项不存在"
            )
        
        return ApiResponse.success_response(
            data=updated_menu,
            message="菜单项更新成功"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("更新菜单项失败", error=e, menu_id=menu_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新菜单项失败: {str(e)}"
        )

@router.delete(
    "/menu/{menu_id}",
    response_model=ApiResponse[Dict[str, Any]],
    summary="删除菜单项",
    description="删除指定的菜单项"
)
async def delete_menu_item(
    menu_id: int
):
    """删除菜单项"""
    try:
        success = await config_service.delete_menu_configuration(menu_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="菜单项不存在"
            )
        
        return ApiResponse.success_response(
            data={"deleted": True, "id": menu_id},
            message="菜单项删除成功"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("删除菜单项失败", error=e, menu_id=menu_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除菜单项失败: {str(e)}"
        )

# 当前服务器选择持久化
class CurrentServerSelection(BaseModel):
    server_name: str = Field(..., description="当前选择的服务器名称")

# 下拉框专用数据结构
class ServerDropdownOption(BaseModel):
    value: str = Field(..., description="服务器名称值")
    label: str = Field(..., description="显示标签")
    enabled: bool = Field(..., description="是否启用")

class ServerDropdownResponse(BaseModel):
    servers: List[ServerDropdownOption] = Field(..., description="服务器选项列表")
    current_server: Optional[str] = Field(default=None, description="当前选择的服务器名称")

@router.get(
    "/current-server",
    response_model=ApiResponse[Dict[str, str]],
    summary="获取当前服务器选择",
    description="获取当前选择的数据库服务器名称"
)
async def get_current_server_selection():
    """获取当前服务器选择"""
    try:
        current_server = config_service.get_current_server_selection()
        
        return ApiResponse.success_response(
            data={"server_name": current_server},
            message="当前服务器选择获取成功"
        )
    
    except Exception as e:
        logger.error("获取当前服务器选择失败", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取当前服务器选择失败: {str(e)}"
        )

@router.post(
    "/current-server",
    response_model=ApiResponse[Dict[str, Any]],
    summary="设置当前服务器选择",
    description="设置当前选择的数据库服务器名称"
)
async def set_current_server_selection(
    selection: CurrentServerSelection
):
    """设置当前服务器选择"""
    try:
        success = config_service.set_current_server_selection(selection.server_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="设置当前服务器选择失败"
            )
        
        return ApiResponse.success_response(
            data={"server_name": selection.server_name, "updated": True},
            message="当前服务器选择设置成功"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("设置当前服务器选择失败", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设置当前服务器选择失败: {str(e)}"
        )

@router.get(
    "/server-dropdown",
    response_model=ApiResponse[ServerDropdownResponse],
    summary="获取服务器下拉框数据",
    description="一次性获取服务器列表和当前选择，专为下拉框设计"
)
async def get_server_dropdown():
    """获取服务器下拉框数据 - 包含服务器列表和当前选择"""
    try:
        # 获取所有数据库服务器配置
        database_servers = await config_service.get_database_servers_async()
        
        # 获取当前服务器选择
        current_server = config_service.get_current_server_selection()
        
        # 构建下拉框选项
        server_options = []
        for server in database_servers:
            server_options.append(ServerDropdownOption(
                value=server.name,
                label=server.name,
                enabled=server.is_enabled
            ))
        
        # 构建响应数据
        dropdown_data = ServerDropdownResponse(
            servers=server_options,
            current_server=current_server
        )
        
        return ApiResponse.success_response(
            data=dropdown_data,
            message=f"获取到 {len(server_options)} 个服务器选项"
        )
    
    except Exception as e:
        logger.error("获取服务器下拉框数据失败", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取服务器下拉框数据失败: {str(e)}"
        )

# 系统设置键值对管理
class SystemSettingRequest(BaseModel):
    key: str = Field(..., description="设置键")
    value: str = Field(..., description="设置值")
    description: str = Field(default="", description="设置描述")

@router.get(
    "/system/{key}",
    response_model=ApiResponse[Dict[str, Any]],
    summary="获取系统设置",
    description="根据键获取系统设置值"
)
async def get_system_setting(key: str):
    """获取系统设置"""
    try:
        value = config_service.get_system_setting(key)
        if value is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"系统设置 '{key}' 不存在"
            )
        
        return ApiResponse.success_response(
            data={"key": key, "value": value},
            message="系统设置获取成功"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取系统设置失败", error=e, key=key)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统设置失败: {str(e)}"
        )

@router.post(
    "/system",
    response_model=ApiResponse[Dict[str, Any]],
    summary="设置系统设置",
    description="设置系统设置键值对"
)
async def set_system_setting(request: SystemSettingRequest):
    """设置系统设置"""
    try:
        success = await config_service.set_system_setting_async(
            key=request.key,
            value=request.value,
            description=request.description
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"设置系统设置 '{request.key}' 失败"
            )
        
        return ApiResponse.success_response(
            data={"key": request.key, "value": request.value, "updated": True},
            message="系统设置保存成功"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("设置系统设置失败", error=e, key=request.key)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设置系统设置失败: {str(e)}"
        )

@router.get(
    "/system",
    response_model=ApiResponse[List[Dict[str, Any]]],
    summary="获取所有系统设置",
    description="获取所有系统设置键值对"
)
async def get_all_system_settings():
    """获取所有系统设置"""
    try:
        settings = await config_service.get_all_system_settings_async()
        
        return ApiResponse.success_response(
            data=settings,
            message=f"获取到 {len(settings)} 个系统设置"
        )
    
    except Exception as e:
        logger.error("获取所有系统设置失败", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取所有系统设置失败: {str(e)}"
        )

@router.delete(
    "/system/{key}",
    response_model=ApiResponse[Dict[str, Any]],
    summary="删除系统设置",
    description="删除指定的系统设置"
)
async def delete_system_setting(key: str):
    """删除系统设置"""
    try:
        success = await config_service.delete_system_setting_async(key)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"系统设置 '{key}' 不存在或删除失败"
            )
        
        return ApiResponse.success_response(
            data={"key": key, "deleted": True},
            message="系统设置删除成功"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("删除系统设置失败", error=e, key=key)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除系统设置失败: {str(e)}"
        )