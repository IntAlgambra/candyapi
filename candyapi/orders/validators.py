from typing import List, Dict, Optional
import re

from pydantic import (BaseModel,
                      PydanticTypeError,
                      PydanticValueError,
                      validator,
                      root_validator,
                      ValidationError)

from couriers.validators import validate_time_intervals
from couriers.utils import parse_errors


class InvalidOrderData(PydanticTypeError):
    code = "order_type_error"
    msg_template = "Type error in order data"


class InvalidOrdersInData(PydanticTypeError):
    code = "errors_in_orders_data"
    msg_template = "errors in orders data"

    def __init__(self, invalid_orders: Optional[List[Dict]] = None):
        super(InvalidOrdersInData, self).__init__()
        self.invaid_orders = invalid_orders


class AssignExcessFieldError(PydanticTypeError):
    code = "excess_field_in_assign_data"
    msg_template = "excess field in assign data"


class CompletionValidationError(PydanticTypeError):
    code = "eror_in_completion_data"
    msg_template = "errors in completion data"


class OrderDataModel(BaseModel):
    order_id: int
    weight: float
    region: int
    delivery_hours: List[str]

    def __init__(self, **data):
        if type(data.get("order_id")) != int:
            data["order_id"] = '"{}"'.format(data.get("order_id"))
        if not (type(data.get("weight")) == int or type(data.get("weight")) == float):
            data["weight"] = '"{}"'.format(data.get("weight"))
        if type(data.get("region")) != int:
            data["region"] = '"{}"'.format(data.get("region"))
        super(OrderDataModel, self).__init__(**data)

    @validator("order_id")
    def validate_order_id(cls, v: int) -> int:
        """
        Checks if order_id is in allowed range
        """
        if v < 0 or v > 9223372036854775807:
            raise InvalidOrderData(order_id="order_id out of allowed range")
        return v

    @validator("weight")
    def validate_weight(cls, v):
        if v > 50 or v < 0.01:
            raise InvalidOrderData(weight="weight out of limit")
        return v

    @validator("delivery_hours")
    def validate_delivery_hours(cls, v):
        return validate_time_intervals(
            intervals=v,
        )

    @root_validator(pre=True)
    def validate_fields(cls, values: Dict) -> Dict:
        required_fields = {"order_id", "weight", "region", "delivery_hours"}
        excess_fields = set(values.keys()).difference(required_fields)
        missing_fields = set(required_fields).difference(excess_fields)
        if excess_fields:
            raise InvalidOrderData(
                excess="excess fields: {}".format(", ".join(excess_fields)),
                missing="excess fields: {}".format(", ".join(missing_fields))
            )
        return values


class OrderListDataModel(BaseModel):
    data: List[Dict]

    def __init__(self, **kwargs):
        super(OrderListDataModel, self).__init__(**kwargs)
        errors = []
        for order in self.data:
            try:
                OrderDataModel(**order)
            except ValidationError as e:
                errors.append(
                    {
                        "id": order.get("order_id", "no id provided"),
                        **parse_errors(e)
                    }
                )
        if errors:
            raise InvalidOrdersInData(invalid_orders=errors)

    @root_validator(pre=True)
    def validate_no_excess_fields(cls, values: Dict) -> Dict:
        excess_fields = set(values.keys()).difference({"data"})
        missed_fields = {"data"}.difference(set(values))
        if excess_fields or missed_fields:
            raise DataFieldsError(
                excess="excess fields: {}".format(", ".join(excess_fields)),
                reqired="missig required fields: {}".format(", ".join(missed_fields))
            )
        return values


class AssignDataModel(BaseModel):
    """
    Describes data, required to assign orders to courier
    """

    courier_id: int

    def __init__(self, **data):
        if type(data.get("courier_id")) != int and data.get("courier_id"):
            data["courier_id"] = '"{}"'.format(data.get("courier_id"))
        super(AssignDataModel, self).__init__(**data)

    @validator("courier_id")
    def validate_courier_id(cls, v: int) -> int:
        if v < 0 or v > 9223372036854775807:
            raise ValueError("courier_id out of allowed range")
        return v

    @root_validator(pre=True)
    def validate_excess_fields(cls, values: Dict) -> Dict:
        excess_fields = set(values.keys()).difference({"courier_id"})
        if excess_fields:
            raise AssignExcessFieldError(
                excess="excess fields: {}".format(", ".join(excess_fields))
            )
        return values


# noinspection PyMethodParameters
class CompletionDataModel(BaseModel):
    """
    Describes data, required to complete order
    """
    courier_id: int
    order_id: int
    complete_time: str

    def __init__(self, **data):
        if type(data.get("courier_id")) != int:
            data["courier_id"] = '"{}"'.format(data.get("courier_id"))
        if type(data.get("order_id")) != int:
            data["order_id"] = '"{}"'.format(data.get("order_id"))
        super(CompletionDataModel, self).__init__(**data)

    @validator("courier_id")
    def validate_courier_id(cls, v: int) -> int:
        if v < 0:
            raise CompletionValidationError()
        return v

    @validator("order_id")
    def validate_order_id(cls, v: int) -> int:
        if v < 0:
            raise CompletionValidationError()
        return v

    @validator("complete_time")
    def validate_time(cls, v: str) -> str:
        """
        Validates complete_time is valid isoformat datetime string
        with UTC time zone clearly specified
        """
        pattern = r"\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{1,6}Z"
        if not re.fullmatch(pattern, v):
            raise ValueError("Invalid complete_time string")
        return v

    @root_validator(pre=True)
    def validate_excess_fields(cls, values: Dict) -> Dict:
        required_fields = {"courier_id", "order_id", "complete_time"}
        excess_fields = set(values.keys()).difference(required_fields)
        if excess_fields:
            CompletionDataModel(
                excess="excess fields: {}".format(", ".join(excess_fields))
            )
        return values
