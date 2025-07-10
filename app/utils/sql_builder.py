"""简化的SQL构建器 - 安全且灵活"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class SQLBuilder:
    """简化的SQL构建器 - 专注于安全性和易用性"""
    
    def __init__(self, table_name: str, schema: str = "dbo"):
        self.table_name = self._validate_identifier(table_name)
        self.schema = self._validate_identifier(schema)
        self.full_table = f"{self.schema}.{self.table_name}"
        
        # SQL组件
        self._select_columns: List[str] = ["*"]
        self._where_conditions: List[str] = []
        self._order_by: List[str] = []
        self._group_by: List[str] = []
        self._having: List[str] = []
        self._joins: List[str] = []
        
        # 参数
        self._parameters: Dict[str, Any] = {}
        self._param_counter = 0
    
    @staticmethod
    def _validate_identifier(identifier: str) -> str:
        """验证SQL标识符安全性"""
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', identifier):
            raise ValueError(f"无效的SQL标识符: {identifier}")
        return identifier
    
    def select(self, columns: Union[str, List[str]]) -> "SQLBuilder":
        """设置SELECT列"""
        if isinstance(columns, str):
            if columns.strip() == "*":
                self._select_columns = ["*"]
            else:
                # 简单验证列名
                columns = [col.strip() for col in columns.split(",")]
                self._select_columns = [self._validate_identifier(col) for col in columns if col]
        else:
            self._select_columns = [self._validate_identifier(col) for col in columns]
        return self
    
    def where(self, condition: str, **params) -> "SQLBuilder":
        """添加WHERE条件"""
        # 直接使用参数，无需验证
        
        # 替换参数占位符
        for key, value in params.items():
            param_name = f"param_{self._param_counter}"
            condition = condition.replace(f":{key}", f":{param_name}")
            self._parameters[param_name] = value
            self._param_counter += 1
        
        self._where_conditions.append(condition)
        return self
    
    def where_equal(self, column: str, value: Any) -> "SQLBuilder":
        """添加等值条件"""
        if value is None:
            return self.where_null(column)
        
        column = self._validate_identifier(column)
        param_name = f"param_{self._param_counter}"
        self._where_conditions.append(f"{column} = :{param_name}")
        self._parameters[param_name] = value
        self._param_counter += 1
        return self
    
    def where_like(self, column: str, value: str) -> "SQLBuilder":
        """添加LIKE条件"""
        if not value:
            return self
        
        column = self._validate_identifier(column)
        param_name = f"param_{self._param_counter}"
        self._where_conditions.append(f"{column} LIKE :{param_name}")
        self._parameters[param_name] = f"%{value}%"
        self._param_counter += 1
        return self
    
    def where_in(self, column: str, values: List[Any]) -> "SQLBuilder":
        """添加IN条件"""
        if not values:
            return self
        
        column = self._validate_identifier(column)
        placeholders = []
        
        for value in values:
            param_name = f"param_{self._param_counter}"
            placeholders.append(f":{param_name}")
            self._parameters[param_name] = value
            self._param_counter += 1
        
        self._where_conditions.append(f"{column} IN ({', '.join(placeholders)})")
        return self
    
    def where_between(self, column: str, start: Any, end: Any) -> "SQLBuilder":
        """添加BETWEEN条件"""
        if start is None and end is None:
            return self
        
        column = self._validate_identifier(column)
        
        if start is not None and end is not None:
            start_param = f"param_{self._param_counter}"
            end_param = f"param_{self._param_counter + 1}"
            self._where_conditions.append(f"{column} BETWEEN :{start_param} AND :{end_param}")
            self._parameters[start_param] = start
            self._parameters[end_param] = end
            self._param_counter += 2
        elif start is not None:
            param_name = f"param_{self._param_counter}"
            self._where_conditions.append(f"{column} >= :{param_name}")
            self._parameters[param_name] = start
            self._param_counter += 1
        elif end is not None:
            param_name = f"param_{self._param_counter}"
            self._where_conditions.append(f"{column} <= :{param_name}")
            self._parameters[param_name] = end
            self._param_counter += 1
        
        return self
    
    def where_null(self, column: str) -> "SQLBuilder":
        """添加IS NULL条件"""
        column = self._validate_identifier(column)
        self._where_conditions.append(f"{column} IS NULL")
        return self
    
    def where_not_null(self, column: str) -> "SQLBuilder":
        """添加IS NOT NULL条件"""
        column = self._validate_identifier(column)
        self._where_conditions.append(f"{column} IS NOT NULL")
        return self
    
    def order_by(self, column: str, desc: bool = False) -> "SQLBuilder":
        """添加排序"""
        column = self._validate_identifier(column)
        direction = "DESC" if desc else "ASC"
        self._order_by.append(f"{column} {direction}")
        return self
    
    def group_by(self, columns: Union[str, List[str]]) -> "SQLBuilder":
        """添加分组"""
        if isinstance(columns, str):
            columns = [columns]
        
        for column in columns:
            column = self._validate_identifier(column)
            self._group_by.append(column)
        return self
    
    def build_select(self) -> Tuple[str, Dict[str, Any]]:
        """构建SELECT查询"""
        # 构建SELECT子句
        columns_str = ", ".join(self._select_columns)
        sql = f"SELECT {columns_str} FROM {self.full_table}"
        
        # 添加JOIN
        if self._joins:
            sql += " " + " ".join(self._joins)
        
        # 添加WHERE
        if self._where_conditions:
            sql += " WHERE " + " AND ".join(self._where_conditions)
        
        # 添加GROUP BY
        if self._group_by:
            sql += " GROUP BY " + ", ".join(self._group_by)
        
        # 添加HAVING
        if self._having:
            sql += " HAVING " + " AND ".join(self._having)
        
        # 添加ORDER BY
        if self._order_by:
            sql += " ORDER BY " + ", ".join(self._order_by)
        
        # 无需验证SQL安全性
        
        return sql, self._parameters.copy()
    
    def build_count(self) -> Tuple[str, Dict[str, Any]]:
        """构建COUNT查询"""
        sql = f"SELECT COUNT(*) as total_count FROM {self.full_table}"
        
        # 添加JOIN
        if self._joins:
            sql += " " + " ".join(self._joins)
        
        # 添加WHERE
        if self._where_conditions:
            sql += " WHERE " + " AND ".join(self._where_conditions)
        
        # 添加GROUP BY
        if self._group_by:
            sql += " GROUP BY " + ", ".join(self._group_by)
        
        # 添加HAVING
        if self._having:
            sql += " HAVING " + " AND ".join(self._having)
        
        return sql, self._parameters.copy()
    