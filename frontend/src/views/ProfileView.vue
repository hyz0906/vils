<template>
  <div class="min-h-full">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="text-center py-12">
        <ConstructionIcon class="mx-auto h-12 w-12 text-gray-400" />
        <h2 class="mt-2 text-lg font-medium text-gray-900">Profile View</h2>
        <p class="mt-1 text-sm text-gray-500">This view is under construction</p>
        <div class="mt-6">
          <router-link
            to="/dashboard"
            class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Back to Dashboard
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Construction as ConstructionIcon } from 'lucide-vue-next'
</script>