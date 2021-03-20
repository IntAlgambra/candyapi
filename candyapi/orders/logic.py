from typing import List, Optional
from functools import reduce
from datetime import datetime

from dateutil import parser

from django.db import transaction

from .models import Delievery, Order
from .utils import construct_assign_query
from couriers.models import Courier, Interval


class CompleteTimeError(Exception):
    """
    Raised if there is attempt to complete order earlier,
    than previous order was completed
    """

    def __init__(self):
        super(CompleteTimeError, self).__init__(
            "Order complete time can not be earlier than previos delievered order"
        )


@transaction.atomic
def assign(courier_id: int) -> Optional[Delievery]:
    """
    Function creates new delivery, assigns it to courier and add to this delivery
    all suitable orders. If couriers alredy has active delievery, returns it
    """
    courier = Courier.objects.get(courier_id=courier_id)
    if courier.delieveries.filter(completed=False).exists():
        active_delievery = courier.delieveries.get(completed=False)
        return active_delievery
    max_weight = Courier.WEIGHT_MAP.get(courier.courier_type)
    if courier.intervals.all().count() == 0:
        return None
    interval_condition = construct_assign_query(list(courier.intervals.all()))
    suitable_orders = Order.objects.filter(
        interval_condition,
        delievery__isnull=True,
        delievered=False,
        weight__lte=max_weight,
        region__couriers=courier
    )
    if suitable_orders.count() == 0:
        return None
    delievery = Delievery.objects.create_delievery(
        orders=suitable_orders,
        courier=courier,
    )
    return delievery


@transaction.atomic()
def complete_order(courier_id: int,
                   order_id: int,
                   complete_time: str) -> Order:
    """
    Completes order with order_id and updaes delievery last_delievery_time. If
    there is no uncompleted orders in delievery, completes delievery as well
    """
    courier = Courier.objects.get(courier_id=courier_id)
    delievery = courier.delieveries.get(completed=False)
    if parser.isoparse(complete_time) <= delievery.last_delievery_time:
        raise CompleteTimeError()
    order = delievery.orders.filter(delievered=False).get(order_id=order_id)
    order.complete(
        datetime_string=complete_time,
        start_time=delievery.last_delievery_time
    )
    delievery.last_delievery_time = order.delievery_time
    if not delievery.orders.filter(delievered=False).exists():
        delievery.completed = True
    delievery.save()
    return order
