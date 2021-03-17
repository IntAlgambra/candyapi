# Needed only for type hints work correctly
from __future__ import annotations
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .models import Region, Interval

from django.db import models, transaction
from django.core.exceptions import ObjectDoesNotExist

from .validators import CourierDataModel, CouriersListDataModel


class CourierManager(models.Manager):

    def create_courier(self,
                       data: CourierDataModel,
                       regions: List[Region] = [],
                       intervals: List[Interval] = []) -> self.model.__class__:
        """
        Creates new courier in database and returns orm representations
        """
        courier = self.create(
            courier_id=data.courier_id,
            courier_type=data.courier_type,
        )
        courier.save()
        courier.regions.set(regions)
        courier.intervals.set(intervals)
        return courier


class RegionManager(models.Manager):

    def create_region(self, region_id: int) -> self.model.__class__:
        """
        Creates new region and returns it.
        """
        region = self.model(region_id=region_id)
        region.save()
        return region

    def create_or_find(self, region_id: int) -> self.model.__class__:
        """
        Creates region with region_id if there isn't one in the database and returns it.
        If there is, just returns it
        """
        try:
            return self.get(region_id=region_id)
        except ObjectDoesNotExist:
            return self.create_region(region_id=region_id)

    def create_from_list(self, regions: List[int]):
        """
        Creates non-existing regions from list and returns list of
        created and found regions
        """
        return list(
            map(
                self.create_or_find,
                regions
            )
        )


class IntervalManager(models.Manager):

    @staticmethod
    def interval_string_to_start_end(interval_string: str) -> (int, int):
        start, end = interval_string.split("-")
        start_hours, start_minutes = list(
            map(
                int,
                start.split(":")
            )
        )
        end_hours, end_minutes = list(
            map(
                int,
                end.split(":")
            )
        )
        start_seconds = start_hours * 60 * 60 + start_minutes * 60
        end_seconds = end_hours * 60 * 60 + end_minutes * 60
        return start_seconds, end_seconds

    def create_interval(self, interval_string: str) -> self.model.__class__:
        """
        Creates time interval.
        """

        start_seconds, end_seconds = self.interval_string_to_start_end(
            interval_string
        )
        interval = self.model(
            start=start_seconds,
            end=end_seconds
        )
        interval.save()
        return interval

    def create_or_find(self, interval_string) -> self.model.__class__:
        """
        Creates interval from start to end if there isn't one in database.
        If there is, just returns it
        """
        try:
            start_seconds, end_seconds = self.interval_string_to_start_end(
                interval_string
            )
            return self.get(start=start_seconds, end=end_seconds)
        except ObjectDoesNotExist:
            interval = self.create_interval(interval_string)
            return interval

    def create_from_list(self, intervals: List[str]):
        return list(
            map(
                self.create_or_find,
                intervals
            )
        )
