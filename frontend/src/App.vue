<template>
  <div id="app" class="min-h-screen bg-gray-50 flex flex-col">
    <!-- Navigation Bar -->
    <NavBar v-if="shouldShowNavBar" />
    
    <!-- Main Content -->
    <main class="flex-1 flex flex-col">
      <router-view v-slot="{ Component, route }">
        <transition :name="getTransitionName(route)" mode="out-in">
          <component :is="Component" :key="route.path" />
        </transition>
      </router-view>
    </main>
    
    <!-- Global Notifications -->
    <NotificationContainer />
    
    <!-- Loading Overlay -->
    <LoadingOverlay v-if="isGlobalLoading" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import NavBar from '@/components/layout/NavBar.vue'
import NotificationContainer from '@/components/common/NotificationContainer.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import { useWebSocketStore } from '@/stores/websocket'

const route = useRoute()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()
const webSocketStore = useWebSocketStore()

// Computed properties
const shouldShowNavBar = computed(() => {
  const authRoutes = ['login', 'register']
  return !authRoutes.includes(route.name as string)
})

const isGlobalLoading = computed(() => {
  // Add global loading conditions here
  return false
})

// Transition logic
const getTransitionName = (route: any) => {
  // Simple fade transition for most routes
  if (route.meta?.transition) {
    return route.meta.transition
  }
  return 'fade'
}

// Lifecycle hooks
onMounted(async () => {
  try {
    // Initialize authentication
    await authStore.initializeAuth()
    
    // Connect WebSocket if authenticated
    if (authStore.isAuthenticated) {
      webSocketStore.connect()
    }
  } catch (error) {
    console.warn('App initialization failed:', error)
    // Continue loading the app even if auth initialization fails
  }
  
  // Listen for auth state changes
  window.addEventListener('auth:logout', handleAuthLogout)
})

onUnmounted(() => {
  // Cleanup
  window.removeEventListener('auth:logout', handleAuthLogout)
  webSocketStore.disconnect()
})

// Event handlers
const handleAuthLogout = () => {
  authStore.logout()
  webSocketStore.disconnect()
  notificationStore.clear()
}
</script>

<style scoped>
/* Transition animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from {
  transform: translateX(100%);
}

.slide-leave-to {
  transform: translateX(-100%);
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.3s ease;
}

.slide-up-enter-from {
  transform: translateY(20px);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateY(-20px);
  opacity: 0;
}
</style>