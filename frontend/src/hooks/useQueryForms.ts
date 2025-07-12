/**
 * Custom hook for query forms management
 */

import { useQuery } from '@tanstack/react-query';
import { queryFormApi } from '../services/query-forms/query-form-api';
import { QueryFormResponse } from '../types/query-forms';

export const useQueryForms = () => {
  const {
    data: queryFormsResponse,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['query-forms-list'],
    queryFn: () => queryFormApi.getAllForms(true), // 只获取激活的表单
    refetchInterval: 10 * 60 * 1000, // 每10分钟刷新一次
    retry: 1,
  });

  const queryForms = queryFormsResponse?.success
    ? (queryFormsResponse.data as QueryFormResponse[])
        .filter(form => form.is_active)
        .sort((a, b) => a.form_name.localeCompare(b.form_name))
    : [];

  return {
    queryForms,
    isLoading,
    error,
    refetch,
    hasData: !!queryFormsResponse?.success
  };
};