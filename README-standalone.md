# VILS Frontend - Standalone Demo Mode

This guide shows how to run the VILS frontend in standalone mode with comprehensive mock data, allowing you to test and demonstrate all features without requiring a backend server.

## 🚀 Quick Start

### Method 1: Using the Test Script (Recommended)

```bash
cd frontend
npm run test:standalone
```

### Method 2: Using Environment Variables

```bash
cd frontend
npm run demo
```

### Method 3: Manual Setup

```bash
cd frontend
VITE_USE_MOCK_API=true npm run dev
```

## 🌐 Access the Application

After starting, visit: **http://localhost:5173**

## 👥 Test Accounts

Use any of these accounts to log in:

| Username | Password | Role |
|----------|----------|------|
| `john_doe` | `password123` | Project Owner |
| `jane_smith` | `password123` | Developer |
| `alex_johnson` | `password123` | Tester |

> **Note**: In mock mode, any password with 6+ characters will work

## ✨ Available Features

### ✅ Fully Functional in Mock Mode

- **User Authentication**: Login/logout with mock validation
- **Dashboard**: Statistics, recent activity, and progress tracking
- **Projects Management**: Create, view, and manage projects
- **Tasks Management**: Create and track localization tasks
- **Binary Search Visualization**: Interactive algorithm demonstration
- **Real-time Updates**: Simulated WebSocket connections
- **Responsive Design**: Mobile-friendly interface
- **Notifications**: Toast messages and activity feed
- **Dark Mode Support**: Automatic based on system preference

### 🎯 Interactive Demo Features

#### 1. Binary Search Localization
- Create a new task from any project
- Watch the interactive visualization narrow down commit ranges
- Mark candidates as "Good", "Bad", or "Skip"
- See real-time progress and algorithm explanation

#### 2. Real-time Simulations
- Mock WebSocket connections with periodic updates
- Simulated build output streaming
- Progress notifications and status changes

#### 3. Comprehensive Mock Data
- 5 sample projects with different technologies
- Multiple task states (active, completed, failed)
- Realistic commit hashes and timestamps
- User activity timeline
- Build history and iterations

## 🛠️ Configuration Options

### Environment Variables

Create a `.env.local` file in the frontend directory:

```env
# Enable mock API
VITE_USE_MOCK_API=true

# Optional: Customize mock behavior
VITE_MOCK_DELAY_MIN=300
VITE_MOCK_DELAY_MAX=1500
VITE_DEBUG=true
```

### Switching to Real Backend

To connect to a real backend, set:

```env
VITE_USE_MOCK_API=false
VITE_API_BASE_URL=http://localhost:8000
```

## 📱 Testing Different Scenarios

### 1. Test User Workflows

1. **New User Registration**:
   - Go to registration page
   - Fill out form (validation included)
   - Auto-login after registration

2. **Project Creation**:
   - Navigate to Projects
   - Click "New Project"
   - Fill out project details
   - See it appear in the list

3. **Binary Search Task**:
   - Go to any project
   - Click "Start task"
   - Follow the interactive binary search process
   - Watch visualization update in real-time

### 2. Test Responsive Design

- **Desktop**: Full navigation and sidebar
- **Tablet**: Collapsible navigation
- **Mobile**: Bottom navigation and touch-friendly interface

### 3. Test Real-time Features

- Start an active task
- Watch build output stream in real-time
- Observe progress updates and notifications

## 🎨 UI/UX Showcase

### Design System
- **Colors**: Primary blue with semantic color palette
- **Typography**: Inter font with responsive sizing
- **Components**: Consistent button styles, forms, and cards
- **Animations**: Smooth transitions and micro-interactions
- **Accessibility**: ARIA labels, keyboard navigation, screen reader support

### Interactive Elements
- **Binary Search Visualization**: Click-to-test interface
- **Real-time Progress Bars**: Dynamic updates with smooth animations
- **Toast Notifications**: Contextual success/error messages
- **Loading States**: Skeleton screens and spinners

## 🔧 Development Features

### Mock API Simulation
- **Realistic Delays**: Configurable response times
- **Error Scenarios**: Network failures and validation errors
- **State Persistence**: Local storage for authentication
- **WebSocket Mocking**: Simulated real-time connections

### Debug Tools
When `VITE_DEBUG=true`:
- Console logging for API calls
- Mock data inspection
- Performance timing
- State change tracking

## 📊 Mock Data Overview

### Projects (5 total)
- **Frontend Application**: React TypeScript project
- **Backend API Service**: Python FastAPI service
- **Database Migration Tools**: Python utilities
- **CI/CD Pipeline**: Docker-based deployment
- **Mobile Application**: React Native cross-platform

### Tasks (5 total)
- **Active Tasks**: Currently running binary search
- **Completed Tasks**: Successfully identified problematic commits
- **Failed Tasks**: Examples of error handling

### Users (3 total)
- Different roles and permissions
- Realistic timestamps and activity

## 🚀 Production Deployment

To build for production with mock data:

```bash
npm run build
```

The built application can be deployed to any static hosting service (Netlify, Vercel, GitHub Pages) and will work completely standalone.

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Kill process on port 5173
   npx kill-port 5173
   ```

2. **TypeScript Errors**
   ```bash
   npm run type-check
   ```

3. **Mock Data Not Loading**
   - Check browser console for errors
   - Verify `VITE_USE_MOCK_API=true` in environment

### Performance Tips

- **Lazy Loading**: Routes and components load on demand
- **Optimized Assets**: Images and icons are optimized
- **Bundle Splitting**: Vendor libraries separated from app code

## 🎯 Demo Script

For presentations or demonstrations:

1. **Login** (`john_doe` / `password123`)
2. **Dashboard Overview**: Show statistics and activity
3. **Projects**: Browse existing projects and create new one
4. **Binary Search**: Start a task and demonstrate the visualization
5. **Real-time Updates**: Show WebSocket notifications
6. **Mobile Responsive**: Resize window to show adaptability

## 📈 Analytics & Monitoring

In mock mode, the application simulates:
- User interaction tracking
- Performance metrics
- Error reporting
- Usage analytics

Ready for integration with real analytics services like Google Analytics, Mixpanel, or custom solutions.

---

**Built with ❤️ using Vue 3, TypeScript, and Tailwind CSS**