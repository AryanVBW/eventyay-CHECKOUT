import { useApiStore } from '@/stores/api'
import { useSessionsStore } from '@/stores/sessions'
import { useStationsStore } from '@/stores/stations'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAttendeesStore = defineStore('attendees', () => {
  const apiStore = useApiStore()
  const stations = useStationsStore()
  const sessions = useSessionsStore()
  const attendees = ref([])

  function $reset() {
    attendees.value = []
  }

  async function fetchAttendees(eventId, fieldType, value) {
    let route = `events/${eventId}/attendees/search?`
    if (fieldType === 'name') {
      route += `name=${value}`
    }

    if (fieldType === 'email') {
      route += `email=${value}`
    }
    try {
      const res = await apiStore.get(
        true,
        `events/${eventId}/attendees/search?sort=firstname&${route}`
      )
      attendees.value = res.attendees.map((attendee) => ({
        id: attendee.id,
        name: attendee.firstname + ' ' + attendee.lastname,
        email: attendee.email,
        ticketId: attendee.ticket_id,
        checkedIn: ref(attendee.is_registered),
        info: {
          attendee
        }
      }))
    } catch (error) {
      return Promise.reject(error)
    }
  }

  async function registerAttendee(attendeeId, stationId) {
    const payload = {
      data: {
        relationships: {
          station: {
            data: {
              type: 'station',
              id: String(stationId)
            }
          },
          ticket_holder: {
            data: {
              type: 'attendee',
              id: String(attendeeId)
            }
          }
        },
        type: 'user_check_in'
      }
    }
    try {
      const res = await apiStore.post(true, 'user-check-in', payload, false)
      return res.data.attributes.success
    } catch (error) {
      return Promise.reject(error)
    }
  }

  async function checkInAttendee(attendeeId, stationId, scannerType) {
    try {
      const actualStationId = await stations.getActualStationId(stationId, scannerType)
      if (!actualStationId) {
        return Promise.reject('No station found.')
      }
      let payload = {
        data: {
          relationships: {
            station: {
              data: {
                type: 'station',
                id: String(actualStationId)
              }
            },
            ticket_holder: {
              data: {
                type: 'attendee',
                id: String(attendeeId)
              }
            }
          },
          type: 'user_check_in'
        }
      }

      if (scannerType !== 'daily') {
        const session = await sessions.getCurrentSession(stationId)
        const sessionId = session ? String(session.id) : null
        payload.data.relationships.session = {
          data: {
            type: 'session',
            id: String(sessionId)
          }
        }
      }
      return await apiStore.post(true, 'user-check-in', payload)
    } catch (error) {
      if (error.response?.status === 422) {
        return Promise.reject('already done')
      }
      return Promise.reject('Error processing.')
    }
  }

  async function getAttendeeName(attendeeId) {
    try {
      const attendee = await apiStore.get(true, `attendees/${attendeeId}`)
      return attendee.data.attributes['firstname'] + ' ' + attendee.data.attributes['lastname']
    } catch (error) {
      return Promise.reject(error)
    }
  }

  async function checkOutAttendee(ticketSecret, checkinListId, force = false) {
    try {
      // For checkout, we'll use the pretix API directly
      // This would need to be adapted based on the actual integration
      const payload = {
        secret: ticketSecret,
        type: 'exit',
        force: force,
        lists: [checkinListId]
      }
      
      const response = await apiStore.post(true, 'checkin/redeem', payload)
      return response
    } catch (error) {
      if (error.response?.status === 400) {
        const errorData = error.response.data
        if (errorData.reason === 'not_checked_in') {
          return Promise.reject('not checked in')
        }
      }
      return Promise.reject('Error processing checkout.')
    }
  }

  async function bulkCheckOutEvent(eventId, checkinListIds = [], force = false) {
    try {
      const payload = {
        checkin_lists: checkinListIds,
        force: force
      }
      
      const response = await apiStore.post(true, `events/${eventId}/checkout/bulk`, payload)
      return response
    } catch (error) {
      return Promise.reject(error)
    }
  }

  return {
    attendees,
    $reset,
    fetchAttendees,
    registerAttendee,
    checkInAttendee,
    checkOutAttendee,
    bulkCheckOutEvent,
    getAttendeeName
  }
})
