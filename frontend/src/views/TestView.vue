<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold text-gray-900">Test View</h1>
    <p class="mt-4 text-gray-600">This is a simple test view to check if Vue is working.</p>
    <p class="mt-2 text-sm text-gray-500">Count: {{ count }}</p>
    <button 
      @click="count++" 
      class="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
    >
      Increment
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const count = ref(0)
</script>