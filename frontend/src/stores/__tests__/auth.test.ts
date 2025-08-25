/**
 * Auth store tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../auth'
import { mockUser, mockApiResponse, mockApiError } from '@/test/utils'

// Mock the API
vi.mock('@/utils/api', () => ({
  default: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    getProfile: vi.fn(),
    refreshToken: vi.fn(),
    changePassword: vi.fn(),
    storeTokens: vi.fn(),
    clearTokens: vi.fn(),
    setAuthToken: vi.fn(),
    removeAuthToken: vi.fn(),
    isAuthenticated: vi.fn(() => false)
  },
  api: {
    auth: {
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      getProfile: vi.fn(),
      refresh: vi.fn(),
      changePassword: vi.fn()
    }
  }
}))

describe('Auth Store', () => {
  let authStore: ReturnType<typeof useAuthStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    authStore = useAuthStore()
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      expect(authStore.user).toBeNull()
      expect(authStore.isLoading).toBe(false)
      expect(authStore.error).toBeNull()
      expect(authStore.isAuthenticated).toBe(false)
    })
  })

  describe('Login', () => {
    it('should login successfully', async () => {
      const credentials = { username: 'testuser', password: 'password' }
      const tokens = {
        access_token: 'test-token',
        refresh_token: 'refresh-token',
        token_type: 'bearer',
        expires_in: 3600
      }

      const { api } = await import('@/utils/api')
      vi.mocked(api.auth.login).mockResolvedValue(tokens)
      vi.mocked(api.auth.getProfile).mockResolvedValue(mockUser)

      await authStore.login(credentials)

      expect(authStore.isLoading).toBe(false)
      expect(authStore.error).toBeNull()
      expect(authStore.user).toEqual(mockUser)
    })

    it('should handle login error', async () => {
      const credentials = { username: 'testuser', password: 'wrong' }
      const errorMessage = 'Invalid credentials'

      const { api } = await import('@/utils/api')
      vi.mocked(api.auth.login).mockRejectedValue(new Error(errorMessage))

      await expect(authStore.login(credentials)).rejects.toThrow()
      
      expect(authStore.isLoading).toBe(false)
      expect(authStore.error).toBe(errorMessage)
      expect(authStore.user).toBeNull()
    })

    it('should set loading state during login', async () => {
      const credentials = { username: 'testuser', password: 'password' }
      
      const { api } = await import('@/utils/api')
      vi.mocked(api.auth.login).mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

      const loginPromise = authStore.login(credentials)
      expect(authStore.isLoading).toBe(true)

      await loginPromise
      expect(authStore.isLoading).toBe(false)
    })
  })

  describe('Register', () => {
    it('should register successfully', async () => {
      const userData = {
        username: 'newuser',
        email: 'new@example.com',
        password: 'password'
      }

      const { api } = await import('@/utils/api')
      vi.mocked(api.auth.register).mockResolvedValue(mockUser)
      vi.mocked(api.auth.login).mockResolvedValue({
        access_token: 'token',
        refresh_token: 'refresh',
        token_type: 'bearer',
        expires_in: 3600
      })
      vi.mocked(api.auth.getProfile).mockResolvedValue(mockUser)

      await authStore.register(userData)

      expect(authStore.user).toEqual(mockUser)
      expect(authStore.error).toBeNull()
    })

    it('should handle register error', async () => {
      const userData = {
        username: 'existing',
        email: 'existing@example.com',
        password: 'password'
      }
      const errorMessage = 'User already exists'

      const { api } = await import('@/utils/api')
      vi.mocked(api.auth.register).mockRejectedValue(new Error(errorMessage))

      await expect(authStore.register(userData)).rejects.toThrow()
      
      expect(authStore.error).toBe(errorMessage)
      expect(authStore.user).toBeNull()
    })
  })

  describe('Logout', () => {
    it('should logout successfully', async () => {
      // Set initial authenticated state
      authStore.user = mockUser
      
      const { api } = await import('@/utils/api')
      vi.mocked(api.auth.logout).mockResolvedValue({})

      await authStore.logout()

      expect(authStore.user).toBeNull()
      expect(authStore.error).toBeNull()
    })

    it('should handle logout even if API call fails', async () => {
      // Set initial authenticated state
      authStore.user = mockUser
      
      const { api } = await import('@/utils/api')
      vi.mocked(api.auth.logout).mockRejectedValue(new Error('Network error'))

      await authStore.logout()

      expect(authStore.user).toBeNull()
    })
  })

  describe('Profile Management', () => {
    it('should fetch user profile', async () => {
      const { api } = await import('@/utils/api')
      vi.mocked(api.auth.getProfile).mockResolvedValue(mockUser)

      await authStore.fetchUserProfile()

      expect(authStore.user).toEqual(mockUser)
      expect(authStore.error).toBeNull()
    })

    it('should handle profile fetch error', async () => {
      const errorMessage = 'Unauthorized'
      
      const { api } = await import('@/utils/api')
      vi.mocked(api.auth.getProfile).mockRejectedValue({
        response: { status: 401 },
        message: errorMessage
      })

      await expect(authStore.fetchUserProfile()).rejects.toThrow()
      expect(authStore.error).toBe(errorMessage)
    })

    it('should logout user on 401 error', async () => {
      const { api } = await import('@/utils/api')
      vi.mocked(api.auth.getProfile).mockRejectedValue({
        response: { status: 401 },
        message: 'Unauthorized'
      })
      vi.mocked(api.auth.logout).mockResolvedValue({})

      await expect(authStore.fetchUserProfile()).rejects.toThrow()
      expect(authStore.user).toBeNull()
    })
  })

  describe('Utilities', () => {
    it('should clear error', () => {
      authStore.error = 'Some error'
      authStore.clearError()
      expect(authStore.error).toBeNull()
    })

    it('should initialize auth when tokens exist', async () => {
      const apiClient = await import('@/utils/api')
      vi.mocked(apiClient.default.isAuthenticated).mockReturnValue(true)
      vi.mocked(apiClient.api.auth.getProfile).mockResolvedValue(mockUser)

      await authStore.initializeAuth()

      expect(authStore.user).toEqual(mockUser)
    })
  })
})