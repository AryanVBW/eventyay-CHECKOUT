from datetime import timedelta
from functools import partial, reduce

import dateutil
import dateutil.parser
from django.core.files import File
from django.db import transaction
from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.timezone import now, override
from django.utils.translation import gettext as _
from django_scopes import scope, scopes_disabled

from pretix.base.models import (
    Checkin,
    CheckinList,
    Device,
    Order,
    OrderPosition,
)
from pretix.base.signals import checkin_created
from pretix.base.services.checkin import CheckInError, get_logic_environment, LazyRuleVars


class CheckOutError(Exception):
    def __init__(self, message, code=None):
        self.message = message
        self.code = code
        super().__init__(message)


def perform_bulk_checkout(event, checkin_lists=None, user=None, auth=None, datetime=None, force=False):
    """
    Perform bulk checkout for all attendees currently checked in to an event.
    
    :param event: The event to perform bulk checkout for
    :param checkin_lists: List of checkin lists to checkout from. If None, uses all lists.
    :param user: The user performing the checkout
    :param auth: The authentication object
    :param datetime: The datetime of the checkout, defaults to now
    :param force: Whether to force checkout even if not checked in
    :return: Dictionary with checkout results
    """
    dt = datetime or now()
    
    if checkin_lists is None:
        checkin_lists = list(event.checkin_lists.all())
    
    results = {
        'success_count': 0,
        'error_count': 0,
        'errors': [],
        'checked_out_positions': []
    }
    
    device = None
    if isinstance(auth, Device):
        device = auth
    
    with transaction.atomic():
        for checkin_list in checkin_lists:
            # Get all positions currently inside (checked in)
            inside_positions = checkin_list.positions_inside
            
            for position in inside_positions:
                try:
                    # Check if position can be checked out
                    last_checkin = position.checkins.filter(
                        list=checkin_list,
                        type=Checkin.TYPE_ENTRY
                    ).order_by('-datetime').first()
                    
                    if not last_checkin and not force:
                        results['errors'].append({
                            'position_id': position.id,
                            'error': 'Position is not checked in'
                        })
                        results['error_count'] += 1
                        continue
                    
                    # Perform checkout
                    checkout = Checkin.objects.create(
                        position=position,
                        type=Checkin.TYPE_EXIT,
                        list=checkin_list,
                        datetime=dt,
                        device=device,
                        gate=device.gate if device else None,
                        forced=force and not last_checkin,
                    )
                    
                    # Log the checkout action
                    position.order.log_action(
                        'pretix.event.checkout',
                        data={
                            'position': position.id,
                            'positionid': position.positionid,
                            'datetime': dt,
                            'type': Checkin.TYPE_EXIT,
                            'list': checkin_list.pk,
                            'bulk_operation': True,
                        },
                        user=user,
                        auth=auth,
                    )
                    
                    # Send signal
                    checkin_created.send(event, checkin=checkout)
                    
                    results['checked_out_positions'].append({
                        'position_id': position.id,
                        'order_code': position.order.code,
                        'attendee_name': position.attendee_name_cached or position.attendee_name
                    })
                    results['success_count'] += 1
                    
                except Exception as e:
                    results['errors'].append({
                        'position_id': position.id,
                        'error': str(e)
                    })
                    results['error_count'] += 1
    
    return results


def perform_single_checkout(position, checkin_list, user=None, auth=None, datetime=None, force=False):
    """
    Perform checkout for a single attendee position.
    
    :param position: The OrderPosition to checkout
    :param checkin_list: The checkin list to checkout from
    :param user: The user performing the checkout
    :param auth: The authentication object
    :param datetime: The datetime of the checkout, defaults to now
    :param force: Whether to force checkout even if not checked in
    :return: The created Checkin object
    """
    dt = datetime or now()
    
    device = None
    if isinstance(auth, Device):
        device = auth
    
    with transaction.atomic():
        # Lock the position
        position = OrderPosition.all.select_for_update().get(pk=position.pk)
        
        # Check if position is currently checked in
        last_checkin = position.checkins.filter(
            list=checkin_list,
            type=Checkin.TYPE_ENTRY
        ).order_by('-datetime').first()
        
        last_checkout = position.checkins.filter(
            list=checkin_list,
            type=Checkin.TYPE_EXIT
        ).order_by('-datetime').first()
        
        # Determine if position is currently inside
        is_inside = (
            last_checkin and 
            (not last_checkout or last_checkout.datetime < last_checkin.datetime)
        )
        
        if not is_inside and not force:
            raise CheckOutError(
                _('This attendee is not currently checked in.'),
                'not_checked_in'
            )
        
        # Create checkout record
        checkout = Checkin.objects.create(
            position=position,
            type=Checkin.TYPE_EXIT,
            list=checkin_list,
            datetime=dt,
            device=device,
            gate=device.gate if device else None,
            forced=force and not is_inside,
        )
        
        # Log the checkout action
        position.order.log_action(
            'pretix.event.checkout',
            data={
                'position': position.id,
                'positionid': position.positionid,
                'datetime': dt,
                'type': Checkin.TYPE_EXIT,
                'list': checkin_list.pk,
            },
            user=user,
            auth=auth,
        )
        
        # Send signal
        checkin_created.send(checkin_list.event, checkin=checkout)
        
        return checkout 