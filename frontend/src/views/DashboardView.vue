<template>
  <div class="min-h-full">
    <!-- Page header -->
    <div class="bg-white shadow">
      <div class="px-4 sm:px-6 lg:max-w-6xl lg:mx-auto lg:px-8">
        <div class="py-6 md:flex md:items-center md:justify-between">
          <div class="min-w-0 flex-1">
            <div class="flex items-center">
              <div>
                <div class="flex items-center">
                  <h1 class="text-2xl font-bold leading-7 text-gray-900 sm:leading-9 sm:truncate">
                    Dashboard
                  </h1>
                </div>
                <dl class="mt-6 flex flex-col sm:mt-1 sm:flex-row sm:flex-wrap">
                  <dt class="sr-only">Account status</dt>
                  <dd class="flex items-center text-sm text-gray-500 font-medium capitalize sm:mr-6">
                    <CheckCircleIcon class="flex-shrink-0 mr-1.5 h-5 w-5 text-green-400" />
                    Welcome back, {{ authStore.user?.username }}
                  </dd>
                  <dt class="sr-only">Last login</dt>
                  <dd class="mt-3 flex items-center text-sm text-gray-500 font-medium sm:mr-6 sm:mt-0">
                    <CalendarIcon class="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" />
                    Last login: {{ formatDate(authStore.user?.last_login) }}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
          <div class="mt-6 flex space-x-3 md:mt-0 md:ml-4">
            <button
              @click="refreshData"
              :disabled="isRefreshing"
              class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              <RefreshCwIcon class="mr-2 h-4 w-4" :class="{ 'animate-spin': isRefreshing }" />
              Refresh
            </button>
            <router-link
              to="/projects/new"
              class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <PlusIcon class="mr-2 h-4 w-4" />
              New Project
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- Main content -->
    <div class="px-4 sm:px-6 lg:max-w-6xl lg:mx-auto lg:px-8 py-8">
      <!-- Stats overview -->
      <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="p-5">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <FolderIcon class="h-6 w-6 text-gray-400" />
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Total Projects</dt>
                  <dd class="text-lg font-medium text-gray-900">{{ stats.totalProjects }}</dd>
                </dl>
              </div>
            </div>
          </div>
          <div class="bg-gray-50 px-5 py-3">
            <div class="text-sm">
              <router-link to="/projects" class="font-medium text-primary-700 hover:text-primary-900">
                View all
              </router-link>
            </div>
          </div>
        </div>

        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="p-5">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <SearchIcon class="h-6 w-6 text-gray-400" />
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Active Tasks</dt>
                  <dd class="text-lg font-medium text-gray-900">{{ stats.activeTasks }}</dd>
                </dl>
              </div>
            </div>
          </div>
          <div class="bg-gray-50 px-5 py-3">
            <div class="text-sm">
              <router-link to="/tasks" class="font-medium text-primary-700 hover:text-primary-900">
                View all
              </router-link>
            </div>
          </div>
        </div>

        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="p-5">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <CheckCircleIcon class="h-6 w-6 text-gray-400" />
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Completed Tasks</dt>
                  <dd class="text-lg font-medium text-gray-900">{{ stats.completedTasks }}</dd>
                </dl>
              </div>
            </div>
          </div>
          <div class="bg-gray-50 px-5 py-3">
            <div class="text-sm">
              <span class="text-green-600 font-medium">
                +{{ stats.completedThisWeek }} this week
              </span>
            </div>
          </div>
        </div>

        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="p-5">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <ClockIcon class="h-6 w-6 text-gray-400" />
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Avg Resolution Time</dt>
                  <dd class="text-lg font-medium text-gray-900">{{ stats.avgResolutionTime }}</dd>
                </dl>
              </div>
            </div>
          </div>
          <div class="bg-gray-50 px-5 py-3">
            <div class="text-sm">
              <span class="text-gray-500">
                Based on last 30 tasks
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Main content grid -->
      <div class="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-2">
        <!-- Recent Tasks -->
        <div class="bg-white shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg leading-6 font-medium text-gray-900">Recent Tasks</h3>
              <router-link
                to="/tasks"
                class="text-sm font-medium text-primary-600 hover:text-primary-500"
              >
                View all
              </router-link>
            </div>
            <div v-if="recentTasks.length === 0" class="text-center py-8">
              <SearchIcon class="mx-auto h-12 w-12 text-gray-400" />
              <h3 class="mt-2 text-sm font-medium text-gray-900">No tasks yet</h3>
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
            <div v-else class="space-y-4">
              <div
                v-for="task in recentTasks"
                :key="task.id"
                class="border rounded-lg p-4 hover:bg-gray-50 transition-colors duration-200"
              >
                <div class="flex items-center justify-between">
                  <div class="flex-1">
                    <div class="flex items-center">
                      <h4 class="text-sm font-medium text-gray-900">
                        {{ task.project.name }}
                      </h4>
                      <span
                        class="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                        :class="getTaskStatusClass(task.status)"
                      >
                        {{ task.status }}
                      </span>
                    </div>
                    <p class="mt-1 text-sm text-gray-500">
                      {{ task.description || 'Binary search localization task' }}
                    </p>
                    <div class="mt-2 flex items-center text-xs text-gray-500">
                      <CalendarIcon class="mr-1 h-3 w-3" />
                      {{ formatDate(task.created_at) }}
                      <span class="mx-2">•</span>
                      <UserIcon class="mr-1 h-3 w-3" />
                      {{ task.user.username }}
                    </div>
                  </div>
                  <router-link
                    :to="`/tasks/${task.id}`"
                    class="ml-4 text-sm font-medium text-primary-600 hover:text-primary-500"
                  >
                    View
                  </router-link>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Projects -->
        <div class="bg-white shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg leading-6 font-medium text-gray-900">Recent Projects</h3>
              <router-link
                to="/projects"
                class="text-sm font-medium text-primary-600 hover:text-primary-500"
              >
                View all
              </router-link>
            </div>
            <div v-if="recentProjects.length === 0" class="text-center py-8">
              <FolderIcon class="mx-auto h-12 w-12 text-gray-400" />
              <h3 class="mt-2 text-sm font-medium text-gray-900">No projects yet</h3>
              <p class="mt-1 text-sm text-gray-500">Get started by creating your first project.</p>
              <div class="mt-6">
                <router-link
                  to="/projects/new"
                  class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  <PlusIcon class="mr-2 h-4 w-4" />
                  New Project
                </router-link>
              </div>
            </div>
            <div v-else class="space-y-4">
              <div
                v-for="project in recentProjects"
                :key="project.id"
                class="border rounded-lg p-4 hover:bg-gray-50 transition-colors duration-200"
              >
                <div class="flex items-center justify-between">
                  <div class="flex-1">
                    <div class="flex items-center">
                      <h4 class="text-sm font-medium text-gray-900">
                        {{ project.name }}
                      </h4>
                      <span
                        v-if="project.is_active"
                        class="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
                      >
                        Active
                      </span>
                    </div>
                    <p class="mt-1 text-sm text-gray-500">
                      {{ project.description || 'No description' }}
                    </p>
                    <div class="mt-2 flex items-center text-xs text-gray-500">
                      <CalendarIcon class="mr-1 h-3 w-3" />
                      Updated {{ formatDate(project.updated_at) }}
                      <span class="mx-2">•</span>
                      <TagIcon class="mr-1 h-3 w-3" />
                      {{ project.tags?.length || 0 }} tags
                    </div>
                  </div>
                  <router-link
                    :to="`/projects/${project.id}`"
                    class="ml-4 text-sm font-medium text-primary-600 hover:text-primary-500"
                  >
                    View
                  </router-link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Activity timeline -->
      <div class="mt-8 bg-white shadow rounded-lg">
        <div class="px-4 py-5 sm:p-6">
          <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Recent Activity</h3>
          <div v-if="recentActivity.length === 0" class="text-center py-8">
            <ClockIcon class="mx-auto h-12 w-12 text-gray-400" />
            <h3 class="mt-2 text-sm font-medium text-gray-900">No recent activity</h3>
            <p class="mt-1 text-sm text-gray-500">Activity will appear here as you use the system.</p>
          </div>
          <div v-else class="flow-root">
            <ul class="-mb-8">
              <li v-for="(activity, index) in recentActivity" :key="activity.id">
                <div class="relative pb-8">
                  <span
                    v-if="index !== recentActivity.length - 1"
                    class="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                    aria-hidden="true"
                  ></span>
                  <div class="relative flex space-x-3">
                    <div>
                      <span
                        class="h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white"
                        :class="getActivityIconClass(activity.type)"
                      >
                        <component :is="getActivityIcon(activity.type)" class="h-5 w-5 text-white" />
                      </span>
                    </div>
                    <div class="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                      <div>
                        <p class="text-sm text-gray-500">
                          {{ activity.description }}
                        </p>
                      </div>
                      <div class="text-right text-sm whitespace-nowrap text-gray-500">
                        {{ formatDate(activity.timestamp) }}
                      </div>
                    </div>
                  </div>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  CheckCircle as CheckCircleIcon,
  Calendar as CalendarIcon,
  RefreshCw as RefreshCwIcon,
  Plus as PlusIcon,
  Folder as FolderIcon,
  Search as SearchIcon,
  Clock as ClockIcon,
  User as UserIcon,
  Tag as TagIcon,
} from 'lucide-vue-next'

import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import type { Project, LocalizationTask, User } from '@/types'

const authStore = useAuthStore()
const notificationStore = useNotificationStore()

// State
const isRefreshing = ref(false)
const stats = ref({
  totalProjects: 0,
  activeTasks: 0,
  completedTasks: 0,
  completedThisWeek: 0,
  avgResolutionTime: '0 min'
})

const recentTasks = ref<LocalizationTask[]>([])
const recentProjects = ref<Project[]>([])
const recentActivity = ref<{
  id: string
  type: 'task_created' | 'task_completed' | 'project_created' | 'project_updated'
  description: string
  timestamp: string
}[]>([])

// Computed
const isLoading = computed(() => authStore.isLoading)

// Methods
const formatDate = (dateString?: string) => {
  if (!dateString) return 'Never'
  
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  // Less than 1 minute
  if (diff < 60000) return 'Just now'
  
  // Less than 1 hour
  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000)
    return `${minutes} minute${minutes > 1 ? 's' : ''} ago`
  }
  
  // Less than 1 day
  if (diff < 86400000) {
    const hours = Math.floor(diff / 3600000)
    return `${hours} hour${hours > 1 ? 's' : ''} ago`
  }
  
  // Less than 1 week
  if (diff < 604800000) {
    const days = Math.floor(diff / 86400000)
    return `${days} day${days > 1 ? 's' : ''} ago`
  }
  
  // Format as date
  return date.toLocaleDateString()
}

const getTaskStatusClass = (status: string) => {
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

const getActivityIconClass = (type: string) => {
  switch (type) {
    case 'task_created':
      return 'bg-blue-500'
    case 'task_completed':
      return 'bg-green-500'
    case 'project_created':
      return 'bg-purple-500'
    case 'project_updated':
      return 'bg-yellow-500'
    default:
      return 'bg-gray-500'
  }
}

const getActivityIcon = (type: string) => {
  switch (type) {
    case 'task_created':
      return SearchIcon
    case 'task_completed':
      return CheckCircleIcon
    case 'project_created':
    case 'project_updated':
      return FolderIcon
    default:
      return ClockIcon
  }
}

const loadDashboardData = async () => {
  // Mock data for now - in production, these would be API calls
  stats.value = {
    totalProjects: 12,
    activeTasks: 3,
    completedTasks: 47,
    completedThisWeek: 8,
    avgResolutionTime: '2.5 hrs'
  }

  // Mock recent tasks
  recentTasks.value = []

  // Mock recent projects  
  recentProjects.value = []

  // Mock recent activity
  recentActivity.value = []
}

const refreshData = async () => {
  isRefreshing.value = true
  try {
    await loadDashboardData()
    notificationStore.success('Data Refreshed', 'Dashboard data has been updated')
  } catch (error) {
    notificationStore.error('Refresh Failed', 'Failed to refresh dashboard data')
  } finally {
    isRefreshing.value = false
  }
}

// Lifecycle
onMounted(async () => {
  await loadDashboardData()
})
</script>