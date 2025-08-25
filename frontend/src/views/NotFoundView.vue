<template>
  <div class="min-h-full flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full text-center">
      <div class="mb-8">
        <div class="mx-auto h-24 w-24 bg-gray-100 rounded-full flex items-center justify-center">
          <FileQuestionIcon class="h-12 w-12 text-gray-400" />
        </div>
      </div>
      
      <h1 class="text-4xl font-bold text-gray-900 mb-2">404</h1>
      <h2 class="text-xl font-semibold text-gray-600 mb-4">Page Not Found</h2>
      <p class="text-gray-500 mb-8">
        The page you're looking for doesn't exist or has been moved.
      </p>
      
      <div class="flex flex-col sm:flex-row gap-4 justify-center">
        <router-link
          to="/dashboard"
          class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <HomeIcon class="mr-2 h-4 w-4" />
          Go Home
        </router-link>
        
        <button
          @click="$router.back()"
          class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <ArrowLeftIcon class="mr-2 h-4 w-4" />
          Go Back
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { FileQuestion as FileQuestionIcon, Home as HomeIcon, ArrowLeft as ArrowLeftIcon } from 'lucide-vue-next'
</script>