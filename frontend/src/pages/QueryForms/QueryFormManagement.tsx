/**
 * 查询表单配置管理页面
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Input,
  Select,
  Modal,
  message,
  Popconfirm,
  Tag,
  Tooltip,
  Row,
  Col,
  Statistic,
  Badge,
  Drawer,
  Form,
  Switch,
  Typography,
  Alert,
  Divider,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CopyOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  EyeOutlined,
  HistoryOutlined,
  DownloadOutlined,
  UploadOutlined,
  ReloadOutlined,
  SearchOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import type { ColumnsType, TableProps } from 'antd/es/table';
import { useNavigate } from 'react-router-dom';

import {
  QueryFormResponse,
  FormManagementState,
  QueryFormCreateRequest,
  QueryFormExecuteRequest,
  FormAction,
  FormActionResult,
} from '../../types/query-forms';
import { queryFormApi } from '../../services/query-forms/query-form-api';
import QueryFormBuilder from '../../components/QueryFormBuilder';
import DynamicForm from '../../components/DynamicForm';

const { Search } = Input;
const { Option } = Select;
const { Text, Title } = Typography;

const QueryFormManagement: React.FC = () => {
  const navigate = useNavigate();
  const [state, setState] = useState<FormManagementState>({
    forms: [],
    isLoading: false,
    searchTerm: '',
    activeOnly: true,
    selectedForms: [],
  });

  const [builderVisible, setBuilderVisible] = useState(false);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [duplicateVisible, setDuplicateVisible] = useState(false);
  const [currentForm, setCurrentForm] = useState<QueryFormResponse | undefined>();
  const [editMode, setEditMode] = useState<'create' | 'edit'>('create');
  const [newFormName, setNewFormName] = useState('');
  const [statistics, setStatistics] = useState({
    total: 0,
    active: 0,
    inactive: 0,
    recentExecutions: 0,
  });

  // 加载表单列表
  const loadForms = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));
      const result = await queryFormApi.getAllForms(state.activeOnly);
      
      if (result.success && result.data) {
        setState(prev => ({ ...prev, forms: result.data! }));
        
        // 更新统计信息
        const total = result.data.length;
        const active = result.data.filter(f => f.is_active).length;
        const inactive = total - active;
        
        setStatistics({
          total,
          active,
          inactive,
          recentExecutions: 0, // 这里需要额外的API获取
        });
      }
    } catch (error) {
      message.error('加载表单列表失败');
      console.error('Load forms failed:', error);
    } finally {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, [state.activeOnly]);

  // 初始化加载
  useEffect(() => {
    loadForms();
  }, [loadForms]);

  // 搜索处理
  const handleSearch = (value: string) => {
    setState(prev => ({ ...prev, searchTerm: value }));
  };

  // 过滤表单数据
  const filteredForms = state.forms.filter(form => {
    if (!state.searchTerm) return true;
    const searchLower = state.searchTerm.toLowerCase();
    return (
      form.form_name.toLowerCase().includes(searchLower) ||
      (form.form_description && form.form_description.toLowerCase().includes(searchLower))
    );
  });

  // 表单操作
  const handleFormAction = async (action: FormAction, form?: QueryFormResponse, data?: any) => {
    try {
      let result: any;
      
      switch (action) {
        case FormAction.CREATE:
          setEditMode('create');
          setCurrentForm(undefined);
          setBuilderVisible(true);
          break;
          
        case FormAction.UPDATE:
          if (!form) return;
          setEditMode('edit');
          setCurrentForm(form);
          setBuilderVisible(true);
          break;
          
        case FormAction.DELETE:
          if (!form) return;
          result = await queryFormApi.deleteForm(form.id, true);
          if (result.success) {
            message.success('删除成功');
            loadForms();
          }
          break;
          
        case FormAction.DUPLICATE:
          if (!form) return;
          result = await queryFormApi.duplicateForm(form.id, newFormName);
          if (result.success) {
            message.success('复制成功');
            setDuplicateVisible(false);
            setNewFormName('');
            loadForms();
          }
          break;
          
        case FormAction.TOGGLE_STATUS:
          if (!form) return;
          result = await queryFormApi.toggleFormStatus(form.id);
          if (result.success) {
            const status = result.data?.is_active ? '激活' : '禁用';
            message.success(`${status}成功`);
            loadForms();
          }
          break;
          
        case FormAction.PREVIEW:
          if (!form) return;
          setCurrentForm(form);
          setPreviewVisible(true);
          break;
          
        case FormAction.EXECUTE:
          if (!form) return;
          navigate(`/query-forms/${form.id}/execute`);
          break;
          
        default:
          message.info(`功能 ${action} 待实现`);
      }
    } catch (error) {
      message.error(`操作失败: ${error}`);
      console.error('Form action failed:', error);
    }
  };

  // 批量操作
  const handleBatchOperation = async (operation: 'delete' | 'activate' | 'deactivate') => {
    if (state.selectedForms.length === 0) {
      message.warning('请先选择要操作的表单');
      return;
    }

    try {
      const result = await queryFormApi.batchOperation(state.selectedForms, operation);
      if (result.success && result.data) {
        const { success_count, failed_count } = result.data;
        message.success(`批量操作完成: 成功${success_count}个，失败${failed_count}个`);
        setState(prev => ({ ...prev, selectedForms: [] }));
        loadForms();
      }
    } catch (error) {
      message.error('批量操作失败');
      console.error('Batch operation failed:', error);
    }
  };

  // 表格列配置
  const columns: ColumnsType<QueryFormResponse> = [
    {
      title: '表单名称',
      dataIndex: 'form_name',
      key: 'form_name',
      width: 200,
      fixed: 'left',
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          {record.form_description && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {record.form_description}
            </Text>
          )}
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active: boolean) => (
        <Badge
          status={active ? 'success' : 'default'}
          text={active ? '激活' : '禁用'}
        />
      ),
      filters: [
        { text: '激活', value: true },
        { text: '禁用', value: false },
      ],
      onFilter: (value, record) => record.is_active === value,
    },
    {
      title: '字段数量',
      key: 'field_count',
      width: 80,
      render: (_, record) => (
        <Text>{record.form_config.fields.length}</Text>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (text) => new Date(text).toLocaleString(),
      sorter: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: '最后更新',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 160,
      render: (text) => new Date(text).toLocaleString(),
      sorter: (a, b) => new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime(),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="执行查询">
            <Button
              type="primary"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => handleFormAction(FormAction.EXECUTE, record)}
            />
          </Tooltip>
          
          <Tooltip title="预览">
            <Button
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleFormAction(FormAction.PREVIEW, record)}
            />
          </Tooltip>
          
          <Tooltip title="编辑">
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleFormAction(FormAction.UPDATE, record)}
            />
          </Tooltip>
          
          <Tooltip title="复制">
            <Button
              size="small"
              icon={<CopyOutlined />}
              onClick={() => {
                setCurrentForm(record);
                setNewFormName(`${record.form_name}_副本`);
                setDuplicateVisible(true);
              }}
            />
          </Tooltip>
          
          <Tooltip title={record.is_active ? '禁用' : '激活'}>
            <Button
              size="small"
              icon={record.is_active ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              onClick={() => handleFormAction(FormAction.TOGGLE_STATUS, record)}
            />
          </Tooltip>
          
          <Popconfirm
            title="确定要删除这个表单吗？"
            onConfirm={() => handleFormAction(FormAction.DELETE, record)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 行选择配置
  const rowSelection: TableProps<QueryFormResponse>['rowSelection'] = {
    selectedRowKeys: state.selectedForms,
    onChange: (selectedRowKeys) => {
      setState(prev => ({ ...prev, selectedForms: selectedRowKeys as number[] }));
    },
  };

  return (
    <div className="query-form-management">
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic title="总表单数" value={statistics.total} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="激活表单"
              value={statistics.active}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="禁用表单"
              value={statistics.inactive}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="近期执行" value={statistics.recentExecutions} />
          </Card>
        </Col>
      </Row>

      {/* 主要内容 */}
      <Card
        title="查询表单管理"
        extra={
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => handleFormAction(FormAction.CREATE)}
            >
              创建表单
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadForms}
            >
              刷新
            </Button>
          </Space>
        }
      >
        {/* 搜索和过滤 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={8}>
            <Search
              placeholder="搜索表单名称或描述"
              allowClear
              onSearch={handleSearch}
              enterButton={<SearchOutlined />}
            />
          </Col>
          <Col span={4}>
            <Select
              style={{ width: '100%' }}
              value={state.activeOnly}
              onChange={(value) => setState(prev => ({ ...prev, activeOnly: value }))}
            >
              <Option value={true}>仅显示激活</Option>
              <Option value={false}>显示全部</Option>
            </Select>
          </Col>
          <Col span={12}>
            {state.selectedForms.length > 0 && (
              <Space>
                <Text>已选择 {state.selectedForms.length} 项</Text>
                <Button
                  size="small"
                  onClick={() => handleBatchOperation('activate')}
                >
                  批量激活
                </Button>
                <Button
                  size="small"
                  onClick={() => handleBatchOperation('deactivate')}
                >
                  批量禁用
                </Button>
                <Popconfirm
                  title="确定要批量删除选中的表单吗？"
                  onConfirm={() => handleBatchOperation('delete')}
                  okText="确定"
                  cancelText="取消"
                >
                  <Button size="small" danger>
                    批量删除
                  </Button>
                </Popconfirm>
              </Space>
            )}
          </Col>
        </Row>

        {/* 表格 */}
        <Table
          columns={columns}
          dataSource={filteredForms}
          rowKey="id"
          rowSelection={rowSelection}
          loading={state.isLoading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `第 ${range[0]}-${range[1]} 条，共 ${total} 条记录`,
          }}
          scroll={{ x: 1200 }}
          size="middle"
        />
      </Card>

      {/* 表单构建器抽屉 */}
      <Drawer
        title={editMode === 'create' ? '创建查询表单' : '编辑查询表单'}
        placement="right"
        size="large"
        open={builderVisible}
        onClose={() => setBuilderVisible(false)}
        destroyOnClose
        style={{ top: 64 }}
      >
        <QueryFormBuilder
          mode={editMode}
          initialForm={currentForm}
          onSave={(form) => {
            setBuilderVisible(false);
            message.success(`${editMode === 'create' ? '创建' : '更新'}成功`);
            loadForms();
          }}
          onCancel={() => setBuilderVisible(false)}
        />
      </Drawer>

      {/* 预览模态框 */}
      <Modal
        title={`预览表单: ${currentForm?.form_name}`}
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={null}
        width={1000}
        destroyOnClose
      >
        {currentForm && (
          <DynamicForm
            form={currentForm}
            showResult={false}
            onExecute={(result) => {
              message.success(`预览查询成功，返回${result.total}条记录`);
            }}
            onError={(error) => {
              message.error(`预览查询失败: ${error}`);
            }}
          />
        )}
      </Modal>

      {/* 复制表单模态框 */}
      <Modal
        title="复制表单"
        open={duplicateVisible}
        onOk={() => handleFormAction(FormAction.DUPLICATE, currentForm)}
        onCancel={() => {
          setDuplicateVisible(false);
          setNewFormName('');
        }}
        okText="确定"
        cancelText="取消"
      >
        <Form layout="vertical">
          <Form.Item
            label="新表单名称"
            required
            help="复制后的表单将使用此名称"
          >
            <Input
              value={newFormName}
              onChange={(e) => setNewFormName(e.target.value)}
              placeholder="请输入新表单名称"
            />
          </Form.Item>
          {currentForm && (
            <Alert
              message={`将复制表单: ${currentForm.form_name}`}
              type="info"
              showIcon
            />
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default QueryFormManagement;