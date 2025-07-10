"""SQL参数解析器 - 用于动态表单系统"""

import re
from typing import List, Dict, Any, Tuple
from app.models.schemas import QueryFormField, FieldType, MatchType, SQLParseResult
from app.core.logging import LoggerMixin


class SQLParameterParser(LoggerMixin):
    """SQL参数解析器 - 解析SQL模板中的@参数并生成表单字段建议"""
    
    def __init__(self):
        super().__init__()
        
        # 参数匹配正则表达式
        self.param_pattern = re.compile(r'@(\w+)', re.IGNORECASE)
        
        # 字段类型推断规则
        self.field_type_rules = {
            # 数字相关
            r'(?i)(id|count|num|number|age|year|amount|price|rate|percent)': FieldType.NUMBER,
            # 邮箱相关
            r'(?i)(email|mail)': FieldType.EMAIL,
            # 日期相关
            r'(?i)(date|time|created|updated|birth|start|end)': FieldType.DATE,
            # 状态、类型相关 (下拉选择)
            r'(?i)(status|type|category|level|role|gender|state)': FieldType.SELECT,
            # 文本区域
            r'(?i)(description|comment|note|remark|content|text)': FieldType.TEXTAREA,
            # 默认文本
            r'.*': FieldType.TEXT
        }
        
        # 匹配类型推断规则 (基于SQL条件)
        self.match_type_rules = [
            (r"LIKE\s+['\"]?%.*@\w+.*%['\"]?", MatchType.LIKE),       # LIKE '%@param%'
            (r"LIKE\s+['\"]?@\w+%['\"]?", MatchType.START_WITH),      # LIKE '@param%'
            (r"LIKE\s+['\"]?%@\w+['\"]?", MatchType.END_WITH),        # LIKE '%@param'
            (r">=\s*@\w+", MatchType.GREATER_EQUAL),                  # >= @param
            (r">\s*@\w+", MatchType.GREATER),                         # > @param
            (r"<=\s*@\w+", MatchType.LESS_EQUAL),                     # <= @param
            (r"<\s*@\w+", MatchType.LESS),                            # < @param
            (r"BETWEEN\s+@\w+\s+AND\s+@\w+", MatchType.BETWEEN),     # BETWEEN @param1 AND @param2
            (r"IN\s*\(\s*@\w+\s*\)", MatchType.IN_LIST),             # IN (@param)
            (r"=\s*@\w+", MatchType.EXACT),                           # = @param
        ]
    
    def parse_sql_parameters(self, sql_template: str) -> SQLParseResult:
        """解析SQL模板中的参数并生成字段建议"""
        try:
            # 提取所有参数
            parameters = self._extract_parameters(sql_template)
            
            # 生成字段建议
            suggested_fields = []
            warnings = []
            
            for param in parameters:
                field = self._generate_field_suggestion(param, sql_template)
                suggested_fields.append(field)
                
                # 检查潜在问题
                param_warnings = self._check_parameter_warnings(param, sql_template)
                warnings.extend(param_warnings)
            
            # 按参数在SQL中出现的顺序排序
            suggested_fields.sort(key=lambda f: sql_template.find(f.parameter))
            
            # 设置order字段
            for i, field in enumerate(suggested_fields):
                field.order = i + 1
            
            self.log_info(f"Successfully parsed SQL template, found {len(parameters)} parameters")
            
            return SQLParseResult(
                parameters=parameters,
                suggested_fields=suggested_fields,
                warnings=warnings
            )
            
        except Exception as e:
            self.log_error("Failed to parse SQL parameters", error=e)
            return SQLParseResult(
                parameters=[],
                suggested_fields=[],
                warnings=[f"解析SQL失败: {str(e)}"]
            )
    
    def _extract_parameters(self, sql_template: str) -> List[str]:
        """提取SQL模板中的所有参数"""
        matches = self.param_pattern.findall(sql_template)
        # 去重并保持顺序
        seen = set()
        parameters = []
        for match in matches:
            param_name = f"@{match}"
            if param_name not in seen:
                parameters.append(param_name)
                seen.add(param_name)
        
        return parameters
    
    def _generate_field_suggestion(self, parameter: str, sql_template: str) -> QueryFormField:
        """为参数生成字段建议"""
        param_name = parameter[1:]  # 去掉@符号
        
        # 推断字段类型
        field_type = self._infer_field_type(param_name)
        
        # 推断匹配类型
        match_type = self._infer_match_type(parameter, sql_template)
        
        # 生成显示标签
        label = self._generate_label(param_name)
        
        # 生成占位符
        placeholder = self._generate_placeholder(param_name, field_type)
        
        # 生成验证规则
        validation = self._generate_validation_rules(field_type)
        
        # 生成数据源配置 (用于下拉选择框)
        data_source = self._generate_data_source(param_name, field_type)
        
        return QueryFormField(
            parameter=parameter,
            label=label,
            field_type=field_type,
            required=False,  # 默认非必填
            match_type=match_type,
            placeholder=placeholder,
            validation=validation,
            data_source=data_source,
            order=0  # 稍后设置
        )
    
    def _infer_field_type(self, param_name: str) -> FieldType:
        """根据参数名推断字段类型"""
        for pattern, field_type in self.field_type_rules.items():
            if re.match(pattern, param_name):
                return field_type
        return FieldType.TEXT
    
    def _infer_match_type(self, parameter: str, sql_template: str) -> MatchType:
        """根据SQL上下文推断匹配类型"""
        # 查找参数在SQL中的使用上下文
        param_contexts = []
        
        # 分割SQL为行，查找包含参数的行
        lines = sql_template.split('\n')
        for line in lines:
            if parameter in line:
                param_contexts.append(line.strip())
        
        # 对每个上下文应用匹配规则
        for context in param_contexts:
            for pattern, match_type in self.match_type_rules:
                if re.search(pattern.replace('@\\w+', re.escape(parameter)), context, re.IGNORECASE):
                    return match_type
        
        # 默认精确匹配
        return MatchType.EXACT
    
    def _generate_label(self, param_name: str) -> str:
        """生成显示标签"""
        # 简单的标签生成规则
        label_mapping = {
            'id': 'ID',
            'userid': '用户ID',
            'username': '用户名',
            'email': '邮箱',
            'password': '密码',
            'phone': '电话',
            'mobile': '手机号',
            'status': '状态',
            'type': '类型',
            'category': '分类',
            'level': '级别',
            'role': '角色',
            'gender': '性别',
            'age': '年龄',
            'name': '姓名',
            'title': '标题',
            'description': '描述',
            'content': '内容',
            'remark': '备注',
            'comment': '评论',
            'createdate': '创建日期',
            'updatedate': '更新日期',
            'startdate': '开始日期',
            'enddate': '结束日期',
            'datefrom': '日期从',
            'dateto': '日期到',
            'amount': '金额',
            'price': '价格',
            'count': '数量',
            'pagesize': '页面大小'
        }
        
        # 转为小写进行匹配
        lower_param = param_name.lower()
        
        # 直接匹配
        if lower_param in label_mapping:
            return label_mapping[lower_param]
        
        # 部分匹配
        for key, value in label_mapping.items():
            if key in lower_param:
                return value
        
        # 默认：首字母大写，驼峰转换
        return self._camel_to_chinese(param_name)
    
    def _camel_to_chinese(self, param_name: str) -> str:
        """驼峰命名转换为中文标签"""
        # 简单处理：在大写字母前添加空格，然后首字母大写
        result = re.sub(r'([a-z])([A-Z])', r'\1 \2', param_name)
        return result.title()
    
    def _generate_placeholder(self, param_name: str, field_type: FieldType) -> str:
        """生成占位符"""
        placeholder_mapping = {
            FieldType.TEXT: f"请输入{self._generate_label(param_name)}",
            FieldType.NUMBER: f"请输入{self._generate_label(param_name)}",
            FieldType.EMAIL: "请输入邮箱地址",
            FieldType.DATE: "请选择日期",
            FieldType.DATETIME: "请选择日期时间",
            FieldType.SELECT: f"请选择{self._generate_label(param_name)}",
            FieldType.MULTISELECT: f"请选择{self._generate_label(param_name)}",
            FieldType.TEXTAREA: f"请输入{self._generate_label(param_name)}",
        }
        
        return placeholder_mapping.get(field_type, f"请输入{self._generate_label(param_name)}")
    
    def _generate_validation_rules(self, field_type: FieldType) -> Dict[str, Any]:
        """生成验证规则"""
        validation_rules = {}
        
        if field_type == FieldType.EMAIL:
            validation_rules = {
                "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "message": "请输入有效的邮箱地址"
            }
        elif field_type == FieldType.NUMBER:
            validation_rules = {
                "type": "number",
                "min": 0
            }
        elif field_type == FieldType.TEXT:
            validation_rules = {
                "max_length": 255
            }
        elif field_type == FieldType.TEXTAREA:
            validation_rules = {
                "max_length": 2000
            }
        
        return validation_rules
    
    def _generate_data_source(self, param_name: str, field_type: FieldType) -> Dict[str, Any]:
        """生成数据源配置 (用于下拉选择框)"""
        if field_type not in [FieldType.SELECT, FieldType.MULTISELECT, FieldType.RADIO]:
            return None
        
        # 根据参数名生成建议的数据源
        data_source_mapping = {
            'status': {
                "type": "sql",
                "sql": "SELECT '活跃' as display_value, 'Active' as actual_value UNION ALL SELECT '禁用', 'Disabled' UNION ALL SELECT '暂停', 'Suspended'",
                "value_column": "actual_value",
                "display_column": "display_value"
            },
            'type': {
                "type": "sql",
                "sql": "SELECT '类型1' as display_value, '1' as actual_value UNION ALL SELECT '类型2', '2' UNION ALL SELECT '类型3', '3'",
                "value_column": "actual_value",
                "display_column": "display_value"
            },
            'gender': {
                "type": "static",
                "options": [
                    {"label": "男", "value": "M"},
                    {"label": "女", "value": "F"},
                    {"label": "未知", "value": "U"}
                ]
            },
            'role': {
                "type": "sql",
                "sql": "SELECT '管理员' as display_value, 'Admin' as actual_value UNION ALL SELECT '用户', 'User' UNION ALL SELECT '访客', 'Guest'",
                "value_column": "actual_value",
                "display_column": "display_value"
            }
        }
        
        # 查找匹配的数据源
        lower_param = param_name.lower()
        for key, config in data_source_mapping.items():
            if key in lower_param:
                return config
        
        # 默认数据源配置
        return {
            "type": "sql",
            "sql": f"-- 请配置{self._generate_label(param_name)}的数据源SQL\n-- 示例: SELECT display_text, value FROM your_table",
            "value_column": "value",
            "display_column": "display_text"
        }
    
    def _check_parameter_warnings(self, parameter: str, sql_template: str) -> List[str]:
        """检查参数使用中的潜在问题"""
        warnings = []
        
        # 检查是否有SQL注入风险
        if self._has_sql_injection_risk(parameter, sql_template):
            warnings.append(f"参数 {parameter} 可能存在SQL注入风险，建议使用参数化查询")
        
        # 检查是否有未处理的NULL值
        if not self._has_null_check(parameter, sql_template):
            warnings.append(f"参数 {parameter} 缺少NULL值检查，建议添加 (@param IS NULL OR ...) 条件")
        
        # 检查是否有日期格式问题
        if self._has_date_format_issue(parameter, sql_template):
            warnings.append(f"参数 {parameter} 可能存在日期格式问题，建议明确指定日期格式")
        
        return warnings
    
    def _has_sql_injection_risk(self, parameter: str, sql_template: str) -> bool:
        """检查是否有SQL注入风险"""
        # 简单检查：如果参数直接拼接到字符串中而不是使用参数化查询
        # 这里只是基本检查，实际使用中已经通过参数化查询防止注入
        dangerous_patterns = [
            rf"['\"].*{re.escape(parameter)}.*['\"]",  # 字符串拼接
            rf"concat.*{re.escape(parameter)}",         # CONCAT函数
            rf"\+.*{re.escape(parameter)}.*\+"          # 字符串连接
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sql_template, re.IGNORECASE):
                return True
        
        return False
    
    def _has_null_check(self, parameter: str, sql_template: str) -> bool:
        """检查是否有NULL值检查"""
        null_check_patterns = [
            rf"{re.escape(parameter)}\s+IS\s+NULL",
            rf"\({re.escape(parameter)}\s+IS\s+NULL\s+OR",
            rf"ISNULL\s*\(\s*{re.escape(parameter)}",
            rf"COALESCE\s*\(\s*{re.escape(parameter)}"
        ]
        
        for pattern in null_check_patterns:
            if re.search(pattern, sql_template, re.IGNORECASE):
                return True
        
        return False
    
    def _has_date_format_issue(self, parameter: str, sql_template: str) -> bool:
        """检查是否有日期格式问题"""
        param_name = parameter[1:].lower()
        
        # 如果参数名包含date相关关键字
        if any(keyword in param_name for keyword in ['date', 'time', 'created', 'updated']):
            # 检查是否有明确的日期转换
            date_conversion_patterns = [
                rf"CONVERT\s*\(\s*.*{re.escape(parameter)}",
                rf"CAST\s*\(\s*{re.escape(parameter)}\s+AS",
                rf"FORMAT\s*\(\s*{re.escape(parameter)}"
            ]
            
            for pattern in date_conversion_patterns:
                if re.search(pattern, sql_template, re.IGNORECASE):
                    return False
            
            return True  # 日期参数但没有格式转换
        
        return False


# 全局解析器实例
_sql_parser = None


def get_sql_parser() -> SQLParameterParser:
    """获取SQL参数解析器实例"""
    global _sql_parser
    if _sql_parser is None:
        _sql_parser = SQLParameterParser()
    return _sql_parser