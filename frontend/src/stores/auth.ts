/**
 * Authentication store using Pinia
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, AuthTokens, LoginForm, RegisterForm } from '@/types'
import { api, handleApiError } from '@/utils/api'
import apiClient from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => {
    return !!user.value && apiClient.isAuthenticated()
  })

  const hasRole = computed(() => (role: string) => {
    // Implement role-based access control if needed
    return true
  })

  // Actions
  const login = async (credentials: LoginForm): Promise<void> => {
    isLoading.value = true
    error.value = null

    try {
      const tokens: AuthTokens = await api.auth.login(credentials)
      
      // Store tokens
      apiClient.storeTokens(tokens)
      apiClient.setAuthToken(tokens.access_token)

      // Fetch user profile
      await fetchUserProfile()
      
      // Emit success event
      window.dispatchEvent(new CustomEvent('auth:login', { 
        detail: { user: user.value } 
      }))
      
    } catch (err: any) {
      error.value = handleApiError(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const register = async (userData: RegisterForm): Promise<void> => {
    isLoading.value = true
    error.value = null

    try {
      const newUser: User = await api.auth.register(userData)
      
      // Auto-login after registration
      await login({
        username: userData.username,
        password: userData.password
      })
      
    } catch (err: any) {
      error.value = handleApiError(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const logout = async (): Promise<void> => {
    isLoading.value = true

    try {
      if (isAuthenticated.value) {
        await api.auth.logout()
      }
    } catch (err) {
      // Continue with logout even if server call fails
      console.warn('Logout API call failed:', err)
    } finally {
      // Clear local state
      user.value = null
      apiClient.clearTokens()
      apiClient.removeAuthToken()
      
      // Emit logout event
      window.dispatchEvent(new CustomEvent('auth:logout'))
      
      isLoading.value = false
    }
  }

  const fetchUserProfile = async (): Promise<void> => {
    try {
      const profile: User = await api.auth.getProfile()
      user.value = profile
    } catch (err: any) {
      error.value = handleApiError(err)
      
      // If profile fetch fails, likely token is invalid
      if (err.response?.status === 401) {
        await logout()
      }
      
      throw err
    }
  }

  const refreshToken = async (): Promise<void> => {
    const refreshToken = localStorage.getItem('vils_refresh_token')
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }

    try {
      const tokens: AuthTokens = await api.auth.refresh(refreshToken)
      
      // Store new tokens
      apiClient.storeTokens(tokens)
      apiClient.setAuthToken(tokens.access_token)
      
    } catch (err: any) {
      // Refresh failed, logout user
      await logout()
      throw err
    }
  }

  const changePassword = async (currentPassword: string, newPassword: string): Promise<void> => {
    isLoading.value = true
    error.value = null

    try {
      await api.auth.changePassword(currentPassword, newPassword)
    } catch (err: any) {
      error.value = handleApiError(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const initializeAuth = async (): Promise<void> => {
    // Check if user is already authenticated
    if (apiClient.isAuthenticated() && !user.value) {
      try {
        await fetchUserProfile()
      } catch (err) {
        // If initialization fails, clear auth state
        console.warn('Auth initialization failed:', err)
        await logout()
      }
    }
  }

  const updateUserProfile = async (updates: Partial<User>): Promise<void> => {
    if (!user.value) return

    // Optimistically update local state
    const originalUser = { ...user.value }
    user.value = { ...user.value, ...updates }

    try {
      // Make API call to update profile
      // const updatedUser = await api.auth.updateProfile(updates)
      // user.value = updatedUser
    } catch (err: any) {
      // Revert optimistic update on error
      user.value = originalUser
      error.value = handleApiError(err)
      throw err
    }
  }

  const clearError = () => {
    error.value = null
  }

  // Return store interface
  return {
    // State
    user,
    isLoading,
    error,
    
    // Getters
    isAuthenticated,
    hasRole,
    
    // Actions
    login,
    register,
    logout,
    fetchUserProfile,
    refreshToken,
    changePassword,
    initializeAuth,
    updateUserProfile,
    clearError,
  }
})

// Auto-refresh token before expiration - call this after Pinia is initialized
export const setupTokenRefresh = () => {
  const authStore = useAuthStore()
  
  setInterval(async () => {
    if (authStore.isAuthenticated) {
      try {
        const token = localStorage.getItem('vils_access_token')
        if (token) {
          // Decode token to check expiration
          const payload = JSON.parse(atob(token.split('.')[1]))
          const expiresAt = payload.exp * 1000
          const now = Date.now()
          
          // Refresh if token expires within 5 minutes
          if (expiresAt - now < 5 * 60 * 1000) {
            await authStore.refreshToken()
          }
        }
      } catch (err) {
        console.warn('Token refresh check failed:', err)
      }
    }
  }, 60000) // Check every minute
}