/**
 * NotificationContainer component tests
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { mountComponent, clickElement, nextTick } from '@/test/utils'
import { useNotificationStore } from '@/stores/notification'
import NotificationContainer from '../NotificationContainer.vue'

describe('NotificationContainer Component', () => {
  let notificationStore: ReturnType<typeof useNotificationStore>

  beforeEach(() => {
    const wrapper = mountComponent(NotificationContainer)
    notificationStore = useNotificationStore()
    notificationStore.clearAll()
  })

  describe('Rendering', () => {
    it('should render empty when no notifications', () => {
      const wrapper = mountComponent(NotificationContainer)
      
      expect(wrapper.find('[data-testid="notification-item"]').exists()).toBe(false)
    })

    it('should render notification items', async () => {
      notificationStore.addNotification({
        message: 'Test notification',
        type: 'info'
      })

      const wrapper = mountComponent(NotificationContainer)
      await nextTick()

      expect(wrapper.find('[data-testid="notification-item"]').exists()).toBe(true)
      expect(wrapper.text()).toContain('Test notification')
    })

    it('should render multiple notifications', async () => {
      notificationStore.addNotification({ message: 'First', type: 'info' })
      notificationStore.addNotification({ message: 'Second', type: 'success' })

      const wrapper = mountComponent(NotificationContainer)
      await nextTick()

      const notifications = wrapper.findAll('[data-testid="notification-item"]')
      expect(notifications).toHaveLength(2)
    })
  })

  describe('Notification Types', () => {
    it('should apply correct styling for success notifications', async () => {
      notificationStore.addNotification({
        message: 'Success message',
        type: 'success'
      })

      const wrapper = mountComponent(NotificationContainer)
      await nextTick()

      const notification = wrapper.find('[data-testid="notification-item"]')
      expect(notification.classes()).toContain('bg-green-50')
      expect(notification.classes()).toContain('border-green-200')
    })

    it('should apply correct styling for error notifications', async () => {
      notificationStore.addNotification({
        message: 'Error message',
        type: 'error'
      })

      const wrapper = mountComponent(NotificationContainer)
      await nextTick()

      const notification = wrapper.find('[data-testid="notification-item"]')
      expect(notification.classes()).toContain('bg-red-50')
      expect(notification.classes()).toContain('border-red-200')
    })

    it('should apply correct styling for warning notifications', async () => {
      notificationStore.addNotification({
        message: 'Warning message',
        type: 'warning'
      })

      const wrapper = mountComponent(NotificationContainer)
      await nextTick()

      const notification = wrapper.find('[data-testid="notification-item"]')
      expect(notification.classes()).toContain('bg-yellow-50')
      expect(notification.classes()).toContain('border-yellow-200')
    })

    it('should apply correct styling for info notifications', async () => {
      notificationStore.addNotification({
        message: 'Info message',
        type: 'info'
      })

      const wrapper = mountComponent(NotificationContainer)
      await nextTick()

      const notification = wrapper.find('[data-testid="notification-item"]')
      expect(notification.classes()).toContain('bg-blue-50')
      expect(notification.classes()).toContain('border-blue-200')
    })
  })

  describe('Notification Icons', () => {
    it('should display correct icon for success notifications', async () => {
      notificationStore.addNotification({
        message: 'Success message',
        type: 'success'
      })

      const wrapper = mountComponent(NotificationContainer)
      await nextTick()

      const icon = wrapper.find('[data-testid="success-icon"]')
      expect(icon.exists()).toBe(true)
    })

    it('should display correct icon for error notifications', async () => {
      notificationStore.addNotification({
        message: 'Error message',
        type: 'error'
      })

      const wrapper = mountComponent(NotificationContainer)
      await nextTick()

      const icon = wrapper.find('[data-testid="error-icon"]')
      expect(icon.exists()).toBe(true)
    })

    it('should display correct icon for warning notifications', async () => {
      notificationStore.addNotification({
        message: 'Warning message',
        type: 'warning'
      })

      const wrapper = mountComponent(NotificationContainer)
      await nextTick()

      const icon = wrapper.find('[data-testid="warning-icon"]')
      expect(icon.exists()).toBe(true)
    })

    it('should display correct icon for info notifications', async () => {
      notificationStore.addNotification({
        message: 'Info message',
        type: 'info'
      })

      const wrapper = mountComponent(NotificationContainer)
      await nextTick()

      const icon = wrapper.find('[data-testid="info-icon"]')
      expect(icon.exists()).toBe(true)
    })
  })

  describe('Notification Actions', () => {
    it('should remove notification when close button is clicked', async () => {
      notificationStore.addNotification({
        message: 'Test notification',
        type: 'info'
      })

      const wrapper = mountComponent(NotificationContainer)
      await nextTick()

      expect(wrapper.find('[data-testid="notification-item"]').exists()).toBe(true)

      await clickElement(wrapper, '[data-testid="close-button"]')
      await nextTick()

      expect(wrapper.find('[data-testid="notification-item"]').exists()).toBe(false)
      expect(notificationStore.notifications).toHaveLength(0)
    })

    it('should show action button for notifications with actions', async () => {
      notificationStore.addNotification({
        message: 'Notification with action',
        type: 'info',
        action: {
          label: 'Retry',
          callback: () => {}
        }
      })

      const wrapper = mountComponent(NotificationContainer)
      await nextTick()

      const actionButton = wrapper.find('[data-testid="action-button"]')
      expect(actionButton.exists()).toBe(true)
      expect(actionButton.text()).toBe('Retry')
    })

    it('should call action callback when action button is clicked', async () => {
      let actionCalled = false
      const actionCallback = () => {
        actionCalled = true
      }

      notificationStore.addNotification({
        message: 'Notification with action',
        type: 'info',
        action: {
          label: 'Test Action',
          callback: actionCallback
        }
      })

      const wrapper = mountComponent(NotificationContainer)
      await nextTick()

      await clickElement(wrapper, '[data-testid="action-button"]')

      expect(actionCalled).toBe(true)
    })
  })

  describe('Persistent Notifications', () => {
    it('should not show close button for persistent notifications', async () => {
      notificationStore.addNotification({
        message: 'Persistent notification',
        type: 'error',
        persistent: true
      })

      const wrapper = mountComponent(NotificationContainer)
      await nextTick()

      const closeButton = wrapper.find('[data-testid="close-button"]')
      expect(closeButton.exists()).toBe(false)
    })

    it('should show close button for non-persistent notifications', async () => {
      notificationStore.addNotification({
        message: 'Regular notification',
        type: 'info',
        persistent: false
      })

      const wrapper = mountComponent(NotificationContainer)
      await nextTick()

      const closeButton = wrapper.find('[data-testid="close-button"]')
      expect(closeButton.exists()).toBe(true)
    })
  })

  describe('Animation and Transitions', () => {
    it('should have transition classes', () => {
      const wrapper = mountComponent(NotificationContainer)
      
      const container = wrapper.find('[data-testid="notifications-container"]')
      expect(container.classes()).toContain('transition-all')
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', async () => {
      notificationStore.addNotification({
        message: 'Test notification',
        type: 'info'
      })

      const wrapper = mountComponent(NotificationContainer)
      await nextTick()

      const notification = wrapper.find('[data-testid="notification-item"]')
      expect(notification.attributes('role')).toBe('alert')
      expect(notification.attributes('aria-live')).toBe('polite')
    })

    it('should have proper ARIA attributes for error notifications', async () => {
      notificationStore.addNotification({
        message: 'Error notification',
        type: 'error'
      })

      const wrapper = mountComponent(NotificationContainer)
      await nextTick()

      const notification = wrapper.find('[data-testid="notification-item"]')
      expect(notification.attributes('aria-live')).toBe('assertive')
    })

    it('should have accessible close button', async () => {
      notificationStore.addNotification({
        message: 'Test notification',
        type: 'info'
      })

      const wrapper = mountComponent(NotificationContainer)
      await nextTick()

      const closeButton = wrapper.find('[data-testid="close-button"]')
      expect(closeButton.attributes('aria-label')).toBe('Close notification')
    })
  })
})