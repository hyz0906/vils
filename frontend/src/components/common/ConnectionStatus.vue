<template>
  <div class="flex items-center">
    <div
      class="flex items-center px-2 py-1 rounded-full text-xs font-medium"
      :class="statusClasses"
    >
      <div
        class="w-2 h-2 rounded-full mr-2"
        :class="indicatorClasses"
      ></div>
      <span>{{ statusText }}</span>
    </div>
    
    <!-- Tooltip for more details -->
    <div
      v-if="showTooltip"
      class="absolute top-full right-0 mt-2 w-64 bg-black text-white text-xs rounded-lg p-3 shadow-lg z-50"
      style="transform: translateX(50%)"
    >
      <div class="space-y-2">
        <div class="flex justify-between">
          <span>WebSocket:</span>
          <span :class="webSocketStore.isConnected ? 'text-green-400' : 'text-red-400'">
            {{ webSocketStore.connectionStatus }}
          </span>
        </div>
        <div class="flex justify-between">
          <span>API Status:</span>
          <span :class="apiStatus === 'healthy' ? 'text-green-400' : 'text-red-400'">
            {{ apiStatus }}
          </span>
        </div>
        <div v-if="webSocketStore.lastError" class="text-red-400">
          Error: {{ webSocketStore.lastError }}
        </div>
        <div v-if="webSocketStore.reconnectAttempts > 0" class="text-yellow-400">
          Reconnect attempts: {{ webSocketStore.reconnectAttempts }}
        </div>
        <div class="text-gray-400 text-xs pt-1 border-t border-gray-600">
          Click to {{ webSocketStore.isConnected ? 'disconnect' : 'reconnect' }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useWebSocketStore } from '@/stores/websocket'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/utils/api'

const webSocketStore = useWebSocketStore()
const authStore = useAuthStore()

const showTooltip = ref(false)
const apiStatus = ref<'healthy' | 'degraded' | 'down'>('healthy')
const tooltipTimeout = ref<number>()

// Computed
const overallStatus = computed(() => {
  if (!authStore.isAuthenticated) return 'disconnected'
  
  const wsConnected = webSocketStore.isConnected
  const apiHealthy = apiStatus.value === 'healthy'
  
  if (wsConnected && apiHealthy) return 'connected'
  if (webSocketStore.isConnecting) return 'connecting'
  if (!wsConnected || !apiHealthy) return 'degraded'
  
  return 'disconnected'
})

const statusText = computed(() => {
  switch (overallStatus.value) {
    case 'connected':
      return 'Connected'
    case 'connecting':
      return 'Connecting...'
    case 'degraded':
      return 'Limited'
    case 'disconnected':
      return 'Offline'
    default:
      return 'Unknown'
  }
})

const statusClasses = computed(() => {
  switch (overallStatus.value) {
    case 'connected':
      return 'bg-green-100 text-green-800'
    case 'connecting':
      return 'bg-yellow-100 text-yellow-800'
    case 'degraded':
      return 'bg-orange-100 text-orange-800'
    case 'disconnected':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
})

const indicatorClasses = computed(() => {
  switch (overallStatus.value) {
    case 'connected':
      return 'bg-green-400 animate-pulse'
    case 'connecting':
      return 'bg-yellow-400 animate-bounce'
    case 'degraded':
      return 'bg-orange-400'
    case 'disconnected':
      return 'bg-red-400'
    default:
      return 'bg-gray-400'
  }
})

// Methods
const checkApiHealth = async () => {
  try {
    // Simple ping to check if API is responsive
    const response = await fetch('/api/health', {
      method: 'GET',
      timeout: 5000
    })
    
    if (response.ok) {
      apiStatus.value = 'healthy'
    } else {
      apiStatus.value = 'degraded'
    }
  } catch (error) {
    apiStatus.value = 'down'
  }
}

const handleClick = () => {
  if (!authStore.isAuthenticated) return
  
  if (webSocketStore.isConnected) {
    webSocketStore.disconnect()
  } else {
    webSocketStore.connect()
  }
}

const handleMouseEnter = () => {
  // Clear any existing timeout
  if (tooltipTimeout.value) {
    clearTimeout(tooltipTimeout.value)
  }
  
  // Show tooltip after a short delay
  tooltipTimeout.value = window.setTimeout(() => {
    showTooltip.value = true
  }, 500)
}

const handleMouseLeave = () => {
  // Clear timeout
  if (tooltipTimeout.value) {
    clearTimeout(tooltipTimeout.value)
  }
  
  // Hide tooltip after a short delay
  tooltipTimeout.value = window.setTimeout(() => {
    showTooltip.value = false
  }, 100)
}

// Periodic health checks
let healthCheckInterval: number

const startHealthChecks = () => {
  // Initial check
  checkApiHealth()
  
  // Check every 30 seconds
  healthCheckInterval = window.setInterval(checkApiHealth, 30000)
}

const stopHealthChecks = () => {
  if (healthCheckInterval) {
    clearInterval(healthCheckInterval)
  }
}

// Lifecycle
onMounted(() => {
  startHealthChecks()
})

onUnmounted(() => {
  stopHealthChecks()
  if (tooltipTimeout.value) {
    clearTimeout(tooltipTimeout.value)
  }
})
</script>