from copy import deepcopy

from django.test import SimpleTestCase
from pydantic import ValidationError
from couriers.validators import (CourierDataModel,
                                 CouriersListDataModel,
                                 InvalidCouriersInDataError,
                                 InvalidCourierData,
                                 CourierPatchDataModel,
                                 CouriersValidationError)


class TestCourierDataModel(SimpleTestCase):

    def testValidData(self):
        valid_courier = {
            "courier_id": 1,
            "courier_type": "foot",
            "regions": [1, 12, 22],
            "working_hours": ["11:35-14:05", "09:00-11:00"]
        }
        try:
            CourierDataModel(**valid_courier)
        except:
            self.fail("exception in courier data model creation")

    def testExcessField(self):
        excess_field = {
            "courier_id": 1,
            "courier_type": "foot",
            "regions": [1, 12, 22],
            "working_hours": ["11:35-14:05", "09:00-11:00"],
            "favorite_movies": ["Scott Pilgrim vs the World"]
        }
        with self.assertRaises(ValidationError) as context:
            CourierDataModel(**excess_field)
        self.assertIn(
            "No extra fields allowed",
            context.exception.__str__()
        )

    def testInvalidWorkingHours(self):
        """
        Tests working hours validation
        """
        invalid_courier = {
            "courier_id": 1,
            "courier_type": "foot",
            "regions": [1, 12, 22],
            "working_hours": ["11:35-14:05", "09:00-11:65"]
        }
        with self.assertRaises(ValidationError) as context:
            CourierDataModel(**invalid_courier)
        self.assertIn("working hours interval must be in format hh:mm-hh:mm",
                      context.exception.__str__())

    def testInvalidCourierType(self):
        """
        Tests courier_type validation
        """
        invalid_courier = {
            "courier_id": 1,
            "courier_type": "spaceship",
            "regions": [1, 12, 22],
            "working_hours": ["11:35-14:05", "09:00-11:54"]
        }
        with self.assertRaises(ValidationError) as context:
            CourierDataModel(**invalid_courier)
        self.assertIn("courier_type must be car, bike or foot",
                      context.exception.__str__())

    def testInvalidCourierId(self):
        """
        Tests courier_id validation
        """
        invalid_courier = {
            "courier_id": 1.2,
            "courier_type": "foot",
            "regions": [1, 12, 22],
            "working_hours": ["11:35-14:05", "09:00-11:54"]
        }
        with self.assertRaises(InvalidCourierData) as context:
            CourierDataModel(**invalid_courier)

    def testInvalidRegionNumber(self):
        """
        Tests validation error if regions field contains
        non-integer values
        """
        invalid_courier = {
            "courier_id": 1,
            "courier_type": "foot",
            "regions": [1, 12.3, 22],
            "working_hours": ["11:35-14:05", "09:00-11:54"]
        }
        with self.assertRaises(InvalidCourierData) as context:
            CourierDataModel(**invalid_courier)


class CouriersListDataModelTest(SimpleTestCase):
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

    def testValidData(self):
        """
        Tests model works correctly with valid data
        """
        try:
            CouriersListDataModel(**self.TEST_DATA)
        except ValidationError as e:
            print(e.errors())
            self.fail("exception in couriers list data model creation")

    def testExcessField(self):
        """
        Tests no extra fields allowed
        """
        extra_fields_data = {
            **self.TEST_DATA,
            "pirates": ["Black Beard", "Captain Jack Sparrow"]
        }
        with self.assertRaises(ValidationError) as context:
            CouriersListDataModel(**extra_fields_data)
        self.assertIn(
            "No excess fields allowed",
            context.exception.__str__()
        )

    def testNoDataField(self):
        invalid_data = {
            "stuff": "some stuff"
        }
        with self.assertRaises(CouriersValidationError):
            CouriersListDataModel(**invalid_data)

    def testInvalidCourier(self):
        data_with_invalid_user = deepcopy(self.TEST_DATA)
        data_with_invalid_user["data"][0]["courier_type"] = "teleport"
        data_with_invalid_user["data"][1]["courier_id"] = 1.2
        data_with_invalid_user["data"][2]["regions"] = [1.3, 3, 4]
        with self.assertRaises(InvalidCouriersInDataError) as context:
            CouriersListDataModel(**data_with_invalid_user)
        self.assertIn(1, context.exception.invalid_couriers)
        self.assertIn(1.2, context.exception.invalid_couriers)
        self.assertIn(3, context.exception.invalid_couriers)


class CourierPatchDataModelTest(SimpleTestCase):

    def testValidData(self):
        data = {
            "courier_type": "car",
            "regions": [1, 2, 3],
            "working_hours": ["12:45-14:30", "20:00-22:15"]
        }
        patch_data = CourierPatchDataModel(**data)
        self.assertEqual(patch_data.courier_type, "car")
        data = {
            "courier_type": "car",
            "working_hours": ["12:45-14:30", "20:00-22:15"]
        }
        patch_data = CourierPatchDataModel(**data)
        self.assertEqual(patch_data.regions, None)
