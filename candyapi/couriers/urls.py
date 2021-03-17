from django.urls import path, include

from . import views

courier_pattern = [
    path('<int:courier_id>', views.CourierView.as_view()),
]

urlpatterns = [
    path('/', include(courier_pattern)),
    path("", views.CouriersView.as_view()),
]


