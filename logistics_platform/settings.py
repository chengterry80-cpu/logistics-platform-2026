import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# 从项目根目录读取 .env 文件（与 manage.py 同级）
# 说明：
#   1) 若本地开发，提供 .env 文件即可覆盖默认值
#   2) 若容器化或部署，可直接通过环境变量注入，无需 .env 文件
ENV_PATH = BASE_DIR / '.env'
if ENV_PATH.exists():
    load_dotenv(dotenv_path=str(ENV_PATH), override=False)


def env_str(name, default=''):
    return os.environ.get(name, default)


def env_int(name, default=0):
    value = os.environ.get(name)
    if value in (None, ''):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value in (None, ''):
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ('1', 'true', 'yes', 'y', 'on')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# 提示：生产环境必须通过 DJANGO_SECRET_KEY 环境变量注入一个长随机字符串
DEFAULT_SECRET_KEY = 'django-insecure-dev-change-me-please-placeholder-key-0000000000'
SECRET_KEY = env_str('DJANGO_SECRET_KEY', DEFAULT_SECRET_KEY)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_bool('DJANGO_DEBUG', True)

ALLOWED_HOSTS = [
    h for h in env_str('DJANGO_ALLOWED_HOSTS', '*').split(',') if h
] or ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    'drf_spectacular',
    'django_celery_beat',
    'django_celery_results',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.CurrentUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'logistics_platform.urls'

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

WSGI_APPLICATION = 'logistics_platform.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# 说明：为了不影响已有开发流程，DATABASES 仍给出合理默认值，
# 但数据库名/用户/密码/主机/端口 均可通过 .env 覆盖。
DATABASES = {
    'default': {
        'ENGINE': env_str('DB_ENGINE', 'django.db.backends.mysql'),
        'NAME': env_str('DB_NAME', 'logistics_platform'),
        'USER': env_str('DB_USER', 'root'),
        'PASSWORD': env_str('DB_PASSWORD', ''),
        'HOST': env_str('DB_HOST', '127.0.0.1'),
        'PORT': env_str('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        }
    }
}

# 自定义用户模型
AUTH_USER_MODEL = 'core.User'


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================================
# DRF 配置
# ============================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'core.views.custom_exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=env_int('JWT_ACCESS_TTL_HOURS', 24)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=env_int('JWT_REFRESH_TTL_DAYS', 7)),
    'ROTATE_REFRESH_TOKENS': True,
}

SPECTACULAR_SETTINGS = {
    'TITLE': '无车承运智能物流平台 API',
    'DESCRIPTION': '基于 Django REST Framework 的物流平台后端 API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}


# ============================================================
# Redis 缓存配置 / Celery Broker
# ============================================================
# Redis 连接串的通用构造：优先使用 REDIS_URL；否则按主机/端口/密码拼接
REDIS_HOST = env_str('REDIS_HOST', '127.0.0.1')
REDIS_PORT = env_str('REDIS_PORT', '6379')
REDIS_PASSWORD = env_str('REDIS_PASSWORD', '')
REDIS_PASSWORD_PART = f':{REDIS_PASSWORD}@' if REDIS_PASSWORD else ''
REDIS_BASE = f'redis://{REDIS_PASSWORD_PART}{REDIS_HOST}:{REDIS_PORT}'

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'{REDIS_BASE}/{env_int("REDIS_CACHE_DB", 1)}',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,  # Redis 不可用时降级，不抛异常
        },
        'KEY_PREFIX': env_str('REDIS_KEY_PREFIX', 'logistics'),
        'TIMEOUT': env_int('CACHE_TIMEOUT', 300),  # 默认缓存超时 5 分钟
    }
}

# 缓存超时时间常量（秒）
CACHE_TIMEOUTS = {
    'VEHICLE_AVAILABLE': 300,      # 运力档案：5分钟
    'REQUEST_PENDING': 180,        # 需求广场：3分钟
    'QUOTE_BY_REQUEST': 600,       # 报价列表（按需求ID）：10分钟
}


# ============================================================
# Celery 配置
# ============================================================

CELERY_BROKER_URL = env_str(
    'CELERY_BROKER_URL',
    f'{REDIS_BASE}/{env_int("REDIS_CELERY_DB", 0)}'
)
CELERY_RESULT_BACKEND = env_str('CELERY_RESULT_BACKEND', 'django-db')

# 使用 json 序列化
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# 时区
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_ENABLE_UTC = False

# 任务结果有效期（1天）
CELERY_RESULT_EXPIRES = 86400

# 任务重试延迟
CELERY_TASK_ACKS_ON_FAILURE_OR_TIMEOUT = True

# 每个 worker 子进程数（Windows 环境 solo 模式）
CELERY_WORKER_POOL = 'solo'

# Beat 定时任务调度表
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers.DatabaseScheduler'

# 定时任务周期定义（Beat 启动时从数据库读取，这里作为默认值参考）
CELERY_BEAT_SCHEDULE = {
    'clean-expired-cache': {
        'task': 'core.tasks.task_clean_expired_cache',
        'schedule': 1800.0,  # 每 30 分钟
    },
    'cancel-timeout-orders': {
        'task': 'core.tasks.task_cancel_timeout_orders',
        'schedule': 3600.0,  # 每小时
    },
}
