from datetime import timedelta

from django.test import TestCase
from django.db import IntegrityError
from django.utils import timezone

from couriers.models import Courier
from couriers.validators import CourierDataModel, CourierPatchDataModel
from orders.models import Order, Delievery
from orders.validators import OrderDataModel, OrderListDataModel
from orders.logic import assign, complete_order
from utils.models import Region, Interval
from candyapi.utils import format_time

from .orders import (COURIER_TYPE_CHANGE_ORDERS,
                     COURIER_REGIONS_CHANGE_ORDERS,
                     COURIER_INTERVALS_CHANGE_ORDERS)


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
        Region.objects.create_from_list(
            courier_data_model.regions
        )
        Interval.objects.create_from_list(
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
        Region.objects.create_from_list(
            courier_data_model.regions
        )
        Interval.objects.create_from_list(
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


# noinspection DuplicatedCode
class TestPatchCourier(TestCase):
    """
    Tests courier updates correctly and all orders, which can not be delieverd
    after courier updates are being unassigned
    """

    @classmethod
    def setUpTestData(cls):
        """
        Tests orders are reassigned if courier type is changing
        """
        courier = Courier.objects.create_courier(
            CourierDataModel(**{
                "courier_id": 1,
                "courier_type": "car",
                "regions": [1, 2],
                "working_hours": ["09:00-17:00"]
            })
        )
        cls.courier_id = courier.courier_id

    def testReassingAfterTypeChange(self):
        """
        Tests orders are correctly reassigned if courier type changed
        """
        Order.objects.create_from_list(
            OrderListDataModel(**{
                "data": COURIER_TYPE_CHANGE_ORDERS
            })
        )
        assign(self.courier_id)
        patch_data_1 = CourierPatchDataModel(**{
            "courier_type": "bike",
        })
        courier = Courier.objects.get(courier_id=self.courier_id)
        courier.update(patch_data_1)
        courier.refresh_from_db()
        delievery = courier.delieveries.get(completed=False)
        self.assertEqual(
            set([order.order_id for order in delievery.orders.all()]),
            {2, 3, 5}
        )

    def testReassignAfterRegionChange(self):
        """
        Tests orders are correctly reassigned if courier regions changes
        """
        Order.objects.create_from_list(
            OrderListDataModel(**{
                "data": COURIER_REGIONS_CHANGE_ORDERS
            })
        )
        assign(self.courier_id)
        patch_data = CourierPatchDataModel(**{
            "regions": [1],
        })
        courier = Courier.objects.get(courier_id=self.courier_id)
        courier.update(patch_data)
        courier.refresh_from_db()
        delievery = courier.delieveries.get(completed=False)
        self.assertEqual(
            set([order.order_id for order in delievery.orders.all()]),
            {1, 2}
        )

    def testReassignAfterIntervalsChange(self):
        """
        Tests orders are correctly reassigned if courier working hours changes
        """
        Order.objects.create_from_list(
            OrderListDataModel(**{
                "data": COURIER_INTERVALS_CHANGE_ORDERS
            })
        )
        assign(self.courier_id)
        patch_data = CourierPatchDataModel(**{
            "working_hours": ["09:00-13:00"],
        })
        courier = Courier.objects.get(courier_id=self.courier_id)
        courier.update(patch_data)
        courier.refresh_from_db()
        delievery = courier.delieveries.get(completed=False)
        self.assertEqual(
            set([order.order_id for order in delievery.orders.all()]),
            {1, 2}
        )


class TestCourierStats(TestCase):

    def testCalcRating(self):
        """
        Tests courier rating calculations
        """
        # create courier
        courier = Courier.objects.create_courier(
            CourierDataModel(**{
                "courier_id": 1,
                "courier_type": "foot",
                "regions": [1, 2, 3, 4],
                "working_hours": ["09:00-17:00"]
            })
        )
        # creating orders for 3 of 4 regions
        for region_id in range(1, 4):
            for order_id in range(region_id * 10, region_id * 10 + 5):
                Order.objects.create_order(
                    OrderDataModel(**{
                        "order_id": order_id,
                        "weight": 0.5,
                        "region": region_id,
                        "delivery_hours": ["12:00-13:00"]
                    })
                )
        # assigning all these orders to courier
        delievery = assign(courier_id=courier.courier_id)
        # Should be assigned 15 orders
        self.assertEqual(
            delievery.orders.all().count(),
            15
        )
        # now lets complete all orders in 30 minutes (that would get us
        # 2.5 rating)
        for order in delievery.orders.all():
            start_time = delievery.last_delievery_time
            completion_time = start_time + timedelta(minutes=30)
            complete_order(
                courier_id=courier.courier_id,
                order_id=order.order_id,
                complete_time=format_time(completion_time)
            )
            delievery.refresh_from_db()
        # now let's check rating (it should be 2.5)
        courier.refresh_from_db()
        self.assertEqual(
            courier.calculate_rating(),
            2.50
        )
        self.assertEqual(delievery.completed, True)
        # Let's add 7 more orders for region 4
        for order_id in range(40, 47):
            Order.objects.create_order(
                OrderDataModel(**{
                    "order_id": order_id,
                    "weight": 0.5,
                    "region": 4,
                    "delivery_hours": ["12:00-13:00"]
                })
            )
        # assigning new orders
        second_delievery = assign(courier.courier_id)
        # if we want to get rating "4" minimum mean delievery time should be
        # 720 seconds. let's complete 1 order in 540 second, and add 60 seconds
        # to every next order, so resulting mean time will be 720 seconds
        test = []
        for index, order in enumerate(second_delievery.orders.all()):
            start_time = second_delievery.last_delievery_time
            completion_time = start_time + timedelta(
                seconds=540 + index * 60
            )
            test.append(540 + index * 60)
            complete_order(
                order_id=order.order_id,
                courier_id=courier.courier_id,
                complete_time=format_time(completion_time)
            )
            second_delievery.refresh_from_db()
        courier.refresh_from_db()
        self.assertEqual(
            courier.calculate_rating(),
            4.0
        )

    def testCalcEarning(self):
        courier = Courier.objects.create_courier(
            CourierDataModel(**{
                "courier_id": 1,
                "courier_type": "foot",
                "regions": [1, 2, 3, 4],
                "working_hours": ["09:00-17:00"]
            })
        )
        Order.objects.create_order(
            OrderDataModel(**{
                "order_id": 1,
                "weight": 0.5,
                "region": 1,
                "delivery_hours": ["12:00-13:00"]
            })
        )
        Order.objects.create_order(
            OrderDataModel(**{
                "order_id": 2,
                "weight": 35,
                "region": 1,
                "delivery_hours": ["12:00-13:00"]
            })
        )
        assign(courier_id=courier.courier_id)
        complete_order(
            courier_id=courier.courier_id,
            order_id=1,
            complete_time=format_time(
                timezone.now() + timedelta(minutes=15)
            )
        )
        courier.courier_type = "car"
        courier.save()
        courier.refresh_from_db()
        assign(courier.courier_id)
        complete_order(
            courier_id=courier.courier_id,
            order_id=2,
            complete_time=format_time(
                timezone.now() + timedelta(minutes=25)
            )
        )
        courier.refresh_from_db()
        self.assertEqual(
            courier.calculate_earnings(),
            500 * (2 + 9)
        )
