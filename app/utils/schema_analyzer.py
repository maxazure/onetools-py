"""SQL表结构分析器"""

import re
import sqlparse
from typing import Dict, List, Set, Optional, Tuple
from sqlalchemy import text
from app.core.logging import LoggerMixin


class SQLSchemaAnalyzer(LoggerMixin):
    """SQL表结构分析器 - 分析SQL语句中的表和视图，获取表结构定义"""
    
    def __init__(self, query_service):
        super().__init__()
        self.query_service = query_service
    
    def extract_table_names(self, sql: str) -> Set[str]:
        """从SQL语句中提取表名和视图名"""
        try:
            # 使用正则表达式简单提取表名
            import re
            
            # 移除注释
            sql_clean = re.sub(r'--.*?\n', '\n', sql)
            sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.DOTALL)
            
            table_names = set()
            
            # 匹配FROM和JOIN后的表名
            # 支持格式：database.schema.table, schema.table, table
            from_pattern = r'\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*){0,2})'
            
            matches = re.finditer(from_pattern, sql_clean, re.IGNORECASE)
            for match in matches:
                table_name = match.group(1).strip()
                if table_name:
                    table_names.add(table_name)
            
            # 清理表名格式 - 移除方括号并统一格式
            cleaned_names = set()
            for name in table_names:
                # 移除方括号
                cleaned_name = name.strip('[]')
                # 如果没有数据库前缀，添加默认数据库前缀
                if '.' not in cleaned_name:
                    cleaned_name = f"OneToolsDb.dbo.{cleaned_name}"
                elif cleaned_name.count('.') == 1:
                    # 只有schema，添加数据库名
                    cleaned_name = f"OneToolsDb.{cleaned_name}"
                cleaned_names.add(cleaned_name)
            
            self.log_info(f"Extracted table names: {cleaned_names}")
            return cleaned_names
            
        except Exception as e:
            self.log_error("Failed to extract table names", error=e)
            return set()
    
    async def get_create_statements(self, table_names: Set[str], server_name: str) -> Dict[str, str]:
        """获取表和视图的CREATE语句"""
        create_statements = {}
        processed_objects = set()  # 避免重复处理
        
        for table_name in table_names:
            await self._process_table_or_view(table_name, server_name, create_statements, processed_objects)
        
        return create_statements
    
    async def _process_table_or_view(self, object_name: str, server_name: str, 
                                   create_statements: Dict[str, str], processed_objects: Set[str]):
        """处理表或视图，递归处理视图中的依赖表"""
        if object_name in processed_objects:
            return
        
        processed_objects.add(object_name)
        
        try:
            # 解析对象名称
            db_name, schema_name, object_name_only = self._parse_object_name(object_name)
            self.log_info(f"Processing object: {object_name} -> db:{db_name}, schema:{schema_name}, table:{object_name_only}")
            
            # 首先检查是否为视图
            view_definition = await self._get_view_definition(db_name, schema_name, object_name_only, server_name)
            if view_definition:
                # 这是一个视图
                create_statements[object_name] = f"CREATE VIEW {object_name} AS\n{view_definition}"
                self.log_info(f"Successfully processed view: {object_name}")
                
                # 分析视图中的依赖表
                dependent_tables = self.extract_table_names(view_definition)
                for dep_table in dependent_tables:
                    await self._process_table_or_view(dep_table, server_name, create_statements, processed_objects)
            else:
                # 这是一个表，获取表结构
                self.log_info(f"Not a view, trying to get table structure for: {object_name}")
                table_structure = await self._get_table_structure(db_name, schema_name, object_name_only, server_name)
                if table_structure:
                    create_statements[object_name] = table_structure
                    self.log_info(f"Successfully processed table: {object_name}")
                else:
                    self.log_warning(f"No table structure returned for: {object_name}")
                    create_statements[object_name] = f"-- Warning: No structure information found for table {object_name}\n-- This may indicate the table does not exist or access is denied"
                    
        except Exception as e:
            self.log_error(f"Failed to process object: {object_name}", error=e)
            error_msg = str(e)
            if "08001" in error_msg or "connection" in error_msg.lower():
                create_statements[object_name] = f"-- Error: Unable to connect to database server for {object_name}\n-- Please ensure the database server is running and accessible"
            else:
                create_statements[object_name] = f"-- Error retrieving definition for {object_name}: {error_msg}"
    
    def _parse_object_name(self, full_name: str) -> Tuple[str, str, str]:
        """解析完整对象名称为数据库名、模式名、对象名"""
        parts = full_name.split('.')
        if len(parts) == 3:
            return parts[0], parts[1], parts[2]
        elif len(parts) == 2:
            return "OneToolsDb", parts[0], parts[1]
        else:
            return "OneToolsDb", "dbo", parts[0]
    
    async def _get_view_definition(self, db_name: str, schema_name: str, view_name: str, server_name: str) -> Optional[str]:
        """获取视图定义"""
        try:
            sql = f"""
                SELECT VIEW_DEFINITION
                FROM {db_name}.INFORMATION_SCHEMA.VIEWS
                WHERE TABLE_SCHEMA = '{schema_name}' AND TABLE_NAME = '{view_name}'
            """
            
            result = await self.query_service.execute_query(sql=sql, server_name=server_name)
            if result.data and len(result.data) > 0:
                return result.data[0].get('VIEW_DEFINITION', '')
            return None
            
        except Exception as e:
            self.log_error(f"Failed to get view definition for {db_name}.{schema_name}.{view_name}", error=e)
            return None
    
    async def _get_table_structure(self, db_name: str, schema_name: str, table_name: str, server_name: str) -> Optional[str]:
        """获取表结构的CREATE语句"""
        try:
            self.log_info(f"Getting table structure for {db_name}.{schema_name}.{table_name} on server {server_name}")
            
            # 获取列信息 - 使用与调试脚本完全相同的SQL
            columns_sql = f"""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    NUMERIC_PRECISION,
                    NUMERIC_SCALE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT
                FROM {db_name}.INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = '{schema_name}' AND TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
            """
            
            self.log_info(f"Executing columns query for {table_name}")
            columns_result = await self.query_service.execute_query(sql=columns_sql, server_name=server_name)
            self.log_info(f"Columns query completed, found {len(columns_result.data) if columns_result.data else 0} columns")
            
            if not columns_result.data:
                self.log_warning(f"No columns found for table {db_name}.{schema_name}.{table_name}")
                return f"-- Warning: No columns found for table {db_name}.{schema_name}.{table_name}\n-- This may indicate the table does not exist"
            
            # 获取主键信息
            pk_sql = f"""
                SELECT COLUMN_NAME
                FROM {db_name}.INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = '{schema_name}' AND TABLE_NAME = '{table_name}'
                AND CONSTRAINT_NAME IN (
                    SELECT CONSTRAINT_NAME
                    FROM {db_name}.INFORMATION_SCHEMA.TABLE_CONSTRAINTS
                    WHERE TABLE_SCHEMA = '{schema_name}' AND TABLE_NAME = '{table_name}'
                    AND CONSTRAINT_TYPE = 'PRIMARY KEY'
                )
                ORDER BY ORDINAL_POSITION
            """
            
            try:
                pk_result = await self.query_service.execute_query(sql=pk_sql, server_name=server_name)
                primary_keys = [row['COLUMN_NAME'] for row in pk_result.data] if pk_result.data else []
                self.log_info(f"Found {len(primary_keys)} primary key columns")
            except Exception as pk_error:
                self.log_warning(f"Failed to get primary keys: {pk_error}")
                primary_keys = []
            
            # 构建CREATE TABLE语句 - 使用与调试脚本完全相同的逻辑
            create_statement = f"CREATE TABLE {db_name}.{schema_name}.{table_name} (\n"
            
            column_definitions = []
            for row in columns_result.data:
                col_name = row['COLUMN_NAME']
                data_type = row['DATA_TYPE'].upper()
                max_length = row['CHARACTER_MAXIMUM_LENGTH']
                precision = row['NUMERIC_PRECISION']
                scale = row['NUMERIC_SCALE']
                is_nullable = row['IS_NULLABLE']
                default_value = row['COLUMN_DEFAULT']
                
                # 构建数据类型
                if data_type in ['VARCHAR', 'NVARCHAR', 'CHAR', 'NCHAR'] and max_length:
                    if max_length == -1:
                        data_type += "(MAX)"
                    else:
                        data_type += f"({max_length})"
                elif data_type in ['DECIMAL', 'NUMERIC'] and precision:
                    if scale:
                        data_type += f"({precision},{scale})"
                    else:
                        data_type += f"({precision})"
                
                # 构建列定义
                col_def = f"    [{col_name}] {data_type}"
                
                # 添加NULL/NOT NULL
                if is_nullable == 'NO':
                    col_def += " NOT NULL"
                
                # 添加默认值
                if default_value:
                    col_def += f" DEFAULT {default_value}"
                
                column_definitions.append(col_def)
            
            create_statement += ",\n".join(column_definitions)
            
            # 添加主键约束
            if primary_keys:
                pk_constraint = f",\n    CONSTRAINT [PK_{table_name}] PRIMARY KEY ({', '.join([f'[{pk}]' for pk in primary_keys])})"
                create_statement += pk_constraint
            
            create_statement += "\n)"
            
            self.log_info(f"Successfully generated CREATE statement for {table_name}")
            return create_statement
            
        except Exception as e:
            self.log_error(f"Failed to get table structure for {db_name}.{schema_name}.{table_name}", error=e)
            return f"-- Error: Failed to get table structure for {db_name}.{schema_name}.{table_name}\n-- Error details: {str(e)}"
    
    async def analyze_sql_schema(self, sql: str, server_name: str) -> str:
        """分析SQL语句中所有表和视图的结构，返回合并的CREATE语句"""
        try:
            self.log_info(f"Starting schema analysis for SQL: {sql[:100]}...")
            
            # 1. 提取表名
            table_names = self.extract_table_names(sql)
            if not table_names:
                return "-- No tables or views found in the SQL statement"
            
            # 2. 获取CREATE语句
            create_statements = await self.get_create_statements(table_names, server_name)
            
            # 3. 合并结果
            result_parts = [
                "-- ======================================",
                "-- SQL Schema Analysis Result",
                "-- ======================================",
                "",
                f"-- Analyzed SQL: {sql[:200]}{'...' if len(sql) > 200 else ''}",
                "",
                f"-- Found {len(create_statements)} database objects:",
                f"-- {', '.join(create_statements.keys())}",
                "",
            ]
            
            for object_name, create_statement in create_statements.items():
                result_parts.extend([
                    f"-- ===== {object_name} =====",
                    create_statement,
                    "",
                ])
            
            result_parts.extend([
                "-- ======================================",
                "-- End of Schema Analysis",
                "-- ======================================"
            ])
            
            final_result = "\n".join(result_parts)
            self.log_info("Schema analysis completed successfully")
            return final_result
            
        except Exception as e:
            self.log_error("Failed to analyze SQL schema", error=e)
            return f"-- Error during schema analysis: {str(e)}"


def get_schema_analyzer(query_service):
    """获取SQL表结构分析器实例"""
    return SQLSchemaAnalyzer(query_service)