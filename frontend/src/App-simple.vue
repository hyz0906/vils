<template>
  <div id="app" class="min-h-screen bg-gray-50 p-8">
    <h1 class="text-3xl font-bold text-gray-900">VILS App Test</h1>
    <p class="mt-4 text-gray-600">This is a simple test to verify Vue is working.</p>
    <p class="mt-2">Count: {{ count }}</p>
    <button 
      @click="increment" 
      class="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
    >
      Increment ({{ count }})
    </button>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const count = ref(0)

const increment = () => {
  count.value++
  console.log('Button clicked, count:', count.value)
}

console.log('App component loaded')
</script>