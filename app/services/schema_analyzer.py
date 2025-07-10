"""表结构分析器 - 分析SQL语句中的表/视图结构"""

import re
import asyncio
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass

from app.core.database import get_sqlserver_manager
from app.core.logging import LoggerMixin


@dataclass
class TableInfo:
    """表/视图信息"""
    name: str
    schema: str
    database: str
    full_name: str
    object_type: str  # 'TABLE' or 'VIEW'
    columns: List[Dict[str, Any]]
    view_definition: Optional[str] = None
    referenced_tables: Optional[Set[str]] = None


@dataclass
class SchemaAnalysisResult:
    """表结构分析结果"""
    tables: List[TableInfo]
    views: List[TableInfo]
    all_referenced_tables: Set[str]
    formatted_output: str
    analysis_summary: str


class SchemaAnalyzer(LoggerMixin):
    """表结构分析器 - 分析SQL语句中包含的所有表和视图的结构"""
    
    def __init__(self):
        super().__init__()
        self.sqlserver = get_sqlserver_manager()
        self._analyzed_objects: Set[str] = set()  # 防止循环分析
        
    async def analyze_sql_schema(self, sql: str, server_name: Optional[str] = None) -> SchemaAnalysisResult:
        """分析SQL语句中的表结构"""
        try:
            self.log_info("开始分析SQL语句中的表结构")
            
            # 重置状态
            self._analyzed_objects.clear()
            
            # 1. 提取SQL中的表名和视图名
            table_references = self._extract_table_references(sql)
            
            if not table_references:
                return SchemaAnalysisResult(
                    tables=[],
                    views=[],
                    all_referenced_tables=set(),
                    formatted_output="未找到任何表或视图引用",
                    analysis_summary="SQL语句中未包含表或视图引用"
                )
            
            # 2. 获取所有表和视图的详细信息
            tables = []
            views = []
            all_referenced_tables = set()
            
            for table_ref in table_references:
                table_info = await self._get_table_info(table_ref, server_name)
                if table_info:
                    all_referenced_tables.add(table_info.full_name)
                    
                    if table_info.object_type == 'TABLE':
                        tables.append(table_info)
                    elif table_info.object_type == 'VIEW':
                        views.append(table_info)
                        
                        # 3. 递归分析视图内的表
                        if table_info.view_definition:
                            nested_tables = await self._analyze_view_dependencies(
                                table_info.view_definition, 
                                server_name
                            )
                            for nested_table in nested_tables:
                                all_referenced_tables.add(nested_table.full_name)
                                if nested_table.object_type == 'TABLE':
                                    # 避免重复添加
                                    if not any(t.full_name == nested_table.full_name for t in tables):
                                        tables.append(nested_table)
                                elif nested_table.object_type == 'VIEW':
                                    if not any(v.full_name == nested_table.full_name for v in views):
                                        views.append(nested_table)
            
            # 4. 生成格式化输出
            formatted_output = self._format_schema_output(tables, views)
            analysis_summary = self._generate_analysis_summary(tables, views, all_referenced_tables)
            
            self.log_info(f"表结构分析完成：找到{len(tables)}个表，{len(views)}个视图")
            
            return SchemaAnalysisResult(
                tables=tables,
                views=views,
                all_referenced_tables=all_referenced_tables,
                formatted_output=formatted_output,
                analysis_summary=analysis_summary
            )
            
        except Exception as e:
            self.log_error("表结构分析失败", error=e)
            return SchemaAnalysisResult(
                tables=[],
                views=[],
                all_referenced_tables=set(),
                formatted_output=f"分析失败: {str(e)}",
                analysis_summary=f"分析过程中发生错误: {str(e)}"
            )
    
    def _extract_table_references(self, sql: str) -> List[str]:
        """提取SQL语句中的表名引用"""
        try:
            # 清理SQL语句
            sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)  # 移除行注释
            sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)  # 移除块注释
            
            table_references = []
            
            # 简化的表名提取方法
            # 匹配 FROM、JOIN、INTO、UPDATE、DELETE FROM 后面的表名
            patterns = [
                r'FROM\s+(\[?[\w]+\]?(?:\.\[?[\w]+\]?(?:\.\[?[\w]+\]?)?)?)',
                r'JOIN\s+(\[?[\w]+\]?(?:\.\[?[\w]+\]?(?:\.\[?[\w]+\]?)?)?)',
                r'INTO\s+(\[?[\w]+\]?(?:\.\[?[\w]+\]?(?:\.\[?[\w]+\]?)?)?)',
                r'UPDATE\s+(\[?[\w]+\]?(?:\.\[?[\w]+\]?(?:\.\[?[\w]+\]?)?)?)',
                r'DELETE\s+FROM\s+(\[?[\w]+\]?(?:\.\[?[\w]+\]?(?:\.\[?[\w]+\]?)?)?)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, sql, re.IGNORECASE)
                for match in matches:
                    # 清理方括号
                    clean_match = re.sub(r'[\[\]]', '', match)
                    if clean_match:
                        table_references.append(clean_match)
            
            # 去重
            return list(set(table_references))
            
        except Exception as e:
            self.log_error("提取表名引用失败", error=e)
            return []
    
    async def _get_table_info(self, table_ref: str, server_name: Optional[str] = None) -> Optional[TableInfo]:
        """获取表或视图的详细信息"""
        try:
            # 解析表名
            parts = table_ref.split('.')
            if len(parts) == 3:
                database, schema, table = parts
            elif len(parts) == 2:
                database, schema, table = None, parts[0], parts[1]
            else:
                database, schema, table = None, 'dbo', parts[0]
            
            full_name = f"{database}.{schema}.{table}" if database else f"{schema}.{table}"
            
            # 防止重复分析
            if full_name in self._analyzed_objects:
                return None
            self._analyzed_objects.add(full_name)
            
            # 查询对象信息
            object_info_sql = f"""
            SELECT 
                o.name as object_name,
                s.name as schema_name,
                DB_NAME() as database_name,
                o.type_desc as object_type,
                CASE WHEN o.type = 'V' THEN 
                    OBJECT_DEFINITION(o.object_id) 
                ELSE NULL END as view_definition
            FROM sys.objects o
            JOIN sys.schemas s ON o.schema_id = s.schema_id
            WHERE o.name = '{table}' 
            AND s.name = '{schema}'
            AND o.type IN ('U', 'V')  -- 用户表和视图
            """
            
            if database:
                object_info_sql = f"USE [{database}];\n" + object_info_sql
            
            object_info = await self._execute_query(object_info_sql, server_name)
            
            if not object_info:
                self.log_warning(f"未找到表或视图: {full_name}")
                return None
            
            obj_info = object_info[0]
            
            # 获取列信息
            columns = await self._get_table_columns(database, schema, table, server_name)
            
            return TableInfo(
                name=obj_info['object_name'],
                schema=obj_info['schema_name'],
                database=obj_info['database_name'],
                full_name=f"{obj_info['database_name']}.{obj_info['schema_name']}.{obj_info['object_name']}",
                object_type='TABLE' if obj_info['object_type'] == 'USER_TABLE' else 'VIEW',
                columns=columns,
                view_definition=obj_info.get('view_definition'),
                referenced_tables=set()
            )
            
        except Exception as e:
            self.log_error(f"获取表信息失败: {table_ref}", error=e)
            return None
    
    async def _get_table_columns(self, database: Optional[str], schema: str, table: str, server_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取表的列信息"""
        try:
            columns_sql = f"""
            SELECT 
                c.COLUMN_NAME as column_name,
                c.DATA_TYPE as data_type,
                c.CHARACTER_MAXIMUM_LENGTH as max_length,
                c.NUMERIC_PRECISION as precision,
                c.NUMERIC_SCALE as scale,
                c.IS_NULLABLE as is_nullable,
                c.COLUMN_DEFAULT as default_value,
                c.ORDINAL_POSITION as ordinal_position,
                CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 'YES' ELSE 'NO' END as is_primary_key
            FROM INFORMATION_SCHEMA.COLUMNS c
            LEFT JOIN (
                SELECT ku.TABLE_CATALOG, ku.TABLE_SCHEMA, ku.TABLE_NAME, ku.COLUMN_NAME
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku 
                    ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
                WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
            ) pk ON c.TABLE_CATALOG = pk.TABLE_CATALOG 
                AND c.TABLE_SCHEMA = pk.TABLE_SCHEMA 
                AND c.TABLE_NAME = pk.TABLE_NAME 
                AND c.COLUMN_NAME = pk.COLUMN_NAME
            WHERE c.TABLE_NAME = '{table}' 
            AND c.TABLE_SCHEMA = '{schema}'
            """
            
            if database:
                columns_sql = f"USE [{database}];\n" + columns_sql
                
            columns_sql += " ORDER BY c.ORDINAL_POSITION"
            
            return await self._execute_query(columns_sql, server_name)
            
        except Exception as e:
            self.log_error(f"获取列信息失败: {database}.{schema}.{table}", error=e)
            return []
    
    async def _analyze_view_dependencies(self, view_definition: str, server_name: Optional[str] = None) -> List[TableInfo]:
        """递归分析视图内的表依赖"""
        try:
            if not view_definition:
                return []
            
            # 从视图定义中提取表引用
            table_references = self._extract_table_references(view_definition)
            
            nested_tables = []
            for table_ref in table_references:
                table_info = await self._get_table_info(table_ref, server_name)
                if table_info:
                    nested_tables.append(table_info)
                    
                    # 如果是视图，递归分析
                    if table_info.object_type == 'VIEW' and table_info.view_definition:
                        deeper_tables = await self._analyze_view_dependencies(
                            table_info.view_definition, 
                            server_name
                        )
                        nested_tables.extend(deeper_tables)
            
            return nested_tables
            
        except Exception as e:
            self.log_error("分析视图依赖失败", error=e)
            return []
    
    def _format_schema_output(self, tables: List[TableInfo], views: List[TableInfo]) -> str:
        """格式化输出表结构信息"""
        output = []
        
        # 添加分析摘要
        output.append("=" * 80)
        output.append("SQL 表结构分析报告")
        output.append("=" * 80)
        output.append(f"分析时间: {self._get_current_time()}")
        output.append(f"发现表数量: {len(tables)}")
        output.append(f"发现视图数量: {len(views)}")
        output.append("")
        
        # 输出表结构
        if tables:
            output.append("📋 表结构信息")
            output.append("-" * 40)
            for i, table in enumerate(tables, 1):
                output.append(f"\n{i}. {table.full_name} (表)")
                output.append(f"   数据库: {table.database}")
                output.append(f"   架构: {table.schema}")
                output.append(f"   表名: {table.name}")
                output.append(f"   列数: {len(table.columns)}")
                output.append("")
                
                # 列信息
                if table.columns:
                    output.append("   列信息:")
                    output.append("   " + "-" * 60)
                    output.append(f"   {'列名':<20} {'数据类型':<15} {'可空':<5} {'主键':<5} {'默认值':<15}")
                    output.append("   " + "-" * 60)
                    
                    for col in table.columns:
                        col_type = col['data_type']
                        if col['max_length'] and col['data_type'] in ['varchar', 'nvarchar', 'char', 'nchar']:
                            col_type += f"({col['max_length']})"
                        elif col['precision'] and col['data_type'] in ['decimal', 'numeric']:
                            col_type += f"({col['precision']},{col['scale'] or 0})"
                        
                        output.append(f"   {col['column_name']:<20} {col_type:<15} {col['is_nullable']:<5} {col['is_primary_key']:<5} {col['default_value'] or '':<15}")
                
                output.append("")
        
        # 输出视图结构
        if views:
            output.append("👁️ 视图结构信息")
            output.append("-" * 40)
            for i, view in enumerate(views, 1):
                output.append(f"\n{i}. {view.full_name} (视图)")
                output.append(f"   数据库: {view.database}")
                output.append(f"   架构: {view.schema}")
                output.append(f"   视图名: {view.name}")
                output.append(f"   列数: {len(view.columns)}")
                output.append("")
                
                # 列信息
                if view.columns:
                    output.append("   列信息:")
                    output.append("   " + "-" * 60)
                    output.append(f"   {'列名':<20} {'数据类型':<15} {'可空':<5} {'主键':<5} {'默认值':<15}")
                    output.append("   " + "-" * 60)
                    
                    for col in view.columns:
                        col_type = col['data_type']
                        if col['max_length'] and col['data_type'] in ['varchar', 'nvarchar', 'char', 'nchar']:
                            col_type += f"({col['max_length']})"
                        elif col['precision'] and col['data_type'] in ['decimal', 'numeric']:
                            col_type += f"({col['precision']},{col['scale'] or 0})"
                        
                        output.append(f"   {col['column_name']:<20} {col_type:<15} {col['is_nullable']:<5} {col['is_primary_key']:<5} {col['default_value'] or '':<15}")
                
                # 视图定义
                if view.view_definition:
                    output.append("")
                    output.append("   视图定义:")
                    output.append("   " + "-" * 40)
                    view_lines = view.view_definition.split('\n')
                    for line in view_lines[:10]:  # 只显示前10行
                        output.append(f"   {line}")
                    if len(view_lines) > 10:
                        output.append(f"   ... (还有 {len(view_lines) - 10} 行)")
                
                output.append("")
        
        output.append("=" * 80)
        output.append("报告结束")
        output.append("=" * 80)
        
        return "\n".join(output)
    
    def _generate_analysis_summary(self, tables: List[TableInfo], views: List[TableInfo], all_referenced_tables: Set[str]) -> str:
        """生成分析摘要"""
        total_columns = sum(len(table.columns) for table in tables + views)
        
        summary = f"""
分析摘要:
- 总计发现 {len(all_referenced_tables)} 个数据库对象
- 其中表: {len(tables)} 个
- 其中视图: {len(views)} 个  
- 总列数: {total_columns} 个
- 分析时间: {self._get_current_time()}
"""
        return summary.strip()
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    async def _execute_query(self, sql: str, server_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """执行SQL查询"""
        try:
            if server_name:
                return await self.sqlserver.execute_query_with_server(server_name, sql)
            else:
                return await self.sqlserver.execute_query(sql)
        except Exception as e:
            self.log_error("查询执行失败", error=e)
            return []


# 全局分析器实例
_schema_analyzer: Optional[SchemaAnalyzer] = None


def get_schema_analyzer() -> SchemaAnalyzer:
    """获取全局表结构分析器实例"""
    global _schema_analyzer
    if _schema_analyzer is None:
        _schema_analyzer = SchemaAnalyzer()
    return _schema_analyzer