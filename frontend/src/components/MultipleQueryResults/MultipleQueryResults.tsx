/**
 * Multiple Query Results Component
 */

import React from 'react';
import {
  Card,
  Space,
  Button,
  Typography,
  Alert,
  Spin,
  Row,
  Col,
  message,
  Divider,
} from 'antd';
import {
  DownloadOutlined,
  CopyOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  TableOutlined,
  CheckCircleOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';
import { MultipleQueryResult } from '../../types/api';
import VirtualTable from '../VirtualTable/VirtualTable';

const { Title, Text } = Typography;

interface MultipleQueryResultsProps {
  data?: MultipleQueryResult | null;
  loading?: boolean;
  error?: string | null;
  onExport?: (format: 'csv' | 'excel') => void;
  onRefresh?: () => void;
}

const MultipleQueryResults: React.FC<MultipleQueryResultsProps> = ({
  data,
  loading = false,
  error = null,
  onExport,
  onRefresh,
}) => {

  const handleCopyToClipboard = async (resultIndex: number) => {
    if (!data?.results || data.results.length === 0) {
      message.warning('No data to copy');
      return;
    }

    const result = data.results[resultIndex];
    if (!result || !result.data || result.data.length === 0) {
      message.warning('No data to copy');
      return;
    }

    try {
      // Convert data to CSV format
      const headers = result.columns.join('\t');
      const rows = result.data.map(row => 
        result.columns.map(col => String(row[col] || '')).join('\t')
      ).join('\n');
      const csvContent = `${headers}\n${rows}`;

      await navigator.clipboard.writeText(csvContent);
      message.success(`Data from Result Set ${resultIndex + 1} copied to clipboard`);
    } catch (err) {
      message.error('Failed to copy data');
    }
  };

  const calculateTableHeight = (rowCount: number): number => {
    // 表头高度约 32px，每行约 32px，最多显示20行，最少显示2行
    const headerHeight = 32;
    const rowHeight = 32;
    const maxRows = Math.min(Math.max(rowCount, 2), 20);
    return headerHeight + (maxRows * rowHeight);
  };

  if (error) {
    return (
      <Card title="查询结果">
        <Alert
          message="查询错误"
          description={error}
          type="error"
          showIcon
          action={
            onRefresh && (
              <Button size="small" onClick={onRefresh} icon={<ReloadOutlined />}>
                重试
              </Button>
            )
          }
        />
      </Card>
    );
  }

  return (
    <Card
      title={
        <Space>
          <InfoCircleOutlined />
          <span>查询结果</span>
          {data && (
            <Text type="secondary">({data.results.length} 个结果集)</Text>
          )}
          {loading && <Spin size="small" />}
        </Space>
      }
      extra={
        onRefresh && (
          <Button
            icon={<ReloadOutlined />}
            onClick={onRefresh}
            loading={loading}
            size="small"
          >
            刷新
          </Button>
        )
      }
    >
      {data && data.results && data.results.length > 0 ? (
        <>
          {data.results.map((result, index) => {
            const isRowCount = result.type === 'rowcount';
            const icon = isRowCount ? <CheckCircleOutlined /> : <TableOutlined />;
            const title = isRowCount ? `操作结果 ${result.index}` : `结果集 ${result.index}`;
            const description = isRowCount ? `影响 ${result.total} 行` : `${result.total} 行`;
            
            return (
              <div key={index}>
                <div
                  style={{ 
                    marginBottom: index < data.results.length - 1 ? 16 : 0,
                    backgroundColor: isRowCount ? '#f6ffed' : undefined,
                    border: isRowCount ? '1px solid #b7eb8f' : '1px solid #d9d9d9',
                    borderRadius: '6px',
                    overflow: 'hidden'
                  }}
                >
                  {isRowCount ? (
                    // 行数结果显示
                    <div style={{ padding: '12px 0', textAlign: 'center' }}>
                      <Space direction="vertical" size="small">
                        <CheckCircleOutlined style={{ fontSize: '24px', color: '#52c41a' }} />
                        <Text strong style={{ fontSize: '16px' }}>
                          {result.message}
                        </Text>
                        <Text type="secondary">
                          语句执行成功
                        </Text>
                      </Space>
                    </div>
                  ) : (
                    // 结果集显示
                    <div style={{ position: 'relative' }}>
                      <VirtualTable
                        data={result.data || []}
                        columns={result.columns || []}
                        height={calculateTableHeight(result.total)}
                        loading={loading}
                      />
                      
                      <div style={{ 
                        position: 'absolute', 
                        top: '8px', 
                        right: '8px', 
                        zIndex: 10 
                      }}>
                        <Button
                          icon={<CopyOutlined />}
                          onClick={() => handleCopyToClipboard(index)}
                          disabled={!result.data || result.data.length === 0}
                          size="small"
                          type="text"
                        >
                          复制
                        </Button>
                      </div>
                      
                      <div style={{ padding: '8px 12px', background: '#fafafa', borderTop: '1px solid #f0f0f0' }}>
                        <Text type="secondary">
                          记录数: {result.total}
                        </Text>
                      </div>
                    </div>
                  )}
                </div>
                
                {index < data.results.length - 1 && (
                  <Divider style={{ margin: '16px 0' }} />
                )}
              </div>
            );
          })}

          {/* Footer info */}
          <div style={{ marginTop: 16, textAlign: 'right' }}>
            <Space split={<span>•</span>}>
              <Text type="secondary">
                总结果集: {data.results.length} | 执行时间: {data.execution_time?.toFixed(2)}秒
              </Text>
              <Text type="secondary">
                总记录数: {data.results.reduce((sum, result) => sum + result.total, 0)}
              </Text>
            </Space>
          </div>
        </>
      ) : (
        !loading && (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Text type="secondary">
              执行查询后结果将在此处显示
            </Text>
          </div>
        )
      )}
    </Card>
  );
};

export default MultipleQueryResults;