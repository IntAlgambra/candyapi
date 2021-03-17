from __future__ import annotations
from typing import TYPE_CHECKING, List
from functools import reduce

if TYPE_CHECKING:
    from couriers.models import Interval

from django.db.models import Q


def construct_assign_query(intervals: List[Interval]) -> List:
    """
    Creates filter condition
    """
    interval_filters = []
    for interval in intervals:
        cond = Q(intervals__start__lte=interval.end) & Q(intervals__end__gte=interval.start)
        interval_filters.append(cond)
    condition = reduce(lambda acc, c: acc | c, interval_filters)
    return condition
