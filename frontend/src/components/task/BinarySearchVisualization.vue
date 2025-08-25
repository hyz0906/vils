<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
    <div class="mb-6">
      <h3 class="text-lg font-medium text-gray-900 mb-2">
        Binary Search Progress
      </h3>
      <p class="text-sm text-gray-600">
        Visual representation of the commit range being narrowed down through binary search
      </p>
    </div>

    <!-- Overall progress -->
    <div class="mb-6">
      <div class="flex justify-between items-center mb-2">
        <span class="text-sm font-medium text-gray-700">Overall Progress</span>
        <span class="text-sm text-gray-600">
          {{ progressPercentage }}% complete
        </span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-3">
        <div
          class="bg-primary-600 h-3 rounded-full transition-all duration-500 ease-out"
          :style="{ width: `${progressPercentage}%` }"
        ></div>
      </div>
      <div class="flex justify-between text-xs text-gray-500 mt-1">
        <span>{{ remainingCommits }} commits remaining</span>
        <span>Iteration {{ currentIteration }}</span>
      </div>
    </div>

    <!-- Commit range visualization -->
    <div class="mb-6">
      <h4 class="text-sm font-medium text-gray-700 mb-3">Commit Range</h4>
      <div class="relative">
        <!-- Timeline line -->
        <div class="absolute top-6 left-0 right-0 h-0.5 bg-gray-300"></div>
        
        <!-- Good commit marker -->
        <div class="relative flex items-start mb-4">
          <div class="flex-shrink-0">
            <div class="w-3 h-3 bg-green-500 rounded-full border-2 border-white shadow-sm"></div>
          </div>
          <div class="ml-3 min-w-0 flex-1">
            <div class="text-sm">
              <span class="font-medium text-green-700">Good Commit</span>
              <span class="text-gray-500 ml-2 font-mono text-xs">
                {{ goodCommit?.substring(0, 8) }}
              </span>
            </div>
            <div class="text-xs text-gray-500 mt-1">
              Last known working state
            </div>
          </div>
        </div>

        <!-- Current candidates visualization -->
        <div v-if="currentCandidates && currentCandidates.length > 0" class="my-6">
          <h5 class="text-sm font-medium text-gray-700 mb-3">
            Current Candidates ({{ currentCandidates.length }})
          </h5>
          <div class="grid grid-cols-5 gap-2">
            <div
              v-for="(candidate, index) in currentCandidates"
              :key="candidate"
              class="relative group"
            >
              <div
                class="w-full h-8 rounded border-2 border-dashed border-gray-300 bg-gray-50 flex items-center justify-center cursor-pointer hover:border-primary-300 hover:bg-primary-50 transition-colors duration-200"
                :class="{
                  'border-blue-400 bg-blue-50': selectedCandidate === candidate,
                  'border-yellow-400 bg-yellow-50': testingCandidate === candidate,
                }"
                @click="selectCandidate(candidate)"
              >
                <span class="text-xs font-mono text-gray-600">
                  {{ candidate.substring(0, 6) }}
                </span>
              </div>
              
              <!-- Tooltip -->
              <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-1 px-2 py-1 bg-black text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-10">
                {{ candidate }}
              </div>
            </div>
          </div>
          
          <div class="mt-2 text-xs text-gray-500">
            Click on a candidate to mark it for testing
          </div>
        </div>

        <!-- Bad commit marker -->
        <div class="relative flex items-start">
          <div class="flex-shrink-0">
            <div class="w-3 h-3 bg-red-500 rounded-full border-2 border-white shadow-sm"></div>
          </div>
          <div class="ml-3 min-w-0 flex-1">
            <div class="text-sm">
              <span class="font-medium text-red-700">Bad Commit</span>
              <span class="text-gray-500 ml-2 font-mono text-xs">
                {{ badCommit?.substring(0, 8) }}
              </span>
            </div>
            <div class="text-xs text-gray-500 mt-1">
              Known problematic state
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Search statistics -->
    <div class="grid grid-cols-3 gap-4 mb-6">
      <div class="text-center">
        <div class="text-2xl font-semibold text-gray-900">
          {{ totalCommits }}
        </div>
        <div class="text-sm text-gray-500">Total Commits</div>
      </div>
      <div class="text-center">
        <div class="text-2xl font-semibold text-primary-600">
          {{ currentIteration }}
        </div>
        <div class="text-sm text-gray-500">Current Iteration</div>
      </div>
      <div class="text-center">
        <div class="text-2xl font-semibold text-gray-900">
          {{ estimatedRemaining }}
        </div>
        <div class="text-sm text-gray-500">Est. Remaining</div>
      </div>
    </div>

    <!-- Algorithm explanation -->
    <div class="bg-gray-50 rounded-lg p-4">
      <h5 class="text-sm font-medium text-gray-700 mb-2">
        How Binary Search Works
      </h5>
      <p class="text-sm text-gray-600 leading-relaxed">
        Binary search efficiently narrows down the problematic commit by testing the middle point
        of the remaining range. Each iteration eliminates approximately half of the remaining candidates,
        making it much faster than testing every commit individually.
      </p>
      
      <div class="mt-3 space-y-2">
        <div class="flex items-center text-xs text-gray-500">
          <div class="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
          <span>Good: Test passes, move search range forward</span>
        </div>
        <div class="flex items-center text-xs text-gray-500">
          <div class="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
          <span>Bad: Test fails, move search range backward</span>
        </div>
        <div class="flex items-center text-xs text-gray-500">
          <div class="w-2 h-2 bg-yellow-500 rounded-full mr-2"></div>
          <span>Skip: Unable to test, try adjacent commits</span>
        </div>
      </div>
    </div>

    <!-- Action buttons for active tasks -->
    <div v-if="status === 'active' && selectedCandidate" class="mt-6 flex justify-between items-center">
      <div class="text-sm text-gray-600">
        Testing commit: 
        <span class="font-mono font-medium">{{ selectedCandidate.substring(0, 8) }}</span>
      </div>
      <div class="flex space-x-3">
        <button
          @click="markCandidateAs('skip')"
          :disabled="isProcessing"
          class="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50"
        >
          <ClockIcon class="mr-1.5 h-4 w-4" />
          Skip
        </button>
        <button
          @click="markCandidateAs('good')"
          :disabled="isProcessing"
          class="inline-flex items-center px-3 py-1.5 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
        >
          <CheckIcon class="mr-1.5 h-4 w-4" />
          Good
        </button>
        <button
          @click="markCandidateAs('bad')"
          :disabled="isProcessing"
          class="inline-flex items-center px-3 py-1.5 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
        >
          <XIcon class="mr-1.5 h-4 w-4" />
          Bad
        </button>
      </div>
    </div>

    <!-- Completion message -->
    <div v-if="status === 'completed'" class="mt-6 bg-green-50 border border-green-200 rounded-lg p-4">
      <div class="flex">
        <CheckCircleIcon class="h-5 w-5 text-green-400" />
        <div class="ml-3">
          <h3 class="text-sm font-medium text-green-800">
            Localization Complete!
          </h3>
          <div class="mt-2 text-sm text-green-700">
            <p>
              Found problematic commit: 
              <span class="font-mono font-medium">{{ problematicCommit?.substring(0, 8) }}</span>
            </p>
            <p class="mt-1">
              Completed in {{ totalIterations }} iterations
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Error state -->
    <div v-if="status === 'failed'" class="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
      <div class="flex">
        <XCircleIcon class="h-5 w-5 text-red-400" />
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800">
            Localization Failed
          </h3>
          <div class="mt-2 text-sm text-red-700">
            <p>{{ errorMessage || 'An error occurred during the binary search process' }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  Check as CheckIcon,
  X as XIcon,
  Clock as ClockIcon,
  CheckCircle as CheckCircleIcon,
  XCircle as XCircleIcon,
} from 'lucide-vue-next'

interface Props {
  taskId: string
  status: 'active' | 'completed' | 'failed'
  goodCommit?: string
  badCommit?: string
  currentCandidates?: string[]
  currentIteration?: number
  totalIterations?: number
  problematicCommit?: string
  errorMessage?: string
}

interface Emits {
  candidateMarked: [{ candidate: string; result: 'good' | 'bad' | 'skip' }]
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// State
const selectedCandidate = ref<string>()
const testingCandidate = ref<string>()
const isProcessing = ref(false)

// Computed
const totalCommits = computed(() => {
  // Estimate total commits in range - in production this would come from git
  return Math.max(1, (props.currentCandidates?.length || 10) * 2)
})

const remainingCommits = computed(() => {
  return props.currentCandidates?.length || 0
})

const currentIteration = computed(() => {
  return props.currentIteration || 1
})

const progressPercentage = computed(() => {
  if (props.status === 'completed') return 100
  if (props.status === 'failed') return 0
  
  // Calculate progress based on binary search efficiency
  const maxIterations = Math.ceil(Math.log2(totalCommits.value))
  const currentIter = currentIteration.value
  
  return Math.min(Math.round((currentIter / maxIterations) * 100), 95)
})

const estimatedRemaining = computed(() => {
  if (props.status !== 'active') return 0
  
  // Estimate remaining iterations based on remaining candidates
  const remaining = remainingCommits.value
  if (remaining <= 1) return 0
  
  return Math.ceil(Math.log2(remaining))
})

// Methods
const selectCandidate = (candidate: string) => {
  if (props.status !== 'active') return
  selectedCandidate.value = candidate
}

const markCandidateAs = async (result: 'good' | 'bad' | 'skip') => {
  if (!selectedCandidate.value || isProcessing.value) return
  
  isProcessing.value = true
  testingCandidate.value = selectedCandidate.value
  
  try {
    // Simulate processing time
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    emit('candidateMarked', {
      candidate: selectedCandidate.value,
      result
    })
    
    // Clear selection after processing
    selectedCandidate.value = undefined
    
  } finally {
    isProcessing.value = false
    testingCandidate.value = undefined
  }
}

// Watch for changes in candidates to auto-select middle candidate
watch(
  () => props.currentCandidates,
  (newCandidates) => {
    if (newCandidates && newCandidates.length > 0 && !selectedCandidate.value) {
      // Auto-select the middle candidate for binary search
      const middleIndex = Math.floor(newCandidates.length / 2)
      selectedCandidate.value = newCandidates[middleIndex]
    }
  },
  { immediate: true }
)
</script>