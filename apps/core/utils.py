"""Small helpers shared by the public forms."""
import logging
import re
import unicodedata

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(value):
    """Strip HTML tags and control characters from free text (output is also auto-escaped)."""
    if not value:
        return value
    value = unicodedata.normalize("NFC", str(value))
    value = _CONTROL_CHARS.sub("", strip_tags(value))
    return value.strip()


def client_ip(request):
    return request.META.get("REMOTE_ADDR", "unknown")


def throttled(request, scope):
    """Return True when this client has exceeded the POST limit for `scope`."""
    key = f"throttle:{scope}:{client_ip(request)}"
    count = cache.get(key, 0)
    if count >= settings.FORM_THROTTLE_LIMIT:
        return True
    cache.set(key, count + 1, settings.FORM_THROTTLE_WINDOW)
    return False


def notify_staff(subject, body):
    """Email the academy about a new enquiry. Never raises; failures are logged."""
    recipients = settings.ENQUIRY_NOTIFY_EMAILS
    if not recipients:
        return
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=False)
    except Exception:  # noqa: BLE001 - never break the visitor's submission
        logger.exception("Could not send notification email")


def optimise_image(field_file, max_side=2000, quality=85):
    """Downscale a freshly uploaded image (in place, before it is saved to storage)."""
    from io import BytesIO

    from django.core.files.base import ContentFile
    from PIL import Image, ImageOps

    if not field_file or getattr(field_file, "_committed", True):
        return
    try:
        field_file.file.seek(0)
        with Image.open(field_file.file) as img:
            fmt = img.format
            img = ImageOps.exif_transpose(img)
            if max(img.size) <= max_side and fmt in {"JPEG", "PNG", "WEBP"}:
                field_file.file.seek(0)
                return
            img.thumbnail((max_side, max_side), Image.LANCZOS)
            buf = BytesIO()
            if fmt == "PNG":
                img.save(buf, "PNG", optimize=True)
            elif fmt == "WEBP":
                img.save(buf, "WEBP", quality=quality)
            else:
                img.convert("RGB").save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
        field_file.save(field_file.name, ContentFile(buf.getvalue()), save=False)
    except Exception:  # noqa: BLE001 - keep the original upload if processing fails
        logger.exception("Image optimisation failed for %s", field_file.name)
        try:
            field_file.file.seek(0)
        except Exception:  # noqa: BLE001
            pass


def acknowledge(to_email, subject, name, message):
    """Send a short acknowledgement to the visitor (only when they gave an email). Never raises."""
    if not to_email:
        return
    from .models import SiteSettings

    site = SiteSettings.load()
    body = (
        f"Namaste {name},\n\n{message}\n\n"
        f"For anything urgent, call {site.phone}.\n\n"
        f"{site.organisation_name}\n{site.address}\n{site.email}\n"
    )
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to_email], fail_silently=False)
    except Exception:  # noqa: BLE001
        logger.exception("Could not send acknowledgement email")


def page_enabled(flag):
    """View decorator: 404 when the matching Site settings switch (e.g. show_gallery) is off."""
    from functools import wraps

    from django.http import Http404

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            from .models import SiteSettings

            if not getattr(SiteSettings.load(), flag):
                raise Http404("This page is switched off")
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


def paginate(request, queryset, per_page, param="page"):
    """Return the requested page of `queryset` (invalid page numbers fall back to the nearest valid page)."""
    from django.core.paginator import Paginator

    return Paginator(queryset, per_page).get_page(request.GET.get(param))
