import dateutil.parser
from datetime import datetime

from django.db import models

from .managers import OrderManager, DelieveryManager


class Delievery(models.Model):
    """
    Модель описывает таблицу Развозов (Доставок), создаваемых
    при назначении курьеру заказов
    поля:
        assigned_time: время создания развоза
        last_delievery_time: время завершения последнего на данный момент
            заказа из развоза. Еси таковых нет, равняется assigned_time
        courier: ссылка на курьера, которому назначен развоз
        completed: флаг, обозначающий завершен ли развоз
        transport_type: тип курьера на момент назначния развоза
    """
    assigned_time = models.DateTimeField()
    last_delievery_time = models.DateTimeField()
    courier = models.ForeignKey(to="couriers.Courier",
                                related_name="delieveries",
                                on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    transport_type = models.CharField(default="foot", max_length=4)
    objects = DelieveryManager()


class Order(models.Model):
    """
    Описывает таблицу заказов в БД
    поля:
        order_id: идентификатор и первичный ключ
        weight: вес заказа
        region: регион заказа
        intervals: интервалы, в которые может быть принята доставка
        delievered: флаг, обозначающий завершен ли заказ
        delievery_time: время завершения заказа
        completion_time: время, за которео был завершен заказ в секундах
        delievery: развоз, к которому принадлежит заказ
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
        Завершает развоз
        """
        complete_time = dateutil.parser.isoparse(datetime_string)
        self.delievered = True
        self.delievery_time = complete_time
        time_to_complete = (complete_time - start_time).total_seconds()
        self.completion_time = time_to_complete
        self.save()
