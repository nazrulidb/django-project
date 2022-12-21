from decouple import config
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent
print(f"PROD BASE_DIR {BASE_DIR}")

# CSRF_COOKIE_SECURE = True
# CSRF_COOKIE_HTTPONLY = True
# CSRF_USE_SESSIONS=True

# SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7 * 52  # one year
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
# SECURE_SSL_REDIRECT = True

# SECURE_CONTENT_TYPE_NOSNIFF = True
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# SESSION_COOKIE_SECURE = True
# SESSION_SAVE_EVERY_REQUEST = True
if config("DEBUG", default=False, cast=bool):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "fsoftuni2",
            "USER": "postgres",
            "PASSWORD": "123",
            "HOST": "103.157.135.131",
            "PORT": "5432",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("DB_NAME"),
            "USER": config("DB_USER"),
            "PASSWORD": config("DB_PASSWORD"),
            "HOST": "127.0.0.1",
            "PORT": "5432",
        }
    }

AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = config("AWS_S3_ENDPOINT_URL")
AWS_S3_REGION_NAME = "sgp1"
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400", "ACL": "public-read"}
AWS_DEFAULT_ACL = "public-read"
AWS_HEADERS = {"Access-Control-Allow-Origin": "*"}

# AWS_QUERYSTRING_AUTH=False
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_USE_SSL = True
AWS_S3_FILE_OVERWRITE = False
AWS_LOCATION = config("AWS_LOCATION")
AWS_MEDIA_LOCATION = "media"
STATIC_URL = "https://%s/%s/" % (AWS_S3_ENDPOINT_URL, AWS_LOCATION)

MEDIA_URL = "/media/"

STATICFILES_DIRS = [
    os.path.join(os.path.dirname(BASE_DIR), "assets", "static"),
    os.path.join(os.path.dirname(BASE_DIR), "assets", "media"),
]


TEMP = os.path.join(BASE_DIR, "temp")

STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
# DEFAULT_FILE_STORAGE = 'storage.ManifestS3Storage'


ADMINS = [("papatupher", "papatupher@gmail.com")]

BASE_URL = ""
WAGTAILADMIN_BASE_URL = ""

INTERNAL_IPS = ["103.157.135.131", "localhost"]
# ALLOWED_HOSTS = ["localhost", '128.199.252.217', 'jerizfoodcarts.com', 'www.jerizfoodcarts.com']
ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = [
    "https://*.127.0.0.1",
    "https://*.159.223.72.173",
    "https://*.facebook.com",
    "https://*.google.com",
    "https://*.freshosoft.dev",
    "https://butex.freshosoft.dev",
]


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "filters": [],
        },
        # 'gunicorn': {
        #     'level': 'DEBUG',
        #     'class': 'logging.handlers.RotatingFileHandler',
        #     'formatter': 'verbose',
        #     'filename': '/root/project/gunicorn.logs',
        #     'maxBytes': 1024 * 1024 * 100,  # 100 mb
        # }
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "propagate": True,
        },
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        # 'gunicorn.errors': {
        #     'level': 'DEBUG',
        #     'handlers': ['gunicorn'],
        #     'propagate': True,
        # },
    },
}
