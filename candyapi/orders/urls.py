from django.urls import path, include

from .views import OrdersView, AssignView, CompletionView

assignment_pattern = [
    path("assign", AssignView.as_view()),
    path("complete", CompletionView.as_view())
]

urlpatterns = [
    path("/", include(assignment_pattern)),
    path("", OrdersView.as_view())
]
