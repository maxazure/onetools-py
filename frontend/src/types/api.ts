/**
 * API Types and Interfaces
 */

// Base response types
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  errors?: string[] | null;
  meta?: any;
  timestamp?: string;
}

export interface PaginatedData<T = any> {
  items: T[];
  total_count: number;
  page_number: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface PaginatedResponse<T = any> {
  data: PaginatedData<T>;
  status: 'success' | 'error';
  message?: string;
  timestamp?: string;
}

// Query types
export type QueryType = 'USER' | 'TRANSACTION' | 'CUSTOM' | 'DYNAMIC';

export interface QueryRequest {
  query_type: QueryType;
  parameters?: Record<string, any>;
  page_number?: number;
  page_size?: number;
  sql_query?: string;
}

export interface CustomQueryRequest {
  sql: string;
  parameters?: Record<string, any>;
  save_query?: boolean;
  query_name?: string;
  server_name?: string;
}

export interface DynamicQueryRequest {
  sql_query: string;
  parameters?: Record<string, any>;
  page_number?: number;
  page_size?: number;
}

// Database types
export interface DatabaseConfig {
  type: 'sqlserver' | 'sqlite';
  host?: string;
  port?: number;
  database?: string;
  username?: string;
  trusted_connection?: boolean;
}

export interface DatabaseStatus {
  connected: boolean;
  database_type: string;
  server_name: string;
  error_message?: string;
}


// Query results
export interface QueryResult {
  columns: string[];
  data: Record<string, any>[];
  total_count: number;
  execution_time: number;
  query_id?: string;
}

// Settings types
export interface DatabaseSettings {
  connections: DatabaseConfig[];
  default_connection: string;
  query_timeout: number;
  max_rows: number;
}

export interface AppSettings {
  theme: 'light' | 'dark';
  language: string;
  auto_save: boolean;
  query_history_limit: number;
}

// Menu configuration types
export interface MenuConfiguration {
  id?: number;
  key: string;
  label: string;
  icon: string;
  path: string;
  component: string;
  position: 'top' | 'bottom';
  section: 'main' | 'system';
  order: number;
  enabled: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export interface MenuFormData {
  key: string;
  label: string;
  icon: string;
  path: string;
  component: string;
  position: 'top' | 'bottom';
  section: 'main' | 'system';
  order: number;
  enabled: boolean;
}

// Saved Query types
export interface SavedQuery {
  id?: number;
  name: string;
  description?: string;
  query_type: QueryType;
  sql: string;
  params?: Record<string, any>;
  is_public?: boolean;
  tags?: string[];
  is_favorite?: boolean;
  user_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface SavedQueryRequest {
  name: string;
  description?: string;
  sql: string;
  query_type?: QueryType;
  params?: Record<string, any>;
  is_public?: boolean;
  tags?: string[];
  is_favorite?: boolean;
}

// Error types
export interface ApiError {
  error_code: string;
  error_message: string;
  details?: Record<string, any>;
  timestamp: string;
}