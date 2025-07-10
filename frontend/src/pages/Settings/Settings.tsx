/**
 * 系统设置页面 - 基于原有OneTools结构
 */

import React from 'react';
import { Typography, Space } from 'antd';
import { 
  SettingOutlined, 
  KeyOutlined
} from '@ant-design/icons';
import SystemSettingsManagement from './components/SystemSettingsManagement';

const { Title, Text } = Typography;

const Settings: React.FC = () => {
  return (
    <div>
      <Title level={2}>
        <Space>
          <SettingOutlined />
          系统设置
        </Space>
      </Title>
      <Text type="secondary">
        配置系统各项参数和功能设置。管理系统运行时的关键配置参数。
      </Text>
      
      <div style={{ marginTop: 24 }}>
        <SystemSettingsManagement />
      </div>
    </div>
  );
};

export default Settings;