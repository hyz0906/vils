import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './style.css'

const app = createApp(App)

// Pinia store
app.use(createPinia())

// Vue Router
app.use(router)

// Global error handler
app.config.errorHandler = (error, vm, info) => {
  console.error('Global error:', error, info)
  // Here you could send to error tracking service
}

app.mount('#app')