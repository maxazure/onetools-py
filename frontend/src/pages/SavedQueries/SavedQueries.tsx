/**
 * Saved Queries Page
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Row,
  Col,
  Card,
  Button,
  Space,
  Modal,
  Input,
  Typography,
  Table,
  Tag,
  Divider,
  Popconfirm,
  Tooltip,
  Select,
  Switch,
  App,
  Badge,
} from 'antd';
import {
  PlayCircleOutlined,
  EditOutlined,
  DeleteOutlined,
  CopyOutlined,
  StarOutlined,
  StarFilled,
  FileTextOutlined,
  PlusOutlined,
  SearchOutlined,
  FilterOutlined,
  TagOutlined,
} from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import type { ColumnsType } from 'antd/es/table';
import { SavedQuery, SavedQueryRequest, QueryType } from '../../types/api';
import { queryHistoryApi } from '../../services/api';
import { useDatabaseContext } from '../../contexts/DatabaseContext';
import SqlEditor from '../../components/SqlEditor/SqlEditor';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

const SavedQueries: React.FC = () => {
  const [selectedQuery, setSelectedQuery] = useState<SavedQuery | null>(null);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [viewModalVisible, setViewModalVisible] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [filterFavorites, setFilterFavorites] = useState(false);
  const [filterQueryType, setFilterQueryType] = useState<QueryType | 'ALL'>('ALL');
  
  // Form fields for create/edit modal
  const [formData, setFormData] = useState<SavedQueryRequest>({
    name: '',
    description: '',
    sql: '',
    query_type: 'CUSTOM',
    params: {},
    is_public: false,
    tags: [],
    is_favorite: false,
  });

  const queryClient = useQueryClient();
  const { currentServer } = useDatabaseContext();
  const { message } = App.useApp();
  const navigate = useNavigate();

  // Fetch saved queries
  const { data: savedQueries, isLoading, error, refetch } = useQuery<SavedQuery[]>({
    queryKey: ['saved-queries'],
    queryFn: async () => {
      try {
        const response = await queryHistoryApi.getSavedQueries();
        console.log('Saved queries response:', response); // Debug log
        
        // Ensure we return an array
        const data = response.data;
        if (Array.isArray(data)) {
          return data;
        } else if (data && Array.isArray(data.items)) {
          // If the response has a paginated structure
          return data.items;
        } else {
          console.warn('Unexpected saved queries data format:', data);
          return [];
        }
      } catch (error) {
        console.error('Failed to fetch saved queries:', error);
        return [];
      }
    },
    staleTime: 1 * 60 * 1000, // 减少缓存时间到1分钟
    refetchOnMount: 'always', // 确保每次组件挂载时都重新获取数据
    refetchOnWindowFocus: false, // 避免窗口获焦时重复加载
  });

  // 强制在组件挂载时重新获取数据
  useEffect(() => {
    refetch();
  }, [refetch]);

  // Create saved query mutation
  const createQueryMutation = useMutation({
    mutationFn: (queryData: SavedQueryRequest) =>
      queryHistoryApi.saveQuery(queryData.sql, queryData.name),
    onSuccess: () => {
      message.success('Query saved successfully!');
      setCreateModalVisible(false);
      resetForm();
      queryClient.invalidateQueries({ queryKey: ['saved-queries'] });
    },
    onError: (error: any) => {
      message.error(error.error_message || 'Failed to save query');
    },
  });

  // Update saved query mutation
  const updateQueryMutation = useMutation({
    mutationFn: ({ id, queryData }: { id: number; queryData: SavedQueryRequest }) =>
      queryHistoryApi.updateSavedQuery(id, queryData.sql, queryData.name),
    onSuccess: () => {
      message.success('Query updated successfully!');
      setEditModalVisible(false);
      setSelectedQuery(null);
      resetForm();
      queryClient.invalidateQueries({ queryKey: ['saved-queries'] });
    },
    onError: (error: any) => {
      message.error(error.error_message || 'Failed to update query');
    },
  });

  // Delete saved query mutation
  const deleteQueryMutation = useMutation({
    mutationFn: (queryId: number) =>
      queryHistoryApi.deleteSavedQuery(queryId),
    onSuccess: () => {
      message.success('Query deleted successfully!');
      queryClient.invalidateQueries({ queryKey: ['saved-queries'] });
    },
    onError: (error: any) => {
      message.error(error.error_message || 'Failed to delete query');
    },
  });

  // Reset form
  const resetForm = useCallback(() => {
    setFormData({
      name: '',
      description: '',
      sql: '',
      query_type: 'CUSTOM',
      params: {},
      is_public: false,
      tags: [],
      is_favorite: false,
    });
  }, []);

  // Handle create query
  const handleCreateQuery = useCallback(() => {
    setCreateModalVisible(true);
    resetForm();
  }, [resetForm]);

  // Handle edit query
  const handleEditQuery = useCallback((query: SavedQuery) => {
    setSelectedQuery(query);
    setFormData({
      name: query.name,
      description: query.description || '',
      sql: query.sql,
      query_type: query.query_type,
      params: query.params || {},
      is_public: query.is_public || false,
      tags: query.tags || [],
      is_favorite: query.is_favorite || false,
    });
    setEditModalVisible(true);
  }, []);

  // Handle view query
  const handleViewQuery = useCallback((query: SavedQuery) => {
    setSelectedQuery(query);
    setViewModalVisible(true);
  }, []);

  // Handle execute query
  const handleExecuteQuery = useCallback((query: SavedQuery) => {
    if (!currentServer) {
      message.warning('Please select a database server first');
      return;
    }
    
    // Navigate to custom query page with the SQL pre-filled
    navigate('/custom-query', { 
      state: { 
        sql: query.sql,
        name: query.name,
        queryId: query.id 
      } 
    });
  }, [currentServer, message, navigate]);

  // Handle delete query
  const handleDeleteQuery = useCallback((queryId: number) => {
    deleteQueryMutation.mutate(queryId);
  }, [deleteQueryMutation]);

  // Handle save form
  const handleSaveForm = useCallback(() => {
    if (!formData.name.trim()) {
      message.warning('Please enter a query name');
      return;
    }
    
    if (!formData.sql.trim()) {
      message.warning('Please enter SQL query');
      return;
    }

    if (selectedQuery) {
      // Update existing query
      updateQueryMutation.mutate({
        id: selectedQuery.id!,
        queryData: formData,
      });
    } else {
      // Create new query
      createQueryMutation.mutate(formData);
    }
  }, [formData, selectedQuery, createQueryMutation, updateQueryMutation, message]);

  // Filter queries based on search and filters
  const filteredQueries = React.useMemo(() => {
    if (!savedQueries || !Array.isArray(savedQueries)) return [];
    
    return savedQueries.filter(query => {
      // Search filter
      const matchesSearch = !searchText || 
        query.name.toLowerCase().includes(searchText.toLowerCase()) ||
        query.description?.toLowerCase().includes(searchText.toLowerCase()) ||
        query.sql.toLowerCase().includes(searchText.toLowerCase());
      
      // Favorites filter
      const matchesFavorites = !filterFavorites || query.is_favorite;
      
      // Query type filter
      const matchesQueryType = filterQueryType === 'ALL' || query.query_type === filterQueryType;
      
      return matchesSearch && matchesFavorites && matchesQueryType;
    });
  }, [savedQueries, searchText, filterFavorites, filterQueryType]);

  // Table columns
  const columns: ColumnsType<SavedQuery> = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (text: string, record: SavedQuery) => (
        <Space>
          {record.is_favorite ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
          <Button type="link" onClick={() => handleViewQuery(record)}>
            {text}
          </Button>
        </Space>
      ),
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string) => text || '-',
    },
    {
      title: 'Type',
      dataIndex: 'query_type',
      key: 'query_type',
      width: 100,
      render: (type: QueryType) => (
        <Tag color={type === 'CUSTOM' ? 'blue' : type === 'DYNAMIC' ? 'green' : 'orange'}>
          {type}
        </Tag>
      ),
    },
    {
      title: 'Public',
      dataIndex: 'is_public',
      key: 'is_public',
      width: 80,
      render: (isPublic: boolean) => (
        <Badge status={isPublic ? 'success' : 'default'} text={isPublic ? 'Yes' : 'No'} />
      ),
    },
    {
      title: 'Tags',
      dataIndex: 'tags',
      key: 'tags',
      width: 150,
      render: (tags: string[]) => (
        <Space>
          {tags?.slice(0, 2).map(tag => (
            <Tag key={tag} icon={<TagOutlined />} color="processing">
              {tag}
            </Tag>
          ))}
          {tags?.length > 2 && <Tag>+{tags.length - 2}</Tag>}
        </Space>
      ),
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date: string) => date ? new Date(date).toLocaleDateString() : '-',
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 200,
      render: (_, record: SavedQuery) => (
        <Space size="small">
          <Tooltip title="Execute Query">
            <Button
              type="text"
              icon={<PlayCircleOutlined />}
              onClick={() => handleExecuteQuery(record)}
            />
          </Tooltip>
          <Tooltip title="Edit Query">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEditQuery(record)}
            />
          </Tooltip>
          <Tooltip title="Copy SQL">
            <Button
              type="text"
              icon={<CopyOutlined />}
              onClick={() => {
                navigator.clipboard.writeText(record.sql);
                message.success('SQL copied to clipboard!');
              }}
            />
          </Tooltip>
          <Popconfirm
            title="Delete Query"
            description="Are you sure you want to delete this query?"
            onConfirm={() => handleDeleteQuery(record.id!)}
            okText="Yes"
            cancelText="No"
          >
            <Tooltip title="Delete Query">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>
          <FileTextOutlined style={{ marginRight: '8px' }} />
          Saved Queries
        </Title>
        <Paragraph type="secondary">
          Manage your saved SQL queries. Create, edit, organize and execute your frequently used queries.
        </Paragraph>
      </div>

      {/* Filters and Actions */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={8} lg={6}>
            <Input
              placeholder="Search queries..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear
            />
          </Col>
          <Col xs={12} sm={6} md={4} lg={3}>
            <Select
              placeholder="Query Type"
              value={filterQueryType}
              onChange={setFilterQueryType}
              style={{ width: '100%' }}
            >
              <Option value="ALL">All Types</Option>
              <Option value="CUSTOM">Custom</Option>
              <Option value="USER">User</Option>
              <Option value="TRANSACTION">Transaction</Option>
              <Option value="DYNAMIC">Dynamic</Option>
            </Select>
          </Col>
          <Col xs={12} sm={6} md={4} lg={3}>
            <Space>
              <Switch
                checked={filterFavorites}
                onChange={setFilterFavorites}
                checkedChildren={<StarFilled />}
                unCheckedChildren={<StarOutlined />}
              />
              <Text>Favorites Only</Text>
            </Space>
          </Col>
          <Col xs={24} sm={12} md={8} lg={6} style={{ textAlign: 'right' }}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreateQuery}
            >
              Create Query
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Queries Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={filteredQueries}
          rowKey="id"
          loading={isLoading}
          pagination={{
            total: filteredQueries.length,
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} queries`,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={selectedQuery ? 'Edit Query' : 'Create New Query'}
        open={createModalVisible || editModalVisible}
        onOk={handleSaveForm}
        onCancel={() => {
          setCreateModalVisible(false);
          setEditModalVisible(false);
          setSelectedQuery(null);
          resetForm();
        }}
        confirmLoading={createQueryMutation.isPending || updateQueryMutation.isPending}
        okText={selectedQuery ? 'Update' : 'Create'}
        cancelText="Cancel"
        width={800}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <Text strong>Query Name *</Text>
            <Input
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="Enter query name..."
              style={{ marginTop: 8 }}
            />
          </div>
          
          <div>
            <Text strong>Description</Text>
            <TextArea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Enter query description..."
              rows={2}
              style={{ marginTop: 8 }}
            />
          </div>

          <div>
            <Text strong>SQL Query *</Text>
            <div style={{ marginTop: 8, border: '1px solid #d9d9d9', borderRadius: '6px' }}>
              <SqlEditor
                value={formData.sql}
                onChange={(value) => setFormData(prev => ({ ...prev, sql: value }))}
                onExecute={() => {}} // Dummy function for create/edit mode
                height={200}
              />
            </div>
          </div>

          <Row gutter={16}>
            <Col span={8}>
              <Text strong>Query Type</Text>
              <Select
                value={formData.query_type}
                onChange={(value) => setFormData(prev => ({ ...prev, query_type: value }))}
                style={{ width: '100%', marginTop: 8 }}
              >
                <Option value="CUSTOM">Custom</Option>
                <Option value="USER">User</Option>
                <Option value="TRANSACTION">Transaction</Option>
                <Option value="DYNAMIC">Dynamic</Option>
              </Select>
            </Col>
            <Col span={8}>
              <Text strong>Public Query</Text>
              <div style={{ marginTop: 8 }}>
                <Switch
                  checked={formData.is_public}
                  onChange={(checked) => setFormData(prev => ({ ...prev, is_public: checked }))}
                />
              </div>
            </Col>
            <Col span={8}>
              <Text strong>Favorite</Text>
              <div style={{ marginTop: 8 }}>
                <Switch
                  checked={formData.is_favorite}
                  onChange={(checked) => setFormData(prev => ({ ...prev, is_favorite: checked }))}
                  checkedChildren={<StarFilled />}
                  unCheckedChildren={<StarOutlined />}
                />
              </div>
            </Col>
          </Row>
        </Space>
      </Modal>

      {/* View Modal */}
      <Modal
        title={
          <Space>
            <FileTextOutlined />
            {selectedQuery?.name}
            {selectedQuery?.is_favorite && <StarFilled style={{ color: '#faad14' }} />}
          </Space>
        }
        open={viewModalVisible}
        onCancel={() => {
          setViewModalVisible(false);
          setSelectedQuery(null);
        }}
        footer={[
          <Button key="copy" icon={<CopyOutlined />} onClick={() => {
            navigator.clipboard.writeText(selectedQuery?.sql || '');
            message.success('SQL copied to clipboard!');
          }}>
            Copy SQL
          </Button>,
          <Button key="edit" type="primary" icon={<EditOutlined />} onClick={() => {
            setViewModalVisible(false);
            handleEditQuery(selectedQuery!);
          }}>
            Edit
          </Button>,
          <Button key="execute" type="primary" icon={<PlayCircleOutlined />} onClick={() => {
            setViewModalVisible(false);
            handleExecuteQuery(selectedQuery!);
          }}>
            Execute
          </Button>,
        ]}
        width={800}
      >
        {selectedQuery && (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            {selectedQuery.description && (
              <div>
                <Text strong>Description:</Text>
                <Paragraph style={{ marginTop: 8 }}>{selectedQuery.description}</Paragraph>
              </div>
            )}
            
            <div>
              <Text strong>Query Type:</Text>
              <Tag color={selectedQuery.query_type === 'CUSTOM' ? 'blue' : 'green'} style={{ marginLeft: 8 }}>
                {selectedQuery.query_type}
              </Tag>
            </div>

            <div>
              <Text strong>SQL Query:</Text>
              <div style={{ marginTop: 8, border: '1px solid #d9d9d9', borderRadius: '6px' }}>
                <SqlEditor
                  value={selectedQuery.sql}
                  onChange={() => {}} // Read-only
                  onExecute={() => {}} // Dummy function for read-only mode
                  height={200}
                  readOnly
                />
              </div>
            </div>

            {selectedQuery.tags && selectedQuery.tags.length > 0 && (
              <div>
                <Text strong>Tags:</Text>
                <div style={{ marginTop: 8 }}>
                  {selectedQuery.tags.map(tag => (
                    <Tag key={tag} icon={<TagOutlined />} color="processing">
                      {tag}
                    </Tag>
                  ))}
                </div>
              </div>
            )}

            <Row gutter={16}>
              <Col span={8}>
                <Text strong>Public:</Text>
                <Badge 
                  status={selectedQuery.is_public ? 'success' : 'default'} 
                  text={selectedQuery.is_public ? 'Yes' : 'No'} 
                  style={{ marginLeft: 8 }}
                />
              </Col>
              <Col span={8}>
                <Text strong>Created:</Text>
                <Text style={{ marginLeft: 8 }}>
                  {selectedQuery.created_at ? new Date(selectedQuery.created_at).toLocaleString() : '-'}
                </Text>
              </Col>
              <Col span={8}>
                <Text strong>Updated:</Text>
                <Text style={{ marginLeft: 8 }}>
                  {selectedQuery.updated_at ? new Date(selectedQuery.updated_at).toLocaleString() : '-'}
                </Text>
              </Col>
            </Row>
          </Space>
        )}
      </Modal>
    </div>
  );
};

export default SavedQueries;
