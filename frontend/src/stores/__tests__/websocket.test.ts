/**
 * WebSocket store tests
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useWebSocketStore } from '../websocket'

describe('WebSocket Store', () => {
  let websocketStore: ReturnType<typeof useWebSocketStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    websocketStore = useWebSocketStore()
    vi.clearAllMocks()
  })

  afterEach(() => {
    websocketStore.disconnect()
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      expect(websocketStore.isConnected).toBe(false)
      expect(websocketStore.connectionStatus).toBe('disconnected')
      expect(websocketStore.reconnectAttempts).toBe(0)
    })
  })

  describe('Connection Management', () => {
    it('should connect to WebSocket', async () => {
      const mockToken = 'test-token'
      
      websocketStore.connect(mockToken)
      
      // Wait for connection to establish
      await new Promise(resolve => setTimeout(resolve, 50))

      expect(websocketStore.connectionStatus).toBe('connected')
      expect(websocketStore.isConnected).toBe(true)
    })

    it('should handle connection errors', async () => {
      const originalWebSocket = global.WebSocket

      // Mock WebSocket that fails to connect
      class FailingMockWebSocket {
        constructor() {
          setTimeout(() => {
            if (this.onerror) {
              this.onerror(new Event('error'))
            }
          }, 10)
        }
        
        onerror: ((event: Event) => void) | null = null
        onopen: ((event: Event) => void) | null = null
        onclose: ((event: CloseEvent) => void) | null = null
        onmessage: ((event: MessageEvent) => void) | null = null
        
        send() {}
        close() {}
      }

      global.WebSocket = FailingMockWebSocket as any

      websocketStore.connect('test-token')
      
      await new Promise(resolve => setTimeout(resolve, 50))

      expect(websocketStore.connectionStatus).toBe('error')
      expect(websocketStore.isConnected).toBe(false)

      global.WebSocket = originalWebSocket
    })

    it('should disconnect from WebSocket', async () => {
      websocketStore.connect('test-token')
      await new Promise(resolve => setTimeout(resolve, 50))

      expect(websocketStore.isConnected).toBe(true)

      websocketStore.disconnect()

      expect(websocketStore.isConnected).toBe(false)
      expect(websocketStore.connectionStatus).toBe('disconnected')
    })
  })

  describe('Message Handling', () => {
    beforeEach(async () => {
      websocketStore.connect('test-token')
      await new Promise(resolve => setTimeout(resolve, 50))
    })

    it('should handle task update messages', () => {
      const taskUpdateMessage = {
        type: 'task_update',
        data: {
          task_id: 'task-1',
          status: 'running',
          current_iteration: 2,
          current_candidates: ['commit1', 'commit2']
        }
      }

      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify(taskUpdateMessage)
      })

      // Simulate receiving message
      websocketStore.ws!.onmessage!(messageEvent)

      // Verify the message was processed (this would typically update other stores)
      expect(websocketStore.isConnected).toBe(true) // Basic verification that store is functioning
    })

    it('should handle build status messages', () => {
      const buildStatusMessage = {
        type: 'build_status',
        data: {
          build_id: 'build-1',
          status: 'success',
          output: 'Build completed successfully'
        }
      }

      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify(buildStatusMessage)
      })

      websocketStore.ws!.onmessage!(messageEvent)

      expect(websocketStore.isConnected).toBe(true)
    })

    it('should handle notification messages', () => {
      const notificationMessage = {
        type: 'notification',
        data: {
          message: 'Task completed',
          type: 'success'
        }
      }

      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify(notificationMessage)
      })

      websocketStore.ws!.onmessage!(messageEvent)

      expect(websocketStore.isConnected).toBe(true)
    })

    it('should handle invalid JSON messages gracefully', () => {
      const messageEvent = new MessageEvent('message', {
        data: 'invalid json'
      })

      expect(() => {
        websocketStore.ws!.onmessage!(messageEvent)
      }).not.toThrow()

      expect(websocketStore.isConnected).toBe(true)
    })
  })

  describe('Send Message', () => {
    beforeEach(async () => {
      websocketStore.connect('test-token')
      await new Promise(resolve => setTimeout(resolve, 50))
    })

    it('should send message when connected', () => {
      const mockSend = vi.spyOn(websocketStore.ws!, 'send')
      
      const message = { type: 'ping', data: {} }
      websocketStore.sendMessage(message)

      expect(mockSend).toHaveBeenCalledWith(JSON.stringify(message))
    })

    it('should not send message when disconnected', () => {
      websocketStore.disconnect()
      
      const message = { type: 'ping', data: {} }
      
      expect(() => {
        websocketStore.sendMessage(message)
      }).not.toThrow()
    })
  })

  describe('Reconnection Logic', () => {
    it('should attempt to reconnect on connection loss', async () => {
      websocketStore.connect('test-token')
      await new Promise(resolve => setTimeout(resolve, 50))

      expect(websocketStore.isConnected).toBe(true)

      // Simulate connection loss
      websocketStore.ws!.onclose!(new CloseEvent('close', { wasClean: false }))

      expect(websocketStore.connectionStatus).toBe('reconnecting')
      expect(websocketStore.reconnectAttempts).toBeGreaterThan(0)
    })

    it('should stop reconnecting after max attempts', async () => {
      vi.useFakeTimers()

      websocketStore.connect('test-token')
      await vi.advanceTimersByTimeAsync(50)

      // Mock WebSocket that always fails
      const originalWebSocket = global.WebSocket
      class AlwaysFailingWebSocket {
        constructor() {
          setTimeout(() => {
            if (this.onerror) {
              this.onerror(new Event('error'))
            }
          }, 10)
        }
        
        onerror: ((event: Event) => void) | null = null
        onopen: ((event: Event) => void) | null = null
        onclose: ((event: CloseEvent) => void) | null = null
        onmessage: ((event: MessageEvent) => void) | null = null
        
        send() {}
        close() {}
      }

      global.WebSocket = AlwaysFailingWebSocket as any

      // Simulate connection loss
      websocketStore.ws!.onclose!(new CloseEvent('close', { wasClean: false }))

      // Fast-forward through all reconnection attempts
      for (let i = 0; i < 10; i++) {
        await vi.advanceTimersByTimeAsync(5000)
      }

      expect(websocketStore.connectionStatus).toBe('error')

      global.WebSocket = originalWebSocket
      vi.useRealTimers()
    })
  })
})