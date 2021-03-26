from typing import List, Optional
from functools import reduce
from datetime import datetime

from dateutil import parser

from django.db import transaction

from .models import Delievery, Order
from .utils import construct_assign_query, fill_weight
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


def select_orders(courier: Courier) -> Optional[List[Order]]:
    """
    Function selects orders, which can be assigned to courier by weight, region
    and delievery time. Then function uses greedy algorithm to assign to courier
    as many orders, as courier can carry.
    """
    interval_condition = construct_assign_query(list(courier.intervals.all()))
    max_weight = Courier.WEIGHT_MAP.get(courier.courier_type)
    suitable_orders = Order.objects.filter(
        interval_condition,
        delievery__isnull=True,
        delievered=False,
        weight__lte=max_weight,
        region__couriers=courier
    ).order_by("-weight")
    if not suitable_orders.count():
        return None
    orders_to_assign = fill_weight(suitable_orders, max_weight)
    return orders_to_assign


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
    if courier.intervals.all().count() == 0:
        return None
    orders = select_orders(courier)
    if not orders:
        return None
    delievery = Delievery.objects.create_delievery(
        orders=orders,
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
    order = delievery.orders.filter(delievered=False).get(order_id=order_id)
    if parser.isoparse(complete_time) <= delievery.last_delievery_time:
        raise CompleteTimeError()
    order.complete(
        datetime_string=complete_time,
        start_time=delievery.last_delievery_time
    )
    delievery.last_delievery_time = order.delievery_time
    if not delievery.orders.filter(delievered=False).exists():
        delievery.completed = True
    delievery.save()
    return order
