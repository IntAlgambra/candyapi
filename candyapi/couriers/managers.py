from django.db import models, transaction
from django.core.exceptions import ObjectDoesNotExist

from .validators import CourierDataModel, CouriersListDataModel
from utils.models import Region, Interval


class CourierManager(models.Manager):

    def create_courier(self, data: CourierDataModel):
        """
        Создает объект курьера из объекта CourierDataModel
        и возвращает его
        """
        courier = self.create(
            courier_id=data.courier_id,
            courier_type=data.courier_type,
        )
        courier.save()
        courier.regions.set(
            Region.objects.create_from_list(data.regions)
        )
        courier.intervals.set(
            Interval.objects.create_from_list(data.working_hours)
        )
        return courier



