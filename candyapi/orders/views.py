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
                         InvalidOrdersInData,
                         AssignDataModel,
                         CompletionDataModel)
from .models import Order
from .logic import (assign,
                    complete_order,
                    CompleteTimeError)

from couriers.utils import parse_errors


class OrdersView(View):
    """Орабатывает запрос к /orders"""

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        """
        Sets csrf decorator on all methods
        """
        return super(OrdersView, self).dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest) -> HttpResponse:
        """Обрабатывает запрос на дообавление заказов"""
        try:
            data = json.loads(request.body.decode())
            orders_list = OrderListDataModel(**data)
            orders = Order.objects.create_from_list(orders_list.data)
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
        except InvalidOrdersInData as e:
            error_data = [
                {**errors} for errors in e.invaid_orders
            ]
            return ValidationErrorsResponse(errors={
                "order": error_data
            })
        except ValidationError as e:
            errors = parse_errors(e)
            return ValidationErrorsResponse(errors={
                "data": {
                    **errors
                }
            })
        except IntegrityError:
            return DatabaseErrorResponse("attempt to add existing order")
        except JSONDecodeError:
            return InvalidJsonResponse()


class AssignView(View):
    """Обрабатывает запрос на /orders/assign"""

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(AssignView, self).dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Обрабатывает запрос на назнаяение заказов курьеру
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
        except ValidationError as e:
            errors = parse_errors(e)
            return ValidationErrorsResponse({
                **errors
            })
        except ObjectDoesNotExist:
            return DatabaseErrorResponse(
                "courier with courier_id={} does not exist".format(courier_id)
            )
        except JSONDecodeError:
            return InvalidJsonResponse()


class CompletionView(View):
    """Обрабатывает запросы на /orders/complete"""

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(CompletionView, self).dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Обрабатывает запрос на завершение заказа
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
        except ValidationError as e:
            errors = parse_errors(e)
            return ValidationErrorsResponse({
                **errors
            })
        except ObjectDoesNotExist:
            return DatabaseErrorResponse(
                "courier or order does not exist, order was never assigned, or already completed"
            )
        except CompleteTimeError:
            return DatabaseErrorResponse(
                "comple_time can not be earlier than previos order complete_time (or assigned_time)"
            )
        except JSONDecodeError:
            return InvalidJsonResponse()
