"""Shared validators for uploads."""
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_IMAGE_PIXELS = 40_000_000


def validate_image_upload(upload):
    """Check size, extension and that the file really is an image."""
    max_size = getattr(settings, "MAX_UPLOAD_SIZE", 5 * 1024 * 1024)
    if upload.size > max_size:
        raise ValidationError(f"Image is too large. Maximum size is {max_size // (1024 * 1024)} MB.")
    ext = os.path.splitext(upload.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError("Unsupported file type. Upload a JPG, PNG or WebP image.")
    try:
        pos = upload.tell() if hasattr(upload, "tell") else 0
        upload.seek(0)
        with Image.open(upload) as img:
            if img.format not in ALLOWED_IMAGE_FORMATS:
                raise ValidationError("The file content is not a valid JPG, PNG or WebP image.")
            if img.width * img.height > MAX_IMAGE_PIXELS:
                raise ValidationError("Image dimensions are too large.")
            img.verify()
        upload.seek(pos)
    except (UnidentifiedImageError, OSError, SyntaxError):
        raise ValidationError("The uploaded file is not a valid image.")


def validate_instagram_post_url(value):
    """Accept only a link to one specific Instagram reel/video/post, never a profile or a generic page."""
    import re
    from urllib.parse import urlparse

    parts = urlparse(value)
    host = (parts.hostname or "").lower()
    if parts.scheme not in {"http", "https"} or host not in {"instagram.com", "www.instagram.com"}:
        raise ValidationError("Enter a link on instagram.com.")
    if not re.match(r"^/(?:[A-Za-z0-9_.]+/)?(?:reel|reels|p|tv)/[A-Za-z0-9_-]{5,}/?$", parts.path):
        raise ValidationError("Paste the link of one specific reel or video, e.g. https://www.instagram.com/reel/XXXXXXXXXXX/ (not the profile).")


VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov"}
MAX_VIDEO_MB = 60


def validate_video_upload(upload):
    """Short clips only: MP4 / WebM / MOV, up to 60 MB (keeps the page fast on mobile data)."""
    import os

    from django.core.exceptions import ValidationError

    if os.path.splitext(upload.name)[1].lower() not in VIDEO_EXTENSIONS:
        raise ValidationError("Upload an MP4, WebM or MOV video.")
    if upload.size > MAX_VIDEO_MB * 1024 * 1024:
        raise ValidationError(f"The video is larger than {MAX_VIDEO_MB} MB. Please compress it or upload a shorter clip.")
