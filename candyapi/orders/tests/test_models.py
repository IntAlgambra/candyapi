from django.test import TestCase
from django.db import IntegrityError

from orders.models import Order
from orders.validators import OrderDataModel, OrderListDataModel


# noinspection DuplicatedCode
class OrderModelTest(TestCase):

    def testCreateOrder(self):
        """
        Tests creation order with valid data
        """
        order_data = {
            "order_id": 42,
            "weight": 0.67,
            "region": 22,
            "delivery_hours": ["12:44-13:50", "14:00-16:30"]
        }
        order_model = OrderDataModel(**order_data)
        order = Order.objects.create_order(order_model)
        self.assertEqual(order.order_id, order_model.order_id)

    def testCreateOrdersFromList(self):
        """
        Tests creation of several orders from list
        """
        orders_data = {
            "data": [
                {
                    "order_id": 42,
                    "weight": 0.67,
                    "region": 22,
                    "delivery_hours": ["12:44-13:50", "14:00-16:30"]
                },
                {
                    "order_id": 45,
                    "weight": 25,
                    "region": 20,
                    "delivery_hours": ["09:00-12:00", "15:00-16:30"]
                },
                {
                    "order_id": 13,
                    "weight": 33.5,
                    "region": 12,
                    "delivery_hours": ["03:00-05:00"]
                }
            ]
        }
        orders_list = OrderListDataModel(**orders_data)
        orders = Order.objects.create_from_list(orders_list)
        self.assertEqual(len(orders), 3)

    def testAttemptToCreateExistingOrder(self):
        """
        Tests attempt to create order which is already exists
        """
        order_data_1 = {
            "data": [
                {
                    "order_id": 42,
                    "weight": 0.67,
                    "region": 22,
                    "delivery_hours": ["12:44-13:50", "14:00-16:30"]
                },
                {
                    "order_id": 45,
                    "weight": 25,
                    "region": 20,
                    "delivery_hours": ["09:00-12:00", "15:00-16:30"]
                },
            ]
        }
        Order.objects.create_from_list(OrderListDataModel(**order_data_1))
        order_data_2 = {
            "data": [
                {
                    "order_id": 42,
                    "weight": 0.67,
                    "region": 22,
                    "delivery_hours": ["12:44-13:50", "14:00-16:30"]
                },
            ]
        }
        with self.assertRaises(IntegrityError):
            Order.objects.create_from_list(OrderListDataModel(**order_data_2))

class DelieveryModeltest(TestCase):
    pass
