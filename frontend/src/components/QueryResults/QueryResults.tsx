/**
 * Query Results Component
 */

import React from 'react';
import {
  Card,
  Space,
  Button,
  Typography,
  Alert,
  Spin,
  Statistic,
  Row,
  Col,
  message,
} from 'antd';
import {
  DownloadOutlined,
  CopyOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { QueryResult } from '../../types/api';
import VirtualTable from '../VirtualTable/VirtualTable';

const { Title, Text } = Typography;

interface QueryResultsProps {
  data?: QueryResult | null;
  loading?: boolean;
  error?: string | null;
  onExport?: (format: 'csv' | 'excel') => void;
  onRefresh?: () => void;
}

const QueryResults: React.FC<QueryResultsProps> = ({
  data,
  loading = false,
  error = null,
  onExport,
  onRefresh,
}) => {

  const handleCopyToClipboard = async () => {
    if (!data?.data || data.data.length === 0) {
      message.warning('No data to copy');
      return;
    }

    try {
      // Convert data to CSV format
      const headers = data.columns.join('\t');
      const rows = data.data.map(row => 
        data.columns.map(col => String(row[col] || '')).join('\t')
      ).join('\n');
      const csvContent = `${headers}\n${rows}`;

      await navigator.clipboard.writeText(csvContent);
      message.success('Data copied to clipboard');
    } catch (err) {
      message.error('Failed to copy data');
    }
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
          {loading && <Spin size="small" />}
        </Space>
      }
      extra={
        <Space>
          {onRefresh && (
            <Button
              icon={<ReloadOutlined />}
              onClick={onRefresh}
              loading={loading}
              size="small"
            >
              刷新
            </Button>
          )}
          <Button
            icon={<CopyOutlined />}
            onClick={handleCopyToClipboard}
            disabled={!data?.data || data.data.length === 0}
            size="small"
          >
            复制
          </Button>
          {onExport && (
            <Space.Compact size="small">
              <Button
                icon={<DownloadOutlined />}
                onClick={() => onExport('csv')}
                disabled={!data?.data || data.data.length === 0}
              >
                导出CSV
              </Button>
              <Button
                onClick={() => onExport('excel')}
                disabled={!data?.data || data.data.length === 0}
              >
                导出Excel
              </Button>
            </Space.Compact>
          )}
        </Space>
      }
    >
      {data && (
        <>
          {/* High Performance Virtual Table */}
          <VirtualTable
            data={data?.data || []}
            columns={data?.columns || []}
            height={400}
            loading={loading}
          />

          {/* Footer info */}
          <div style={{ marginTop: 16, textAlign: 'right' }}>
            <Space split={<span>•</span>}>
              <Text type="secondary">
                记录数: {data.total_count} | 执行时间: {data.execution_time?.toFixed(2)}秒
              </Text>
              {data.query_id && (
                <Text type="secondary" copyable>
                  查询ID: {data.query_id}
                </Text>
              )}
            </Space>
          </div>
        </>
      )}

      {!data && !loading && (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Text type="secondary">
            执行查询后结果将在此处显示
          </Text>
        </div>
      )}
    </Card>
  );
};

export default QueryResults;