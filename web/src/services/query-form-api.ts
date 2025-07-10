/**
 * 动态查询表单API服务
 */

import {
  QueryFormCreateRequest,
  QueryFormUpdateRequest,
  QueryFormResponse,
  QueryFormExecuteRequest,
  QueryFormHistory,
  SQLParseResult,
  DataSourceTestRequest,
  DataSourceTestResponse,
  QueryResponse,
  ApiResponse,
  FormPreviewData,
} from '../types/query-forms';

const API_BASE_URL = '/api/v1/query-forms';

class QueryFormApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  // 获取所有查询表单
  async getAllForms(activeOnly: boolean = true): Promise<ApiResponse<QueryFormResponse[]>> {
    return this.request<QueryFormResponse[]>(`/?active_only=${activeOnly}`);
  }

  // 根据ID获取查询表单
  async getFormById(formId: number): Promise<ApiResponse<QueryFormResponse>> {
    return this.request<QueryFormResponse>(`/${formId}`);
  }

  // 创建查询表单
  async createForm(formData: QueryFormCreateRequest): Promise<ApiResponse<QueryFormResponse>> {
    return this.request<QueryFormResponse>('/', {
      method: 'POST',
      body: JSON.stringify(formData),
    });
  }

  // 更新查询表单
  async updateForm(
    formId: number,
    formData: QueryFormUpdateRequest
  ): Promise<ApiResponse<QueryFormResponse>> {
    return this.request<QueryFormResponse>(`/${formId}`, {
      method: 'PUT',
      body: JSON.stringify(formData),
    });
  }

  // 删除查询表单
  async deleteForm(formId: number, softDelete: boolean = true): Promise<ApiResponse<void>> {
    return this.request<void>(`/${formId}?soft_delete=${softDelete}`, {
      method: 'DELETE',
    });
  }

  // 解析SQL模板
  async parseSQLTemplate(sqlTemplate: string): Promise<ApiResponse<SQLParseResult>> {
    return this.request<SQLParseResult>('/parse-sql', {
      method: 'POST',
      body: JSON.stringify({ sql_template: sqlTemplate }),
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
  }

  // 测试数据源
  async testDataSource(request: DataSourceTestRequest): Promise<ApiResponse<DataSourceTestResponse>> {
    return this.request<DataSourceTestResponse>('/test-data-source', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // 执行查询表单
  async executeForm(request: QueryFormExecuteRequest): Promise<ApiResponse<QueryResponse>> {
    return this.request<QueryResponse>('/execute', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // 获取查询表单执行历史
  async getFormHistory(
    formId?: number,
    limit: number = 100
  ): Promise<ApiResponse<QueryFormHistory[]>> {
    const params = new URLSearchParams();
    if (formId) params.append('form_id', formId.toString());
    params.append('limit', limit.toString());
    
    return this.request<QueryFormHistory[]>(`/history/?${params.toString()}`);
  }

  // 预览查询表单
  async previewForm(formId: number): Promise<ApiResponse<FormPreviewData>> {
    return this.request<FormPreviewData>(`/${formId}/preview`);
  }

  // 复制查询表单
  async duplicateForm(formId: number, newName: string): Promise<ApiResponse<QueryFormResponse>> {
    return this.request<QueryFormResponse>(`/${formId}/duplicate?new_name=${encodeURIComponent(newName)}`, {
      method: 'POST',
    });
  }

  // 切换查询表单状态
  async toggleFormStatus(formId: number): Promise<ApiResponse<{ is_active: boolean }>> {
    return this.request<{ is_active: boolean }>(`/${formId}/toggle-status`, {
      method: 'POST',
    });
  }

  // 批量操作
  async batchOperation(
    formIds: number[],
    operation: 'delete' | 'activate' | 'deactivate'
  ): Promise<ApiResponse<{ success_count: number; failed_count: number }>> {
    const promises = formIds.map(formId => {
      switch (operation) {
        case 'delete':
          return this.deleteForm(formId, true);
        case 'activate':
        case 'deactivate':
          return this.toggleFormStatus(formId);
        default:
          throw new Error(`Unknown operation: ${operation}`);
      }
    });

    const results = await Promise.allSettled(promises);
    const successCount = results.filter(r => r.status === 'fulfilled').length;
    const failedCount = results.filter(r => r.status === 'rejected').length;

    return {
      success: true,
      data: {
        success_count: successCount,
        failed_count: failedCount,
      },
      message: `批量操作完成: 成功${successCount}个，失败${failedCount}个`,
      timestamp: new Date().toISOString(),
    };
  }

  // 导出表单配置
  async exportFormConfig(formId: number): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/${formId}/export`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`Export failed: ${response.status}`);
    }

    return await response.blob();
  }

  // 导入表单配置
  async importFormConfig(file: File): Promise<ApiResponse<QueryFormResponse>> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/import`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Import failed: ${response.status}`);
    }

    return await response.json();
  }

  // 验证表单配置
  async validateFormConfig(formData: QueryFormCreateRequest): Promise<ApiResponse<{
    valid: boolean;
    errors: string[];
    warnings: string[];
  }>> {
    return this.request<{
      valid: boolean;
      errors: string[];
      warnings: string[];
    }>('/validate', {
      method: 'POST',
      body: JSON.stringify(formData),
    });
  }

  // 获取表单统计信息
  async getFormStats(formId: number): Promise<ApiResponse<{
    total_executions: number;
    success_rate: number;
    avg_execution_time: number;
    last_execution: string;
  }>> {
    return this.request<{
      total_executions: number;
      success_rate: number;
      avg_execution_time: number;
      last_execution: string;
    }>(`/${formId}/stats`);
  }
}

// 创建单例实例
export const queryFormApi = new QueryFormApiService();
export default queryFormApi;