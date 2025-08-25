/**
 * API client utilities and HTTP service
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import type { AuthTokens } from '@/types'
import { mockApiClient } from './mockApi'

class ApiClient {
  private client: AxiosInstance
  private tokenRefreshPromise: Promise<string> | null = null

  constructor(baseURL?: string) {
    this.client = axios.create({
      baseURL: baseURL || import.meta.env.VITE_API_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = this.getStoredToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response
      },
      async (error) => {
        const originalRequest = error.config

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            const newToken = await this.refreshToken()
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            return this.client(originalRequest)
          } catch (refreshError) {
            // Refresh failed, redirect to login
            this.handleAuthFailure()
            return Promise.reject(refreshError)
          }
        }

        return Promise.reject(error)
      }
    )
  }

  private getStoredToken(): string | null {
    return localStorage.getItem('vils_access_token')
  }

  private getStoredRefreshToken(): string | null {
    return localStorage.getItem('vils_refresh_token')
  }

  private async refreshToken(): Promise<string> {
    if (this.tokenRefreshPromise) {
      return this.tokenRefreshPromise
    }

    this.tokenRefreshPromise = new Promise(async (resolve, reject) => {
      try {
        const refreshToken = this.getStoredRefreshToken()
        if (!refreshToken) {
          reject(new Error('No refresh token available'))
          return
        }

        const response = await axios.post('/api/auth/refresh', {
          refresh_token: refreshToken,
        })

        const tokens: AuthTokens = response.data
        this.storeTokens(tokens)
        resolve(tokens.access_token)
      } catch (error) {
        this.clearTokens()
        reject(error)
      } finally {
        this.tokenRefreshPromise = null
      }
    })

    return this.tokenRefreshPromise
  }

  private handleAuthFailure() {
    this.clearTokens()
    // Emit event or use router to redirect to login
    window.dispatchEvent(new CustomEvent('auth:logout'))
  }

  public storeTokens(tokens: AuthTokens) {
    localStorage.setItem('vils_access_token', tokens.access_token)
    if (tokens.refresh_token) {
      localStorage.setItem('vils_refresh_token', tokens.refresh_token)
    }
  }

  public clearTokens() {
    localStorage.removeItem('vils_access_token')
    localStorage.removeItem('vils_refresh_token')
  }

  // HTTP methods
  public async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get(url, config)
    return response.data
  }

  public async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post(url, data, config)
    return response.data
  }

  public async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put(url, data, config)
    return response.data
  }

  public async patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch(url, data, config)
    return response.data
  }

  public async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete(url, config)
    return response.data
  }

  // Utility methods
  public setAuthToken(token: string) {
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`
  }

  public removeAuthToken() {
    delete this.client.defaults.headers.common['Authorization']
  }

  public isAuthenticated(): boolean {
    return !!this.getStoredToken()
  }

  // WebSocket token for real-time connections
  public getWebSocketToken(): string | null {
    return this.getStoredToken()
  }
}

// Environment configuration
const useMockApi = import.meta.env.VITE_USE_MOCK_API === 'true' || !import.meta.env.VITE_API_BASE_URL

// Create singleton instance
const apiClient = useMockApi ? mockApiClient : new ApiClient()

export default apiClient

// Export typed API methods with mock support
export const api = {
  // Authentication
  auth: {
    register: (data: { email: string; username: string; password: string }) =>
      useMockApi ? apiClient.register(data) : apiClient.post('/api/auth/register', data),
    
    login: (data: { username: string; password: string }) =>
      useMockApi ? apiClient.login(data) : apiClient.post<AuthTokens>('/api/auth/login', new URLSearchParams(data), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      }),
    
    refresh: (refreshToken: string) =>
      useMockApi ? apiClient.refresh(refreshToken) : apiClient.post<AuthTokens>('/api/auth/refresh', { refresh_token: refreshToken }),
    
    logout: () =>
      useMockApi ? apiClient.logout() : apiClient.post('/api/auth/logout'),
    
    getProfile: () =>
      useMockApi ? apiClient.getProfile() : apiClient.get('/api/auth/me'),
    
    changePassword: (currentPassword: string, newPassword: string) =>
      useMockApi ? apiClient.changePassword(currentPassword, newPassword) : apiClient.post('/api/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      }),
  },

  // Projects
  projects: {
    list: (params?: { skip?: number; limit?: number; search?: string; active?: boolean }) =>
      useMockApi ? apiClient.getProjects(params) : apiClient.get('/api/projects', { params }),
    
    create: (data: any) =>
      useMockApi ? apiClient.createProject(data) : apiClient.post('/api/projects', data),
    
    get: (id: string) =>
      useMockApi ? apiClient.getProject(id) : apiClient.get(`/api/projects/${id}`),
    
    update: (id: string, data: any) => apiClient.put(`/api/projects/${id}`, data),
    
    delete: (id: string) => apiClient.delete(`/api/projects/${id}`),
    
    getBranches: (id: string) => apiClient.get(`/api/projects/${id}/branches`),
    
    getTags: (projectId: string, branchId: string, params?: any) =>
      apiClient.get(`/api/projects/${projectId}/branches/${branchId}/tags`, { params }),
    
    sync: (id: string) => apiClient.post(`/api/projects/${id}/sync`),
    
    importTags: (projectId: string, branchId: string, tags: any[]) =>
      apiClient.post(`/api/projects/${projectId}/branches/${branchId}/tags/import`, tags),
  },

  // Tasks
  tasks: {
    list: (params?: { status?: string; project_id?: string; skip?: number; limit?: number }) =>
      useMockApi ? apiClient.getTasks(params) : apiClient.get('/api/tasks', { params }),
    
    create: (data: any) =>
      useMockApi ? apiClient.createTask(data) : apiClient.post('/api/tasks', data),
    
    get: (id: string) =>
      useMockApi ? apiClient.getTask(id) : apiClient.get(`/api/tasks/${id}`),
    
    update: (id: string, data: any) => apiClient.put(`/api/tasks/${id}`, data),
    
    delete: (id: string) => apiClient.delete(`/api/tasks/${id}`),
    
    getCandidates: (id: string) => apiClient.get(`/api/tasks/${id}/candidates`),
    
    selectCandidates: (id: string, indices: number[]) =>
      apiClient.post(`/api/tasks/${id}/select-candidates`, { candidate_indices: indices }),
    
    getIterations: (id: string) =>
      useMockApi ? apiClient.getTaskIterations(id) : apiClient.get(`/api/tasks/${id}/iterations`),
    
    markCandidate: (id: string, data: { candidate: string; result: 'good' | 'bad' | 'skip' }) =>
      useMockApi ? apiClient.markCandidate(id, data) : apiClient.post(`/api/tasks/${id}/mark-candidate`, data),
    
    pause: (id: string) => apiClient.put(`/api/tasks/${id}/pause`),
    
    resume: (id: string) => apiClient.put(`/api/tasks/${id}/resume`),
  },

  // Dashboard
  dashboard: {
    getStats: () =>
      useMockApi ? apiClient.getDashboardStats() : apiClient.get('/api/dashboard/stats'),
    
    getActivity: () =>
      useMockApi ? apiClient.getRecentActivity() : apiClient.get('/api/dashboard/activity'),
  },

  // Notifications
  notifications: {
    list: () =>
      useMockApi ? apiClient.getNotifications() : apiClient.get('/api/notifications'),
  },

  // Health
  health: () =>
    useMockApi ? apiClient.healthCheck() : apiClient.get('/api/health'),

  // Builds
  builds: {
    trigger: (data: {
      task_id: string
      iteration_id: string
      tag_ids: string[]
      build_service: string
      build_parameters?: Record<string, any>
    }) => apiClient.post('/api/builds/trigger', data),
    
    get: (id: string) => apiClient.get(`/api/builds/${id}`),
    
    getLogs: (id: string) => apiClient.get(`/api/builds/${id}/logs`),
    
    cancel: (id: string) => apiClient.post(`/api/builds/${id}/cancel`),
    
    submitFeedback: (id: string, data: { feedback_type: string; notes?: string }) =>
      apiClient.post(`/api/builds/${id}/feedback`, data),
    
    getTaskBuilds: (taskId: string) => apiClient.get(`/api/builds/task/${taskId}`),
  },
}

// Error handling utilities
export const handleApiError = (error: any): string => {
  if (error.response?.data?.detail) {
    return error.response.data.detail
  }
  if (error.response?.data?.message) {
    return error.response.data.message
  }
  if (error.message) {
    return error.message
  }
  return 'An unexpected error occurred'
}

// Request/response transformers
export const transformDateStrings = (data: any): any => {
  if (data === null || data === undefined) return data
  
  if (typeof data === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(data)) {
    return new Date(data)
  }
  
  if (Array.isArray(data)) {
    return data.map(transformDateStrings)
  }
  
  if (typeof data === 'object') {
    const transformed: any = {}
    for (const [key, value] of Object.entries(data)) {
      transformed[key] = transformDateStrings(value)
    }
    return transformed
  }
  
  return data
}