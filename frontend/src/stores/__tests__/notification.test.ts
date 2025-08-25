/**
 * Notification store tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useNotificationStore } from '../notification'

describe('Notification Store', () => {
  let notificationStore: ReturnType<typeof useNotificationStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    notificationStore = useNotificationStore()
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should have empty notifications array', () => {
      expect(notificationStore.notifications).toEqual([])
    })

    it('should have correct initial settings', () => {
      expect(notificationStore.settings.enabled).toBe(true)
      expect(notificationStore.settings.sound).toBe(true)
      expect(notificationStore.settings.desktop).toBe(true)
    })
  })

  describe('Add Notification', () => {
    it('should add notification with correct properties', () => {
      const notification = {
        message: 'Test notification',
        type: 'info' as const
      }

      notificationStore.addNotification(notification)

      expect(notificationStore.notifications).toHaveLength(1)
      expect(notificationStore.notifications[0]).toMatchObject({
        message: 'Test notification',
        type: 'info'
      })
      expect(notificationStore.notifications[0].id).toBeDefined()
      expect(notificationStore.notifications[0].timestamp).toBeDefined()
    })

    it('should add notification with custom duration', () => {
      const notification = {
        message: 'Custom duration',
        type: 'warning' as const,
        duration: 10000
      }

      notificationStore.addNotification(notification)

      expect(notificationStore.notifications[0].duration).toBe(10000)
    })

    it('should add persistent notification', () => {
      const notification = {
        message: 'Persistent notification',
        type: 'error' as const,
        persistent: true
      }

      notificationStore.addNotification(notification)

      expect(notificationStore.notifications[0].persistent).toBe(true)
    })
  })

  describe('Remove Notification', () => {
    it('should remove notification by id', () => {
      const notification1 = { message: 'First', type: 'info' as const }
      const notification2 = { message: 'Second', type: 'success' as const }

      notificationStore.addNotification(notification1)
      notificationStore.addNotification(notification2)

      const firstId = notificationStore.notifications[0].id
      notificationStore.removeNotification(firstId)

      expect(notificationStore.notifications).toHaveLength(1)
      expect(notificationStore.notifications[0].message).toBe('Second')
    })

    it('should handle removing non-existent notification', () => {
      notificationStore.addNotification({ message: 'Test', type: 'info' })
      
      expect(() => {
        notificationStore.removeNotification('non-existent-id')
      }).not.toThrow()

      expect(notificationStore.notifications).toHaveLength(1)
    })
  })

  describe('Clear Notifications', () => {
    it('should clear all notifications', () => {
      notificationStore.addNotification({ message: 'First', type: 'info' })
      notificationStore.addNotification({ message: 'Second', type: 'success' })

      expect(notificationStore.notifications).toHaveLength(2)

      notificationStore.clearAll()

      expect(notificationStore.notifications).toHaveLength(0)
    })
  })

  describe('Update Settings', () => {
    it('should update notification settings', () => {
      const newSettings = {
        enabled: false,
        sound: false,
        desktop: true
      }

      notificationStore.updateSettings(newSettings)

      expect(notificationStore.settings).toEqual(newSettings)
    })

    it('should partially update settings', () => {
      notificationStore.updateSettings({ sound: false })

      expect(notificationStore.settings.sound).toBe(false)
      expect(notificationStore.settings.enabled).toBe(true)
      expect(notificationStore.settings.desktop).toBe(true)
    })
  })

  describe('Convenience Methods', () => {
    it('should add success notification', () => {
      notificationStore.success('Success message')

      expect(notificationStore.notifications[0].type).toBe('success')
      expect(notificationStore.notifications[0].message).toBe('Success message')
    })

    it('should add error notification', () => {
      notificationStore.error('Error message')

      expect(notificationStore.notifications[0].type).toBe('error')
      expect(notificationStore.notifications[0].message).toBe('Error message')
    })

    it('should add warning notification', () => {
      notificationStore.warning('Warning message')

      expect(notificationStore.notifications[0].type).toBe('warning')
      expect(notificationStore.notifications[0].message).toBe('Warning message')
    })

    it('should add info notification', () => {
      notificationStore.info('Info message')

      expect(notificationStore.notifications[0].type).toBe('info')
      expect(notificationStore.notifications[0].message).toBe('Info message')
    })
  })

  describe('Auto-remove Timer', () => {
    it('should auto-remove non-persistent notifications', () => {
      vi.useFakeTimers()
      
      notificationStore.addNotification({
        message: 'Auto-remove test',
        type: 'info',
        duration: 1000
      })

      expect(notificationStore.notifications).toHaveLength(1)

      vi.advanceTimersByTime(1000)

      expect(notificationStore.notifications).toHaveLength(0)

      vi.useRealTimers()
    })

    it('should not auto-remove persistent notifications', () => {
      vi.useFakeTimers()
      
      notificationStore.addNotification({
        message: 'Persistent test',
        type: 'error',
        persistent: true,
        duration: 1000
      })

      expect(notificationStore.notifications).toHaveLength(1)

      vi.advanceTimersByTime(5000)

      expect(notificationStore.notifications).toHaveLength(1)

      vi.useRealTimers()
    })
  })
})