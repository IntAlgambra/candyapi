from django.http import JsonResponse


class InvalidJsonResponse(JsonResponse):
    """
    This response is returning if request body can not be
    decoded as vald json
    """

    def __init__(self):
        super(InvalidJsonResponse, self).__init__(
            status=400,
            data={
                "json_error": "request body is not valid json"
            }
        )


class ValidationErrorsResponse(JsonResponse):
    """
    This response is returned if request data has infalid fields
    or structure
    """

    def __init__(self, errors):
        super(ValidationErrorsResponse, self).__init__(
            status=400,
            data={
                "validation_errors": {
                    **errors
                }
            }
        )


class DatabaseErrorResponse(JsonResponse):
    """
    This response is returned if there was an database error proceeding
    request (for example, if there is an attempt to add existing courier,
    or complete order, that does not exist)
    """

    def __init__(self, error: str):
        super(DatabaseErrorResponse, self).__init__(
            status=400,
            data={
                "database_error": error
            }
        )
