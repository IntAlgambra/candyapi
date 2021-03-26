from copy import deepcopy

from django.test import SimpleTestCase

from pydantic import ValidationError

from orders.validators import (OrderDataModel,
                               InvalidOrderData,
                               OrderListDataModel,
                               InvalidOrdersInData,
                               CompletionDataModel)


class TestOrderDataModel(SimpleTestCase):

    def testValidData(self):
        """
        Tests order data model with valid input data
        """
        order_data = {
            "order_id": 42,
            "weight": 0.67,
            "region": 22,
            "delivery_hours": ["12:44-13:50", "14:00-16:30"]
        }

        order = OrderDataModel(**order_data)
        self.assertEqual(order.order_id, order_data.get("order_id"))
        self.assertEqual(order.weight, order_data.get("weight"))
        self.assertEqual(order.region, order_data.get("region"))
        self.assertEqual(order.delivery_hours, order_data.get("delivery_hours"))

    def testInvalidTypes(self):
        """
        Tests if it is possible to create order data model from invalid input types
        """
        order_data = {
            "order_id": 42,
            "weight": 0.67,
            "region": 22,
            "delivery_hours": ["12:44-13:50", "14:00-16:30"]
        }
        with self.assertRaises(ValidationError):
            invalid_id_data = {
                **order_data,
                "order_id": 42.12
            }
            OrderDataModel(**invalid_id_data)
        with self.assertRaises(ValidationError):
            invalid_weight_data = {
                **order_data,
                "weight": "13.23"
            }
            OrderDataModel(**invalid_weight_data)
        with self.assertRaises(ValidationError):
            invalid_region_data = {
                **order_data,
                "region": 12.23
            }
            OrderDataModel(**invalid_region_data)


# noinspection DuplicatedCode
class TestOrderListDataModel(SimpleTestCase):
    TEST_DATA = {
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

    def testValidData(self):
        """
        Tests no errors when data is valid
        """
        orders_data = OrderListDataModel(**self.TEST_DATA)
        self.assertEqual(len(orders_data.data), 3)

    def testInvalidSchema(self):
        """
        Tests there is only data field
        """
        invalid_data = deepcopy(self.TEST_DATA)
        invalid_data["stuff"] = "stuff"
        with self.assertRaises(ValidationError):
            OrderListDataModel(**invalid_data)

    def testInvalidOrder(self):
        """
        Tests with one invalid order data
        """
        invalid_data = deepcopy(self.TEST_DATA)
        invalid_data.get("data").append({
            "order_id": 13,
            "weight": 33.5,
            "region": 12,
            "delivery_hours": ["invalid"]
        })
        with self.assertRaises(InvalidOrdersInData) as context:
            OrderListDataModel(**invalid_data)
        invalid_ids = [order.get('id') for order in context.exception.invaid_orders]
        self.assertEqual(
            invalid_ids,
            [13]
        )


class TestCompletionDataModel(SimpleTestCase):

    def testValidData(self):
        """
        Tests creation CompletionModel with valid data
        """
        data = {
            "courier_id": 2,
            "order_id": 33,
            "complete_time": "2021-01-10T10:33:01.42Z"
        }
        data_model = CompletionDataModel(**data)
        self.assertEqual(data_model.courier_id, 2)
        self.assertEqual(data_model.order_id, 33)
        self.assertEqual(data_model.complete_time, "2021-01-10T10:33:01.42Z")
