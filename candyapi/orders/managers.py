from __future__ import annotations
from typing import TYPE_CHECKING
from typing import List

if TYPE_CHECKING:
    from .models import Order
    from couriers.models import Region

from django.apps import apps
from django.db import models
from django.db import transaction
from django.utils import timezone
from .validators import OrderDataModel, OrderListDataModel

from utils.models import Region, Interval


class DelieveryManager(models.Manager):

    def create_delievery(self, orders: List[Order], courier: Courier):
        """
        Creates new delievery, adds orders to it
        """
        assigned_time = timezone.now()
        delievery = self.create(
            assigned_time=assigned_time,
            last_delievery_time=assigned_time,
            courier=courier,
            transport_type=courier.courier_type
        )
        for order in orders:
            delievery.orders.add(order)
        return delievery


class OrderManager(models.Manager):

    def create_order(self, data: OrderDataModel) -> Order:
        """
        Creates new order
        """
        order = self.create(
            order_id=data.order_id,
            weight=data.weight,
        )
        order.region = Region.objects.create_or_find(data.region)
        intervals = Interval.objects.create_from_list(data.delivery_hours)
        order.intervals.set(intervals)
        order.save()
        return order

    @transaction.atomic()
    def create_from_list(self, data: OrderListDataModel) -> List[Order]:
        """
        Creates new orders from orders list. Raises IntegrityError when
        attempt to add order with already existing order_id
        """
        return list(map(
            self.create_order,
            data.data
        ))
