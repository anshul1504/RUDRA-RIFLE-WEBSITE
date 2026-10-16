from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from apps.core import views as core_views
from apps.core.sitemaps import sitemaps

admin.site.site_header = "Rudra Sports - Site administration"
admin.site.site_title = "Rudra Sports admin"
admin.site.index_title = "Manage website content"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("robots.txt", core_views.robots_txt, name="robots"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("programs/", include("apps.programs.urls")),
    path("gallery/", include("apps.gallery.urls")),
    path("achievements/", include("apps.achievements.urls")),
    path("events/", include("apps.events.urls")),
    path("admission/", include("apps.admissions.urls")),
    path("contact/", include("apps.contact.urls")),
    path("book/", include("apps.bookings.urls")),
    path("", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"
