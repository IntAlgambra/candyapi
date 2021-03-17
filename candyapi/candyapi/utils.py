from datetime import datetime


class WrongTimezoneError(Exception):
    """
    Raised when datetime is ot timezone aware, although needed to be.
    """
    def __init__(self):
        super(WrongTimezoneError, self).__init__("Dtetime is not timezone aware")


def format_time(t: datetime) -> str:
    """
    Fuction formats datetime to format "YYYY-MM-DDTHH:MM:SS.ssZ"
    (like in the assigment). Should always return datetime string in utc time,
    so raises exception if t is not in utc timezone
    """
    if t.tzname() != "UTC":
        raise WrongTimezoneError()
    return "{}{}".format(t.isoformat()[:-10], "Z")
