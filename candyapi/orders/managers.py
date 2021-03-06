from __future__ import annotations
from typing import TYPE_CHECKING
from typing import List, Dict

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
        Создает новый развоз, добавляет в него заказы из переданного
        списка и наначает его переданому курьеру
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
        Создает новый заказ
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
    def create_from_list(self, data: List[Dict]) -> List[Order]:
        """
        Создает заказы из переданного списка. Обернута в transaction.atomic,
        чтобы предотвратить частичное добавление заказов в БД при ошибках
        """
        return list(map(
            self.create_order,
            [OrderDataModel(**order_data) for order_data in data ]
        ))
