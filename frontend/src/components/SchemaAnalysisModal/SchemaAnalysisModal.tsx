/**
 * Schema Analysis Modal Component
 * 显示SQL表结构分析结果
 */

import React, { useState } from 'react';
import { Modal, Typography, Button, Space, message, Divider, Tag, Card, Spin } from 'antd';
import { CopyOutlined, DatabaseOutlined, TableOutlined } from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

interface SchemaAnalysisData {
  sql: string;
  server_name?: string;
  tables_found: string[];
  create_statements: string;
  table_count: number;
}

interface SchemaAnalysisModalProps {
  visible: boolean;
  data: SchemaAnalysisData | null;
  loading: boolean;
  onClose: () => void;
}

const SchemaAnalysisModal: React.FC<SchemaAnalysisModalProps> = ({
  visible,
  data,
  loading,
  onClose,
}) => {
  const [copying, setCopying] = useState(false);

  const handleCopyToClipboard = async () => {
    if (!data?.create_statements) {
      message.warning('没有可复制的内容');
      return;
    }

    setCopying(true);
    try {
      await navigator.clipboard.writeText(data.create_statements);
      message.success('表结构已复制到剪切板');
    } catch (error) {
      console.error('复制失败:', error);
      message.error('复制失败，请手动复制');
    } finally {
      setCopying(false);
    }
  };

  const renderAnalysisResult = () => {
    if (loading) {
      return (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text>正在分析SQL语句中的表结构...</Text>
          </div>
        </div>
      );
    }

    if (!data) {
      return (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Text type="secondary">暂无分析结果</Text>
        </div>
      );
    }

    return (
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* 分析摘要 */}
        <Card size="small" title={<><DatabaseOutlined /> 分析摘要</>}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text strong>SQL语句: </Text>
              <Text code style={{ wordBreak: 'break-all' }}>
                {data.sql.length > 100 ? `${data.sql.substring(0, 100)}...` : data.sql}
              </Text>
            </div>
            
            {data.server_name && (
              <div>
                <Text strong>数据库服务器: </Text>
                <Tag color="blue">{data.server_name}</Tag>
              </div>
            )}
            
            <div>
              <Text strong>发现数据库对象: </Text>
              <Tag color="green">{data.table_count} 个</Tag>
            </div>
          </Space>
        </Card>

        {/* 发现的表列表 */}
        {data.tables_found && data.tables_found.length > 0 && (
          <Card size="small" title={<><TableOutlined /> 发现的表和视图</>}>
            <Space wrap>
              {data.tables_found.map((tableName, index) => (
                <Tag key={index} color="processing">
                  {tableName}
                </Tag>
              ))}
            </Space>
          </Card>
        )}

        {/* CREATE语句 */}
        <Card 
          size="small" 
          title="表结构定义 (CREATE语句)"
          extra={
            <Button
              type="primary"
              icon={<CopyOutlined />}
              onClick={handleCopyToClipboard}
              loading={copying}
              size="small"
            >
              复制到剪切板
            </Button>
          }
        >
          <div style={{ maxHeight: '400px', overflow: 'auto' }}>
            <pre style={{ 
              backgroundColor: '#f5f5f5', 
              padding: '16px', 
              borderRadius: '6px',
              fontSize: '13px',
              lineHeight: '1.4',
              margin: 0,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word'
            }}>
              {data.create_statements}
            </pre>
          </div>
        </Card>

        {/* 使用说明 */}
        <Card size="small" title="💡 使用说明" style={{ backgroundColor: '#f8f9fa' }}>
          <Space direction="vertical" size="small">
            <Text>
              • 上述CREATE语句包含了SQL中引用的所有表和视图的结构定义
            </Text>
            <Text>
              • 如果包含视图，会递归分析视图中依赖的表结构
            </Text>
            <Text>
              • 可以将这些定义复制给LLM（如ChatGPT、Claude等）进行数据库结构分析
            </Text>
            <Text>
              • 结构定义包含了列名、数据类型、约束等完整信息
            </Text>
          </Space>
        </Card>
      </Space>
    );
  };

  return (
    <Modal
      title={
        <Space>
          <DatabaseOutlined />
          SQL表结构分析结果
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={800}
      footer={[
        <Button key="close" onClick={onClose}>
          关闭
        </Button>,
        data && !loading && (
          <Button
            key="copy"
            type="primary"
            icon={<CopyOutlined />}
            onClick={handleCopyToClipboard}
            loading={copying}
          >
            复制CREATE语句
          </Button>
        ),
      ].filter(Boolean)}
      style={{ top: 20 }}
      styles={{
        body: { 
          maxHeight: '70vh', 
          overflow: 'auto',
          padding: '20px'
        }
      }}
    >
      {renderAnalysisResult()}
    </Modal>
  );
};

export default SchemaAnalysisModal;