from django.db import models
from .managers import RegionManager, IntervalManager


class Region(models.Model):
    """
    Класс описывает модель данных регионов
    поля:
        region_id (int): идентификатор региона
    """
    region_id = models.IntegerField(primary_key=True, unique=True)
    objects = RegionManager()


class Interval(models.Model):
    """
    Описывает модель интервалов (раоты курьера или доставки заказа)
    поля:
        start (int): начало в секундах от 00:00
        end (int): окончание в секундах от 00:00
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
