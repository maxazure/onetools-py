/**
 * 菜单配置页面 - 系统菜单配置管理
 */

import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Space,
  message,
  Popconfirm,
  Typography,
  Tag,
  InputNumber,
  Card,
  Divider,
  Alert
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  MenuOutlined,
  UpOutlined,
  DownOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import * as Icons from '@ant-design/icons';
import { apiService } from '../../services/api';
import { MenuConfiguration, MenuFormData } from '../../types/api';
import { useMenuConfig } from '../../hooks/useMenuConfig';

const { Title, Text } = Typography;
const { Option } = Select;

const MenuConfig: React.FC = () => {
  const [form] = Form.useForm<MenuFormData>();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingMenu, setEditingMenu] = useState<MenuConfiguration | null>(null);
  const [loading, setLoading] = useState(false);

  // 使用自定义 hook 管理菜单配置
  const { refreshMenuConfig } = useMenuConfig();
  const [allMenuItems, setAllMenuItems] = useState<MenuConfiguration[]>([]);

  // 加载所有菜单项（包括禁用的）
  const loadAllMenuItems = async () => {
    setLoading(true);
    try {
      const response = await apiService.getMenuConfiguration();
      if (response.success && response.data) {
        setAllMenuItems(response.data);
      }
    } catch (error) {
      console.error('加载菜单配置失败:', error);
      message.error('加载菜单配置失败');
    } finally {
      setLoading(false);
    }
  };

  // 组件加载时获取所有菜单配置
  useEffect(() => {
    loadAllMenuItems();
  }, []);

  // 可用的图标列表
  const availableIcons = [
    'UserOutlined', 'CodeOutlined', 'HistoryOutlined', 'DatabaseOutlined',
    'SettingOutlined', 'DashboardOutlined', 'FileTextOutlined', 'BarChartOutlined',
    'PieChartOutlined', 'TableOutlined', 'SearchOutlined', 'AppstoreOutlined',
    'MenuOutlined', 'HomeOutlined', 'InfoCircleOutlined', 'BellOutlined',
    'MailOutlined', 'PhoneOutlined', 'CalendarOutlined', 'ClockCircleOutlined',
    'FolderOutlined', 'FileOutlined', 'PictureOutlined', 'VideoCameraOutlined',
    'AudioOutlined', 'TeamOutlined', 'ShopOutlined', 'ShoppingCartOutlined',
    'SaveOutlined', 'DeleteOutlined', 'EditOutlined', 'EyeOutlined',
    'EyeInvisibleOutlined', 'LockOutlined', 'UnlockOutlined', 'KeyOutlined',
    'UploadOutlined', 'DownloadOutlined', 'ExportOutlined', 'ImportOutlined',
    'PrinterOutlined', 'ScanOutlined', 'CopyOutlined', 'ScissorOutlined',
    'HighlightOutlined', 'FontSizeOutlined', 'BoldOutlined', 'ItalicOutlined'
  ];

  // 可用的组件列表
  const availableComponents = [
    'CustomQuery', 'QueryHistory', 'SavedQueries', 'QueryStats', 
    'DatabaseConfig', 'MenuConfig', 'Settings', 'About', 'Dashboard'
  ];

  // 获取图标组件
  const getIconComponent = (iconName: string) => {
    const IconComponent = (Icons as any)[iconName];
    return IconComponent ? <IconComponent /> : <MenuOutlined />;
  };

  // 处理表单提交
  const handleSubmit = async (values: MenuFormData) => {
    setLoading(true);
    try {
      if (editingMenu) {
        // 更新菜单项
        const response = await apiService.updateMenuItem(editingMenu.id!, values);
        if (response.success) {
          message.success('菜单项更新成功');
          await loadAllMenuItems();
          refreshMenuConfig(); // 刷新主布局菜单
        } else {
          message.error('菜单项更新失败');
        }
      } else {
        // 创建新菜单项
        const response = await apiService.createMenuItem(values);
        if (response.success) {
          message.success('菜单项创建成功');
          await loadAllMenuItems();
          refreshMenuConfig(); // 刷新主布局菜单
        } else {
          message.error('菜单项创建失败');
        }
      }
      
      setIsModalVisible(false);
      form.resetFields();
      setEditingMenu(null);
    } catch (error) {
      console.error('操作失败:', error);
      message.error('操作失败');
    } finally {
      setLoading(false);
    }
  };

  // 显示编辑对话框
  const showEditModal = (menu?: MenuConfiguration) => {
    if (menu) {
      setEditingMenu(menu);
      form.setFieldsValue(menu);
    } else {
      setEditingMenu(null);
      form.resetFields();
      form.setFieldsValue({
        enabled: true,
        position: 'top',
        section: 'main',
        order: allMenuItems.length + 1
      });
    }
    setIsModalVisible(true);
  };

  // 删除菜单项
  const handleDelete = async (id: number) => {
    setLoading(true);
    try {
      const response = await apiService.deleteMenuItem(id);
      if (response.success) {
        message.success('菜单项删除成功');
        await loadAllMenuItems();
        refreshMenuConfig(); // 刷新主布局菜单
      } else {
        message.error('菜单项删除失败');
      }
    } catch (error) {
      console.error('删除菜单项失败:', error);
      message.error('删除菜单项失败');
    } finally {
      setLoading(false);
    }
  };

  // 切换启用状态
  const toggleEnabled = async (id: number) => {
    const menuItem = allMenuItems.find(item => item.id === id);
    if (!menuItem) return;

    setLoading(true);
    try {
      const updatedItem = { ...menuItem, enabled: !menuItem.enabled };
      const response = await apiService.updateMenuItem(id, updatedItem);
      if (response.success) {
        await loadAllMenuItems();
        refreshMenuConfig(); // 刷新主布局菜单
        message.success(`菜单项已${updatedItem.enabled ? '启用' : '禁用'}`);
      } else {
        message.error('更新菜单状态失败');
      }
    } catch (error) {
      console.error('更新菜单状态失败:', error);
      message.error('更新菜单状态失败');
    } finally {
      setLoading(false);
    }
  };

  // 调整顺序
  const adjustOrder = async (id: number, direction: 'up' | 'down') => {
    const currentIndex = allMenuItems.findIndex(item => item.id === id);
    if (currentIndex === -1) return;

    const newItems = [...allMenuItems];
    const targetIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
    
    if (targetIndex >= 0 && targetIndex < newItems.length) {
      setLoading(true);
      try {
        // 交换位置
        [newItems[currentIndex], newItems[targetIndex]] = [newItems[targetIndex], newItems[currentIndex]];
        
        // 更新 order 字段并提交到后端
        const updatePromises = newItems.map(async (item, index) => {
          const updatedItem = { ...item, order: index + 1 };
          return apiService.updateMenuItem(item.id!, updatedItem);
        });

        await Promise.all(updatePromises);
        await loadAllMenuItems();
        refreshMenuConfig(); // 刷新主布局菜单
        message.success('菜单顺序调整成功');
      } catch (error) {
        console.error('调整菜单顺序失败:', error);
        message.error('调整菜单顺序失败');
      } finally {
        setLoading(false);
      }
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '菜单项',
      dataIndex: 'label',
      key: 'label',
      render: (text: string, record: MenuConfiguration) => (
        <Space>
          {getIconComponent(record.icon)}
          <Text strong>{text}</Text>
        </Space>
      )
    },
    {
      title: '路径',
      dataIndex: 'path',
      key: 'path',
      render: (text: string) => <Text code>{text}</Text>
    },
    {
      title: '组件',
      dataIndex: 'component',
      key: 'component',
      render: (text: string) => <Tag color="blue">{text}</Tag>
    },
    {
      title: '位置',
      dataIndex: 'position',
      key: 'position',
      render: (position: string) => (
        <Tag color={position === 'top' ? 'green' : 'orange'}>
          {position === 'top' ? '顶部' : '底部'}
        </Tag>
      )
    },
    {
      title: '分组',
      dataIndex: 'section',
      key: 'section',
      render: (section: string) => (
        <Tag color={section === 'main' ? 'blue' : 'purple'}>
          {section === 'main' ? '主要功能' : '系统管理'}
        </Tag>
      )
    },
    {
      title: '排序',
      dataIndex: 'order',
      key: 'order',
      render: (order: number) => <Text>{order}</Text>
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled: boolean, record: MenuConfiguration) => (
        <Switch
          checked={enabled}
          onChange={() => toggleEnabled(record.id!)}
          checkedChildren={<EyeOutlined />}
          unCheckedChildren={<EyeInvisibleOutlined />}
        />
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: MenuConfiguration) => (
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
            icon={<UpOutlined />}
            onClick={() => adjustOrder(record.id!, 'up')}
            disabled={record.order === 1}
          >
            上移
          </Button>
          
          <Button
            type="link"
            size="small"
            icon={<DownOutlined />}
            onClick={() => adjustOrder(record.id!, 'down')}
            disabled={record.order === allMenuItems.length}
          >
            下移
          </Button>

          <Popconfirm
            title="确定要删除这个菜单项吗?"
            onConfirm={() => handleDelete(record.id!)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              icon={<DeleteOutlined />}
              danger
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>菜单配置</Title>
      <Text type="secondary">
        管理系统左侧菜单的显示项目、顺序和分组。修改后系统会自动刷新菜单配置。
      </Text>

      <Card style={{ marginTop: 24 }}>
        <Alert
          message="菜单管理说明"
          description="在这里可以添加、编辑、删除和调整菜单项的顺序。支持主要功能和系统管理两个分组，每个菜单项可以设置图标、路径、组件等属性。"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
          <div>
            <Text type="secondary">共 {allMenuItems.length} 个菜单项</Text>
            <Text type="secondary" style={{ marginLeft: 16 }}>
              启用: {allMenuItems.filter(item => item.enabled).length} 个
            </Text>
          </div>
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadAllMenuItems}
              loading={loading}
            >
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => showEditModal()}
            >
              添加菜单项
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={allMenuItems.sort((a, b) => a.order - b.order)}
          rowKey="id"
          size="small"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 项，共 ${total} 项`,
          }}
        />
      </Card>

      <Modal
        title={editingMenu ? '编辑菜单项' : '添加菜单项'}
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
          setEditingMenu(null);
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
            label="菜单键值"
            rules={[
              { required: true, message: '请输入菜单键值' },
              { pattern: /^\/[a-zA-Z0-9-_/]*$/, message: '键值必须以/开头，只能包含字母、数字、-、_和/' }
            ]}
          >
            <Input placeholder="例如: /custom-query" />
          </Form.Item>

          <Form.Item
            name="label"
            label="显示名称"
            rules={[
              { required: true, message: '请输入显示名称' },
              { max: 50, message: '名称不能超过50个字符' }
            ]}
          >
            <Input placeholder="例如: 自定义查询" />
          </Form.Item>

          <Form.Item
            name="icon"
            label="图标"
            rules={[{ required: true, message: '请选择图标' }]}
          >
            <Select placeholder="选择图标" showSearch>
              {availableIcons.map(icon => (
                <Option key={icon} value={icon}>
                  <Space>
                    {getIconComponent(icon)}
                    {icon}
                  </Space>
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="path"
            label="路径"
            rules={[
              { required: true, message: '请输入路径' },
              { pattern: /^\/[a-zA-Z0-9-_/]*$/, message: '路径必须以/开头，只能包含字母、数字、-、_和/' }
            ]}
          >
            <Input placeholder="例如: /custom-query" />
          </Form.Item>

          <Form.Item
            name="component"
            label="组件"
            rules={[{ required: true, message: '请选择组件' }]}
          >
            <Select placeholder="选择组件" showSearch>
              {availableComponents.map(component => (
                <Option key={component} value={component}>
                  {component}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="position"
            label="位置"
            rules={[{ required: true, message: '请选择位置' }]}
          >
            <Select placeholder="选择位置">
              <Option value="top">顶部</Option>
              <Option value="bottom">底部</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="section"
            label="分组"
            rules={[{ required: true, message: '请选择分组' }]}
          >
            <Select placeholder="选择分组">
              <Option value="main">主要功能</Option>
              <Option value="system">系统管理</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="order"
            label="排序"
            rules={[{ required: true, message: '请输入排序值' }]}
          >
            <InputNumber min={1} max={100} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="enabled" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
            <Text style={{ marginLeft: 8 }}>启用此菜单项</Text>
          </Form.Item>

          <Divider />

          <Form.Item style={{ marginBottom: 0 }}>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                {editingMenu ? '更新' : '创建'}
              </Button>
              <Button
                onClick={() => {
                  setIsModalVisible(false);
                  form.resetFields();
                  setEditingMenu(null);
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

export default MenuConfig;