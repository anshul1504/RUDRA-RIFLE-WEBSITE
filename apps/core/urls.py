from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("facilities/", views.FacilitiesView.as_view(), name="facilities"),
    path("privacy-policy/", views.legal_page, {"slug": "privacy-policy"}, name="privacy"),
    path("terms-and-conditions/", views.legal_page, {"slug": "terms-and-conditions"}, name="terms"),
    path("legal/<slug:slug>/", views.legal_page, name="legal"),
]
