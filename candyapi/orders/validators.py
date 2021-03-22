from typing import List, Dict, Optional
import re

from pydantic import (BaseModel,
                      PydanticTypeError,
                      PydanticValueError,
                      validator,
                      root_validator,
                      ValidationError)

from couriers.validators import validate_time_intervals


class OrderTypeError(PydanticTypeError):
    code = "order_type_error"
    msg_template = "Type error in order data"


class OrdersValidationError(PydanticTypeError):
    code = "errors_in_orders_data"
    msg_template = "errors in orders data"

    def __init__(self, invalid_orders: Optional[List[int]] = None):
        super(OrdersValidationError, self).__init__()
        self.invaid_orders = invalid_orders


class AssignValidationError(PydanticTypeError):
    code = "error_in_assign_data"
    msg_template = "errors in assign data"


class CompletionValidationError(PydanticTypeError):
    code = "eror_in_completion_data"
    msg_template = "errors in completion data"


class OrderDataModel(BaseModel):
    order_id: int
    weight: float
    region: int
    delivery_hours: List[str]

    def __init__(self, **data):
        super(OrderDataModel, self).__init__(**data)
        if type(data.get("order_id")) != int:
            raise OrderTypeError()
        if not (type(data.get("weight")) == int or type(data.get("weight")) == float):
            raise OrderTypeError()
        if type(data.get("region")) != int:
            raise OrderTypeError()

    @validator("order_id")
    def validate_order_id(cls, v: int) -> int:
        """
        Checks if order_id is in allowed range
        """
        if v < 0 or v > 9223372036854775807:
            raise ValueError("order_id out of allowed range")
        return v

    @validator("weight")
    def validate_weight(cls, v):
        if v > 50 or v < 0.01:
            raise ValueError("weight not in limit")
        return v

    @validator("delivery_hours")
    def validate_delivery_hours(cls, v):
        return validate_time_intervals(
            intervals=v,
            error_msg="delivery hours interval string must be in format hh:mm-hh:mm"
        )

    @root_validator(pre=True)
    def validate_no_excess_fields(cls, values: Dict) -> Dict:
        if set(values.keys()) != {"order_id", "weight", "region", "delivery_hours"}:
            raise ValueError("Invalid schema")
        return values


class OrderListDataModel(BaseModel):
    data: List[OrderDataModel]

    def __init__(self, **kwargs):
        if set(kwargs.keys()) != {"data"}:
            raise OrdersValidationError()
        errors = []
        for order_data in kwargs.get("data"):
            try:
                OrderDataModel(**order_data)
            except ValidationError:
                errors.append(order_data.get("order_id"))
            except OrderTypeError:
                errors.append(order_data.get("order_id"))
        if errors:
            raise OrdersValidationError(invalid_orders=errors)
        super(OrderListDataModel, self).__init__(**kwargs)

    @root_validator(pre=True)
    def validate_no_excess_fields(cls, values: Dict) -> Dict:
        if set(values.keys()) != {"data"}:
            raise ValueError("Invalid schema")
        return values


class AssignDataModel(BaseModel):
    """
    Describes data, required to assign orders to courier
    """

    courier_id: int

    def __init__(self, **data):
        if set(data.keys()) != {"courier_id"}:
            raise AssignValidationError()
        if type(data.get("courier_id")) != int:
            raise AssignValidationError()
        super(AssignDataModel, self).__init__(**data)

    @validator("courier_id")
    def validate_courier_id(cls, v: int) -> int:
        if v < 0:
            raise AssignValidationError()
        return v


class CompletionDataModel(BaseModel):
    """
    Describes data, required to complete order
    """
    courier_id: int
    order_id: int
    complete_time: str

    def __init__(self, **data):
        if set(data.keys()) != {"courier_id", "order_id", "complete_time"}:
            raise CompletionValidationError()
        if (type(data.get("courier_id")) != int
                or type(data.get("order_id")) != int):
            raise CompletionValidationError()
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
        """
        pattern = r"\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{1,6}Z"
        if not re.fullmatch(pattern, v):
            raise ValueError("Invalid complete_time string")
        return v


