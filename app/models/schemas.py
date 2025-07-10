"""统一的 Pydantic 模型定义 - 重构合并版本"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from uuid import UUID, uuid4
from enum import Enum

from pydantic import BaseModel, Field, field_validator

T = TypeVar('T')


class BaseSchema(BaseModel):
    """基础 Schema 配置"""
    
    model_config = {
        "from_attributes": True,
        "validate_by_name": True,
        "use_enum_values": True,
        "validate_default": True,
        "extra": "forbid",
        "json_encoders": {
            datetime: lambda v: v.isoformat() if v else None
        }
    }


class TimestampMixin(BaseModel):
    """时间戳混入类"""
    
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="更新时间")


# ===================== 查询相关模型 =====================

class QueryType(str, Enum):
    """查询类型"""
    CUSTOM = "custom"      # 自定义SQL查询
    DYNAMIC = "dynamic"    # 动态表查询


class OperatorType(str, Enum):
    """查询操作符"""
    EQUAL = "eq"
    NOT_EQUAL = "ne"
    LIKE = "like"
    NOT_LIKE = "not_like"
    GREATER_THAN = "gt"
    GREATER_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_EQUAL = "lte"
    BETWEEN = "between"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class QueryRequest(BaseSchema):
    """统一的查询请求模型"""
    
    query_type: QueryType = Field(description="查询类型")
    params: Dict[str, Any] = Field(default_factory=dict, description="查询参数")
    sort_by: Optional[str] = Field(default=None, description="排序字段")
    sort_desc: bool = Field(default=False, description="是否降序")
    custom_sql: Optional[str] = Field(default=None, description="自定义SQL查询")
    
    @field_validator('params')
    def clean_params(cls, v):
        """清理参数，移除空值"""
        return {k: val for k, val in v.items() if val is not None and str(val).strip()}


class QueryResponse(BaseSchema):
    """统一的查询响应模型"""
    
    data: Union[List[Dict[str, Any]], List[Dict[str, Union[List[Dict[str, Any]], List[str], int]]]] = Field(description="查询结果或多结果集")
    columns: List[str] = Field(description="列名列表")
    total: int = Field(description="总记录数或结果集数量")
    execution_time: Optional[float] = Field(default=None, description="执行时间(秒)")
    sql: Optional[str] = Field(default=None, description="实际执行的SQL")
    is_multiple: Optional[bool] = Field(default=False, description="是否为多结果集")


class QueryParameter(BaseSchema):
    """查询参数定义"""
    
    name: str = Field(description="参数名")
    type: str = Field(description="参数类型")
    is_required: bool = Field(default=False, description="是否必需")
    label: str = Field(description="显示标签")
    placeholder: Optional[str] = Field(default=None, description="占位符")
    default_value: Optional[Any] = Field(default=None, description="默认值")
    operator_type: str = Field(default="equal", description="操作符类型")
    options: Optional[List[Dict[str, Any]]] = Field(default=None, description="选项列表")
    validation_pattern: Optional[str] = Field(default=None, description="验证正则")
    help_text: Optional[str] = Field(default=None, description="帮助文本")


# ===================== 数据库相关模型 =====================

# DatabaseType 已移除 - 仅支持SQL Server，SQLite仅用于本地配置


class ConnectionStatus(str, Enum):
    """连接状态"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    TESTING = "testing"


class MsDatabaseServer(BaseSchema):
    """微软SQL Server服务器配置 - 仅支持Windows集成认证"""
    
    id: Optional[int] = Field(default=None, description="服务器ID")
    name: str = Field(description="服务器名称/地址", min_length=1, max_length=100)
    port: Optional[int] = Field(default=1433, description="端口号")
    is_enabled: bool = Field(default=True, description="是否启用")
    description: Optional[str] = Field(default=None, description="描述")
    
    @field_validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('服务器名称不能为空')
        return v.strip()
    
    # 默认仅支持SQL Server，无需数据库类型验证


class MsDatabaseConnection(BaseSchema):
    """微软SQL Server连接信息"""
    
    server_name: str = Field(description="服务器名称")
    database_name: Optional[str] = Field(default=None, description="数据库名称")
    status: ConnectionStatus = Field(description="连接状态")
    connection_string: Optional[str] = Field(default=None, description="连接字符串（已脱敏）")
    last_error: Optional[str] = Field(default=None, description="最后错误信息")
    connected_at: Optional[datetime] = Field(default=None, description="连接时间")
    response_time: Optional[float] = Field(default=None, description="响应时间(毫秒)")


# ===================== 历史记录模型 =====================

class QueryHistory(BaseSchema, TimestampMixin):
    """查询历史记录"""
    
    id: Optional[int] = Field(default=None, description="历史ID")
    query_type: QueryType = Field(description="查询类型")
    sql: str = Field(description="执行的SQL")
    params: Dict[str, Any] = Field(default_factory=dict, description="查询参数")
    execution_time: float = Field(description="执行时间(秒)")
    row_count: int = Field(description="返回行数")
    success: bool = Field(description="是否成功")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    user_id: Optional[str] = Field(default="system", description="用户ID")


class SavedQuery(BaseSchema, TimestampMixin):
    """保存的查询"""
    
    id: Optional[int] = Field(default=None, description="查询ID")
    name: str = Field(description="查询名称")
    description: Optional[str] = Field(default=None, description="查询描述")
    query_type: QueryType = Field(description="查询类型")
    sql: str = Field(description="SQL语句")
    params: Dict[str, Any] = Field(default_factory=dict, description="默认参数")
    is_public: bool = Field(default=False, description="是否公开")
    tags: List[str] = Field(default_factory=list, description="标签")
    is_favorite: bool = Field(default=False, description="是否收藏")
    user_id: Optional[str] = Field(default="system", description="用户ID")


# ===================== 配置相关模型 =====================

class MsDatabaseServerConfigCreate(BaseModel):
    """创建微软SQL Server配置"""
    name: str = Field(..., description="服务器名称/地址")
    port: Optional[int] = Field(default=1433, description="端口号")
    description: Optional[str] = Field(default=None, description="描述")


class MsDatabaseServerConfigUpdate(BaseModel):
    """更新微软SQL Server配置"""
    name: Optional[str] = Field(default=None, description="服务器名称/地址")
    port: Optional[int] = Field(default=None, description="端口号")
    is_enabled: Optional[bool] = Field(default=None, description="是否启用")
    description: Optional[str] = Field(default=None, description="描述")


class MsDatabaseServerConfigResponse(BaseModel):
    """微软SQL Server配置响应"""
    id: int
    name: str
    port: int
    is_enabled: bool
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MenuConfigurationCreate(BaseModel):
    """创建菜单配置"""
    key: str = Field(..., description="菜单键值")
    label: str = Field(..., description="显示名称")
    icon: str = Field(..., description="图标名称")
    path: str = Field(..., description="路径")
    component: str = Field(..., description="组件名称")
    position: str = Field("top", description="位置")
    section: str = Field("main", description="分组")
    order: int = Field(1, description="排序值")
    enabled: bool = Field(True, description="是否启用")


class MenuConfigurationUpdate(BaseModel):
    """更新菜单配置"""
    key: Optional[str] = Field(None, description="菜单键值")
    label: Optional[str] = Field(None, description="显示名称")
    icon: Optional[str] = Field(None, description="图标名称")
    path: Optional[str] = Field(None, description="路径")
    component: Optional[str] = Field(None, description="组件名称")
    position: Optional[str] = Field(None, description="位置")
    section: Optional[str] = Field(None, description="分组")
    order: Optional[int] = Field(None, description="排序值")
    enabled: Optional[bool] = Field(None, description="是否启用")


class MenuConfigurationResponse(BaseModel):
    """菜单配置响应"""
    id: int
    key: str
    label: str
    icon: str
    path: str
    component: str
    position: str
    section: str
    order: int
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===================== 通用响应模型 =====================

# QueryResult 已移除 - 使用 ApiResponse 替代


class ApiResponse(BaseSchema, Generic[T]):
    """标准API响应包装器"""
    
    success: bool = Field(description="是否成功")
    data: Optional[T] = Field(default=None, description="响应数据")
    message: Optional[str] = Field(default=None, description="响应消息")
    errors: Optional[List[str]] = Field(default=None, description="错误列表")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="元数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间戳")
    
    @classmethod
    def success_response(cls, data: Optional[T] = None, message: Optional[str] = None, **kwargs) -> "ApiResponse[T]":
        """创建成功响应"""
        return cls(success=True, data=data, message=message, **kwargs)
    
    @classmethod
    def error_response(cls, errors: List[str], message: Optional[str] = None, **kwargs) -> "ApiResponse[T]":
        """创建错误响应"""
        return cls(success=False, errors=errors, message=message, **kwargs)


class ErrorResponse(BaseSchema):
    """标准错误响应"""
    
    error: str = Field(description="错误消息")
    error_code: Optional[str] = Field(default=None, description="错误代码")
    details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="错误时间戳")
    request_id: str = Field(default_factory=lambda: str(uuid4()), description="请求ID")


class HealthCheckResponse(BaseSchema):
    """健康检查响应 - 仅检查本地配置状态"""
    
    status: str = Field(description="健康状态")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="检查时间戳")
    version: str = Field(description="应用版本")
    sqlite_status: Optional[bool] = Field(default=None, description="SQLite配置状态")
    uptime: Optional[float] = Field(default=None, description="运行时间(秒)")


# ===================== 请求相关模型 =====================

class QueryExecutionRequest(BaseSchema):
    """查询执行请求"""
    
    query: str = Field(description="SQL查询", max_length=10000)
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="查询参数")
    include_execution_time: bool = Field(default=True, description="包含执行时间")
    
    @field_validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('查询不能为空')
        return v.strip()


class ExportRequest(BaseSchema):
    """数据导出请求"""
    
    query: QueryRequest = Field(description="查询请求")
    format: str = Field(default="csv", description="导出格式")
    filename: Optional[str] = Field(default=None, description="文件名")
    include_headers: bool = Field(default=True, description="包含表头")
    max_rows: int = Field(default=10000, ge=1, le=100000, description="最大行数")
    
    @field_validator('format')
    def validate_format(cls, v):
        allowed_formats = ['csv', 'json', 'excel']
        if v.lower() not in allowed_formats:
            raise ValueError(f'导出格式必须是: {allowed_formats}')
        return v.lower()


class MsDatabaseConnectionTest(BaseSchema):
    """微软SQL Server连接测试 - 仅支持Windows集成认证"""
    
    server_name: str = Field(description="数据库服务器名称")
    database_name: Optional[str] = Field(default=None, description="数据库名称")



