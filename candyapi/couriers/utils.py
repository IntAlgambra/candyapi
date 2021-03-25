from typing import Dict

from pydantic import ValidationError


def parse_errors(error: ValidationError) -> Dict:
    """
    Fucntion parses pydantic validation error to dictionary
    with format "field": "error_msg"
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


