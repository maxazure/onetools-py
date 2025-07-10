"""简化的查询服务 - 专注于SQL Server查询执行"""

import time
from typing import Any, Dict, List, Optional

from app.core.database import get_sqlserver_manager
from app.core.logging import LoggerMixin, log_execution_time
from app.models.schemas import QueryResponse


class QueryService(LoggerMixin):
    """简化的查询服务 - 专注于SQL Server查询执行"""
    
    def __init__(self):
        super().__init__()
        self.sqlserver = get_sqlserver_manager()
    
    @log_execution_time("execute_query")
    async def execute_query(
        self, 
        sql: str, 
        parameters: Optional[Dict[str, Any]] = None,
        server_name: Optional[str] = None
    ) -> QueryResponse:
        """执行SQL查询 - 统一接口"""
        try:
            start_time = time.time()
            
            # 根据是否指定服务器选择执行方式
            if server_name:
                data = await self.sqlserver.execute_query_with_server(server_name, sql, parameters)
            else:
                data = await self.sqlserver.execute_query(sql, parameters)
            
            execution_time = time.time() - start_time
            
            # 获取列名
            columns = list(data[0].keys()) if data else []
            
            return QueryResponse(
                data=data,
                columns=columns,
                total=len(data),
                execution_time=execution_time,
                sql=sql
            )
            
        except Exception as e:
            self.log_error("Query execution failed", error=e)
            raise
    
    async def validate_sql_safety(self, sql: str) -> Dict[str, Any]:
        """简单的SQL安全验证"""
        try:
            sql_upper = sql.upper().strip()
            
            # 检查危险的SQL关键字
            dangerous_keywords = [
                "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", 
                "TRUNCATE", "EXEC", "EXECUTE", "SP_", "XP_"
            ]
            
            found_dangerous = []
            for keyword in dangerous_keywords:
                if keyword in sql_upper:
                    found_dangerous.append(keyword)
            
            is_safe = len(found_dangerous) == 0
            
            return {
                "is_safe": is_safe,
                "dangerous_keywords": found_dangerous,
                "message": "SQL validation completed",
                "recommendations": [] if is_safe else ["Use SELECT statements only"]
            }
            
        except Exception as e:
            self.log_error("SQL validation failed", error=e)
            return {
                "is_safe": False,
                "dangerous_keywords": [],
                "message": f"Validation error: {str(e)}",
                "recommendations": ["Please check SQL syntax"]
            }
    
    async def get_table_columns(self, table_name: str, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取表列信息 - 用于动态返回列名和类型"""
        try:
            if database:
                sql = f"""
                SELECT 
                    COLUMN_NAME as name,
                    DATA_TYPE as type,
                    IS_NULLABLE as nullable,
                    COLUMN_DEFAULT as default_value
                FROM [{database}].INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
                """
            else:
                sql = f"""
                SELECT 
                    COLUMN_NAME as name,
                    DATA_TYPE as type,
                    IS_NULLABLE as nullable,
                    COLUMN_DEFAULT as default_value
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
                """
            
            result = await self.sqlserver.execute_query(sql)
            return result
        except Exception as e:
            self.log_error("Failed to get table columns", error=e)
            return []


# 全局查询服务实例
_query_service: Optional[QueryService] = None


def get_query_service() -> QueryService:
    """获取全局查询服务实例"""
    global _query_service
    
    if _query_service is None:
        _query_service = QueryService()
    
    return _query_service