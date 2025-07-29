<script setup>
import { onBeforeMount, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useLoadingStore } from '@/stores/loading'
import { useSessionsStore } from '@/stores/sessions'
import { useStatsStore } from '@/stores/stats'
import { useProcessCheckOutStore } from '@/stores/processCheckOut'
import RefreshButton from '@/components/Utilities/RefreshButton.vue'

const loadingStore = useLoadingStore()
const statsStore = useStatsStore()
const sessionsStore = useSessionsStore()
const processCheckOutStore = useProcessCheckOutStore()
const route = useRoute()
const eventId = route.params.eventId
const scannerType = route.params.scannerType
const microlocationId = route.params.stationId

const sessionStats = ref([
  { name: 'Check-In', stat: '0' },
  { name: 'Checkout', stat: '0' }
])

const trackStats = ref([
  { name: 'Check-In', stat: '0' },
  { name: 'Checkout', stat: '0' }
])

const trackName = ref('')
const isCheckoutMode = ref(false)
const isProcessingBulkCheckout = ref(false)

async function toggleCheckoutMode() {
  isCheckoutMode.value = !isCheckoutMode.value
}

async function performBulkCheckout() {
  if (isProcessingBulkCheckout.value) return
  
  isProcessingBulkCheckout.value = true
  try {
    const result = await processCheckOutStore.bulkCheckOutEvent(eventId)
    if (result) {
      // Refresh stats after bulk checkout
      await refreshStats()
    }
  } catch (error) {
    console.error('Bulk checkout failed:', error)
  } finally {
    isProcessingBulkCheckout.value = false
  }
}

async function refreshStats() {
  if (scannerType !== 'daily') {
    const session = await sessionsStore.getCurrentSession(microlocationId)
    if (session) {
      const stats = await statsStore.getStats(eventId, session.id)
      trackName.value = stats.session_stats[0].track_name
      sessionStats.value[0].stat = stats.total_session_checked_in
      sessionStats.value[1].stat = stats.total_session_checked_out
      trackStats.value[0].stat = stats.total_track_checked_in
      trackStats.value[1].stat = stats.total_track_checked_out
    }
  }
}

onBeforeMount(async () => {
  // check for location then pass to get curent sessions
  await sessionsStore.getCurrentSession(microlocationId).then(async (res) => {
    if (res === undefined) {
      trackName.value = 'No Track'
      loadingStore.contentLoaded()
      return
    }

    await statsStore.getStats(eventId, res.id).then((r) => {
      trackName.value = r.session_stats[0].track_name
      sessionStats.value[0].stat = r.total_session_checked_in
      sessionStats.value[1].stat = r.total_session_checked_out
      trackStats.value[0].stat = r.total_track_checked_in
      trackStats.value[1].stat = r.total_track_checked_out
      loadingStore.contentLoaded()
    })
  })
})
</script>

<template>
  <div class="grow">
    <div class="my-5 flex items-center justify-between">
      <h2>Stats</h2>
      <div class="flex items-center gap-4">
        <!-- Checkout Mode Toggle -->
        <div class="flex items-center gap-2">
          <label for="checkout-toggle" class="text-sm font-medium text-gray-700">
            Checkout Mode
          </label>
          <button
            id="checkout-toggle"
            type="button"
            @click="toggleCheckoutMode"
            :class="[
              'relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2',
              isCheckoutMode ? 'bg-indigo-600' : 'bg-gray-200'
            ]"
          >
            <span
              :class="[
                'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                isCheckoutMode ? 'translate-x-6' : 'translate-x-1'
              ]"
            />
          </button>
        </div>
        <!-- Bulk Checkout Button -->
        <button
          v-if="isCheckoutMode"
          @click="performBulkCheckout"
          :disabled="isProcessingBulkCheckout"
          class="rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600 disabled:opacity-50"
        >
          {{ isProcessingBulkCheckout ? 'Processing...' : 'Bulk Checkout All' }}
        </button>
        <RefreshButton />
      </div>
    </div>

    <!-- Checkout Status Messages -->
    <div v-if="processCheckOutStore.response.message" class="mb-4">
      <div 
        :class="[
          'rounded-md p-4',
          processCheckOutStore.response.class === 'text-success' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'
        ]"
      >
        <p class="text-sm font-medium">
          {{ processCheckOutStore.response.message }}
        </p>
      </div>
    </div>

    <div v-if="scannerType !== 'daily'" class="space-y-5">
      <div>
        <h3 class="text-base font-semibold leading-6 text-body">
          Current Session: {{ sessionsStore.currentSessionName }}
        </h3>
        <dl class="mt-5 grid grid-cols-2 gap-5">
          <div
            v-for="item in sessionStats"
            :key="item.name"
            class="overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:p-6"
          >
            <dt class="truncate text-base font-medium">{{ item.name }}</dt>
            <dd class="mt-1 text-3xl font-semibold tracking-tight text-body">
              {{ item.stat }}
            </dd>
          </div>
        </dl>
      </div>
      <div>
        <h3 class="text-base font-semibold leading-6 text-body">Current Track: {{ trackName }}</h3>
        <dl class="mt-5 grid grid-cols-2 gap-5">
          <div
            v-for="item in trackStats"
            :key="item.name"
            class="overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:p-6"
          >
            <dt class="truncate text-base font-medium">{{ item.name }}</dt>
            <dd class="mt-1 text-3xl font-semibold tracking-tight text-body">
              {{ item.stat }}
            </dd>
          </div>
        </dl>
      </div>
    </div>
    <div v-else>Work in progress</div>
  </div>
</template>
