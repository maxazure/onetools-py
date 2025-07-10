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
          {/* Statistics */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Statistic
                title="记录数"
                value={data.total_count}
                formatter={(value) => value?.toLocaleString()}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="列数"
                value={data.columns.length}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="执行时间"
                value={data.execution_time}
                suffix="秒"
                precision={2}
              />
            </Col>
          </Row>

          {/* Simple HTML Table */}
          <div style={{ 
            maxHeight: '400px', 
            overflow: 'auto', 
            border: '1px solid #d9d9d9',
            borderRadius: '6px'
          }}>
            {loading ? (
              <div style={{ textAlign: 'center', padding: '20px' }}>
                <Spin /> 加载中...
              </div>
            ) : data?.data && data.data.length > 0 ? (
              <table style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: '12px'
              }}>
                <thead>
                  <tr style={{ backgroundColor: '#fafafa' }}>
                    {data.columns.map((column, index) => (
                      <th key={index} style={{
                        padding: '8px 12px',
                        textAlign: 'left',
                        borderBottom: '1px solid #d9d9d9',
                        fontWeight: 600,
                        position: 'sticky',
                        top: 0,
                        backgroundColor: '#fafafa',
                        zIndex: 1
                      }}>
                        {column}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.data.map((row, rowIndex) => (
                    <tr key={rowIndex} style={{
                      backgroundColor: rowIndex % 2 === 0 ? '#ffffff' : '#fafafa'
                    }}>
                      {data.columns.map((column, colIndex) => (
                        <td key={colIndex} style={{
                          padding: '6px 12px',
                          borderBottom: '1px solid #f0f0f0',
                          maxWidth: '200px',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}>
                          {String(row[column] || '')}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Text type="secondary">暂无数据</Text>
              </div>
            )}
          </div>

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