from functools import reduce

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import QuerySet

from .managers import CourierManager
from .validators import CourierPatchDataModel
from orders.utils import construct_assign_query
from orders.models import Order
from utils.models import Interval, Region


class Courier(models.Model):
    """
    Класс описывает модель данных курьеров
    fields:
        courier_id (int): courier identifier
        courier_type (str): courier type, can be foot, bike or car
        regions: links to regions courier can serve
        rating (float): courier rating
        earnings (float): courier earnings
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
    rating = models.FloatField(default=5)
    earnings = models.FloatField(default=0)
    last_deliver_time = models.DateTimeField(null=True)

    objects = CourierManager()

    def update(self, data: CourierPatchDataModel):
        """
        Updates courier data. If courier has active delievery, checks if there are
        orders, whick courier can not deliever after changes. If there are,
        unassignes these orders.
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
            unfitted_orders = active_delievery.orders.exclude(
                interval_condition,
                region__couriers=self,
                weight__lte=new_max_weight,
            )
            for order in unfitted_orders:
                order.delievery = None
                order.save()
        except ObjectDoesNotExist:
            pass
        finally:
            return self.to_dict()

    def calculate_earnings(self) -> int:
        """
        Calculates courier earnings based on completed delieveries
        """
        delieveres = self.delieveries.filter(completed=True)
        return sum([
            500 * self.EARNINGS_EFFICIENCY.get(delievery.transport_type)
            for delievery in delieveres
        ])

    def _calc_mean_delievery_time(self, region_id: int) -> float:
        """
        Calculates mean delievery time for region with
        provided region id
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

    def calculate_rating(self):
        """
        Calculates courier rating
        """
        # selects all region where courier has completed orders
        regions_with_completed_orders = Region.objects.filter(
            order__delievered=True,
            order__delievery__courier_id=self.courier_id
        )
        min_mean_time = min(
            self._calc_mean_delievery_time(region.region_id) for
            region in regions_with_completed_orders
        )
        rating = (3600 - min(min_mean_time, 3600)) / 3600 * 5
        return round(rating, 2)

    def to_dict(self):
        """
        Returns courier info without rating and earnings
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
        Returns courier info
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
