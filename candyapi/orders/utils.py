from typing import List
from functools import reduce

from django.db.models import Q

from utils.models import Interval
from .models import Order


def construct_assign_query(intervals: List[Interval]) -> List:
    """
    Creates filter condition
    """
    interval_filters = []
    for interval in intervals:
        cond = Q(intervals__start__lt=interval.end) & Q(intervals__end__gt=interval.start)
        interval_filters.append(cond)
    condition = reduce(lambda acc, c: acc | c, interval_filters)
    return condition


def fill_weight(orders: List[Order], max_weight: float) -> List[Order]:
    """
    Uses greedy algorithm to select from list of suitable orders
    such orders, that courier would carry as much weight as he can.
    Orders list should be sorted by order weight
    """
    sum_weight = 0
    orders_to_assign = []
    for order in orders:
        if sum_weight + order.weight > max_weight:
            continue
        orders_to_assign.append(order)
        sum_weight += order.weight
    return orders_to_assign

