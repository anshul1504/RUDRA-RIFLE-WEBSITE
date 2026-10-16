from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("", views.slot_list, name="slots"),
    path("slot/<int:pk>/", views.book_slot, name="book"),
    path("confirmation/<str:reference>/", views.confirmation, name="confirmation"),
]
