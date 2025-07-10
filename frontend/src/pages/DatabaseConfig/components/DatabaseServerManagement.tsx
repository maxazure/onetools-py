/**
 * 数据库服务器管理组件
 */

import React, { useState } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Switch,
  Space,
  message,
  Popconfirm,
  Typography,
  Tag,
  Tooltip,
  Card,
  Divider
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  DatabaseOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { databaseApi, settingsApi } from '../../../services/api';

const { Text } = Typography;

interface DatabaseServer {
  id?: number;
  name: string;
  order: number;
  created_at?: string;
  updated_at?: string;
}

interface DatabaseServerFormData {
  name: string;
}

const DatabaseServerManagement: React.FC = () => {
  const [form] = Form.useForm<DatabaseServerFormData>();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingServer, setEditingServer] = useState<DatabaseServer | null>(null);
  const [testingConnection, setTestingConnection] = useState<string | null>(null);
  
  const queryClient = useQueryClient();

  // 获取数据库服务器列表
  const { data: servers, isLoading, error } = useQuery<DatabaseServer[]>({
    queryKey: ['database-servers'],
    queryFn: async () => {
      try {
        const response = await settingsApi.getDatabaseServers();
        return response.data || [];
      } catch (error) {
        console.error('Failed to fetch database servers:', error);
        return [];
      }
    },
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });

  // 创建/更新数据库服务器
  const saveServerMutation = useMutation({
    mutationFn: async (serverData: DatabaseServerFormData) => {
      if (editingServer) {
        // 更新服务器
        return settingsApi.updateDatabaseServer(editingServer.id!, serverData);
      } else {
        // 创建服务器
        return settingsApi.createDatabaseServer(serverData);
      }
    },
    retry: false, // 禁用重试以防止重复创建/更新服务器配置
    onSuccess: () => {
      message.success(editingServer ? '服务器更新成功' : '服务器创建成功');
      setIsModalVisible(false);
      form.resetFields();
      setEditingServer(null);
      queryClient.invalidateQueries({ queryKey: ['database-servers'] });
      // 同时刷新服务器下拉框缓存
      queryClient.invalidateQueries({ queryKey: ['server-dropdown'] });
    },
    onError: (error: any) => {
      message.error(error.message || '操作失败');
    }
  });

  // 删除数据库服务器
  const deleteServerMutation = useMutation({
    mutationFn: async (serverId: number) => {
      return settingsApi.deleteDatabaseServer(serverId);
    },
    retry: false, // 禁用重试以防止重复删除
    onSuccess: () => {
      message.success('服务器删除成功');
      queryClient.invalidateQueries({ queryKey: ['database-servers'] });
      // 同时刷新服务器下拉框缓存
      queryClient.invalidateQueries({ queryKey: ['server-dropdown'] });
    },
    onError: (error: any) => {
      message.error(error.message || '删除失败');
    }
  });


  // 测试连接
  const testConnection = async (server: DatabaseServer) => {
    setTestingConnection(server.name);
    try {
      await databaseApi.testConnection({ server: server.name });
      message.success(`连接 ${server.name} 成功`);
    } catch (error) {
      message.error(`连接 ${server.name} 失败`);
    } finally {
      setTestingConnection(null);
    }
  };

  // 处理表单提交
  const handleSubmit = async (values: DatabaseServerFormData) => {
    saveServerMutation.mutate(values);
  };

  // 显示编辑对话框
  const showEditModal = (server?: DatabaseServer) => {
    if (server) {
      setEditingServer(server);
      form.setFieldsValue({
        name: server.name
      });
    } else {
      setEditingServer(null);
      form.resetFields();
    }
    setIsModalVisible(true);
  };

  // 表格列定义
  const columns = [
    {
      title: '服务器名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: DatabaseServer) => (
        <Space>
          <DatabaseOutlined />
          <Text strong>{text}</Text>
        </Space>
      )
    },
    {
      title: '类型',
      key: 'type',
      render: () => (
        <Tag color="green">
          SQL Server
        </Tag>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (created_at: string) => (
        <Text type="secondary">
          {created_at ? new Date(created_at).toLocaleString() : '-'}
        </Text>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: DatabaseServer) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => showEditModal(record)}
          >
            编辑
          </Button>
          
          <Button
            type="link"
            size="small"
            loading={testingConnection === record.name}
            onClick={() => testConnection(record)}
          >
            测试连接
          </Button>

          <Popconfirm
            title="确定要删除这个数据库服务器吗?"
            onConfirm={() => record.id && deleteServerMutation.mutate(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              icon={<DeleteOutlined />}
              danger
              loading={deleteServerMutation.isPending}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <div>
          <Text type="secondary">管理数据库服务器连接配置</Text>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => showEditModal()}
        >
          添加服务器
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={servers || []}
        loading={isLoading}
        rowKey="name"
        size="small"
      />

      <Modal
        title={editingServer ? '编辑数据库服务器' : '添加数据库服务器'}
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
          setEditingServer(null);
        }}
        footer={null}
        width={480}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label="服务器名称"
            rules={[
              { required: true, message: '请输入服务器名称' },
              { max: 100, message: '服务器名称不能超过100个字符' }
            ]}
          >
            <Input placeholder="例如: localhost\SQLEXPRESS" />
          </Form.Item>

          <div style={{ marginBottom: 16 }}>
            <Text type="secondary">
              <DatabaseOutlined style={{ marginRight: 8 }} />
              数据库类型将自动设置为 SQL Server，连接字符串将根据服务器名称自动生成
            </Text>
          </div>

          <Divider />

          <Form.Item style={{ marginBottom: 0 }}>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={saveServerMutation.isPending}
              >
                {editingServer ? '更新' : '创建'}
              </Button>
              <Button
                onClick={() => {
                  setIsModalVisible(false);
                  form.resetFields();
                  setEditingServer(null);
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

export default DatabaseServerManagement;