"""SQLAlchemy 表定义 - 重构合并版本"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class DatabaseServerConfig(Base):
    """数据库服务器配置表"""
    __tablename__ = "database_servers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, comment="服务器名称")
    order = Column(Integer, default=1, comment="排序值")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class MenuConfiguration(Base):
    """菜单配置表"""
    __tablename__ = "menu_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), nullable=False, unique=True, comment="菜单键值")
    label = Column(String(100), nullable=False, comment="显示名称")
    icon = Column(String(50), nullable=False, comment="图标名称")
    path = Column(String(255), nullable=False, comment="路径")
    component = Column(String(100), nullable=False, comment="组件名称")
    position = Column(String(20), default="top", comment="位置")
    section = Column(String(20), default="main", comment="分组")
    order = Column(Integer, default=1, comment="排序值")
    enabled = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class SystemSettings(Base):
    """系统设置表"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), nullable=False, unique=True, comment="设置键")
    value = Column(Text, comment="设置值")
    description = Column(Text, comment="描述")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class QueryHistory(Base):
    """查询历史记录表"""
    __tablename__ = "query_history"
    
    id = Column(Integer, primary_key=True, index=True)
    query_type = Column(String(50), nullable=False, comment="查询类型")
    sql = Column(Text, nullable=False, comment="执行的SQL")
    params = Column(JSON, default=dict, comment="查询参数")
    execution_time = Column(Float, nullable=False, comment="执行时间(秒)")
    row_count = Column(Integer, nullable=False, comment="返回行数")
    success = Column(Boolean, nullable=False, comment="是否成功")
    error_message = Column(Text, comment="错误信息")
    user_id = Column(String(100), default="system", comment="用户ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class SavedQuery(Base):
    """保存的查询表"""
    __tablename__ = "saved_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="查询名称")
    description = Column(Text, comment="查询描述")
    query_type = Column(String(50), nullable=False, comment="查询类型")
    sql = Column(Text, nullable=False, comment="SQL语句")
    params = Column(JSON, default=dict, comment="默认参数")
    is_public = Column(Boolean, default=False, comment="是否公开")
    tags = Column(JSON, default=list, comment="标签")
    is_favorite = Column(Boolean, default=False, comment="是否收藏")
    user_id = Column(String(100), default="system", comment="用户ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class DatabaseConnection(Base):
    """数据库连接状态表"""
    __tablename__ = "database_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    server_name = Column(String(255), nullable=False, comment="服务器名称")
    database_name = Column(String(255), comment="数据库名称")
    status = Column(String(50), nullable=False, comment="连接状态")
    last_error = Column(Text, comment="最后错误信息")
    connected_at = Column(DateTime, comment="连接时间")
    response_time = Column(Float, comment="响应时间(毫秒)")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class QueryPerformance(Base):
    """查询性能统计表"""
    __tablename__ = "query_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    query_hash = Column(String(64), nullable=False, unique=True, comment="查询哈希")
    sql_text = Column(Text, nullable=False, comment="SQL文本")
    execution_count = Column(Integer, default=0, comment="执行次数")
    total_duration = Column(Float, default=0.0, comment="总执行时间(秒)")
    avg_duration = Column(Float, default=0.0, comment="平均执行时间(秒)")
    max_duration = Column(Float, default=0.0, comment="最大执行时间(秒)")
    min_duration = Column(Float, default=0.0, comment="最小执行时间(秒)")
    total_rows = Column(Integer, default=0, comment="总返回行数")
    avg_rows = Column(Float, default=0.0, comment="平均返回行数")
    error_count = Column(Integer, default=0, comment="错误次数")
    last_execution = Column(DateTime, default=datetime.utcnow, comment="最后执行时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")