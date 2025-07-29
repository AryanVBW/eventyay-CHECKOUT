import { useAttendeesStore } from '@/stores/attendees'
import { useCameraStore } from '@/stores/camera'
import { useLoadingStore } from '@/stores/loading'
import extractVcardID from '@/utils/extractVcardID'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export const useProcessCheckOutStore = defineStore('processCheckOut', () => {
  const loadingStore = useLoadingStore()
  const cameraStore = useCameraStore()
  const attendeesStore = useAttendeesStore()

  const message = ref('')
  const showSuccess = ref(false)
  const showError = ref(false)

  function $reset() {
    message.value = ''
    showSuccess.value = false
    showError.value = false
  }

  const response = computed(() => {
    let classType = ''
    if (showSuccess.value) {
      classType = 'text-success'
    }
    if (showError.value) {
      classType = 'text-danger'
    }
    return {
      message: message.value,
      class: classType
    }
  })

  function showErrorMsg() {
    showSuccess.value = false
    showError.value = true
  }

  function showSuccessMsg() {
    showSuccess.value = true
    showError.value = false
  }

  async function checkOutAttendeeScannerFromRoom(microlocationId, scannerType) {
    const qrCodeValue = cameraStore.qrCodeValue
    if (!qrCodeValue) {
      message.value = 'Invalid QR Code'
      showErrorMsg()
      return
    }

    loadingStore.contentLoading()

    try {
      // For now, use a default checkin list ID - this should be configurable
      const defaultCheckinListId = 1
      
      const checkedOut = await attendeesStore.checkOutAttendee(
        qrCodeValue,
        defaultCheckinListId,
        false
      )
      
      if (checkedOut) {
        message.value = 'Checkout successful!'
        showSuccessMsg()
      } else {
        message.value = 'Unknown error'
        showErrorMsg()
      }
      loadingStore.contentLoaded()
    } catch (error) {
      if (error === 'not checked in') {
        message.value = 'Attendee is not currently checked in.'
      } else {
        message.value = error
      }
      loadingStore.contentLoaded()
      showErrorMsg()
    }
  }

  async function bulkCheckOutEvent(eventId, checkinListIds = [], force = false) {
    loadingStore.contentLoading()

    try {
      const result = await attendeesStore.bulkCheckOutEvent(eventId, checkinListIds, force)
      if (result && result.status === 'success') {
        message.value = result.message
        showSuccessMsg()
        return result
      } else {
        message.value = 'Unknown error during bulk checkout'
        showErrorMsg()
        return null
      }
    } catch (error) {
      message.value = error.message || 'Error during bulk checkout'
      showErrorMsg()
      return null
    } finally {
      loadingStore.contentLoaded()
    }
  }

  return {
    response,
    $reset,
    checkOutAttendeeScannerFromRoom,
    bulkCheckOutEvent
  }
}) 