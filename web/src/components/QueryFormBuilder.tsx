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
import CodeMirror from '@uiw/react-codemirror';
import { sql } from '@codemirror/lang-sql';
import { oneDark } from '@codemirror/theme-one-dark';

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
import { queryFormApi } from '../services/query-form-api';

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
      target_database: '',
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
          target_database: initialForm.target_database || '',
        },
      }));
      form.setFieldsValue({
        form_name: initialForm.form_name,
        form_description: initialForm.form_description,
        sql_template: initialForm.sql_template,
        target_database: initialForm.target_database,
        ...initialForm.form_config,
      });
    }
  }, [initialForm, form]);

  // 解析SQL模板
  const handleSQLParse = useCallback(async (sqlTemplate: string) => {
    if (!sqlTemplate.trim()) return;

    try {
      setState(prev => ({ ...prev, isValidating: true }));
      const result = await queryFormApi.parseSQLTemplate(sqlTemplate);
      
      if (result.success && result.data) {
        setState(prev => ({
          ...prev,
          sqlParseResult: result.data,
          form: {
            ...prev.form,
            form_config: {
              ...prev.form.form_config,
              fields: result.data.suggested_fields,
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
      message.error('解析SQL失败');
      console.error('SQL解析失败:', error);
    } finally {
      setState(prev => ({ ...prev, isValidating: false }));
    }
  }, []);

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
          fields: prev.form.form_config.fields.map((f, i) => 
            i === index ? { ...f, ...field } : f
          ),
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
    try {
      await form.validateFields();
      setLoading(true);

      const formData = mode === 'create' 
        ? state.form as QueryFormCreateRequest
        : state.form as QueryFormUpdateRequest;

      const result = mode === 'create'
        ? await queryFormApi.createForm(formData)
        : await queryFormApi.updateForm(initialForm!.id, formData);

      if (result.success && result.data) {
        message.success(`${mode === 'create' ? '创建' : '更新'}表单成功`);
        setState(prev => ({ ...prev, isDirty: false }));
        onSave?.(result.data);
      } else {
        message.error(`${mode === 'create' ? '创建' : '更新'}表单失败`);
      }
    } catch (error) {
      message.error('表单验证失败');
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
              {Object.values(MatchType).map(type => (
                <Option key={type} value={type}>{type}</Option>
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
    </Card>
  );

  return (
    <div className="query-form-builder">
      <Form form={form} layout="vertical">
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="基本信息" key="basic">
            <Card title="表单基本信息">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="表单名称"
                    name="form_name"
                    rules={[{ required: true, message: '请输入表单名称' }]}
                  >
                    <Input
                      placeholder="请输入表单名称"
                      onChange={(e) => setState(prev => ({
                        ...prev,
                        form: { ...prev.form, form_name: e.target.value },
                        isDirty: true,
                      }))}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="目标数据库" name="target_database">
                    <Input
                      placeholder="目标数据库名称"
                      onChange={(e) => setState(prev => ({
                        ...prev,
                        form: { ...prev.form, target_database: e.target.value },
                        isDirty: true,
                      }))}
                    />
                  </Form.Item>
                </Col>
              </Row>
              
              <Form.Item label="表单描述" name="form_description">
                <TextArea
                  rows={3}
                  placeholder="请输入表单描述"
                  onChange={(e) => setState(prev => ({
                    ...prev,
                    form: { ...prev.form, form_description: e.target.value },
                    isDirty: true,
                  }))}
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
                <CodeMirror
                  value={state.form.sql_template}
                  height="300px"
                  extensions={[sql()]}
                  theme={oneDark}
                  onChange={(value) => setState(prev => ({
                    ...prev,
                    form: { ...prev.form, sql_template: value },
                    isDirty: true,
                  }))}
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
                <Droppable droppableId="fields">
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
              disabled={!state.isDirty}
            >
              {mode === 'create' ? '创建' : '更新'}
            </Button>
          </Space>
        </Row>
      </Form>

      {/* 预览模态框 */}
      <Modal
        title="表单预览"
        visible={previewVisible}
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