from couriers.models import Courier
from utils.models import Region, Interval
from orders.models import Delievery, Order


def run():
    """
    Deletes all data from database
    """
    Courier.objects.all().delete()
    Order.objects.all().delete()
    Delievery.objects.all().delete()
    Region.objects.all().delete()
    Interval.objects.all().delete()
    print("DATABASE CLEANED WITHOUT ERRORS")
