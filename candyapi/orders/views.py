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
from candyapi.responses import (InvalidJsonResponse,
                                DatabaseErrorResponse,
                                ValidationErrorsResponse)

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
                return ValidationErrorsResponse({
                    "orders": [
                        {
                            "id": error_id
                        } for error_id in e.invaid_orders
                    ]
                })
            else:
                return ValidationErrorsResponse({
                    "schema": "invalid fields"
                })
        except IntegrityError:
            return DatabaseErrorResponse("attempt to add existing order")
        except JSONDecodeError:
            return InvalidJsonResponse()


class AssignView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(AssignView, self).dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Process assigning orders to courier
        """
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
            return ValidationErrorsResponse({
                "schema": "invalid data in request"
            })
        except ObjectDoesNotExist:
            return DatabaseErrorResponse(
                "courier with courier_id={} does not exist".format(courier_id)
            )
        except AttributeError:
            return ValidationErrorsResponse({
                "courier_id": "no courier_id in request"
            })
        except JSONDecodeError:
            return InvalidJsonResponse()


class CompletionView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(CompletionView, self).dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest) -> HttpResponse:
        """
        method process adding new orders to database
        """
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
            return ValidationErrorsResponse({
                "complete_time": "complete_time is earlier than complete_time for previous order"
            })
        except ObjectDoesNotExist:
            return DatabaseErrorResponse(
                "courier or order does not exist, order was never assigned, or already completed"
            )
        except CompletionValidationError:
            return ValidationErrorsResponse({
                "schema": "invalid data"
            })
        except JSONDecodeError:
            return InvalidJsonResponse()
