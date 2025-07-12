/**
 * 动态查询表单类型定义
 */

// 基础类型
export interface BaseTimestamp {
  created_at: string;
  updated_at: string;
}

// 字段类型枚举
export enum FieldType {
  TEXT = 'text',
  NUMBER = 'number',
  EMAIL = 'email',
  DATE = 'date',
  DATETIME = 'datetime',
  SELECT = 'select',
  MULTISELECT = 'multiselect',
  CHECKBOX = 'checkbox',
  RADIO = 'radio',
  TEXTAREA = 'textarea',
}

// 匹配类型枚举
export enum MatchType {
  // 精确匹配
  EXACT = 'exact',
  NOT_EQUAL = 'not_equal',
  
  // 数值比较
  GREATER = 'greater',
  GREATER_EQUAL = 'greater_equal',
  LESS = 'less',
  LESS_EQUAL = 'less_equal',
  BETWEEN = 'between',
  
  // 文本匹配
  LIKE = 'like',
  NOT_LIKE = 'not_like',
  START_WITH = 'start_with',
  END_WITH = 'end_with',
  CONTAINS = 'contains',
  
  // 列表匹配
  IN_LIST = 'in_list',
  NOT_IN_LIST = 'not_in_list',
  
  // 空值检查
  IS_NULL = 'is_null',
  IS_NOT_NULL = 'is_not_null',
}

// 数据源类型枚举
export enum DataSourceType {
  STATIC = 'static',
  SQL = 'sql',
}

// 静态数据源选项
export interface StaticOption {
  label: string;
  value: string | number;
}

// 数据源配置
export interface DataSourceConfig {
  type: DataSourceType;
  options?: StaticOption[];
  sql?: string;
  value_column?: string;
  display_column?: string;
}

// 验证规则
export interface ValidationRule {
  pattern?: string;
  message?: string;
  type?: string;
  min?: number;
  max?: number;
  max_length?: number;
  min_length?: number;
  required?: boolean;
}

// 表单字段配置
export interface QueryFormField {
  parameter: string;
  label: string;
  field_type: FieldType;
  required: boolean;
  default_value?: string;
  match_type: MatchType;
  placeholder?: string;
  help_text?: string;
  validation?: ValidationRule;
  data_source?: DataSourceConfig;
  grid_span?: number;
  order: number;
}

// 表单布局配置
export interface QueryFormLayout {
  columns: number;
  button_position: 'bottom' | 'right';
  label_width?: string;
  field_spacing?: string;
}

// 表单配置
export interface QueryFormConfig {
  title: string;
  description?: string;
  fields: QueryFormField[];
  layout: QueryFormLayout;
}

// 查询表单基础模型
export interface QueryFormBase {
  form_name: string;
  form_description?: string;
  sql_template: string;
  form_config: QueryFormConfig;
}

// 创建查询表单请求
export interface QueryFormCreateRequest extends QueryFormBase {}

// 更新查询表单请求
export interface QueryFormUpdateRequest extends Partial<QueryFormBase> {
  is_active?: boolean;
}

// 查询表单响应
export interface QueryFormResponse extends QueryFormBase, BaseTimestamp {
  id: number;
  is_active: boolean;
}

// 查询表单执行请求
export interface QueryFormExecuteRequest {
  form_id: number;
  params: Record<string, any>;
  server_name?: string;
}

// 查询表单历史记录
export interface QueryFormHistory extends BaseTimestamp {
  id: number;
  form_id: number;
  query_params: Record<string, any>;
  executed_sql?: string;
  execution_time?: number;
  row_count?: number;
  success: boolean;
  error_message?: string;
  user_id: string;
}

// SQL解析结果
export interface SQLParseResult {
  parameters: string[];
  suggested_fields: QueryFormField[];
  warnings: string[];
}

// 数据源测试请求
export interface DataSourceTestRequest {
  data_source_config: DataSourceConfig;
  server_name?: string;
}

// 数据源测试响应
export interface DataSourceTestResponse {
  success: boolean;
  data: Record<string, any>[];
  error_message?: string;
}

// 查询响应
export interface QueryResponse {
  data: Record<string, any>[];
  columns: string[];
  total: number;
  execution_time?: number;
  sql?: string;
  is_multiple?: boolean;
}

// API响应包装器
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: string[];
  meta?: Record<string, any>;
  timestamp: string;
}

// 表单构建器状态
export interface FormBuilderState {
  form: QueryFormBase;
  isDirty: boolean;
  isValidating: boolean;
  validationErrors: Record<string, string>;
  sqlParseResult?: SQLParseResult;
}

// 表单渲染状态
export interface FormRenderState {
  formId: number;
  formConfig: QueryFormConfig;
  values: Record<string, any>;
  isSubmitting: boolean;
  isLoading: boolean;
  errors: Record<string, string>;
  dataSourceCache: Record<string, any[]>;
}

// 表单管理状态
export interface FormManagementState {
  forms: QueryFormResponse[];
  currentForm?: QueryFormResponse;
  isLoading: boolean;
  error?: string;
  searchTerm: string;
  activeOnly: boolean;
  selectedForms: number[];
}

// 表单执行状态
export interface FormExecutionState {
  isExecuting: boolean;
  result?: QueryResponse;
  error?: string;
  history: QueryFormHistory[];
  isLoadingHistory: boolean;
}

// 表单验证错误
export interface FormValidationError {
  field: string;
  message: string;
  code: string;
}

// 表单预览数据
export interface FormPreviewData {
  form_info: {
    id: number;
    name: string;
    description?: string;
    is_active: boolean;
  };
  sql_template: string;
  form_config: QueryFormConfig;
  parameters: string[];
  warnings: string[];
}

// 表单操作类型
export enum FormAction {
  CREATE = 'create',
  UPDATE = 'update',
  DELETE = 'delete',
  DUPLICATE = 'duplicate',
  TOGGLE_STATUS = 'toggle_status',
  EXECUTE = 'execute',
  PREVIEW = 'preview',
}

// 表单操作结果
export interface FormActionResult {
  action: FormAction;
  success: boolean;
  message: string;
  data?: any;
  error?: string;
}