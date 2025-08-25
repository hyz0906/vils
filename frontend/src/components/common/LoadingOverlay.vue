<template>
  <div 
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    :class="{ 'backdrop-blur-sm': blur }"
  >
    <div class="bg-white rounded-lg shadow-xl p-6 max-w-sm mx-4">
      <div class="flex items-center space-x-4">
        <!-- Spinner -->
        <div class="flex-shrink-0">
          <div
            class="animate-spin rounded-full border-4 border-gray-300 border-t-primary-600"
            :class="spinnerSizeClass"
          ></div>
        </div>
        
        <!-- Content -->
        <div class="flex-1">
          <h3 v-if="title" class="text-lg font-medium text-gray-900 mb-1">
            {{ title }}
          </h3>
          <p v-if="message" class="text-sm text-gray-600">
            {{ message }}
          </p>
          <p v-else class="text-sm text-gray-600">
            Loading...
          </p>
        </div>
      </div>
      
      <!-- Progress bar -->
      <div v-if="showProgress && progress !== undefined" class="mt-4">
        <div class="flex justify-between text-sm text-gray-600 mb-1">
          <span>Progress</span>
          <span>{{ Math.round(progress) }}%</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-2">
          <div
            class="bg-primary-600 h-2 rounded-full transition-all duration-300 ease-out"
            :style="{ width: `${progress}%` }"
          ></div>
        </div>
      </div>
      
      <!-- Cancel button -->
      <div v-if="cancelable" class="mt-4 flex justify-end">
        <button
          @click="handleCancel"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
        >
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  title?: string
  message?: string
  progress?: number
  showProgress?: boolean
  cancelable?: boolean
  blur?: boolean
  size?: 'sm' | 'md' | 'lg'
}

interface Emits {
  cancel: []
}

const props = withDefaults(defineProps<Props>(), {
  showProgress: false,
  cancelable: false,
  blur: true,
  size: 'md'
})

const emit = defineEmits<Emits>()

// Computed
const spinnerSizeClass = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'h-6 w-6'
    case 'md':
      return 'h-8 w-8'
    case 'lg':
      return 'h-10 w-10'
    default:
      return 'h-8 w-8'
  }
})

// Methods
const handleCancel = () => {
  emit('cancel')
}
</script>