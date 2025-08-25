/**
 * Notification store for managing toast notifications
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { NotificationState } from '@/types'

interface NotificationSettings {
  enabled: boolean
  sound: boolean
  desktop: boolean
}

export const useNotificationStore = defineStore('notification', () => {
  // State
  const notifications = ref<NotificationState[]>([])
  const settings = ref<NotificationSettings>({
    enabled: true,
    sound: true,
    desktop: true
  })
  const nextId = ref(0)

  // Actions
  const addNotification = (notification: Omit<NotificationState, 'id'>): string => {
    const id = `notification-${nextId.value++}`
    const newNotification: NotificationState = {
      ...notification,
      id,
      duration: notification.duration ?? (notification.persistent ? undefined : (notification.type === 'error' ? 8000 : 5000)),
      timestamp: new Date().toISOString()
    }

    notifications.value.push(newNotification)

    // Auto-remove after duration if not persistent
    if (!notification.persistent && newNotification.duration) {
      setTimeout(() => {
        removeNotification(id)
      }, newNotification.duration)
    }

    return id
  }

  const removeNotification = (id: string): void => {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }

  const clearAll = (): void => {
    notifications.value = []
  }

  const clearError = (): void => {
    // Clear error state - this is for the auth store compatibility
    // The notification store doesn't have an error state
  }

  const updateSettings = (newSettings: Partial<NotificationSettings>): void => {
    settings.value = { ...settings.value, ...newSettings }
  }

  // Convenience methods
  const success = (message: string, options?: Partial<NotificationState>) => {
    return addNotification({ 
      type: 'success', 
      title: 'Success', 
      message,
      ...options 
    })
  }

  const error = (message: string, options?: Partial<NotificationState>) => {
    return addNotification({ 
      type: 'error', 
      title: 'Error', 
      message,
      ...options 
    })
  }

  const warning = (message: string, options?: Partial<NotificationState>) => {
    return addNotification({ 
      type: 'warning', 
      title: 'Warning', 
      message,
      ...options 
    })
  }

  const info = (message: string, options?: Partial<NotificationState>) => {
    return addNotification({ 
      type: 'info', 
      title: 'Info', 
      message,
      ...options 
    })
  }

  return {
    // State
    notifications,
    settings,
    
    // Actions
    addNotification,
    removeNotification,
    clearAll,
    clearError,
    updateSettings,
    
    // Convenience methods
    success,
    error,
    warning,
    info,
  }
})