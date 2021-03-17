from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from .managers import CourierManager, IntervalManager, RegionManager
from .validators import CourierPatchDataModel
from orders.utils import construct_assign_query


class Region(models.Model):
    """
    Класс описывает модель данных регионов
    fields:
        region_id (int): region identifier
    """
    region_id = models.IntegerField(primary_key=True, unique=True)
    objects = RegionManager()


class Interval(models.Model):
    """
    Class describes model of time interval data
    fields:
        start (int): seconds from 00:00
        end (int): seconds from 00:00
    """

    class Meta:
        unique_together = ("start", "end")

    start = models.IntegerField()
    end = models.IntegerField()
    objects = IntervalManager()

    def __str__(self):
        start_hours = "{}".format(self.start // (60 * 60)).zfill(2)
        start_minutes = "{}".format((self.start % (60 * 60)) // 60).zfill(2)
        end_hours = "{}".format(self.end // (60 * 60)).zfill(2)
        end_minutes = "{}".format((self.end % (60 * 60)) // 60).zfill(2)
        return "{}:{}-{}:{}".format(
            start_hours,
            start_minutes,
            end_hours,
            end_minutes
        )


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
    courier_id = models.IntegerField(primary_key=True, unique=True)
    courier_type = models.CharField(max_length=4)
    regions = models.ManyToManyField(to=Region, related_name="couriers")
    intervals = models.ManyToManyField(to=Interval, related_name="couriers")
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

    def to_dict(self):
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
