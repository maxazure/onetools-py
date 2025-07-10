/**
 * API Service Layer
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { API_CONFIG } from '../config/api';
import {
  ApiResponse,
  PaginatedResponse,
  QueryRequest,
  CustomQueryRequest,
  DynamicQueryRequest,
  QueryResult,
  DatabaseSettings,
  ApiError,
} from '../types/api';

class ApiService {
  private client: AxiosInstance;
  private currentDatabaseServer: string = '';

  constructor() {
    this.client = axios.create({
      baseURL: API_CONFIG.BASE_URL,
      timeout: API_CONFIG.TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  // 创建专用于SQL执行的客户端，使用更长的超时时间
  private createSqlClient() {
    const sqlClient = axios.create({
      baseURL: API_CONFIG.BASE_URL,
      timeout: 120000, // 2分钟超时，适合复杂SQL查询
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 为SQL客户端添加相同的拦截器
    sqlClient.interceptors.request.use(
      (config) => {
        if (this.currentDatabaseServer) {
          config.headers['X-Database-Server'] = this.currentDatabaseServer;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    sqlClient.interceptors.response.use(
      (response) => response,
      (error) => {
        return Promise.reject(this.formatError(error));
      }
    );

    return sqlClient;
  }

  // Set current database server for API calls
  setDatabaseServer(serverName: string) {
    this.currentDatabaseServer = serverName;
  }

  // Get current database server
  getCurrentDatabaseServer(): string {
    return this.currentDatabaseServer;
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add database server header if set
        if (this.currentDatabaseServer) {
          config.headers['X-Database-Server'] = this.currentDatabaseServer;
        }

        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error) => {
        return Promise.reject(this.formatError(error));
      }
    );
  }

  private formatError(error: any): ApiError {
    if (error.response?.data) {
      return error.response.data;
    }
    
    return {
      error_code: 'NETWORK_ERROR',
      error_message: error.message || 'Network error occurred',
      timestamp: new Date().toISOString(),
    };
  }

  // Health check
  async healthCheck(): Promise<ApiResponse> {
    const response = await this.client.get(API_CONFIG.ENDPOINTS.HEALTH);
    return response.data;
  }

  // User queries - 使用专用SQL客户端，禁用重试
  async executeUserQuery(request: QueryRequest): Promise<PaginatedResponse<QueryResult>> {
    const sqlClient = this.createSqlClient();
    const response = await sqlClient.post(API_CONFIG.ENDPOINTS.USER_QUERY, request);
    return response.data;
  }

  // Custom queries - 使用专用SQL客户端，禁用重试
  async executeCustomQuery(request: CustomQueryRequest): Promise<ApiResponse<any>> {
    const sqlClient = this.createSqlClient();
    const response = await sqlClient.post('/api/v1/custom/execute', request);
    return response.data;
  }

  async validateCustomQuery(sql: string): Promise<ApiResponse<any>> {
    const response = await this.client.post('/api/v1/custom/validate', { sql });
    return response.data;
  }

  async getCustomQueryParameters(): Promise<ApiResponse<any>> {
    const response = await this.client.get('/api/v1/custom/parameters');
    return response.data;
  }

  // Dynamic queries - 使用专用SQL客户端，禁用重试
  async executeDynamicQuery(request: DynamicQueryRequest): Promise<PaginatedResponse<QueryResult>> {
    const sqlClient = this.createSqlClient();
    const response = await sqlClient.post(API_CONFIG.ENDPOINTS.DYNAMIC_QUERY, request);
    return response.data;
  }

  // Database management
  async testConnection(config: any): Promise<ApiResponse<boolean>> {
    const response = await this.client.post(`${API_CONFIG.ENDPOINTS.DATABASE}/test-connection`, config);
    return response.data;
  }

  async getConnectionStatus(): Promise<ApiResponse<any>> {
    const response = await this.client.get(`${API_CONFIG.ENDPOINTS.DATABASE}/connection-status`);
    return response.data;
  }

  // Server selection persistence
  async getCurrentServerSelection(): Promise<ApiResponse<{ server_name: string }>> {
    const response = await this.client.get(`${API_CONFIG.ENDPOINTS.SETTINGS}/current-server`);
    return response.data;
  }

  async setCurrentServerSelection(serverName: string): Promise<ApiResponse> {
    const response = await this.client.post(`${API_CONFIG.ENDPOINTS.SETTINGS}/current-server`, { server_name: serverName });
    return response.data;
  }

  // Server dropdown - combined endpoint for servers and current selection
  async getServerDropdown(): Promise<ApiResponse<{
    servers: Array<{value: string, label: string, enabled: boolean}>,
    current_server: string | null
  }>> {
    const response = await this.client.get(`${API_CONFIG.ENDPOINTS.SETTINGS}/server-dropdown`);
    return response.data;
  }

  // Database servers
  async getDatabaseServers(): Promise<ApiResponse<any[]>> {
    const response = await this.client.get(`${API_CONFIG.ENDPOINTS.DATABASE}/servers`);
    return response.data;
  }


  // Settings
  async getDatabaseSettings(): Promise<ApiResponse<DatabaseSettings>> {
    const response = await this.client.get(`${API_CONFIG.ENDPOINTS.SETTINGS}/database`);
    return response.data;
  }

  async updateDatabaseSettings(settings: DatabaseSettings): Promise<ApiResponse> {
    const response = await this.client.put(`${API_CONFIG.ENDPOINTS.SETTINGS}/database`, settings);
    return response.data;
  }

  // Export functionality
  async exportQueryResults(queryId: string, format: 'csv' | 'excel'): Promise<Blob> {
    const response = await this.client.get(
      `${API_CONFIG.ENDPOINTS.CUSTOM_QUERY}/${queryId}/export`,
      {
        params: { format },
        responseType: 'blob',
      }
    );
    return response.data;
  }

  // Query history
  async getQueryHistory(page = 1, pageSize: number = API_CONFIG.DEFAULT_PAGE_SIZE): Promise<PaginatedResponse> {
    const response = await this.client.get('/api/v1/query-history', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  }

  async clearQueryHistory(): Promise<ApiResponse> {
    const response = await this.client.post('/api/v1/query-history/clear');
    return response.data;
  }

  async getSavedQueries(): Promise<ApiResponse> {
    const response = await this.client.get('/api/v1/query-history/saved');
    return response.data;
  }

  async saveQuery(query: string, name: string, description?: string): Promise<ApiResponse> {
    const response = await this.client.post('/api/v1/query-history/saved', {
      sql: query,
      name: name,
      description: description || '',
      query_type: 'custom',
      params: {},
      is_public: false,
      tags: [],
      is_favorite: false,
      user_id: 'system'
    });
    return response.data;
  }

  async getSavedQuery(queryId: number): Promise<ApiResponse> {
    const response = await this.client.get(`/api/v1/query-history/saved/${queryId}`);
    return response.data;
  }

  async updateSavedQuery(queryId: number, query: string, name: string): Promise<ApiResponse> {
    const response = await this.client.put(`/api/v1/query-history/saved/${queryId}`, {
      sql: query,
      name: name,
      query_type: 'custom',
    });
    return response.data;
  }

  async deleteSavedQuery(queryId: number): Promise<ApiResponse> {
    const response = await this.client.delete(`/api/v1/query-history/saved/${queryId}`);
    return response.data;
  }

  async getQueryStats(): Promise<ApiResponse> {
    const response = await this.client.get('/api/v1/query-history/stats');
    return response.data;
  }

  // Settings API
  async getSystemSettings(): Promise<ApiResponse> {
    const response = await this.client.get(`${API_CONFIG.ENDPOINTS.SETTINGS}`);
    return response.data;
  }

  async updateSystemSettings(settings: any): Promise<ApiResponse> {
    const response = await this.client.put(`${API_CONFIG.ENDPOINTS.SETTINGS}`, settings);
    return response.data;
  }

  async getSettingsDatabaseServers(): Promise<ApiResponse> {
    const response = await this.client.get(`${API_CONFIG.ENDPOINTS.SETTINGS}/database-servers`);
    return response.data;
  }

  async createDatabaseServer(server: any): Promise<ApiResponse> {
    const response = await this.client.post(`${API_CONFIG.ENDPOINTS.SETTINGS}/database-servers`, server);
    return response.data;
  }

  async updateDatabaseServer(serverId: number, server: any): Promise<ApiResponse> {
    const response = await this.client.put(`${API_CONFIG.ENDPOINTS.SETTINGS}/database-servers/${serverId}`, server);
    return response.data;
  }

  async deleteDatabaseServer(serverId: number): Promise<ApiResponse> {
    const response = await this.client.delete(`${API_CONFIG.ENDPOINTS.SETTINGS}/database-servers/${serverId}`);
    return response.data;
  }

  // System Settings API
  async getSystemSetting(key: string): Promise<ApiResponse> {
    const response = await this.client.get(`${API_CONFIG.ENDPOINTS.SETTINGS}/system/${key}`);
    return response.data;
  }

  async setSystemSetting(key: string, value: string, description?: string): Promise<ApiResponse> {
    const response = await this.client.post(`${API_CONFIG.ENDPOINTS.SETTINGS}/system`, {
      key,
      value,
      description: description || ''
    });
    return response.data;
  }

  async getAllSystemSettings(): Promise<ApiResponse> {
    const response = await this.client.get(`${API_CONFIG.ENDPOINTS.SETTINGS}/system`);
    return response.data;
  }

  async deleteSystemSetting(key: string): Promise<ApiResponse> {
    const response = await this.client.delete(`${API_CONFIG.ENDPOINTS.SETTINGS}/system/${key}`);
    return response.data;
  }

  async getMenuConfiguration(): Promise<ApiResponse> {
    const response = await this.client.get(`${API_CONFIG.ENDPOINTS.SETTINGS}/menu`);
    return response.data;
  }

  async updateMenuConfiguration(menuConfig: any): Promise<ApiResponse> {
    const response = await this.client.put(`${API_CONFIG.ENDPOINTS.SETTINGS}/menu`, menuConfig);
    return response.data;
  }

  async createMenuItem(menuItem: any): Promise<ApiResponse> {
    const response = await this.client.post(`${API_CONFIG.ENDPOINTS.SETTINGS}/menu`, menuItem);
    return response.data;
  }

  async updateMenuItem(menuId: number, menuItem: any): Promise<ApiResponse> {
    const response = await this.client.put(`${API_CONFIG.ENDPOINTS.SETTINGS}/menu/${menuId}`, menuItem);
    return response.data;
  }

  async deleteMenuItem(menuId: number): Promise<ApiResponse> {
    const response = await this.client.delete(`${API_CONFIG.ENDPOINTS.SETTINGS}/menu/${menuId}`);
    return response.data;
  }

  // System settings key-value API
  async getSystemSetting(key: string): Promise<ApiResponse> {
    const response = await this.client.get(`${API_CONFIG.ENDPOINTS.SETTINGS}/system/${key}`);
    return response.data;
  }

  async setSystemSetting(key: string, value: any, description?: string): Promise<ApiResponse> {
    const payload: any = { key, value };
    if (description !== undefined) {
      payload.description = description;
    }
    const response = await this.client.post(`${API_CONFIG.ENDPOINTS.SETTINGS}/system`, payload);
    return response.data;
  }

  async getAllSystemSettings(): Promise<ApiResponse> {
    const response = await this.client.get(`${API_CONFIG.ENDPOINTS.SETTINGS}/system`);
    return response.data;
  }

  async deleteSystemSetting(key: string): Promise<ApiResponse> {
    const response = await this.client.delete(`${API_CONFIG.ENDPOINTS.SETTINGS}/system/${key}`);
    return response.data;
  }
}

export const apiService = new ApiService();

// Database API functions
export const databaseApi = {
  testConnection: (config: any) => apiService.testConnection(config),
  getDatabaseServers: () => apiService.getDatabaseServers(),
  getConnectionStatus: () => apiService.getConnectionStatus(),
};

// Settings API functions
export const settingsApi = {
  getSystemSettings: () => apiService.getSystemSettings(),
  updateSystemSettings: (settings: any) => apiService.updateSystemSettings(settings),
  
  // Database servers
  getDatabaseServers: () => apiService.getSettingsDatabaseServers(),
  createDatabaseServer: (server: any) => apiService.createDatabaseServer(server),
  updateDatabaseServer: (serverId: number, server: any) => apiService.updateDatabaseServer(serverId, server),
  deleteDatabaseServer: (serverId: number) => apiService.deleteDatabaseServer(serverId),
  
  // Menu configuration
  getMenuConfiguration: () => apiService.getMenuConfiguration(),
  updateMenuConfiguration: (menuConfig: any) => apiService.updateMenuConfiguration(menuConfig),
  createMenuItem: (menuItem: any) => apiService.createMenuItem(menuItem),
  updateMenuItem: (menuId: number, menuItem: any) => apiService.updateMenuItem(menuId, menuItem),
  deleteMenuItem: (menuId: number) => apiService.deleteMenuItem(menuId),
  
  // System settings key-value
  getSystemSetting: (key: string) => apiService.getSystemSetting(key),
  setSystemSetting: (key: string, value: any, description?: string) => apiService.setSystemSetting(key, value, description),
  getAllSystemSettings: () => apiService.getAllSystemSettings(),
  deleteSystemSetting: (key: string) => apiService.deleteSystemSetting(key),
};

// Query history API functions
export const queryHistoryApi = {
  getQueryHistory: (page?: number, pageSize?: number) => apiService.getQueryHistory(page, pageSize),
  clearQueryHistory: () => apiService.clearQueryHistory(),
  getSavedQueries: () => apiService.getSavedQueries(),
  saveQuery: (query: string, name: string, description?: string) => apiService.saveQuery(query, name, description),
  getSavedQuery: (queryId: number) => apiService.getSavedQuery(queryId),
  updateSavedQuery: (queryId: number, query: string, name: string) => apiService.updateSavedQuery(queryId, query, name),
  deleteSavedQuery: (queryId: number) => apiService.deleteSavedQuery(queryId),
  getQueryStats: () => apiService.getQueryStats(),
};

// Custom query API functions
export const customQueryApi = {
  executeCustomQuery: (request: CustomQueryRequest) => apiService.executeCustomQuery(request),
  validateCustomQuery: (sql: string) => apiService.validateCustomQuery(sql),
  getCustomQueryParameters: () => apiService.getCustomQueryParameters(),
};

export default apiService;