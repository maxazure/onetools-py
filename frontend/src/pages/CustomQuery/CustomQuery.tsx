/**
 * Custom Query Page
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
import { useLocation } from 'react-router-dom';
import SqlEditor from '../../components/SqlEditor/SqlEditor';
import QueryResults from '../../components/QueryResults/QueryResults';
import MultipleQueryResults from '../../components/MultipleQueryResults/MultipleQueryResults';
import SchemaAnalysisModal from '../../components/SchemaAnalysisModal/SchemaAnalysisModal';
import { apiService, customQueryApi } from '../../services/api';
import { CustomQueryRequest, QueryResult, MultipleQueryResult } from '../../types/api';
import { useDatabaseContext } from '../../contexts/DatabaseContext';

const { Title, Text } = Typography;
const { TextArea } = Input;

const CustomQuery: React.FC = () => {
  const [sqlQuery, setSqlQuery] = useState('');
  const [queryResult, setQueryResult] = useState<QueryResult | MultipleQueryResult | null>(null);
  const [saveModalVisible, setSaveModalVisible] = useState(false);
  const [queryName, setQueryName] = useState('');
  const [queryDescription, setQueryDescription] = useState('');
  const [schemaModalVisible, setSchemaModalVisible] = useState(false);
  const [schemaAnalysisData, setSchemaAnalysisData] = useState<any>(null);
  
  const queryClient = useQueryClient();
  const { currentServer } = useDatabaseContext();
  const { message } = App.useApp();
  const location = useLocation();

  // Fetch default SQL from system settings
  const { data: defaultSqlSetting, isLoading: isLoadingSettings, error: settingsError } = useQuery({
    queryKey: ['system-setting', 'default_custom_query_sql'],
    queryFn: async () => {
      try {
        const response = await apiService.getSystemSetting('default_custom_query_sql');
        
        if (response.success && response.data?.value) {
          return response.data.value;
        } else {
          return 'SELECT * FROM OneToolsDb.dbo.Users;';
        }
      } catch (error) {
        console.log('Error fetching default SQL setting:', error);
        return 'SELECT * FROM OneToolsDb.dbo.Users;';
      }
    },
    staleTime: 1 * 60 * 1000, // 减少到1分钟缓存
    refetchOnMount: true, // 确保每次加载都重新获取
  });

  // Initialize SQL query with default setting
  useEffect(() => {
    // Only set default SQL setting when it's first loaded and no navigation SQL
    if (defaultSqlSetting && !location.state?.sql) {
      setSqlQuery(defaultSqlSetting);
    }
  }, [defaultSqlSetting, location.state?.sql]);

  // Handle incoming SQL from saved queries navigation
  useEffect(() => {
    if (location.state?.sql) {
      setSqlQuery(location.state.sql);
      
      // Show success message indicating the query was loaded
      const queryName = location.state.name || 'saved query';
      message.success(`Loaded SQL from "${queryName}"`);
      
      // Clear the state to prevent reloading on subsequent renders
      window.history.replaceState({}, document.title);
    }
  }, [location.state, message]);

  // Execute query mutation
  const executeQueryMutation = useMutation({
    mutationFn: (request: CustomQueryRequest) =>
      apiService.executeCustomQuery(request),
    retry: false, // 禁用重试以防止重复执行SQL操作（特别是INSERT/UPDATE/DELETE）
    onSuccess: (response) => {
      if (response.success && response.data) {
        // 检查是否为多结果集
        if (response.data.is_multiple && Array.isArray(response.data.data)) {
          const multipleResult: MultipleQueryResult = {
            results: response.data.data.map((resultSet: any) => ({
              type: resultSet.type || 'resultset',
              index: resultSet.index || 1,
              columns: resultSet.columns || [],
              data: resultSet.data || [],
              total: resultSet.total || 0,
              message: resultSet.message || '',
            })),
            execution_time: response.data.execution_time || 0,
            is_multiple: true,
          };
          setQueryResult(multipleResult);
          
          // 统计结果集和操作结果的数量
          const resultSets = multipleResult.results.filter(r => r.type === 'resultset').length;
          const operations = multipleResult.results.filter(r => r.type === 'rowcount').length;
          
          let successMsg = 'Query executed successfully!';
          if (resultSets > 0 && operations > 0) {
            successMsg += ` Found ${resultSets} result sets and ${operations} operations.`;
          } else if (resultSets > 0) {
            successMsg += ` Found ${resultSets} result sets.`;
          } else if (operations > 0) {
            successMsg += ` Completed ${operations} operations.`;
          }
          
          message.success(successMsg);
        } else {
          // 单结果集
          const result: QueryResult = {
            columns: response.data.columns || [],
            data: response.data.data || [],
            total_count: response.data.total || 0,
            execution_time: response.data.execution_time || 0,
            is_multiple: false,
          };
          setQueryResult(result);
          message.success(`Query executed successfully! Found ${result.total_count} rows.`);
        }
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
    mutationFn: (queryData: any) =>
      apiService.saveQuery(queryData),
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

  // Schema analysis mutation
  const schemaAnalysisMutation = useMutation({
    mutationFn: (request: { sql: string; server_name?: string }) => customQueryApi.analyzeSchema(request),
    onSuccess: (response) => {
      if (response.success && response.data) {
        setSchemaAnalysisData(response.data);
        setSchemaModalVisible(true);
        message.success('表结构分析完成');
      } else {
        message.error('表结构分析失败');
      }
    },
    onError: (error: any) => {
      const errorMessage = error?.response?.data?.detail || error?.message || 'Schema analysis failed';
      message.error(`表结构分析失败: ${errorMessage}`);
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
      sql: sqlQuery,
      name: queryName,
      description: queryDescription,
      query_type: 'custom',
      params: {},
      is_public: false,
      tags: [],
      is_favorite: false
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

  const handleReloadDefault = useCallback(async () => {
    try {
      // Force reload default SQL setting
      queryClient.invalidateQueries({ queryKey: ['system-setting', 'default_custom_query_sql'] });
      
      // Wait a moment for the query to refetch, then get the latest value
      setTimeout(async () => {
        try {
          const response = await apiService.getSystemSetting('default_custom_query_sql');
          if (response.success && response.data?.value) {
            setSqlQuery(response.data.value);
            message.success('Default SQL reloaded successfully');
          } else {
            message.warning('No default SQL setting found');
          }
        } catch (error) {
          console.error('Error reloading default SQL:', error);
          message.error('Failed to reload default SQL');
        }
      }, 100);
      
    } catch (error) {
      console.error('Error invalidating query:', error);
      message.error('Failed to reload default SQL');
    }
  }, [queryClient, message]);

  const handleExport = useCallback((format: 'csv' | 'excel') => {
    if (!queryResult) {
      message.warning('No data to export');
      return;
    }

    // In a real implementation, this would call the export API
    // For now, we'll just show a message
    if ('is_multiple' in queryResult && queryResult.is_multiple) {
      const multipleResult = queryResult as MultipleQueryResult;
      const resultSets = multipleResult.results.filter(r => r.type === 'resultset');
      const totalRows = resultSets.reduce((sum: number, result) => sum + result.total, 0);
      
      if (resultSets.length > 0) {
        message.info(`Exporting ${resultSets.length} result sets (${totalRows} total rows) as ${format.toUpperCase()}...`);
      } else {
        message.info('No data available for export (only operation results)');
      }
    } else {
      const singleResult = queryResult as QueryResult;
      message.info(`Exporting ${singleResult.data.length} rows as ${format.toUpperCase()}...`);
    }
  }, [queryResult, message]);

  const handleAnalyzeSchema = useCallback(() => {
    if (!sqlQuery.trim()) {
      message.warning('请输入SQL查询语句');
      return;
    }

    schemaAnalysisMutation.mutate({
      sql: sqlQuery,
      server_name: currentServer
    });
  }, [sqlQuery, currentServer, schemaAnalysisMutation, message]);


  return (
    <div style={{ height: 'calc(100vh - 112px)', display: 'flex', flexDirection: 'column' }}>
      {/* SQL查询编辑器区域 */}
      <div style={{ marginBottom: '16px' }}>
        <Card 
          title={
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>SQL查询编辑器</span>
              <Button 
                size="small" 
                type="link" 
                onClick={handleReloadDefault}
                loading={isLoadingSettings}
              >
                重新加载默认SQL
              </Button>
            </div>
          }
          size="small"
          style={{ height: '320px' }}
          styles={{ body: { height: '280px', padding: '16px' } }}
        >
          <SqlEditor
            value={sqlQuery}
            onChange={setSqlQuery}
            onExecute={handleExecuteQuery}
            onSave={handleSaveQuery}
            onFormat={handleFormatQuery}
            onClear={handleClearQuery}
            onAnalyzeSchema={handleAnalyzeSchema}
            loading={executeQueryMutation.isPending}
            analyzingSchema={schemaAnalysisMutation.isPending}
            height={220}
          />
        </Card>
      </div>

      {/* 查询结果区域 */}
      <div style={{ flex: 1, minHeight: 0 }}>
        {queryResult && 'is_multiple' in queryResult && queryResult.is_multiple ? (
          <MultipleQueryResults
            data={queryResult as MultipleQueryResult}
            loading={executeQueryMutation.isPending}
            error={executeQueryMutation.error?.error_message || null}
            onExport={handleExport}
            onRefresh={handleExecuteQuery}
            sqlQuery={sqlQuery}
          />
        ) : (
          <QueryResults
            data={queryResult as QueryResult}
            loading={executeQueryMutation.isPending}
            error={executeQueryMutation.error?.error_message || null}
            onExport={handleExport}
            onRefresh={handleExecuteQuery}
          />
        )}
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

      {/* Schema Analysis Modal */}
      <SchemaAnalysisModal
        visible={schemaModalVisible}
        data={schemaAnalysisData}
        loading={schemaAnalysisMutation.isPending}
        onClose={() => {
          setSchemaModalVisible(false);
          setSchemaAnalysisData(null);
        }}
      />
    </div>
  );
};

export default CustomQuery;