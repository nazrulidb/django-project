STATIC_URL = "/static/"
MEDIA_URL = "/media/"
BASE_URL = "http://localhost:8000"
WAGTAILADMIN_BASE_URL = "http://localhost:8000"
ALLOWED_HOSTS = ["*"]
INTERNAL_IPS = ["159.223.72.173", "localhost", "https://butex.freshosoft.dev"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "fsoftuni2",
        "USER": "postgres",
        "PASSWORD": "123",
        "HOST": "159.223.72.173",
        "PORT": "5432",
    }
}
