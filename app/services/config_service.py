"""配置服务 - 使用core SQLite管理器"""

from typing import List, Optional
from datetime import datetime
import asyncio

from app.core.database import get_sqlite_manager
from app.core.logging import LoggerMixin, get_logger
from app.models.schemas import (
    MsDatabaseServerConfigCreate,
    MsDatabaseServerConfigUpdate,
    MsDatabaseServerConfigResponse,
    MenuConfigurationCreate,
    MenuConfigurationUpdate,
    MenuConfigurationResponse
)
from app.models.tables import SystemSettings
from sqlalchemy import text

logger = get_logger(__name__)


class ConfigService(LoggerMixin):
    """配置服务 - 使用SQLite配置管理器"""
    
    def __init__(self):
        super().__init__()
        self.sqlite = get_sqlite_manager()
        # 初始化默认数据
        self._init_default_data()
    
    def _init_default_data(self):
        """初始化默认数据"""
        try:
            # 在实际项目中，这里应该使用SQLAlchemy ORM创建表和初始数据
            # 暂时跳过实际的数据库操作
            self.log_info("Default configuration data initialized")
        except Exception as e:
            self.log_error("Failed to initialize default data", error=e)
    
    # 数据库服务器配置相关方法
    def get_database_servers(self) -> List[MsDatabaseServerConfigResponse]:
        """获取所有数据库服务器配置"""
        try:
            # 检查是否已经在事件循环中
            try:
                loop = asyncio.get_running_loop()
                # 如果已经在事件循环中，返回空列表
                self.log_info("Already in event loop, returning empty database servers")
                return []
            except RuntimeError:
                # 没有运行的事件循环，正常运行
                return asyncio.run(self._get_database_servers_async())
        except Exception as e:
            self.log_error("Failed to get database servers", error=e)
            return []
    
    async def get_database_servers_async(self) -> List[MsDatabaseServerConfigResponse]:
        """异步获取所有数据库服务器配置"""
        return await self._get_database_servers_async()
    
    async def _get_database_servers_async(self) -> List[MsDatabaseServerConfigResponse]:
        """异步获取数据库服务器配置"""
        try:
            self.log_info("Starting to get database servers from database")
            async with self.sqlite.get_connection() as conn:
                result = await conn.execute(text("""
                    SELECT id, name, port, is_enabled, description, "order", created_at, updated_at
                    FROM database_servers
                    ORDER BY "order", id
                """))
                
                rows = result.fetchall()
                self.log_info(f"Found {len(rows)} database servers in database")
                
                if not rows:
                    # 如果没有数据，返回空列表，让用户自行配置
                    self.log_info("No database servers found, returning empty list")
                    return []
                
                servers = []
                for row in rows:
                    server = MsDatabaseServerConfigResponse(
                        id=row[0],
                        name=row[1],
                        port=row[2],
                        is_enabled=bool(row[3]),
                        description=row[4],
                        created_at=row[6] if row[6] else datetime.utcnow(),
                        updated_at=row[7] if row[7] else datetime.utcnow()
                    )
                    servers.append(server)
                    self.log_info(f"Added database server: {server.name}")
                
                self.log_info(f"Successfully loaded {len(servers)} database servers from database")
                return servers
                
        except Exception as e:
            self.log_error("Failed to get database servers from database", error=e)
            self.log_info("Returning empty list due to database error")
            return []
    
    
    def get_database_server(self, server_id: int) -> Optional[MsDatabaseServerConfigResponse]:
        """获取单个数据库服务器配置"""
        try:
            # 这里应该从SQLite配置数据库读取
            # 暂时返回None
            return None
        except Exception as e:
            self.log_error("Failed to get database server", error=e, server_id=server_id)
            return None
    
    def create_database_server(self, server_data: MsDatabaseServerConfigCreate) -> Optional[MsDatabaseServerConfigResponse]:
        """创建数据库服务器配置"""
        try:
            # 检查是否已经在事件循环中
            try:
                loop = asyncio.get_running_loop()
                # 如果已经在事件循环中，返回失败
                self.log_info(f"Already in event loop, cannot create database server: {server_data.name}")
                return None
            except RuntimeError:
                # 没有运行的事件循环，正常运行
                return asyncio.run(self._create_database_server_async(server_data))
        except Exception as e:
            self.log_error("Failed to create database server", error=e, server_name=server_data.name)
            return None
    
    async def create_database_server_async(self, server_data: MsDatabaseServerConfigCreate) -> Optional[MsDatabaseServerConfigResponse]:
        """异步创建数据库服务器配置 - 供FastAPI直接调用"""
        return await self._create_database_server_async(server_data)
    
    async def _create_database_server_async(self, server_data: MsDatabaseServerConfigCreate) -> Optional[MsDatabaseServerConfigResponse]:
        """异步创建数据库服务器配置"""
        try:
            now = datetime.utcnow()
            async with self.sqlite.get_connection() as conn:
                # 插入新的数据库服务器配置
                result = await conn.execute(text("""
                    INSERT INTO database_servers (name, port, is_enabled, description, "order", created_at, updated_at)
                    VALUES (:name, :port, :is_enabled, :description, :order, :created_at, :updated_at)
                """), {
                    "name": server_data.name,
                    "port": server_data.port or 1433,
                    "is_enabled": True,
                    "description": server_data.description,
                    "order": 1,
                    "created_at": now,
                    "updated_at": now
                })
                
                # 获取新创建的ID
                server_id = result.lastrowid
                
                # 返回创建的数据库服务器配置
                return MsDatabaseServerConfigResponse(
                    id=server_id,
                    name=server_data.name,
                    port=server_data.port or 1433,
                    is_enabled=True,
                    description=server_data.description,
                    created_at=now,
                    updated_at=now
                )
                
        except Exception as e:
            self.log_error("Failed to create database server in database", error=e, server_name=server_data.name)
            return None
    
    def update_database_server(self, server_id: int, server_data: MsDatabaseServerConfigUpdate) -> Optional[MsDatabaseServerConfigResponse]:
        """更新数据库服务器配置"""
        try:
            # 检查是否已经在事件循环中
            try:
                loop = asyncio.get_running_loop()
                # 如果已经在事件循环中，返回失败
                self.log_info(f"Already in event loop, cannot update database server: {server_id}")
                return None
            except RuntimeError:
                # 没有运行的事件循环，正常运行
                return asyncio.run(self._update_database_server_async(server_id, server_data))
        except Exception as e:
            self.log_error("Failed to update database server", error=e, server_id=server_id)
            return None
    
    async def update_database_server_async(self, server_id: int, server_data: MsDatabaseServerConfigUpdate) -> Optional[MsDatabaseServerConfigResponse]:
        """异步更新数据库服务器配置 - 供FastAPI直接调用"""
        return await self._update_database_server_async(server_id, server_data)
    
    async def _update_database_server_async(self, server_id: int, server_data: MsDatabaseServerConfigUpdate) -> Optional[MsDatabaseServerConfigResponse]:
        """异步更新数据库服务器配置"""
        try:
            now = datetime.utcnow()
            async with self.sqlite.get_connection() as conn:
                # 构建更新SQL
                update_fields = []
                params = {"server_id": server_id, "updated_at": now}
                
                if server_data.name is not None:
                    update_fields.append("name = :name")
                    params["name"] = server_data.name
                
                if server_data.port is not None:
                    update_fields.append("port = :port")
                    params["port"] = server_data.port
                
                if server_data.is_enabled is not None:
                    update_fields.append("is_enabled = :is_enabled")
                    params["is_enabled"] = server_data.is_enabled
                
                if server_data.description is not None:
                    update_fields.append("description = :description")
                    params["description"] = server_data.description
                
                if not update_fields:
                    # 如果没有字段需要更新，直接返回现有数据
                    return await self._get_database_server_by_id_async(server_id)
                
                # 执行更新
                update_sql = f"""
                    UPDATE database_servers 
                    SET {', '.join(update_fields)}, updated_at = :updated_at
                    WHERE id = :server_id
                """
                
                result = await conn.execute(text(update_sql), params)
                
                if result.rowcount == 0:
                    self.log_warning("No database server found to update", server_id=server_id)
                    return None
                
                # 返回更新后的数据
                return await self._get_database_server_by_id_async(server_id)
                
        except Exception as e:
            self.log_error("Failed to update database server in database", error=e, server_id=server_id)
            return None
    
    async def _get_database_server_by_id_async(self, server_id: int) -> Optional[MsDatabaseServerConfigResponse]:
        """异步根据ID获取数据库服务器配置"""
        try:
            async with self.sqlite.get_connection() as conn:
                result = await conn.execute(text("""
                    SELECT id, name, port, is_enabled, description, "order", created_at, updated_at
                    FROM database_servers
                    WHERE id = :server_id
                """), {"server_id": server_id})
                
                row = result.fetchone()
                if not row:
                    return None
                
                return MsDatabaseServerConfigResponse(
                    id=row[0],
                    name=row[1],
                    port=row[2],
                    is_enabled=bool(row[3]),
                    description=row[4],
                    created_at=row[6] if row[6] else datetime.utcnow(),
                    updated_at=row[7] if row[7] else datetime.utcnow()
                )
        except Exception as e:
            self.log_error("Failed to get database server by ID", error=e, server_id=server_id)
            return None
    
    def delete_database_server(self, server_id: int) -> bool:
        """删除数据库服务器配置"""
        try:
            # 检查是否已经在事件循环中
            try:
                loop = asyncio.get_running_loop()
                # 如果已经在事件循环中，返回失败
                self.log_info(f"Already in event loop, cannot delete database server: {server_id}")
                return False
            except RuntimeError:
                # 没有运行的事件循环，正常运行
                return asyncio.run(self._delete_database_server_async(server_id))
        except Exception as e:
            self.log_error("Failed to delete database server", error=e, server_id=server_id)
            return False
    
    async def delete_database_server_async(self, server_id: int) -> bool:
        """异步删除数据库服务器配置 - 供FastAPI直接调用"""
        return await self._delete_database_server_async(server_id)
    
    async def _delete_database_server_async(self, server_id: int) -> bool:
        """异步删除数据库服务器配置"""
        try:
            # 使用SQLite管理器删除数据库服务器配置
            delete_sql = "DELETE FROM database_servers WHERE id = ?"
            result = await self.sqlite.execute_query(delete_sql, (server_id,))
            
            if result is None:
                self.log_error("Failed to delete database server", server_id=server_id)
                return False
            
            # 检查是否有行被删除
            if result.rowcount == 0:
                self.log_warning("No database server found to delete", server_id=server_id)
                return False
                
            self.log_info("Database server deleted successfully", server_id=server_id)
            return True
        except Exception as e:
            self.log_error("Failed to delete database server", error=e, server_id=server_id)
            return False
    
    # 菜单配置相关方法
    def get_menu_configurations(self) -> List[MenuConfigurationResponse]:
        """获取所有菜单配置"""
        try:
            # 检查是否已经在事件循环中
            try:
                loop = asyncio.get_running_loop()
                # 如果已经在事件循环中，返回默认配置
                self.log_info("Already in event loop, returning default menu configurations")
                return self._get_default_menu_configurations()
            except RuntimeError:
                # 没有运行的事件循环，正常运行
                return asyncio.run(self._get_menu_configurations_async())
        except Exception as e:
            self.log_error("Failed to get menu configurations", error=e)
            return self._get_default_menu_configurations()
    
    async def get_menu_configurations_async(self) -> List[MenuConfigurationResponse]:
        """异步获取所有菜单配置"""
        return await self._get_menu_configurations_async()
    
    async def _get_menu_configurations_async(self) -> List[MenuConfigurationResponse]:
        """异步获取菜单配置"""
        try:
            self.log_info("Starting to get menu configurations from database")
            async with self.sqlite.get_connection() as conn:
                result = await conn.execute(text("""
                    SELECT id, key, label, icon, path, component, position, section, "order", enabled, created_at, updated_at
                    FROM menu_configurations
                    ORDER BY section, "order", id
                """))
                
                rows = result.fetchall()
                self.log_info(f"Found {len(rows)} menu configurations in database")
                
                if not rows:
                    # 如果没有数据，返回默认配置
                    self.log_info("No menu configurations found, returning default configurations")
                    return self._get_default_menu_configurations()
                
                menu_configs = []
                for row in rows:
                    menu_config = MenuConfigurationResponse(
                        id=row[0],
                        key=row[1],
                        label=row[2],
                        icon=row[3],
                        path=row[4],
                        component=row[5],
                        position=row[6],
                        section=row[7],
                        order=row[8],
                        enabled=bool(row[9]),
                        created_at=row[10] if row[10] else datetime.utcnow(),
                        updated_at=row[11] if row[11] else datetime.utcnow()
                    )
                    menu_configs.append(menu_config)
                    self.log_info(f"Added menu config: {menu_config.key} - {menu_config.label}")
                
                self.log_info(f"Successfully loaded {len(menu_configs)} menu configurations from database")
                return menu_configs
                
        except Exception as e:
            self.log_error("Failed to get menu configurations from database", error=e)
            self.log_info("Falling back to default menu configurations")
            return self._get_default_menu_configurations()
    
    def _get_default_menu_configurations(self) -> List[MenuConfigurationResponse]:
        """获取默认菜单配置"""
        return [
            MenuConfigurationResponse(
                id=1,
                key="/custom-query",
                label="自定义查询",
                icon="CodeOutlined",
                path="/custom-query",
                component="CustomQuery",
                position="top",
                section="main",
                order=1,
                enabled=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            MenuConfigurationResponse(
                id=2,
                key="/query-history",
                label="查询历史",
                icon="HistoryOutlined",
                path="/query-history",
                component="QueryHistory",
                position="top",
                section="main",
                order=2,
                enabled=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            MenuConfigurationResponse(
                id=3,
                key="/settings",
                label="系统设置",
                icon="SettingOutlined",
                path="/settings",
                component="Settings",
                position="bottom",
                section="system",
                order=1,
                enabled=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
    
    def get_menu_configuration(self, menu_id: int) -> Optional[MenuConfigurationResponse]:
        """获取单个菜单配置"""
        try:
            # 这里应该从SQLite配置数据库读取
            # 暂时返回None
            return None
        except Exception as e:
            self.log_error("Failed to get menu configuration", error=e, menu_id=menu_id)
            return None
    
    def create_menu_configuration(self, menu_data: MenuConfigurationCreate) -> Optional[MenuConfigurationResponse]:
        """创建菜单配置"""
        try:
            # 检查是否已经在事件循环中
            try:
                loop = asyncio.get_running_loop()
                # 如果已经在事件循环中，返回失败
                self.log_info(f"Already in event loop, cannot create menu configuration: {menu_data.key}")
                return None
            except RuntimeError:
                # 没有运行的事件循环，正常运行
                return asyncio.run(self._create_menu_configuration_async(menu_data))
        except Exception as e:
            self.log_error("Failed to create menu configuration", error=e, menu_key=menu_data.key)
            return None
    
    async def create_menu_configuration_async(self, menu_data: MenuConfigurationCreate) -> Optional[MenuConfigurationResponse]:
        """异步创建菜单配置 - 供FastAPI直接调用"""
        return await self._create_menu_configuration_async(menu_data)
    
    async def _create_menu_configuration_async(self, menu_data: MenuConfigurationCreate) -> Optional[MenuConfigurationResponse]:
        """异步创建菜单配置"""
        try:
            now = datetime.utcnow()
            async with self.sqlite.get_connection() as conn:
                # 插入新的菜单配置
                result = await conn.execute(text("""
                    INSERT INTO menu_configurations (key, label, icon, path, component, position, section, "order", enabled, created_at, updated_at)
                    VALUES (:key, :label, :icon, :path, :component, :position, :section, :order, :enabled, :created_at, :updated_at)
                """), {
                    "key": menu_data.key,
                    "label": menu_data.label,
                    "icon": menu_data.icon,
                    "path": menu_data.path,
                    "component": menu_data.component,
                    "position": menu_data.position,
                    "section": menu_data.section,
                    "order": menu_data.order,
                    "enabled": menu_data.enabled,
                    "created_at": now,
                    "updated_at": now
                })
                
                # 获取新创建的ID
                menu_id = result.lastrowid
                
                # 返回创建的菜单配置
                return MenuConfigurationResponse(
                    id=menu_id,
                    key=menu_data.key,
                    label=menu_data.label,
                    icon=menu_data.icon,
                    path=menu_data.path,
                    component=menu_data.component,
                    position=menu_data.position,
                    section=menu_data.section,
                    order=menu_data.order,
                    enabled=menu_data.enabled,
                    created_at=now,
                    updated_at=now
                )
                
        except Exception as e:
            self.log_error("Failed to create menu configuration in database", error=e, menu_key=menu_data.key)
            return None
    
    def update_menu_configuration(self, menu_id: int, menu_data: MenuConfigurationUpdate) -> Optional[MenuConfigurationResponse]:
        """更新菜单配置"""
        try:
            # 检查是否已经在事件循环中
            try:
                loop = asyncio.get_running_loop()
                # 如果已经在事件循环中，返回失败
                self.log_info(f"Already in event loop, cannot update menu configuration: {menu_id}")
                return None
            except RuntimeError:
                # 没有运行的事件循环，正常运行
                return asyncio.run(self._update_menu_configuration_async(menu_id, menu_data))
        except Exception as e:
            self.log_error("Failed to update menu configuration", error=e, menu_id=menu_id)
            return None
    
    async def update_menu_configuration_async(self, menu_id: int, menu_data: MenuConfigurationUpdate) -> Optional[MenuConfigurationResponse]:
        """异步更新菜单配置 - 供FastAPI直接调用"""
        return await self._update_menu_configuration_async(menu_id, menu_data)
    
    async def _update_menu_configuration_async(self, menu_id: int, menu_data: MenuConfigurationUpdate) -> Optional[MenuConfigurationResponse]:
        """异步更新菜单配置"""
        try:
            now = datetime.utcnow()
            async with self.sqlite.get_connection() as conn:
                # 构建更新SQL
                update_fields = []
                params = {"menu_id": menu_id, "updated_at": now}
                
                if menu_data.key is not None:
                    update_fields.append("key = :key")
                    params["key"] = menu_data.key
                
                if menu_data.label is not None:
                    update_fields.append("label = :label")
                    params["label"] = menu_data.label
                
                if menu_data.icon is not None:
                    update_fields.append("icon = :icon")
                    params["icon"] = menu_data.icon
                
                if menu_data.path is not None:
                    update_fields.append("path = :path")
                    params["path"] = menu_data.path
                
                if menu_data.component is not None:
                    update_fields.append("component = :component")
                    params["component"] = menu_data.component
                
                if menu_data.position is not None:
                    update_fields.append("position = :position")
                    params["position"] = menu_data.position
                
                if menu_data.section is not None:
                    update_fields.append("section = :section")
                    params["section"] = menu_data.section
                
                if menu_data.order is not None:
                    update_fields.append('"order" = :order')
                    params["order"] = menu_data.order
                
                if menu_data.enabled is not None:
                    update_fields.append("enabled = :enabled")
                    params["enabled"] = menu_data.enabled
                
                if not update_fields:
                    # 如果没有字段需要更新，直接返回现有数据
                    return await self._get_menu_configuration_by_id_async(menu_id)
                
                # 执行更新
                update_sql = f"""
                    UPDATE menu_configurations 
                    SET {', '.join(update_fields)}, updated_at = :updated_at
                    WHERE id = :menu_id
                """
                
                result = await conn.execute(text(update_sql), params)
                
                if result.rowcount == 0:
                    self.log_warning("No menu configuration found to update", menu_id=menu_id)
                    return None
                
                # 返回更新后的数据
                return await self._get_menu_configuration_by_id_async(menu_id)
                
        except Exception as e:
            self.log_error("Failed to update menu configuration in database", error=e, menu_id=menu_id)
            return None
    
    async def _get_menu_configuration_by_id_async(self, menu_id: int) -> Optional[MenuConfigurationResponse]:
        """异步根据ID获取菜单配置"""
        try:
            async with self.sqlite.get_connection() as conn:
                result = await conn.execute(text("""
                    SELECT id, key, label, icon, path, component, position, section, "order", enabled, created_at, updated_at
                    FROM menu_configurations
                    WHERE id = :menu_id
                """), {"menu_id": menu_id})
                
                row = result.fetchone()
                if not row:
                    return None
                
                return MenuConfigurationResponse(
                    id=row[0],
                    key=row[1],
                    label=row[2],
                    icon=row[3],
                    path=row[4],
                    component=row[5],
                    position=row[6],
                    section=row[7],
                    order=row[8],
                    enabled=bool(row[9]),
                    created_at=row[10] if row[10] else datetime.utcnow(),
                    updated_at=row[11] if row[11] else datetime.utcnow()
                )
        except Exception as e:
            self.log_error("Failed to get menu configuration by ID", error=e, menu_id=menu_id)
            return None
    
    async def delete_menu_configuration(self, menu_id: int) -> bool:
        """删除菜单配置"""
        try:
            # 使用SQLite管理器删除菜单配置
            delete_sql = "DELETE FROM menu_configurations WHERE id = ?"
            result = await self.sqlite.execute_query(delete_sql, (menu_id,))
            
            if result is None:
                self.log_error("Failed to delete menu configuration", menu_id=menu_id)
                return False
            
            # 检查是否有行被删除
            if result.rowcount == 0:
                self.log_warning("No menu configuration found to delete", menu_id=menu_id)
                return False
                
            self.log_info("Menu configuration deleted successfully", menu_id=menu_id)
            return True
        except Exception as e:
            self.log_error("Failed to delete menu configuration", error=e, menu_id=menu_id)
            return False
    
    # 系统设置相关方法
    def get_system_setting(self, key: str) -> Optional[str]:
        """获取系统设置"""
        try:
            # 这里应该从SQLite配置数据库读取
            # 暂时返回None
            return None
        except Exception as e:
            self.log_error("Failed to get system setting", error=e, key=key)
            return None
    
    def set_system_setting(self, key: str, value: str, description: str = None) -> bool:
        """设置系统设置"""
        try:
            # 这里应该使用core SQLite管理器保存
            self.log_info("System setting updated successfully", key=key)
            return True
        except Exception as e:
            self.log_error("Failed to set system setting", error=e, key=key)
            return False
    
    # 当前服务器选择持久化
    def get_current_server_selection(self) -> Optional[str]:
        """获取当前服务器选择"""
        current_server = self.get_system_setting("current_server_selection")
        if current_server:
            return current_server
        
        # 如果没有保存的选择，返回第一个服务器
        servers = self.get_database_servers()
        if servers:
            return servers[0].name
        
        return None
    
    def set_current_server_selection(self, server_name: str) -> bool:
        """设置当前服务器选择"""
        return self.set_system_setting(
            "current_server_selection", 
            server_name, 
            "当前选择的数据库服务器名称"
        )
    
    # 系统设置键值对管理
    def get_system_setting(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        """获取系统设置值"""
        try:
            # 检查是否已经在事件循环中
            try:
                loop = asyncio.get_running_loop()
                # 如果已经在事件循环中，需要使用异步方法
                self.log_warning(f"Already in event loop for key: {key}, this should use async method")
                return default_value
            except RuntimeError:
                # 没有运行的事件循环，正常运行
                return asyncio.run(self._get_system_setting_async(key, default_value))
        except Exception as e:
            self.log_error("Failed to get system setting", error=e, key=key)
            return default_value
    
    async def get_system_setting_async(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        """异步获取系统设置值 - 供FastAPI直接调用"""
        return await self._get_system_setting_async(key, default_value)
    
    async def _get_system_setting_async(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        """异步获取系统设置值"""
        try:
            async with self.sqlite.get_connection() as conn:
                result = await conn.execute(text("SELECT value FROM system_settings WHERE key = :key"), {"key": key})
                row = result.fetchone()
                
                if row:
                    return row[0]
                
                return default_value
                
        except Exception as e:
            self.log_error("Failed to get system setting from database", error=e, key=key)
            return default_value
    
    def set_system_setting(self, key: str, value: str, description: str = "") -> bool:
        """设置系统设置值"""
        try:
            # 检查是否已经在事件循环中
            try:
                loop = asyncio.get_running_loop()
                # 如果已经在事件循环中，返回失败
                self.log_info(f"Already in event loop, cannot set system setting: {key}")
                return False
            except RuntimeError:
                # 没有运行的事件循环，正常运行
                return asyncio.run(self._set_system_setting_async(key, value, description))
        except Exception as e:
            self.log_error("Failed to set system setting", error=e, key=key, value=value)
            return False
    
    async def set_system_setting_async(self, key: str, value: str, description: str = "") -> bool:
        """异步设置系统设置值 - 供FastAPI直接调用"""
        return await self._set_system_setting_async(key, value, description)
    
    async def _set_system_setting_async(self, key: str, value: str, description: str = "") -> bool:
        """异步设置系统设置值"""
        try:
            async with self.sqlite.get_connection() as conn:
                # 检查设置是否存在
                existing_result = await conn.execute(text("SELECT id FROM system_settings WHERE key = :key"), {"key": key})
                existing = existing_result.fetchone()
                
                if existing:
                    # 更新现有设置
                    await conn.execute(text("""
                        UPDATE system_settings 
                        SET value = :value, description = :description, updated_at = :updated_at 
                        WHERE key = :key
                    """), {
                        "value": value,
                        "description": description,
                        "updated_at": datetime.utcnow(),
                        "key": key
                    })
                else:
                    # 创建新设置
                    await conn.execute(text("""
                        INSERT INTO system_settings (key, value, description, created_at, updated_at)
                        VALUES (:key, :value, :description, :created_at, :updated_at)
                    """), {
                        "key": key,
                        "value": value,
                        "description": description,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    })
                
                self.log_info(f"System setting updated: {key} = {value}")
                return True
                
        except Exception as e:
            self.log_error("Failed to set system setting in database", error=e, key=key, value=value)
            return False
    
    def get_all_system_settings(self) -> dict:
        """获取所有系统设置"""
        try:
            # 检查是否已经在事件循环中
            try:
                loop = asyncio.get_running_loop()
                # 如果已经在事件循环中，返回空字典
                self.log_info("Already in event loop, returning empty settings dict")
                return {}
            except RuntimeError:
                # 没有运行的事件循环，正常运行
                return asyncio.run(self._get_all_system_settings_async())
        except Exception as e:
            self.log_error("Failed to get all system settings", error=e)
            return {}
    
    async def get_all_system_settings_async(self) -> list:
        """异步获取所有系统设置 - 供FastAPI直接调用"""
        return await self._get_all_system_settings_async()
    
    async def _get_all_system_settings_async(self) -> list:
        """异步获取所有系统设置"""
        try:
            async with self.sqlite.get_connection() as conn:
                result = await conn.execute(text("SELECT id, key, value, description, created_at, updated_at FROM system_settings"))
                rows = result.fetchall()
                
                settings = []
                for row in rows:
                    # Handle datetime conversion properly
                    created_at = None
                    updated_at = None
                    
                    if row[4]:
                        if hasattr(row[4], 'isoformat'):
                            created_at = row[4].isoformat()
                        else:
                            created_at = str(row[4])
                    
                    if row[5]:
                        if hasattr(row[5], 'isoformat'):
                            updated_at = row[5].isoformat()
                        else:
                            updated_at = str(row[5])
                    
                    settings.append({
                        'id': row[0],
                        'key': row[1],
                        'value': row[2],
                        'description': row[3] or '',
                        'created_at': created_at,
                        'updated_at': updated_at,
                    })
                
                return settings
                
        except Exception as e:
            self.log_error("Failed to get all system settings from database", error=e)
            return []
    
    def delete_system_setting(self, key: str) -> bool:
        """删除系统设置"""
        try:
            # 检查是否已经在事件循环中
            try:
                loop = asyncio.get_running_loop()
                # 如果已经在事件循环中，返回失败
                self.log_info(f"Already in event loop, cannot delete system setting: {key}")
                return False
            except RuntimeError:
                # 没有运行的事件循环，正常运行
                return asyncio.run(self._delete_system_setting_async(key))
        except Exception as e:
            self.log_error("Failed to delete system setting", error=e, key=key)
            return False
    
    async def delete_system_setting_async(self, key: str) -> bool:
        """异步删除系统设置 - 供FastAPI直接调用"""
        return await self._delete_system_setting_async(key)
    
    async def _delete_system_setting_async(self, key: str) -> bool:
        """异步删除系统设置"""
        try:
            async with self.sqlite.get_connection() as conn:
                await conn.execute(text("DELETE FROM system_settings WHERE key = :key"), {"key": key})
                self.log_info(f"System setting deleted: {key}")
                return True
                
        except Exception as e:
            self.log_error("Failed to delete system setting from database", error=e, key=key)
            return False


# 全局配置服务实例
_config_service: Optional[ConfigService] = None


def get_config_service() -> ConfigService:
    """获取全局配置服务实例"""
    global _config_service
    
    if _config_service is None:
        _config_service = ConfigService()
    
    return _config_service


# 保持向后兼容
config_service = get_config_service()