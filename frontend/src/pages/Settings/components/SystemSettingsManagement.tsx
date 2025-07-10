/**
 * 系统设置管理组件
 * 基于 SystemSettings 模型的 UI 界面
 */

import React, { useState } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Space,
  message,
  Popconfirm,
  Typography,
  Tag,
  Card,
  Divider,
  Row,
  Col,
  Tooltip,
  DatePicker,
  Select,
  Switch,
  InputNumber,
  Alert
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SettingOutlined,
  SearchOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  KeyOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { settingsApi } from '../../../services/api';

const { Text, Title, Paragraph } = Typography;
const { TextArea } = Input;

interface SystemSetting {
  id: number;
  key: string;
  value: string;
  description: string;
  created_at: string;
  updated_at: string;
}

interface SystemSettingFormData {
  key: string;
  value: string;
  description: string;
}

// 预定义的系统设置类型
const SETTING_TYPES = [
  { value: 'string', label: '字符串' },
  { value: 'number', label: '数字' },
  { value: 'boolean', label: '布尔值' },
  { value: 'json', label: 'JSON对象' },
  { value: 'url', label: 'URL地址' },
  { value: 'email', label: '邮箱地址' },
  { value: 'path', label: '文件路径' },
];

// 常用设置键建议
const COMMON_SETTING_KEYS = [
  'default_custom_query_sql',
  'app.name',
  'app.version',
  'app.debug',
  'database.timeout',
  'database.pool_size',
  'log.level',
  'log.format',
  'server.host',
  'server.port',
  'cache.enabled',
  'cache.ttl',
  'email.smtp_host',
  'email.smtp_port',
  'email.from_address',
  'security.session_timeout',
  'security.max_login_attempts',
  'ui.theme',
  'ui.language',
  'backup.enabled',
  'backup.schedule',
];

const SystemSettingsManagement: React.FC = () => {
  const [form] = Form.useForm<SystemSettingFormData>();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingSetting, setEditingSetting] = useState<SystemSetting | null>(null);
  const [searchText, setSearchText] = useState('');
  const [settingType, setSettingType] = useState<string>('string');
  
  const queryClient = useQueryClient();

  // 获取系统设置列表
  const { data: settings, isLoading, error } = useQuery<SystemSetting[]>({
    queryKey: ['system-settings'],
    queryFn: async () => {
      try {
        const response = await settingsApi.getAllSystemSettings();
        const data = response.data;
        
        // 确保返回的是数组
        if (Array.isArray(data)) {
          return data;
        } else if (data && typeof data === 'object') {
          // 如果返回的是对象，尝试转换为数组格式
          return Object.entries(data).map(([key, value]: [string, any]) => ({
            id: Date.now() + Math.random(), // 临时ID
            key,
            value: typeof value === 'object' ? JSON.stringify(value) : String(value),
            description: '',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }));
        } else {
          return [];
        }
      } catch (error) {
        console.error('Failed to fetch system settings:', error);
        return [];
      }
    },
    staleTime: 2 * 60 * 1000, // 2分钟缓存
  });

  // 创建/更新系统设置
  const saveSettingMutation = useMutation({
    mutationFn: async (settingData: SystemSettingFormData) => {
      // 发送 { key: string, value: string, description?: string }
      try {
        const response = await settingsApi.setSystemSetting(
          settingData.key, 
          settingData.value, 
          settingData.description
        );
        return response;
      } catch (error) {
        console.error('Save setting error:', error);
        throw error;
      }
    },
    retry: false,
    onSuccess: () => {
      message.success(editingSetting ? '设置更新成功' : '设置创建成功');
      setIsModalVisible(false);
      form.resetFields();
      setEditingSetting(null);
      setSettingType('string');
      queryClient.invalidateQueries({ queryKey: ['system-settings'] });
    },
    onError: (error: any) => {
      console.error('Setting save mutation error:', error);
      
      // 显示详细的错误信息
      if (error.response?.data?.errors && error.response.data.errors.length > 0) {
        message.error(error.response.data.errors[0]);
      } else if (error.response?.data?.message) {
        message.error(error.response.data.message);
      } else if (error.message) {
        message.error(error.message);
      } else {
        message.error('操作失败');
      }
    }
  });

  // 删除系统设置
  const deleteSettingMutation = useMutation({
    mutationFn: async (settingKey: string) => {
      return settingsApi.deleteSystemSetting(settingKey);
    },
    retry: false,
    onSuccess: () => {
      message.success('设置删除成功');
      queryClient.invalidateQueries({ queryKey: ['system-settings'] });
    },
    onError: (error: any) => {
      message.error(error.message || '删除失败');
    }
  });

  // 处理表单提交
  const handleSubmit = async (values: SystemSettingFormData) => {
    // 根据设置类型格式化值
    let formattedValue = values.value;
    
    switch (settingType) {
      case 'boolean':
        formattedValue = values.value === 'true' || values.value === '1' ? 'true' : 'false';
        break;
      case 'number':
        formattedValue = parseFloat(values.value).toString();
        break;
      case 'json':
        try {
          JSON.parse(values.value);
        } catch (e) {
          message.error('JSON格式不正确');
          return;
        }
        break;
    }
    
    saveSettingMutation.mutate({
      ...values,
      value: formattedValue
    });
  };

  // 显示编辑对话框
  const showEditModal = (setting?: SystemSetting) => {
    if (setting) {
      setEditingSetting(setting);
      form.setFieldsValue({
        key: setting.key,
        value: setting.value,
        description: setting.description
      });
      
      // 推断设置类型
      if (setting.value === 'true' || setting.value === 'false') {
        setSettingType('boolean');
      } else if (!isNaN(Number(setting.value))) {
        setSettingType('number');
      } else if (setting.value.startsWith('{') || setting.value.startsWith('[')) {
        setSettingType('json');
      } else {
        setSettingType('string');
      }
    } else {
      setEditingSetting(null);
      form.resetFields();
      setSettingType('string');
    }
    setIsModalVisible(true);
  };

  // 处理预设设置键的点击
  const handlePresetKeyClick = (key: string) => {
    form.setFieldsValue({ key });
    
    // 为特定键设置预设值和描述
    if (key === 'default_custom_query_sql') {
      form.setFieldsValue({
        key,
        value: 'SELECT * FROM OneToolsDb.dbo.Users;',
        description: 'Custom Query页面的默认SQL查询语句，用户可以修改此语句作为页面初始显示的SQL'
      });
    }
  };

  // 格式化设置值显示
  const formatSettingValue = (value: string, key: string) => {
    if (!value) return '-';
    
    // 根据键名推断类型
    if (value === 'true' || value === 'false') {
      return <Tag color={value === 'true' ? 'green' : 'red'}>{value}</Tag>;
    }
    
    if (key.includes('password') || key.includes('secret') || key.includes('token')) {
      return <Text type="secondary">••••••••</Text>;
    }
    
    if (value.length > 50) {
      return (
        <Tooltip title={value}>
          <Text>{value.substring(0, 50)}...</Text>
        </Tooltip>
      );
    }
    
    return <Text>{value}</Text>;
  };

  // 过滤设置
  const filteredSettings = React.useMemo(() => {
    if (!settings || !Array.isArray(settings)) {
      return [];
    }
    
    if (!searchText) {
      return settings;
    }
    
    return settings.filter(setting => 
      setting.key.toLowerCase().includes(searchText.toLowerCase()) ||
      (setting.description && setting.description.toLowerCase().includes(searchText.toLowerCase()))
    );
  }, [settings, searchText]);

  // 表格列定义
  const columns = [
    {
      title: '设置键',
      dataIndex: 'key',
      key: 'key',
      width: 250,
      render: (text: string) => (
        <Space>
          <KeyOutlined />
          <Text code strong>{text}</Text>
        </Space>
      )
    },
    {
      title: '设置值',
      dataIndex: 'value',
      key: 'value',
      width: 200,
      render: (value: string, record: SystemSetting) => formatSettingValue(value, record.key)
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      render: (description: string) => (
        <Space>
          <FileTextOutlined />
          <Text type="secondary">{description || '-'}</Text>
        </Space>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (created_at: string) => (
        <Text type="secondary">
          {created_at ? new Date(created_at).toLocaleString() : '-'}
        </Text>
      )
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 180,
      render: (updated_at: string) => (
        <Text type="secondary">
          {updated_at ? new Date(updated_at).toLocaleString() : '-'}
        </Text>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (record: SystemSetting) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => showEditModal(record)}
          >
            编辑
          </Button>

          <Popconfirm
            title="确定要删除这个设置吗?"
            description="删除后无法恢复"
            onConfirm={() => deleteSettingMutation.mutate(record.key)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              icon={<DeleteOutlined />}
              danger
              loading={deleteSettingMutation.isPending}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  // 渲染值输入组件
  const renderValueInput = () => {
    switch (settingType) {
      case 'boolean':
        return (
          <Select
            placeholder="选择布尔值"
            options={[
              { value: 'true', label: 'true' },
              { value: 'false', label: 'false' }
            ]}
          />
        );
      case 'number':
        return <InputNumber style={{ width: '100%' }} placeholder="输入数字" />;
      case 'json':
        return (
          <TextArea
            rows={4}
            placeholder="输入JSON对象，例如: {&quot;key&quot;: &quot;value&quot;}"
          />
        );
      default:
        return <Input placeholder="输入设置值" />;
    }
  };

  return (
    <div>
      <Card>
        <div style={{ marginBottom: 16 }}>
          <Row gutter={16} align="middle">
            <Col flex="auto">
              <Title level={4}>
                <Space>
                  <SettingOutlined />
                  系统设置管理
                </Space>
              </Title>
              <Text type="secondary">
                管理系统运行时的各项配置参数，支持键值对形式的设置存储
              </Text>
            </Col>
            <Col>
              <Space>
                <Input.Search
                  placeholder="搜索设置键或描述"
                  allowClear
                  style={{ width: 250 }}
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  prefix={<SearchOutlined />}
                />
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() => queryClient.invalidateQueries({ queryKey: ['system-settings'] })}
                  loading={isLoading}
                >
                  刷新
                </Button>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => showEditModal()}
                >
                  添加设置
                </Button>
              </Space>
            </Col>
          </Row>
        </div>

        <Alert
          message="系统设置说明"
          description="系统设置采用键值对存储方式，支持字符串、数字、布尔值、JSON等多种数据类型。修改设置后可能需要重启应用生效。"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        {error && (
          <Alert
            message="加载失败"
            description="无法加载系统设置数据，请检查网络连接或稍后重试。"
            type="error"
            showIcon
            closable
            style={{ marginBottom: 16 }}
          />
        )}

        <Table
          columns={columns}
          dataSource={filteredSettings || []}
          loading={isLoading}
          rowKey="key"
          size="small"
          pagination={{
            total: (filteredSettings || []).length,
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `显示 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
        />
      </Card>

      <Modal
        title={
          <Space>
            <SettingOutlined />
            {editingSetting ? '编辑系统设置' : '添加系统设置'}
          </Space>
        }
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
          setEditingSetting(null);
          setSettingType('string');
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="key"
            label="设置键"
            rules={[
              { required: true, message: '请输入设置键' },
              { max: 100, message: '设置键不能超过100个字符' },
              { pattern: /^[a-zA-Z0-9._-]+$/, message: '设置键只能包含字母、数字、点、下划线和连字符' }
            ]}
          >
            <Input
              placeholder="例如: app.name, database.timeout"
              disabled={!!editingSetting}
              suffix={
                <Tooltip title="设置键应该使用点分隔的层次结构，例如 app.name 或 database.timeout">
                  <InfoCircleOutlined />
                </Tooltip>
              }
            />
          </Form.Item>

          <Form.Item label="数据类型">
            <Select
              value={settingType}
              onChange={setSettingType}
              options={SETTING_TYPES}
              disabled={!!editingSetting}
            />
          </Form.Item>

          <Form.Item
            name="value"
            label="设置值"
            rules={[
              { required: true, message: '请输入设置值' }
            ]}
          >
            {renderValueInput()}
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
            rules={[
              { max: 500, message: '描述不能超过500个字符' }
            ]}
          >
            <TextArea
              rows={3}
              placeholder="输入设置的详细描述，说明其作用和影响"
            />
          </Form.Item>

          {!editingSetting && (
            <Alert
              message="常用设置键建议"
              description={
                <div>
                  <Text type="secondary">您可以参考以下常用设置键：</Text>
                  <div style={{ marginTop: 8 }}>
                    {COMMON_SETTING_KEYS.slice(0, 10).map(key => (
                      <Tag
                        key={key}
                        style={{ cursor: 'pointer', marginBottom: 4 }}
                        onClick={() => handlePresetKeyClick(key)}
                        color={key === 'default_custom_query_sql' ? 'blue' : 'default'}
                      >
                        {key}
                      </Tag>
                    ))}
                  </div>
                </div>
              }
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          <Divider />

          <Form.Item style={{ marginBottom: 0 }}>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={saveSettingMutation.isPending}
              >
                {editingSetting ? '更新设置' : '创建设置'}
              </Button>
              <Button
                onClick={() => {
                  setIsModalVisible(false);
                  form.resetFields();
                  setEditingSetting(null);
                  setSettingType('string');
                }}
              >
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SystemSettingsManagement;