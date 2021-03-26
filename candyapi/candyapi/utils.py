from datetime import datetime


class WrongTimezoneError(Exception):
    """
    Возвращается при попытке передать дату и время не в UTC или без временной зоны
    """
    def __init__(self):
        super(WrongTimezoneError, self).__init__("Datetime is not timezone aware")


def format_time(t: datetime) -> str:
    """
    Форматирует datetime объект к формату "YYYY-MM-DDTHH:MM:SS.ssZ"
    (как в assigment). Всегда принимает объект datetime с временной зоной UTC,
    если нет временной зоны, или время не в UTC возбуждается исключение
    """
    if t.tzname() != "UTC":
        raise WrongTimezoneError()
    return "{}{}".format(t.isoformat(timespec="microseconds")[:-10], "Z")
