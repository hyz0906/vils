<template>
  <div 
    class="inline-block relative"
    :class="[sizeClasses, roundedClass]"
  >
    <img
      v-if="user?.avatar_url"
      :src="user.avatar_url"
      :alt="user.username"
      :class="[sizeClasses, roundedClass]"
      class="object-cover"
    />
    <div
      v-else
      :class="[sizeClasses, roundedClass, backgroundClass]"
      class="flex items-center justify-center font-medium text-white"
    >
      {{ initials }}
    </div>
    
    <!-- Online status indicator -->
    <div
      v-if="showStatus && isOnline"
      class="absolute bottom-0 right-0 block rounded-full ring-2 ring-white bg-green-400"
      :class="statusSizeClass"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { User } from '@/types'

interface Props {
  user?: User | null
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  showStatus?: boolean
  isOnline?: boolean
  rounded?: 'sm' | 'md' | 'lg' | 'full'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  showStatus: false,
  isOnline: false,
  rounded: 'full'
})

// Computed properties
const initials = computed(() => {
  if (!props.user?.username) return '?'
  
  const username = props.user.username
  if (username.length === 1) return username.toUpperCase()
  
  // Take first letter and first letter after space/underscore/hyphen
  const parts = username.split(/[\s_-]/)
  if (parts.length > 1) {
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }
  
  // Take first two letters
  return username.substring(0, 2).toUpperCase()
})

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'xs': return 'h-6 w-6 text-xs'
    case 'sm': return 'h-8 w-8 text-sm'
    case 'md': return 'h-10 w-10 text-base'
    case 'lg': return 'h-12 w-12 text-lg'
    case 'xl': return 'h-16 w-16 text-xl'
    default: return 'h-10 w-10 text-base'
  }
})

const statusSizeClass = computed(() => {
  switch (props.size) {
    case 'xs': return 'h-2 w-2'
    case 'sm': return 'h-2 w-2'
    case 'md': return 'h-3 w-3'
    case 'lg': return 'h-3 w-3'
    case 'xl': return 'h-4 w-4'
    default: return 'h-3 w-3'
  }
})

const roundedClass = computed(() => {
  switch (props.rounded) {
    case 'sm': return 'rounded-sm'
    case 'md': return 'rounded-md'
    case 'lg': return 'rounded-lg'
    case 'full': return 'rounded-full'
    default: return 'rounded-full'
  }
})

const backgroundClass = computed(() => {
  // Generate a consistent color based on username
  if (!props.user?.username) return 'bg-gray-500'
  
  const username = props.user.username
  let hash = 0
  for (let i = 0; i < username.length; i++) {
    hash = username.charCodeAt(i) + ((hash << 5) - hash)
  }
  
  const colors = [
    'bg-red-500',
    'bg-orange-500', 
    'bg-amber-500',
    'bg-yellow-500',
    'bg-lime-500',
    'bg-green-500',
    'bg-emerald-500',
    'bg-teal-500',
    'bg-cyan-500',
    'bg-sky-500',
    'bg-blue-500',
    'bg-indigo-500',
    'bg-violet-500',
    'bg-purple-500',
    'bg-fuchsia-500',
    'bg-pink-500'
  ]
  
  return colors[Math.abs(hash) % colors.length]
})
</script>