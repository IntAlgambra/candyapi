from typing import List, Dict, Optional, Any
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
    """
    Возбуждается, если в полях данных заказа
    были переданы некорректные данные
    """
    code = "order_type_error"
    msg_template = "Type error in order data"


class InvalidOrdersInData(PydanticTypeError):
    """
    Возбуждается, если в списке заказов есть некорректные.
    В поле invalid_orders содержится список объектов
    с описание ошибок в полях заказов
    """
    code = "errors_in_orders_data"
    msg_template = "errors in orders data"

    def __init__(self, invalid_orders: Optional[List[Dict]] = None):
        super(InvalidOrdersInData, self).__init__()
        self.invaid_orders = invalid_orders


class AssignExcessFieldError(PydanticTypeError):
    """
    Возбуждается при наличии лишних полей в данных
    переданных для назначения заказов
    """
    code = "excess_field_in_assign_data"
    msg_template = "excess field in assign data"


class CompletionExcessFieldsError(PydanticTypeError):
    """
    Возбужается при наличии лишних полей в данных
    завершения заказа
    """
    code = "excess_fields_in_completion_data"
    msg_template = "excess fields in completion data"


# noinspection PyMethodParameters
class OrderDataModel(BaseModel):
    """
    Структура данных, описывающая заказ
    """
    order_id: Any
    weight: Any
    region: Any
    delivery_hours: List[str]

    @validator("order_id", always=True)
    def validate_order_id(cls, v: int) -> int:
        """
        Валидирует order_id заказа
        """
        if not v:
            raise InvalidOrderData(order_id="order_id is required")
        if type(v) != int:
            raise InvalidOrderData(order_id="order_id must be integer")
        if v < 0 or v > 9223372036854775807:
            raise InvalidOrderData(order_id="order_id out of allowed range")
        return v

    @validator("region", always=True)
    def validate_region(cls, v):
        """Валидирует регион заказа"""
        if not v:
            raise InvalidOrderData(region="region is required")
        if type(v) != int:
            raise InvalidOrderData(region="region must be integer")
        if v > 2147483647 or v < 0:
            raise InvalidOrderData(region="region out of range")
        return v

    @validator("weight", always=True)
    def validate_weight(cls, v):
        """Валидирует вес заказа"""
        if not v:
            raise InvalidOrderData(weight="weight is required")
        if type(v) != int and type(v) != float:
            raise InvalidOrderData(weight="weight must be integer or float")
        if v > 50 or v < 0.01:
            raise InvalidOrderData(weight="weight out of limit")
        return v

    @validator("delivery_hours")
    def validate_delivery_hours(cls, v):
        """
        Валидирует список интервалов доставки
        """
        if not v:
            raise InvalidOrderData(delievery_hours="at least one interval required")
        return validate_time_intervals(
            intervals=v,
        )

    @root_validator(pre=True)
    def validate_fields(cls, values: Dict) -> Dict:
        """
        Валидирует отсутствие лишних полей
        """
        required_fields = {"order_id", "weight", "region", "delivery_hours"}
        excess_fields = set(values.keys()).difference(required_fields)
        if excess_fields:
            raise InvalidOrderData(
                excess="excess fields: {}".format(", ".join(excess_fields)),
            )
        return values


# noinspection PyMethodParameters
class OrderListDataModel(BaseModel):
    """
    Описывает список заказов. При инициализации валидирует
    все переданные заказы и, если среди них есть невалидные,
    возбуждает исключение, в которое передает информацию
    о невалидных полях в заказах
    """
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
        """
        Валидирует отсутствие лишних полей в заказах
        """
        excess_fields = set(values.keys()).difference({"data"})
        if excess_fields:
            raise ValueError(
                "excess fields: {}".format(", ".join(excess_fields)),
            )
        return values


# noinspection PyMethodParameters
class AssignDataModel(BaseModel):
    """
    Описывает стрктуру данных для назначения заказов
    """

    courier_id: Any

    @validator("courier_id", always=True)
    def validate_courier_id(cls, v: int) -> int:
        """Валидирует courier_id"""
        if not v:
            raise ValueError("courier_id is required")
        if type(v) != int:
            raise ValueError("courier_id must be integer")
        if v < 0 or v > 9223372036854775807:
            raise ValueError("courier_id out of allowed range")
        return v

    @root_validator(pre=True)
    def validate_excess_fields(cls, values: Dict) -> Dict:
        """Валидирует отсутствие лишних полей"""
        excess_fields = set(values.keys()).difference({"courier_id"})
        if excess_fields:
            raise AssignExcessFieldError(
                excess="excess fields: {}".format(", ".join(excess_fields))
            )
        return values


# noinspection PyMethodParameters
class CompletionDataModel(BaseModel):
    """
    Описывает структуру данных для завершения заказа
    """
    courier_id: Any
    order_id: Any
    complete_time: str

    @validator("courier_id", always=True)
    def validate_courier_id(cls, v: int) -> int:
        """Валидирует courier_id"""
        if not v:
            raise ValueError("courier_id is required")
        if type(v) != int:
            raise TypeError("courier_id must be integer")
        if v > 9223372036854775807 or v < 0:
            raise ValueError("courier_id out of allowed range")
        return v

    @validator("order_id", always=True)
    def validate_order_id(cls, v: int) -> int:
        """Валидирует order_id"""
        if not v:
            raise ValueError("order_id is required")
        if type(v) != int:
            raise TypeError("order_id must be integer")
        if v > 9223372036854775807 or v < 0:
            raise ValueError("order_id out of allowed range")
        return v

    @validator("complete_time")
    def validate_time(cls, v: str) -> str:
        """
        Валидирует время окончания заказа (Должно быть строго в UTC)
        """
        pattern = r"\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{1,6}Z"
        if not re.fullmatch(pattern, v):
            raise ValueError("Invalid complete_time string")
        return v

    @root_validator(pre=True)
    def validate_excess_fields(cls, values: Dict) -> Dict:
        """
        Валидирует отсутствие лишних полей
        """
        required_fields = {"courier_id", "order_id", "complete_time"}
        excess_fields = set(values.keys()).difference(required_fields)
        if excess_fields:
            raise ValueError(
                "excess fields: {}".format(", ".join(excess_fields))
            )
        return values
