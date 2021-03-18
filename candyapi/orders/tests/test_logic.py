import json
from django.test import TestCase
from django.conf import settings
from django.utils import timezone

from couriers.models import Courier, Region, Interval
from couriers.validators import CourierDataModel
from orders.models import Order
from orders.validators import OrderDataModel
from orders.logic import assign
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
        courier_data = {
            "courier_id": 42,
            "courier_type": "foot",
            "regions": [1, 12, 22],
            "working_hours": ["11:00-14:00", "05:00-09:00"]
        }
        courier_model = CourierDataModel(**courier_data)
        courier = Courier.objects.create_courier(
            data=courier_model,
            regions=Region.objects.create_from_list(courier_model.regions),
            intervals=Interval.objects.create_from_list(courier_model.working_hours)
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
        courier = Courier.objects.get(courier_id=self.courier_id)
        orders = assign(courier.courier_id).orders.all()
        print(orders)
        self.assertEqual(
            [order.order_id for order in orders],
            [1, 3]
        )
