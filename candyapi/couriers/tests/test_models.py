from django.test import TestCase
from django.db import IntegrityError

from couriers.models import Courier
from couriers.validators import CourierDataModel, CourierPatchDataModel

from utils.models import Region, Interval


class TestCourier(TestCase):

    @classmethod
    def setUpTestData(cls):
        courier_data = {
            "courier_id": 42,
            "courier_type": "foot",
            "regions": [1, 12, 22],
            "working_hours": ["11:35-14:05", "09:00-11:00"]
        }
        courier_data_model = CourierDataModel(**courier_data)
        regions = Region.objects.create_from_list(
            courier_data_model.regions
        )
        intervals = Interval.objects.create_from_list(
            courier_data_model.working_hours
        )
        courier = Courier.objects.create_courier(
            data=courier_data_model,
        )
        cls.test_courier_id = courier.courier_id

    def testCreateCourier(self):
        """
        Tests courier creation with valid data
        """
        courier_data = {
            "courier_id": 1,
            "courier_type": "foot",
            "regions": [1, 12, 22],
            "working_hours": ["11:35-14:05", "09:00-11:00"]
        }
        courier_data_model = CourierDataModel(**courier_data)
        regions = Region.objects.create_from_list(
            courier_data_model.regions
        )
        intervals = Interval.objects.create_from_list(
            courier_data_model.working_hours
        )
        courier = Courier.objects.create_courier(
            data=courier_data_model,
        )
        self.assertEqual(
            courier.courier_id,
            courier_data.get("courier_id")
        )
        self.assertEqual(
            courier.courier_type,
            courier_data.get("courier_type")
        )
        self.assertEqual(
            len(courier.regions.all()),
            3
        )
        self.assertEqual(
            len(courier.intervals.all()),
            2
        )

    def testUpdateCourier(self):
        """
        Tests courier updating
        """
        patch_data_1 = CourierPatchDataModel(**{
            "courier_type": "car",
            "regions": [1, 2, 3]
        })
        courier = Courier.objects.get(courier_id=self.test_courier_id)
        courier.update(patch_data_1)
        courier.refresh_from_db()
        self.assertEqual(
            Courier.objects.get(courier_id=self.test_courier_id).courier_type,
            "car"
        )
