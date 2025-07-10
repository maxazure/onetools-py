/**
 * 动态表单渲染组件
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Form,
  Input,
  InputNumber,
  Select,
  DatePicker,
  TimePicker,
  Switch,
  Checkbox,
  Radio,
  Button,
  Row,
  Col,
  Card,
  Space,
  message,
  Spin,
  Alert,
  Tooltip,
  Empty,
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined,
  DownloadOutlined,
  HistoryOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import moment from 'moment';

import { useDatabaseContext } from '../contexts/DatabaseContext';

import {
  QueryFormField,
  QueryFormConfig,
  QueryFormResponse,
  QueryFormExecuteRequest,
  QueryResponse,
  FormRenderState,
  FieldType,
  MatchType,
  DataSourceConfig,
  StaticOption,
} from '../types/query-forms';
import { QueryResult, MultipleQueryResult } from '../types/api';
import { queryFormApi } from '../services/query-forms/query-form-api';
import QueryResultTable from './QueryResultTable';
import MultipleQueryResults from './MultipleQueryResults/MultipleQueryResults';
import QueryResults from './QueryResults/QueryResults';

const { TextArea } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { Group: RadioGroup } = Radio;
const { Group: CheckboxGroup } = Checkbox;

interface DynamicFormProps {
  form: QueryFormResponse;
  serverName?: string;
  onExecute?: (result: QueryResponse) => void;
  onError?: (error: string) => void;
  showResult?: boolean;
  autoSubmit?: boolean;
}

const DynamicForm: React.FC<DynamicFormProps> = ({
  form,
  serverName,
  onExecute,
  onError,
  showResult = true,
  autoSubmit = false,
}) => {
  const [formInstance] = Form.useForm();
  const { currentServer } = useDatabaseContext();
  const [state, setState] = useState<FormRenderState>({
    formId: form.id,
    formConfig: form.form_config,
    values: {},
    isSubmitting: false,
    isLoading: false,
    errors: {},
    dataSourceCache: {},
  });

  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);
  const [resultVisible, setResultVisible] = useState(false);

  // 转换QueryResponse为QueryResult或MultipleQueryResult
  const convertQueryResult = (result: QueryResponse): QueryResult | MultipleQueryResult => {
    if (result.is_multiple) {
      // 对于多结果集，假设data是结果集数组
      return {
        results: Array.isArray(result.data) ? result.data.map((item, index) => ({
          type: 'resultset' as const,
          index,
          columns: item.columns || result.columns || [],
          data: item.data || (Array.isArray(item) ? item : []),
          total: item.total || (Array.isArray(item.data) ? item.data.length : (Array.isArray(item) ? item.length : 0)),
          message: `结果集 ${index + 1}`
        })) : [],
        execution_time: result.execution_time || 0,
        is_multiple: true as const
      };
    } else {
      // 对于单结果集
      return {
        columns: result.columns || [],
        data: result.data || [],
        total_count: result.total || 0,
        execution_time: result.execution_time || 0,
        is_multiple: false
      };
    }
  };

  // 初始化表单
  useEffect(() => {
    setState(prev => ({
      ...prev,
      formId: form.id,
      formConfig: form.form_config,
    }));
    
    // 设置默认值
    const defaultValues: Record<string, any> = {};
    form.form_config.fields.forEach(field => {
      if (field.default_value) {
        defaultValues[field.parameter] = field.default_value;
      }
    });
    
    if (Object.keys(defaultValues).length > 0) {
      formInstance.setFieldsValue(defaultValues);
      setState(prev => ({ ...prev, values: defaultValues }));
    }
  }, [form, formInstance]);

  // 自动提交
  useEffect(() => {
    if (autoSubmit && Object.keys(state.values).length > 0) {
      handleSubmit();
    }
  }, [autoSubmit, state.values]);

  // 加载数据源
  const loadDataSource = useCallback(async (field: QueryFormField) => {
    if (!field.data_source || state.dataSourceCache[field.parameter]) {
      return;
    }

    try {
      setState(prev => ({ ...prev, isLoading: true }));
      
      const result = await queryFormApi.testDataSource({
        data_source_config: field.data_source,
        server_name: serverName || currentServer,
      });

      if (result.success && result.data) {
        setState(prev => ({
          ...prev,
          dataSourceCache: {
            ...prev.dataSourceCache,
            [field.parameter]: result.data?.data || [],
          },
        }));
      }
    } catch (error) {
      console.error('加载数据源失败:', error);
      message.error(`加载${field.label}数据源失败`);
    } finally {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, [serverName, state.dataSourceCache]);

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      await formInstance.validateFields();
      const values = formInstance.getFieldsValue();
      
      setState(prev => ({ ...prev, isSubmitting: true }));
      
      const executeRequest: QueryFormExecuteRequest = {
        form_id: form.id,
        params: values,
        server_name: serverName || currentServer, // 使用当前选择的服务器
      };
      
      const result = await queryFormApi.executeForm(executeRequest);
      
      if (result.success && result.data) {
        setQueryResult(result.data);
        setResultVisible(true);
        onExecute?.(result.data);
        message.success(`查询成功，返回${result.data.total}条记录`);
      } else {
        const errorMsg = result.errors?.join(', ') || '查询失败';
        message.error(errorMsg);
        onError?.(errorMsg);
      }
    } catch (error) {
      console.error('查询执行失败:', error);
      const errorMsg = error instanceof Error ? error.message : '查询执行失败';
      message.error(errorMsg);
      onError?.(errorMsg);
    } finally {
      setState(prev => ({ ...prev, isSubmitting: false }));
    }
  };

  // 重置表单
  const handleReset = () => {
    formInstance.resetFields();
    setState(prev => ({ ...prev, values: {}, errors: {} }));
    setQueryResult(null);
    setResultVisible(false);
  };

  // 渲染表单项
  const renderFormItem = (field: QueryFormField) => {
    const { parameter, label, field_type, required, placeholder, help_text, validation } = field;
    
    const commonProps = {
      placeholder,
      onChange: (value: any) => {
        setState(prev => ({
          ...prev,
          values: { ...prev.values, [parameter]: value },
        }));
      },
    };

    let inputElement: React.ReactNode;

    switch (field_type) {
      case FieldType.TEXT:
        inputElement = <Input {...commonProps} />;
        break;
        
      case FieldType.NUMBER:
        inputElement = (
          <InputNumber
            {...commonProps}
            style={{ width: '100%' }}
            min={validation?.min}
            max={validation?.max}
          />
        );
        break;
        
      case FieldType.EMAIL:
        inputElement = <Input {...commonProps} type="email" />;
        break;
        
      case FieldType.DATE:
        inputElement = (
          <DatePicker
            {...commonProps}
            style={{ width: '100%' }}
            format="YYYY-MM-DD"
          />
        );
        break;
        
      case FieldType.DATETIME:
        inputElement = (
          <DatePicker
            {...commonProps}
            style={{ width: '100%' }}
            showTime
            format="YYYY-MM-DD HH:mm:ss"
          />
        );
        break;
        
      case FieldType.TEXTAREA:
        inputElement = (
          <TextArea
            {...commonProps}
            rows={4}
            maxLength={validation?.max_length}
          />
        );
        break;
        
      case FieldType.SELECT:
        inputElement = (
          <Select
            {...commonProps}
            style={{ width: '100%' }}
            onFocus={() => loadDataSource(field)}
            loading={state.isLoading}
          >
            {renderSelectOptions(field)}
          </Select>
        );
        break;
        
      case FieldType.MULTISELECT:
        inputElement = (
          <Select
            {...commonProps}
            style={{ width: '100%' }}
            mode="multiple"
            onFocus={() => loadDataSource(field)}
            loading={state.isLoading}
          >
            {renderSelectOptions(field)}
          </Select>
        );
        break;
        
      case FieldType.RADIO:
        inputElement = (
          <RadioGroup>
            {renderRadioOptions(field)}
          </RadioGroup>
        );
        break;
        
      case FieldType.CHECKBOX:
        inputElement = (
          <CheckboxGroup>
            {renderCheckboxOptions(field)}
          </CheckboxGroup>
        );
        break;
        
      default:
        inputElement = <Input {...commonProps} />;
    }

    const rules = [];
    if (required) {
      rules.push({ required: true, message: `请输入${label}` });
    }
    if (validation?.pattern) {
      rules.push({
        pattern: new RegExp(validation.pattern),
        message: validation.message || '格式不正确',
      });
    }
    if (validation?.min_length) {
      rules.push({
        min: validation.min_length,
        message: `最少输入${validation.min_length}个字符`,
      });
    }
    if (validation?.max_length) {
      rules.push({
        max: validation.max_length,
        message: `最多输入${validation.max_length}个字符`,
      });
    }

    return (
      <Col
        key={parameter}
        span={24 / (form.form_config.layout.columns || 3)}
        style={{ marginBottom: form.form_config.layout.field_spacing || '16px' }}
      >
        <Form.Item
          label={
            <Space>
              {label}
              {help_text && (
                <Tooltip title={help_text}>
                  <InfoCircleOutlined style={{ color: '#1890ff' }} />
                </Tooltip>
              )}
            </Space>
          }
          name={parameter}
          rules={rules}
          labelCol={{ style: { width: form.form_config.layout.label_width || '120px' } }}
        >
          {inputElement}
        </Form.Item>
      </Col>
    );
  };

  // 渲染选择项
  const renderSelectOptions = (field: QueryFormField) => {
    const dataSource = state.dataSourceCache[field.parameter] || [];
    
    if (field.data_source?.type === 'static' && field.data_source.options) {
      return field.data_source.options.map((option: StaticOption) => (
        <Option key={option.value} value={option.value}>
          {option.label}
        </Option>
      ));
    }
    
    return dataSource.map((item: any, index: number) => (
      <Option key={index} value={item.value || item.id}>
        {item.label || item.name || item.display_value || item.value}
      </Option>
    ));
  };

  // 渲染单选项
  const renderRadioOptions = (field: QueryFormField) => {
    const dataSource = state.dataSourceCache[field.parameter] || [];
    
    if (field.data_source?.type === 'static' && field.data_source.options) {
      return field.data_source.options.map((option: StaticOption) => (
        <Radio key={option.value} value={option.value}>
          {option.label}
        </Radio>
      ));
    }
    
    return dataSource.map((item: any, index: number) => (
      <Radio key={index} value={item.value || item.id}>
        {item.label || item.name || item.display_value || item.value}
      </Radio>
    ));
  };

  // 渲染复选项
  const renderCheckboxOptions = (field: QueryFormField) => {
    const dataSource = state.dataSourceCache[field.parameter] || [];
    
    if (field.data_source?.type === 'static' && field.data_source.options) {
      return field.data_source.options.map((option: StaticOption) => (
        <Checkbox key={option.value} value={option.value}>
          {option.label}
        </Checkbox>
      ));
    }
    
    return dataSource.map((item: any, index: number) => (
      <Checkbox key={index} value={item.value || item.id}>
        {item.label || item.name || item.display_value || item.value}
      </Checkbox>
    ));
  };

  // 渲染按钮
  const renderButtons = () => {
    const buttons = (
      <Space>
        <Button
          type="primary"
          icon={<SearchOutlined />}
          loading={state.isSubmitting}
          onClick={handleSubmit}
        >
          查询
        </Button>
        <Button
          icon={<ReloadOutlined />}
          onClick={handleReset}
        >
          重置
        </Button>
        {queryResult && (
          <Button
            icon={<DownloadOutlined />}
            onClick={() => {
              // 导出功能待实现
              message.info('导出功能待实现');
            }}
          >
            导出
          </Button>
        )}
      </Space>
    );

    return form.form_config.layout.button_position === 'right' ? (
      <Col span={6} style={{ paddingTop: '32px' }}>
        {buttons}
      </Col>
    ) : (
      <Row justify="center" style={{ marginTop: '24px' }}>
        {buttons}
      </Row>
    );
  };

  if (!form.form_config.fields || form.form_config.fields.length === 0) {
    return (
      <Empty
        description="表单配置为空"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
    );
  }

  return (
    <div className="dynamic-form">
      <Card
        title={form.form_config.title || form.form_name}
        extra={
          <Space>
            <Tooltip title="查看执行历史">
              <Button
                type="text"
                icon={<HistoryOutlined />}
                onClick={() => {
                  // 显示历史记录
                  message.info('历史记录功能待实现');
                }}
              />
            </Tooltip>
          </Space>
        }
      >
        {form.form_config.description && (
          <Alert
            message={form.form_config.description}
            type="info"
            showIcon
            style={{ marginBottom: '16px' }}
          />
        )}

        <Form
          form={formInstance}
          layout="horizontal"
          initialValues={state.values}
        >
          <Row gutter={16}>
            {form.form_config.fields
              .sort((a, b) => a.order - b.order)
              .map(field => renderFormItem(field))}
            
            {form.form_config.layout.button_position === 'right' && renderButtons()}
          </Row>
          
          {form.form_config.layout.button_position === 'bottom' && renderButtons()}
        </Form>
      </Card>

      {showResult && resultVisible && queryResult && (
        <div style={{ marginTop: '16px' }}>
          {queryResult.is_multiple ? (
            <MultipleQueryResults
              data={convertQueryResult(queryResult) as MultipleQueryResult}
              loading={state.isSubmitting}
              error={null}
              onExport={(format) => {
                message.info(`导出功能待实现 (${format})`);
              }}
              onRefresh={() => {
                message.info('刷新功能待实现');
              }}
            />
          ) : (
            <QueryResults
              data={convertQueryResult(queryResult) as QueryResult}
              loading={state.isSubmitting}
              error={null}
              onExport={(format) => {
                message.info(`导出功能待实现 (${format})`);
              }}
              onRefresh={() => {
                message.info('刷新功能待实现');
              }}
            />
          )}
        </div>
      )}
    </div>
  );
};

export default DynamicForm;