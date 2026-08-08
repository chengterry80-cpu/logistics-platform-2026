"""
Celery 应用配置

Broker: Redis (带密码认证)
Backend: django-celery-results (数据库存储结果)
"""

import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logistics_platform.settings')

app = Celery('logistics_platform')

# 使用 Django settings 中的 CELERY_* 前缀配置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现所有 app 的 tasks.py
app.autodiscover_tasks()
