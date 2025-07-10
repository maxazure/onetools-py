/**
 * API Configuration
 */

export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_URL || 'http://192.168.31.129:15008',
  API_VERSION: 'v1',
  TIMEOUT: 30000,
  
  // Endpoints
  ENDPOINTS: {
    HEALTH: '/health',
    USER_QUERY: '/api/v1/users/query',
    CUSTOM_QUERY: '/api/v1/custom/execute',
    DYNAMIC_QUERY: '/api/v1/query/dynamic',
    DATABASE: '/api/v1/database',
    SETTINGS: '/api/v1/settings',
  } as const,
  
  // Default pagination
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
} as const;

export type ApiEndpoint = keyof typeof API_CONFIG.ENDPOINTS;