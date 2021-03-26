import json
from json import JSONDecodeError

from pydantic import ValidationError

from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http.request import HttpRequest
from django.http.response import (HttpResponse,
                                  HttpResponseBadRequest,
                                  JsonResponse)

from .validators import (CouriersListDataModel,
                         CourierDataModel,
                         InvalidCouriersInDataError,
                         CourierPatchDataModel)
from .logic import create_couriers_from_list
from .models import Courier
from candyapi.responses import (InvalidJsonResponse,
                                ValidationErrorsResponse,
                                DatabaseErrorResponse)
from .utils import parse_errors


class CouriersView(View):
    """
    Обрабатывает запросы к /couriers
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        """
        Устанавливает игнорирование csrf защиты (в нашем случае не нужна)
        """
        return super(CouriersView, self).dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Обрабатывает запрос на добавление курьеров
        """
        try:
            data = json.loads(request.body.decode())
            couriers = CouriersListDataModel(**data)
            added_couriers = create_couriers_from_list(couriers)
            return JsonResponse(
                status=201,
                data={"couriers": [
                    {
                        "id": courier_id
                    } for courier_id in added_couriers
                ]}
            )
        except JSONDecodeError:
            return InvalidJsonResponse()
        except ValidationError as e:
            errors = parse_errors(e)
            return ValidationErrorsResponse(errors={
                "data": {
                    **errors
                }
            })
        except InvalidCouriersInDataError as e:
            error_data = [
                {**errors} for errors in e.invalid_couriers
            ]
            return ValidationErrorsResponse(errors={
                "couriers": error_data
            })
        except IntegrityError:
            return DatabaseErrorResponse("atempt to add existing courier")


class CourierView(View):
    """
    Обрабатывает запросы к /couriers/{courier_id}
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        """
        Method sets csrf_exempt decorator for other methods
        """
        return super(CourierView, self).dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, courier_id: int) -> HttpResponse:
        """
        Обрабатывает запрос на получение информации о курьере. Если в
        courier_id будет передан не int, вернет 404
        """
        try:
            courier = Courier.objects.get(courier_id=courier_id)
            return JsonResponse(courier.info())
        except ObjectDoesNotExist:
            return DatabaseErrorResponse(
                "courier with courier_id={} does not exist".format(
                    courier_id
                )
            )

    def patch(self, request: HttpRequest, courier_id: int) -> HttpResponse:
        """
        Обрабатывает запрос на обновление курьера
        """
        try:
            courier = Courier.objects.get(courier_id=courier_id)
            data = CourierPatchDataModel(**json.loads(request.body.decode()))
            data = courier.update(data)
            return JsonResponse(data)
        except ValidationError as e:
            errors = parse_errors(e)
            return ValidationErrorsResponse({
                **errors
            })
        except JSONDecodeError:
            return InvalidJsonResponse()
        except ObjectDoesNotExist:
            return DatabaseErrorResponse(
                "courier with courier_id={} does not exist".format(
                    courier_id
                )
            )
