<template>
  <div
    aria-live="assertive"
    class="fixed inset-0 flex items-end px-4 py-6 pointer-events-none sm:p-6 sm:items-start z-50"
  >
    <div class="w-full flex flex-col items-center space-y-4 sm:items-end">
      <!-- Notification -->
      <transition-group
        enter-active-class="transform ease-out duration-300 transition"
        enter-from-class="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
        enter-to-class="translate-y-0 opacity-100 sm:translate-x-0"
        leave-active-class="transition ease-in duration-100"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
        tag="div"
        class="w-full flex flex-col items-center space-y-4 sm:items-end"
      >
        <div
          v-for="notification in notifications"
          :key="notification.id"
          class="max-w-sm w-full bg-white shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden"
        >
          <div class="p-4">
            <div class="flex items-start">
              <div class="flex-shrink-0">
                <CheckCircleIcon
                  v-if="notification.type === 'success'"
                  class="h-6 w-6 text-green-400"
                />
                <XCircleIcon
                  v-else-if="notification.type === 'error'"
                  class="h-6 w-6 text-red-400"
                />
                <ExclamationTriangleIcon
                  v-else-if="notification.type === 'warning'"
                  class="h-6 w-6 text-yellow-400"
                />
                <InformationCircleIcon
                  v-else
                  class="h-6 w-6 text-blue-400"
                />
              </div>
              <div class="ml-3 w-0 flex-1 pt-0.5">
                <p class="text-sm font-medium text-gray-900">
                  {{ notification.title }}
                </p>
                <p class="mt-1 text-sm text-gray-500">
                  {{ notification.message }}
                </p>
                <div v-if="notification.actions" class="mt-3 flex space-x-7">
                  <button
                    v-for="action in notification.actions"
                    :key="action.label"
                    @click="handleAction(action, notification)"
                    class="bg-white rounded-md text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2"
                    :class="action.primary 
                      ? 'text-primary-600 hover:text-primary-500 focus:ring-primary-500' 
                      : 'text-gray-700 hover:text-gray-500 focus:ring-gray-500'"
                  >
                    {{ action.label }}
                  </button>
                </div>
              </div>
              <div class="ml-4 flex-shrink-0 flex">
                <button
                  @click="removeNotification(notification.id)"
                  class="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  <span class="sr-only">Close</span>
                  <XMarkIcon class="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
          
          <!-- Progress bar for timed notifications -->
          <div
            v-if="notification.duration > 0"
            class="h-1 bg-gray-200"
          >
            <div
              class="h-1 transition-all ease-linear"
              :class="getProgressBarClass(notification.type)"
              :style="{ 
                width: `${getProgressPercentage(notification)}%`,
                transitionDuration: `${notification.duration}ms` 
              }"
            ></div>
          </div>
        </div>
      </transition-group>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import {
  CheckCircle as CheckCircleIcon,
  XCircle as XCircleIcon,
  AlertTriangle as ExclamationTriangleIcon,
  Info as InformationCircleIcon,
  X as XMarkIcon,
} from 'lucide-vue-next'

import { useNotificationStore } from '@/stores/notification'
import type { NotificationState, NotificationAction } from '@/types'

const notificationStore = useNotificationStore()

// Computed
const notifications = computed(() => notificationStore.notifications)

// Methods
const removeNotification = (id: string) => {
  notificationStore.removeNotification(id)
}

const handleAction = (action: NotificationAction, notification: NotificationState) => {
  if (action.handler) {
    action.handler(notification)
  }
  
  // Remove notification after action unless specified otherwise
  if (action.dismissOnAction !== false) {
    removeNotification(notification.id)
  }
}

const getProgressBarClass = (type: string) => {
  switch (type) {
    case 'success':
      return 'bg-green-400'
    case 'error':
      return 'bg-red-400'
    case 'warning':
      return 'bg-yellow-400'
    case 'info':
      return 'bg-blue-400'
    default:
      return 'bg-gray-400'
  }
}

const getProgressPercentage = (notification: NotificationState) => {
  if (!notification.duration || notification.duration <= 0) return 0
  
  // This is a simplified approach - in a real implementation you'd track
  // the actual time elapsed since the notification was created
  const elapsed = Date.now() - new Date(notification.id.split('-')[1]).getTime()
  const percentage = Math.max(0, Math.min(100, (elapsed / notification.duration) * 100))
  return 100 - percentage
}

// Keyboard shortcuts
const handleKeydown = (event: KeyboardEvent) => {
  // ESC to clear all notifications
  if (event.key === 'Escape') {
    notificationStore.clear()
  }
}

// Lifecycle
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>