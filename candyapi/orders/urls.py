from django.urls import path

from .views import OrdersView, AssignView

urlpatterns = [
    path("", OrdersView.as_view()),
    path("assign", AssignView.as_view())
]