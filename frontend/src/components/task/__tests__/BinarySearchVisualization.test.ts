/**
 * BinarySearchVisualization component tests
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { mountComponent, mockTask, clickElement, nextTick } from '@/test/utils'
import BinarySearchVisualization from '../BinarySearchVisualization.vue'

describe('BinarySearchVisualization Component', () => {
  const mockTaskWithIterations = {
    ...mockTask,
    status: 'running' as const,
    current_iteration: 2,
    current_candidates: ['commit1', 'commit2', 'commit3', 'commit4', 'commit5'],
    iterations: [
      {
        id: '1',
        task_id: mockTask.id,
        iteration_number: 1,
        candidates: ['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9', 'a10'],
        selected_candidate: 'a5',
        test_result: 'pass',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        id: '2',
        task_id: mockTask.id,
        iteration_number: 2,
        candidates: ['commit1', 'commit2', 'commit3', 'commit4', 'commit5'],
        selected_candidate: null,
        test_result: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    ]
  }

  describe('Rendering', () => {
    it('should render task information', () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTaskWithIterations }
      })

      expect(wrapper.text()).toContain('Test localization task')
      expect(wrapper.text()).toContain('Iteration 2')
    })

    it('should render current candidates', () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTaskWithIterations }
      })

      const candidates = wrapper.findAll('[data-testid="candidate-item"]')
      expect(candidates).toHaveLength(5)
      
      expect(candidates[0].text()).toContain('commit1')
      expect(candidates[1].text()).toContain('commit2')
    })

    it('should render previous iterations', () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTaskWithIterations }
      })

      const iterations = wrapper.findAll('[data-testid="iteration-item"]')
      expect(iterations).toHaveLength(2)
      
      expect(iterations[0].text()).toContain('Iteration 1')
      expect(iterations[0].text()).toContain('PASS')
    })

    it('should render algorithm explanation', () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTaskWithIterations }
      })

      expect(wrapper.text()).toContain('Binary Search Algorithm')
      expect(wrapper.text()).toContain('How it works')
    })
  })

  describe('Candidate Selection', () => {
    it('should highlight middle candidate by default', () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTaskWithIterations }
      })

      const candidates = wrapper.findAll('[data-testid="candidate-item"]')
      const middleCandidate = candidates[2] // Index 2 is middle of 5 items
      
      expect(middleCandidate.classes()).toContain('ring-2')
      expect(middleCandidate.classes()).toContain('ring-primary-500')
    })

    it('should allow selecting different candidates', async () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTaskWithIterations }
      })

      const candidates = wrapper.findAll('[data-testid="candidate-item"]')
      await clickElement(wrapper, '[data-testid="candidate-item"]:first-child')
      
      expect(candidates[0].classes()).toContain('ring-2')
      expect(candidates[0].classes()).toContain('ring-primary-500')
    })

    it('should emit candidate selection event', async () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTaskWithIterations }
      })

      await clickElement(wrapper, '[data-testid="candidate-item"]:first-child')
      
      expect(wrapper.emitted('select-candidate')).toBeTruthy()
      expect(wrapper.emitted('select-candidate')![0]).toEqual(['commit1'])
    })
  })

  describe('Test Result Actions', () => {
    it('should show test result buttons when candidate is selected', () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTaskWithIterations }
      })

      const passButton = wrapper.find('[data-testid="pass-button"]')
      const failButton = wrapper.find('[data-testid="fail-button"]')
      
      expect(passButton.exists()).toBe(true)
      expect(failButton.exists()).toBe(true)
    })

    it('should emit test result events', async () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTaskWithIterations }
      })

      await clickElement(wrapper, '[data-testid="pass-button"]')
      
      expect(wrapper.emitted('test-result')).toBeTruthy()
      expect(wrapper.emitted('test-result')![0]).toEqual(['pass', 'commit3'])
    })

    it('should emit fail result', async () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTaskWithIterations }
      })

      await clickElement(wrapper, '[data-testid="fail-button"]')
      
      expect(wrapper.emitted('test-result')).toBeTruthy()
      expect(wrapper.emitted('test-result')![0]).toEqual(['fail', 'commit3'])
    })
  })

  describe('Task Status Display', () => {
    it('should show running status', () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTaskWithIterations }
      })

      const statusBadge = wrapper.find('[data-testid="status-badge"]')
      expect(statusBadge.text()).toContain('Running')
      expect(statusBadge.classes()).toContain('bg-yellow-100')
    })

    it('should show completed status', () => {
      const completedTask = {
        ...mockTaskWithIterations,
        status: 'completed' as const,
        problematic_commit: 'commit2'
      }

      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: completedTask }
      })

      const statusBadge = wrapper.find('[data-testid="status-badge"]')
      expect(statusBadge.text()).toContain('Completed')
      expect(statusBadge.classes()).toContain('bg-green-100')
    })

    it('should show failed status', () => {
      const failedTask = {
        ...mockTaskWithIterations,
        status: 'failed' as const,
        error_message: 'Build failed'
      }

      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: failedTask }
      })

      const statusBadge = wrapper.find('[data-testid="status-badge"]')
      expect(statusBadge.text()).toContain('Failed')
      expect(statusBadge.classes()).toContain('bg-red-100')
    })
  })

  describe('Progress Visualization', () => {
    it('should show progress bar', () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTaskWithIterations }
      })

      const progressBar = wrapper.find('[data-testid="progress-bar"]')
      expect(progressBar.exists()).toBe(true)
    })

    it('should calculate progress correctly', () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTaskWithIterations }
      })

      // With 2 iterations and estimated max of 10, progress should be 20%
      const progressBar = wrapper.find('[data-testid="progress-fill"]')
      expect(progressBar.attributes('style')).toContain('width: 20%')
    })
  })

  describe('Iteration History', () => {
    it('should display iteration results', () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTaskWithIterations }
      })

      const iteration = wrapper.find('[data-testid="iteration-1"]')
      expect(iteration.text()).toContain('a5')
      expect(iteration.text()).toContain('PASS')
    })

    it('should show pending iterations', () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTaskWithIterations }
      })

      const iteration = wrapper.find('[data-testid="iteration-2"]')
      expect(iteration.text()).toContain('In Progress')
    })
  })

  describe('Algorithm Explanation', () => {
    it('should show/hide explanation', async () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTaskWithIterations }
      })

      const toggleButton = wrapper.find('[data-testid="toggle-explanation"]')
      const explanation = wrapper.find('[data-testid="algorithm-explanation"]')
      
      expect(explanation.isVisible()).toBe(false)

      await clickElement(wrapper, '[data-testid="toggle-explanation"]')
      await nextTick()

      expect(explanation.isVisible()).toBe(true)
    })

    it('should contain algorithm steps', async () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTaskWithIterations }
      })

      await clickElement(wrapper, '[data-testid="toggle-explanation"]')
      await nextTick()

      const explanation = wrapper.find('[data-testid="algorithm-explanation"]')
      expect(explanation.text()).toContain('Select the middle commit')
      expect(explanation.text()).toContain('Test the selected commit')
      expect(explanation.text()).toContain('Based on the result')
    })
  })

  describe('Responsive Design', () => {
    it('should have responsive classes', () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTaskWithIterations }
      })

      const container = wrapper.find('[data-testid="visualization-container"]')
      expect(container.classes()).toContain('lg:grid-cols-2')
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTaskWithIterations }
      })

      const candidates = wrapper.findAll('[data-testid="candidate-item"]')
      expect(candidates[0].attributes('role')).toBe('button')
      expect(candidates[0].attributes('aria-label')).toContain('Select candidate commit1')
    })

    it('should have keyboard navigation support', async () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTaskWithIterations }
      })

      const candidate = wrapper.find('[data-testid="candidate-item"]')
      expect(candidate.attributes('tabindex')).toBe('0')
    })
  })
})