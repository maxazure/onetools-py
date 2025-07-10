"""简化的查询服务 - 专注于SQL Server查询执行"""

import time
import sqlparse
from typing import Any, Dict, List, Optional

from app.core.database import get_sqlserver_manager
from app.core.logging import LoggerMixin, log_execution_time
from app.models.schemas import QueryResponse


class QueryService(LoggerMixin):
    """简化的查询服务 - 专注于SQL Server查询执行"""
    
    def __init__(self):
        super().__init__()
        self.sqlserver = get_sqlserver_manager()
    
    def _parse_sql_statements(self, sql: str) -> List[str]:
        """使用 sqlparse 解析SQL，返回独立的语句列表"""
        if not sql or not sql.strip():
            return []
        
        # 首先尝试使用 sqlparse 分割（基于分号）
        raw_statements = sqlparse.split(sql)
        
        # 过滤掉空语句
        statements = []
        for stmt in raw_statements:
            cleaned_stmt = stmt.strip()
            if cleaned_stmt:
                statements.append(cleaned_stmt)
        
        # 如果只有一个语句但包含多个 SELECT/INSERT/UPDATE/DELETE 关键字
        # 说明可能是没有分号分隔的多条语句
        if len(statements) == 1:
            single_stmt = statements[0]
            # 检查是否包含多个SQL关键字（简单检测）
            if self._contains_multiple_statements(single_stmt):
                # 尝试按行分割并重新解析
                lines = single_stmt.split('\n')
                potential_statements = []
                current_stmt = ""
                
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('--'):
                        continue
                    
                    # 检查是否是新语句的开始
                    if self._is_statement_start(line) and current_stmt.strip():
                        # 保存之前的语句
                        potential_statements.append(current_stmt.strip())
                        current_stmt = line
                    else:
                        current_stmt += " " + line if current_stmt else line
                
                # 添加最后一个语句
                if current_stmt.strip():
                    potential_statements.append(current_stmt.strip())
                
                # 如果成功分割出多个语句，使用分割结果
                if len(potential_statements) > 1:
                    statements = potential_statements
        
        return statements
    
    def _contains_multiple_statements(self, sql: str) -> bool:
        """检查SQL是否包含多个语句（简单检测）"""
        sql_upper = sql.upper()
        statement_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
        
        count = 0
        for keyword in statement_keywords:
            # 使用简单的单词边界检查
            import re
            matches = re.findall(r'\b' + keyword + r'\b', sql_upper)
            count += len(matches)
        
        return count > 1
    
    def _is_statement_start(self, line: str) -> bool:
        """检查行是否是新语句的开始"""
        line_upper = line.upper().strip()
        statement_starters = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'WITH', 'EXEC', 'EXECUTE']
        
        for starter in statement_starters:
            if line_upper.startswith(starter + ' ') or line_upper == starter:
                return True
        
        return False

    def _get_statement_type(self, statement: str) -> str:
        """获取SQL语句类型"""
        statement = statement.strip().upper()
        
        # 移除前导注释
        while statement.startswith('--'):
            lines = statement.split('\n', 1)
            if len(lines) > 1:
                statement = lines[1].strip().upper()
            else:
                statement = ""
                break
        
        if not statement:
            return "UNKNOWN"
        
        # 获取第一个关键字
        first_word = statement.split()[0] if statement.split() else ""
        
        if first_word in ["SELECT", "WITH"]:
            return "SELECT"
        elif first_word in ["INSERT", "UPDATE", "DELETE"]:
            return "MODIFY"
        elif first_word in ["CREATE", "DROP", "ALTER"]:
            return "DDL"
        elif first_word in ["EXEC", "EXECUTE", "CALL"]:
            return "PROCEDURE"
        else:
            return "OTHER"

    def _should_use_multiple_processing(self, sql: str) -> bool:
        """判断是否应该使用多结果集处理"""
        statements = self._parse_sql_statements(sql)
        
        if len(statements) <= 1:
            return False
        
        # 如果有多条语句，都使用多结果集处理
        # 这样可以正确处理所有情况：
        # 1. 多条SELECT -> 多个结果集
        # 2. 多条INSERT/UPDATE/DELETE -> 多个行数结果
        # 3. 混合语句 -> 结果集+行数结果混合
        return True

    @log_execution_time("execute_query")
    async def execute_query(
        self, 
        sql: str, 
        parameters: Optional[Dict[str, Any]] = None,
        server_name: Optional[str] = None
    ) -> QueryResponse:
        """执行SQL查询 - 统一接口，支持单条和多条语句"""
        try:
            start_time = time.time()
            
            # 检测是否需要使用多结果集处理
            is_multiple = self._should_use_multiple_processing(sql)
            
            if is_multiple:
                # 执行多条语句
                if server_name:
                    results = await self.sqlserver.execute_multiple_statements_with_server(server_name, sql, parameters)
                else:
                    results = await self.sqlserver.execute_multiple_statements_with_connection(
                        self.sqlserver.generate_connection_string(self.sqlserver.config.sqlserver_host), 
                        sql, 
                        parameters
                    )
                
                execution_time = time.time() - start_time
                
                # 返回多结果集响应
                return QueryResponse(
                    data=results,  # 包含多个结果集的列表
                    columns=[],    # 多结果集时不使用单一columns字段
                    total=len(results),  # 结果集数量
                    execution_time=execution_time,
                    sql=sql,
                    is_multiple=True
                )
            else:
                # 执行单条语句
                statements = self._parse_sql_statements(sql)
                if len(statements) == 1:
                    statement_type = self._get_statement_type(statements[0])
                    
                    if statement_type == "MODIFY":
                        # 单条修改语句（INSERT/UPDATE/DELETE）使用多结果集处理以获取行数
                        if server_name:
                            results = await self.sqlserver.execute_multiple_statements_with_server(server_name, sql, parameters)
                        else:
                            results = await self.sqlserver.execute_multiple_statements_with_connection(
                                self.sqlserver.generate_connection_string(self.sqlserver.config.sqlserver_host), 
                                sql, 
                                parameters
                            )
                        
                        execution_time = time.time() - start_time
                        
                        # 返回多结果集格式，但标记为单条语句
                        return QueryResponse(
                            data=results,
                            columns=[],
                            total=len(results),
                            execution_time=execution_time,
                            sql=sql,
                            is_multiple=True  # 虽然是单条语句，但使用多结果集格式显示行数
                        )
                    else:
                        # 单条SELECT语句，使用原有逻辑
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
                            sql=sql,
                            is_multiple=False
                        )
                else:
                    # 空语句或解析失败
                    execution_time = time.time() - start_time
                    return QueryResponse(
                        data=[],
                        columns=[],
                        total=0,
                        execution_time=execution_time,
                        sql=sql,
                        is_multiple=False
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