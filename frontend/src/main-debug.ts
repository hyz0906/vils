console.log('main.ts loading...')

import { createApp } from 'vue'

console.log('Vue imported successfully')

// Create basic app without any complex imports
const app = createApp({
  template: `
    <div style="padding: 2rem; font-family: system-ui;">
      <h1 style="color: #333; font-size: 2rem; margin-bottom: 1rem;">VILS Debug Mode</h1>
      <p style="color: #666; margin-bottom: 1rem;">Vue is working! Count: {{ count }}</p>
      <button 
        @click="increment" 
        style="background: #3b82f6; color: white; padding: 0.5rem 1rem; border: none; border-radius: 0.375rem; cursor: pointer;"
      >
        Increment
      </button>
      <div style="margin-top: 2rem; padding: 1rem; background: #f3f4f6; border-radius: 0.5rem;">
        <h2 style="margin: 0 0 1rem 0; font-size: 1.25rem;">Debug Info:</h2>
        <ul style="margin: 0; padding-left: 1.5rem;">
          <li>Vue.js is loaded and working</li>
          <li>JavaScript execution is successful</li>
          <li>App mounted to #app element</li>
        </ul>
      </div>
    </div>
  `,
  data() {
    return {
      count: 0
    }
  },
  methods: {
    increment() {
      this.count++
      console.log('Button clicked, count:', this.count)
    }
  }
})

console.log('App created, mounting...')
app.mount('#app')
console.log('App mounted!')