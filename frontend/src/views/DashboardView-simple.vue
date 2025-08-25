<template>
  <div class="min-h-full p-8">
    <div class="bg-white shadow rounded-lg">
      <div class="px-4 py-5 sm:p-6">
        <h1 class="text-2xl font-bold text-gray-900 mb-4">VILS Dashboard</h1>
        <p class="text-gray-600 mb-4">Welcome to the Version Issue Locator System!</p>
        
        <!-- Simple stats -->
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <div class="bg-gray-50 overflow-hidden shadow rounded-lg">
            <div class="p-5">
              <div class="flex items-center">
                <div class="flex-shrink-0">
                  <div class="h-6 w-6 bg-blue-500 rounded"></div>
                </div>
                <div class="ml-5 w-0 flex-1">
                  <dl>
                    <dt class="text-sm font-medium text-gray-500 truncate">Total Projects</dt>
                    <dd class="text-lg font-medium text-gray-900">{{ mockStats.totalProjects }}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
          
          <div class="bg-gray-50 overflow-hidden shadow rounded-lg">
            <div class="p-5">
              <div class="flex items-center">
                <div class="flex-shrink-0">
                  <div class="h-6 w-6 bg-green-500 rounded"></div>
                </div>
                <div class="ml-5 w-0 flex-1">
                  <dl>
                    <dt class="text-sm font-medium text-gray-500 truncate">Active Tasks</dt>
                    <dd class="text-lg font-medium text-gray-900">{{ mockStats.activeTasks }}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
          
          <div class="bg-gray-50 overflow-hidden shadow rounded-lg">
            <div class="p-5">
              <div class="flex items-center">
                <div class="flex-shrink-0">
                  <div class="h-6 w-6 bg-purple-500 rounded"></div>
                </div>
                <div class="ml-5 w-0 flex-1">
                  <dl>
                    <dt class="text-sm font-medium text-gray-500 truncate">Completed Tasks</dt>
                    <dd class="text-lg font-medium text-gray-900">{{ mockStats.completedTasks }}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
          
          <div class="bg-gray-50 overflow-hidden shadow rounded-lg">
            <div class="p-5">
              <div class="flex items-center">
                <div class="flex-shrink-0">
                  <div class="h-6 w-6 bg-yellow-500 rounded"></div>
                </div>
                <div class="ml-5 w-0 flex-1">
                  <dl>
                    <dt class="text-sm font-medium text-gray-500 truncate">Success Rate</dt>
                    <dd class="text-lg font-medium text-gray-900">{{ mockStats.successRate }}%</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Action buttons -->
        <div class="flex space-x-4">
          <router-link
            to="/projects"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            View Projects
          </router-link>
          <router-link
            to="/tasks"
            class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            View Tasks
          </router-link>
        </div>
        
        <div class="mt-8">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Getting Started</h3>
          <div class="prose text-gray-600">
            <p>VILS helps you identify problematic code versions using binary search methodology.</p>
            <ol class="list-decimal list-inside space-y-2 mt-4">
              <li>Create a project and connect your Git repository</li>
              <li>Define good and bad commit points</li>
              <li>Let VILS automatically find the problematic commit</li>
              <li>Review results and fix the issue</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// Simple mock data
const mockStats = ref({
  totalProjects: 5,
  activeTasks: 3,
  completedTasks: 12,
  successRate: 85
})
</script>