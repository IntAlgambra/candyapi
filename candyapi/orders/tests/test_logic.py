import json
from datetime import timedelta
from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from couriers.models import Courier, Region, Interval
from couriers.validators import CourierDataModel
from orders.models import Order
from orders.validators import OrderDataModel
from orders.logic import assign, complete_order
from candyapi.utils import format_time


class TestLogic(TestCase):
    """
    Tests assigment and completion logic
    """

    @classmethod
    def setUpTestData(cls):
        """
        Adding to database orders from test_orders.json
        """
        # can deliever orders 1, 3
        courier_data = {
            "courier_id": 42,
            "courier_type": "foot",
            "regions": [1, 12, 22],
            "working_hours": ["11:00-14:00", "05:00-09:00"]
        }
        courier_model = CourierDataModel(**courier_data)
        courier = Courier.objects.create_courier(
            data=courier_model,
        )
        cls.courier_id = courier.courier_id
        test_orders_files_path = settings.BASE_DIR / "orders" / "tests" / "test_orders.json"
        with open(test_orders_files_path, "r") as f:
            orders_data = json.load(f)
            for order_data in orders_data["orders"]:
                Order.objects.create_order(
                    OrderDataModel(**order_data)
                )

    def testSimpleAssign(self):
        """
        Tests assigning orders to courier.
        """
        delievery = assign(self.courier_id)
        # checking delievery time, rounded to seconds
        self.assertEqual(
            round(timezone.now().timestamp()),
            round(delievery.last_delievery_time.timestamp())
        )
        orders = delievery.orders.all()
        # checking only tho orders was assigned
        self.assertEqual(
            [order.order_id for order in orders],
            [1, 3]
        )

    def testNoSuitableOrders(self):
        """
        Tests no delevery is created when no suitable orders for courier found
        """
        courier = Courier.objects.create_courier(
            data=CourierDataModel(**{
                "courier_id": 100500,
                "courier_type": "foot",
                "regions": [100500],
                "working_hours": ["11:00-14:00", "05:00-09:00"]
            }),
        )
        delievery = assign(courier.courier_id)
        self.assertIsNone(delievery)

    def testCompleteOrder(self):
        """
        Tests order completion
        """
        delievery = assign(self.courier_id)
        complete_time = delievery.assigned_time + timedelta(minutes=30)
        order = complete_order(
            order_id=delievery.orders.all().first().order_id,
            courier_id=self.courier_id,
            complete_time=format_time(complete_time)
        )
        delievery.refresh_from_db()
        self.assertTrue(order.delievered)
        self.assertEqual(
            format_time(order.delievery_time),
            format_time(complete_time)
        )
        self.assertEqual(
            format_time(delievery.last_delievery_time),
            format_time(complete_time)
        )

    def testCompleteAllOrders(self):
        """
        Tests delievery is completed after all orders is completed
        """
        delievery = assign(self.courier_id)
        for order in delievery.orders.all():
            delievery.refresh_from_db()
            completion_time = delievery.last_delievery_time + timedelta(minutes=30)
            complete_order(
                order_id=order.order_id,
                courier_id=self.courier_id,
                complete_time=format_time(completion_time)
            )
        delievery.refresh_from_db()
        self.assertTrue(delievery.completed)

    def testCompleteWithWrongCourier(self):
        """
        Tests attemt to complete order, assigned to another courier
        """
        courier = Courier.objects.create_courier(
            data=CourierDataModel(**{
                "courier_id": 100500,
                "courier_type": "foot",
                "regions": [100500],
                "working_hours": ["11:00-14:00", "05:00-09:00"]
            }),
        )
        delievery = assign(self.courier_id)
        with self.assertRaises(ObjectDoesNotExist):
            complete_order(
                order_id=delievery.orders.all().first().order_id,
                courier_id=courier.courier_id,
                complete_time=format_time(
                    timezone.now()
                )
            )

    def testCompleteCompletedOrder(self):
        """
        Tests attempt to complete already completed order
        """
        delievery = assign(self.courier_id)
        complete_order(
            courier_id=self.courier_id,
            order_id=delievery.orders.first().order_id,
            complete_time=format_time(
                timezone.now() + timedelta(minutes=30)
            )
        )
        with self.assertRaises(ObjectDoesNotExist):
            complete_order(
                courier_id=self.courier_id,
                order_id=delievery.orders.first().order_id,
                complete_time=format_time(
                    timezone.now() + timedelta(minutes=40)
                )
            )

    def testCompleteNonExistingOrder(self):
        """
        Tests attempt to complete order which does not exist
        """
        assign(self.courier_id)
        with self.assertRaises(ObjectDoesNotExist):
            complete_order(
                courier_id=self.courier_id,
                order_id=100500300,
                complete_time=format_time(
                    timezone.now() + timedelta(minutes=30)
                )
            )

    def testCompletNotAssignedOrder(self):
        """
        Tests attempt to complete order which was not assigned
        """
        assign(self.courier_id)
        unassigned = Order.objects.filter(delievery__isnull=True).first()
        with self.assertRaises(ObjectDoesNotExist):
            complete_order(
                order_id=unassigned.order_id,
                courier_id=self.courier_id,
                complete_time=format_time(
                    timezone.now() + timedelta(minutes=30)
                )
            )



