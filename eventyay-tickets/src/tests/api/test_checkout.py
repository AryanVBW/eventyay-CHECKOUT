import pytest
from datetime import timedelta
from django.utils.timezone import now
from rest_framework.test import APIClient

from pretix.base.models import (
    Checkin,
    CheckinList,
    Event,
    Organizer,
    Order,
    OrderPosition,
    Item,
    User,
)


@pytest.fixture
def organizer():
    return Organizer.objects.create(name='EventOrg', slug='eventorg')


@pytest.fixture
def event(organizer):
    return Event.objects.create(
        organizer=organizer,
        name='TestEvent',
        slug='test',
        date_from=now(),
        live=True
    )


@pytest.fixture
def item(event):
    return Item.objects.create(
        event=event,
        name='Test Ticket',
        default_price=10
    )


@pytest.fixture
def checkin_list(event):
    return CheckinList.objects.create(
        event=event,
        name='Test List',
        all_products=True
    )


@pytest.fixture
def order(event, item):
    order = Order.objects.create(
        event=event,
        email='test@example.com',
        status=Order.STATUS_PAID,
        total=10,
        datetime=now()
    )
    OrderPosition.objects.create(
        order=order,
        item=item,
        price=10
    )
    return order


@pytest.fixture
def user():
    return User.objects.create_user(
        email='test@example.com',
        password='testpass'
    )


@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_bulk_checkout_api_authentication_required():
    """Test that bulk checkout requires authentication"""
    client = APIClient()
    
    response = client.post('/api/v1/organizers/eventorg/events/test/checkout/bulk/', {})
    assert response.status_code == 401


@pytest.mark.django_db
def test_bulk_checkout_api_empty_event(api_client, event, checkin_list):
    """Test bulk checkout on event with no checked-in attendees"""
    url = f'/api/v1/organizers/{event.organizer.slug}/events/{event.slug}/checkout/bulk/'
    
    response = api_client.post(url, {})
    assert response.status_code == 200
    
    data = response.json()
    assert data['status'] == 'success'
    assert data['results']['success_count'] == 0
    assert data['results']['error_count'] == 0


@pytest.mark.django_db  
def test_bulk_checkout_api_with_checked_in_attendees(api_client, event, checkin_list, order):
    """Test bulk checkout with checked-in attendees"""
    position = order.positions.first()
    
    # First check in the attendee
    Checkin.objects.create(
        position=position,
        list=checkin_list,
        type=Checkin.TYPE_ENTRY
    )
    
    url = f'/api/v1/organizers/{event.organizer.slug}/events/{event.slug}/checkout/bulk/'
    
    response = api_client.post(url, {})
    assert response.status_code == 200
    
    data = response.json()
    assert data['status'] == 'success' 
    assert data['results']['success_count'] == 1
    assert data['results']['error_count'] == 0
    
    # Verify checkout was created
    checkout = Checkin.objects.filter(
        position=position,
        list=checkin_list,
        type=Checkin.TYPE_EXIT
    ).first()
    assert checkout is not None


@pytest.mark.django_db
def test_single_checkout_api(api_client, event, checkin_list, order):
    """Test single attendee checkout"""
    position = order.positions.first()
    
    # First check in the attendee
    Checkin.objects.create(
        position=position,
        list=checkin_list,
        type=Checkin.TYPE_ENTRY
    )
    
    url = f'/api/v1/organizers/{event.organizer.slug}/events/{event.slug}/checkout/single/'
    payload = {
        'position_id': position.id,
        'checkin_list_id': checkin_list.id
    }
    
    response = api_client.post(url, payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data['status'] == 'success'
    assert data['position_id'] == position.id
    
    # Verify checkout was created
    checkout = Checkin.objects.filter(
        position=position,
        list=checkin_list,
        type=Checkin.TYPE_EXIT
    ).first()
    assert checkout is not None


@pytest.mark.django_db
def test_single_checkout_api_not_checked_in(api_client, event, checkin_list, order):
    """Test checkout of attendee who is not checked in"""
    position = order.positions.first()
    
    url = f'/api/v1/organizers/{event.organizer.slug}/events/{event.slug}/checkout/single/'
    payload = {
        'position_id': position.id,
        'checkin_list_id': checkin_list.id
    }
    
    response = api_client.post(url, payload)
    assert response.status_code == 400
    
    data = response.json()
    assert 'error' in data
    assert data['code'] == 'not_checked_in'


@pytest.mark.django_db
def test_checkout_with_force_option(api_client, event, checkin_list, order):
    """Test forced checkout of attendee who is not checked in"""
    position = order.positions.first()
    
    url = f'/api/v1/organizers/{event.organizer.slug}/events/{event.slug}/checkout/single/'
    payload = {
        'position_id': position.id,
        'checkin_list_id': checkin_list.id,
        'force': True
    }
    
    response = api_client.post(url, payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data['status'] == 'success'
    
    # Verify forced checkout was created
    checkout = Checkin.objects.filter(
        position=position,
        list=checkin_list,
        type=Checkin.TYPE_EXIT,
        forced=True
    ).first()
    assert checkout is not None 