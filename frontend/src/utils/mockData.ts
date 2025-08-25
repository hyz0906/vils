/**
 * Mock data for standalone frontend testing
 */

import type { User, Project, LocalizationTask, TaskIteration, Tag } from '@/types'

// Mock users
export const mockUsers: User[] = [
  {
    id: '1',
    username: 'john_doe',
    email: 'john@example.com',
    created_at: new Date(Date.now() - 86400000 * 30).toISOString(), // 30 days ago
    updated_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
    is_active: true,
    last_login: new Date(Date.now() - 1800000).toISOString(), // 30 minutes ago
  },
  {
    id: '2',
    username: 'jane_smith',
    email: 'jane@example.com',
    created_at: new Date(Date.now() - 86400000 * 15).toISOString(), // 15 days ago
    updated_at: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
    is_active: true,
    last_login: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
  },
  {
    id: '3',
    username: 'alex_johnson',
    email: 'alex@example.com',
    created_at: new Date(Date.now() - 86400000 * 7).toISOString(), // 7 days ago
    updated_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
    is_active: true,
    last_login: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
  }
]

// Mock tags
export const mockTags: Tag[] = [
  { id: '1', name: 'frontend', color: '#3B82F6', created_at: new Date().toISOString() },
  { id: '2', name: 'react', color: '#10B981', created_at: new Date().toISOString() },
  { id: '3', name: 'backend', color: '#F59E0B', created_at: new Date().toISOString() },
  { id: '4', name: 'python', color: '#8B5CF6', created_at: new Date().toISOString() },
  { id: '5', name: 'api', color: '#EF4444', created_at: new Date().toISOString() },
  { id: '6', name: 'database', color: '#6B7280', created_at: new Date().toISOString() },
  { id: '7', name: 'ci-cd', color: '#059669', created_at: new Date().toISOString() },
  { id: '8', name: 'testing', color: '#DC2626', created_at: new Date().toISOString() },
]

// Mock projects
export const mockProjects: Project[] = [
  {
    id: '1',
    name: 'Frontend Application',
    description: 'Main React-based frontend application with TypeScript',
    is_active: true,
    repository_url: 'https://github.com/company/frontend-app',
    build_command: 'npm run build',
    test_command: 'npm test',
    created_at: new Date(Date.now() - 86400000 * 10).toISOString(), // 10 days ago
    updated_at: new Date(Date.now() - 3600000 * 2).toISOString(), // 2 hours ago
    owner: mockUsers[0],
    tags: [mockTags[0], mockTags[1]]
  },
  {
    id: '2',
    name: 'Backend API Service',
    description: 'Core API service built with Python FastAPI and PostgreSQL',
    is_active: true,
    repository_url: 'https://github.com/company/backend-api',
    build_command: 'python -m pytest --cov=.',
    test_command: 'python -m pytest tests/',
    created_at: new Date(Date.now() - 86400000 * 20).toISOString(), // 20 days ago
    updated_at: new Date(Date.now() - 3600000 * 5).toISOString(), // 5 hours ago
    owner: mockUsers[1],
    tags: [mockTags[2], mockTags[3], mockTags[4]]
  },
  {
    id: '3',
    name: 'Database Migration Tools',
    description: 'Database schema migration and data transformation utilities',
    is_active: false,
    repository_url: 'https://github.com/company/db-migrations',
    build_command: 'python setup.py test',
    test_command: 'python -m unittest discover',
    created_at: new Date(Date.now() - 86400000 * 45).toISOString(), // 45 days ago
    updated_at: new Date(Date.now() - 86400000 * 7).toISOString(), // 7 days ago
    owner: mockUsers[2],
    tags: [mockTags[5], mockTags[3]]
  },
  {
    id: '4',
    name: 'CI/CD Pipeline',
    description: 'Continuous integration and deployment pipeline configuration',
    is_active: true,
    repository_url: 'https://github.com/company/ci-cd-config',
    build_command: 'docker build -t test-image .',
    test_command: 'docker run --rm test-image npm test',
    created_at: new Date(Date.now() - 86400000 * 5).toISOString(), // 5 days ago
    updated_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
    owner: mockUsers[0],
    tags: [mockTags[6], mockTags[7]]
  },
  {
    id: '5',
    name: 'Mobile Application',
    description: 'React Native mobile application for iOS and Android',
    is_active: true,
    repository_url: 'https://github.com/company/mobile-app',
    build_command: 'npx react-native build-android',
    test_command: 'npm run test:mobile',
    created_at: new Date(Date.now() - 86400000 * 30).toISOString(), // 30 days ago
    updated_at: new Date(Date.now() - 86400000 * 2).toISOString(), // 2 days ago
    owner: mockUsers[1],
    tags: [mockTags[0], mockTags[1]]
  }
]

// Mock task iterations
export const mockTaskIterations: TaskIteration[] = [
  {
    id: '1',
    task_id: '1',
    iteration_number: 1,
    tested_commit: 'a1b2c3d4e5f6g7h8',
    result: 'bad',
    candidates_remaining: 8,
    created_at: new Date(Date.now() - 7200000).toISOString() // 2 hours ago
  },
  {
    id: '2',
    task_id: '1',
    iteration_number: 2,
    tested_commit: 'b2c3d4e5f6g7h8i9',
    result: 'good',
    candidates_remaining: 4,
    created_at: new Date(Date.now() - 5400000).toISOString() // 1.5 hours ago
  },
  {
    id: '3',
    task_id: '1',
    iteration_number: 3,
    tested_commit: 'c3d4e5f6g7h8i9j0',
    result: 'bad',
    candidates_remaining: 2,
    created_at: new Date(Date.now() - 3600000).toISOString() // 1 hour ago
  },
  {
    id: '4',
    task_id: '2',
    iteration_number: 1,
    tested_commit: 'x1y2z3a4b5c6d7e8',
    result: 'good',
    candidates_remaining: 6,
    created_at: new Date(Date.now() - 86400000).toISOString() // 1 day ago
  },
  {
    id: '5',
    task_id: '2',
    iteration_number: 2,
    tested_commit: 'y2z3a4b5c6d7e8f9',
    result: 'skip',
    candidates_remaining: 5,
    created_at: new Date(Date.now() - 82800000).toISOString() // 23 hours ago
  },
  {
    id: '6',
    task_id: '2',
    iteration_number: 3,
    tested_commit: 'z3a4b5c6d7e8f9g0',
    result: 'bad',
    candidates_remaining: 3,
    created_at: new Date(Date.now() - 79200000).toISOString() // 22 hours ago
  },
  {
    id: '7',
    task_id: '2',
    iteration_number: 4,
    tested_commit: 'a4b5c6d7e8f9g0h1',
    result: 'good',
    candidates_remaining: 1,
    created_at: new Date(Date.now() - 75600000).toISOString() // 21 hours ago
  }
]

// Mock localization tasks
export const mockTasks: LocalizationTask[] = [
  {
    id: '1',
    project: mockProjects[0],
    user: mockUsers[0],
    status: 'active',
    description: 'Investigating build failures in CI pipeline after recent updates',
    good_commit: 'abc123def456ghi789jkl012',
    bad_commit: 'mno345pqr678stu901vwx234',
    current_iteration: 4,
    current_candidates: [
      'd4e5f6g7h8i9j0k1',
      'e5f6g7h8i9j0k1l2'
    ],
    total_iterations: null,
    problematic_commit: null,
    error_message: null,
    created_at: new Date(Date.now() - 10800000).toISOString(), // 3 hours ago
    updated_at: new Date(Date.now() - 1800000).toISOString(), // 30 minutes ago
  },
  {
    id: '2',
    project: mockProjects[1],
    user: mockUsers[1],
    status: 'completed',
    description: 'Performance regression in database query optimization',
    good_commit: 'xyz789abc123def456ghi789',
    bad_commit: 'jkl012mno345pqr678stu901',
    current_iteration: null,
    current_candidates: null,
    total_iterations: 4,
    problematic_commit: 'a4b5c6d7e8f9g0h1',
    error_message: null,
    created_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
    updated_at: new Date(Date.now() - 75600000).toISOString(), // 21 hours ago
  },
  {
    id: '3',
    project: mockProjects[2],
    user: mockUsers[2],
    status: 'failed',
    description: 'Database migration rollback issue',
    good_commit: 'qwe123rty456uio789pas012',
    bad_commit: 'dfg345hjk678lmn901bnm234',
    current_iteration: 2,
    current_candidates: null,
    total_iterations: null,
    problematic_commit: null,
    error_message: 'Build environment setup failed: Docker daemon not accessible',
    created_at: new Date(Date.now() - 172800000).toISOString(), // 2 days ago
    updated_at: new Date(Date.now() - 165600000).toISOString(), // 1.9 days ago
  },
  {
    id: '4',
    project: mockProjects[3],
    user: mockUsers[0],
    status: 'active',
    description: 'Docker build optimization causing deployment failures',
    good_commit: 'build123docker456deploy789',
    bad_commit: 'fail123error456timeout789',
    current_iteration: 2,
    current_candidates: [
      'opt123fast456quick789',
      'slow123lag456delay789',
      'med123avg456normal789',
      'test123check456verify789',
      'deploy123live456prod789',
      'stage123prep456ready789'
    ],
    total_iterations: null,
    problematic_commit: null,
    error_message: null,
    created_at: new Date(Date.now() - 14400000).toISOString(), // 4 hours ago
    updated_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
  },
  {
    id: '5',
    project: mockProjects[4],
    user: mockUsers[1],
    status: 'completed',
    description: 'React Native build issues on Android platform',
    good_commit: 'native123react456mobile789',
    bad_commit: 'android123issue456crash789',
    current_iteration: null,
    current_candidates: null,
    total_iterations: 3,
    problematic_commit: 'gradle123build456error789',
    error_message: null,
    created_at: new Date(Date.now() - 259200000).toISOString(), // 3 days ago
    updated_at: new Date(Date.now() - 216000000).toISOString(), // 2.5 days ago
  }
]

// Mock build output lines
export const mockBuildOutput = [
  '> npm run build',
  '',
  '> frontend@1.0.0 build',
  '> vite build',
  '',
  'vite v4.4.0 building for production...',
  '✓ 127 modules transformed.',
  'dist/index.html                   0.46 kB │ gzip:  0.30 kB',
  'dist/assets/index-a1b2c3d4.css    8.93 kB │ gzip:  2.41 kB',
  'dist/assets/index-e5f6g7h8.js   145.23 kB │ gzip: 46.89 kB',
  '✓ built in 2.35s',
  '',
  '> npm test',
  '',
  '> frontend@1.0.0 test',
  '> vitest run',
  '',
  ' RUN  v0.34.0',
  '',
  ' ✓ src/components/UserAvatar.test.ts (3)',
  ' ✓ src/stores/auth.test.ts (5)',
  ' ✓ src/utils/api.test.ts (8)',
  '',
  ' Test Files  3 passed (3)',
  ' Tests  16 passed (16)',
  ' Start at 14:23:45',
  ' Duration  1.87s (transform 234ms, setup 0ms, collect 567ms, tests 1.01s)',
  '',
  'Build completed successfully! ✅'
]

// Mock activity data for dashboard
export const mockActivity = [
  {
    id: '1',
    type: 'task_completed' as const,
    description: 'Completed localization task for Backend API Service',
    timestamp: new Date(Date.now() - 75600000).toISOString() // 21 hours ago
  },
  {
    id: '2',
    type: 'project_created' as const,
    description: 'Created new project: Mobile Application',
    timestamp: new Date(Date.now() - 86400000).toISOString() // 1 day ago
  },
  {
    id: '3',
    type: 'task_created' as const,
    description: 'Started new localization task for CI/CD Pipeline',
    timestamp: new Date(Date.now() - 14400000).toISOString() // 4 hours ago
  },
  {
    id: '4',
    type: 'project_updated' as const,
    description: 'Updated build configuration for Frontend Application',
    timestamp: new Date(Date.now() - 7200000).toISOString() // 2 hours ago
  },
  {
    id: '5',
    type: 'task_created' as const,
    description: 'Started localization task for Frontend Application',
    timestamp: new Date(Date.now() - 10800000).toISOString() // 3 hours ago
  }
]

// Mock dashboard statistics
export const mockStats = {
  totalProjects: mockProjects.length,
  activeTasks: mockTasks.filter(t => t.status === 'active').length,
  completedTasks: mockTasks.filter(t => t.status === 'completed').length,
  completedThisWeek: 3,
  avgResolutionTime: '2.4 hrs',
  taskSuccessRate: 85
}

// Mock notification data
export const mockNotifications = [
  {
    id: '1',
    type: 'success' as const,
    title: 'Task Completed',
    message: 'Binary search localization for Backend API Service completed successfully.',
    timestamp: new Date(Date.now() - 300000).toISOString(), // 5 minutes ago
    read: false
  },
  {
    id: '2',
    type: 'info' as const,
    title: 'New Task Started',
    message: 'Localization task for CI/CD Pipeline has been initiated.',
    timestamp: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
    read: false
  },
  {
    id: '3',
    type: 'warning' as const,
    title: 'Build Timeout',
    message: 'Build for commit a1b2c3d4 exceeded 10-minute timeout limit.',
    timestamp: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
    read: true
  },
  {
    id: '4',
    type: 'error' as const,
    title: 'Task Failed',
    message: 'Localization task failed due to Docker daemon connectivity issues.',
    timestamp: new Date(Date.now() - 165600000).toISOString(), // 1.9 days ago
    read: true
  }
]

// Helper functions for mock API simulation
export const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

export const mockApiResponse = <T>(data: T, delayMs: number = 500) => {
  return delay(delayMs).then(() => ({
    data,
    status: 200,
    statusText: 'OK'
  }))
}

export const mockApiError = (message: string, status: number = 500, delayMs: number = 500) => {
  return delay(delayMs).then(() => Promise.reject({
    response: {
      status,
      data: { message }
    },
    message
  }))
}

// Generate random commit hash
export const generateCommitHash = () => {
  return Array.from({ length: 16 }, () => Math.floor(Math.random() * 16).toString(16)).join('')
}

// Generate mock candidates for binary search
export const generateMockCandidates = (count: number = 5): string[] => {
  return Array.from({ length: count }, () => generateCommitHash())
}