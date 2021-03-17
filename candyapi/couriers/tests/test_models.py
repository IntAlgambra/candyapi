from django.test import TestCase
from django.db import IntegrityError

from couriers.models import Interval, Region, Courier
from couriers.validators import CourierDataModel, CourierPatchDataModel


class TestInterval(TestCase):

    def testCreateInterval(self):
        """
        Tests creating correct interval
        """
        test_interval_string = "11:34-22:15"
        interval = Interval.objects.create_interval(test_interval_string)
        self.assertEqual(
            interval.start,
            11 * 60 * 60 + 34 * 60
        )
        self.assertEqual(
            interval.end,
            22 * 60 * 60 + 15 * 60
        )

    def testCreateExistingInterval(self):
        test_interval_1 = "11:00-12:00"
        test_interval_2 = "11:00-12:00"
        with self.assertRaises(IntegrityError):
            Interval.objects.create_interval(test_interval_1)
            Interval.objects.create_interval(test_interval_2)

    def testCreateOrFind(self):
        test_interval = "11:00-12:00"
        Interval.objects.create_or_find(test_interval)
        Interval.objects.create_or_find(test_interval)
        self.assertEqual(
            len(Interval.objects.all()),
            1
        )

    def testCreateFromList(self):
        intervals_strings = ["11:00-12:00", "11:15-12:15"]
        intervals = Interval.objects.create_from_list(intervals_strings)
        self.assertEqual(
            len(intervals),
            2
        )

    def testIntervalToString(self):
        """
        Tests if interval coverts to string correctly
        """
        interval_string = "09:32-23:48"
        interval = Interval.objects.create_interval(interval_string)
        self.assertEqual(interval.__str__(), interval_string)


class TestRegion(TestCase):

    def testCreateOrFind(self):
        Region.objects.create_region(1)
        Region.objects.create_region(1)
        self.assertEqual(
            len(Region.objects.all()),
            1
        )

    def testCreateFromList(self):
        regions_list = [1, 2, 42]
        regions = Region.objects.create_from_list(regions_list)
        self.assertEqual(
            len(regions),
            3
        )


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
            intervals=intervals,
            regions=regions
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
            intervals=intervals,
            regions=regions
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


