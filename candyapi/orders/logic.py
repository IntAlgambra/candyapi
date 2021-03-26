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
    Возуждается при попытке завершить заказ ранее, чем был завершен
    предыдущий заказ из развоза
    """

    def __init__(self):
        super(CompleteTimeError, self).__init__(
            "Order complete time can not be earlier than previos delievered order"
        )


def select_orders(courier: Courier) -> Optional[List[Order]]:
    """
    Выбирает заказы, подходящие курьеру по весу, размеру, региону ии времени
    доставки. Затем из подходящих заказов набирает те, которые курьер может развезти
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
    Если курьеру назначена активная доставка (разво). возвращает ее. Если
    доставка не назначена, выбирает для курьера подходящие заказы и создает
    новую доставку, назначает ее курьеру и доавляет заказы. В случае,
    если подходящих заказов нет, возвращает None
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
    Завершает заказ и обновляет время последней доставки в активном развозе.
    Если все заказы в развозе выполнены, завершает развоз
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
