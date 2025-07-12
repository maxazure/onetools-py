/**
 * 数据库配置页面 - 专门用于数据库服务器管理
 */

import React from 'react';
import { Typography, Card, Space, Divider } from 'antd';
import { DatabaseOutlined } from '@ant-design/icons';
import DatabaseServerManagement from './components/DatabaseServerManagement';

const { Title, Text } = Typography;

const DatabaseConfig: React.FC = () => {
  return (
    <div>
      <Title level={2}>
        <Space>
          <DatabaseOutlined />
          数据库配置
        </Space>
      </Title>
      <Text type="secondary">
        管理数据库服务器连接配置，这些配置存储在SQLite中用于工具管理，而SQL Server用于实际的数据查询和维护
      </Text>
      
      <div style={{ marginTop: 24 }}>
        <Card>
          <DatabaseServerManagement />
        </Card>
      </div>
    </div>
  );
};

export default DatabaseConfig;