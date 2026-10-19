"""Launch countdown: until the launch time set in Site Settings, public visitors see only a countdown page."""
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from .models import SiteSettings

OPEN_PREFIXES = ("/admin/", "/static/", "/media/", "/robots.txt", "/favicon")


class LaunchCountdownMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith(OPEN_PREFIXES):
            return self.get_response(request)
        site = SiteSettings.objects.first()
        remaining = None
        if site and site.launch_countdown_enabled and site.launch_at:
            remaining = int((site.launch_at - timezone.now()).total_seconds())
        if path == "/launch-status/":
            return JsonResponse({"remaining": remaining if remaining and remaining > 0 else 0}, headers={"Cache-Control": "no-store"})
        if remaining is None or remaining <= 0:
            return self.get_response(request)
        user = getattr(request, "user", None)
        request.launch_pending = True
        if user is not None and user.is_staff and request.GET.get("preview") != "countdown":
            return self.get_response(request)  # the team sees the real site while the countdown runs ("?preview=countdown" shows the visitor view)
        response = render(request, "launch/countdown.html", {"site": site, "remaining": remaining})
        response["Cache-Control"] = "no-store"
        response["X-Robots-Tag"] = "noindex, nofollow"
        return response
