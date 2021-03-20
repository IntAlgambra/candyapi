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


class CouriersView(View):
    """
    Class describes views methods for processing requests
    to /couriers (only for all couriers)
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        """
        Method sets csrf_exempt decorator for other methods
        """
        return super(CouriersView, self).dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest) -> HttpResponse:
        return HttpResponse("ok")

    def post(self, request: HttpRequest) -> HttpResponse:
        """
        View process request for adding new couriers to database
        """
        try:
            data = json.loads(request.body.decode())
            couriers = CouriersListDataModel(**data)
            added_users = create_couriers_from_list(couriers)
            return JsonResponse(
                status=201,
                data={"couriers": [
                    {
                        "id": courier_id
                    } for courier_id in added_users
                ]}
            )
        except JSONDecodeError:
            return JsonResponse(
                status=400,
                data={
                    "validation_errors": {
                        "common": "request body is not valid json"
                    }
                }
            )
        except InvalidCouriersInDataError as e:
            error_data = [
                {"id": courier_id} for courier_id in e.invalid_couriers
            ]
            return HttpResponseBadRequest(
                content=json.dumps({
                    "validation_errors": {
                        "couriers": error_data
                    }
                }).encode()
            )
        except IntegrityError:
            return JsonResponse(
                status=400,
                data={
                    "database_error": "can not add couriers which already exist"
                }
            )


class CourierView(View):
    """
    Class describes views methods to process requests for single courier
    endpoint (for example /couriers/1
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        """
        Method sets csrf_exempt decorator for other methods
        """
        return super(CourierView, self).dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, courier_id: int) -> HttpResponse:
        """
        Process request for courier info and statistics
        """
        try:
            courier = Courier.objects.get(courier_id=courier_id)
            return JsonResponse(courier.info())
        except ObjectDoesNotExist:
            return JsonResponse(
                status=400,
                data={
                    "database_error": "Courier with courier_id={} does not exist".format(
                        courier_id
                    )
                }
            )

    def patch(self, request: HttpRequest, courier_id: int) -> HttpResponse:
        """
        View process request for modifying courier data
        """
        try:
            courier = Courier.objects.get(courier_id=courier_id)
            data = CourierPatchDataModel(**json.loads(request.body.decode()))
            data = courier.update(data)
            return JsonResponse(data)
        except JSONDecodeError:
            return JsonResponse(
                status=400,
                data={
                    "validation_errors": {
                        "common": "request body is not valid json"
                    }
                }
            )
        except ObjectDoesNotExist:
            return JsonResponse(
                status=400,
                data={
                    "database_error": "Courier with courier_id={} does not exist".format(
                        courier_id
                    )
                }
            )
