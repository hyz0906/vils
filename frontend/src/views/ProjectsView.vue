<template>
  <div class="min-h-full">
    <!-- Page header -->
    <div class="bg-white shadow">
      <div class="px-4 sm:px-6 lg:max-w-6xl lg:mx-auto lg:px-8">
        <div class="py-6 md:flex md:items-center md:justify-between">
          <div class="min-w-0 flex-1">
            <h1 class="text-2xl font-bold leading-7 text-gray-900 sm:leading-9 sm:truncate">
              Projects
            </h1>
            <p class="mt-1 text-sm text-gray-500">
              Manage your localization projects and their configurations
            </p>
          </div>
          <div class="mt-6 flex space-x-3 md:mt-0 md:ml-4">
            <button
              @click="refreshProjects"
              :disabled="isLoading"
              class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              <RefreshCwIcon class="mr-2 h-4 w-4" :class="{ 'animate-spin': isLoading }" />
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
                placeholder="Search projects..."
              />
            </div>
          </div>

          <!-- Filter dropdown -->
          <div class="relative" ref="filterDropdownRef">
            <button
              @click="toggleFilterDropdown"
              class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <FilterIcon class="mr-2 h-4 w-4" />
              Filter
              <ChevronDownIcon class="ml-2 h-4 w-4" />
            </button>
            
            <transition
              enter-active-class="transition ease-out duration-100"
              enter-from-class="transform opacity-0 scale-95"
              enter-to-class="transform opacity-100 scale-100"
              leave-active-class="transition ease-in duration-75"
              leave-from-class="transform opacity-100 scale-100"
              leave-to-class="transform opacity-0 scale-95"
            >
              <div
                v-if="showFilterDropdown"
                class="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-50"
              >
                <div class="py-1">
                  <label class="flex items-center px-4 py-2 text-sm text-gray-700">
                    <input
                      v-model="filters.active"
                      type="checkbox"
                      class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    />
                    <span class="ml-2">Active projects only</span>
                  </label>
                  <label class="flex items-center px-4 py-2 text-sm text-gray-700">
                    <input
                      v-model="filters.myProjects"
                      type="checkbox"
                      class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    />
                    <span class="ml-2">My projects only</span>
                  </label>
                  <hr class="my-1" />
                  <div class="px-4 py-2">
                    <label class="block text-sm font-medium text-gray-700 mb-1">Sort by</label>
                    <select
                      v-model="sortBy"
                      class="block w-full text-sm border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="updated_at">Last updated</option>
                      <option value="created_at">Created date</option>
                      <option value="name">Name</option>
                    </select>
                  </div>
                </div>
              </div>
            </transition>
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
          Loading projects...
        </div>
      </div>

      <!-- Empty state -->
      <div v-else-if="filteredProjects.length === 0 && !searchQuery" class="text-center py-12">
        <FolderIcon class="mx-auto h-12 w-12 text-gray-400" />
        <h3 class="mt-2 text-sm font-medium text-gray-900">No projects</h3>
        <p class="mt-1 text-sm text-gray-500">Get started by creating a new project.</p>
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

      <!-- No results state -->
      <div v-else-if="filteredProjects.length === 0 && searchQuery" class="text-center py-12">
        <SearchIcon class="mx-auto h-12 w-12 text-gray-400" />
        <h3 class="mt-2 text-sm font-medium text-gray-900">No projects found</h3>
        <p class="mt-1 text-sm text-gray-500">
          No projects match your search criteria. Try adjusting your filters.
        </p>
        <div class="mt-6">
          <button
            @click="clearFilters"
            class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Clear filters
          </button>
        </div>
      </div>

      <!-- Projects grid -->
      <div v-else class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <div
          v-for="project in filteredProjects"
          :key="project.id"
          class="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow duration-200"
        >
          <div class="p-6">
            <!-- Project header -->
            <div class="flex items-start justify-between">
              <div class="flex-1 min-w-0">
                <h3 class="text-lg font-medium text-gray-900 truncate">
                  <router-link
                    :to="`/projects/${project.id}`"
                    class="hover:text-primary-600 transition-colors duration-200"
                  >
                    {{ project.name }}
                  </router-link>
                </h3>
                <p class="mt-1 text-sm text-gray-500 line-clamp-2">
                  {{ project.description || 'No description provided' }}
                </p>
              </div>
              
              <!-- Status badge -->
              <span
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                :class="project.is_active 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-gray-100 text-gray-800'"
              >
                {{ project.is_active ? 'Active' : 'Inactive' }}
              </span>
            </div>

            <!-- Project stats -->
            <div class="mt-4 grid grid-cols-2 gap-4">
              <div class="text-center">
                <div class="text-2xl font-semibold text-gray-900">
                  {{ project.tags?.length || 0 }}
                </div>
                <div class="text-xs text-gray-500">Tags</div>
              </div>
              <div class="text-center">
                <div class="text-2xl font-semibold text-gray-900">
                  {{ getProjectTaskCount(project.id) }}
                </div>
                <div class="text-xs text-gray-500">Tasks</div>
              </div>
            </div>

            <!-- Project metadata -->
            <div class="mt-4 flex items-center justify-between text-sm text-gray-500">
              <div class="flex items-center">
                <CalendarIcon class="flex-shrink-0 mr-1 h-4 w-4" />
                <span>Updated {{ formatDate(project.updated_at) }}</span>
              </div>
              <div class="flex items-center">
                <UserIcon class="flex-shrink-0 mr-1 h-4 w-4" />
                <span>{{ project.owner.username }}</span>
              </div>
            </div>

            <!-- Project actions -->
            <div class="mt-6 flex justify-between">
              <router-link
                :to="`/projects/${project.id}`"
                class="text-sm font-medium text-primary-600 hover:text-primary-500"
              >
                View project
              </router-link>
              
              <div class="flex space-x-2">
                <button
                  @click="startLocalization(project)"
                  :disabled="!project.is_active"
                  class="text-sm font-medium text-gray-600 hover:text-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Start task
                </button>
                <router-link
                  :to="`/projects/${project.id}/edit`"
                  class="text-sm font-medium text-gray-600 hover:text-gray-500"
                >
                  Edit
                </router-link>
              </div>
            </div>
          </div>
          
          <!-- Project tags -->
          <div v-if="project.tags && project.tags.length > 0" class="px-6 py-3 bg-gray-50 border-t">
            <div class="flex flex-wrap gap-2">
              <span
                v-for="tag in project.tags.slice(0, 3)"
                :key="tag.id"
                class="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-primary-100 text-primary-800"
              >
                {{ tag.name }}
              </span>
              <span
                v-if="project.tags.length > 3"
                class="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-800"
              >
                +{{ project.tags.length - 3 }} more
              </span>
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
              <span class="font-medium">{{ totalProjects }}</span>
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
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  RefreshCw as RefreshCwIcon,
  Plus as PlusIcon,
  Search as SearchIcon,
  Filter as FilterIcon,
  ChevronDown as ChevronDownIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  Folder as FolderIcon,
  Calendar as CalendarIcon,
  User as UserIcon,
} from 'lucide-vue-next'

import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import type { Project } from '@/types'

const router = useRouter()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

// State
const isLoading = ref(false)
const projects = ref<Project[]>([])
const searchQuery = ref('')
const sortBy = ref<'updated_at' | 'created_at' | 'name'>('updated_at')
const currentPage = ref(1)
const itemsPerPage = 12

const filters = ref({
  active: false,
  myProjects: false
})

const showFilterDropdown = ref(false)
const filterDropdownRef = ref<HTMLElement>()

// Mock task counts for projects
const taskCounts = ref<Record<string, number>>({})

// Computed
const filteredProjects = computed(() => {
  let filtered = projects.value

  // Apply search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(project => 
      project.name.toLowerCase().includes(query) ||
      project.description?.toLowerCase().includes(query)
    )
  }

  // Apply other filters
  if (filters.value.active) {
    filtered = filtered.filter(project => project.is_active)
  }

  if (filters.value.myProjects && authStore.user) {
    filtered = filtered.filter(project => project.owner.id === authStore.user?.id)
  }

  // Sort projects
  filtered.sort((a, b) => {
    switch (sortBy.value) {
      case 'name':
        return a.name.localeCompare(b.name)
      case 'created_at':
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      case 'updated_at':
      default:
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    }
  })

  return filtered
})

const totalProjects = computed(() => filteredProjects.value.length)
const totalPages = computed(() => Math.ceil(totalProjects.value / itemsPerPage))
const startIndex = computed(() => (currentPage.value - 1) * itemsPerPage + 1)
const endIndex = computed(() => Math.min(currentPage.value * itemsPerPage, totalProjects.value))

const paginatedProjects = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return filteredProjects.value.slice(start, end)
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
      return minutes === 0 ? 'Just now' : `${minutes}m ago`
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

const getProjectTaskCount = (projectId: string) => {
  return taskCounts.value[projectId] || 0
}

const loadProjects = async () => {
  isLoading.value = true
  try {
    // Mock data - in production this would be an API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    projects.value = [
      {
        id: '1',
        name: 'Frontend Localization',
        description: 'Identify problematic commits in the frontend application',
        is_active: true,
        repository_url: 'https://github.com/company/frontend',
        build_command: 'npm run build',
        test_command: 'npm test',
        created_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
        updated_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
        owner: {
          id: authStore.user?.id || '1',
          username: authStore.user?.username || 'john_doe',
          email: authStore.user?.email || 'john@example.com',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          is_active: true
        },
        tags: [
          { id: '1', name: 'frontend', color: '#3B82F6', created_at: new Date().toISOString() },
          { id: '2', name: 'react', color: '#10B981', created_at: new Date().toISOString() }
        ]
      },
      {
        id: '2',
        name: 'Backend API Issues',
        description: 'Track down performance regressions in the API',
        is_active: true,
        repository_url: 'https://github.com/company/backend',
        build_command: 'python -m pytest',
        test_command: 'python -m pytest tests/',
        created_at: new Date(Date.now() - 172800000).toISOString(), // 2 days ago
        updated_at: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
        owner: {
          id: '2',
          username: 'jane_smith',
          email: 'jane@example.com',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          is_active: true
        },
        tags: [
          { id: '3', name: 'backend', color: '#F59E0B', created_at: new Date().toISOString() },
          { id: '4', name: 'python', color: '#8B5CF6', created_at: new Date().toISOString() }
        ]
      }
    ]
    
    // Mock task counts
    taskCounts.value = {
      '1': 5,
      '2': 3
    }
    
  } catch (error) {
    notificationStore.error('Failed to load projects', 'Please try again later')
  } finally {
    isLoading.value = false
  }
}

const refreshProjects = async () => {
  await loadProjects()
  notificationStore.success('Projects refreshed', 'Project list has been updated')
}

const startLocalization = (project: Project) => {
  router.push(`/tasks/new?project=${project.id}`)
}

const toggleFilterDropdown = () => {
  showFilterDropdown.value = !showFilterDropdown.value
}

const clearFilters = () => {
  searchQuery.value = ''
  filters.value.active = false
  filters.value.myProjects = false
  sortBy.value = 'updated_at'
  currentPage.value = 1
}

// Click outside handler for filter dropdown
const handleClickOutside = (event: Event) => {
  if (filterDropdownRef.value && !filterDropdownRef.value.contains(event.target as Node)) {
    showFilterDropdown.value = false
  }
}

// Watch for search/filter changes to reset pagination
watch([searchQuery, filters, sortBy], () => {
  currentPage.value = 1
}, { deep: true })

// Lifecycle
onMounted(async () => {
  await loadProjects()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>