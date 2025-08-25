/**
 * Vue Router configuration
 */

import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import apiClient from '@/utils/api'

// Lazy-loaded components
const Login = () => import('@/views/auth/LoginView.vue')
const Register = () => import('@/views/auth/RegisterView.vue')
const Dashboard = () => import('@/views/DashboardView-simple.vue')
const Projects = () => import('@/views/ProjectsView.vue')
const ProjectDetail = () => import('@/views/ProjectDetailView.vue')
const Tasks = () => import('@/views/TasksView.vue')
const TaskDetail = () => import('@/views/TaskDetailView.vue')
const CreateTask = () => import('@/views/CreateTaskView.vue')
const Profile = () => import('@/views/ProfileView.vue')
const NotFound = () => import('@/views/NotFoundView.vue')

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'login',
    component: Login,
    meta: {
      requiresAuth: false,
      title: 'Login - VILS'
    }
  },
  {
    path: '/register',
    name: 'register', 
    component: Register,
    meta: {
      requiresAuth: false,
      title: 'Register - VILS'
    }
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: Dashboard,
    meta: {
      requiresAuth: true,
      title: 'Dashboard - VILS'
    }
  },
  {
    path: '/projects',
    name: 'projects',
    component: Projects,
    meta: {
      requiresAuth: true,
      title: 'Projects - VILS'
    }
  },
  {
    path: '/projects/:id',
    name: 'project-detail',
    component: ProjectDetail,
    meta: {
      requiresAuth: true,
      title: 'Project Details - VILS'
    },
    props: true
  },
  {
    path: '/tasks',
    name: 'tasks',
    component: Tasks,
    meta: {
      requiresAuth: true,
      title: 'Tasks - VILS'
    }
  },
  {
    path: '/tasks/new',
    name: 'create-task',
    component: CreateTask,
    meta: {
      requiresAuth: true,
      title: 'Create Task - VILS'
    }
  },
  {
    path: '/tasks/:id',
    name: 'task-detail',
    component: TaskDetail,
    meta: {
      requiresAuth: true,
      title: 'Task Details - VILS'
    },
    props: true
  },
  {
    path: '/profile',
    name: 'profile',
    component: Profile,
    meta: {
      requiresAuth: true,
      title: 'Profile - VILS'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: NotFound,
    meta: {
      title: 'Page Not Found - VILS'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// Navigation guards
router.beforeEach((to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const isAuthenticated = apiClient.isAuthenticated()
  const useMockApi = import.meta.env.VITE_USE_MOCK_API === 'true'

  // Set document title
  if (to.meta.title) {
    document.title = to.meta.title as string
  }

  // In demo mode, bypass authentication for protected routes
  if (useMockApi && requiresAuth && !isAuthenticated) {
    // Skip authentication check in demo mode - allow access to all routes
    next()
    return
  }

  if (requiresAuth && !isAuthenticated) {
    // Redirect to login if authentication required but user not authenticated
    next({
      name: 'login',
      query: { redirect: to.fullPath }
    })
  } else if (!requiresAuth && isAuthenticated && (to.name === 'login' || to.name === 'register')) {
    // Redirect authenticated users away from auth pages
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

// Handle auth logout event
window.addEventListener('auth:logout', () => {
  router.push({ name: 'login' })
})

export default router

// Route helper functions
export const getRouteTitle = (routeName: string): string => {
  const route = routes.find(r => r.name === routeName)
  return route?.meta?.title as string || 'VILS'
}

export const isCurrentRoute = (routeName: string): boolean => {
  return router.currentRoute.value.name === routeName
}

// Navigation helpers
export const navigateTo = (routeName: string, params?: Record<string, any>) => {
  router.push({ name: routeName, params })
}

export const navigateBack = () => {
  router.back()
}

export const navigateToLogin = (redirectPath?: string) => {
  router.push({
    name: 'login',
    query: redirectPath ? { redirect: redirectPath } : {}
  })
}

export const navigateAfterLogin = (defaultRoute: string = 'dashboard') => {
  const redirect = router.currentRoute.value.query.redirect as string
  router.push(redirect || { name: defaultRoute })
}