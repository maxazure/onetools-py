/**
 * Custom Query Page
 */

import React, { useState, useCallback } from 'react';
import {
  Row,
  Col,
  Card,
  Button,
  Space,
  Modal,
  Input,
  Typography,
  Divider,
  Alert,
  App,
} from 'antd';
import {
  SaveOutlined,
  FolderOpenOutlined,
  ClearOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import SqlEditor from '../../components/SqlEditor/SqlEditor';
import QueryResults from '../../components/QueryResults/QueryResults';
import { apiService } from '../../services/api';
import { CustomQueryRequest, QueryResult } from '../../types/api';
import { useDatabaseContext } from '../../contexts/DatabaseContext';

const { Title, Text } = Typography;
const { TextArea } = Input;

const CustomQuery: React.FC = () => {
  const [sqlQuery, setSqlQuery] = useState('SELECT * FROM OneToolsDb.dbo.Users;');
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [saveModalVisible, setSaveModalVisible] = useState(false);
  const [queryName, setQueryName] = useState('');
  const [queryDescription, setQueryDescription] = useState('');
  
  const queryClient = useQueryClient();
  const { currentServer } = useDatabaseContext();
  const { message } = App.useApp();

  // Execute query mutation
  const executeQueryMutation = useMutation({
    mutationFn: (request: CustomQueryRequest) =>
      apiService.executeCustomQuery(request),
    retry: false, // 禁用重试以防止重复执行SQL操作（特别是INSERT/UPDATE/DELETE）
    onSuccess: (response) => {
      if (response.success && response.data) {
        const result: QueryResult = {
          columns: response.data.columns || [],
          data: response.data.data || [],
          total_count: response.data.total || 0,
          execution_time: response.data.execution_time || 0,
        };
        setQueryResult(result);
        message.success(`Query executed successfully! Found ${result.total_count} rows.`);
      } else {
        message.error(response.message || 'Query execution failed');
      }
    },
    onError: (error: any) => {
      message.error(error.error_message || 'Failed to execute query');
      console.error('Query execution error:', error);
    },
  });

  // Save query mutation
  const saveQueryMutation = useMutation({
    mutationFn: ({ query, name, description }: { query: string; name: string; description?: string }) =>
      apiService.saveQuery(query, name, description),
    retry: false, // 禁用重试以防止重复保存
    onSuccess: () => {
      message.success('Query saved successfully!');
      setSaveModalVisible(false);
      setQueryName('');
      setQueryDescription('');
      queryClient.invalidateQueries({ queryKey: ['saved-queries'] });
    },
    onError: (error: any) => {
      message.error(error.error_message || 'Failed to save query');
    },
  });

  // Get saved queries
  const { data: savedQueries } = useQuery({
    queryKey: ['saved-queries'],
    queryFn: () => apiService.getSavedQueries(),
  });

  const handleExecuteQuery = useCallback(() => {
    if (!sqlQuery.trim()) {
      message.warning('Please enter a SQL query');
      return;
    }

    if (!currentServer) {
      message.warning('Please select a database server first');
      return;
    }


    const request: CustomQueryRequest = {
      sql: sqlQuery,
      server_name: currentServer,
    };

    executeQueryMutation.mutate(request);
  }, [sqlQuery, currentServer, executeQueryMutation, message]);

  const handleSaveQuery = useCallback(() => {
    if (!sqlQuery.trim()) {
      message.warning('Please enter a SQL query to save');
      return;
    }
    setSaveModalVisible(true);
  }, [sqlQuery, message]);

  const handleConfirmSave = useCallback(() => {
    if (!queryName.trim()) {
      message.warning('Please enter a query name');
      return;
    }

    saveQueryMutation.mutate({
      query: sqlQuery,
      name: queryName,
      description: queryDescription,
    });
  }, [sqlQuery, queryName, queryDescription, saveQueryMutation, message]);

  const handleFormatQuery = useCallback(() => {
    // Basic SQL formatting - in a real app, you might use a SQL formatter library
    const formatted = sqlQuery
      .replace(/\s+/g, ' ')
      .replace(/,\s*/g, ',\n  ')
      .replace(/\bSELECT\b/gi, 'SELECT')
      .replace(/\bFROM\b/gi, '\nFROM')
      .replace(/\bWHERE\b/gi, '\nWHERE')
      .replace(/\bORDER BY\b/gi, '\nORDER BY')
      .replace(/\bGROUP BY\b/gi, '\nGROUP BY')
      .replace(/\bHAVING\b/gi, '\nHAVING')
      .replace(/\bJOIN\b/gi, '\nJOIN')
      .replace(/\bINNER JOIN\b/gi, '\nINNER JOIN')
      .replace(/\bLEFT JOIN\b/gi, '\nLEFT JOIN')
      .replace(/\bRIGHT JOIN\b/gi, '\nRIGHT JOIN')
      .replace(/\bFULL JOIN\b/gi, '\nFULL JOIN')
      .trim();
    
    setSqlQuery(formatted);
    message.success('Query formatted');
  }, [sqlQuery, message]);

  const handleClearQuery = useCallback(() => {
    setSqlQuery('');
    setQueryResult(null);
    message.info('Query cleared');
  }, [message]);

  const handleExport = useCallback((format: 'csv' | 'excel') => {
    if (!queryResult) {
      message.warning('No data to export');
      return;
    }

    // In a real implementation, this would call the export API
    // For now, we'll just show a message
    message.info(`Exporting ${queryResult.data.length} rows as ${format.toUpperCase()}...`);
  }, [queryResult, message]);


  return (
    <div style={{ height: 'calc(100vh - 112px)', display: 'flex', flexDirection: 'column' }}>
      {/* SQL查询编辑器区域 */}
      <div style={{ marginBottom: '16px' }}>
        <Card 
          title="SQL查询编辑器" 
          size="small"
          style={{ height: '320px' }}
          bodyStyle={{ height: '280px', padding: '16px' }}
        >
          <SqlEditor
            value={sqlQuery}
            onChange={setSqlQuery}
            onExecute={handleExecuteQuery}
            onSave={handleSaveQuery}
            onFormat={handleFormatQuery}
            onClear={handleClearQuery}
            loading={executeQueryMutation.isPending}
            height={220}
          />
        </Card>
      </div>

      {/* 查询结果区域 */}
      <div style={{ flex: 1, minHeight: 0 }}>
        <QueryResults
          data={queryResult}
          loading={executeQueryMutation.isPending}
          error={executeQueryMutation.error?.error_message || null}
          onExport={handleExport}
          onRefresh={handleExecuteQuery}
        />
      </div>

      {/* Save Query Modal */}
      <Modal
        title="保存查询"
        open={saveModalVisible}
        onOk={handleConfirmSave}
        onCancel={() => {
          setSaveModalVisible(false);
          setQueryName('');
          setQueryDescription('');
        }}
        confirmLoading={saveQueryMutation.isPending}
        okText="保存"
        cancelText="取消"
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <Text strong>查询名称:</Text>
            <Input
              value={queryName}
              onChange={(e) => setQueryName(e.target.value)}
              placeholder="输入查询名称..."
              style={{ marginTop: 8 }}
            />
          </div>
          
          <div>
            <Text strong>查询描述:</Text>
            <TextArea
              value={queryDescription}
              onChange={(e) => setQueryDescription(e.target.value)}
              placeholder="输入查询描述（可选）..."
              rows={2}
              style={{ marginTop: 8 }}
            />
          </div>
          
          <div>
            <Text strong>查询预览:</Text>
            <TextArea
              value={sqlQuery}
              rows={4}
              readOnly
              style={{ marginTop: 8 }}
            />
          </div>
        </Space>
      </Modal>
    </div>
  );
};

export default CustomQuery;