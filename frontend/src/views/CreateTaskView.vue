<template>
  <div class="min-h-full">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Header -->
      <div class="mb-8">
        <nav class="flex" aria-label="Breadcrumb">
          <ol class="flex items-center space-x-4">
            <li>
              <div>
                <router-link to="/tasks" class="text-gray-400 hover:text-gray-500">
                  <ChevronLeftIcon class="h-5 w-5" />
                  Tasks
                </router-link>
              </div>
            </li>
            <li>
              <div class="flex items-center">
                <ChevronRightIcon class="flex-shrink-0 h-5 w-5 text-gray-300" />
                <span class="ml-4 text-sm font-medium text-gray-500">Create Task</span>
              </div>
            </li>
          </ol>
        </nav>
        <div class="mt-4">
          <h1 class="text-3xl font-bold leading-tight text-gray-900">Create New Localization Task</h1>
          <p class="mt-2 text-sm text-gray-600">
            Set up a binary search task to identify problematic commits in your codebase.
          </p>
        </div>
      </div>

      <!-- Main Form -->
      <form @submit.prevent="createTask" class="space-y-8">
        <!-- Project Selection -->
        <div class="bg-white shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Project Selection</h3>
            
            <div class="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
              <div class="sm:col-span-6">
                <label for="project" class="block text-sm font-medium text-gray-700">
                  Project *
                </label>
                <select
                  id="project"
                  v-model="form.project_id"
                  required
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  :class="{ 'border-red-300': errors.project_id }"
                >
                  <option value="">Select a project</option>
                  <option v-for="project in projects" :key="project.id" :value="project.id">
                    {{ project.name }} - {{ project.repository_url }}
                  </option>
                </select>
                <p v-if="errors.project_id" class="mt-2 text-sm text-red-600">{{ errors.project_id }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Task Configuration -->
        <div class="bg-white shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Task Configuration</h3>
            
            <div class="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
              <div class="sm:col-span-6">
                <label for="title" class="block text-sm font-medium text-gray-700">
                  Task Title *
                </label>
                <input
                  type="text"
                  id="title"
                  v-model="form.title"
                  required
                  placeholder="e.g., Fix authentication bug in user login"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  :class="{ 'border-red-300': errors.title }"
                />
                <p v-if="errors.title" class="mt-2 text-sm text-red-600">{{ errors.title }}</p>
              </div>

              <div class="sm:col-span-6">
                <label for="description" class="block text-sm font-medium text-gray-700">
                  Description
                </label>
                <textarea
                  id="description"
                  v-model="form.description"
                  rows="3"
                  placeholder="Describe the issue you're trying to locate..."
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                ></textarea>
              </div>
            </div>
          </div>
        </div>

        <!-- Commit Range -->
        <div class="bg-white shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Commit Range</h3>
            <p class="text-sm text-gray-600 mb-4">
              Define the range of commits to search. The binary search will find the first "bad" commit between these points.
            </p>
            
            <div class="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-2">
              <div>
                <label for="good_commit" class="block text-sm font-medium text-gray-700">
                  Good Commit (Known Working) *
                </label>
                <div class="mt-1 flex rounded-md shadow-sm">
                  <input
                    type="text"
                    id="good_commit"
                    v-model="form.good_commit"
                    required
                    placeholder="e.g., abc123ef or v1.0.0"
                    class="flex-1 block w-full px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    :class="{ 'border-red-300': errors.good_commit }"
                  />
                  <button
                    type="button"
                    @click="validateCommit('good')"
                    class="inline-flex items-center px-3 py-2 border border-l-0 border-gray-300 rounded-r-md bg-gray-50 text-gray-500 text-sm hover:bg-gray-100"
                  >
                    <CheckCircleIcon class="h-4 w-4" />
                  </button>
                </div>
                <p v-if="errors.good_commit" class="mt-2 text-sm text-red-600">{{ errors.good_commit }}</p>
                <p class="mt-1 text-xs text-gray-500">Commit hash, tag, or branch name where the issue doesn't exist</p>
              </div>

              <div>
                <label for="bad_commit" class="block text-sm font-medium text-gray-700">
                  Bad Commit (Known Broken) *
                </label>
                <div class="mt-1 flex rounded-md shadow-sm">
                  <input
                    type="text"
                    id="bad_commit"
                    v-model="form.bad_commit"
                    required
                    placeholder="e.g., def456gh or main"
                    class="flex-1 block w-full px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    :class="{ 'border-red-300': errors.bad_commit }"
                  />
                  <button
                    type="button"
                    @click="validateCommit('bad')"
                    class="inline-flex items-center px-3 py-2 border border-l-0 border-gray-300 rounded-r-md bg-gray-50 text-gray-500 text-sm hover:bg-gray-100"
                  >
                    <CheckCircleIcon class="h-4 w-4" />
                  </button>
                </div>
                <p v-if="errors.bad_commit" class="mt-2 text-sm text-red-600">{{ errors.bad_commit }}</p>
                <p class="mt-1 text-xs text-gray-500">Commit hash, tag, or branch name where the issue exists</p>
              </div>
            </div>

            <!-- Commit Range Preview -->
            <div v-if="commitRange.total > 0" class="mt-4 p-4 bg-blue-50 rounded-lg">
              <div class="flex">
                <InfoIcon class="flex-shrink-0 h-5 w-5 text-blue-400" />
                <div class="ml-3">
                  <h4 class="text-sm font-medium text-blue-800">Commit Range Analysis</h4>
                  <div class="mt-2 text-sm text-blue-700">
                    <p>{{ commitRange.total }} commits will be searched</p>
                    <p>Expected iterations: ~{{ Math.ceil(Math.log2(commitRange.total)) }}</p>
                    <p>Estimated time: {{ estimatedTime }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Build Configuration -->
        <div class="bg-white shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Build & Test Configuration</h3>
            
            <div class="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
              <div class="sm:col-span-3">
                <label for="build_command" class="block text-sm font-medium text-gray-700">
                  Build Command
                </label>
                <input
                  type="text"
                  id="build_command"
                  v-model="form.build_command"
                  placeholder="e.g., npm run build"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                />
                <p class="mt-1 text-xs text-gray-500">Command to build/compile the project</p>
              </div>

              <div class="sm:col-span-3">
                <label for="test_command" class="block text-sm font-medium text-gray-700">
                  Test Command
                </label>
                <input
                  type="text"
                  id="test_command"
                  v-model="form.test_command"
                  placeholder="e.g., npm test"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                />
                <p class="mt-1 text-xs text-gray-500">Command to run tests that detect the issue</p>
              </div>

              <div class="sm:col-span-6">
                <label for="environment_vars" class="block text-sm font-medium text-gray-700">
                  Environment Variables
                </label>
                <textarea
                  id="environment_vars"
                  v-model="form.environment_vars"
                  rows="2"
                  placeholder="KEY1=value1&#10;KEY2=value2"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm font-mono text-xs"
                ></textarea>
                <p class="mt-1 text-xs text-gray-500">One variable per line in KEY=value format</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Advanced Options -->
        <div class="bg-white shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg leading-6 font-medium text-gray-900">Advanced Options</h3>
              <button
                type="button"
                @click="showAdvanced = !showAdvanced"
                class="text-sm text-primary-600 hover:text-primary-500"
              >
                {{ showAdvanced ? 'Hide' : 'Show' }} Advanced
              </button>
            </div>

            <div v-if="showAdvanced" class="space-y-6">
              <div class="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-2">
                <div>
                  <label for="timeout" class="block text-sm font-medium text-gray-700">
                    Timeout (minutes)
                  </label>
                  <input
                    type="number"
                    id="timeout"
                    v-model.number="form.timeout"
                    min="1"
                    max="60"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  />
                  <p class="mt-1 text-xs text-gray-500">Maximum time to wait for each build/test</p>
                </div>

                <div>
                  <label for="parallel_jobs" class="block text-sm font-medium text-gray-700">
                    Parallel Jobs
                  </label>
                  <input
                    type="number"
                    id="parallel_jobs"
                    v-model.number="form.parallel_jobs"
                    min="1"
                    max="10"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  />
                  <p class="mt-1 text-xs text-gray-500">Number of parallel builds (if supported)</p>
                </div>
              </div>

              <div>
                <div class="flex items-start">
                  <div class="flex items-center h-5">
                    <input
                      id="auto_skip_merge_commits"
                      v-model="form.auto_skip_merge_commits"
                      type="checkbox"
                      class="focus:ring-primary-500 h-4 w-4 text-primary-600 border-gray-300 rounded"
                    />
                  </div>
                  <div class="ml-3 text-sm">
                    <label for="auto_skip_merge_commits" class="font-medium text-gray-700">
                      Auto-skip merge commits
                    </label>
                    <p class="text-gray-500">Automatically skip merge commits during binary search</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Form Actions -->
        <div class="flex justify-end space-x-3">
          <router-link
            to="/tasks"
            class="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Cancel
          </router-link>
          <button
            type="button"
            @click="saveDraft"
            :disabled="isLoading"
            class="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
          >
            Save Draft
          </button>
          <button
            type="submit"
            :disabled="isLoading || !isFormValid"
            class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
          >
            <LoaderIcon v-if="isLoading" class="animate-spin -ml-1 mr-3 h-5 w-5" />
            {{ isLoading ? 'Creating...' : 'Create Task' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon,
  Loader as LoaderIcon,
} from 'lucide-vue-next'

import { api } from '@/utils/api'
import { useNotificationStore } from '@/stores/notification'
import type { Project } from '@/types'

// Router and stores
const router = useRouter()
const notificationStore = useNotificationStore()

// State
const projects = ref<Project[]>([])
const isLoading = ref(false)
const showAdvanced = ref(false)

// Form data
const form = ref({
  project_id: '',
  title: '',
  description: '',
  good_commit: '',
  bad_commit: '',
  build_command: 'npm run build',
  test_command: 'npm test',
  environment_vars: '',
  timeout: 30,
  parallel_jobs: 1,
  auto_skip_merge_commits: true,
})

// Form validation
const errors = ref<Record<string, string>>({})

const isFormValid = computed(() => {
  return form.value.project_id && 
         form.value.title && 
         form.value.good_commit && 
         form.value.bad_commit &&
         Object.keys(errors.value).length === 0
})

// Commit range analysis
const commitRange = ref({
  total: 0,
  commits: [] as any[]
})

const estimatedTime = computed(() => {
  const iterations = Math.ceil(Math.log2(commitRange.value.total))
  const timePerIteration = form.value.timeout || 30
  const totalMinutes = iterations * timePerIteration
  
  if (totalMinutes < 60) {
    return `${totalMinutes} minutes`
  } else {
    const hours = Math.floor(totalMinutes / 60)
    const minutes = totalMinutes % 60
    return `${hours}h ${minutes}m`
  }
})

// Watchers
watch([() => form.value.good_commit, () => form.value.bad_commit, () => form.value.project_id], 
  async () => {
    if (form.value.project_id && form.value.good_commit && form.value.bad_commit) {
      await analyzeCommitRange()
    }
  }
)

// Methods
const loadProjects = async () => {
  try {
    const response = await api.projects.list({ active: true })
    projects.value = response.data || response
  } catch (error) {
    console.error('Failed to load projects:', error)
    notificationStore.addNotification({
      type: 'error',
      title: 'Error',
      message: 'Failed to load projects'
    })
  }
}

const validateCommit = async (type: 'good' | 'bad') => {
  const commit = form.value[`${type}_commit`]
  if (!commit || !form.value.project_id) return

  try {
    // In a real implementation, this would validate the commit exists
    // For now, just clear any existing errors
    delete errors.value[`${type}_commit`]
    
    notificationStore.addNotification({
      type: 'success',
      title: 'Commit Valid',
      message: `${type} commit "${commit}" is valid`
    })
  } catch (error) {
    errors.value[`${type}_commit`] = `Invalid commit: ${commit}`
  }
}

const analyzeCommitRange = async () => {
  if (!form.value.project_id || !form.value.good_commit || !form.value.bad_commit) return

  try {
    // Mock commit range analysis
    // In reality, this would call the API to get the commit range
    commitRange.value = {
      total: Math.floor(Math.random() * 50) + 10, // 10-60 commits
      commits: []
    }
  } catch (error) {
    console.error('Failed to analyze commit range:', error)
  }
}

const validateForm = () => {
  errors.value = {}

  if (!form.value.project_id) {
    errors.value.project_id = 'Project is required'
  }
  if (!form.value.title) {
    errors.value.title = 'Title is required'
  }
  if (!form.value.good_commit) {
    errors.value.good_commit = 'Good commit is required'
  }
  if (!form.value.bad_commit) {
    errors.value.bad_commit = 'Bad commit is required'
  }

  return Object.keys(errors.value).length === 0
}

const saveDraft = async () => {
  if (!validateForm()) return

  isLoading.value = true
  
  try {
    // Save as draft
    const draftData = { ...form.value, status: 'draft' }
    await api.tasks.create(draftData)
    
    notificationStore.addNotification({
      type: 'success',
      title: 'Draft Saved',
      message: 'Task draft has been saved successfully'
    })
    
    router.push('/tasks')
  } catch (error) {
    console.error('Failed to save draft:', error)
    notificationStore.addNotification({
      type: 'error',
      title: 'Error',
      message: 'Failed to save draft'
    })
  } finally {
    isLoading.value = false
  }
}

const createTask = async () => {
  if (!validateForm()) return

  isLoading.value = true

  try {
    // Parse environment variables
    const envVars: Record<string, string> = {}
    if (form.value.environment_vars) {
      form.value.environment_vars.split('\n').forEach(line => {
        const [key, ...valueParts] = line.trim().split('=')
        if (key && valueParts.length > 0) {
          envVars[key] = valueParts.join('=')
        }
      })
    }

    const taskData = {
      ...form.value,
      environment_vars: envVars,
      status: 'pending'
    }

    const newTask = await api.tasks.create(taskData)
    
    notificationStore.addNotification({
      type: 'success',
      title: 'Task Created',
      message: 'Localization task has been created successfully'
    })
    
    // Navigate to the new task
    router.push(`/tasks/${newTask.id}`)
  } catch (error) {
    console.error('Failed to create task:', error)
    notificationStore.addNotification({
      type: 'error',
      title: 'Error',
      message: 'Failed to create task'
    })
  } finally {
    isLoading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadProjects()
})
</script>