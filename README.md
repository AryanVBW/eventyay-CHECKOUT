# Checkout Functionality Implementation

This document describes the implementation of checkout functionality for the eventyay-tickets backend and Check-In app.

## Overview

The checkout functionality allows event organizers to:
1. Check out individual attendees via QR code scanning
2. Perform bulk checkout of all checked-in attendees for an event
3. Toggle between check-in and check-out modes in the UI
4. Track checkout statistics alongside check-in statistics

## Backend Implementation (eventyay-tickets)

### 1. Checkout Service (`pretix/base/services/checkout.py`)

**New file created** with reusable checkout functions:

- `perform_bulk_checkout()`: Checks out all attendees currently checked in to an event
- `perform_single_checkout()`: Checks out a single attendee position
- `CheckOutError`: Custom exception class for checkout-specific errors

**Key Features:**
- Transactional operations for data integrity
- Comprehensive error handling
- Support for forced checkouts
- Audit logging for all checkout operations
- Signal emission for external integrations

### 2. API Views (`pretix/api/views/checkin.py`)

**Added new API endpoints:**

#### Bulk Checkout API
- **Endpoint:** `POST /api/v1/organizers/{organizer}/events/{event}/checkout/bulk/`
- **Purpose:** Check out all attendees in an event
- **Parameters:**
  - `checkin_lists` (optional): List of checkin list IDs to checkout from
  - `force` (optional): Force checkout even if not checked in
  - `datetime` (optional): Custom checkout timestamp

#### Single Checkout API  
- **Endpoint:** `POST /api/v1/organizers/{organizer}/events/{event}/checkout/single/`
- **Purpose:** Check out a specific attendee
- **Parameters:**
  - `position_id`: Order position ID to checkout
  - `checkin_list_id`: Checkin list ID
  - `force` (optional): Force checkout even if not checked in
  - `datetime` (optional): Custom checkout timestamp

### 3. URL Configuration (`pretix/api/urls.py`)

Added new URL patterns for checkout endpoints:
- `/checkout/bulk/` for bulk operations
- `/checkout/single/` for individual operations

### 4. Testing (`tests/api/test_checkout.py`)

**Comprehensive test suite including:**
- Authentication requirements
- Empty event scenarios
- Bulk checkout with checked-in attendees
- Single attendee checkout
- Error handling for non-checked-in attendees
- Forced checkout functionality

## Frontend Implementation (eventyay-checkin)

### 1. Checkout Store (`src/stores/processCheckOut.js`)

**New store** for managing checkout operations:
- `checkOutAttendeeScannerFromRoom()`: Handle QR code checkout scanning
- `bulkCheckOutEvent()`: Perform bulk checkout via API
- Error handling and user feedback
- Integration with loading states

### 2. Attendees Store Updates (`src/stores/attendees.js`)

**Extended existing store** with checkout functions:
- `checkOutAttendee()`: Individual attendee checkout
- `bulkCheckOutEvent()`: Bulk event checkout
- Pretix API integration

### 3. Checkout Camera Component (`src/components/CheckIn/CheckOutCamera.vue`)

**New component** for checkout scanning:
- QR code scanning for checkout operations
- Session support for non-daily scanners
- Real-time feedback messages
- Consistent UI with check-in component

### 4. Enhanced Check-In Components

#### Check-In Camera (`src/components/CheckIn/CheckInCamera.vue`)
**Enhanced with:**
- Mode toggle between check-in and check-out
- Dynamic QR type switching
- Dual store management
- Visual mode indicators

#### Check-In Stats (`src/components/CheckIn/CheckInStats.vue`)
**Enhanced with:**
- Checkout mode toggle switch
- Bulk checkout button
- Checkout status messages
- Real-time stats refresh

#### QR Camera (`src/components/Common/QRCamera.vue`)
**Enhanced with:**
- Support for `checkOut` QR type
- Integration with checkout store
- Unified scanning interface

## Usage Instructions

### For Event Staff (Frontend)

1. **Individual Checkout:**
   - Navigate to the check-in interface
   - Toggle to "Check-Out" mode using the mode buttons
   - Scan attendee's QR code
   - Receive immediate feedback

2. **Bulk Checkout:**
   - Go to the Stats page
   - Enable "Checkout Mode" using the toggle
   - Click "Bulk Checkout All" button
   - Confirm the operation

### For Developers (API)

1. **Bulk Checkout:**
```bash
curl -X POST \
  'https://api.eventyay.com/api/v1/organizers/myorg/events/myevent/checkout/bulk/' \
  -H 'Authorization: JWT your-token' \
  -H 'Content-Type: application/json' \
  -d '{
    "checkin_lists": [1, 2],
    "force": false
  }'
```

2. **Single Checkout:**
```bash
curl -X POST \
  'https://api.eventyay.com/api/v1/organizers/myorg/events/myevent/checkout/single/' \
  -H 'Authorization: JWT your-token' \
  -H 'Content-Type: application/json' \
  -d '{
    "position_id": 123,
    "checkin_list_id": 1,
    "force": false
  }'
```

## Error Handling

### Backend Errors
- `not_checked_in`: Attendee is not currently checked in
- `invalid_position`: Position or checkin list not found
- `permission_denied`: Insufficient permissions
- `validation_error`: Invalid request data

### Frontend Errors
- QR code validation
- Network connectivity issues
- API response handling
- User feedback messages

## Security Considerations

1. **Authentication:** All API endpoints require proper authentication
2. **Authorization:** Permission checks for checkin/checkout operations
3. **Validation:** Input validation for all parameters
4. **Audit Trail:** All operations are logged for accountability

## Performance Optimizations

1. **Bulk Operations:** Efficient database queries for bulk checkout
2. **Transactions:** Atomic operations to prevent data inconsistency
3. **Caching:** Event and checkin list caching where appropriate
4. **Error Handling:** Graceful degradation on failures

## Future Enhancements

1. **Partial Checkout:** Support for checking out specific checkin lists
2. **Scheduled Checkout:** Automatic checkout at specified times
3. **Export Functionality:** Export checkout data and statistics
4. **Mobile Optimization:** Enhanced mobile interface for staff
5. **Offline Support:** Offline checkout capability with sync

## Development Practices Followed

1. **Minimal Changes:** Leveraged existing patterns and structures
2. **Reusable Code:** Created separate service files for maintainability
3. **Error Handling:** Comprehensive error handling for edge cases
4. **Testing:** Full test coverage for new functionality
5. **Documentation:** Clear documentation and code comments

## Integration Points

The checkout functionality integrates with:
- Existing checkin system
- Order management
- Event statistics
- Audit logging
- Permission system
- Device authentication

This implementation provides a robust, scalable checkout system that complements the existing check-in functionality while maintaining code quality and system reliability. 