/**
 * WebSocket store for real-time updates
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { WebSocketMessage, TaskUpdateMessage, BuildUpdateMessage, ProgressUpdateMessage } from '@/types'
import apiClient from '@/utils/api'
import { createMockWebSocket } from '@/utils/mockApi'
import { useNotificationStore } from './notification'

export const useWebSocketStore = defineStore('websocket', () => {
  // State
  const socket = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const isConnecting = ref(false)
  const lastError = ref<string | null>(null)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  const reconnectInterval = ref<number | null>(null)

  // Subscriptions
  const subscriptions = ref<Set<string>>(new Set())
  
  // Message handlers
  const messageHandlers = ref<Map<string, ((message: any) => void)[]>>(new Map())

  // Getters
  const connectionStatus = computed(() => {
    if (isConnecting.value) return 'connecting'
    if (isConnected.value) return 'connected'
    return 'disconnected'
  })

  // Actions
  const connect = (): void => {
    if (socket.value?.readyState === WebSocket.OPEN || isConnecting.value) {
      return
    }

    const token = apiClient.getWebSocketToken()
    if (!token) {
      lastError.value = 'No authentication token available'
      return
    }

    isConnecting.value = true
    lastError.value = null

    try {
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws?token=${encodeURIComponent(token)}`
      
      // Use mock WebSocket if in development mode or mock API is enabled
      const useMockApi = import.meta.env.VITE_USE_MOCK_API === 'true' || !import.meta.env.VITE_API_BASE_URL
      socket.value = useMockApi ? createMockWebSocket(wsUrl) : new WebSocket(wsUrl)

      socket.value.onopen = handleOpen
      socket.value.onmessage = handleMessage
      socket.value.onclose = handleClose
      socket.value.onerror = handleError

    } catch (error) {
      console.error('WebSocket connection error:', error)
      isConnecting.value = false
      lastError.value = 'Failed to establish connection'
    }
  }

  const disconnect = (): void => {
    if (socket.value) {
      socket.value.close(1000, 'Manual disconnect')
    }
    
    if (reconnectInterval.value) {
      clearTimeout(reconnectInterval.value)
      reconnectInterval.value = null
    }
    
    socket.value = null
    isConnected.value = false
    isConnecting.value = false
    subscriptions.value.clear()
    messageHandlers.value.clear()
    reconnectAttempts.value = 0
  }

  const sendMessage = (message: WebSocketMessage): void => {
    if (socket.value?.readyState === WebSocket.OPEN) {
      try {
        socket.value.send(JSON.stringify(message))
      } catch (error) {
        console.error('Failed to send WebSocket message:', error)
      }
    } else {
      console.warn('WebSocket not connected, message not sent:', message)
    }
  }

  const subscribe = (key: string): void => {
    subscriptions.value.add(key)
    
    if (isConnected.value) {
      sendMessage({
        type: 'subscribe',
        key
      })
    }
  }

  const unsubscribe = (key: string): void => {
    subscriptions.value.delete(key)
    
    if (isConnected.value) {
      sendMessage({
        type: 'unsubscribe',
        key
      })
    }
  }

  const subscribeToTask = (taskId: string): void => {
    subscribe(`task_${taskId}`)
  }

  const unsubscribeFromTask = (taskId: string): void => {
    unsubscribe(`task_${taskId}`)
  }

  const addMessageHandler = (messageType: string, handler: (message: any) => void): () => void => {
    if (!messageHandlers.value.has(messageType)) {
      messageHandlers.value.set(messageType, [])
    }
    
    messageHandlers.value.get(messageType)!.push(handler)
    
    // Return unsubscribe function
    return () => {
      const handlers = messageHandlers.value.get(messageType)
      if (handlers) {
        const index = handlers.indexOf(handler)
        if (index > -1) {
          handlers.splice(index, 1)
        }
      }
    }
  }

  // Event handlers
  const handleOpen = (): void => {
    isConnected.value = true
    isConnecting.value = false
    reconnectAttempts.value = 0
    lastError.value = null

    // Resubscribe to previous subscriptions
    subscriptions.value.forEach(key => {
      sendMessage({
        type: 'subscribe',
        key
      })
    })

    console.log('WebSocket connected')
  }

  const handleMessage = (event: MessageEvent): void => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data)
      
      // Handle specific message types
      switch (message.type) {
        case 'connection_established':
          console.log('WebSocket connection established:', message)
          break
          
        case 'task_update':
          handleTaskUpdate(message as TaskUpdateMessage)
          break
          
        case 'build_update':
          handleBuildUpdate(message as BuildUpdateMessage)
          break
          
        case 'progress_update':
          handleProgressUpdate(message as ProgressUpdateMessage)
          break
          
        case 'subscription_confirmed':
          console.log('Subscription confirmed:', message.key)
          break
          
        case 'unsubscription_confirmed':
          console.log('Unsubscription confirmed:', message.key)
          break
          
        case 'pong':
          // Handle ping/pong for keepalive
          break
          
        case 'error':
          console.error('WebSocket error message:', message.message)
          break
          
        default:
          console.log('Unknown WebSocket message:', message)
      }

      // Call registered handlers
      const handlers = messageHandlers.value.get(message.type)
      if (handlers) {
        handlers.forEach(handler => {
          try {
            handler(message)
          } catch (error) {
            console.error('Message handler error:', error)
          }
        })
      }

    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
    }
  }

  const handleClose = (event: CloseEvent): void => {
    isConnected.value = false
    isConnecting.value = false
    socket.value = null

    console.log('WebSocket disconnected:', event.code, event.reason)

    // Attempt to reconnect if not a manual disconnect
    if (event.code !== 1000 && reconnectAttempts.value < maxReconnectAttempts) {
      scheduleReconnect()
    }
  }

  const handleError = (error: Event): void => {
    console.error('WebSocket error:', error)
    lastError.value = 'Connection error occurred'
    isConnecting.value = false
  }

  const scheduleReconnect = (): void => {
    if (reconnectAttempts.value >= maxReconnectAttempts) {
      lastError.value = 'Max reconnection attempts reached'
      return
    }

    reconnectAttempts.value++
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.value), 30000) // Exponential backoff, max 30s

    console.log(`Scheduling WebSocket reconnection attempt ${reconnectAttempts.value} in ${delay}ms`)

    reconnectInterval.value = window.setTimeout(() => {
      console.log(`Attempting WebSocket reconnection ${reconnectAttempts.value}/${maxReconnectAttempts}`)
      connect()
    }, delay)
  }

  const ping = (): void => {
    sendMessage({
      type: 'ping',
      timestamp: new Date().toISOString()
    })
  }

  // Message type handlers
  const handleTaskUpdate = (message: TaskUpdateMessage): void => {
    // Emit custom event for components to listen to
    window.dispatchEvent(new CustomEvent('task:update', {
      detail: message
    }))
  }

  const handleBuildUpdate = (message: BuildUpdateMessage): void => {
    const notificationStore = useNotificationStore()
    
    // Show notification for build status changes
    if (message.status === 'success') {
      notificationStore.success('Build Completed', `Build ${message.build_id} completed successfully`)
    } else if (message.status === 'failed') {
      notificationStore.error('Build Failed', `Build ${message.build_id} failed`)
    }

    // Emit custom event
    window.dispatchEvent(new CustomEvent('build:update', {
      detail: message
    }))
  }

  const handleProgressUpdate = (message: ProgressUpdateMessage): void => {
    // Emit custom event for progress updates
    window.dispatchEvent(new CustomEvent('progress:update', {
      detail: message
    }))
  }

  // Keepalive ping
  const startPingInterval = (): void => {
    setInterval(() => {
      if (isConnected.value) {
        ping()
      }
    }, 30000) // Ping every 30 seconds
  }

  // Initialize ping on first connection
  if (typeof window !== 'undefined') {
    startPingInterval()
  }

  return {
    // State
    isConnected,
    isConnecting,
    connectionStatus,
    lastError,
    reconnectAttempts,
    subscriptions,

    // Actions
    connect,
    disconnect,
    sendMessage,
    subscribe,
    unsubscribe,
    subscribeToTask,
    unsubscribeFromTask,
    addMessageHandler,
    ping,
  }
})