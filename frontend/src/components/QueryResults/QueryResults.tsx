/**
 * Query Results Component
 */

import React, { useState, useMemo } from 'react';
import {
  Table,
  Card,
  Space,
  Button,
  Pagination,
  Typography,
  Alert,
  Spin,
  Statistic,
  Row,
  Col,
  Tooltip,
  message,
} from 'antd';
import {
  DownloadOutlined,
  CopyOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { QueryResult } from '../../types/api';

const { Title, Text } = Typography;

interface QueryResultsProps {
  data?: QueryResult | null;
  loading?: boolean;
  error?: string | null;
  onExport?: (format: 'csv' | 'excel') => void;
  onRefresh?: () => void;
  pagination?: {
    current: number;
    pageSize: number;
    total: number;
    onChange: (page: number, pageSize: number) => void;
  };
}

const QueryResults: React.FC<QueryResultsProps> = ({
  data,
  loading = false,
  error = null,
  onExport,
  onRefresh,
  pagination,
}) => {
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  // Generate table columns from data
  const columns: ColumnsType<any> = useMemo(() => {
    if (!data?.columns) return [];

    return data.columns.map((column) => ({
      title: column,
      dataIndex: column,
      key: column,
      width: 150,
      ellipsis: {
        showTitle: false,
      },
      render: (value: any) => (
        <Tooltip title={String(value)} placement="topLeft">
          <span>{String(value)}</span>
        </Tooltip>
      ),
      sorter: (a: any, b: any) => {
        const aVal = String(a[column] || '');
        const bVal = String(b[column] || '');
        return aVal.localeCompare(bVal);
      },
    }));
  }, [data?.columns]);

  // Add row keys to data
  const tableData = useMemo(() => {
    if (!data?.data) return [];
    return data.data.map((row, index) => ({
      ...row,
      key: index,
    }));
  }, [data?.data]);

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

  const handleSelectChange = (newSelectedRowKeys: React.Key[]) => {
    setSelectedRowKeys(newSelectedRowKeys);
  };

  const rowSelection = {
    selectedRowKeys,
    onChange: handleSelectChange,
    getCheckboxProps: (record: any) => ({
      disabled: false,
    }),
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
            <Col span={6}>
              <Statistic
                title="记录数"
                value={data.total_count}
                formatter={(value) => value?.toLocaleString()}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="列数"
                value={data.columns.length}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="执行时间"
                value={data.execution_time}
                suffix="秒"
                precision={2}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="已选择"
                value={selectedRowKeys.length}
              />
            </Col>
          </Row>

          {/* Table */}
          <Table
            columns={columns}
            dataSource={tableData}
            rowSelection={rowSelection}
            loading={loading}
            scroll={{ x: 'max-content', y: 400 }}
            size="small"
            pagination={
              pagination
                ? {
                    current: pagination.current,
                    pageSize: pagination.pageSize,
                    total: pagination.total,
                    onChange: pagination.onChange,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total, range) =>
                      `${range[0]}-${range[1]} of ${total} items`,
                    pageSizeOptions: ['10', '20', '50', '100'],
                  }
                : false
            }
            locale={{
              emptyText: loading ? '加载中...' : '暂无数据',
            }}
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