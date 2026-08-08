import logging

from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from core.models import (
    ShippingRequest, Quote, TransportTask, StateLog,
    Vehicle,
)
from core.utils.cache_utils import delete_cache, delete_cache_pattern, cache_key

logger = logging.getLogger(__name__)

STATUS_FIELD_MAP = {
    'ShippingRequest': 'status',
    'Quote': 'status',
    'TransportTask': 'task_status',
}


# ============================================================
# 状态变更日志（pre_save）
# ============================================================

@receiver(pre_save, sender=ShippingRequest)
def shipping_request_status_log(sender, instance, **kwargs):
    _log_status_change(sender, instance)


@receiver(pre_save, sender=Quote)
def quote_status_log(sender, instance, **kwargs):
    _log_status_change(sender, instance)


@receiver(pre_save, sender=TransportTask)
def transport_task_status_log(sender, instance, **kwargs):
    _log_status_change(sender, instance)


def _log_status_change(sender, instance):
    try:
        if instance.pk is None:
            return

        model_name = sender.__name__
        field_name = STATUS_FIELD_MAP.get(model_name)
        if field_name is None:
            return

        old_obj = sender._default_manager.get(pk=instance.pk)
        old_status = getattr(old_obj, field_name)
        new_status = getattr(instance, field_name)

        if old_status == new_status:
            return

        from core.middleware import get_current_user
        user = get_current_user()
        changed_by = str(user) if user else 'system'

        content_type = ContentType.objects.get_for_model(sender)

        StateLog.objects.create(
            content_type=content_type,
            object_id=instance.pk,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
        )
    except Exception as e:
        logger.warning('StateLog creation failed for %s #%s: %s', sender.__name__, instance.pk, e)


# ============================================================
# 缓存失效信号（post_save / post_delete）
# ============================================================

@receiver(post_save, sender=Vehicle)
@receiver(post_delete, sender=Vehicle)
def invalidate_vehicle_cache(sender, instance, **kwargs):
    """车辆变更时删除运力档案缓存"""
    try:
        # 通配符删除所有车辆列表缓存
        delete_cache_pattern('core:vehicle:list:*')
        logger.info('Vehicle cache invalidated: vehicle_id=%s', instance.vehicle_id)
    except Exception as e:
        logger.warning('Vehicle cache invalidation failed: %s', e)


@receiver(post_save, sender=ShippingRequest)
def invalidate_request_cache(sender, instance, **kwargs):
    """运输需求变更时删除需求广场缓存"""
    try:
        # 删除需求广场（待报价列表）缓存
        delete_cache_pattern('core:request:list:*')
        # 如果状态发生变化，确保缓存失效
        delete_cache_pattern('core:request:*')
        logger.info('ShippingRequest cache invalidated: request_id=%s, status=%s',
                     instance.request_id, instance.status)
    except Exception as e:
        logger.warning('ShippingRequest cache invalidation failed: %s', e)


@receiver(post_save, sender=Quote)
def invalidate_quote_cache(sender, instance, **kwargs):
    """报价变更时删除该需求的报价列表缓存"""
    try:
        # 删除按需求ID缓存的报价列表
        c_key = cache_key('quote', 'request', instance.request_id)
        delete_cache(c_key)
        logger.info('Quote cache invalidated: quote_id=%s, request_id=%s',
                     instance.quote_id, instance.request_id)
    except Exception as e:
        logger.warning('Quote cache invalidation failed: %s', e)
