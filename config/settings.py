"""Django settings for the Rudra Sports Rifle Shooting Society website.

All secrets and environment-specific values come from environment variables
(optionally loaded from a local .env file). See .env.example.
"""
import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

try:  # python-dotenv is optional at runtime; real env vars always win
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent.parent
if load_dotenv:
    load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [v.strip() for v in os.environ.get(name, default).split(",") if v.strip()]


DEBUG = env_bool("DJANGO_DEBUG", False)
TESTING = "test" in sys.argv

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if TESTING:
        SECRET_KEY = "test-only-secret-key-not-for-use"
    else:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY is not set. Copy .env.example to .env and set it."
        )

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1" if DEBUG else "")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")
# Fixed developer credit - intentionally NOT editable from the admin panel.
DEVELOPER_CREDIT = {"text": "Designed & Developed by The Webfix", "label": "The Webfix", "url": "https://thewebfix.in"}
SITE_URL = os.environ.get("SITE_URL", "http://127.0.0.1:8000").rstrip("/")

INSTALLED_APPS = [
    "jazzmin",  # admin theme - must come before django.contrib.admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "apps.core",
    "apps.programs",
    "apps.gallery",
    "apps.achievements",
    "apps.events",
    "apps.admissions",
    "apps.contact",
    "apps.bookings",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.core.middleware.LaunchCountdownMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "builtins": ["apps.core.templatetags.compat"],
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site",
                "apps.core.context_processors.admin_dashboard",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Database: SQLite locally, PostgreSQL in production -------------------
if os.environ.get("DB_ENGINE", "sqlite").lower() in {"postgres", "postgresql"}:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "rudra_sports"),
            "USER": os.environ.get("DB_USER", ""),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# --- Static & media ---------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = Path(os.environ.get("STATIC_ROOT", BASE_DIR / "staticfiles"))
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", BASE_DIR / "media"))

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        if (DEBUG or TESTING)
        else "config.storage.RelaxedManifestStorage"
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Uploads: validated again in apps.core.validators
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_PERMISSIONS = 0o644

# Throttle for public forms: requests allowed per window, per IP
FORM_THROTTLE_LIMIT = 5
FORM_THROTTLE_WINDOW = 600  # seconds

# --- Email ------------------------------------------------------------------
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)  # port 465 uses SSL; port 587 uses TLS (set only one)
EMAIL_TIMEOUT = 15
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "") or "info@rudrasports.com"
ENQUIRY_NOTIFY_EMAILS = env_list("ENQUIRY_NOTIFY_EMAILS")

# --- Security ---------------------------------------------------------------
LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/admin/"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"

if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
    # Secure cookies need HTTPS. Only switch off while a new domain is still waiting for its SSL certificate.
    SESSION_COOKIE_SECURE = env_bool("DJANGO_SECURE_COOKIES", True)
    CSRF_COOKIE_SECURE = env_bool("DJANGO_SECURE_COOKIES", True)
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = False  # opt in deliberately once HTTPS is confirmed everywhere
    if env_bool("DJANGO_BEHIND_PROXY", False):
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --- Caching (swap for Redis/Memcached in production for shared throttling) --
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# --- Logging ----------------------------------------------------------------
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "{asctime} {levelname} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "site.log",
            "maxBytes": 1_000_000,
            "backupCount": 3,
            "formatter": "standard",
            "encoding": "utf-8",
        },
    },
    "root": {"handlers": ["console", "file"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["console", "file"], "level": "WARNING", "propagate": False},
    },
}
if TESTING:
    LOGGING["root"]["handlers"] = []
    LOGGING["loggers"]["django.request"]["handlers"] = []


# --- Admin theme (django-jazzmin), branded with the academy colours ----------
JAZZMIN_SETTINGS = {
    "site_title": "Rudra Sports Admin",
    "site_header": "Rudra Sports",
    "site_brand": "Rudra Sports",
    "site_logo": "images/favicon.png",
    "login_logo": "images/favicon.png",
    "site_logo_classes": "img-circle",
    "site_icon": "images/favicon.png",
    "welcome_sign": "Welcome to the Rudra Sports admin",
    "copyright": "Rudra Sports Rifle Shooting Society",
    "search_model": ["admissions.AdmissionEnquiry", "bookings.SlotBooking", "programs.Program"],
    "user_avatar": None,
    "topmenu_links": [
        {"name": "Dashboard", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Website", "url": "/", "new_window": True},
        {"name": "Countdown", "url": "admin:core_launchcountdown_changelist", "permissions": ["core.change_sitesettings"]},
        {"name": "Enquiries", "url": "admin:admissions_admissionenquiry_changelist", "permissions": ["admissions.view_admissionenquiry"]},
        {"name": "Slots", "url": "admin:bookings_slot_changelist", "permissions": ["bookings.view_slot"]},
    ],
    "usermenu_links": [
        {"name": "View website", "url": "/", "new_window": True, "icon": "fas fa-globe"},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "order_with_respect_to": [
        "bookings", "admissions", "contact", "core", "core.launchcountdown", "core.sitesettings", "programs", "gallery", "events", "achievements", "auth",
    ],
    "icons": {
        "auth": "fas fa-users-cog", "auth.user": "fas fa-user", "auth.Group": "fas fa-users",
        "core.sitesettings": "fas fa-sliders-h", "core.launchcountdown": "fas fa-hourglass-half", "core.menuitem": "fas fa-bars", "core.heroslide": "fas fa-images", "core.announcement": "fas fa-bullhorn", "core.instagramreel": "fab fa-instagram",
        "core.testimonial": "fas fa-quote-right", "core.faq": "fas fa-question-circle", "core.facility": "fas fa-building",
        "core.contentitem": "fas fa-list-ul", "core.legalpage": "fas fa-gavel",
        "programs.program": "fas fa-bullseye", "gallery.galleryimage": "fas fa-photo-video", "gallery.category": "fas fa-tags",
        "achievements.achievement": "fas fa-trophy", "events.event": "fas fa-calendar-alt",
        "admissions.admissionenquiry": "fas fa-user-plus", "contact.contactmessage": "fas fa-envelope",
        "bookings.slot": "fas fa-calendar-check", "bookings.slotbooking": "fas fa-ticket-alt", "bookings.slotschedule": "fas fa-redo",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": True,
    "custom_css": "css/admin-brand.css",
    "custom_js": "js/admin-credit.js",
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {"auth.user": "collapsible", "auth.group": "vertical_tabs"},
}
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False, "footer_small_text": False, "body_small_text": False, "brand_small_text": False,
    "brand_colour": False, "accent": "accent-indigo", "navbar": "navbar-white navbar-light", "no_navbar_border": False,
    "navbar_fixed": True, "layout_boxed": False, "footer_fixed": False, "sidebar_fixed": True,
    "sidebar": "sidebar-dark-indigo", "sidebar_nav_small_text": False, "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True, "sidebar_nav_compact_style": False, "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False, "theme": "default", "default_theme_mode": "light",
    "button_classes": {
        "primary": "btn-primary", "secondary": "btn-secondary", "info": "btn-info", "warning": "btn-warning",
        "danger": "btn-danger", "success": "btn-success",
    },
}
