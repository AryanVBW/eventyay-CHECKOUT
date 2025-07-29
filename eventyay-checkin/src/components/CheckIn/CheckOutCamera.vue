<script setup>
import { onBeforeMount } from 'vue'
import { useRoute } from 'vue-router'
import QRCamera from '@/components/Common/QRCamera.vue'
import { useLoadingStore } from '@/stores/loading'
import { useProcessCheckOutStore } from '@/stores/processCheckOut'
import { useSessionsStore } from '@/stores/sessions'

const loadingStore = useLoadingStore()
const processCheckOutStore = useProcessCheckOutStore()
const sessionsStore = useSessionsStore()

// get scanner type from vue router params
const route = useRoute()
const scannerType = route.params.scannerType
const microlocationId = route.params.stationId

onBeforeMount(async () => {
  if (scannerType !== 'daily') {
    await sessionsStore.getCurrentSession(microlocationId)
  }
  processCheckOutStore.$reset()
  loadingStore.contentLoaded()
})
</script>

<template>
  <div
    class="grid w-full grid-cols-1 place-items-center items-center justify-center gap-6 align-middle"
  >
    <QRCamera
      :qr-type="'checkOut'"
      :scan-type="scannerType"
      :details="scannerType !== 'daily' ? sessionsStore.formattedSessionDetails : null"
    />
    <p class="text-bold mt-5 text-center text-lg">
      <span :class="processCheckOutStore.response.class"
        >{{ processCheckOutStore.response.message }}
      </span>
    </p>
  </div>
</template> 