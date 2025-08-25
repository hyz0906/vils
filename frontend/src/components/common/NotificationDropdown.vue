<template>
  <div class="relative" ref="dropdownRef">
    <button
      @click="toggleDropdown"
      class="p-2 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded-full relative"
    >
      <span class="sr-only">View notifications</span>
      <BellIcon class="h-6 w-6" />
      
      <!-- Notification badge -->
      <span
        v-if="unreadCount > 0"
        class="absolute -top-0.5 -right-0.5 h-4 w-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-medium"
      >
        {{ unreadCount > 9 ? '9+' : unreadCount }}
      </span>
    </button>

    <!-- Dropdown menu -->
    <transition
      enter-active-class="transition ease-out duration-100"
      enter-from-class="transform opacity-0 scale-95"
      enter-to-class="transform opacity-100 scale-100"
      leave-active-class="transition ease-in duration-75"
      leave-from-class="transform opacity-100 scale-100"
      leave-to-class="transform opacity-0 scale-95"
    >
      <div
        v-if="isDropdownOpen"
        class="origin-top-right absolute right-0 mt-2 w-80 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-50"
      >
        <div class="max-h-96 overflow-y-auto">
          <!-- Header -->
          <div class="px-4 py-3 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-medium text-gray-900">
                Notifications
              </h3>
              <div class="flex items-center space-x-2">
                <button
                  v-if="unreadCount > 0"
                  @click="markAllAsRead"
                  class="text-xs text-primary-600 hover:text-primary-500"
                >
                  Mark all read
                </button>
                <button
                  @click="clearAll"
                  class="text-xs text-gray-500 hover:text-gray-700"
                >
                  Clear all
                </button>
              </div>
            </div>
          </div>

          <!-- Notifications list -->
          <div v-if="notifications.length === 0" class="px-4 py-8 text-center">
            <BellIcon class="mx-auto h-8 w-8 text-gray-400" />
            <p class="mt-2 text-sm text-gray-500">No notifications</p>
          </div>
          
          <div v-else class="divide-y divide-gray-200">
            <div
              v-for="notification in notifications"
              :key="notification.id"
              class="px-4 py-3 hover:bg-gray-50 transition-colors duration-150"
              :class="{ 'bg-blue-50': !notification.read }"
            >
              <div class="flex items-start space-x-3">
                <div class="flex-shrink-0">
                  <div
                    class="h-8 w-8 rounded-full flex items-center justify-center"
                    :class="getNotificationIconClass(notification.type)"
                  >
                    <component :is="getNotificationIcon(notification.type)" class="h-4 w-4 text-white" />
                  </div>
                </div>
                
                <div class="flex-1 min-w-0">
                  <div class="flex items-center justify-between">
                    <p class="text-sm font-medium text-gray-900 truncate">
                      {{ notification.title }}
                    </p>
                    <button
                      @click="removeNotification(notification.id)"
                      class="flex-shrink-0 text-gray-400 hover:text-gray-500"
                    >
                      <XMarkIcon class="h-4 w-4" />
                    </button>
                  </div>
                  <p class="text-sm text-gray-600 mt-1">
                    {{ notification.message }}
                  </p>
                  <div class="flex items-center justify-between mt-2">
                    <p class="text-xs text-gray-500">
                      {{ formatNotificationTime(notification.timestamp) }}
                    </p>
                    <div v-if="!notification.read" class="flex">
                      <button
                        @click="markAsRead(notification.id)"
                        class="text-xs text-primary-600 hover:text-primary-500"
                      >
                        Mark as read
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="px-4 py-3 border-t border-gray-200">
            <router-link
              to="/notifications"
              @click="closeDropdown"
              class="block text-center text-sm text-primary-600 hover:text-primary-500"
            >
              View all notifications
            </router-link>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  Bell as BellIcon,
  CheckCircle as CheckCircleIcon,
  XCircle as XCircleIcon,
  ExclamationTriangle as ExclamationTriangleIcon,
  InformationCircle as InformationCircleIcon,
  XMark as XMarkIcon,
} from 'lucide-vue-next'

import { useNotificationStore } from '@/stores/notification'

interface DropdownNotification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  timestamp: string
  read: boolean
}

const notificationStore = useNotificationStore()
const dropdownRef = ref<HTMLElement>()
const isDropdownOpen = ref(false)

// Mock notification data - in production this would come from an API or store
const notifications = ref<DropdownNotification[]>([
  {
    id: '1',
    type: 'success',
    title: 'Task Completed',
    message: 'Binary search localization for Project Alpha completed successfully.',
    timestamp: new Date(Date.now() - 300000).toISOString(), // 5 minutes ago
    read: false
  },
  {
    id: '2',
    type: 'info',
    title: 'New Project Created',
    message: 'Project Beta has been created and is ready for configuration.',
    timestamp: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
    read: false
  },
  {
    id: '3',
    type: 'warning',
    title: 'Build Issue',
    message: 'Build #42 for Project Gamma failed. Check the logs for details.',
    timestamp: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
    read: true
  }
])

// Computed
const unreadCount = computed(() => {
  return notifications.value.filter(n => !n.read).length
})

// Methods
const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

const closeDropdown = () => {
  isDropdownOpen.value = false
}

const removeNotification = (id: string) => {
  const index = notifications.value.findIndex(n => n.id === id)
  if (index > -1) {
    notifications.value.splice(index, 1)
  }
}

const markAsRead = (id: string) => {
  const notification = notifications.value.find(n => n.id === id)
  if (notification) {
    notification.read = true
  }
}

const markAllAsRead = () => {
  notifications.value.forEach(n => n.read = true)
}

const clearAll = () => {
  notifications.value = []
}

const getNotificationIcon = (type: string) => {
  switch (type) {
    case 'success':
      return CheckCircleIcon
    case 'error':
      return XCircleIcon
    case 'warning':
      return ExclamationTriangleIcon
    case 'info':
      return InformationCircleIcon
    default:
      return InformationCircleIcon
  }
}

const getNotificationIconClass = (type: string) => {
  switch (type) {
    case 'success':
      return 'bg-green-500'
    case 'error':
      return 'bg-red-500'
    case 'warning':
      return 'bg-yellow-500'
    case 'info':
      return 'bg-blue-500'
    default:
      return 'bg-gray-500'
  }
}

const formatNotificationTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  // Less than 1 minute
  if (diff < 60000) return 'Just now'
  
  // Less than 1 hour
  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000)
    return `${minutes}m ago`
  }
  
  // Less than 1 day
  if (diff < 86400000) {
    const hours = Math.floor(diff / 3600000)
    return `${hours}h ago`
  }
  
  // Less than 1 week
  if (diff < 604800000) {
    const days = Math.floor(diff / 86400000)
    return `${days}d ago`
  }
  
  // Format as date
  return date.toLocaleDateString()
}

// Click outside handler
const handleClickOutside = (event: Event) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    closeDropdown()
  }
}

// Lifecycle
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>