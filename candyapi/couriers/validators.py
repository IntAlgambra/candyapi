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
    Исключение, которое возбуждается, если в списке курьеров
    присутствуют элементы с некорректными данными.
    В поле invalid_coriers устанавливается словарь с описанием
    некорректных полей и значений ошибок для каждого невалидного объекта
    в списке курьеров
    """
    code = "invalid_couriers_in_data"
    msg_template = "found invalid couriers in data"

    def __init__(self, invalid_couriers):
        super(InvalidCouriersInDataError, self).__init__()
        self.invalid_couriers = invalid_couriers


class InvalidCourierData(PydanticTypeError):
    """
    Исключение возбуждается при провале валидации поля
    в данных  курьера
    """
    code = "invalid_data_type_in_courier_data"
    msg_template = "Invalid data type in courier data"


class DataFieldsError(PydanticTypeError):
    """
    Возбуждается, если в в структуре данных есть лишние поля
    """
    code = "extra_or_missing_fields"
    msg_template = "there are extra or missing fields in data"


class InvalidIntervalError(PydanticValueError):
    """
    Возбуждается если временной интервал некорректен или
    в неверном формате
    """
    code = "wrong_interval_format"
    msg_template = "wrong interval format"


def validate_courier_type(v: str) -> str:
    """
    Валидирует тип курьера
    """
    if v not in ["foot", "car", "bike"]:
        raise InvalidCourierData(courier_type="must be car, foot or bike")
    return v


def validate_regions(regions: List[int]) -> List[int]:
    """
    Валидирует список регионов. Проверяет тип, наличие дубликатов
    и находится ли регион в допустимом диапазоне
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
    """
    Валидирует список временных интервалов.
    Проверяет как формат интервала, так и чтобы интервал не начинался позднее,
    чем заканчивается
    """
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
    Описывает список полей в данных курьера
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
        Проверяет, что courier_id присутствует, является типом int
        и не выходит из допустимого диапазона
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
        Валидирует тип курьера
        """
        return validate_courier_type(v)

    @validator("regions")
    def validate_regions(cls, v: List[int]) -> List[int]:
        """
        Валидирует список регионов
        """
        return validate_regions(v)

    @validator("working_hours")
    def validate_woring_hours(cls, v: List[str]) -> List[str]:
        """
        Валидирует список интервалов работы
        """
        return validate_time_intervals(
            intervals=v,
        )

    @root_validator(pre=True, skip_on_failure=False)
    def validate_fields(cls, values: Dict) -> Dict:
        """
        Валидирует отсутствие лишних полей
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
    Описывает поля при обновлении данных курьера
    """
    courier_type: Optional[str] = None
    regions: Optional[List[Any]] = None
    working_hours: Optional[List[str]] = None

    @validator("courier_type")
    def validate_type(cls, v: str) -> str:
        """
        Валидирует тип курьера
        """
        return validate_courier_type(v)

    @validator("regions")
    def validate_regions(cls, v: List[int]) -> List[int]:
        """
        Валиирует список регионов
        """
        return validate_regions(v)

    @validator("working_hours")
    def validate_working_hours(cls, v: List[str]) -> List[str]:
        """
        Валиддирует список интервалов работы
        """
        return validate_time_intervals(
            intervals=v,
        )

    @root_validator(pre=True)
    def validate_fields(cls, values: Dict) -> Dict:
        """
        Валидирует отсутствие лишних полей
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
    Описывает список курьеров. При инициализации проходится
    по всем курьерам и при наличии ошибок, возбуждает исключение,
    в которое передает список этих ошибок
    """
    data: List[Dict]

    def __init__(self, **kwargs):
        """
        Валидирует всех курьеров. При ошибках вызывает
        InvalidCouriersInDataError в который передает список словарей
        описывающих ошибки в данных курьеров
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
        """
        Валидирует отсутствие лишних полей
        """
        excess_fields = set(values.keys()).difference({"data"})
        missed_fields = {"data"}.difference(set(values))
        if excess_fields or missed_fields:
            raise ValueError(
                "excess fields: {}".format(", ".join(excess_fields))
            )
        return values
