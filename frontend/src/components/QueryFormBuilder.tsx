/**
 * 动态查询表单构建器组件
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Space,
  Row,
  Col,
  Select,
  InputNumber,
  Switch,
  Divider,
  message,
  Alert,
  Collapse,
  Badge,
  Tooltip,
  Modal,
  Typography,
  Tabs,
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  CopyOutlined,
  EditOutlined,
  BugOutlined,
  EyeOutlined,
  SaveOutlined,
  ReloadOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import SqlEditor from './SqlEditor/SqlEditor';

import {
  QueryFormField,
  QueryFormConfig,
  QueryFormBase,
  FieldType,
  MatchType,
  DataSourceType,
  StaticOption,
  DataSourceConfig,
  ValidationRule,
  SQLParseResult,
  FormBuilderState,
  QueryFormCreateRequest,
  QueryFormUpdateRequest,
  QueryFormResponse,
} from '../types/query-forms';
import { queryFormApi } from '../services/query-forms/query-form-api';

const { TextArea } = Input;
const { Option } = Select;
const { Panel } = Collapse;
const { Text, Title } = Typography;
const { TabPane } = Tabs;

interface QueryFormBuilderProps {
  initialForm?: QueryFormResponse;
  onSave?: (form: QueryFormResponse) => void;
  onCancel?: () => void;
  mode?: 'create' | 'edit';
}

const QueryFormBuilder: React.FC<QueryFormBuilderProps> = ({
  initialForm,
  onSave,
  onCancel,
  mode = 'create',
}) => {
  const [form] = Form.useForm();
  const [state, setState] = useState<FormBuilderState>({
    form: {
      form_name: '',
      form_description: '',
      sql_template: '',
      form_config: {
        title: '',
        description: '',
        fields: [],
        layout: {
          columns: 3,
          button_position: 'bottom',
          label_width: '120px',
          field_spacing: '16px',
        },
      },
    },
    isDirty: false,
    isValidating: false,
    validationErrors: {},
  });

  const [loading, setLoading] = useState(false);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [activeTab, setActiveTab] = useState('basic');

  // 初始化表单数据
  useEffect(() => {
    if (initialForm) {
      setState(prev => ({
        ...prev,
        form: {
          form_name: initialForm.form_name,
          form_description: initialForm.form_description || '',
          sql_template: initialForm.sql_template,
          form_config: initialForm.form_config,
        },
      }));
      form.setFieldsValue({
        form_name: initialForm.form_name,
        form_description: initialForm.form_description,
        sql_template: initialForm.sql_template,
        ...initialForm.form_config,
      });
    }
  }, [initialForm, form]);

  // 解析SQL模板
  const handleSQLParse = useCallback(async (sqlTemplate: string) => {
    if (!sqlTemplate.trim()) return;

    console.log('🔍 开始解析SQL模板', sqlTemplate);
    try {
      setState(prev => ({ ...prev, isValidating: true }));
      const result = await queryFormApi.parseSQLTemplate(sqlTemplate);
      console.log('📥 SQL解析结果', result);
      
      if (result.success && result.data) {
        setState(prev => ({
          ...prev,
          sqlParseResult: result.data,
          form: {
            ...prev.form,
            form_config: {
              ...prev.form.form_config,
              fields: result.data?.suggested_fields || [],
            },
          },
          isDirty: true,
        }));
        
        if (result.data.warnings.length > 0) {
          message.warning(`SQL解析完成，但有${result.data.warnings.length}个警告`);
        } else {
          message.success(`成功解析SQL，发现${result.data.parameters.length}个参数`);
        }
      }
    } catch (error) {
      console.log('❌ SQL解析失败', error);
      message.error('解析SQL失败: ' + (error as Error).message);
      console.error('SQL解析失败:', error);
    } finally {
      setState(prev => ({ ...prev, isValidating: false }));
    }
  }, []);

  // 根据字段类型获取默认匹配类型
  const getDefaultMatchType = (fieldType: FieldType): MatchType => {
    switch (fieldType) {
      case FieldType.NUMBER:
        return MatchType.EXACT;
      case FieldType.TEXT:
      case FieldType.EMAIL:
      case FieldType.TEXTAREA:
        return MatchType.LIKE;
      case FieldType.DATE:
      case FieldType.DATETIME:
        return MatchType.EXACT;
      case FieldType.SELECT:
      case FieldType.RADIO:
        return MatchType.EXACT;
      case FieldType.MULTISELECT:
      case FieldType.CHECKBOX:
        return MatchType.IN_LIST;
      default:
        return MatchType.EXACT;
    }
  };

  // 根据字段类型获取可用的匹配类型
  const getAvailableMatchTypes = (fieldType: FieldType): MatchType[] => {
    switch (fieldType) {
      case FieldType.NUMBER:
        return [
          MatchType.EXACT,
          MatchType.NOT_EQUAL,
          MatchType.GREATER,
          MatchType.GREATER_EQUAL,
          MatchType.LESS,
          MatchType.LESS_EQUAL,
          MatchType.BETWEEN,
          MatchType.IN_LIST,
          MatchType.IS_NULL,
          MatchType.IS_NOT_NULL,
        ];
      case FieldType.TEXT:
      case FieldType.EMAIL:
      case FieldType.TEXTAREA:
        return [
          MatchType.EXACT,
          MatchType.NOT_EQUAL,
          MatchType.LIKE,
          MatchType.NOT_LIKE,
          MatchType.START_WITH,
          MatchType.END_WITH,
          MatchType.CONTAINS,
          MatchType.IN_LIST,
          MatchType.IS_NULL,
          MatchType.IS_NOT_NULL,
        ];
      case FieldType.DATE:
      case FieldType.DATETIME:
        return [
          MatchType.EXACT,
          MatchType.NOT_EQUAL,
          MatchType.GREATER,
          MatchType.GREATER_EQUAL,
          MatchType.LESS,
          MatchType.LESS_EQUAL,
          MatchType.BETWEEN,
          MatchType.IS_NULL,
          MatchType.IS_NOT_NULL,
        ];
      case FieldType.SELECT:
      case FieldType.RADIO:
        return [
          MatchType.EXACT,
          MatchType.NOT_EQUAL,
          MatchType.IN_LIST,
          MatchType.IS_NULL,
          MatchType.IS_NOT_NULL,
        ];
      case FieldType.MULTISELECT:
      case FieldType.CHECKBOX:
        return [
          MatchType.IN_LIST,
          MatchType.NOT_IN_LIST,
          MatchType.IS_NULL,
          MatchType.IS_NOT_NULL,
        ];
      default:
        return Object.values(MatchType);
    }
  };

  // 获取匹配类型的显示名称
  const getMatchTypeLabel = (matchType: MatchType): string => {
    switch (matchType) {
      case MatchType.EXACT:
        return '等于 (=)';
      case MatchType.NOT_EQUAL:
        return '不等于 (<>)';
      case MatchType.GREATER:
        return '大于 (>)';
      case MatchType.GREATER_EQUAL:
        return '大于等于 (>=)';
      case MatchType.LESS:
        return '小于 (<)';
      case MatchType.LESS_EQUAL:
        return '小于等于 (<=)';
      case MatchType.BETWEEN:
        return '区间匹配 (BETWEEN)';
      case MatchType.LIKE:
        return '模糊匹配 (LIKE)';
      case MatchType.NOT_LIKE:
        return '不匹配 (NOT LIKE)';
      case MatchType.START_WITH:
        return '开头匹配';
      case MatchType.END_WITH:
        return '结尾匹配';
      case MatchType.CONTAINS:
        return '包含';
      case MatchType.IN_LIST:
        return '在列表中 (IN)';
      case MatchType.NOT_IN_LIST:
        return '不在列表中 (NOT IN)';
      case MatchType.IS_NULL:
        return '为空 (IS NULL)';
      case MatchType.IS_NOT_NULL:
        return '不为空 (IS NOT NULL)';
      default:
        return matchType;
    }
  };

  // 字段操作
  const handleFieldAdd = () => {
    const newField: QueryFormField = {
      parameter: '@NewParam',
      label: '新字段',
      field_type: FieldType.TEXT,
      required: false,
      match_type: MatchType.EXACT,
      placeholder: '请输入',
      order: state.form.form_config.fields.length + 1,
    };

    setState(prev => ({
      ...prev,
      form: {
        ...prev.form,
        form_config: {
          ...prev.form.form_config,
          fields: [...prev.form.form_config.fields, newField],
        },
      },
      isDirty: true,
    }));
  };

  const handleFieldUpdate = (index: number, field: Partial<QueryFormField>) => {
    setState(prev => ({
      ...prev,
      form: {
        ...prev.form,
        form_config: {
          ...prev.form.form_config,
          fields: prev.form.form_config.fields.map((f, i) => {
            if (i === index) {
              const updatedField = { ...f, ...field };
              
              // 如果字段类型发生变化，自动选择适合的匹配类型
              if (field.field_type && field.field_type !== f.field_type) {
                updatedField.match_type = getDefaultMatchType(field.field_type);
              }
              
              return updatedField;
            }
            return f;
          }),
        },
      },
      isDirty: true,
    }));
  };

  const handleFieldDelete = (index: number) => {
    setState(prev => ({
      ...prev,
      form: {
        ...prev.form,
        form_config: {
          ...prev.form.form_config,
          fields: prev.form.form_config.fields.filter((_, i) => i !== index),
        },
      },
      isDirty: true,
    }));
  };

  const handleFieldDuplicate = (index: number) => {
    const fieldToCopy = state.form.form_config.fields[index];
    const newField: QueryFormField = {
      ...fieldToCopy,
      parameter: `${fieldToCopy.parameter}_copy`,
      label: `${fieldToCopy.label} (副本)`,
      order: state.form.form_config.fields.length + 1,
    };

    setState(prev => ({
      ...prev,
      form: {
        ...prev.form,
        form_config: {
          ...prev.form.form_config,
          fields: [...prev.form.form_config.fields, newField],
        },
      },
      isDirty: true,
    }));
  };

  // 拖拽排序
  const handleDragEnd = (result: any) => {
    if (!result.destination) return;

    const fields = Array.from(state.form.form_config.fields);
    const [reorderedField] = fields.splice(result.source.index, 1);
    fields.splice(result.destination.index, 0, reorderedField);

    // 重新设置order
    const reorderedFields = fields.map((field, index) => ({
      ...field,
      order: index + 1,
    }));

    setState(prev => ({
      ...prev,
      form: {
        ...prev.form,
        form_config: {
          ...prev.form.form_config,
          fields: reorderedFields,
        },
      },
      isDirty: true,
    }));
  };

  // 保存表单
  const handleSave = async () => {
    console.log('🚀 开始保存表单', { mode, form: state.form });
    try {
      await form.validateFields();
      console.log('✅ 表单验证通过');
      setLoading(true);

      if (mode === 'create') {
        const createData: QueryFormCreateRequest = {
          form_name: state.form.form_name,
          form_description: state.form.form_description,
          sql_template: state.form.sql_template,
          form_config: state.form.form_config,
        };
        console.log('📤 发送创建请求', createData);
        const result = await queryFormApi.createForm(createData);
        console.log('📥 收到创建响应', result);
        
        if (result.success && result.data) {
          console.log('✅ 创建成功');
          message.success('创建表单成功');
          setState(prev => ({ ...prev, isDirty: false }));
          onSave?.(result.data);
        } else {
          console.log('❌ 创建失败', result);
          message.error('创建表单失败');
        }
      } else {
        const updateData: QueryFormUpdateRequest = {
          form_name: state.form.form_name,
          form_description: state.form.form_description,
          sql_template: state.form.sql_template,
          form_config: state.form.form_config,
        };
        const result = await queryFormApi.updateForm(initialForm!.id, updateData);
        
        if (result.success && result.data) {
          message.success('更新表单成功');
          setState(prev => ({ ...prev, isDirty: false }));
          onSave?.(result.data);
        } else {
          message.error('更新表单失败');
        }
      }
    } catch (error) {
      console.log('❌ 保存过程中出错', error);
      if (error instanceof Error && error.message.includes('validation')) {
        message.error('表单验证失败');
      } else {
        message.error('保存失败: ' + (error as Error).message);
      }
      console.error('保存失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 预览表单
  const handlePreview = () => {
    setPreviewVisible(true);
  };

  // 渲染字段编辑器
  const renderFieldEditor = (field: QueryFormField, index: number) => (
    <Card
      key={index}
      size="small"
      title={
        <Space>
          <Text strong>{field.label}</Text>
          <Badge count={field.parameter} style={{ backgroundColor: '#108ee9' }} />
        </Space>
      }
      extra={
        <Space>
          <Tooltip title="复制字段">
            <Button
              type="text"
              icon={<CopyOutlined />}
              onClick={() => handleFieldDuplicate(index)}
            />
          </Tooltip>
          <Tooltip title="删除字段">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleFieldDelete(index)}
            />
          </Tooltip>
        </Space>
      }
      style={{ marginBottom: 16 }}
    >
      <Row gutter={16}>
        <Col span={8}>
          <Form.Item label="参数名" required>
            <Input
              value={field.parameter}
              onChange={(e) => handleFieldUpdate(index, { parameter: e.target.value })}
              placeholder="@参数名"
            />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item label="显示标签" required>
            <Input
              value={field.label}
              onChange={(e) => handleFieldUpdate(index, { label: e.target.value })}
              placeholder="字段显示名称"
            />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item label="字段类型">
            <Select
              value={field.field_type}
              onChange={(value) => handleFieldUpdate(index, { field_type: value })}
            >
              {Object.values(FieldType).map(type => (
                <Option key={type} value={type}>{type}</Option>
              ))}
            </Select>
          </Form.Item>
        </Col>
      </Row>
      
      <Row gutter={16}>
        <Col span={8}>
          <Form.Item label="匹配类型">
            <Select
              value={field.match_type}
              onChange={(value) => handleFieldUpdate(index, { match_type: value })}
            >
              {getAvailableMatchTypes(field.field_type).map(type => (
                <Option key={type} value={type}>
                  {getMatchTypeLabel(type)}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item label="占位符">
            <Input
              value={field.placeholder}
              onChange={(e) => handleFieldUpdate(index, { placeholder: e.target.value })}
              placeholder="输入提示"
            />
          </Form.Item>
        </Col>
        <Col span={4}>
          <Form.Item label="必填">
            <Switch
              checked={field.required}
              onChange={(checked) => handleFieldUpdate(index, { required: checked })}
            />
          </Form.Item>
        </Col>
        <Col span={4}>
          <Form.Item label="网格跨度">
            <InputNumber
              min={1}
              max={4}
              value={field.grid_span || 1}
              onChange={(value) => handleFieldUpdate(index, { grid_span: value || 1 })}
            />
          </Form.Item>
        </Col>
      </Row>
      
      {/* 数据源配置 */}
      {(field.field_type === FieldType.SELECT || field.field_type === FieldType.MULTISELECT || 
        field.field_type === FieldType.RADIO || field.field_type === FieldType.CHECKBOX) && (
        <div style={{ marginTop: 16 }}>
          <Form.Item label="数据源类型">
            <Select
              value={field.data_source?.type || 'static'}
              onChange={(value) => handleFieldUpdate(index, { 
                data_source: { 
                  type: value as DataSourceType,
                  options: value === 'static' ? [{ label: '选项1', value: 'option1' }] : undefined,
                  sql: value === 'sql' ? 'SELECT value, label FROM table_name' : undefined,
                  value_column: value === 'sql' ? 'value' : undefined,
                  display_column: value === 'sql' ? 'label' : undefined,
                }
              })}
            >
              <Option value="static">静态选项</Option>
              <Option value="sql">SQL查询</Option>
            </Select>
          </Form.Item>
          
          {field.data_source?.type === 'static' && (
            <Form.Item label="静态选项">
              <div>
                {field.data_source.options?.map((option, optionIndex) => (
                  <Row key={optionIndex} gutter={8} style={{ marginBottom: 8 }}>
                    <Col span={8}>
                      <Input
                        placeholder="显示文本"
                        value={option.label}
                        onChange={(e) => {
                          const newOptions = [...(field.data_source?.options || [])];
                          newOptions[optionIndex] = { ...option, label: e.target.value };
                          handleFieldUpdate(index, {
                            data_source: { ...field.data_source!, options: newOptions }
                          });
                        }}
                      />
                    </Col>
                    <Col span={8}>
                      <Input
                        placeholder="值"
                        value={option.value}
                        onChange={(e) => {
                          const newOptions = [...(field.data_source?.options || [])];
                          newOptions[optionIndex] = { ...option, value: e.target.value };
                          handleFieldUpdate(index, {
                            data_source: { ...field.data_source!, options: newOptions }
                          });
                        }}
                      />
                    </Col>
                    <Col span={8}>
                      <Space>
                        <Button
                          size="small"
                          icon={<PlusOutlined />}
                          onClick={() => {
                            const newOptions = [...(field.data_source?.options || [])];
                            newOptions.splice(optionIndex + 1, 0, { label: '新选项', value: 'new_option' });
                            handleFieldUpdate(index, {
                              data_source: { ...field.data_source!, options: newOptions }
                            });
                          }}
                        />
                        {field.data_source?.options && field.data_source.options.length > 1 && (
                          <Button
                            size="small"
                            danger
                            icon={<DeleteOutlined />}
                            onClick={() => {
                              const newOptions = [...(field.data_source?.options || [])];
                              newOptions.splice(optionIndex, 1);
                              handleFieldUpdate(index, {
                                data_source: { ...field.data_source!, options: newOptions }
                              });
                            }}
                          />
                        )}
                      </Space>
                    </Col>
                  </Row>
                ))}
              </div>
            </Form.Item>
          )}
          
          {field.data_source?.type === 'sql' && (
            <div>
              <Form.Item 
                label="SQL查询语句" 
                help={
                  <div>
                    <div>查询语句应返回用于显示和存储的列，示例：</div>
                    <div style={{ fontFamily: 'monospace', fontSize: '12px', marginTop: '4px' }}>
                      <div>-- 用户组选项</div>
                      <div>SELECT usergroupid as value, usergroupname as label</div>
                      <div>FROM usergroups WHERE is_active = 1</div>
                      <div>ORDER BY usergroupname</div>
                    </div>
                  </div>
                }
              >
                <SqlEditor
                  value={field.data_source.sql || 'SELECT value_column as value, display_column as label\nFROM table_name\nWHERE condition = 1\nORDER BY display_column'}
                  onChange={(value) => handleFieldUpdate(index, {
                    data_source: { ...field.data_source!, sql: value }
                  })}
                  height="120px"
                  showToolbar={false}
                  placeholder="请输入SQL查询语句"
                />
              </Form.Item>
              
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item label="值字段" help="用于存储的字段名">
                    <Input
                      placeholder="value"
                      value={field.data_source.value_column || ''}
                      onChange={(e) => handleFieldUpdate(index, {
                        data_source: { ...field.data_source!, value_column: e.target.value }
                      })}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="显示字段" help="用于显示的字段名">
                    <Input
                      placeholder="label"
                      value={field.data_source.display_column || ''}
                      onChange={(e) => handleFieldUpdate(index, {
                        data_source: { ...field.data_source!, display_column: e.target.value }
                      })}
                    />
                  </Form.Item>
                </Col>
              </Row>
              
              <Form.Item>
                <Button
                  type="dashed"
                  icon={<BugOutlined />}
                  onClick={async () => {
                    try {
                      const result = await queryFormApi.testDataSource({
                        data_source_config: field.data_source!,
                        server_name: '', // 使用当前服务器
                      });
                      
                      if (result.success && result.data) {
                        message.success(`测试成功，返回${result.data.data.length}条记录`);
                      } else {
                        message.error('测试失败: ' + (result.errors?.join(', ') || '未知错误'));
                      }
                    } catch (error) {
                      message.error('测试失败: ' + (error as Error).message);
                    }
                  }}
                >
                  测试数据源
                </Button>
              </Form.Item>
            </div>
          )}
        </div>
      )}
    </Card>
  );

  return (
    <div className="query-form-builder">
      <Form form={form} layout="vertical">
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="基本信息" key="basic">
            <Card title="表单基本信息">
              <Form.Item
                label="表单名称"
                name="form_name"
                rules={[{ required: true, message: '请输入表单名称' }]}
              >
                <Input
                  placeholder="请输入表单名称"
                  value={state.form.form_name}
                  onChange={(e) => {
                    const value = e.target.value;
                    setState(prev => ({
                      ...prev,
                      form: { ...prev.form, form_name: value },
                      isDirty: true,
                    }));
                    form.setFieldsValue({ form_name: value });
                  }}
                />
              </Form.Item>
              
              <Form.Item label="表单描述" name="form_description">
                <TextArea
                  rows={3}
                  placeholder="请输入表单描述"
                  value={state.form.form_description}
                  onChange={(e) => {
                    const value = e.target.value;
                    setState(prev => ({
                      ...prev,
                      form: { ...prev.form, form_description: value },
                      isDirty: true,
                    }));
                    form.setFieldsValue({ form_description: value });
                  }}
                />
              </Form.Item>
            </Card>
          </TabPane>

          <TabPane tab="SQL模板" key="sql">
            <Card 
              title="SQL模板配置"
              extra={
                <Space>
                  <Button
                    type="primary"
                    icon={<BugOutlined />}
                    loading={state.isValidating}
                    onClick={() => handleSQLParse(state.form.sql_template)}
                  >
                    解析SQL
                  </Button>
                </Space>
              }
            >
              <Form.Item
                label="SQL模板"
                name="sql_template"
                rules={[{ required: true, message: '请输入SQL模板' }]}
              >
                <SqlEditor
                  value={state.form.sql_template}
                  onChange={(value) => {
                    setState(prev => ({
                      ...prev,
                      form: { ...prev.form, sql_template: value },
                      isDirty: true,
                    }));
                    form.setFieldsValue({ sql_template: value });
                  }}
                  height="300px"
                  showToolbar={false}
                  placeholder="请输入SQL模板，使用@参数名作为占位符，例如：SELECT * FROM users WHERE name = @username"
                />
              </Form.Item>
              
              {state.sqlParseResult && (
                <Alert
                  message={`发现${state.sqlParseResult.parameters.length}个参数`}
                  description={
                    <div>
                      <p>参数列表: {state.sqlParseResult.parameters.join(', ')}</p>
                      {state.sqlParseResult.warnings.length > 0 && (
                        <div>
                          <p>警告信息:</p>
                          <ul>
                            {state.sqlParseResult.warnings.map((warning, index) => (
                              <li key={index}>{warning}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  }
                  type={state.sqlParseResult.warnings.length > 0 ? "warning" : "success"}
                  showIcon
                />
              )}
            </Card>
          </TabPane>

          <TabPane tab="字段配置" key="fields">
            <Card
              title="字段配置"
              extra={
                <Space>
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={handleFieldAdd}
                  >
                    添加字段
                  </Button>
                </Space>
              }
            >
              <DragDropContext onDragEnd={handleDragEnd}>
                <Droppable 
                  droppableId="fields" 
                  isDropDisabled={false}
                  isCombineEnabled={false}
                >
                  {(provided) => (
                    <div {...provided.droppableProps} ref={provided.innerRef}>
                      {state.form.form_config.fields.map((field, index) => (
                        <Draggable
                          key={index}
                          draggableId={`field-${index}`}
                          index={index}
                        >
                          {(provided) => (
                            <div
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              {...provided.dragHandleProps}
                            >
                              {renderFieldEditor(field, index)}
                            </div>
                          )}
                        </Draggable>
                      ))}
                      {provided.placeholder}
                    </div>
                  )}
                </Droppable>
              </DragDropContext>
            </Card>
          </TabPane>

          <TabPane tab="布局设置" key="layout">
            <Card title="布局配置">
              <Row gutter={16}>
                <Col span={6}>
                  <Form.Item label="列数">
                    <InputNumber
                      min={1}
                      max={6}
                      value={state.form.form_config.layout.columns}
                      onChange={(value) => setState(prev => ({
                        ...prev,
                        form: {
                          ...prev.form,
                          form_config: {
                            ...prev.form.form_config,
                            layout: {
                              ...prev.form.form_config.layout,
                              columns: value || 3,
                            },
                          },
                        },
                        isDirty: true,
                      }))}
                    />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item label="按钮位置">
                    <Select
                      value={state.form.form_config.layout.button_position}
                      onChange={(value) => setState(prev => ({
                        ...prev,
                        form: {
                          ...prev.form,
                          form_config: {
                            ...prev.form.form_config,
                            layout: {
                              ...prev.form.form_config.layout,
                              button_position: value,
                            },
                          },
                        },
                        isDirty: true,
                      }))}
                    >
                      <Option value="bottom">底部</Option>
                      <Option value="right">右侧</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item label="标签宽度">
                    <Input
                      value={state.form.form_config.layout.label_width}
                      onChange={(e) => setState(prev => ({
                        ...prev,
                        form: {
                          ...prev.form,
                          form_config: {
                            ...prev.form.form_config,
                            layout: {
                              ...prev.form.form_config.layout,
                              label_width: e.target.value,
                            },
                          },
                        },
                        isDirty: true,
                      }))}
                      placeholder="120px"
                    />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item label="字段间距">
                    <Input
                      value={state.form.form_config.layout.field_spacing}
                      onChange={(e) => setState(prev => ({
                        ...prev,
                        form: {
                          ...prev.form,
                          form_config: {
                            ...prev.form.form_config,
                            layout: {
                              ...prev.form.form_config.layout,
                              field_spacing: e.target.value,
                            },
                          },
                        },
                        isDirty: true,
                      }))}
                      placeholder="16px"
                    />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </TabPane>
        </Tabs>

        <Divider />

        <Row justify="end">
          <Space>
            <Button onClick={onCancel}>
              取消
            </Button>
            <Button
              icon={<EyeOutlined />}
              onClick={handlePreview}
            >
              预览
            </Button>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              loading={loading}
              onClick={handleSave}
              disabled={mode === 'edit' && !state.isDirty}
            >
              {mode === 'create' ? '创建' : '更新'}
            </Button>
          </Space>
        </Row>
      </Form>

      {/* 预览模态框 */}
      <Modal
        title="表单预览"
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={null}
        width={800}
      >
        {/* 这里会渲染动态表单预览 */}
        <div>表单预览功能待实现</div>
      </Modal>
    </div>
  );
};

export default QueryFormBuilder;