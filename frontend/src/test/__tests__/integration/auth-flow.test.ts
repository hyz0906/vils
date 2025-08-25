/**
 * Authentication flow integration tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createMockRouter, mountComponent, fillInput, clickElement, waitFor } from '@/test/utils'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import DashboardView from '@/views/DashboardView.vue'

describe('Authentication Flow Integration', () => {
  let router: ReturnType<typeof createMockRouter>

  beforeEach(() => {
    router = createMockRouter('/')
    vi.clearAllMocks()
  })

  describe('Login Flow', () => {
    it('should complete full login flow successfully', async () => {
      const wrapper = mountComponent(LoginView, { router })
      const authStore = useAuthStore()
      const notificationStore = useNotificationStore()

      // Fill in login form
      await fillInput(wrapper, '[data-testid="username-input"]', 'testuser')
      await fillInput(wrapper, '[data-testid="password-input"]', 'password123')

      // Submit form
      await clickElement(wrapper, '[data-testid="login-button"]')

      // Wait for async operations
      await waitFor(() => authStore.user !== null)

      // Verify user is logged in
      expect(authStore.isAuthenticated).toBe(true)
      expect(authStore.user?.username).toBe('testuser')

      // Verify success notification
      expect(notificationStore.notifications).toHaveLength(1)
      expect(notificationStore.notifications[0].type).toBe('success')
      expect(notificationStore.notifications[0].message).toContain('Welcome')

      // Verify navigation to dashboard
      expect(router.currentRoute.value.path).toBe('/dashboard')
    })

    it('should handle login errors gracefully', async () => {
      const wrapper = mountComponent(LoginView, { router })
      const authStore = useAuthStore()
      const notificationStore = useNotificationStore()

      // Mock API to return error
      const { api } = await import('@/utils/api')
      vi.mocked(api.auth.login).mockRejectedValue(new Error('Invalid credentials'))

      // Fill in login form with invalid credentials
      await fillInput(wrapper, '[data-testid="username-input"]', 'invalid')
      await fillInput(wrapper, '[data-testid="password-input"]', 'wrong')

      // Submit form
      await clickElement(wrapper, '[data-testid="login-button"]')

      // Wait for error handling
      await waitFor(() => authStore.error !== null)

      // Verify error state
      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.error).toBe('Invalid credentials')

      // Verify error notification
      expect(notificationStore.notifications.some(n => n.type === 'error')).toBe(true)

      // Verify user stays on login page
      expect(router.currentRoute.value.path).toBe('/')
    })

    it('should show loading state during login', async () => {
      const wrapper = mountComponent(LoginView, { router })

      // Mock slow API response
      const { api } = await import('@/utils/api')
      vi.mocked(api.auth.login).mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({
          access_token: 'token',
          refresh_token: 'refresh',
          token_type: 'bearer',
          expires_in: 3600
        }), 100))
      )

      // Fill form and submit
      await fillInput(wrapper, '[data-testid="username-input"]', 'testuser')
      await fillInput(wrapper, '[data-testid="password-input"]', 'password123')

      const loginButton = wrapper.find('[data-testid="login-button"]')
      await loginButton.trigger('click')

      // Verify loading state
      expect(loginButton.attributes('disabled')).toBeDefined()
      expect(wrapper.find('[data-testid="loading-spinner"]').exists()).toBe(true)
    })
  })

  describe('Registration Flow', () => {
    it('should complete full registration flow successfully', async () => {
      const wrapper = mountComponent(RegisterView, { router })
      const authStore = useAuthStore()
      const notificationStore = useNotificationStore()

      // Fill in registration form
      await fillInput(wrapper, '[data-testid="username-input"]', 'newuser')
      await fillInput(wrapper, '[data-testid="email-input"]', 'new@example.com')
      await fillInput(wrapper, '[data-testid="password-input"]', 'password123')
      await fillInput(wrapper, '[data-testid="confirm-password-input"]', 'password123')

      // Submit form
      await clickElement(wrapper, '[data-testid="register-button"]')

      // Wait for async operations
      await waitFor(() => authStore.user !== null)

      // Verify user is registered and logged in
      expect(authStore.isAuthenticated).toBe(true)
      expect(authStore.user?.username).toBe('newuser')
      expect(authStore.user?.email).toBe('new@example.com')

      // Verify success notification
      expect(notificationStore.notifications.some(n => 
        n.type === 'success' && n.message.includes('Account created')
      )).toBe(true)

      // Verify navigation to dashboard
      expect(router.currentRoute.value.path).toBe('/dashboard')
    })

    it('should validate password confirmation', async () => {
      const wrapper = mountComponent(RegisterView, { router })

      // Fill form with mismatched passwords
      await fillInput(wrapper, '[data-testid="username-input"]', 'newuser')
      await fillInput(wrapper, '[data-testid="email-input"]', 'new@example.com')
      await fillInput(wrapper, '[data-testid="password-input"]', 'password123')
      await fillInput(wrapper, '[data-testid="confirm-password-input"]', 'different')

      // Submit form
      await clickElement(wrapper, '[data-testid="register-button"]')

      // Verify validation error
      expect(wrapper.find('[data-testid="password-mismatch-error"]').exists()).toBe(true)
      expect(wrapper.text()).toContain('Passwords do not match')
    })

    it('should handle registration errors', async () => {
      const wrapper = mountComponent(RegisterView, { router })
      const authStore = useAuthStore()
      const notificationStore = useNotificationStore()

      // Mock API to return error
      const { api } = await import('@/utils/api')
      vi.mocked(api.auth.register).mockRejectedValue(new Error('Username already exists'))

      // Fill in form
      await fillInput(wrapper, '[data-testid="username-input"]', 'existing')
      await fillInput(wrapper, '[data-testid="email-input"]', 'existing@example.com')
      await fillInput(wrapper, '[data-testid="password-input"]', 'password123')
      await fillInput(wrapper, '[data-testid="confirm-password-input"]', 'password123')

      // Submit form
      await clickElement(wrapper, '[data-testid="register-button"]')

      // Wait for error handling
      await waitFor(() => authStore.error !== null)

      // Verify error state
      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.error).toBe('Username already exists')

      // Verify error notification
      expect(notificationStore.notifications.some(n => n.type === 'error')).toBe(true)
    })
  })

  describe('Authentication Guard', () => {
    it('should redirect unauthenticated users to login', async () => {
      router.push('/dashboard')
      await router.isReady()

      const wrapper = mountComponent(DashboardView, { router })
      
      // Should redirect to login
      expect(router.currentRoute.value.path).toBe('/login')
    })

    it('should allow authenticated users to access protected routes', async () => {
      const authStore = useAuthStore()
      
      // Mock authenticated state
      authStore.user = {
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        is_active: true
      }

      router.push('/dashboard')
      await router.isReady()

      const wrapper = mountComponent(DashboardView, { router })
      
      // Should stay on dashboard
      expect(router.currentRoute.value.path).toBe('/dashboard')
      expect(wrapper.find('[data-testid="dashboard-content"]').exists()).toBe(true)
    })
  })

  describe('Logout Flow', () => {
    it('should complete logout flow successfully', async () => {
      const authStore = useAuthStore()
      const notificationStore = useNotificationStore()

      // Set initial authenticated state
      authStore.user = {
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        is_active: true
      }

      router.push('/dashboard')
      await router.isReady()

      const wrapper = mountComponent(DashboardView, { router })

      // Trigger logout
      await clickElement(wrapper, '[data-testid="logout-button"]')

      // Wait for logout to complete
      await waitFor(() => authStore.user === null)

      // Verify user is logged out
      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.user).toBeNull()

      // Verify logout notification
      expect(notificationStore.notifications.some(n => 
        n.type === 'info' && n.message.includes('logged out')
      )).toBe(true)

      // Verify navigation to login
      expect(router.currentRoute.value.path).toBe('/login')
    })
  })

  describe('Session Persistence', () => {
    it('should restore session on app reload', async () => {
      const authStore = useAuthStore()

      // Mock existing tokens in storage
      const apiClient = await import('@/utils/api')
      vi.mocked(apiClient.default.isAuthenticated).mockReturnValue(true)
      vi.mocked(apiClient.api.auth.getProfile).mockResolvedValue({
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        is_active: true
      })

      // Initialize auth (simulates app startup)
      await authStore.initializeAuth()

      // Verify session is restored
      expect(authStore.isAuthenticated).toBe(true)
      expect(authStore.user?.username).toBe('testuser')
    })

    it('should handle invalid tokens gracefully', async () => {
      const authStore = useAuthStore()

      // Mock invalid tokens
      const apiClient = await import('@/utils/api')
      vi.mocked(apiClient.default.isAuthenticated).mockReturnValue(true)
      vi.mocked(apiClient.api.auth.getProfile).mockRejectedValue({
        response: { status: 401 },
        message: 'Token expired'
      })

      // Initialize auth
      await expect(authStore.initializeAuth()).rejects.toThrow()

      // Verify user is logged out
      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.user).toBeNull()
    })
  })
})