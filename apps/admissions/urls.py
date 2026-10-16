from django.urls import path

from . import views

app_name = "admissions"

urlpatterns = [
    path("", views.enquiry, name="enquiry"),
    path("thank-you/", views.thanks, name="thanks"),
]
