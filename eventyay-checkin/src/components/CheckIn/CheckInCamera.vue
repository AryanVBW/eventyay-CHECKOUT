<script setup>
import { onBeforeMount, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import QRCamera from '@/components/Common/QRCamera.vue'
import { useLoadingStore } from '@/stores/loading'
import { useProcessCheckInStore } from '@/stores/processCheckIn'
import { useProcessCheckOutStore } from '@/stores/processCheckOut'
import { useSessionsStore } from '@/stores/sessions'
const loadingStore = useLoadingStore()
const processCheckInStore = useProcessCheckInStore()
const processCheckOutStore = useProcessCheckOutStore()
const sessionsStore = useSessionsStore()

// get scanner type from vue router params
const route = useRoute()
const scannerType = route.params.scannerType
const microlocationId = route.params.stationId

const isCheckoutMode = ref(false)

function toggleMode() {
  isCheckoutMode.value = !isCheckoutMode.value
  // Reset both stores when switching modes
  processCheckInStore.$reset()
  processCheckOutStore.$reset()
}

const currentQrType = computed(() => {
  return isCheckoutMode.value ? 'checkOut' : 'checkIn'
})

const currentStore = computed(() => {
  return isCheckoutMode.value ? processCheckOutStore : processCheckInStore
})

onBeforeMount(async () => {
  if (scannerType !== 'daily') {
    await sessionsStore.getCurrentSession(microlocationId)
  }
  processCheckInStore.$reset()
  processCheckOutStore.$reset()
  loadingStore.contentLoaded()
})
</script>

<template>
  <div
    class="grid w-full grid-cols-1 place-items-center items-center justify-center gap-6 align-middle"
  >
    <!-- Mode Toggle -->
    <div class="flex items-center gap-4 mb-4">
      <span class="text-sm font-medium text-gray-700">Mode:</span>
      <button
        @click="toggleMode"
        :class="[
          'px-4 py-2 rounded-md text-sm font-medium transition-colors',
          !isCheckoutMode 
            ? 'bg-blue-600 text-white hover:bg-blue-700' 
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
        ]"
      >
        Check-In
      </button>
      <button
        @click="toggleMode"
        :class="[
          'px-4 py-2 rounded-md text-sm font-medium transition-colors',
          isCheckoutMode 
            ? 'bg-red-600 text-white hover:bg-red-700' 
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
        ]"
      >
        Check-Out
      </button>
    </div>

    <QRCamera
      :qr-type="currentQrType"
      :scan-type="scannerType"
      :details="scannerType !== 'daily' ? sessionsStore.formattedSessionDetails : null"
    />
    <p class="text-bold mt-5 text-center text-lg">
      <span :class="currentStore.response.class">
        {{ currentStore.response.message }}
      </span>
    </p>
  </div>
</template>
