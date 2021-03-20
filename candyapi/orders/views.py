import json
from json import JSONDecodeError

from pydantic import ValidationError

from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import (JsonResponse,
                         HttpResponseBadRequest,
                         HttpRequest,
                         HttpResponse)
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from candyapi.utils import format_time

from .validators import (OrderDataModel,
                         OrderListDataModel,
                         OrdersValidationError,
                         AssignDataModel,
                         AssignValidationError,
                         CompletionDataModel,
                         CompletionValidationError)
from .models import Order
from .logic import (assign,
                    complete_order,
                    CompleteTimeError)


class OrdersView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        """
        Sets csrf decorator on all methods
        """
        return super(OrdersView, self).dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest) -> HttpResponse:
        try:
            data = json.loads(request.body.decode())
            orders_list = OrderListDataModel(**data)
            orders = Order.objects.create_from_list(orders_list)
            return JsonResponse(
                status=201,
                data={
                    "orders": [
                        {
                            "id": order.order_id
                        } for order in orders
                    ]
                }
            )
        except OrdersValidationError as e:
            if e.invaid_orders:
                return JsonResponse(
                    status=400,
                    data={
                        "validation_errors": {
                            "orders": [
                                {
                                    "id": error_id
                                } for error_id in e.invaid_orders
                            ]
                        }
                    }
                )
            else:
                return HttpResponseBadRequest("Invaid data in request")
        except IntegrityError:
            return HttpResponseBadRequest("attemt to create order which already exists")
        except JSONDecodeError:
            return HttpResponseBadRequest("Request body is not a valid json")


class AssignView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(AssignView, self).dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest) -> HttpResponse:
        try:
            data = json.loads(request.body.decode())
            courier_id = AssignDataModel(**data).courier_id
            delievery = assign(courier_id)
            if not delievery:
                return JsonResponse(
                    data={"orders": []}
                )
            delievery_data = {
                "orders": [
                    {
                        "id": order.order_id
                    } for order in delievery.orders.filter(delievered=False)
                ],
                "assign_time": format_time(delievery.assigned_time)
            }
            return JsonResponse(data=delievery_data)
        except AssignValidationError:
            return HttpResponseBadRequest("Invalid data in request")
        except AttributeError:
            return HttpResponseBadRequest("No ocourier_id in request")
        except JSONDecodeError:
            return HttpResponseBadRequest("Request body is not valid json")


class CompletionView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(CompletionView, self).dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest) -> HttpResponse:
        try:
            data = CompletionDataModel(
                **json.loads(request.body.decode())
            )
            order = complete_order(
                order_id=data.order_id,
                courier_id=data.courier_id,
                complete_time=data.complete_time
            )
            return JsonResponse(data={
                "order_id": order.order_id
            })
        except CompleteTimeError:
            return JsonResponse(
                data={
                    "error": "Order can not be completed earlier, than previos order"
                }
            )
        except ObjectDoesNotExist:
            return HttpResponseBadRequest(
                "Order does not exists, is not assigned or have been completed"
            )
        except CompletionValidationError:
            return HttpResponseBadRequest("Invalid data in request")
        except JSONDecodeError:
            return HttpResponseBadRequest("Request body is not valid json")
