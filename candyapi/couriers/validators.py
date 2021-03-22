from typing import List, Dict, Optional
import re

from pydantic import (BaseModel,
                      validator,
                      root_validator,
                      ValidationError,
                      PydanticValueError,
                      PydanticTypeError)


def validate_time_intervals(intervals: List[str], error_msg: str) -> List[str]:
    pattern = r"[012][0-9]:[0-5][0-9]\-[012][0-9]:[0-5][0-9]"
    for period in intervals:
        if not re.fullmatch(pattern=pattern, string=period):
            raise ValueError(error_msg)
        start, end = period.split("-")
        start_minutes = int(start.split(":")[0]) * 60 + int(start.split(":")[0])
        end_minutes = int(end.split(":")[0]) * 60 + int(end.split(":")[0])
        if end_minutes < start_minutes:
            raise ValueError("interval should not end earlier than starts")
    return intervals


def validate_courier_type(v: str) -> str:
    if v not in ["foot", "car", "bike"]:
        raise ValueError(
            "courier_type must be car, bike or foot"
        )
    return v


def validate_regions(regions: List[int]) -> List[int]:
    """
    Checks regions id's in list in allowed range
    """
    for region in regions:
        if region > 2147483647 or region < 0:
            raise ValueError("region id out of allowed range")
    return regions


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


class NoFieldsInPatchDataError(PydanticValueError):
    """
    Class describes error when no fields was provided in patch data
    """
    code = "no_fields_in_patch_data"
    msg_template = "No fields provided to patch data model"


class CouriersValidationError(PydanticTypeError):
    """
    Class describes error in validating couriers data
    """
    code = "error_in_couriers_data"
    msg_template = "error in couriers data"


class CourierDataModel(BaseModel):
    """
    Describes courier data model, which will be used to validate
    input json data
    """

    courier_id: int
    courier_type: str
    regions: List[int]
    working_hours: List[str]

    def __init__(self, **data):
        super(CourierDataModel, self).__init__(**data)
        if type(data.get("courier_id")) != int:
            raise InvalidCourierData()
        for region in data.get("regions"):
            if type(region) != int:
                raise InvalidCourierData()

    @validator("courier_id")
    def validate_courier_id(cls, v: int) -> int:
        """
        Checks tht courier_id is positive and not exceeds postgres bigserial
        """
        if v > 9223372036854775807 or v < 0:
            raise ValueError("courier_id out of allowed range")
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
            error_msg="working hours interval must be in format hh:mm-hh:mm"
        )

    @root_validator(pre=True)
    def validate_no_excess_fields(cls, values: Dict) -> Dict:
        """
        Checks if courier data has some excess fields
        """
        if set(values.keys()) != {
            "courier_id",
            "courier_type",
            "working_hours",
            "regions"
        }:
            raise ValueError(
                "No extra fields allowed"
            )
        return values


class CourierPatchDataModel(BaseModel):
    """
    Describes data model for patch courier data
    """
    courier_type: Optional[str] = None
    regions: Optional[List[int]] = None
    working_hours: Optional[List[str]] = None

    def __init__(self, **data):
        """
        Checks if at least one field is provided
        If new regions field is provided, checks if all region are
        integers
        """
        super(CourierPatchDataModel, self).__init__(**data)
        if not data:
            raise NoFieldsInPatchDataError()
        if data.get("regions"):
            for region in data.get("regions"):
                if type(region) != int:
                    raise InvalidCourierData()

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
            error_msg="working hours interval must be in format hh:mm-hh:mm"
        )

    @root_validator(pre=True)
    def validate_no_excess_fields(cls, values: Dict) -> Dict:
        """
        validates no extra fields provided
        """
        if not set(values.keys()).issubset({
            "courier_type",
            "working_hours",
            "regions"
        }):
            raise ValueError("No extra fields allowed")
        return values


class CouriersListDataModel(BaseModel):
    """
    Describes list of couriers data (basically, describes input data from api user
    on endpoint POST /couriers)
    """
    data: List[CourierDataModel]

    def __init__(self, **kwargs):
        """
        Because pydantic is not validation library, but we still has some
        fields requires strong types, we need to validate those fields
        in overloaded __init__ method
        """
        if "data" not in kwargs.keys():
            raise CouriersValidationError()
        errors = []
        for courier in kwargs.get("data"):
            try:
                CourierDataModel(**courier)
            except InvalidCourierData:
                courier_id = courier.get("courier_id")
                if courier_id:
                    errors.append(courier_id)
            except ValidationError:
                errors.append(courier.get("courier_id"))
        if errors:
            raise InvalidCouriersInDataError(invalid_couriers=errors)
        super(CouriersListDataModel, self).__init__(**kwargs)

    @root_validator(pre=True)
    def validate_no_excess_fields(cls, values: Dict) -> Dict:
        if set(values.keys()) != {"data"}:
            raise ValueError("No excess fields allowed")
        return values
