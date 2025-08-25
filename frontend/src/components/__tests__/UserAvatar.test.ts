/**
 * UserAvatar component tests
 */

import { describe, it, expect } from 'vitest'
import { mountComponent, mockUser } from '@/test/utils'
import UserAvatar from '../UserAvatar.vue'

describe('UserAvatar Component', () => {
  describe('Rendering', () => {
    it('should render user initials when no image provided', () => {
      const wrapper = mountComponent(UserAvatar, {
        props: {
          user: mockUser,
          size: 'md'
        }
      })

      expect(wrapper.find('[data-testid="user-initials"]').text()).toBe('TU')
      expect(wrapper.find('img').exists()).toBe(false)
    })

    it('should render user image when provided', () => {
      const userWithImage = {
        ...mockUser,
        avatar_url: 'https://example.com/avatar.jpg'
      }

      const wrapper = mountComponent(UserAvatar, {
        props: {
          user: userWithImage,
          size: 'md'
        }
      })

      const img = wrapper.find('img')
      expect(img.exists()).toBe(true)
      expect(img.attributes('src')).toBe('https://example.com/avatar.jpg')
      expect(img.attributes('alt')).toBe('testuser')
    })

    it('should fallback to initials when image fails to load', async () => {
      const userWithImage = {
        ...mockUser,
        avatar_url: 'https://example.com/broken-image.jpg'
      }

      const wrapper = mountComponent(UserAvatar, {
        props: {
          user: userWithImage,
          size: 'md'
        }
      })

      const img = wrapper.find('img')
      await img.trigger('error')

      expect(wrapper.find('[data-testid="user-initials"]').exists()).toBe(true)
      expect(wrapper.find('img').exists()).toBe(false)
    })
  })

  describe('Size Variants', () => {
    it('should apply correct classes for small size', () => {
      const wrapper = mountComponent(UserAvatar, {
        props: {
          user: mockUser,
          size: 'sm'
        }
      })

      expect(wrapper.classes()).toContain('h-8')
      expect(wrapper.classes()).toContain('w-8')
      expect(wrapper.classes()).toContain('text-sm')
    })

    it('should apply correct classes for medium size', () => {
      const wrapper = mountComponent(UserAvatar, {
        props: {
          user: mockUser,
          size: 'md'
        }
      })

      expect(wrapper.classes()).toContain('h-10')
      expect(wrapper.classes()).toContain('w-10')
      expect(wrapper.classes()).toContain('text-base')
    })

    it('should apply correct classes for large size', () => {
      const wrapper = mountComponent(UserAvatar, {
        props: {
          user: mockUser,
          size: 'lg'
        }
      })

      expect(wrapper.classes()).toContain('h-12')
      expect(wrapper.classes()).toContain('w-12')
      expect(wrapper.classes()).toContain('text-lg')
    })

    it('should apply correct classes for extra large size', () => {
      const wrapper = mountComponent(UserAvatar, {
        props: {
          user: mockUser,
          size: 'xl'
        }
      })

      expect(wrapper.classes()).toContain('h-16')
      expect(wrapper.classes()).toContain('w-16')
      expect(wrapper.classes()).toContain('text-xl')
    })
  })

  describe('Initials Generation', () => {
    it('should generate initials from username', () => {
      const user = {
        ...mockUser,
        username: 'john_doe'
      }

      const wrapper = mountComponent(UserAvatar, {
        props: { user, size: 'md' }
      })

      expect(wrapper.find('[data-testid="user-initials"]').text()).toBe('JD')
    })

    it('should handle single name', () => {
      const user = {
        ...mockUser,
        username: 'admin'
      }

      const wrapper = mountComponent(UserAvatar, {
        props: { user, size: 'md' }
      })

      expect(wrapper.find('[data-testid="user-initials"]').text()).toBe('AD')
    })

    it('should handle names with special characters', () => {
      const user = {
        ...mockUser,
        username: 'user@example.com'
      }

      const wrapper = mountComponent(UserAvatar, {
        props: { user, size: 'md' }
      })

      expect(wrapper.find('[data-testid="user-initials"]').text()).toBe('UE')
    })

    it('should handle empty or invalid usernames', () => {
      const user = {
        ...mockUser,
        username: ''
      }

      const wrapper = mountComponent(UserAvatar, {
        props: { user, size: 'md' }
      })

      expect(wrapper.find('[data-testid="user-initials"]').text()).toBe('??')
    })
  })

  describe('Accessibility', () => {
    it('should have proper alt text for images', () => {
      const userWithImage = {
        ...mockUser,
        avatar_url: 'https://example.com/avatar.jpg'
      }

      const wrapper = mountComponent(UserAvatar, {
        props: {
          user: userWithImage,
          size: 'md'
        }
      })

      const img = wrapper.find('img')
      expect(img.attributes('alt')).toBe('testuser')
    })

    it('should have proper title attribute', () => {
      const wrapper = mountComponent(UserAvatar, {
        props: {
          user: mockUser,
          size: 'md'
        }
      })

      expect(wrapper.attributes('title')).toBe('testuser')
    })
  })

  describe('Online Status', () => {
    it('should show online indicator when user is online', () => {
      const wrapper = mountComponent(UserAvatar, {
        props: {
          user: mockUser,
          size: 'md',
          showOnlineStatus: true,
          isOnline: true
        }
      })

      const indicator = wrapper.find('[data-testid="online-indicator"]')
      expect(indicator.exists()).toBe(true)
      expect(indicator.classes()).toContain('bg-green-400')
    })

    it('should show offline indicator when user is offline', () => {
      const wrapper = mountComponent(UserAvatar, {
        props: {
          user: mockUser,
          size: 'md',
          showOnlineStatus: true,
          isOnline: false
        }
      })

      const indicator = wrapper.find('[data-testid="online-indicator"]')
      expect(indicator.exists()).toBe(true)
      expect(indicator.classes()).toContain('bg-gray-400')
    })

    it('should not show online status by default', () => {
      const wrapper = mountComponent(UserAvatar, {
        props: {
          user: mockUser,
          size: 'md'
        }
      })

      const indicator = wrapper.find('[data-testid="online-indicator"]')
      expect(indicator.exists()).toBe(false)
    })
  })
})