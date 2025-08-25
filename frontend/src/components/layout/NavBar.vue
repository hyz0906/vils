<template>
  <nav class="bg-white shadow-sm border-b border-gray-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <!-- Logo and Navigation -->
        <div class="flex">
          <!-- Logo -->
          <div class="flex-shrink-0 flex items-center">
            <router-link to="/dashboard" class="flex items-center">
              <div class="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center mr-3">
                <span class="text-white font-bold text-sm">V</span>
              </div>
              <span class="text-xl font-bold text-gray-900">VILS</span>
            </router-link>
          </div>
          
          <!-- Primary Navigation -->
          <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
            <router-link
              to="/dashboard"
              class="nav-link"
              :class="{ 'nav-link-active': $route.name === 'dashboard' }"
            >
              <DashboardIcon class="w-4 h-4 mr-2" />
              Dashboard
            </router-link>
            
            <router-link
              to="/projects"
              class="nav-link"
              :class="{ 'nav-link-active': $route.name?.toString().startsWith('project') }"
            >
              <FolderIcon class="w-4 h-4 mr-2" />
              Projects
            </router-link>
            
            <router-link
              to="/tasks"
              class="nav-link"
              :class="{ 'nav-link-active': $route.name?.toString().startsWith('task') }"
            >
              <TaskIcon class="w-4 h-4 mr-2" />
              Tasks
            </router-link>
          </div>
        </div>

        <!-- Right side -->
        <div class="hidden sm:ml-6 sm:flex sm:items-center sm:space-x-4">
          <!-- Notifications -->
          <NotificationDropdown />
          
          <!-- Connection Status -->
          <ConnectionStatus />
          
          <!-- User Menu -->
          <div class="relative" ref="userMenuRef">
            <button
              @click="toggleUserMenu"
              class="flex text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              :class="{ 'ring-2 ring-primary-500': isUserMenuOpen }"
            >
              <span class="sr-only">Open user menu</span>
              <UserAvatar 
                :user="authStore.user" 
                class="h-8 w-8"
              />
            </button>
            
            <!-- User dropdown menu -->
            <transition
              enter-active-class="transition ease-out duration-100"
              enter-from-class="transform opacity-0 scale-95"
              enter-to-class="transform opacity-100 scale-100"
              leave-active-class="transition ease-in duration-75"
              leave-from-class="transform opacity-100 scale-100"
              leave-to-class="transform opacity-0 scale-95"
            >
              <div
                v-if="isUserMenuOpen"
                class="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-50"
              >
                <div class="py-1">
                  <div class="px-4 py-2 text-sm text-gray-700 border-b">
                    <div class="font-medium">{{ authStore.user?.username }}</div>
                    <div class="text-gray-500">{{ authStore.user?.email }}</div>
                  </div>
                  
                  <router-link
                    to="/profile"
                    class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    @click="closeUserMenu"
                  >
                    <UserIcon class="w-4 h-4 mr-2 inline" />
                    Profile
                  </router-link>
                  
                  <button
                    @click="handleLogout"
                    class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <LogOutIcon class="w-4 h-4 mr-2 inline" />
                    Sign out
                  </button>
                </div>
              </div>
            </transition>
          </div>
        </div>

        <!-- Mobile menu button -->
        <div class="sm:hidden flex items-center">
          <button
            @click="toggleMobileMenu"
            class="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500"
          >
            <span class="sr-only">Open main menu</span>
            <MenuIcon v-if="!isMobileMenuOpen" class="block h-6 w-6" />
            <XIcon v-else class="block h-6 w-6" />
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile menu -->
    <transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition ease-in duration-100"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div v-if="isMobileMenuOpen" class="sm:hidden">
        <div class="pt-2 pb-3 space-y-1">
          <router-link
            to="/dashboard"
            class="mobile-nav-link"
            :class="{ 'mobile-nav-link-active': $route.name === 'dashboard' }"
            @click="closeMobileMenu"
          >
            <DashboardIcon class="w-4 h-4 mr-3" />
            Dashboard
          </router-link>
          
          <router-link
            to="/projects"
            class="mobile-nav-link"
            :class="{ 'mobile-nav-link-active': $route.name?.toString().startsWith('project') }"
            @click="closeMobileMenu"
          >
            <FolderIcon class="w-4 h-4 mr-3" />
            Projects
          </router-link>
          
          <router-link
            to="/tasks"
            class="mobile-nav-link"
            :class="{ 'mobile-nav-link-active': $route.name?.toString().startsWith('task') }"
            @click="closeMobileMenu"
          >
            <TaskIcon class="w-4 h-4 mr-3" />
            Tasks
          </router-link>
        </div>
        
        <div class="pt-4 pb-3 border-t border-gray-200">
          <div class="flex items-center px-4">
            <UserAvatar :user="authStore.user" class="h-10 w-10" />
            <div class="ml-3">
              <div class="text-base font-medium text-gray-800">{{ authStore.user?.username }}</div>
              <div class="text-sm font-medium text-gray-500">{{ authStore.user?.email }}</div>
            </div>
          </div>
          <div class="mt-3 space-y-1">
            <router-link
              to="/profile"
              class="mobile-nav-link"
              @click="closeMobileMenu"
            >
              <UserIcon class="w-4 h-4 mr-3" />
              Profile
            </router-link>
            <button
              @click="handleLogout"
              class="mobile-nav-link text-left w-full"
            >
              <LogOutIcon class="w-4 h-4 mr-3" />
              Sign out
            </button>
          </div>
        </div>
      </div>
    </transition>
  </nav>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Menu as MenuIcon,
  X as XIcon,
  LayoutDashboard as DashboardIcon,
  Folder as FolderIcon,
  CheckSquare as TaskIcon,
  User as UserIcon,
  LogOut as LogOutIcon,
} from 'lucide-vue-next'

import UserAvatar from '@/components/common/UserAvatar.vue'
import NotificationDropdown from '@/components/common/NotificationDropdown.vue'
import ConnectionStatus from '@/components/common/ConnectionStatus.vue'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'

const router = useRouter()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

// Reactive state
const isMobileMenuOpen = ref(false)
const isUserMenuOpen = ref(false)
const userMenuRef = ref<HTMLElement>()

// Methods
const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

const closeMobileMenu = () => {
  isMobileMenuOpen.value = false
}

const toggleUserMenu = () => {
  isUserMenuOpen.value = !isUserMenuOpen.value
}

const closeUserMenu = () => {
  isUserMenuOpen.value = false
}

const handleLogout = async () => {
  try {
    await authStore.logout()
    router.push('/login')
    notificationStore.addNotification({
      type: 'success',
      title: 'Logged Out',
      message: 'You have been successfully logged out.',
    })
  } catch (error) {
    notificationStore.addNotification({
      type: 'error',
      title: 'Logout Failed',
      message: 'Failed to log out. Please try again.',
    })
  }
  closeUserMenu()
}

// Click outside handler for user menu
const handleClickOutside = (event: Event) => {
  if (userMenuRef.value && !userMenuRef.value.contains(event.target as Node)) {
    closeUserMenu()
  }
}

// Lifecycle
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.nav-link {
  @apply inline-flex items-center px-1 pt-1 pb-1 border-b-2 border-transparent text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300 transition-colors duration-200;
}

.nav-link-active {
  @apply border-primary-500 text-primary-600;
}

.mobile-nav-link {
  @apply block pl-3 pr-4 py-2 border-l-4 border-transparent text-base font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-50 hover:border-gray-300 transition-colors duration-200 flex items-center;
}

.mobile-nav-link-active {
  @apply border-primary-500 text-primary-700 bg-primary-50;
}
</style>