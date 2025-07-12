/**
 * Main Application Layout - SQL查询管理器界面
 */

import React, { useState, useEffect } from 'react';
import {
  Layout,
  Menu,
  Button,
  Space,
  Typography,
  Tooltip,
  message,
  theme,
  Badge,
  Divider,
} from 'antd';
import {
  DatabaseOutlined,
  CodeOutlined,
  HistoryOutlined,
  SettingOutlined,
  UserOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
  InfoCircleOutlined,
  ThunderboltOutlined,
  MenuOutlined,
  BookOutlined,
  BarChartOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  MinusCircleOutlined,
  LoadingOutlined,
  SaveOutlined,
  FolderOpenOutlined,
  MenuUnfoldOutlined as MenuIcon,
  FormOutlined
} from '@ant-design/icons';
import * as Icons from '@ant-design/icons';
import { useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../../services/api';
import { MenuConfiguration } from '../../types/api';
import { useMenuConfig } from '../../hooks/useMenuConfig';
import { useQueryForms } from '../../hooks/useQueryForms';
import DatabaseSelector from './DatabaseSelector';
import { useDatabaseContext } from '../../contexts/DatabaseContext';

const { Header, Content, Sider } = Layout;
const { Title, Text } = Typography;

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { token } = theme.useToken();
  const { currentServer, switchServer } = useDatabaseContext();


  // 移除自动健康检查 - 不对SQL Server进行自动查询
  // const { data: healthCheck } = useQuery({
  //   queryKey: ['health-check'],
  //   queryFn: () => apiService.healthCheck(),
  //   refetchInterval: 60000, // Refetch every minute
  //   retry: 1,
  // });

  // Load menu configuration from API
  const { menuItems: apiMenuItems, isLoading: menuLoading, hasData } = useMenuConfig();
  
  // Load query forms for dynamic menu
  const { queryForms, isLoading: formsLoading } = useQueryForms();

  // Get icon component by name
  const getIconComponent = (iconName: string) => {
    const IconComponent = (Icons as any)[iconName];
    return IconComponent ? React.createElement(IconComponent) : React.createElement(MenuOutlined);
  };

  // Process menu configuration from API
  const getMenuConfiguration = () => {
    // Fallback menu configuration if API is not available
    const fallbackConfig = [
      {
        section: 'main',
        title: '功能菜单',
        items: [
          {
            key: '/custom-query',
            label: '自定义查询',
            icon: <CodeOutlined />,
            path: '/custom-query'
          },
          {
            key: '/query-history',
            label: '查询历史',
            icon: <HistoryOutlined />,
            path: '/query-history'
          },
          {
            key: '/saved-queries',
            label: '保存的查询',
            icon: <SaveOutlined />,
            path: '/saved-queries'
          },
          {
            key: '/query-stats',
            label: '查询统计',
            icon: <BarChartOutlined />,
            path: '/query-stats'
          }
        ]
      },
      {
        section: 'system',
        title: '系统菜单',
        items: [
          {
            key: '/database-config',
            label: '数据库配置',
            icon: <DatabaseOutlined />,
            path: '/database-config'
          },
          {
            key: '/menu-config',
            label: '菜单配置',
            icon: <MenuIcon />,
            path: '/menu-config'
          },
          {
            key: '/settings',
            label: '系统设置',
            icon: <SettingOutlined />,
            path: '/settings'
          },
          {
            key: '/about',
            label: '关于',
            icon: <InfoCircleOutlined />,
            path: '/about'
          }
        ]
      }
    ];

    // If API data is not available, return fallback
    if (!hasData || apiMenuItems.length === 0) {
      return fallbackConfig;
    }

    // Group by section
    const sections = apiMenuItems.reduce((acc: Record<string, any>, item: MenuConfiguration) => {
      if (!acc[item.section]) {
        acc[item.section] = {
          section: item.section,
          title: item.section === 'main' ? '功能菜单' : '系统菜单',
          items: []
        };
      }
      acc[item.section].items.push({
        key: item.path,
        label: item.label,
        icon: getIconComponent(item.icon),
        path: item.path
      });
      return acc;
    }, {} as Record<string, any>);

    return Object.values(sections);
  };

  // Add dynamic forms menu section
  const addDynamicFormsSection = (menuSections: any[]) => {
    if (queryForms.length === 0) return menuSections;
    
    const formsSection = {
      section: 'forms',
      title: '查询表单',
      items: queryForms.map(form => ({
        key: `/query-forms/${form.id}/execute`,
        label: form.form_name,
        icon: React.createElement(FormOutlined),
        path: `/query-forms/${form.id}/execute`,
        description: form.form_description
      }))
    };
    
    // Insert forms section after main section (index 1)
    const result = [...menuSections];
    result.splice(1, 0, formsSection);
    return result;
  };

  const baseMenuConfig = getMenuConfiguration();
  const menuConfig = addDynamicFormsSection(baseMenuConfig);

  // Create menu items for Ant Design Menu
  const createMenuItems = () => {
    const menuItems: any[] = [];
    
    menuConfig.forEach((section, index) => {
      // Add section items
      section.items.forEach((item: any) => {
        menuItems.push({
          key: item.key,
          icon: item.icon,
          label: item.label,
          onClick: () => navigate(item.path)
        });
      });
      
      // Add divider between sections (except for the last section)
      if (index < menuConfig.length - 1) {
        menuItems.push({
          type: 'divider' as const,
          key: `divider-${index}`
        });
      }
    });
    
    return menuItems;
  };


  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const handleDatabaseServerChange = (serverName: string) => {
    switchServer(serverName);
  };


  const toggleCollapsed = () => {
    setCollapsed(!collapsed);
  };


  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* Header - Fixed at top like original */}
      <Header 
        style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          background: '#001529',
          padding: '0 24px',
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 1000,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={toggleCollapsed}
            style={{ 
              fontSize: '18px', 
              color: '#fff',
              marginRight: '16px'
            }}
          />
          <Title 
            level={3} 
            style={{ 
              color: '#fff', 
              margin: 0,
              fontWeight: 'bold'
            }}
          >
            OneTools v1.0
          </Title>
        </div>
        
        {/* Database Selector with Status in Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <Text style={{ color: '#fff', fontSize: '14px' }}>当前服务器:</Text>
          <DatabaseSelector 
            onServerChange={handleDatabaseServerChange}
            currentServer={currentServer}
          />
        </div>
      </Header>

      <Layout style={{ marginTop: 64 }}>
        {/* Sidebar - Fixed position like original */}
        <Sider 
          trigger={null}
          collapsible
          collapsed={collapsed}
          style={{
            background: '#fff',
            boxShadow: '2px 0 8px rgba(0,0,0,0.1)',
            position: 'fixed',
            left: 0,
            top: 64,
            bottom: 0,
            zIndex: 999,
            overflow: 'auto'
          }}
          width={200}
        >
          {/* Menu sections with custom layout */}
          <div style={{ padding: '16px 0' }}>
            {menuConfig.map((section, index) => (
              <div key={section.section} style={{ marginBottom: index < menuConfig.length - 1 ? '20px' : 0 }}>
                <div style={{ 
                  padding: '0 24px 8px 24px', 
                  fontSize: '12px', 
                  fontWeight: 'bold',
                  color: '#8c8c8c',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px'
                }}>
                  {section.title}
                </div>
                <Menu
                  mode="inline"
                  selectedKeys={[location.pathname]}
                  style={{
                    borderRight: 0,
                    background: 'transparent'
                  }}
                  items={section.items.map((item: any) => ({
                    key: item.key,
                    icon: item.icon,
                    label: item.label,
                    onClick: () => navigate(item.path),
                    style: {
                      margin: '4px 8px',
                      borderRadius: '6px',
                      height: '40px',
                      lineHeight: '40px'
                    }
                  }))}
                />
                {index < menuConfig.length - 1 && (
                  <Divider style={{ margin: '16px 0', borderColor: '#f0f0f0' }} />
                )}
              </div>
            ))}
          </div>
        </Sider>

        {/* Main Content */}
        <Layout 
          style={{ 
            marginLeft: collapsed ? 80 : 200,
            transition: 'margin-left 0.2s'
          }}
        >
          <Content
            style={{
              padding: '24px',
              background: '#f0f2f5',
              minHeight: 'calc(100vh - 64px)'
            }}
          >
            <div
              style={{
                background: '#fff',
                padding: '24px',
                borderRadius: '8px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                minHeight: 'calc(100vh - 112px)'
              }}
            >
              {children}
            </div>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default MainLayout;