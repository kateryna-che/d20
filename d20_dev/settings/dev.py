from .base import *

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-kcye==jf*fsy8fvkrg!4q$h*!^y^!%cyg5!)6oh(&o)0cs97j+",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "") != "False"

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            "transaction_mode": "IMMEDIATE",
        },
    }
}


WHITENOISE_USE_FINDERS = True


MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}
