/**
 * Main Application Component
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider, App as AntApp } from 'antd';
import MainLayout from './components/Layout/MainLayout';
import CustomQuery from './pages/CustomQuery/CustomQuery';
import SavedQueries from './pages/SavedQueries/SavedQueries';
import Settings from './pages/Settings/Settings';
import MenuConfig from './pages/MenuConfig/MenuConfig';
import DatabaseConfig from './pages/DatabaseConfig/DatabaseConfig';
import QueryFormManagement from './pages/QueryForms/QueryFormManagement';
import QueryFormExecution from './pages/QueryForms/QueryFormExecution';
import { DatabaseProvider } from './contexts/DatabaseContext';
import './App.css';

// Create a query client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
    mutations: {
      retry: 1,
    },
  },
});

// Ant Design theme configuration
const antdTheme = {
  token: {
    colorPrimary: '#1890ff',
    borderRadius: 6,
    fontSize: 14,
  },
  components: {
    Layout: {
      siderBg: '#001529',
      triggerBg: '#002140',
    },
    Menu: {
      darkItemBg: '#001529',
      darkSubMenuItemBg: '#000c17',
    },
  },
};



const QueryHistory: React.FC = () => (
  <div style={{ padding: 24 }}>
    <h2>查询历史</h2>
    <p>查询执行历史功能开发中...</p>
  </div>
);

const QueryStats: React.FC = () => (
  <div style={{ padding: 24 }}>
    <h2>查询统计</h2>
    <p>查询性能统计功能开发中...</p>
  </div>
);



const About: React.FC = () => (
  <div style={{ padding: 24 }}>
    <h2>关于</h2>
    <h3>OneTools</h3>
    <p>一个功能强大的SQL查询管理工具，支持多数据库连接、查询历史记录、结果导出等功能。</p>
  </div>
);

// Settings component is now imported from ./pages/Settings/Settings

const Dashboard: React.FC = () => (
  <div style={{ padding: 24 }}>
    <h2>SQL查询管理器</h2>
    <p>欢迎使用 OneTools v1.0</p>
    <p>请从左侧菜单选择功能开始使用。</p>
  </div>
);

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider theme={antdTheme}>
        <AntApp>
          <DatabaseProvider>
            <Router>
              <MainLayout>
                <Routes>
                  {/* Default route - redirect to custom query */}
                  <Route path="/" element={<Navigate to="/custom-query" replace />} />
                  
                  {/* Main application routes */}
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/custom-query" element={<CustomQuery />} />
                  <Route path="/query-history" element={<QueryHistory />} />
                  <Route path="/saved-queries" element={<SavedQueries />} />
                  <Route path="/query-stats" element={<QueryStats />} />
                  <Route path="/database-config" element={<DatabaseConfig />} />
                  <Route path="/menu-config" element={<MenuConfig />} />
                  <Route path="/query-forms" element={<QueryFormManagement />} />
                  <Route path="/query-forms/:formId/execute" element={<QueryFormExecution />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="/about" element={<About />} />
                  
                  {/* Catch all route - redirect to custom query */}
                  <Route path="*" element={<Navigate to="/custom-query" replace />} />
                </Routes>
              </MainLayout>
            </Router>
          </DatabaseProvider>
        </AntApp>
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default App;
