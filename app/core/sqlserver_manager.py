"""SQL Server动态查询管理器 - 用于执行用户的动态查询"""

import asyncio
from typing import Any, Dict, List, Optional

from sqlalchemy import MetaData, create_engine, text

from app.core.config import DatabaseConfig, settings
from app.core.logging import LoggerMixin, get_logger, log_execution_time

logger = get_logger(__name__)


class SQLServerQueryManager(LoggerMixin):
    """SQL Server动态查询管理器 - 专门用于执行用户的动态查询"""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__()
        self.config = config
        self._sync_engine: Optional[Any] = None
        self._metadata = MetaData()
        
        # 初始化SQL Server引擎
        self._setup_engine()
    
    def _setup_engine(self) -> None:
        """设置SQL Server引擎"""
        try:
            connection_string = self._build_connection_string()
            
            self._sync_engine = create_engine(
                connection_string,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=settings.debug
            )
            
            logger.info("SQL Server query engine created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create SQL Server query engine: {e}")
            raise RuntimeError(f"SQL Server query engine creation failed: {e}")
    
    def _build_connection_string(self) -> str:
        """构建SQL Server连接字符串
        
        注意：仅支持Windows集成认证，不指定数据库名称
        数据库名称应该通过SQL语句指定（USE database_name 或 database.table）
        """
        driver = "ODBC+Driver+17+for+SQL+Server"
        server = self.config.sqlserver_host
        
        # 不指定数据库名称，实现真正的动态数据库连接
        return (
            f"mssql+pyodbc://@{server}?"
            f"driver={driver}"
            f"&Trusted_Connection=yes"
            f"&TrustServerCertificate=yes"
            f"&Encrypt=no"
        )
    
    def generate_connection_string(self, server_name: str) -> str:
        """生成动态SQL Server连接字符串
        
        Args:
            server_name: 服务器名称
            
        Returns:
            SQL Server连接字符串（使用Windows集成认证，无数据库名称）
        """
        return f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server_name};Trusted_Connection=yes;TrustServerCertificate=yes;"
    
    def generate_sqlalchemy_connection_string(self, server_name: str) -> str:
        """生成SQLAlchemy格式的SQL Server连接字符串
        
        Args:
            server_name: 服务器名称
            
        Returns:
            SQLAlchemy格式的SQL Server连接字符串
        """
        driver = "ODBC+Driver+17+for+SQL+Server"
        return (
            f"mssql+pyodbc://@{server_name}?"
            f"driver={driver}"
            f"&Trusted_Connection=yes"
            f"&TrustServerCertificate=yes"
            f"&Encrypt=no"
        )
    
    async def test_connection_with_string(self, connection_string: str) -> bool:
        """使用自定义连接字符串测试数据库连接"""
        try:
            import pyodbc
            
            def _test_sync_connection():
                """同步测试连接"""
                try:
                    self.log_info("Testing SQL Server connection")
                    conn = pyodbc.connect(connection_string, timeout=10)
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    self.log_info(f"Query result: {result}")
                    cursor.close()
                    conn.close()
                    return True
                except Exception as e:
                    self.log_error("Sync connection test failed", error=e)
                    return False
            
            # 在线程池中运行同步测试
            result = await asyncio.get_event_loop().run_in_executor(
                None, _test_sync_connection
            )
            
            if result:
                self.log_info("SQL Server connection test successful")
            else:
                self.log_error("SQL Server connection test failed")
                
            return result
            
        except Exception as e:
            self.log_error("SQL Server connection test failed", error=e)
            return False
    
    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """执行SQL查询并返回结果"""
        if not self._sync_engine:
            raise ValueError("SQL Server sync engine is not available")
        
        def sync_execute():
            with self._sync_engine.connect() as conn:
                result = conn.execute(text(query), parameters or {})
                columns = result.keys()
                rows = result.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_execute)
    
    async def execute_scalar(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Any:
        """执行查询并返回单个标量值"""
        if not self._sync_engine:
            raise ValueError("SQL Server sync engine is not available")
        
        def sync_execute_scalar():
            with self._sync_engine.connect() as conn:
                result = conn.execute(text(query), parameters or {})
                return result.scalar()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_execute_scalar)
    
    async def execute_non_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> int:
        """执行非查询语句（INSERT, UPDATE, DELETE）"""
        if not self._sync_engine:
            raise ValueError("SQL Server sync engine is not available")
        
        def sync_execute_non_query():
            with self._sync_engine.connect() as conn:
                result = conn.execute(text(query), parameters or {})
                return result.rowcount
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_execute_non_query)
    
    async def execute_raw_sql_with_connection(
        self,
        connection_string: str,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """使用指定连接字符串执行原始SQL查询"""
        import pyodbc
        
        def sync_execute_raw():
            conn = pyodbc.connect(connection_string)
            cursor = conn.cursor()
            
            try:
                if parameters:
                    cursor.execute(query, parameters)
                else:
                    cursor.execute(query)
                
                # 获取列名
                columns = [column[0] for column in cursor.description]
                
                # 获取数据
                rows = cursor.fetchall()
                data = [dict(zip(columns, row)) for row in rows]
                
                return data
            finally:
                cursor.close()
                conn.close()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_execute_raw)

    async def execute_multiple_statements_with_connection(
        self,
        connection_string: str,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """使用指定连接字符串执行多条SQL查询并返回所有结果
        
        根据ODBC官方文档，每条语句可能返回：
        1. 结果集（Result Sets）：SELECT、系统目录函数或某些存储过程
        2. 影响行数（Row Counts）：INSERT、UPDATE、DELETE等修改语句
        """
        import pyodbc
        
        def sync_execute_multiple():
            conn = pyodbc.connect(connection_string)
            cursor = conn.cursor()
            
            try:
                if parameters:
                    cursor.execute(query, parameters)
                else:
                    cursor.execute(query)
                
                results = []
                result_index = 0
                
                # 处理第一个结果
                result_index += 1
                if cursor.description:
                    # 这是一个结果集（SELECT等）
                    columns = [column[0] for column in cursor.description]
                    rows = cursor.fetchall()
                    data = [dict(zip(columns, row)) for row in rows]
                    results.append({
                        'type': 'resultset',
                        'index': result_index,
                        'columns': columns,
                        'data': data,
                        'total': len(data),
                        'message': f'查询结果集 {result_index}'
                    })
                else:
                    # 这是一个行数结果（INSERT/UPDATE/DELETE等）
                    row_count = cursor.rowcount
                    results.append({
                        'type': 'rowcount',
                        'index': result_index,
                        'columns': ['affected_rows'],
                        'data': [{'affected_rows': row_count}],
                        'total': 1,
                        'message': f'影响 {row_count} 行'
                    })
                
                # 处理后续结果（使用nextset()遍历）
                while cursor.nextset():
                    result_index += 1
                    if cursor.description:
                        # 结果集
                        columns = [column[0] for column in cursor.description]
                        rows = cursor.fetchall()
                        data = [dict(zip(columns, row)) for row in rows]
                        results.append({
                            'type': 'resultset',
                            'index': result_index,
                            'columns': columns,
                            'data': data,
                            'total': len(data),
                            'message': f'查询结果集 {result_index}'
                        })
                    else:
                        # 行数结果
                        row_count = cursor.rowcount
                        results.append({
                            'type': 'rowcount',
                            'index': result_index,
                            'columns': ['affected_rows'],
                            'data': [{'affected_rows': row_count}],
                            'total': 1,
                            'message': f'影响 {row_count} 行'
                        })
                
                return results
            finally:
                cursor.close()
                conn.close()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_execute_multiple)
    
    async def execute_query_with_server(
        self,
        server_name: str,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """使用指定服务器执行SQL查询"""
        connection_string = self.generate_connection_string(server_name)
        return await self.execute_raw_sql_with_connection(connection_string, query, parameters)

    async def execute_multiple_statements_with_server(
        self,
        server_name: str,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """使用指定服务器执行多条SQL查询并返回所有结果集"""
        connection_string = self.generate_connection_string(server_name)
        return await self.execute_multiple_statements_with_connection(connection_string, query, parameters)
    
    async def test_server_connection(self, server_name: str) -> bool:
        """测试指定服务器的连接"""
        connection_string = self.generate_connection_string(server_name)
        return await self.test_connection_with_string(connection_string)

    def close(self) -> None:
        """关闭SQL Server连接"""
        if self._sync_engine:
            self._sync_engine.dispose()
            self.log_info("SQL Server query engine closed")