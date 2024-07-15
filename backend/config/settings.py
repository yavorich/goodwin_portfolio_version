from pathlib import Path
import os

from aiogram import Bot
from django.utils.timezone import timedelta
from django.utils.translation import gettext_lazy as _
from import_export.formats.base_formats import XLSX
from tablib.formats import registry
from telethon import TelegramClient
from telethon.sessions import StringSession

from core.import_export.formats import DimensionXLSXFormat


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-gxc4#5+%jv_)3s$h-ymoezn6tyjl4wqzxd1z5$!+fd9(osevmz"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ["DEBUG"].lower() == "true"
TEST_MODE = os.environ["TEST_MODE"].lower() == "true"

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(
    ","
)

CSRF_TRUSTED_ORIGINS = ["http://" + host + ":8000" for host in ALLOWED_HOSTS] + [
    "https://" + host for host in ALLOWED_HOSTS
]

CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:8000").split(
    ","
)

# Application definition
LOCAL_APPS = [
    "core",
    "apps.accounts",
    "apps.faq",
    "apps.finance",
    "apps.gdw_site",
    "apps.support",
    "apps.telegram",
]

THIRD_PARTY_APPS = [
    "django.contrib.postgres",
    "psqlextra",
    "localized_fields",
    "rest_framework",
    "django_filters",
    "corsheaders",
    "nested_admin",
    "import_export",
    "django_admin_geomap",
]

INSTALLED_APPS = (
    [
        "daphne",
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "django.contrib.humanize",
    ]
    + THIRD_PARTY_APPS
    + LOCAL_APPS
)

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
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
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

ASGI_APPLICATION = "config.asgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "psqlextra.backend",
        # "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ.get("POSTGRES_DB", "postgres"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": 5432,
        "ATOMIC_REQUESTS": True,
    }
}

# Redis
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(os.environ.get("REDIS_HOST"), os.environ.get("REDIS_PORT"))],
        },
    },
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "ru"

LANGUAGES = [
    ("ru", _("Russian")),
    ("en", _("English")),
    ("cn", _("China")),
]

LOCALE_PATHS = [
    BASE_DIR / "locale/",
]

TIME_ZONE = os.environ.get("TIME_ZONE", "UTC")

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "staticfiles"),
]


# Media files

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

ATOMIC_REQUESTS = True

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_PORT = os.environ.get("EMAIL_PORT")
EMAIL_USE_TLS = True

RABBITMQ = {
    "PROTOCOL": "amqp",
    "HOST": os.environ.get("RABBITMQ_HOST"),
    "PORT": os.environ.get("RABBITMQ_PORT"),
    "USER": os.environ.get("RABBITMQ_USER"),
    "PASSWORD": os.environ.get("RABBITMQ_PASSWORD"),
}

CELERY_BROKER_URL = (
    f"{RABBITMQ['PROTOCOL']}://{RABBITMQ['USER']}:"
    f"{RABBITMQ['PASSWORD']}@{RABBITMQ['HOST']}:{RABBITMQ['PORT']}"
)
CELERY_TIMEZONE = "UTC"

MAIN_URL = os.environ.get("MAIN_URL", "http://localhost:8000/")

RECOVER_PASSWORD_CODE_EXPIRES = timedelta(hours=24)
REGISTER_CONFIRMATION_EXPIRES = timedelta(hours=1)
PRE_AUTH_CODE_EXPIRES = timedelta(minutes=5)
CHANGE_SETTINGS_CODE_EXPIRES = timedelta(days=1)
OPERATION_CONFIRM_CODE_EXPIRES = timedelta(minutes=5)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

# telegram bot settings
TELEGRAM_BOT_NAME = os.environ.get("TELEGRAM_BOT_NAME")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", None)
MAIN_BOT = Bot(TELEGRAM_BOT_TOKEN, parse_mode="HTML") if TELEGRAM_BOT_TOKEN else None

CORS_ALLOW_CREDENTIALS = True

NODE_JS_HOST = os.environ.get("NODE_JS_HOST")
NODE_JS_URL = "http://" + NODE_JS_HOST
NODE_JS_TOKEN = os.environ.get("NODE_JS_TOKEN")
LOCAL_TOKEN = os.environ.get("LOCAL_TOKEN")

LOGIN_AS_USER_TOKEN = os.environ.get("LOGIN_AS_USER_TOKEN")

# import, export
IMPORT_EXPORT_FORMATS = [XLSX]
registry.register("xlsx", DimensionXLSXFormat)

# telegram api settings
TELEGRAM_API_ID = os.environ.get("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH")
TELEGRAM_NEWS_CHANNELS = {
    "ru": os.environ.get("TELEGRAM_NEWS_CHANNEL_RU"),
    "en": os.environ.get("TELEGRAM_NEWS_CHANNEL_EN"),
}
TELEGRAM_PHONE_NUMBER = os.environ.get("TELEGRAM_PHONE_NUMBER")
TELEGRAM_SESSION = os.environ.get("TELEGRAM_SESSION")

NEWS_BOT = TelegramClient(
    StringSession(TELEGRAM_SESSION), TELEGRAM_API_ID, TELEGRAM_API_HASH
)
NEWS_BOT.parse_mode = "html"
