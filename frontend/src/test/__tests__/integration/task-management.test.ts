/**
 * Task management integration tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createMockRouter, mountComponent, fillInput, clickElement, waitFor, mockTask, mockProject } from '@/test/utils'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import TasksView from '@/views/TasksView.vue'
import TaskDetailsView from '@/views/TaskDetailsView.vue'
import BinarySearchVisualization from '@/components/task/BinarySearchVisualization.vue'

describe('Task Management Integration', () => {
  let router: ReturnType<typeof createMockRouter>
  let authStore: ReturnType<typeof useAuthStore>

  beforeEach(() => {
    router = createMockRouter('/tasks')
    authStore = useAuthStore()
    
    // Mock authenticated user
    authStore.user = {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      is_active: true
    }
    
    vi.clearAllMocks()
  })

  describe('Task Creation Flow', () => {
    it('should create a new localization task', async () => {
      const wrapper = mountComponent(TasksView, { router })
      const notificationStore = useNotificationStore()

      // Mock API responses
      const { api } = await import('@/utils/api')
      vi.mocked(api.projects.list).mockResolvedValue([mockProject])
      vi.mocked(api.tasks.create).mockResolvedValue(mockTask)

      // Click create task button
      await clickElement(wrapper, '[data-testid="create-task-button"]')

      // Verify modal opens
      expect(wrapper.find('[data-testid="create-task-modal"]').exists()).toBe(true)

      // Fill in task form
      await fillInput(wrapper, '[data-testid="project-select"]', mockProject.id)
      await fillInput(wrapper, '[data-testid="description-input"]', 'Test task description')
      await fillInput(wrapper, '[data-testid="good-commit-input"]', 'abc123')
      await fillInput(wrapper, '[data-testid="bad-commit-input"]', 'def456')

      // Submit form
      await clickElement(wrapper, '[data-testid="submit-task-button"]')

      // Wait for task creation
      await waitFor(() => notificationStore.notifications.length > 0)

      // Verify success notification
      expect(notificationStore.notifications.some(n => 
        n.type === 'success' && n.message.includes('Task created')
      )).toBe(true)

      // Verify API was called with correct data
      expect(api.tasks.create).toHaveBeenCalledWith({
        project_id: mockProject.id,
        description: 'Test task description',
        good_commit: 'abc123',
        bad_commit: 'def456'
      })
    })

    it('should validate task creation form', async () => {
      const wrapper = mountComponent(TasksView, { router })

      await clickElement(wrapper, '[data-testid="create-task-button"]')

      // Try to submit empty form
      await clickElement(wrapper, '[data-testid="submit-task-button"]')

      // Verify validation errors
      expect(wrapper.find('[data-testid="project-error"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="description-error"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="good-commit-error"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="bad-commit-error"]').exists()).toBe(true)
    })

    it('should handle task creation errors', async () => {
      const wrapper = mountComponent(TasksView, { router })
      const notificationStore = useNotificationStore()

      // Mock API error
      const { api } = await import('@/utils/api')
      vi.mocked(api.projects.list).mockResolvedValue([mockProject])
      vi.mocked(api.tasks.create).mockRejectedValue(new Error('Invalid commit range'))

      await clickElement(wrapper, '[data-testid="create-task-button"]')
      
      // Fill form
      await fillInput(wrapper, '[data-testid="project-select"]', mockProject.id)
      await fillInput(wrapper, '[data-testid="description-input"]', 'Test task')
      await fillInput(wrapper, '[data-testid="good-commit-input"]', 'invalid')
      await fillInput(wrapper, '[data-testid="bad-commit-input"]', 'invalid')

      await clickElement(wrapper, '[data-testid="submit-task-button"]')

      // Wait for error handling
      await waitFor(() => notificationStore.notifications.some(n => n.type === 'error'))

      // Verify error notification
      expect(notificationStore.notifications.some(n => 
        n.type === 'error' && n.message.includes('Invalid commit range')
      )).toBe(true)
    })
  })

  describe('Task List Management', () => {
    it('should display task list with correct data', async () => {
      const { api } = await import('@/utils/api')
      vi.mocked(api.tasks.list).mockResolvedValue([mockTask])

      const wrapper = mountComponent(TasksView, { router })

      // Wait for tasks to load
      await waitFor(() => wrapper.find('[data-testid="task-item"]').exists())

      // Verify task data is displayed
      expect(wrapper.text()).toContain(mockTask.description)
      expect(wrapper.text()).toContain(mockTask.status)
      expect(wrapper.text()).toContain(mockTask.project.name)
    })

    it('should filter tasks by status', async () => {
      const tasks = [
        { ...mockTask, id: '1', status: 'active' as const },
        { ...mockTask, id: '2', status: 'completed' as const },
        { ...mockTask, id: '3', status: 'failed' as const }
      ]

      const { api } = await import('@/utils/api')
      vi.mocked(api.tasks.list).mockResolvedValue(tasks)

      const wrapper = mountComponent(TasksView, { router })

      await waitFor(() => wrapper.findAll('[data-testid="task-item"]').length === 3)

      // Filter by active status
      await clickElement(wrapper, '[data-testid="filter-active"]')

      // Verify only active tasks are shown
      const visibleTasks = wrapper.findAll('[data-testid="task-item"]:visible')
      expect(visibleTasks).toHaveLength(1)
      expect(visibleTasks[0].text()).toContain('active')
    })

    it('should navigate to task details', async () => {
      const { api } = await import('@/utils/api')
      vi.mocked(api.tasks.list).mockResolvedValue([mockTask])

      const wrapper = mountComponent(TasksView, { router })

      await waitFor(() => wrapper.find('[data-testid="task-item"]').exists())

      // Click on task
      await clickElement(wrapper, '[data-testid="task-item"]')

      // Verify navigation to task details
      expect(router.currentRoute.value.path).toBe(`/tasks/${mockTask.id}`)
    })
  })

  describe('Task Details and Binary Search', () => {
    it('should display task details correctly', async () => {
      const taskWithIterations = {
        ...mockTask,
        iterations: [
          {
            id: '1',
            task_id: mockTask.id,
            iteration_number: 1,
            candidates: ['commit1', 'commit2', 'commit3'],
            selected_candidate: 'commit2',
            test_result: 'pass',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }
        ]
      }

      const { api } = await import('@/utils/api')
      vi.mocked(api.tasks.get).mockResolvedValue(taskWithIterations)

      router.push(`/tasks/${mockTask.id}`)
      await router.isReady()

      const wrapper = mountComponent(TaskDetailsView, { router })

      await waitFor(() => wrapper.find('[data-testid="task-details"]').exists())

      // Verify task information is displayed
      expect(wrapper.text()).toContain(mockTask.description)
      expect(wrapper.text()).toContain(mockTask.project.name)
      expect(wrapper.text()).toContain('Iteration 1')
    })

    it('should handle candidate selection in binary search', async () => {
      const runningTask = {
        ...mockTask,
        status: 'running' as const,
        current_candidates: ['commit1', 'commit2', 'commit3'],
        current_iteration: 1
      }

      const { api } = await import('@/utils/api')
      vi.mocked(api.tasks.get).mockResolvedValue(runningTask)

      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: runningTask }
      })

      // Select a candidate
      await clickElement(wrapper, '[data-testid="candidate-item"]:first-child')

      // Verify candidate is selected
      expect(wrapper.emitted('select-candidate')).toBeTruthy()
      expect(wrapper.emitted('select-candidate')![0]).toEqual(['commit1'])
    })

    it('should submit test results', async () => {
      const runningTask = {
        ...mockTask,
        status: 'running' as const,
        current_candidates: ['commit1', 'commit2', 'commit3'],
        current_iteration: 1
      }

      const { api } = await import('@/utils/api')
      vi.mocked(api.tasks.get).mockResolvedValue(runningTask)
      vi.mocked(api.tasks.submitResult).mockResolvedValue({ success: true })

      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: runningTask }
      })

      // Select candidate and submit pass result
      await clickElement(wrapper, '[data-testid="pass-button"]')

      // Verify test result is emitted
      expect(wrapper.emitted('test-result')).toBeTruthy()
      expect(wrapper.emitted('test-result')![0]).toEqual(['pass', 'commit2']) // Middle candidate
    })
  })

  describe('Real-time Updates', () => {
    it('should handle WebSocket task updates', async () => {
      const { api } = await import('@/utils/api')
      vi.mocked(api.tasks.list).mockResolvedValue([mockTask])

      const wrapper = mountComponent(TasksView, { router })

      await waitFor(() => wrapper.find('[data-testid="task-item"]').exists())

      // Simulate WebSocket update
      const updatedTask = {
        ...mockTask,
        status: 'completed' as const,
        problematic_commit: 'commit2'
      }

      // Mock WebSocket message
      const mockWebSocket = new window.WebSocket('ws://localhost')
      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify({
          type: 'task_update',
          data: updatedTask
        })
      })

      // Trigger WebSocket message handler
      if (mockWebSocket.onmessage) {
        mockWebSocket.onmessage(messageEvent)
      }

      // Wait for UI update
      await waitFor(() => wrapper.text().includes('completed'))

      // Verify task status is updated
      expect(wrapper.text()).toContain('completed')
      expect(wrapper.text()).toContain('commit2')
    })
  })

  describe('Task Actions', () => {
    it('should cancel running task', async () => {
      const runningTask = { ...mockTask, status: 'running' as const }

      const { api } = await import('@/utils/api')
      vi.mocked(api.tasks.get).mockResolvedValue(runningTask)
      vi.mocked(api.tasks.cancel).mockResolvedValue({ success: true })

      router.push(`/tasks/${mockTask.id}`)
      await router.isReady()

      const wrapper = mountComponent(TaskDetailsView, { router })

      await waitFor(() => wrapper.find('[data-testid="cancel-task-button"]').exists())

      // Cancel task
      await clickElement(wrapper, '[data-testid="cancel-task-button"]')

      // Confirm cancellation
      await clickElement(wrapper, '[data-testid="confirm-cancel-button"]')

      // Verify API call
      expect(api.tasks.cancel).toHaveBeenCalledWith(mockTask.id)
    })

    it('should restart failed task', async () => {
      const failedTask = { 
        ...mockTask, 
        status: 'failed' as const,
        error_message: 'Build failed'
      }

      const { api } = await import('@/utils/api')
      vi.mocked(api.tasks.get).mockResolvedValue(failedTask)
      vi.mocked(api.tasks.restart).mockResolvedValue({ success: true })

      router.push(`/tasks/${mockTask.id}`)
      await router.isReady()

      const wrapper = mountComponent(TaskDetailsView, { router })

      await waitFor(() => wrapper.find('[data-testid="restart-task-button"]').exists())

      // Restart task
      await clickElement(wrapper, '[data-testid="restart-task-button"]')

      // Verify API call
      expect(api.tasks.restart).toHaveBeenCalledWith(mockTask.id)
    })

    it('should delete completed task', async () => {
      const completedTask = { 
        ...mockTask, 
        status: 'completed' as const,
        problematic_commit: 'commit3'
      }

      const { api } = await import('@/utils/api')
      vi.mocked(api.tasks.get).mockResolvedValue(completedTask)
      vi.mocked(api.tasks.delete).mockResolvedValue({ success: true })

      router.push(`/tasks/${mockTask.id}`)
      await router.isReady()

      const wrapper = mountComponent(TaskDetailsView, { router })

      await waitFor(() => wrapper.find('[data-testid="delete-task-button"]').exists())

      // Delete task
      await clickElement(wrapper, '[data-testid="delete-task-button"]')

      // Confirm deletion
      await clickElement(wrapper, '[data-testid="confirm-delete-button"]')

      // Verify API call and navigation
      expect(api.tasks.delete).toHaveBeenCalledWith(mockTask.id)
      expect(router.currentRoute.value.path).toBe('/tasks')
    })
  })
})