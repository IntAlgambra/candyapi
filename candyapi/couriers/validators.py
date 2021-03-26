from typing import List, Dict, Optional, Any
import re

from pydantic import (BaseModel,
                      validator,
                      root_validator,
                      ValidationError,
                      PydanticValueError,
                      PydanticTypeError)

from .utils import parse_errors


class InvalidCouriersInDataError(PydanticValueError):
    """
    Class describes error when some couriers in data are invalid.
    This exception has field "invalid_couriers" with list of id,
    which did not pass validation
    """
    code = "invalid_couriers_in_data"
    msg_template = "found invalid couriers in data"

    def __init__(self, invalid_couriers):
        super(InvalidCouriersInDataError, self).__init__()
        self.invalid_couriers = invalid_couriers


class InvalidCourierData(PydanticTypeError):
    """
    class describesr error in courier data types
    """
    code = "invalid_data_type_in_courier_data"
    msg_template = "Invalid data type in courier data"


class DataFieldsError(PydanticTypeError):
    """
    Describes exception, raised when there is excess
    fields in data structure
    """
    code = "extra_or_missing_fields"
    msg_template = "there are extra or missing fields in data"


class InvalidIntervalError(PydanticValueError):
    """
    Describes exception, which is raised when
    interval is in wrong format
    """
    code = "wrong_interval_format"
    msg_template = "wrong interval format"


def validate_courier_type(v: str) -> str:
    if v not in ["foot", "car", "bike"]:
        raise InvalidCourierData(courier_type="must be car, foot or bike")
    return v


def validate_regions(regions: List[int]) -> List[int]:
    """
    Checks regions id's in list in allowed range
    """
    for region in regions:
        if type(region) != int:
            raise InvalidCourierData(regions="region must be integer")
        if region > 2147483647 or region < 0:
            raise InvalidCourierData(regions="region is out of range")
    if len(set(regions)) < len(regions):
        raise InvalidCourierData(regions="no duplicates allowed")
    return regions


def validate_time_intervals(intervals: List[str]) -> List[str]:
    pattern = r"[012][0-9]:[0-5][0-9]\-[012][0-9]:[0-5][0-9]"
    for period in intervals:
        if not re.fullmatch(pattern=pattern, string=period):
            raise InvalidIntervalError(interval="wrong interval format")
        start, end = period.split("-")
        start_minutes = int(start.split(":")[0]) * 60 + int(start.split(":")[0])
        end_minutes = int(end.split(":")[0]) * 60 + int(end.split(":")[0])
        if end_minutes < start_minutes:
            raise InvalidIntervalError(interval="interval starts later than ends")
    return intervals


# noinspection PyMethodParameters
class CourierDataModel(BaseModel):
    """
    Describes courier data model, which will be used to validate
    input json data.
    """

    # For courier_id and regions type is checked manually in validators
    # so we declare them as Any to prevent pydantic to automatically
    # convert in with int() function
    courier_id: Any
    courier_type: str
    regions: List[Any]
    working_hours: List[str]

    @validator("courier_id", always=True)
    def validate_courier_id(cls, v: int) -> int:
        """
        Checks tht courier_id is positive and not exceeds postgres bigserial
        """
        if not v:
            raise InvalidCourierData(courier_id="courier_id is required")
        if type(v) != int:
            raise InvalidCourierData(courier_id="courier_id must be integer")
        if v > 9223372036854775807 or v < 0:
            raise InvalidCourierData(courier_id="courier_id out of allowed range")
        return v

    @validator("courier_type")
    def validate_type(cls, v: str) -> str:
        """
        Checks if courier type is car, bike or foot and nothing else
        """
        return validate_courier_type(v)

    @validator("regions")
    def validate_regions(cls, v: List[int]) -> List[int]:
        """
        Checks if region id is not in allowed range
        """
        return validate_regions(v)

    @validator("working_hours")
    def validate_woring_hours(cls, v: List[str]) -> List[str]:
        """
        Checks if working hours field contains only valid strings
        """
        return validate_time_intervals(
            intervals=v,
        )

    @root_validator(pre=True, skip_on_failure=False)
    def validate_fields(cls, values: Dict) -> Dict:
        """
        Checks if courier data has some excess fields
        """
        excess_fields = set(values.keys()).difference({
            "courier_id",
            "courier_type",
            "working_hours",
            "regions"
        })
        if excess_fields:
            raise InvalidCourierData(excess="excess fields: {}".format(
                " ".join(excess_fields)
            ))
        return values


# noinspection PyMethodParameters
class CourierPatchDataModel(BaseModel):
    """
    Describes data model for patch courier data
    """
    courier_type: Optional[str] = None
    regions: Optional[List[Any]] = None
    working_hours: Optional[List[str]] = None

    @validator("courier_type")
    def validate_type(cls, v: str) -> str:
        """
        Validates courier type
        """
        return validate_courier_type(v)

    @validator("regions")
    def validate_regions(cls, v: List[int]) -> List[int]:
        """
        Checks if region id's are in allowed range
        """
        return validate_regions(v)

    @validator("working_hours")
    def validate_working_hours(cls, v: List[str]) -> List[str]:
        """
        Validates working hours
        """
        return validate_time_intervals(
            intervals=v,
        )

    @root_validator(pre=True)
    def validate_fields(cls, values: Dict) -> Dict:
        """
        validates no extra fields provided
        """
        possible_fields = {
            "courier_type",
            "working_hours",
            "regions"
        }
        excess_fields = set(values.keys()).difference(possible_fields)
        if excess_fields:
            raise DataFieldsError(
                excess="excess fields: {}".format(", ".join(excess_fields)),
            )
        if not possible_fields.intersection(set(values.keys())):
            raise DataFieldsError(
                required="courier_type, working_hours or regions required"
            )
        return values


# noinspection PyMethodParameters
class CouriersListDataModel(BaseModel):
    """
    Describes list of couriers data (basically, describes input data from api user
    on endpoint POST /couriers)
    """
    data: List[Dict]

    def __init__(self, **kwargs):
        """
        validates all couriers, if there are problems
        raise InvalidCouriersInData exception
        """
        super(CouriersListDataModel, self).__init__(**kwargs)
        errors = []
        for courier in self.data:
            try:
                CourierDataModel(**courier)
            except ValidationError as e:
                errors.append(
                    {
                        "id": courier.get("courier_id", "no id provided"),
                        **parse_errors(e)
                    }
                )
        if errors:
            raise InvalidCouriersInDataError(invalid_couriers=errors)

    @root_validator(pre=True)
    def validate_no_excess_fields(cls, values: Dict) -> Dict:
        excess_fields = set(values.keys()).difference({"data"})
        missed_fields = {"data"}.difference(set(values))
        if excess_fields or missed_fields:
            raise ValueError(
                "excess fields: {}".format(", ".join(excess_fields))
            )
        return values
