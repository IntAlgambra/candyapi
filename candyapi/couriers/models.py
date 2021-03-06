from functools import reduce

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import QuerySet

from .managers import CourierManager
from .validators import CourierPatchDataModel
from orders.utils import construct_assign_query, fill_weight
from orders.models import Order
from utils.models import Interval, Region


class Courier(models.Model):
    """
    Класс описывает модель данных курьеров
    поля:
        courier_id (int): идентификатор курьера
        courier_type (str): тип курьера, может быть foot, bike или car
        regions: регионы, в которых работает курьер (ссылка на таблицу с регионами)
    """
    WEIGHT_MAP = {
        "foot": 10,
        "bike": 15,
        "car": 50
    }
    EARNINGS_EFFICIENCY = {
        "foot": 2,
        "bike": 5,
        "car": 9
    }
    courier_id = models.IntegerField(primary_key=True, unique=True)
    courier_type = models.CharField(max_length=4)
    regions = models.ManyToManyField(to="utils.Region", related_name="couriers")
    intervals = models.ManyToManyField(to="utils.Interval", related_name="couriers")

    objects = CourierManager()

    def update(self, data: CourierPatchDataModel):
        """
        Обновляет данные курьера и проверяет, назначена ли курьеру активная доставка (развоз).
        Если активная доставка присутствует, проверяет, все ли заказы из доставки курьер
        может развести. Если нет, те заказы, которые курьер теперь развезти не может
        попадают в пул свободных к выдаче
        """
        if data.courier_type:
            self.courier_type = data.courier_type
            self.save()
        if data.working_hours:
            intervals = Interval.objects.create_from_list(data.working_hours)
            self.intervals.set(intervals)
        if data.regions:
            regions = Region.objects.create_from_list(data.regions)
            self.regions.set(regions)
        try:
            active_delievery = self.delieveries.get(completed=False)
            interval_condition = construct_assign_query(
                list(self.intervals.all())
            )
            new_max_weight = self.WEIGHT_MAP.get(self.courier_type)
            new_suitable_orders = active_delievery.orders.filter(
                interval_condition,
                region__couriers=self,
                weight__lte=new_max_weight,
            ).order_by("-weight")
            orders_to_keep = fill_weight(new_suitable_orders, new_max_weight)
            for order in active_delievery.orders.filter(delievered=False):
                if order not in orders_to_keep:
                    order.delievery = None
                    order.save()
            active_delievery.refresh_from_db()
            if not active_delievery.orders.all().count():
                active_delievery.delete()
        except ObjectDoesNotExist:
            pass
        finally:
            return self.to_dict()

    def calculate_earnings(self) -> int:
        """
        Рассчитывает заработок курьера
        """
        delieveres = self.delieveries.filter(completed=True)
        return sum([
            500 * self.EARNINGS_EFFICIENCY.get(delievery.transport_type)
            for delievery in delieveres
        ])

    def _calc_mean_delievery_time(self, region_id: int) -> float:
        """
        Рассчитывает среднее время доставки курьера по региону с
        переданным region_id
        """
        completed_orders = Order.objects.filter(
            delievery__courier__courier_id=self.courier_id,
            delievered=True,
            region_id=region_id
        )
        mean = sum([
            order.completion_time for order in completed_orders
        ]) / completed_orders.count()
        return mean

    def calculate_rating(self) -> float:
        """
        Рассчитывает рейтинг курьера. Если у курьера пока нет заверенных
        заказов, возвращает -1
        """
        # selects all region where courier has completed orders
        regions_with_completed_orders = Region.objects.filter(
            order__delievered=True,
            order__delievery__courier_id=self.courier_id
        )
        if not regions_with_completed_orders.exists():
            return -1
        min_mean_time = min(
            [self._calc_mean_delievery_time(region.region_id) for
             region in regions_with_completed_orders]
        )
        rating = (3600 - min(min_mean_time, 3600)) / 3600 * 5
        return round(rating, 2)

    def to_dict(self):
        """
        Возвращает данные курьера без рейтинга и без заработка
        """
        return {
            "courier_id": self.courier_id,
            "courier_type": self.courier_type,
            "regions:": [
                region.region_id for region in self.regions.all()
            ],
            "working_hours": [
                str(interval) for interval in self.intervals.all()
            ]
        }

    def info(self):
        """
        Возвращает информацию о курьере
        """
        rating = self.calculate_rating()
        if rating >= 0:
            return {
                **self.to_dict(),
                "rating": self.calculate_rating(),
                "earnings": self.calculate_earnings()
            }
        else:
            return {
                **self.to_dict(),
                "earnings": 0
            }
