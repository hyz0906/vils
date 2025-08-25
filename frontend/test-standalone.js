#!/usr/bin/env node

/**
 * Test script to run the frontend in standalone mode with mock data
 */

const { spawn } = require('child_process')
const path = require('path')

console.log('🚀 Starting VILS Frontend in Standalone Mode with Mock Data...\n')

// Set environment variables for standalone mode
process.env.VITE_USE_MOCK_API = 'true'
process.env.VITE_API_BASE_URL = ''
process.env.VITE_DEBUG = 'true'

console.log('📝 Configuration:')
console.log('  - Mock API: Enabled')
console.log('  - Backend: Not required')
console.log('  - Real-time WebSocket: Mock enabled')
console.log('  - Test data: Comprehensive mock dataset')
console.log('')

console.log('🌐 Features available in standalone mode:')
console.log('  ✅ User authentication (mock login)')
console.log('  ✅ Dashboard with statistics')
console.log('  ✅ Projects management')
console.log('  ✅ Tasks management')  
console.log('  ✅ Binary search visualization')
console.log('  ✅ Real-time updates (simulated)')
console.log('  ✅ Responsive design')
console.log('  ✅ Complete UI/UX flow')
console.log('')

console.log('👥 Test accounts available:')
console.log('  Username: john_doe   | Password: password123')
console.log('  Username: jane_smith | Password: password123')
console.log('  Username: alex_johnson | Password: password123')
console.log('')

console.log('🔗 After startup, visit: http://localhost:5173')
console.log('📱 Mobile-friendly: Test on different screen sizes')
console.log('')

// Start the development server
const vite = spawn('npm', ['run', 'dev'], {
  cwd: __dirname,
  stdio: 'inherit',
  env: { ...process.env }
})

vite.on('close', (code) => {
  console.log(`\n🔚 Development server exited with code ${code}`)
  process.exit(code)
})

vite.on('error', (error) => {
  console.error('❌ Failed to start development server:', error)
  process.exit(1)
})

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down development server...')
  vite.kill('SIGINT')
})

process.on('SIGTERM', () => {
  console.log('\n🛑 Shutting down development server...')
  vite.kill('SIGTERM')
})