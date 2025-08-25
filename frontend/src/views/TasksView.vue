<template>
  <div class="min-h-full">
    <!-- Page header -->
    <div class="bg-white shadow">
      <div class="px-4 sm:px-6 lg:max-w-6xl lg:mx-auto lg:px-8">
        <div class="py-6 md:flex md:items-center md:justify-between">
          <div class="min-w-0 flex-1">
            <h1 class="text-2xl font-bold leading-7 text-gray-900 sm:leading-9 sm:truncate">
              Localization Tasks
            </h1>
            <p class="mt-1 text-sm text-gray-500">
              Track and manage your binary search localization tasks
            </p>
          </div>
          <div class="mt-6 flex space-x-3 md:mt-0 md:ml-4">
            <button
              @click="refreshTasks"
              :disabled="isLoading"
              class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              <RefreshCwIcon class="mr-2 h-4 w-4" :class="{ 'animate-spin': isLoading }" />
              Refresh
            </button>
            <router-link
              to="/tasks/new"
              class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <PlusIcon class="mr-2 h-4 w-4" />
              New Task
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- Filters and search -->
    <div class="bg-white border-b border-gray-200">
      <div class="px-4 sm:px-6 lg:max-w-6xl lg:mx-auto lg:px-8 py-4">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
          <!-- Search -->
          <div class="flex-1 min-w-0">
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <SearchIcon class="h-5 w-5 text-gray-400" />
              </div>
              <input
                v-model="searchQuery"
                type="text"
                class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                placeholder="Search tasks..."
              />
            </div>
          </div>

          <!-- Status filter -->
          <div class="flex space-x-3">
            <select
              v-model="statusFilter"
              class="block text-sm border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">All statuses</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>

            <select
              v-model="sortBy"
              class="block text-sm border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="created_at">Latest first</option>
              <option value="updated_at">Recently updated</option>
              <option value="status">Status</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- Main content -->
    <div class="px-4 sm:px-6 lg:max-w-6xl lg:mx-auto lg:px-8 py-8">
      <!-- Loading state -->
      <div v-if="isLoading" class="text-center py-12">
        <div class="inline-flex items-center px-4 py-2 font-medium text-gray-600">
          <RefreshCwIcon class="animate-spin h-5 w-5 mr-3" />
          Loading tasks...
        </div>
      </div>

      <!-- Empty state -->
      <div v-else-if="filteredTasks.length === 0 && !searchQuery" class="text-center py-12">
        <SearchIcon class="mx-auto h-12 w-12 text-gray-400" />
        <h3 class="mt-2 text-sm font-medium text-gray-900">No tasks</h3>
        <p class="mt-1 text-sm text-gray-500">Get started by creating a new localization task.</p>
        <div class="mt-6">
          <router-link
            to="/tasks/new"
            class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <PlusIcon class="mr-2 h-4 w-4" />
            New Task
          </router-link>
        </div>
      </div>

      <!-- No results state -->
      <div v-else-if="filteredTasks.length === 0 && searchQuery" class="text-center py-12">
        <SearchIcon class="mx-auto h-12 w-12 text-gray-400" />
        <h3 class="mt-2 text-sm font-medium text-gray-900">No tasks found</h3>
        <p class="mt-1 text-sm text-gray-500">
          No tasks match your search criteria.
        </p>
        <div class="mt-6">
          <button
            @click="clearFilters"
            class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Clear search
          </button>
        </div>
      </div>

      <!-- Tasks list -->
      <div v-else class="space-y-6">
        <div
          v-for="task in paginatedTasks"
          :key="task.id"
          class="bg-white shadow rounded-lg hover:shadow-md transition-shadow duration-200"
        >
          <div class="px-6 py-4">
            <div class="flex items-center justify-between">
              <!-- Task info -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center">
                  <h3 class="text-lg font-medium text-gray-900">
                    <router-link
                      :to="`/tasks/${task.id}`"
                      class="hover:text-primary-600 transition-colors duration-200"
                    >
                      {{ task.project.name }} Localization
                    </router-link>
                  </h3>
                  <span
                    class="ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
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
                    Created {{ formatDate(task.created_at) }}
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

              <!-- Task actions -->
              <div class="flex items-center space-x-3 ml-4">
                <div v-if="task.status === 'active'" class="text-right">
                  <div class="text-sm font-medium text-gray-900">
                    {{ task.current_candidates?.length || 0 }} candidates
                  </div>
                  <div class="text-xs text-gray-500">
                    {{ getProgress(task) }}% complete
                  </div>
                </div>
                
                <router-link
                  :to="`/tasks/${task.id}`"
                  class="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-primary-700 bg-primary-100 hover:bg-primary-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  {{ task.status === 'active' ? 'Continue' : 'View' }}
                </router-link>
              </div>
            </div>
          </div>

          <!-- Progress bar for active tasks -->
          <div v-if="task.status === 'active'" class="px-6 pb-4">
            <div class="bg-gray-200 rounded-full h-2">
              <div
                class="bg-primary-600 h-2 rounded-full transition-all duration-300"
                :style="{ width: `${getProgress(task)}%` }"
              ></div>
            </div>
            <div class="mt-1 flex justify-between text-xs text-gray-500">
              <span>{{ task.current_candidates?.length || 0 }} candidates remaining</span>
              <span>{{ task.current_iteration || 0 }} iterations completed</span>
            </div>
          </div>

          <!-- Task result for completed tasks -->
          <div v-if="task.status === 'completed' && task.problematic_commit" class="px-6 py-3 bg-green-50 border-t">
            <div class="flex items-center">
              <CheckCircleIcon class="h-5 w-5 text-green-400 mr-2" />
              <div class="flex-1">
                <p class="text-sm font-medium text-green-800">
                  Problematic commit identified
                </p>
                <p class="text-sm text-green-700 font-mono">
                  {{ task.problematic_commit.substring(0, 8) }}
                </p>
              </div>
              <div class="text-sm text-green-600">
                Found in {{ task.total_iterations || 0 }} iterations
              </div>
            </div>
          </div>

          <!-- Task error for failed tasks -->
          <div v-if="task.status === 'failed'" class="px-6 py-3 bg-red-50 border-t">
            <div class="flex items-center">
              <XCircleIcon class="h-5 w-5 text-red-400 mr-2" />
              <div class="flex-1">
                <p class="text-sm font-medium text-red-800">
                  Task failed
                </p>
                <p class="text-sm text-red-700">
                  {{ task.error_message || 'An error occurred during localization' }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="mt-8 flex items-center justify-between">
        <div class="flex-1 flex justify-between sm:hidden">
          <button
            @click="currentPage--"
            :disabled="currentPage <= 1"
            class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            Previous
          </button>
          <button
            @click="currentPage++"
            :disabled="currentPage >= totalPages"
            class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            Next
          </button>
        </div>
        <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
          <div>
            <p class="text-sm text-gray-700">
              Showing
              <span class="font-medium">{{ startIndex }}</span>
              to
              <span class="font-medium">{{ endIndex }}</span>
              of
              <span class="font-medium">{{ totalTasks }}</span>
              results
            </p>
          </div>
          <div>
            <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
              <button
                @click="currentPage--"
                :disabled="currentPage <= 1"
                class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
              >
                <ChevronLeftIcon class="h-5 w-5" />
              </button>
              <button
                v-for="page in visiblePages"
                :key="page"
                @click="currentPage = page"
                class="relative inline-flex items-center px-4 py-2 border text-sm font-medium"
                :class="page === currentPage
                  ? 'z-10 bg-primary-50 border-primary-500 text-primary-600'
                  : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'"
              >
                {{ page }}
              </button>
              <button
                @click="currentPage++"
                :disabled="currentPage >= totalPages"
                class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
              >
                <ChevronRightIcon class="h-5 w-5" />
              </button>
            </nav>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  RefreshCw as RefreshCwIcon,
  Plus as PlusIcon,
  Search as SearchIcon,
  Calendar as CalendarIcon,
  User as UserIcon,
  Target as TargetIcon,
  CheckCircle as CheckCircleIcon,
  XCircle as XCircleIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
} from 'lucide-vue-next'

import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import { api } from '@/utils/api'
import type { LocalizationTask } from '@/types'

const authStore = useAuthStore()
const notificationStore = useNotificationStore()

// State
const isLoading = ref(false)
const tasks = ref<LocalizationTask[]>([])
const searchQuery = ref('')
const statusFilter = ref<'active' | 'completed' | 'failed' | ''>('')
const sortBy = ref<'created_at' | 'updated_at' | 'status'>('created_at')
const currentPage = ref(1)
const itemsPerPage = 10

// Computed
const filteredTasks = computed(() => {
  let filtered = tasks.value

  // Apply search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(task => 
      task.project.name.toLowerCase().includes(query) ||
      task.description?.toLowerCase().includes(query)
    )
  }

  // Apply status filter
  if (statusFilter.value) {
    filtered = filtered.filter(task => task.status === statusFilter.value)
  }

  // Sort tasks
  filtered.sort((a, b) => {
    switch (sortBy.value) {
      case 'status':
        return a.status.localeCompare(b.status)
      case 'updated_at':
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      case 'created_at':
      default:
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    }
  })

  return filtered
})

const totalTasks = computed(() => filteredTasks.value.length)
const totalPages = computed(() => Math.ceil(totalTasks.value / itemsPerPage))
const startIndex = computed(() => (currentPage.value - 1) * itemsPerPage + 1)
const endIndex = computed(() => Math.min(currentPage.value * itemsPerPage, totalTasks.value))

const paginatedTasks = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return filteredTasks.value.slice(start, end)
})

const visiblePages = computed(() => {
  const pages = []
  const start = Math.max(1, currentPage.value - 2)
  const end = Math.min(totalPages.value, currentPage.value + 2)
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
})

// Methods
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  // Less than 1 day
  if (diff < 86400000) {
    const hours = Math.floor(diff / 3600000)
    if (hours === 0) {
      const minutes = Math.floor(diff / 60000)
      return minutes === 0 ? 'just now' : `${minutes}m ago`
    }
    return `${hours}h ago`
  }
  
  // Less than 1 week
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

const getProgress = (task: LocalizationTask) => {
  // Estimate progress based on iteration count
  // This is a simplified calculation - in production you'd have more sophisticated progress tracking
  const maxIterations = 10 // Typical binary search iterations
  const currentIteration = task.current_iteration || 0
  return Math.min(Math.round((currentIteration / maxIterations) * 100), 90)
}

const loadTasks = async () => {
  isLoading.value = true
  try {
    const data = await api.tasks.list()
    tasks.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('Failed to load tasks:', error)
    notificationStore.error('Failed to load tasks', 'Please try again later')
  } finally {
    isLoading.value = false
  }
}

const refreshTasks = async () => {
  await loadTasks()
  notificationStore.success('Tasks refreshed', 'Task list has been updated')
}

const clearFilters = () => {
  searchQuery.value = ''
  statusFilter.value = ''
  sortBy.value = 'created_at'
  currentPage.value = 1
}

// Watch for search/filter changes to reset pagination
watch([searchQuery, statusFilter, sortBy], () => {
  currentPage.value = 1
})

// Lifecycle
onMounted(async () => {
  await loadTasks()
})
</script>