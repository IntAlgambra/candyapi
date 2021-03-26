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
    Создает курьеров из списка с данными курьеров. Обернута в transaction.atomic
    чтобы гарантировать, что при ошибке ни один курьер из списка не будет
    добавлен в БД
    """
    created_couriers = []
    for courier in couriers.data:
        courier_object = Courier.objects.create_courier(
            data=CourierDataModel(**courier)
        )
        created_couriers.append(courier_object.courier_id)
    return created_couriers
