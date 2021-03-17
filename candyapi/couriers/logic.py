"""
Module contains bisnes logic for managing couriers in database
"""
from typing import List

from django.db import transaction

from .models import Courier, Region, Interval
from .validators import CouriersListDataModel


@transaction.atomic
def create_couriers_from_list(couriers: CouriersListDataModel) -> List[int]:
    """
    Function creates several couriers from input data. Couriers added inside
    transaction_atomic  to prevent database changes in case of errors
    """
    created_couriers = []
    for courier in couriers.data:
        regions = Region.objects.create_from_list(courier.regions)
        intervals = Interval.objects.create_from_list(courier.working_hours)
        courier_object = Courier.objects.create_courier(
            data=courier,
            regions=regions,
            intervals=intervals
        )
        created_couriers.append(courier_object.courier_id)
    return created_couriers
