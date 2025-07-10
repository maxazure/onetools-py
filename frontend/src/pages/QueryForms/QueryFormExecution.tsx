/**
 * 查询表单执行页面
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Spin,
  Alert,
  message,
  Button,
  Space,
  Divider,
  Typography,
  Tag,
  Tooltip,
  Modal,
  Table,
} from 'antd';
import {
  ArrowLeftOutlined,
  HistoryOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import type { ColumnsType } from 'antd/es/table';

import {
  QueryFormResponse,
  QueryFormHistory,
  QueryResponse,
  FormExecutionState,
} from '../../types/query-forms';
import { queryFormApi } from '../../services/query-forms/query-form-api';
import DynamicForm from '../../components/DynamicForm';

const { Title, Text } = Typography;

const QueryFormExecution: React.FC = () => {
  const { formId } = useParams<{ formId: string }>();
  const navigate = useNavigate();
  
  const [form, setForm] = useState<QueryFormResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [historyVisible, setHistoryVisible] = useState(false);
  const [state, setState] = useState<FormExecutionState>({
    isExecuting: false,
    history: [],
    isLoadingHistory: false,
  });


  // 加载表单配置
  useEffect(() => {
    if (!formId) {
      message.error('表单ID无效');
      navigate('/query-forms');
      return;
    }

    loadForm();
  }, [formId]);

  const loadForm = async () => {
    try {
      setLoading(true);
      const result = await queryFormApi.getFormById(parseInt(formId!));
      
      if (result.success && result.data) {
        setForm(result.data);
      } else {
        message.error('表单不存在或已删除');
        navigate('/query-forms');
      }
    } catch (error) {
      message.error('加载表单失败');
      console.error('Load form failed:', error);
      navigate('/query-forms');
    } finally {
      setLoading(false);
    }
  };

  // 加载执行历史
  const loadHistory = async () => {
    try {
      setState(prev => ({ ...prev, isLoadingHistory: true }));
      const result = await queryFormApi.getFormHistory(parseInt(formId!), 50);
      
      if (result.success && result.data) {
        setState(prev => ({ ...prev, history: result.data! }));
      }
    } catch (error) {
      message.error('加载执行历史失败');
      console.error('Load history failed:', error);
    } finally {
      setState(prev => ({ ...prev, isLoadingHistory: false }));
    }
  };

  // 处理查询执行
  const handleExecute = (result: QueryResponse) => {
    setState(prev => ({
      ...prev,
      result,
      isExecuting: false,
    }));
    
    // 重新加载历史记录
    if (historyVisible) {
      loadHistory();
    }
  };

  // 处理执行错误
  const handleError = (error: string) => {
    setState(prev => ({
      ...prev,
      error,
      isExecuting: false,
    }));
  };

  // 历史记录表格列
  const historyColumns: ColumnsType<QueryFormHistory> = [
    {
      title: '执行时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (text) => new Date(text).toLocaleString(),
      sorter: (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    },
    {
      title: '状态',
      dataIndex: 'success',
      key: 'success',
      width: 80,
      render: (success: boolean) => (
        <Tag color={success ? 'success' : 'error'}>
          {success ? '成功' : '失败'}
        </Tag>
      ),
    },
    {
      title: '执行时间(秒)',
      dataIndex: 'execution_time',
      key: 'execution_time',
      width: 120,
      render: (time?: number) => time ? time.toFixed(3) : '-',
    },
    {
      title: '返回行数',
      dataIndex: 'row_count',
      key: 'row_count',
      width: 100,
      render: (count?: number) => count?.toLocaleString() || '-',
    },
    {
      title: '查询参数',
      dataIndex: 'query_params',
      key: 'query_params',
      render: (params: Record<string, any>) => (
        <Tooltip title={JSON.stringify(params, null, 2)}>
          <Text ellipsis style={{ maxWidth: 200 }}>
            {Object.keys(params).length > 0 
              ? Object.keys(params).join(', ')
              : '无参数'
            }
          </Text>
        </Tooltip>
      ),
    },
    {
      title: '错误信息',
      dataIndex: 'error_message',
      key: 'error_message',
      render: (error?: string) => (
        error ? (
          <Tooltip title={error}>
            <Text type="danger" ellipsis style={{ maxWidth: 200 }}>
              {error}
            </Text>
          </Tooltip>
        ) : '-'
      ),
    },
    {
      title: '用户',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 100,
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>加载表单配置中...</Text>
        </div>
      </div>
    );
  }

  if (!form) {
    return (
      <Alert
        message="表单不存在"
        description="请检查表单ID是否正确，或者返回表单列表重新选择。"
        type="error"
        showIcon
        action={
          <Button type="primary" onClick={() => navigate('/query-forms')}>
            返回列表
          </Button>
        }
      />
    );
  }

  return (
    <div className="query-form-execution">
      {/* 页面头部 */}
      <Card style={{ marginBottom: 16 }}>
        <Row align="middle" justify="space-between">
          <Col>
            <Space>
              <Button
                type="text"
                icon={<ArrowLeftOutlined />}
                onClick={() => navigate('/query-forms')}
              >
                返回列表
              </Button>
              <Divider type="vertical" />
              <Title level={4} style={{ margin: 0 }}>
                {form.form_name}
              </Title>
              <Tag color={form.is_active ? 'success' : 'error'}>
                {form.is_active ? '激活' : '禁用'}
              </Tag>
            </Space>
          </Col>
          
          <Col>
            <Space>
              <Button
                icon={<HistoryOutlined />}
                onClick={() => {
                  setHistoryVisible(true);
                  loadHistory();
                }}
              >
                执行历史
              </Button>
              
              <Button
                icon={<ReloadOutlined />}
                onClick={loadForm}
              >
                刷新
              </Button>
            </Space>
          </Col>
        </Row>

        {form.form_description && (
          <div style={{ marginTop: 8 }}>
            <Text type="secondary">{form.form_description}</Text>
          </div>
        )}

        {form.target_database && (
          <div style={{ marginTop: 8 }}>
            <Space>
              <Text type="secondary">目标数据库:</Text>
              <Tag>{form.target_database}</Tag>
            </Space>
          </div>
        )}
      </Card>

      {/* 表单执行区域 */}
      {!form.is_active && (
        <Alert
          message="表单已禁用"
          description="此表单当前处于禁用状态，无法执行查询。请联系管理员启用。"
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <DynamicForm
        form={form}
        serverName=""
        onExecute={handleExecute}
        onError={handleError}
        showResult={true}
        autoSubmit={false}
      />

      {/* 执行历史模态框 */}
      <Modal
        title={`执行历史 - ${form.form_name}`}
        open={historyVisible}
        onCancel={() => setHistoryVisible(false)}
        footer={[
          <Button key="refresh" onClick={loadHistory} loading={state.isLoadingHistory}>
            刷新
          </Button>,
          <Button key="close" onClick={() => setHistoryVisible(false)}>
            关闭
          </Button>,
        ]}
        width={1200}
        destroyOnClose
      >
        <Table
          columns={historyColumns}
          dataSource={state.history}
          rowKey="id"
          loading={state.isLoadingHistory}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `第 ${range[0]}-${range[1]} 条，共 ${total} 条记录`,
          }}
          size="small"
          scroll={{ x: 800 }}
        />
      </Modal>
    </div>
  );
};

export default QueryFormExecution;