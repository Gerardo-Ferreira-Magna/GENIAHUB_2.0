

from pathlib import Path
import os
from django.utils import timezone
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-%1qcci-a)qqtp6+!%e-)s_d(uqo=&tl-581lw_323as844drne'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'AppWeb.apps.AppwebConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    "AppWeb.middleware.AuditMiddleware",
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'GENIAHUB.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'GENIAHUB.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.postgresql',
#        'NAME': 'GENIAHUB',
#        'USER': 'postgres',
#        'PASSWORD': 'admin',
#        'HOST': 'localhost',
#        'PORT': '5432',
#    }
#}

DATABASES = {
    'default': dj_database_url.parse(
        os.environ.get("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True
    )
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {'NAME': 'AppWeb.validators.LongitudMinimaValidator'},
    {'NAME': 'AppWeb.validators.ContraseñaComunValidator'},
    {'NAME': 'AppWeb.validators.NumericaValidator'},
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es-cl'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'AppWeb.Usuario'

LOGIN_REDIRECT_URL = 'proyectos'
LOGOUT_REDIRECT_URL = 'login'

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]


AUDIT_EXCLUDE_PREFIXES = (
    "/admin/login/",
    "/admin/logout/",
    "/admin/password_change/",
    "/__debug__/",
    "/api/healthcheck/",
    # agrega aquí cualquier otra ruta que NO quieras auditar
)

# Registrar también GET (vistas navegadas)
AUDIT_CAPTURE_GET = True

# Límite de bytes para leer del body (para no saturar)
AUDIT_MAX_BODY_BYTES = 100_000


# EMAIL (dev)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "no-reply@geniahub.cl"


# Archivos subidos
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"