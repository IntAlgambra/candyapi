from django.http import JsonResponse


class InvalidJsonResponse(JsonResponse):
    """
    Ответ, возвращаемый в случае, если в запросе был невалидный json
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
    Возвращается в случае, если во входных данных были
    некорректные значения
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
    Возвращается при ошибке в БД или логике программы, например:
    - Попытка добавить существующиего курьера или существующий заказ
    - Получить информаци о несуществующем курьере
    - Завершить несуществующий, не назначенный или завершенный заказ
    - Завершить заказ ранее, чем был завершен предыдущий.
    и т. д. Конкретное описание ошибки в поле database_error
    """

    def __init__(self, error: str):
        super(DatabaseErrorResponse, self).__init__(
            status=400,
            data={
                "database_error": error
            }
        )
