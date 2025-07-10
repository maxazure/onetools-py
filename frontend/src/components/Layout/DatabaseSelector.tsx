import React, { useState, useEffect } from 'react';
import { Select, message } from 'antd';
import { DatabaseOutlined } from '@ant-design/icons';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { settingsApi, apiService } from '../../services/api';

interface DatabaseServer {
  id?: number;
  name: string;
  order: number;
  created_at?: string;
  updated_at?: string;
}

interface ServerDropdownOption {
  value: string;
  label: string;
  enabled: boolean;
}

interface ServerDropdownData {
  servers: ServerDropdownOption[];
  current_server: string | null;
}

interface DatabaseSelectorProps {
  onServerChange?: (serverName: string) => void;
  currentServer?: string;
}

const DatabaseSelector: React.FC<DatabaseSelectorProps> = ({ 
  onServerChange, 
  currentServer 
}) => {
  const [selectedServer, setSelectedServer] = useState<string>('');
  const queryClient = useQueryClient();

  // Fetch server dropdown data (servers + current selection)
  const { data: serverDropdownData, isLoading, error } = useQuery<ServerDropdownData>({
    queryKey: ['server-dropdown'],
    queryFn: async () => {
      try {
        const response = await apiService.getServerDropdown();
        return response.data;
      } catch (error) {
        console.error('Failed to fetch server dropdown data:', error);
        return { servers: [], current_server: null };
      }
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  // Set server selection on load
  useEffect(() => {
    if (serverDropdownData?.current_server) {
      // Use saved server selection
      setSelectedServer(serverDropdownData.current_server);
      onServerChange?.(serverDropdownData.current_server);
    } else if (serverDropdownData?.servers && serverDropdownData.servers.length > 0 && !selectedServer) {
      // Use first enabled server if no saved selection
      const firstEnabledServer = serverDropdownData.servers.find(s => s.enabled) || serverDropdownData.servers[0];
      setSelectedServer(firstEnabledServer.value);
      onServerChange?.(firstEnabledServer.value);
    }
  }, [serverDropdownData, selectedServer, onServerChange]);

  // Update selected server when currentServer prop changes
  useEffect(() => {
    if (currentServer && currentServer !== selectedServer) {
      setSelectedServer(currentServer);
    }
  }, [currentServer, selectedServer]);

  const handleServerChange = async (newServerName: string) => {
    if (newServerName === selectedServer) return;

    try {
      // 检查服务器是否已存在于列表中
      const serverExists = serverDropdownData?.servers?.some(server => server.value === newServerName);
      
      // 如果服务器不存在，自动创建一个数据库服务器条目
      if (!serverExists) {
        try {
          await settingsApi.createDatabaseServer({
            name: newServerName,
            order: (serverDropdownData?.servers?.length || 0) + 1
          });
          
          // 刷新服务器下拉框数据
          queryClient.invalidateQueries({ queryKey: ['server-dropdown'] });
          
          console.log(`自动创建数据库服务器: ${newServerName}`);
        } catch (createError) {
          console.warn(`创建数据库服务器失败，但继续保存选择: ${newServerName}`, createError);
          // 即使创建失败，也继续保存选择
        }
      }

      // Save server selection to API
      await apiService.setCurrentServerSelection(newServerName);
      
      setSelectedServer(newServerName);
      onServerChange?.(newServerName);
      
      // 刷新服务器下拉框数据
      queryClient.invalidateQueries({ queryKey: ['server-dropdown'] });
      
      message.success(`已选择数据库服务器: ${newServerName}`);
    } catch (error: any) {
      message.error(`保存服务器选择失败: ${error.message || '未知错误'}`);
      console.error('Failed to save server selection:', error);
    }
  };

  if (error) {
    return (
      <div style={{ color: '#ff4d4f', fontSize: '12px' }}>
        数据库服务器加载失败
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <DatabaseOutlined style={{ color: '#fff', fontSize: '16px' }} />
      <Select
        style={{ 
          minWidth: 180,
          color: '#fff'
        }}
        value={selectedServer}
        onChange={handleServerChange}
        loading={isLoading}
        placeholder="选择数据库服务器"
        showSearch
        allowClear={false}
        filterOption={(input, option) =>
          (option?.value as string)?.toLowerCase().includes(input.toLowerCase())
        }
        classNames={{
          popup: { root: 'database-selector-dropdown' }
        }}
        options={(() => {
          const serverOptions: { value: string; label: React.ReactNode; disabled?: boolean }[] = 
            serverDropdownData?.servers?.map(server => ({
              value: server.value,
              label: server.label,
              disabled: !server.enabled
            })) || [];

          // 如果当前选择的服务器不在列表中，添加它
          if (selectedServer && !serverOptions.some(opt => opt.value === selectedServer)) {
            serverOptions.unshift({
              value: selectedServer,
              label: (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span>{selectedServer}</span>
                  <span style={{ fontSize: '12px', color: 'orange' }}>当前</span>
                </div>
              )
            });
          }

          return serverOptions;
        })()}
      />
    </div>
  );
};

export default DatabaseSelector;