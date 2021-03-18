# Needed only for type hints work correctly
from __future__ import annotations
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .models import Region, Interval

from django.db import models, transaction
from django.core.exceptions import ObjectDoesNotExist

from .validators import CourierDataModel, CouriersListDataModel


class CourierManager(models.Manager):

    def create_courier(self,
                       data: CourierDataModel,
                       regions: List[Region] = [],
                       intervals: List[Interval] = []) -> self.model.__class__:
        """
        Creates new courier in database and returns orm representations
        """
        courier = self.create(
            courier_id=data.courier_id,
            courier_type=data.courier_type,
        )
        courier.save()
        courier.regions.set(regions)
        courier.intervals.set(intervals)
        return courier



