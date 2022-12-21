"""
Django settings for main project.

Generated by 'django-admin startproject' using Django 4.0.5.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from pathlib import Path
import os
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-7e*&_mac!ukx1!5^i$l@=6*zwa^y-8m2h6y(_@+8cyj3lf7_b^"

# SECURITY WARNING: don't run with debug turned on in production!

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

DEBUG = config("DEBUG", default=False, cast=bool)
DEBUG_PROD = config("DEBUG_PROD", default=False, cast=bool)
ALLOWED_HOSTS = ["13.212.91.212"]
INTERNAL_IPS = ["13.212.91.212", "localhost"]

DATABASES = {
  'default': {
  'ENGINE': 'django.db.backends.postgresql_psycopg2',
  'NAME': 'university',
  'USER': 'postgres',
  'PASSWORD': 'CAT00123',
  'HOST': 'localhost',
  'PORT': '',
  }
 }

if config("DEBUG_PROD", default=False, cast=bool):
    from .config.prod import *
else:
    if DEBUG:
        from .config.local import *
    else:
        from .config.prod import *


# Application definition

INSTALLED_APPS = [
    "main",
    'daphne',
    "users",
    "institutes",
    "departments",
    "custom_dashboard",
    "students",
    # wagtail
    # "home",
    "search",
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.contrib.settings",
    "wagtail.contrib.modeladmin",
    "wagtail.contrib.routable_page",
    "wagtail.embeds",
    "wagtail.sites",
    "users.apps.CustomUsersAppConfig",
    # 'wagtail.users',
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail.core",
    "modelcluster",
    "taggit",
    # wagtail
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "storages",
    "widget_tweaks",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

ROOT_URLCONF = "main.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
            os.path.join(BASE_DIR, "../templates"),
        ],
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

WSGI_APPLICATION = "main.wsgi.application"
ASGI_APPLICATION = 'main.routing.application'
# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
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
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('13.212.91.212', 6379)],
        },
    },
 }

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CONTENT_TYPES = ["image", "video"]

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000
DATA_UPLOAD_MAX_MEMORY_SIZE = 429916160
MAX_UPLOAD_SIZE = 429916160
SITE_ID = 1

APPEND_SLASH = True
WAGTAIL_APPEND_SLASH = True
# wagtail
WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.search.backends.database",
    }
}

AUTH_USER_MODEL = "users.CustomUser"


WAGTAIL_SITE_NAME = "FSoftUni"

WAGTAIL_FRONTEND_LOGIN_TEMPLATE = "student/login_form.html"
WAGTAIL_FRONTEND_LOGIN_URL = "/student/login/"

WAGTAIL_USER_EDIT_FORM = "users.forms.CustomUserEditForm"
WAGTAIL_USER_CREATION_FORM = "users.forms.CustomUserCreationForm"
WAGTAIL_USER_CUSTOM_FIELDS = ["institute", "department"]
WAGTAILADMIN_COMMENTS_ENABLED = True

WAGTAILDOCS_DOCUMENT_MODEL = "institutes.CustomDocument"
WAGTAILDOCS_DOCUMENT_FORM_BASE = 'institutes.forms.DocumentForm'


WAGTAILDOCS_SERVE_METHOD = "redirect"  # 'direct' 'serve_view'
WAGTAILDOCS_INLINE_CONTENT_TYPES = [
    "application/pdf",
    "text/plain",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]
WAGTAILDOCS_EXTENSIONS = ["xls", "xlsx"]
WAGTAIL_ENABLE_UPDATE_CHECK = False
