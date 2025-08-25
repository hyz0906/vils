/**
 * Test utilities and helpers
 */

import { mount, VueWrapper } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory } from 'vue-router'
import { vi } from 'vitest'
import type { Component, Plugin } from 'vue'

// Mock router for testing
export const createMockRouter = (initialRoute = '/') => {
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
      { path: '/login', name: 'login', component: { template: '<div>Login</div>' } },
      { path: '/dashboard', name: 'dashboard', component: { template: '<div>Dashboard</div>' } },
      { path: '/projects', name: 'projects', component: { template: '<div>Projects</div>' } },
      { path: '/tasks', name: 'tasks', component: { template: '<div>Tasks</div>' } },
    ]
  })
  
  router.push(initialRoute)
  return router
}

// Mount component with common test setup
export const mountComponent = (
  component: Component,
  options: {
    props?: Record<string, any>
    router?: ReturnType<typeof createMockRouter>
    pinia?: boolean
    global?: {
      plugins?: Plugin[]
      provide?: Record<string, any>
      stubs?: Record<string, any>
    }
  } = {}
): VueWrapper => {
  const plugins: Plugin[] = []
  
  if (options.pinia !== false) {
    plugins.push(createTestingPinia({
      createSpy: vi.fn,
      stubActions: false
    }))
  }
  
  if (options.router) {
    plugins.push(options.router)
  }

  return mount(component, {
    props: options.props,
    global: {
      plugins: [...plugins, ...(options.global?.plugins || [])],
      provide: options.global?.provide,
      stubs: {
        'router-link': {
          template: '<a><slot /></a>',
          props: ['to']
        },
        'router-view': {
          template: '<div><slot /></div>'
        },
        ...options.global?.stubs
      }
    }
  })
}

// Mock API responses
export const mockApiResponse = <T>(data: T, delay = 0) => {
  return new Promise<T>((resolve) => {
    setTimeout(() => resolve(data), delay)
  })
}

export const mockApiError = (message: string, status = 500, delay = 0) => {
  return new Promise((_, reject) => {
    setTimeout(() => reject({
      response: { status, data: { message } },
      message
    }), delay)
  })
}

// Common test data
export const mockUser = {
  id: '1',
  username: 'testuser',
  email: 'test@example.com',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  is_active: true
}

export const mockProject = {
  id: '1',
  name: 'Test Project',
  description: 'A test project',
  is_active: true,
  repository_url: 'https://github.com/test/project',
  build_command: 'npm run build',
  test_command: 'npm test',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  owner: mockUser,
  tags: []
}

export const mockTask = {
  id: '1',
  project: mockProject,
  user: mockUser,
  status: 'active' as const,
  description: 'Test localization task',
  good_commit: 'abc123',
  bad_commit: 'def456',
  current_iteration: 1,
  current_candidates: ['commit1', 'commit2', 'commit3'],
  total_iterations: null,
  problematic_commit: null,
  error_message: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString()
}

// Wait for next tick
export const nextTick = () => new Promise(resolve => setTimeout(resolve, 0))

// Wait for async operations
export const waitFor = (fn: () => any, timeout = 1000) => {
  return new Promise((resolve, reject) => {
    const startTime = Date.now()
    
    const check = () => {
      try {
        const result = fn()
        if (result) {
          resolve(result)
          return
        }
      } catch (error) {
        // Continue checking
      }
      
      if (Date.now() - startTime >= timeout) {
        reject(new Error('waitFor timeout'))
        return
      }
      
      setTimeout(check, 10)
    }
    
    check()
  })
}

// Trigger events
export const triggerEvent = async (wrapper: VueWrapper, selector: string, event: string, data?: any) => {
  const element = wrapper.find(selector)
  await element.trigger(event, data)
  await wrapper.vm.$nextTick()
}

// Fill form inputs
export const fillInput = async (wrapper: VueWrapper, selector: string, value: string) => {
  const input = wrapper.find(selector)
  await input.setValue(value)
  await wrapper.vm.$nextTick()
}

// Click element
export const clickElement = async (wrapper: VueWrapper, selector: string) => {
  const element = wrapper.find(selector)
  await element.trigger('click')
  await wrapper.vm.$nextTick()
}