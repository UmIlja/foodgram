# flake8: noqa
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'any_key')

DEBUG = True
# os.getenv("DEBUG_MODE") == "False"

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'django_filters',
    'rest_framework',
    'rest_framework.authtoken',
    'djoser',
    'api.apps.ApiConfig',
    'users.apps.UsersConfig', 
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  
]

ROOT_URLCONF = 'foodgram_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'foodgram_backend.wsgi.application'


BASE_URL = "https://foodgram-ilja.sytes.net"


AUTH_USER_MODEL = 'users.UserProfile'  # Profile user model


# DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',  # Указываем, что используем SQLite
#        'NAME': BASE_DIR / 'db.sqlite3',  # Путь к файлу базы данных
#    }
#}
DATABASES = {
    'default': {
        #для работы будет использоваться бэкенд postgresql
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'django'),
        'USER': os.getenv('POSTGRES_USER', 'django'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', 5432)
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'  # Адрес для статических файтов
STATIC_ROOT = BASE_DIR / 'collected_static'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static'),]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / '/media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated', 
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '10000/day', #  Лимит для UserRateThrottle
        'anon': '1000/day',  #  Лимит для AnonRateThrottle
    },    
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 6,
    'DEFAULT_FILTER_BACKENDS': [
      'django_filters.rest_framework.DjangoFilterBackend'
    ]
}


DJOSER = {
    "SERIALIZERS": {
        "user": "api.serializers.FullUserSerializer",
        "current_user": "api.serializers.FullUserSerializer",
    },
    "PERMISSIONS": {
        "user": ["rest_framework.permissions.AllowAny"],  # Разрешаем доступ к пользователям всем
        "user_create": ["rest_framework.permissions.AllowAny"],  # Разрешаем регистрацию всем
        "user_list": ["rest_framework.permissions.AllowAny"],
        "current_user": ["rest_framework.permissions.IsAuthenticated"]
    },
}