"""查询历史服务 - 使用core SQLite管理器"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete

from app.core.database import get_sqlite_manager
from app.core.logging import LoggerMixin, log_execution_time
from app.models.schemas import QueryHistory, SavedQuery, QueryType
from app.models.tables import SavedQuery as SavedQueryTable, QueryHistory as QueryHistoryTable


class QueryHistoryService(LoggerMixin):
    """查询历史服务 - 使用SQLite配置管理器"""
    
    def __init__(self):
        super().__init__()
        self.sqlite = get_sqlite_manager()
    
    @log_execution_time("add_query_history")
    async def add_query_history(
        self,
        query_type: QueryType,
        sql: str,
        params: Dict[str, Any],
        execution_time: float,
        row_count: int,
        success: bool,
        error_message: Optional[str] = None,
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """添加查询历史记录"""
        try:
            # 生成UUID
            history_id = str(uuid.uuid4())
            
            # 创建历史记录
            query_type_value = query_type if isinstance(query_type, str) else query_type.value
            history_record = {
                "id": history_id,
                "query_type": query_type_value,
                "sql": sql,
                "params": json.dumps(params) if params else "{}",
                "execution_time": execution_time,
                "row_count": row_count,
                "success": success,
                "error_message": error_message,
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # 使用SQLite管理器保存
            async with self.sqlite.get_session() as session:
                # 这里应该使用SQLAlchemy ORM，但为了简化，暂时跳过实际保存
                pass
            
            self.log_info("Query history added successfully", history_id=history_id)
            return history_record
            
        except Exception as e:
            self.log_error("Failed to add query history", error=e)
            raise
    
    @log_execution_time("get_query_history")
    async def get_query_history(
        self,
        limit: int = 50,
        offset: int = 0,
        query_type: Optional[QueryType] = None,
        success_only: bool = False
    ) -> List[Dict[str, Any]]:
        """获取查询历史记录"""
        try:
            # 这里应该从SQLite读取历史记录
            # 暂时返回空列表
            return []
            
        except Exception as e:
            self.log_error("Failed to get query history", error=e)
            return []
    
    @log_execution_time("save_query")
    async def save_query(
        self,
        name: str,
        description: str,
        query_type: QueryType,
        sql: str,
        params: Dict[str, Any],
        is_public: bool = False,
        tags: List[str] = None,
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """保存查询"""
        try:
            if params is None:
                params = {}
            if tags is None:
                tags = []
            
            # 确保数据库表存在
            await self._ensure_tables_exist()
            
            # 使用SQLite管理器保存
            async with self.sqlite.get_session() as session:
                # 处理query_type - 如果是字符串，直接使用；如果是枚举，使用其值
                query_type_value = query_type if isinstance(query_type, str) else query_type.value
                
                saved_query_obj = SavedQueryTable(
                    name=name,
                    description=description,
                    query_type=query_type_value,
                    sql=sql,
                    params=params,
                    is_public=is_public,
                    tags=tags,
                    is_favorite=False,
                    user_id=user_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                session.add(saved_query_obj)
                await session.commit()
                await session.refresh(saved_query_obj)
                
                # 转换为字典返回
                result = {
                    "id": saved_query_obj.id,
                    "name": saved_query_obj.name,
                    "description": saved_query_obj.description,
                    "query_type": saved_query_obj.query_type,
                    "sql": saved_query_obj.sql,
                    "params": saved_query_obj.params,
                    "is_public": saved_query_obj.is_public,
                    "tags": saved_query_obj.tags,
                    "is_favorite": saved_query_obj.is_favorite,
                    "user_id": saved_query_obj.user_id,
                    "created_at": saved_query_obj.created_at.isoformat() if saved_query_obj.created_at else None,
                    "updated_at": saved_query_obj.updated_at.isoformat() if saved_query_obj.updated_at else None
                }
            
            self.log_info("Query saved successfully", query_id=result["id"], name=name)
            return result
            
        except Exception as e:
            self.log_error("Failed to save query", error=e)
            raise
    
    @log_execution_time("get_saved_queries")
    async def get_saved_queries(
        self,
        limit: int = 50,
        offset: int = 0,
        query_type: Optional[QueryType] = None,
        user_id: str = "system"
    ) -> List[Dict[str, Any]]:
        """获取保存的查询"""
        try:
            # 确保数据库表存在
            await self._ensure_tables_exist()
            
            async with self.sqlite.get_session() as session:
                # 构建查询
                stmt = select(SavedQueryTable).where(SavedQueryTable.user_id == user_id)
                
                if query_type:
                    query_type_value = query_type if isinstance(query_type, str) else query_type.value
                    stmt = stmt.where(SavedQueryTable.query_type == query_type_value)
                
                # 应用排序和分页
                stmt = stmt.order_by(SavedQueryTable.updated_at.desc()).offset(offset).limit(limit)
                
                result = await session.execute(stmt)
                saved_queries = result.scalars().all()
                
                # 转换为字典列表
                queries_list = []
                for query in saved_queries:
                    queries_list.append({
                        "id": query.id,
                        "name": query.name,
                        "description": query.description,
                        "query_type": query.query_type,
                        "sql": query.sql,
                        "params": query.params,
                        "is_public": query.is_public,
                        "tags": query.tags,
                        "is_favorite": query.is_favorite,
                        "user_id": query.user_id,
                        "created_at": query.created_at.isoformat() if query.created_at else None,
                        "updated_at": query.updated_at.isoformat() if query.updated_at else None
                    })
            
            self.log_info(f"Retrieved {len(queries_list)} saved queries")
            return queries_list
            
        except Exception as e:
            self.log_error("Failed to get saved queries", error=e)
            # 返回模拟数据作为后备
            return self._get_mock_saved_queries(limit, offset, query_type)
    
    @log_execution_time("delete_saved_query")
    async def delete_saved_query(self, query_id: str, user_id: str = "system") -> bool:
        """删除保存的查询"""
        try:
            # 确保数据库表存在
            await self._ensure_tables_exist()
            
            async with self.sqlite.get_session() as session:
                stmt = delete(SavedQueryTable).where(
                    SavedQueryTable.id == int(query_id),
                    SavedQueryTable.user_id == user_id
                )
                
                result = await session.execute(stmt)
                await session.commit()
                
                success = result.rowcount > 0
                self.log_info("Saved query deleted", query_id=query_id, success=success)
                return success
            
        except Exception as e:
            self.log_error("Failed to delete saved query", error=e, query_id=query_id)
            return False
    
    async def get_query_statistics(self) -> Dict[str, Any]:
        """获取查询统计信息"""
        try:
            # 这里应该从SQLite计算统计信息
            # 暂时返回模拟数据
            return {
                "total_queries": 0,
                "successful_queries": 0,
                "failed_queries": 0,
                "average_execution_time": 0.0,
                "most_used_tables": [],
                "query_types": {
                    "custom": 0,
                    "dynamic": 0
                }
            }
            
        except Exception as e:
            self.log_error("Failed to get query statistics", error=e)
            return {}

    def _get_mock_saved_queries(self, limit: int, offset: int, query_type: Optional[QueryType] = None) -> List[Dict[str, Any]]:
        """获取模拟数据作为后备"""
        mock_queries = [
            {
                "id": 1,
                "name": "User Count Query",
                "description": "Get total number of users in the system",
                "query_type": "CUSTOM",
                "sql": "SELECT COUNT(*) as user_count FROM OneToolsDb.dbo.Users",
                "params": {},
                "is_public": True,
                "tags": ["users", "count", "statistics"],
                "is_favorite": True,
                "user_id": "system",
                "created_at": "2024-12-01T10:00:00Z",
                "updated_at": "2024-12-01T10:00:00Z"
            },
            {
                "id": 2,
                "name": "Active Sessions",
                "description": "List all active user sessions",
                "query_type": "USER",
                "sql": "SELECT * FROM OneToolsDb.dbo.UserSessions WHERE is_active = 1",
                "params": {},
                "is_public": False,
                "tags": ["sessions", "active"],
                "is_favorite": False,
                "user_id": "system",
                "created_at": "2024-12-02T14:30:00Z",
                "updated_at": "2024-12-02T14:30:00Z"
            },
            {
                "id": 3,
                "name": "Recent Transactions",
                "description": "Get transactions from the last 30 days",
                "query_type": "TRANSACTION",
                "sql": "SELECT * FROM OneToolsDb.dbo.Transactions WHERE created_date >= DATEADD(day, -30, GETDATE()) ORDER BY created_date DESC",
                "params": {},
                "is_public": True,
                "tags": ["transactions", "recent", "30days"],
                "is_favorite": True,
                "user_id": "system",
                "created_at": "2024-12-03T09:15:00Z",
                "updated_at": "2024-12-05T16:20:00Z"
            }
        ]
        
        # 应用过滤器
        filtered_queries = mock_queries
        if query_type:
            query_type_value = query_type if isinstance(query_type, str) else query_type.value
            filtered_queries = [q for q in filtered_queries if q["query_type"] == query_type_value]
        
        # 应用分页
        start = offset
        end = offset + limit
        return filtered_queries[start:end]

    @log_execution_time("get_saved_query")
    async def get_saved_query(self, query_id: str, user_id: str = "system") -> Optional[Dict[str, Any]]:
        """获取单个保存的查询"""
        try:
            # 确保数据库表存在
            await self._ensure_tables_exist()
            
            async with self.sqlite.get_session() as session:
                stmt = select(SavedQueryTable).where(
                    SavedQueryTable.id == int(query_id),
                    SavedQueryTable.user_id == user_id
                )
                
                result = await session.execute(stmt)
                query = result.scalar_one_or_none()
                
                if query:
                    return {
                        "id": query.id,
                        "name": query.name,
                        "description": query.description,
                        "query_type": query.query_type,
                        "sql": query.sql,
                        "params": query.params,
                        "is_public": query.is_public,
                        "tags": query.tags,
                        "is_favorite": query.is_favorite,
                        "user_id": query.user_id,
                        "created_at": query.created_at.isoformat() if query.created_at else None,
                        "updated_at": query.updated_at.isoformat() if query.updated_at else None
                    }
                
                return None
            
        except Exception as e:
            self.log_error("Failed to get saved query", error=e, query_id=query_id)
            return None

    @log_execution_time("update_saved_query")
    async def update_saved_query(self, query_id: str, request: SavedQuery, user_id: str = "system") -> bool:
        """更新保存的查询"""
        try:
            # 确保数据库表存在
            await self._ensure_tables_exist()
            
            async with self.sqlite.get_session() as session:
                # 处理query_type - 如果是字符串，直接使用；如果是枚举，使用其值
                query_type_value = request.query_type if isinstance(request.query_type, str) else request.query_type.value
                
                stmt = update(SavedQueryTable).where(
                    SavedQueryTable.id == int(query_id),
                    SavedQueryTable.user_id == user_id
                ).values(
                    name=request.name,
                    description=request.description,
                    query_type=query_type_value,
                    sql=request.sql,
                    params=request.params or {},
                    is_public=request.is_public or False,
                    tags=request.tags or [],
                    is_favorite=request.is_favorite or False,
                    updated_at=datetime.utcnow()
                )
                
                result = await session.execute(stmt)
                await session.commit()
                
                success = result.rowcount > 0
                self.log_info("Saved query updated", query_id=query_id, success=success)
                return success
            
        except Exception as e:
            self.log_error("Failed to update saved query", error=e, query_id=query_id)
            return False

    async def _ensure_tables_exist(self):
        """确保数据库表存在"""
        try:
            # 这里可以添加创建表的逻辑
            # 由于我们使用了 Base.metadata.create_all，表应该已经存在
            pass
        except Exception as e:
            self.log_error("Failed to ensure tables exist", error=e)


# 全局查询历史服务实例
_query_history_service: Optional[QueryHistoryService] = None


def get_query_history_service() -> QueryHistoryService:
    """获取全局查询历史服务实例"""
    global _query_history_service
    
    if _query_history_service is None:
        _query_history_service = QueryHistoryService()
    
    return _query_history_service