"""
Module contains bisnes logic for managing couriers in database
"""
from typing import List

from django.db import transaction

from .models import Courier
from .validators import CouriersListDataModel, CourierDataModel


@transaction.atomic
def create_couriers_from_list(couriers: CouriersListDataModel) -> List[int]:
    """
    Function creates several couriers from input data. Couriers added inside
    transaction_atomic  to prevent database changes in case of errors
    """
    created_couriers = []
    for courier in couriers.data:
        courier_object = Courier.objects.create_courier(
            data=CourierDataModel(**courier)
        )
        created_couriers.append(courier_object.courier_id)
    return created_couriers
