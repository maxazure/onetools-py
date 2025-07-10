"""动态查询表单服务层"""

import json
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import text

from app.core.database import get_sqlite_manager
from app.core.logging import LoggerMixin
from app.models.schemas import (
    QueryFormCreate,
    QueryFormUpdate,
    QueryFormResponse,
    QueryFormExecuteRequest,
    QueryFormHistory,
    QueryFormConfig,
    SQLParseResult,
    DataSourceTestRequest,
    DataSourceTestResponse,
    QueryResponse
)
from app.utils.sql_parser import get_sql_parser
from app.services.query_service import get_query_service


class QueryFormService(LoggerMixin):
    """动态查询表单服务"""
    
    def __init__(self):
        super().__init__()
        self.sqlite = get_sqlite_manager()
        self.sql_parser = get_sql_parser()
        self.query_service = get_query_service()
    
    # ===================== 表单管理 =====================
    
    async def get_all_forms(self, active_only: bool = True) -> List[QueryFormResponse]:
        """获取所有查询表单"""
        try:
            async with self.sqlite.get_connection() as conn:
                sql = """
                    SELECT id, form_name, form_description, sql_template, form_config, 
                           target_database, is_active, created_by, created_at, updated_at
                    FROM query_forms
                """
                
                if active_only:
                    sql += " WHERE is_active = 1"
                
                sql += " ORDER BY form_name"
                
                result = await conn.execute(text(sql))
                rows = result.fetchall()
                
                forms = []
                for row in rows:
                    form_config = json.loads(row[4]) if row[4] else {}
                    
                    form = QueryFormResponse(
                        id=row[0],
                        form_name=row[1],
                        form_description=row[2],
                        sql_template=row[3],
                        form_config=QueryFormConfig(**form_config),
                        target_database=row[5],
                        is_active=bool(row[6]),
                        created_by=row[7],
                        created_at=row[8] if row[8] else datetime.utcnow(),
                        updated_at=row[9] if row[9] else datetime.utcnow()
                    )
                    forms.append(form)
                
                self.log_info(f"Successfully retrieved {len(forms)} query forms")
                return forms
                
        except Exception as e:
            self.log_error("Failed to get query forms", error=e)
            return []
    
    async def get_form_by_id(self, form_id: int) -> Optional[QueryFormResponse]:
        """根据ID获取查询表单"""
        try:
            async with self.sqlite.get_connection() as conn:
                result = await conn.execute(text("""
                    SELECT id, form_name, form_description, sql_template, form_config, 
                           target_database, is_active, created_by, created_at, updated_at
                    FROM query_forms
                    WHERE id = :form_id
                """), {"form_id": form_id})
                
                row = result.fetchone()
                if not row:
                    return None
                
                form_config = json.loads(row[4]) if row[4] else {}
                
                return QueryFormResponse(
                    id=row[0],
                    form_name=row[1],
                    form_description=row[2],
                    sql_template=row[3],
                    form_config=QueryFormConfig(**form_config),
                    target_database=row[5],
                    is_active=bool(row[6]),
                    created_by=row[7],
                    created_at=row[8] if row[8] else datetime.utcnow(),
                    updated_at=row[9] if row[9] else datetime.utcnow()
                )
                
        except Exception as e:
            self.log_error("Failed to get query form by ID", error=e, form_id=form_id)
            return None
    
    async def create_form(self, form_data: QueryFormCreate) -> Optional[QueryFormResponse]:
        """创建查询表单"""
        try:
            now = datetime.utcnow()
            form_config_json = form_data.form_config.model_dump()
            
            async with self.sqlite.get_connection() as conn:
                result = await conn.execute(text("""
                    INSERT INTO query_forms (
                        form_name, form_description, sql_template, form_config, 
                        target_database, is_active, created_by, created_at, updated_at
                    ) VALUES (
                        :form_name, :form_description, :sql_template, :form_config,
                        :target_database, :is_active, :created_by, :created_at, :updated_at
                    )
                """), {
                    "form_name": form_data.form_name,
                    "form_description": form_data.form_description,
                    "sql_template": form_data.sql_template,
                    "form_config": json.dumps(form_config_json, ensure_ascii=False),
                    "target_database": form_data.target_database,
                    "is_active": True,
                    "created_by": "system",
                    "created_at": now,
                    "updated_at": now
                })
                
                form_id = result.lastrowid
                
                self.log_info(f"Successfully created query form: {form_data.form_name}")
                
                return QueryFormResponse(
                    id=form_id,
                    form_name=form_data.form_name,
                    form_description=form_data.form_description,
                    sql_template=form_data.sql_template,
                    form_config=form_data.form_config,
                    target_database=form_data.target_database,
                    is_active=True,
                    created_by="system",
                    created_at=now,
                    updated_at=now
                )
                
        except Exception as e:
            self.log_error("Failed to create query form", error=e, form_name=form_data.form_name)
            return None
    
    async def update_form(self, form_id: int, form_data: QueryFormUpdate) -> Optional[QueryFormResponse]:
        """更新查询表单"""
        try:
            now = datetime.utcnow()
            
            async with self.sqlite.get_connection() as conn:
                # 构建更新SQL
                update_fields = []
                params = {"form_id": form_id, "updated_at": now}
                
                if form_data.form_name is not None:
                    update_fields.append("form_name = :form_name")
                    params["form_name"] = form_data.form_name
                
                if form_data.form_description is not None:
                    update_fields.append("form_description = :form_description")
                    params["form_description"] = form_data.form_description
                
                if form_data.sql_template is not None:
                    update_fields.append("sql_template = :sql_template")
                    params["sql_template"] = form_data.sql_template
                
                if form_data.form_config is not None:
                    update_fields.append("form_config = :form_config")
                    params["form_config"] = json.dumps(form_data.form_config.model_dump(), ensure_ascii=False)
                
                if form_data.target_database is not None:
                    update_fields.append("target_database = :target_database")
                    params["target_database"] = form_data.target_database
                
                if form_data.is_active is not None:
                    update_fields.append("is_active = :is_active")
                    params["is_active"] = form_data.is_active
                
                if not update_fields:
                    # 如果没有字段需要更新，直接返回现有数据
                    return await self.get_form_by_id(form_id)
                
                # 执行更新
                update_sql = f"""
                    UPDATE query_forms 
                    SET {', '.join(update_fields)}, updated_at = :updated_at
                    WHERE id = :form_id
                """
                
                result = await conn.execute(text(update_sql), params)
                
                if result.rowcount == 0:
                    self.log_warning("No query form found to update", form_id=form_id)
                    return None
                
                self.log_info(f"Successfully updated query form: {form_id}")
                
                # 返回更新后的数据
                return await self.get_form_by_id(form_id)
                
        except Exception as e:
            self.log_error("Failed to update query form", error=e, form_id=form_id)
            return None
    
    async def delete_form(self, form_id: int, soft_delete: bool = True) -> bool:
        """删除查询表单"""
        try:
            async with self.sqlite.get_connection() as conn:
                if soft_delete:
                    # 软删除：设置is_active为False
                    result = await conn.execute(text("""
                        UPDATE query_forms 
                        SET is_active = 0, updated_at = :updated_at
                        WHERE id = :form_id
                    """), {
                        "form_id": form_id,
                        "updated_at": datetime.utcnow()
                    })
                else:
                    # 硬删除：物理删除记录
                    # 先删除相关的历史记录
                    await conn.execute(text("DELETE FROM query_form_history WHERE form_id = :form_id"), {"form_id": form_id})
                    
                    # 再删除表单记录
                    result = await conn.execute(text("DELETE FROM query_forms WHERE id = :form_id"), {"form_id": form_id})
                
                if result.rowcount == 0:
                    self.log_warning("No query form found to delete", form_id=form_id)
                    return False
                
                delete_type = "soft" if soft_delete else "hard"
                self.log_info(f"Successfully {delete_type} deleted query form: {form_id}")
                return True
                
        except Exception as e:
            self.log_error("Failed to delete query form", error=e, form_id=form_id)
            return False
    
    # ===================== SQL解析 =====================
    
    async def parse_sql_template(self, sql_template: str) -> SQLParseResult:
        """解析SQL模板并生成字段建议"""
        try:
            result = self.sql_parser.parse_sql_parameters(sql_template)
            self.log_info(f"Successfully parsed SQL template, found {len(result.parameters)} parameters")
            return result
            
        except Exception as e:
            self.log_error("Failed to parse SQL template", error=e)
            return SQLParseResult(
                parameters=[],
                suggested_fields=[],
                warnings=[f"解析SQL失败: {str(e)}"]
            )
    
    # ===================== 数据源测试 =====================
    
    async def test_data_source(self, request: DataSourceTestRequest) -> DataSourceTestResponse:
        """测试数据源配置"""
        try:
            config = request.data_source_config
            
            if config.get("type") == "static":
                # 静态数据源测试
                options = config.get("options", [])
                return DataSourceTestResponse(
                    success=True,
                    data=options,
                    error_message=None
                )
            
            elif config.get("type") == "sql":
                # SQL数据源测试
                sql = config.get("sql", "")
                if not sql.strip():
                    return DataSourceTestResponse(
                        success=False,
                        data=[],
                        error_message="SQL查询不能为空"
                    )
                
                # 执行SQL查询
                query_result = await self.query_service.execute_query(
                    sql=sql,
                    server_name=request.server_name
                )
                
                # 转换查询结果
                test_data = []
                if query_result.data:
                    for row in query_result.data[:10]:  # 最多返回10条测试数据
                        test_data.append(row)
                
                return DataSourceTestResponse(
                    success=True,
                    data=test_data,
                    error_message=None
                )
            
            else:
                return DataSourceTestResponse(
                    success=False,
                    data=[],
                    error_message=f"不支持的数据源类型: {config.get('type')}"
                )
                
        except Exception as e:
            self.log_error("Failed to test data source", error=e)
            return DataSourceTestResponse(
                success=False,
                data=[],
                error_message=f"数据源测试失败: {str(e)}"
            )
    
    # ===================== 查询执行 =====================
    
    async def execute_form_query(self, request: QueryFormExecuteRequest) -> QueryResponse:
        """执行动态表单查询 - 使用和custom接口相同的执行逻辑"""
        try:
            # 获取表单配置
            form = await self.get_form_by_id(request.form_id)
            if not form:
                raise ValueError(f"表单不存在: {request.form_id}")
            
            if not form.is_active:
                raise ValueError(f"表单已禁用: {form.form_name}")
            
            # 构建参数化SQL
            sql_with_params = self._build_parameterized_sql(form.sql_template, request.params)
            
            # 调试日志
            self.log_info(f"Original SQL: {form.sql_template}")
            self.log_info(f"Parameters: {request.params}")
            self.log_info(f"Final SQL: {sql_with_params}")
            
            # 直接使用query_service执行查询（和custom接口相同的逻辑）
            query_result = await self.query_service.execute_query(
                sql=sql_with_params,
                server_name=request.server_name
            )
            
            # 记录执行历史
            try:
                await self._record_execution_history(
                    form_id=request.form_id,
                    params=request.params,
                    executed_sql=sql_with_params,
                    execution_time=query_result.execution_time,
                    row_count=query_result.total,
                    success=True,
                    error_message=None
                )
            except Exception as history_error:
                # 历史记录失败不影响查询结果
                self.log_warning(f"Failed to record execution history: {history_error}")
            
            self.log_info(f"Successfully executed form query: {form.form_name}")
            return query_result
            
        except Exception as e:
            # 记录执行失败历史
            try:
                await self._record_execution_history(
                    form_id=request.form_id,
                    params=request.params,
                    executed_sql=None,
                    execution_time=0,
                    row_count=0,
                    success=False,
                    error_message=str(e)
                )
            except:
                pass  # 记录历史失败不影响主要错误
            
            self.log_error("Failed to execute form query", error=e, form_id=request.form_id)
            raise
    
    def _build_parameterized_sql(self, sql_template: str, params: Dict[str, Any]) -> str:
        """构建参数化SQL - 智能处理不同SQL上下文中的参数，过滤空参数"""
        import re
        
        sql = sql_template
        
        # 先过滤空参数对应的WHERE条件
        empty_params = []
        valid_params = {}
        
        # 标准化参数名，确保所有参数都以@开头
        normalized_params = {}
        for param_name, param_value in params.items():
            # 确保参数名以@开头
            normalized_name = f'@{param_name}' if not param_name.startswith('@') else param_name
            normalized_params[normalized_name] = param_value
        
        for param_name, param_value in normalized_params.items():
            # 检查参数是否为空
            if param_value is None or param_value == '' or (isinstance(param_value, str) and param_value.strip() == ''):
                empty_params.append(param_name)
                self.log_info(f"Empty parameter detected: {param_name} = '{param_value}'")
            else:
                valid_params[param_name] = param_value
                self.log_info(f"Valid parameter detected: {param_name} = '{param_value}'")
        
        self.log_info(f"Empty params: {empty_params}")
        self.log_info(f"Valid params: {valid_params}")
        
        # 移除空参数对应的WHERE条件
        for param_name in empty_params:
            param_placeholder = param_name  # param_name已经是@开头的格式了
            
            self.log_info(f"Removing conditions for empty parameter: {param_placeholder}")
            
            # 更精确的匹配模式，只匹配包含该特定参数的条件
            # 使用更严格的边界匹配，避免误删其他条件
            patterns = [
                # 匹配: AND (...包含该参数的条件...)
                rf'\s+AND\s+\([^)]*{re.escape(param_placeholder)}[^)]*\)',
                # 匹配: OR (...包含该参数的条件...)
                rf'\s+OR\s+\([^)]*{re.escape(param_placeholder)}[^)]*\)',
                # 匹配: AND column LIKE '%@param%' (精确匹配带引号的参数)
                rf'\s+AND\s+\w+\s+LIKE\s+\'[^\']*{re.escape(param_placeholder)}[^\']*\'',
                # 匹配: OR column LIKE '%@param%' (精确匹配带引号的参数)
                rf'\s+OR\s+\w+\s+LIKE\s+\'[^\']*{re.escape(param_placeholder)}[^\']*\'',
                # 匹配: AND column = @param (精确匹配等号条件)
                rf'\s+AND\s+\w+\s*=\s*{re.escape(param_placeholder)}(?=\s|$)',
                # 匹配: OR column = @param (精确匹配等号条件)
                rf'\s+OR\s+\w+\s*=\s*{re.escape(param_placeholder)}(?=\s|$)',
                # 匹配WHERE开头的条件
                rf'WHERE\s+\([^)]*{re.escape(param_placeholder)}[^)]*\)',
                rf'WHERE\s+\w+\s+LIKE\s+\'[^\']*{re.escape(param_placeholder)}[^\']*\'',
                rf'WHERE\s+\w+\s*=\s*{re.escape(param_placeholder)}(?=\s|$)',
            ]
            
            for pattern in patterns:
                before = sql
                sql = re.sub(pattern, '', sql, flags=re.IGNORECASE)
                if before != sql:
                    self.log_info(f"Removed condition matching pattern: {pattern}")
                    self.log_info(f"SQL after removal: {sql.strip()}")
        
        # 清理可能出现的多余的AND/OR
        sql = re.sub(r'\s+AND\s+AND\s+', ' AND ', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\s+OR\s+OR\s+', ' OR ', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\s+AND\s+OR\s+', ' OR ', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\s+OR\s+AND\s+', ' AND ', sql, flags=re.IGNORECASE)
        sql = re.sub(r'WHERE\s+(AND|OR)\s+', 'WHERE ', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\s+(AND|OR)\s*(?=ORDER\s+BY|GROUP\s+BY|HAVING|LIMIT|$)', '', sql, flags=re.IGNORECASE)
        
        # 如果WHERE子句变空了，移除整个WHERE
        sql = re.sub(r'WHERE\s+(?=ORDER\s+BY|GROUP\s+BY|HAVING|LIMIT|$)', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'WHERE\s*$', '', sql, flags=re.IGNORECASE)
        
        self.log_info(f"Starting parameter replacement...")
        # 替换有效参数
        for param_name, param_value in valid_params.items():
            # param_name已经是@开头的格式了
            self.log_info(f"Processing param: {param_name} = '{param_value}'")
            
            # 根据值的类型进行适当的转换
            if isinstance(param_value, str):
                # 转义单引号
                escaped_value = param_value.replace("'", "''")
                
                # 检查参数是否在LIKE表达式中
                # 寻找类似 '%@param%' 或 '%@param' 或 '@param%' 的模式
                like_patterns = [
                    f"'%{param_name}%'",
                    f"'%{param_name}",
                    f"{param_name}%'",
                    f"'%{param_name}'",
                ]
                
                is_in_like = any(pattern in sql for pattern in like_patterns)
                
                if is_in_like:
                    # 对于LIKE表达式，直接替换参数值，不加额外引号
                    sql_value = escaped_value
                else:
                    # 对于其他情况，添加引号
                    sql_value = f"'{escaped_value}'"
                    
            elif isinstance(param_value, (int, float)):
                sql_value = str(param_value)
            elif isinstance(param_value, bool):
                sql_value = '1' if param_value else '0'
            else:
                # 其他类型转为字符串
                escaped_value = str(param_value).replace("'", "''")
                sql_value = f"'{escaped_value}'"
            
            sql = sql.replace(param_name, sql_value)
        
        # 清理多余的空白字符
        sql = ' '.join(sql.split())
        
        # 最后的安全检查，移除任何剩余的未替换参数的条件
        # 但是要排除已经有有效值的参数
        remaining_params = re.findall(r'@\w+', sql)
        self.log_info(f"Remaining unreplaced parameters: {remaining_params}")
        
        for remaining_param in remaining_params:
            # 只移除那些没有有效值的参数对应的条件
            if remaining_param not in valid_params:
                self.log_info(f"Removing conditions for unreplaced parameter: {remaining_param}")
                # 如果还有未替换的参数，移除包含它的条件
                patterns = [
                    rf'\s+AND\s+\w+\s+LIKE\s+\'[^\']*{re.escape(remaining_param)}[^\']*\'',
                    rf'\s+OR\s+\w+\s+LIKE\s+\'[^\']*{re.escape(remaining_param)}[^\']*\'',
                    rf'WHERE\s+\w+\s+LIKE\s+\'[^\']*{re.escape(remaining_param)}[^\']*\'',
                    rf'\s+AND\s+\w+\s*=\s*{re.escape(remaining_param)}(?=\s|$)',
                    rf'\s+OR\s+\w+\s*=\s*{re.escape(remaining_param)}(?=\s|$)',
                    rf'WHERE\s+\w+\s*=\s*{re.escape(remaining_param)}(?=\s|$)',
                ]
                for pattern in patterns:
                    before = sql
                    sql = re.sub(pattern, '', sql, flags=re.IGNORECASE)
                    if before != sql:
                        self.log_info(f"Removed unreplaced condition: {pattern}")
            else:
                self.log_info(f"Keeping parameter {remaining_param} as it has a valid value")
        
        # 再次清理
        sql = re.sub(r'WHERE\s+(AND|OR)\s+', 'WHERE ', sql, flags=re.IGNORECASE)
        sql = re.sub(r'WHERE\s*$', '', sql, flags=re.IGNORECASE)
        sql = ' '.join(sql.split())
        
        return sql
    
    async def _record_execution_history(
        self,
        form_id: int,
        params: Dict[str, Any],
        executed_sql: Optional[str],
        execution_time: float,
        row_count: int,
        success: bool,
        error_message: Optional[str]
    ):
        """记录执行历史"""
        try:
            async with self.sqlite.get_connection() as conn:
                await conn.execute(text("""
                    INSERT INTO query_form_history (
                        form_id, query_params, executed_sql, execution_time,
                        row_count, success, error_message, user_id, created_at, updated_at
                    ) VALUES (
                        :form_id, :query_params, :executed_sql, :execution_time,
                        :row_count, :success, :error_message, :user_id, :created_at, :updated_at
                    )
                """), {
                    "form_id": form_id,
                    "query_params": json.dumps(params, ensure_ascii=False),
                    "executed_sql": executed_sql,
                    "execution_time": execution_time,
                    "row_count": row_count,
                    "success": success,
                    "error_message": error_message,
                    "user_id": "system",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
                
        except Exception as e:
            self.log_error("Failed to record execution history", error=e)
    
    # ===================== 历史记录 =====================
    
    async def get_form_history(self, form_id: Optional[int] = None, limit: int = 100) -> List[QueryFormHistory]:
        """获取表单执行历史"""
        try:
            async with self.sqlite.get_connection() as conn:
                sql = """
                    SELECT id, form_id, query_params, executed_sql, execution_time,
                           row_count, success, error_message, user_id, created_at, updated_at
                    FROM query_form_history
                """
                
                params = {}
                if form_id is not None:
                    sql += " WHERE form_id = :form_id"
                    params["form_id"] = form_id
                
                sql += " ORDER BY created_at DESC LIMIT :limit"
                params["limit"] = limit
                
                result = await conn.execute(text(sql), params)
                rows = result.fetchall()
                
                history_list = []
                for row in rows:
                    query_params = json.loads(row[2]) if row[2] else {}
                    
                    history = QueryFormHistory(
                        id=row[0],
                        form_id=row[1],
                        query_params=query_params,
                        executed_sql=row[3],
                        execution_time=row[4],
                        row_count=row[5],
                        success=bool(row[6]),
                        error_message=row[7],
                        user_id=row[8],
                        created_at=row[9] if row[9] else datetime.utcnow(),
                        updated_at=row[10] if row[10] else datetime.utcnow()
                    )
                    history_list.append(history)
                
                return history_list
                
        except Exception as e:
            self.log_error("Failed to get form history", error=e)
            return []


# 全局服务实例
_query_form_service: Optional[QueryFormService] = None


def get_query_form_service() -> QueryFormService:
    """获取查询表单服务实例"""
    global _query_form_service
    if _query_form_service is None:
        _query_form_service = QueryFormService()
    return _query_form_service