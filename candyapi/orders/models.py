import dateutil.parser
from datetime import datetime

from django.db import models

from .managers import OrderManager, DelieveryManager


class Delievery(models.Model):
    """
    Model describes set of orders assigned to courier via
    one request to /orders/assign. Courier earnings depends
    on how much Delieveres (Развоз) courier has complete
    """
    assigned_time = models.DateTimeField()
    last_delievery_time = models.DateTimeField()
    courier = models.ForeignKey(to="couriers.Courier",
                                related_name="delieveries",
                                on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    objects = DelieveryManager()


class Order(models.Model):
    """
    Model describes order instance in database
    """
    order_id = models.IntegerField(primary_key=True, unique=True)
    weight = models.FloatField()
    region = models.ForeignKey(to="utils.Region",
                               null=True,
                               on_delete=models.SET_NULL)
    intervals = models.ManyToManyField(to="utils.Interval")
    delievered = models.BooleanField(default=False)
    delievery_time = models.DateTimeField(null=True)
    completion_time = models.IntegerField(null=True)
    delievery = models.ForeignKey(to=Delievery,
                                  related_name="orders",
                                  null=True,
                                  on_delete=models.SET_NULL)

    objects = OrderManager()

    def __str__(self):
        return "order id: {}".format(self.order_id)

    def complete(self, datetime_string: str, start_time: datetime) -> None:
        """
        Process order completion
        """
        complete_time = dateutil.parser.isoparse(datetime_string)
        self.delievered = True
        self.delievery_time = complete_time
        time_to_complete = (complete_time - start_time).total_seconds()
        self.completion_time = time_to_complete
        self.save()
