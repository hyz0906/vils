/**
 * Mock API implementation for standalone frontend testing
 */

import { 
  mockUsers, 
  mockProjects, 
  mockTasks, 
  mockTaskIterations, 
  mockActivity, 
  mockStats,
  mockNotifications,
  mockBuildOutput,
  mockApiResponse, 
  mockApiError,
  generateMockCandidates,
  generateCommitHash
} from './mockData'
import type { 
  User, 
  Project, 
  LocalizationTask, 
  LoginForm, 
  RegisterForm,
  AuthTokens
} from '@/types'

// Environment check
const isDevelopment = import.meta.env.MODE === 'development'
const useMockApi = import.meta.env.VITE_USE_MOCK_API === 'true' || !import.meta.env.VITE_API_BASE_URL

// Mock storage for auth tokens
let mockAuthTokens: AuthTokens | null = null
let currentUser: User | null = null

// Mock WebSocket simulation
class MockWebSocket {
  url: string
  readyState: number = WebSocket.CONNECTING
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null

  constructor(url: string) {
    this.url = url
    
    // Simulate connection establishment
    setTimeout(() => {
      this.readyState = WebSocket.OPEN
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
      
      // Send connection established message
      setTimeout(() => {
        if (this.onmessage) {
          this.onmessage(new MessageEvent('message', {
            data: JSON.stringify({
              type: 'connection_established',
              message: 'WebSocket connection established'
            })
          }))
        }
      }, 100)
    }, 500)
  }

  send(data: string) {
    if (this.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket not connected')
      return
    }

    try {
      const message = JSON.parse(data)
      
      // Handle subscription messages
      if (message.type === 'subscribe') {
        setTimeout(() => {
          if (this.onmessage) {
            this.onmessage(new MessageEvent('message', {
              data: JSON.stringify({
                type: 'subscription_confirmed',
                key: message.key
              })
            }))
          }
        }, 100)

        // Simulate periodic updates for task subscriptions
        if (message.key.startsWith('task_')) {
          this.simulateTaskUpdates(message.key)
        }
      }

      // Handle ping messages
      if (message.type === 'ping') {
        setTimeout(() => {
          if (this.onmessage) {
            this.onmessage(new MessageEvent('message', {
              data: JSON.stringify({
                type: 'pong',
                timestamp: new Date().toISOString()
              })
            }))
          }
        }, 50)
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
    }
  }

  close(code?: number, reason?: string) {
    this.readyState = WebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code: code || 1000, reason }))
    }
  }

  private simulateTaskUpdates(taskKey: string) {
    const taskId = taskKey.replace('task_', '')
    const task = mockTasks.find(t => t.id === taskId)
    
    if (!task || task.status !== 'active') return

    // Simulate build output updates
    let outputIndex = 0
    const outputInterval = setInterval(() => {
      if (this.readyState !== WebSocket.OPEN || outputIndex >= mockBuildOutput.length) {
        clearInterval(outputInterval)
        return
      }

      if (this.onmessage) {
        this.onmessage(new MessageEvent('message', {
          data: JSON.stringify({
            type: 'build_output',
            task_id: taskId,
            line: mockBuildOutput[outputIndex],
            timestamp: new Date().toISOString()
          })
        }))
      }

      outputIndex++
    }, 200)

    // Simulate progress updates
    setTimeout(() => {
      if (this.readyState === WebSocket.OPEN && this.onmessage) {
        this.onmessage(new MessageEvent('message', {
          data: JSON.stringify({
            type: 'progress_update',
            task_id: taskId,
            progress: Math.min(90, (task.current_iteration || 1) * 20),
            message: 'Binary search in progress...'
          })
        }))
      }
    }, 3000)
  }
}

// Mock API implementation
export class MockApiClient {
  private baseURL: string
  private authToken: string | null = null

  constructor(baseURL: string) {
    this.baseURL = baseURL
  }

  setAuthToken(token: string) {
    this.authToken = token
  }

  removeAuthToken() {
    this.authToken = null
  }

  isAuthenticated(): boolean {
    return !!this.authToken && !!mockAuthTokens
  }

  storeTokens(tokens: AuthTokens) {
    mockAuthTokens = tokens
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('vils_access_token', tokens.access_token)
      localStorage.setItem('vils_refresh_token', tokens.refresh_token)
    }
  }

  clearTokens() {
    mockAuthTokens = null
    currentUser = null
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem('vils_access_token')
      localStorage.removeItem('vils_refresh_token')
    }
  }

  getWebSocketToken(): string | null {
    return this.authToken
  }

  // Auth API
  async login(credentials: LoginForm) {
    await new Promise(resolve => setTimeout(resolve, 1000)) // Simulate network delay

    // Simple mock authentication
    const user = mockUsers.find(u => 
      u.username === credentials.username || u.email === credentials.username
    )

    if (!user || credentials.password.length < 6) {
      throw new Error('Invalid credentials')
    }

    const tokens: AuthTokens = {
      access_token: 'mock_access_token_' + Date.now(),
      refresh_token: 'mock_refresh_token_' + Date.now(),
      token_type: 'bearer',
      expires_in: 3600
    }

    currentUser = { ...user, last_login: new Date().toISOString() }
    return tokens
  }

  async register(userData: RegisterForm) {
    await new Promise(resolve => setTimeout(resolve, 1200)) // Simulate network delay

    // Check if user already exists
    const existingUser = mockUsers.find(u => 
      u.username === userData.username || u.email === userData.email
    )

    if (existingUser) {
      throw new Error('User with this username or email already exists')
    }

    // Create new user
    const newUser: User = {
      id: (mockUsers.length + 1).toString(),
      username: userData.username,
      email: userData.email,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      is_active: true,
      last_login: new Date().toISOString()
    }

    mockUsers.push(newUser)
    currentUser = newUser

    return newUser
  }

  async logout() {
    await new Promise(resolve => setTimeout(resolve, 300))
    // Mock logout - in real implementation would invalidate tokens on server
    return { message: 'Logged out successfully' }
  }

  async getProfile() {
    if (!this.isAuthenticated()) {
      throw { response: { status: 401 }, message: 'Unauthorized' }
    }
    
    await new Promise(resolve => setTimeout(resolve, 200))
    
    if (!currentUser) {
      // Try to find user based on stored token
      currentUser = mockUsers[0] // Default to first user for testing
    }
    
    return currentUser
  }

  async refresh(refreshToken: string) {
    await new Promise(resolve => setTimeout(resolve, 500))

    if (!refreshToken.startsWith('mock_refresh_token_')) {
      throw new Error('Invalid refresh token')
    }

    const tokens: AuthTokens = {
      access_token: 'mock_access_token_refreshed_' + Date.now(),
      refresh_token: 'mock_refresh_token_refreshed_' + Date.now(),
      token_type: 'bearer',
      expires_in: 3600
    }

    return tokens
  }

  async changePassword(currentPassword: string, newPassword: string) {
    await new Promise(resolve => setTimeout(resolve, 800))
    
    if (!this.isAuthenticated()) {
      throw { response: { status: 401 }, message: 'Unauthorized' }
    }

    if (currentPassword === newPassword) {
      throw new Error('New password must be different from current password')
    }

    return { message: 'Password changed successfully' }
  }

  // Projects API
  async getProjects(params?: { search?: string; active?: boolean }) {
    await new Promise(resolve => setTimeout(resolve, 600))
    
    if (!this.isAuthenticated()) {
      throw { response: { status: 401 }, message: 'Unauthorized' }
    }

    let projects = [...mockProjects]

    if (params?.search) {
      const search = params.search.toLowerCase()
      projects = projects.filter(p => 
        p.name.toLowerCase().includes(search) ||
        p.description?.toLowerCase().includes(search)
      )
    }

    if (params?.active !== undefined) {
      projects = projects.filter(p => p.is_active === params.active)
    }

    return projects
  }

  async getProject(id: string) {
    await new Promise(resolve => setTimeout(resolve, 300))
    
    if (!this.isAuthenticated()) {
      throw { response: { status: 401 }, message: 'Unauthorized' }
    }

    const project = mockProjects.find(p => p.id === id)
    if (!project) {
      throw { response: { status: 404 }, message: 'Project not found' }
    }

    return project
  }

  async createProject(projectData: Partial<Project>) {
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    if (!this.isAuthenticated() || !currentUser) {
      throw { response: { status: 401 }, message: 'Unauthorized' }
    }

    const newProject: Project = {
      id: (mockProjects.length + 1).toString(),
      name: projectData.name || 'New Project',
      description: projectData.description || '',
      is_active: projectData.is_active ?? true,
      repository_url: projectData.repository_url || '',
      build_command: projectData.build_command || 'npm run build',
      test_command: projectData.test_command || 'npm test',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      owner: currentUser,
      tags: projectData.tags || []
    }

    mockProjects.push(newProject)
    return newProject
  }

  // Tasks API
  async getTasks(params?: { project_id?: string; status?: string }) {
    await new Promise(resolve => setTimeout(resolve, 700))
    
    if (!this.isAuthenticated()) {
      throw { response: { status: 401 }, message: 'Unauthorized' }
    }

    let tasks = [...mockTasks]

    if (params?.project_id) {
      tasks = tasks.filter(t => t.project.id === params.project_id)
    }

    if (params?.status) {
      tasks = tasks.filter(t => t.status === params.status)
    }

    return tasks
  }

  async getTask(id: string) {
    await new Promise(resolve => setTimeout(resolve, 400))
    
    if (!this.isAuthenticated()) {
      throw { response: { status: 401 }, message: 'Unauthorized' }
    }

    const task = mockTasks.find(t => t.id === id)
    if (!task) {
      throw { response: { status: 404 }, message: 'Task not found' }
    }

    return task
  }

  async createTask(taskData: {
    project_id: string
    good_commit: string
    bad_commit: string
    description?: string
  }) {
    await new Promise(resolve => setTimeout(resolve, 1200))
    
    if (!this.isAuthenticated() || !currentUser) {
      throw { response: { status: 401 }, message: 'Unauthorized' }
    }

    const project = mockProjects.find(p => p.id === taskData.project_id)
    if (!project) {
      throw { response: { status: 404 }, message: 'Project not found' }
    }

    const newTask: LocalizationTask = {
      id: (mockTasks.length + 1).toString(),
      project,
      user: currentUser,
      status: 'active',
      description: taskData.description || 'Binary search localization task',
      good_commit: taskData.good_commit,
      bad_commit: taskData.bad_commit,
      current_iteration: 1,
      current_candidates: generateMockCandidates(8),
      total_iterations: null,
      problematic_commit: null,
      error_message: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }

    mockTasks.push(newTask)
    return newTask
  }

  async markCandidate(taskId: string, candidateData: {
    candidate: string
    result: 'good' | 'bad' | 'skip'
  }) {
    await new Promise(resolve => setTimeout(resolve, 2000)) // Simulate build time
    
    if (!this.isAuthenticated()) {
      throw { response: { status: 401 }, message: 'Unauthorized' }
    }

    const task = mockTasks.find(t => t.id === taskId)
    if (!task) {
      throw { response: { status: 404 }, message: 'Task not found' }
    }

    // Update task iteration
    task.current_iteration = (task.current_iteration || 0) + 1
    task.updated_at = new Date().toISOString()

    // Simulate binary search logic
    const currentCandidates = task.current_candidates || []
    const candidateIndex = currentCandidates.indexOf(candidateData.candidate)

    if (candidateData.result === 'good') {
      task.current_candidates = currentCandidates.slice(candidateIndex + 1)
    } else if (candidateData.result === 'bad') {
      task.current_candidates = currentCandidates.slice(0, candidateIndex)
    } else {
      // Skip - remove this candidate but keep others
      task.current_candidates = currentCandidates.filter(c => c !== candidateData.candidate)
    }

    // Check if we found the problematic commit
    if (task.current_candidates.length <= 1) {
      task.status = 'completed'
      task.problematic_commit = task.current_candidates[0] || candidateData.candidate
      task.total_iterations = task.current_iteration
      task.current_candidates = null
    }

    return task
  }

  // Task iterations
  async getTaskIterations(taskId: string) {
    await new Promise(resolve => setTimeout(resolve, 300))
    
    if (!this.isAuthenticated()) {
      throw { response: { status: 401 }, message: 'Unauthorized' }
    }

    return mockTaskIterations.filter(i => i.task_id === taskId)
  }

  // Dashboard API
  async getDashboardStats() {
    await new Promise(resolve => setTimeout(resolve, 500))
    
    if (!this.isAuthenticated()) {
      throw { response: { status: 401 }, message: 'Unauthorized' }
    }

    return mockStats
  }

  async getRecentActivity() {
    await new Promise(resolve => setTimeout(resolve, 400))
    
    if (!this.isAuthenticated()) {
      throw { response: { status: 401 }, message: 'Unauthorized' }
    }

    return mockActivity
  }

  // Notifications API
  async getNotifications() {
    await new Promise(resolve => setTimeout(resolve, 300))
    
    if (!this.isAuthenticated()) {
      throw { response: { status: 401 }, message: 'Unauthorized' }
    }

    return mockNotifications
  }

  // Health check
  async healthCheck() {
    await new Promise(resolve => setTimeout(resolve, 100))
    return { status: 'ok', timestamp: new Date().toISOString() }
  }
}

// Create mock WebSocket if needed
export const createMockWebSocket = (url: string): WebSocket => {
  if (useMockApi) {
    return new MockWebSocket(url) as unknown as WebSocket
  }
  return new WebSocket(url)
}

// Export mock API instance
export const mockApiClient = new MockApiClient('/api')