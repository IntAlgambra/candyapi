import json

from unittest.mock import patch, MagicMock
from django.test import SimpleTestCase
from django.test import Client

from couriers.validators import InvalidCouriersInDataError


# noinspection DuplicatedCode
class TestPostCouriers(SimpleTestCase):

    @staticmethod
    def post_couriers():
        TEST_DATA = {
            "data": [
                {
                    "courier_id": 1,
                    "courier_type": "foot",
                    "regions": [1, 12, 22],
                    "working_hours": ["11:35-14:05", "09:00-11:00"]
                },
                {
                    "courier_id": 2,
                    "courier_type": "bike",
                    "regions": [22],
                    "working_hours": ["09:00-18:00"]},
                {
                    "courier_id": 3,
                    "courier_type": "car",
                    "regions": [12, 22, 23, 33],
                    "working_hours": []
                },
            ]
        }
        c = Client()
        response = c.post(
            path="/couriers",
            content_type="application/json",
            data=TEST_DATA
        )
        return response

    @patch("couriers.views.create_couriers_from_list")
    def testSuccesfulPost(self, create_couriers_mock: MagicMock):
        """
        Tests successful POST request to /couriers
        """
        returned = [1, 2, 3]
        create_couriers_mock.return_value = returned
        c = Client()
        response = self.post_couriers()
        created = response.json()["couriers"]
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            created,
            [{"id": v} for v in returned]
        )

    @patch("couriers.CouriersListDataModel")
    def invalidCourierPost(self, data_model_mock: MagicMock):
        """
        Tests response if some of courier data is invalid
        """
        data_model_mock.side_effect = InvalidCouriersInDataError([1, 2, 3])
        response = self.post_couriers()
        self.assertEqual(response.status_code, 400)

