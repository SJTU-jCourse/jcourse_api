"""
Django settings for jcourse project.

Generated by 'django-admin startproject' using Django 3.2.3.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-chd73zi=3zn63gqmmczye1&oo)r*=0=h+6tu3*fj+*1-fqrala')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(os.environ.get('DEBUG', False))

ALLOWED_HOSTS = ['course.sjtu.plus']
CSRF_TRUSTED_ORIGINS = ['https://course.sjtu.plus']
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'jcourse_api',
    'rest_framework',
    'oauth',
    'django_filters',
    'import_export',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

ROOT_URLCONF = 'jcourse.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

WSGI_APPLICATION = 'jcourse.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

REDIS_HOST = os.environ.get('REDIS_HOST', None)
if REDIS_HOST:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': f'redis://{REDIS_HOST}:6379',
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'jcourse',
        'USER': 'jcourse',
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'jcourse'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': 5432
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

LANGUAGE_CODE = 'zh-Hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTHLIB_OAUTH_CLIENTS = {
    'jaccount': {
        'client_id': os.environ.get('JACCOUNT_CLIENT_ID', ''),
        'client_secret': os.environ.get('JACCOUNT_CLIENT_SECRET', ''),
    }
}

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_PAGINATION_CLASS': 'jcourse.paginations.GlobalPageNumberPagination',
    'PAGE_SIZE': 20,
    'DATETIME_FORMAT': "%Y/%m/%d %H:%M",
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.UserRateThrottle'],
    'DEFAULT_THROTTLE_RATES': {
        'user': '5/second',
        'review_action': '20/day'
    },
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    )
}

if DEBUG:
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    )

CORS_ORIGIN_WHITELIST = [
    'http://localhost:3000',
]

IMPORT_EXPORT_USE_TRANSACTIONS = True

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True

HASH_SALT = os.environ.get('HASH_SALT', '')

EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.qiye.aliyun.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 465))

EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_SSL = True
DEFAULT_FROM_EMAIL = os.environ.get('EMAIL_HOST_USER', EMAIL_HOST_USER)
ADMIN_EMAIL = os.environ.get('EMAIL_HOST_USER', EMAIL_HOST_USER)

if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = [
        "127.0.0.1",
    ]
    import mimetypes

    mimetypes.add_type("application/javascript", ".js", True)
    DEBUG_TOOLBAR_CONFIG = {
        'INTERCEPT_REDIRECTS': False,
    }
    ALLOWED_HOSTS += ['localhost', '127.0.0.1']
    CSRF_TRUSTED_ORIGINS += ['http://localhost:3000']

LOGGING_FILE = os.environ.get('LOGGING_FILE', '')

if LOGGING_FILE != '':
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse',
            },
            'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
            },
        },
        'formatters': {
            'file': {
                '()': 'django.utils.log.ServerFormatter',
                'format': '[{server_time}] {message}',
                'style': '{',
            },
            'django.server': {
                '()': 'django.utils.log.ServerFormatter',
                'format': '[{server_time}] {message}',
                'style': '{',
            }
        },
        'handlers': {
            'file': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filters': ['require_debug_false'],
                'filename': LOGGING_FILE,
                'formatter': 'file'
            },
            'console': {
                'level': 'INFO',
                'filters': ['require_debug_true'],
                'class': 'logging.StreamHandler',
            },
            'django.server': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'django.server',
            },
            'mail_admins': {
                'level': 'ERROR',
                'filters': ['require_debug_false'],
                'class': 'django.utils.log.AdminEmailHandler'
            }
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'file', 'mail_admins'],
                'level': 'INFO',
            },
            'django.server': {
                'handlers': ['django.server'],
                'level': 'INFO',
                'propagate': False,
            },
        }
    }
