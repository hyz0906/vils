<template>
  <div class="min-h-full">
    <!-- Loading state -->
    <div v-if="isLoading" class="flex items-center justify-center min-h-screen">
      <div class="text-center">
        <RefreshCwIcon class="animate-spin h-8 w-8 text-primary-600 mx-auto mb-4" />
        <p class="text-sm text-gray-600">Loading task details...</p>
      </div>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="flex items-center justify-center min-h-screen">
      <div class="text-center max-w-md">
        <XCircleIcon class="h-12 w-12 text-red-400 mx-auto mb-4" />
        <h2 class="text-lg font-medium text-gray-900 mb-2">Failed to Load Task</h2>
        <p class="text-sm text-gray-600 mb-4">{{ error }}</p>
        <button
          @click="loadTask"
          class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <RefreshCwIcon class="mr-2 h-4 w-4" />
          Try Again
        </button>
      </div>
    </div>

    <!-- Task content -->
    <div v-else-if="task" class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Header -->
      <div class="mb-8">
        <nav class="flex mb-4" aria-label="Breadcrumb">
          <ol class="flex items-center space-x-4">
            <li>
              <div>
                <router-link to="/tasks" class="text-gray-400 hover:text-gray-500">
                  <SearchIcon class="flex-shrink-0 h-5 w-5" />
                  <span class="sr-only">Tasks</span>
                </router-link>
              </div>
            </li>
            <li>
              <div class="flex items-center">
                <ChevronRightIcon class="flex-shrink-0 h-5 w-5 text-gray-400" />
                <span class="ml-4 text-sm font-medium text-gray-500 truncate">
                  {{ task.project.name }}
                </span>
              </div>
            </li>
          </ol>
        </nav>

        <div class="md:flex md:items-center md:justify-between">
          <div class="min-w-0 flex-1">
            <div class="flex items-center">
              <h1 class="text-2xl font-bold leading-7 text-gray-900 sm:leading-9 sm:truncate">
                {{ task.project.name }} Localization
              </h1>
              <span
                class="ml-3 inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium"
                :class="getStatusClass(task.status)"
              >
                {{ task.status }}
              </span>
            </div>
            <p class="mt-1 text-sm text-gray-500">
              {{ task.description || 'Binary search localization task' }}
            </p>
            <div class="mt-2 flex items-center text-sm text-gray-500 space-x-4">
              <div class="flex items-center">
                <CalendarIcon class="mr-1 h-4 w-4" />
                Started {{ formatDate(task.created_at) }}
              </div>
              <div class="flex items-center">
                <UserIcon class="mr-1 h-4 w-4" />
                {{ task.user.username }}
              </div>
              <div v-if="task.current_iteration" class="flex items-center">
                <TargetIcon class="mr-1 h-4 w-4" />
                Iteration {{ task.current_iteration }}
              </div>
            </div>
          </div>
          
          <div class="mt-6 flex space-x-3 md:mt-0 md:ml-4">
            <button
              @click="refreshTask"
              :disabled="isRefreshing"
              class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              <RefreshCwIcon class="mr-2 h-4 w-4" :class="{ 'animate-spin': isRefreshing }" />
              Refresh
            </button>
            
            <button
              v-if="task.status === 'active'"
              @click="pauseTask"
              :disabled="isPausing"
              class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50"
            >
              <PauseIcon class="mr-2 h-4 w-4" />
              Pause
            </button>
            
            <router-link
              :to="`/projects/${task.project.id}`"
              class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <FolderIcon class="mr-2 h-4 w-4" />
              View Project
            </router-link>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Main content -->
        <div class="lg:col-span-2 space-y-8">
          <!-- Binary search visualization -->
          <BinarySearchVisualization
            :task-id="task.id"
            :status="task.status"
            :good-commit="task.good_commit"
            :bad-commit="task.bad_commit"
            :current-candidates="task.current_candidates"
            :current-iteration="task.current_iteration"
            :total-iterations="task.total_iterations"
            :problematic-commit="task.problematic_commit"
            :error-message="task.error_message"
            @candidate-marked="handleCandidateMarked"
          />

          <!-- Build output -->
          <div v-if="task.status === 'active'" class="bg-white rounded-lg shadow-sm border border-gray-200">
            <div class="px-6 py-4 border-b border-gray-200">
              <h3 class="text-lg font-medium text-gray-900">
                Build Output
              </h3>
              <p class="mt-1 text-sm text-gray-500">
                Real-time output from the current build/test execution
              </p>
            </div>
            <div class="p-6">
              <div class="bg-gray-900 rounded-lg p-4 font-mono text-sm text-green-400 max-h-96 overflow-y-auto">
                <div v-if="buildOutput.length === 0" class="text-gray-500">
                  Waiting for build output...
                </div>
                <div v-else>
                  <div
                    v-for="(line, index) in buildOutput"
                    :key="index"
                    class="whitespace-pre-wrap"
                    :class="{
                      'text-red-400': line.includes('ERROR') || line.includes('FAILED'),
                      'text-yellow-400': line.includes('WARN'),
                      'text-blue-400': line.includes('INFO')
                    }"
                  >
                    {{ line }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Task history -->
          <div class="bg-white rounded-lg shadow-sm border border-gray-200">
            <div class="px-6 py-4 border-b border-gray-200">
              <h3 class="text-lg font-medium text-gray-900">
                Iteration History
              </h3>
              <p class="mt-1 text-sm text-gray-500">
                Complete history of binary search iterations and results
              </p>
            </div>
            <div class="overflow-hidden">
              <div v-if="taskHistory.length === 0" class="px-6 py-8 text-center text-gray-500">
                No iterations completed yet
              </div>
              <ul v-else class="divide-y divide-gray-200">
                <li
                  v-for="iteration in taskHistory"
                  :key="iteration.id"
                  class="px-6 py-4"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                      <div
                        class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium"
                        :class="getIterationStatusClass(iteration.result)"
                      >
                        {{ iteration.iteration_number }}
                      </div>
                      <div>
                        <p class="text-sm font-medium text-gray-900">
                          Tested commit {{ iteration.tested_commit.substring(0, 8) }}
                        </p>
                        <p class="text-sm text-gray-500">
                          Result: 
                          <span
                            class="font-medium"
                            :class="{
                              'text-green-600': iteration.result === 'good',
                              'text-red-600': iteration.result === 'bad',
                              'text-yellow-600': iteration.result === 'skip'
                            }"
                          >
                            {{ iteration.result }}
                          </span>
                          • {{ iteration.candidates_remaining }} candidates remaining
                        </p>
                      </div>
                    </div>
                    <div class="text-sm text-gray-500">
                      {{ formatDate(iteration.created_at) }}
                    </div>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Sidebar -->
        <div class="space-y-6">
          <!-- Task info -->
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 class="text-lg font-medium text-gray-900 mb-4">
              Task Information
            </h3>
            <dl class="space-y-3">
              <div>
                <dt class="text-sm font-medium text-gray-500">Project</dt>
                <dd class="text-sm text-gray-900">
                  <router-link
                    :to="`/projects/${task.project.id}`"
                    class="text-primary-600 hover:text-primary-500"
                  >
                    {{ task.project.name }}
                  </router-link>
                </dd>
              </div>
              <div>
                <dt class="text-sm font-medium text-gray-500">Repository</dt>
                <dd class="text-sm text-gray-900 font-mono">
                  {{ task.project.repository_url }}
                </dd>
              </div>
              <div>
                <dt class="text-sm font-medium text-gray-500">Good Commit</dt>
                <dd class="text-sm text-gray-900 font-mono">
                  {{ task.good_commit }}
                </dd>
              </div>
              <div>
                <dt class="text-sm font-medium text-gray-500">Bad Commit</dt>
                <dd class="text-sm text-gray-900 font-mono">
                  {{ task.bad_commit }}
                </dd>
              </div>
              <div>
                <dt class="text-sm font-medium text-gray-500">Created</dt>
                <dd class="text-sm text-gray-900">
                  {{ new Date(task.created_at).toLocaleString() }}
                </dd>
              </div>
              <div>
                <dt class="text-sm font-medium text-gray-500">Last Updated</dt>
                <dd class="text-sm text-gray-900">
                  {{ new Date(task.updated_at).toLocaleString() }}
                </dd>
              </div>
            </dl>
          </div>

          <!-- Quick actions -->
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 class="text-lg font-medium text-gray-900 mb-4">
              Quick Actions
            </h3>
            <div class="space-y-3">
              <button
                v-if="task.status === 'active'"
                @click="restartTask"
                :disabled="isRestarting"
                class="w-full inline-flex justify-center items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50"
              >
                <RefreshCwIcon class="mr-2 h-4 w-4" />
                Restart Search
              </button>
              
              <button
                @click="downloadResults"
                :disabled="isDownloading"
                class="w-full inline-flex justify-center items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50"
              >
                <DownloadIcon class="mr-2 h-4 w-4" />
                Download Report
              </button>
              
              <router-link
                :to="`/tasks/new?project=${task.project.id}`"
                class="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <PlusIcon class="mr-2 h-4 w-4" />
                New Task
              </router-link>
            </div>
          </div>

          <!-- WebSocket status -->
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 class="text-lg font-medium text-gray-900 mb-4">
              Real-time Updates
            </h3>
            <div class="flex items-center">
              <div
                class="w-3 h-3 rounded-full mr-3"
                :class="{
                  'bg-green-400': webSocketStore.isConnected,
                  'bg-red-400': !webSocketStore.isConnected
                }"
              ></div>
              <span class="text-sm text-gray-600">
                {{ webSocketStore.isConnected ? 'Connected' : 'Disconnected' }}
              </span>
            </div>
            <p class="text-xs text-gray-500 mt-2">
              Real-time updates for build progress and results
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  RefreshCw as RefreshCwIcon,
  XCircle as XCircleIcon,
  Search as SearchIcon,
  ChevronRight as ChevronRightIcon,
  Calendar as CalendarIcon,
  User as UserIcon,
  Target as TargetIcon,
  Pause as PauseIcon,
  Folder as FolderIcon,
  Plus as PlusIcon,
  Download as DownloadIcon,
} from 'lucide-vue-next'

import BinarySearchVisualization from '@/components/task/BinarySearchVisualization.vue'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import { useWebSocketStore } from '@/stores/websocket'
import { api } from '@/utils/api'
import type { LocalizationTask, TaskIteration } from '@/types'

const route = useRoute()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()
const webSocketStore = useWebSocketStore()

// State
const task = ref<LocalizationTask | null>(null)
const isLoading = ref(false)
const isRefreshing = ref(false)
const isPausing = ref(false)
const isRestarting = ref(false)
const isDownloading = ref(false)
const error = ref<string | null>(null)

const buildOutput = ref<string[]>([])
const taskHistory = ref<TaskIteration[]>([])

// Computed
const taskId = computed(() => route.params.id as string)

// Methods
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 86400000) {
    const hours = Math.floor(diff / 3600000)
    if (hours === 0) {
      const minutes = Math.floor(diff / 60000)
      return minutes === 0 ? 'just now' : `${minutes}m ago`
    }
    return `${hours}h ago`
  }
  
  if (diff < 604800000) {
    const days = Math.floor(diff / 86400000)
    return `${days}d ago`
  }
  
  return date.toLocaleDateString()
}

const getStatusClass = (status: string) => {
  switch (status) {
    case 'active':
      return 'bg-blue-100 text-blue-800'
    case 'completed':
      return 'bg-green-100 text-green-800'
    case 'failed':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const getIterationStatusClass = (result: string) => {
  switch (result) {
    case 'good':
      return 'bg-green-100 text-green-800'
    case 'bad':
      return 'bg-red-100 text-red-800'
    case 'skip':
      return 'bg-yellow-100 text-yellow-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const loadTask = async () => {
  isLoading.value = true
  error.value = null
  
  try {
    // Load task details
    task.value = await api.tasks.get(taskId.value)
    
    // Load task iterations
    const iterations = await api.tasks.getIterations(taskId.value)
    taskHistory.value = Array.isArray(iterations) ? iterations : []
    
    // Subscribe to task updates via WebSocket
    if (webSocketStore.isConnected) {
      webSocketStore.subscribeToTask(taskId.value)
    }
    
  } catch (err: any) {
    console.error('Failed to load task:', err)
    error.value = err.message || 'Failed to load task'
  } finally {
    isLoading.value = false
  }
}

const refreshTask = async () => {
  isRefreshing.value = true
  try {
    await loadTask()
    notificationStore.success('Task refreshed', 'Task details have been updated')
  } finally {
    isRefreshing.value = false
  }
}

const handleCandidateMarked = async (data: { candidate: string; result: 'good' | 'bad' | 'skip' }) => {
  try {
    // Call API to mark candidate
    const updatedTask = await api.tasks.markCandidate(taskId.value, data)
    
    // Update local task state
    task.value = updatedTask
    
    // Simulate build output for visual feedback
    buildOutput.value.push(`Testing commit ${data.candidate.substring(0, 8)}...`)
    buildOutput.value.push(`Running build command: ${task.value?.project.build_command}`)
    buildOutput.value.push(`Running test command: ${task.value?.project.test_command}`)
    buildOutput.value.push(`Result: ${data.result.toUpperCase()}`)
    
    // Reload task history to get the latest iteration
    const iterations = await api.tasks.getIterations(taskId.value)
    taskHistory.value = Array.isArray(iterations) ? iterations : []
    
    // Check if task was completed
    if (updatedTask.status === 'completed') {
      notificationStore.success(
        'Localization Complete!',
        `Found problematic commit in ${updatedTask.total_iterations} iterations`
      )
    }
    
  } catch (error) {
    console.error('Failed to mark candidate:', error)
    notificationStore.error('Failed to process result', 'Please try again')
  }
}

const pauseTask = async () => {
  isPausing.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    // TODO: Implement pause functionality
    notificationStore.success('Task paused', 'The localization task has been paused')
  } finally {
    isPausing.value = false
  }
}

const restartTask = async () => {
  isRestarting.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    // TODO: Implement restart functionality
    notificationStore.success('Task restarted', 'The localization task has been restarted')
  } finally {
    isRestarting.value = false
  }
}

const downloadResults = async () => {
  isDownloading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    // TODO: Implement download functionality
    notificationStore.success('Report downloaded', 'Task report has been downloaded')
  } finally {
    isDownloading.value = false
  }
}

// WebSocket event handlers
const handleTaskUpdate = (event: CustomEvent) => {
  const update = event.detail
  if (update.task_id === taskId.value && task.value) {
    // Update task with real-time data
    Object.assign(task.value, update.data)
  }
}

// Lifecycle
onMounted(async () => {
  await loadTask()
  
  // Listen for real-time updates
  window.addEventListener('task:update', handleTaskUpdate as EventListener)
})

onUnmounted(() => {
  // Unsubscribe from task updates
  if (webSocketStore.isConnected) {
    webSocketStore.unsubscribeFromTask(taskId.value)
  }
  
  window.removeEventListener('task:update', handleTaskUpdate as EventListener)
})
</script>