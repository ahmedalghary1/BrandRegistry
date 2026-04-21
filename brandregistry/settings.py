import os
import sys
from pathlib import Path


def ensure_writable_dir(preferred: Path, fallback: Path) -> Path:
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        probe_file = preferred / ".write_test"
        probe_file.write_text("ok", encoding="utf-8")
        probe_file.unlink(missing_ok=True)
        return preferred
    except OSError:
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


# Build paths inside the project like this: BASE_DIR / 'subdir'.
if getattr(sys, "frozen", False):
    PROJECT_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
else:
    PROJECT_DIR = Path(__file__).resolve().parent.parent

# Local desktop-safe storage for the SQLite DB, uploads, and collected static files.
appdata_root = Path(os.getenv("APPDATA")) if os.getenv("APPDATA") else (PROJECT_DIR / ".localdata")
fallback_root = PROJECT_DIR / ".localdata"
DATA_DIR = ensure_writable_dir(appdata_root / "trademark-registry", fallback_root / "trademark-registry")

# Use BASE_DIR for compatibility with the rest of the project.
BASE_DIR = PROJECT_DIR

SECRET_KEY = "django-insecure-=w&_6nj#*ayyhx$1zipmq++!9^kv@ww#$+hp&2!7gv2)i5jo_k"
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
DESKTOP_LOCAL_MODE = os.getenv("DESKTOP_LOCAL_MODE", "1") == "1"
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_bootstrap5",
    "solo",
    "registry",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "brandregistry.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "registry.context_processors.global_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "brandregistry.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "db.sqlite3",
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "ar"
LANGUAGES = [("ar", "العربية")]
TIME_ZONE = "Africa/Cairo"
USE_I18N = True
USE_TZ = True


STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = DATA_DIR / "staticfiles"
STATIC_ROOT = ensure_writable_dir(STATIC_ROOT, fallback_root / "trademark-registry" / "staticfiles")

MEDIA_URL = "/media/"
MEDIA_ROOT = DATA_DIR / "media"
MEDIA_ROOT = ensure_writable_dir(MEDIA_ROOT, fallback_root / "trademark-registry" / "media")

FILE_UPLOAD_PERMISSIONS = 0o644
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
X_FRAME_OPTIONS = "SAMEORIGIN"
