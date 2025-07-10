/**
 * 查询结果表格组件
 */

import React, { useState, useMemo } from 'react';
import {
  Table,
  Button,
  Space,
  Input,
  Select,
  Tooltip,
  message,
  Typography,
  Tag,
} from 'antd';
import {
  DownloadOutlined,
  SearchOutlined,
  FilterOutlined,
  FullscreenOutlined,
  CopyOutlined,
} from '@ant-design/icons';
import type { ColumnsType, TableProps } from 'antd/es/table';

const { Search } = Input;
const { Option } = Select;
const { Text } = Typography;

interface QueryResultTableProps {
  data: Record<string, any>[];
  columns: string[];
  total: number;
  loading?: boolean;
  pagination?: TableProps<any>['pagination'];
  onExport?: (format: string) => void;
  maxHeight?: number;
}

const QueryResultTable: React.FC<QueryResultTableProps> = ({
  data,
  columns,
  total,
  loading = false,
  pagination = { pageSize: 50, showSizeChanger: true, showQuickJumper: true },
  onExport,
  maxHeight = 600,
}) => {
  const [searchText, setSearchText] = useState('');
  const [filteredData, setFilteredData] = useState(data);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  // 生成表格列配置
  const tableColumns: ColumnsType<Record<string, any>> = useMemo(() => {
    return columns.map((column, index) => ({
      title: column,
      dataIndex: column,
      key: column,
      width: Math.max(120, column.length * 12),
      ellipsis: {
        showTitle: false,
      },
      render: (value: any) => {
        if (value === null || value === undefined) {
          return <Text type="secondary">NULL</Text>;
        }
        
        const stringValue = String(value);
        
        // 处理长文本
        if (stringValue.length > 100) {
          return (
            <Tooltip title={stringValue} placement="topLeft">
              <Text copyable={{ text: stringValue }}>
                {stringValue.substring(0, 100)}...
              </Text>
            </Tooltip>
          );
        }
        
        // 处理特殊数据类型
        if (typeof value === 'boolean') {
          return <Tag color={value ? 'green' : 'red'}>{value ? 'TRUE' : 'FALSE'}</Tag>;
        }
        
        if (typeof value === 'number') {
          return <Text copyable>{value.toLocaleString()}</Text>;
        }
        
        // 检测是否为日期
        if (stringValue.match(/^\d{4}-\d{2}-\d{2}/) && stringValue.length >= 10) {
          return (
            <Tooltip title={stringValue}>
              <Text copyable>{stringValue}</Text>
            </Tooltip>
          );
        }
        
        return (
          <Tooltip title={stringValue.length > 50 ? stringValue : null}>
            <Text copyable>{stringValue}</Text>
          </Tooltip>
        );
      },
      sorter: (a: any, b: any) => {
        const aVal = a[column];
        const bVal = b[column];
        
        if (aVal === null || aVal === undefined) return -1;
        if (bVal === null || bVal === undefined) return 1;
        
        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return aVal - bVal;
        }
        
        return String(aVal).localeCompare(String(bVal));
      },
      filterable: true,
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder={`搜索 ${column}`}
            value={selectedKeys[0]}
            onChange={(e) => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            style={{ marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button
              type="primary"
              onClick={() => confirm()}
              icon={<SearchOutlined />}
              size="small"
            >
              搜索
            </Button>
            <Button
              onClick={() => clearFilters?.()}
              size="small"
            >
              重置
            </Button>
          </Space>
        </div>
      ),
      filterIcon: (filtered: boolean) => (
        <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />
      ),
      onFilter: (value, record) => {
        const recordValue = record[column];
        if (recordValue === null || recordValue === undefined) {
          return false;
        }
        return String(recordValue)
          .toLowerCase()
          .includes(String(value).toLowerCase());
      },
    }));
  }, [columns]);

  // 全局搜索
  const handleSearch = (value: string) => {
    setSearchText(value);
    if (!value) {
      setFilteredData(data);
      return;
    }

    const filtered = data.filter((record) =>
      Object.values(record).some((fieldValue) => {
        if (fieldValue === null || fieldValue === undefined) {
          return false;
        }
        return String(fieldValue).toLowerCase().includes(value.toLowerCase());
      })
    );
    
    setFilteredData(filtered);
  };

  // 导出数据
  const handleExport = (format: string) => {
    if (onExport) {
      onExport(format);
    } else {
      // 默认导出逻辑
      const exportData = selectedRowKeys.length > 0 
        ? data.filter((_, index) => selectedRowKeys.includes(index))
        : filteredData;
      
      if (format === 'csv') {
        exportToCSV(exportData, columns);
      } else if (format === 'json') {
        exportToJSON(exportData);
      }
    }
  };

  // 导出为CSV
  const exportToCSV = (exportData: Record<string, any>[], exportColumns: string[]) => {
    const csvContent = [
      exportColumns.join(','),
      ...exportData.map(row => 
        exportColumns.map(col => {
          const value = row[col];
          if (value === null || value === undefined) return '';
          const stringValue = String(value);
          // 转义CSV特殊字符
          if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
            return `"${stringValue.replace(/"/g, '""')}"`;
          }
          return stringValue;
        }).join(',')
      )
    ].join('\n');

    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `query_result_${new Date().getTime()}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    message.success('CSV文件导出成功');
  };

  // 导出为JSON
  const exportToJSON = (exportData: Record<string, any>[]) => {
    const jsonContent = JSON.stringify(exportData, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `query_result_${new Date().getTime()}.json`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    message.success('JSON文件导出成功');
  };

  // 复制选中数据
  const handleCopySelected = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要复制的行');
      return;
    }

    const selectedData = data.filter((_, index) => selectedRowKeys.includes(index));
    const textContent = selectedData.map(row => 
      columns.map(col => row[col] || '').join('\t')
    ).join('\n');

    navigator.clipboard.writeText(textContent).then(() => {
      message.success(`已复制${selectedRowKeys.length}行数据到剪贴板`);
    }).catch(() => {
      message.error('复制失败');
    });
  };

  // 行选择配置
  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys: React.Key[]) => {
      setSelectedRowKeys(newSelectedRowKeys);
    },
    onSelectAll: (selected: boolean, selectedRows: any[], changeRows: any[]) => {
      if (selected) {
        setSelectedRowKeys(filteredData.map((_, index) => index));
      } else {
        setSelectedRowKeys([]);
      }
    },
  };

  return (
    <div className="query-result-table">
      {/* 工具栏 */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <Search
            placeholder="全局搜索..."
            allowClear
            onSearch={handleSearch}
            style={{ width: 300 }}
          />
          <Text type="secondary">
            显示 {filteredData.length} / {total} 条记录
          </Text>
          {selectedRowKeys.length > 0 && (
            <Text type="secondary">
              已选择 {selectedRowKeys.length} 行
            </Text>
          )}
        </Space>
        
        <Space>
          {selectedRowKeys.length > 0 && (
            <Button
              icon={<CopyOutlined />}
              onClick={handleCopySelected}
            >
              复制选中
            </Button>
          )}
          
          <Select
            placeholder="导出格式"
            style={{ width: 120 }}
            onSelect={handleExport}
          >
            <Option value="csv">CSV</Option>
            <Option value="json">JSON</Option>
          </Select>
          
          <Button
            icon={<FullscreenOutlined />}
            onClick={() => {
              // 全屏显示功能
              message.info('全屏功能待实现');
            }}
          >
            全屏
          </Button>
        </Space>
      </div>

      {/* 数据表格 */}
      <Table
        columns={tableColumns}
        dataSource={filteredData}
        rowKey={(record, index) => index || 0}
        loading={loading}
        pagination={{
          ...pagination,
          total: filteredData.length,
          showTotal: (total, range) => 
            `第 ${range[0]}-${range[1]} 条，共 ${total} 条记录`,
        }}
        rowSelection={rowSelection}
        scroll={{ 
          x: columns.length * 150,
          y: maxHeight,
        }}
        size="small"
        bordered
        sticky
      />
    </div>
  );
};

export default QueryResultTable;