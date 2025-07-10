/**
 * Custom hook for menu configuration management
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../services/api';
import { MenuConfiguration } from '../types/api';

export const useMenuConfig = () => {
  const queryClient = useQueryClient();

  const {
    data: menuConfigResponse,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['menu-configuration'],
    queryFn: () => apiService.getMenuConfiguration(),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
    retry: 1,
  });

  const refreshMenuConfig = () => {
    queryClient.invalidateQueries({ queryKey: ['menu-configuration'] });
  };

  const menuItems = menuConfigResponse?.success
    ? (menuConfigResponse.data as MenuConfiguration[])
        .filter(item => item.enabled)
        .sort((a, b) => a.order - b.order)
    : [];

  return {
    menuItems,
    isLoading,
    error,
    refetch,
    refreshMenuConfig,
    hasData: !!menuConfigResponse?.success
  };
};