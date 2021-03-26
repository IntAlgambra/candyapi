from typing import Dict

from pydantic import ValidationError


def parse_errors(error: ValidationError) -> Dict:
    """
    Парсит список ошибок из ValidationError в
     формат "field": "error_msg", который возвращается клиенту
    """
    errors = {}
    for e in error.errors():
        if e.get("ctx"):
            context = e.get("ctx")
            errors = {
                **errors,
                **context
            }
        else:
            errors = {
                **errors,
                e.get("loc")[0]: e.get("msg")
            }
    return errors


