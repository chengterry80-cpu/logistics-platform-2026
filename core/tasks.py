"""
Celery 异步任务定义

所有任务使用 @shared_task(bind=True, max_retries=3) 保证幂等性。
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def task_update_location(self, driver_id, lat, lng, task_id=None):
    """
    处理司机位置上报，更新 TransportTask 的经纬度。

    Args:
        driver_id: 司机ID
        lat: 纬度
        lng: 经度
        task_id: 关联的运输任务ID（可选）
    """
    try:
        if task_id:
            from core.models import TransportTask
            task = TransportTask.objects.filter(task_id=task_id).first()
            if task:
                task.current_location = f'{lat:.6f},{lng:.6f}'
                task.save(update_fields=['current_location'])
                logger.info('位置上报成功: task_id=%s, driver_id=%s, lat=%.6f, lng=%.6f',
                            task_id, driver_id, lat, lng)
                return {'status': 'success', 'task_id': task_id}
        return {'status': 'success', 'message': 'location received'}
    except Exception as e:
        logger.error('位置上报失败: driver_id=%s, error=%s', driver_id, e)
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def task_report_anomaly(self, task_id, description, type='accident'):
    """
    处理异常上报（事故、堵车等），记录日志并尝试通知相关方。

    Args:
        task_id: 运输任务ID
        description: 异常描述
        type: 异常类型（accident/traffic/jam/other）
    """
    try:
        from core.models import TransportTask
        task = TransportTask.objects.filter(task_id=task_id).first()
        if not task:
            logger.warning('异常上报：任务不存在 task_id=%s', task_id)
            return {'status': 'ignored', 'reason': 'task not found'}

        logger.warning('异常上报: task_id=%s, type=%s, description=%s',
                       task_id, type, description)

        # 尝试发送通知给承运商和货主
        from django.contrib.contenttypes.models import ContentType
        from core.models import StateLog
        # 记录异常到状态日志（非状态变更，但保留记录）
        # 这里仅打印，真实场景可通过 WebSocket/短信推送

        task_send_notification.delay(
            user_id=None,
            title=f'运输异常: {type}',
            content=f'任务#{task_id} 发生异常: {description}',
            type='warning'
        )

        return {'status': 'success', 'task_id': task_id, 'type': type}
    except Exception as e:
        logger.error('异常上报处理失败: task_id=%s, error=%s', task_id, e)
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def task_send_notification(self, user_id, title, content, type='info'):
    """
    发送推送通知。当前实现为打印日志，后续可扩展为 WebSocket/短信。

    Args:
        user_id: 目标用户ID（None 表示广播/系统通知）
        title: 通知标题
        content: 通知内容
        type: 通知类型（info/warning/error/success）
    """
    try:
        level_map = {
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'success': logging.INFO,
        }
        level = level_map.get(type, logging.INFO)
        logger.log(level, '[NOTIFICATION] user=%s, type=%s, title=%s, content=%s',
                   user_id, type, title, content)
        return {'status': 'sent', 'user_id': user_id, 'type': type}
    except Exception as e:
        logger.error('通知发送失败: error=%s', e)
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=5)
def task_generate_loading_plan(self, cargo_ids, vehicle_id):
    """
    调用二维装箱算法生成装车方案。

    Args:
        cargo_ids: 货物ID列表（运输需求中的货物）
        vehicle_id: 车辆ID

    Returns:
        装车方案结果 dict
    """
    try:
        from core.models import ShippingRequest, Vehicle
        from core.algorithms.loading_plan import generate_loading_plan

        vehicle = Vehicle.objects.select_related('driver').filter(
            vehicle_id=vehicle_id
        ).first()
        if not vehicle:
            return {'error': f'车辆不存在: {vehicle_id}'}

        # 获取货物数据（这里假设通过 cargo_ids 查询运输需求详情）
        cargo_list = []
        for cargo_id in cargo_ids:
            req = ShippingRequest.objects.filter(request_id=cargo_id).first()
            if req:
                cargo_list.append({
                    'cargo_id': cargo_id,
                    'length': req.cargo_length or 0,
                    'width': req.cargo_width or 0,
                    'height': req.cargo_height or 0,
                    'weight': req.weight or 0,
                })

        vehicle_dict = {
            'length': vehicle.length or 0,
            'width': vehicle.width or 0,
            'height': vehicle.height or 0,
            'load_capacity': vehicle.load_capacity or 0,
        }

        result = generate_loading_plan(cargo_list, vehicle_dict)
        logger.info('装箱方案生成完成: vehicle=%s, placed=%d, unplaced=%d',
                     vehicle_id, len(result.get('placed', [])),
                     len(result.get('unplaced', [])))
        return result
    except Exception as e:
        logger.error('装箱方案生成失败: vehicle=%s, error=%s', vehicle_id, e)
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=1, default_retry_delay=5)
def task_clean_expired_cache(self):
    """
    清理过期缓存键（Beat 定时任务，每 30 分钟执行）。
    """
    try:
        from core.utils.cache_utils import delete_cache_pattern
        patterns = ['core:vehicle:list:*', 'core:request:list:*', 'core:quote:request:*']
        total_deleted = 0
        for pattern in patterns:
            n = delete_cache_pattern(pattern)
            total_deleted += n
        logger.info('缓存清理完成: 删除 %d 个过期键', total_deleted)
        return {'status': 'success', 'deleted_count': total_deleted}
    except Exception as e:
        logger.error('缓存清理失败: error=%s', e)
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def task_cancel_timeout_orders(self):
    """
    自动取消超时订单（Beat 定时任务，每小时执行）。

    规则：PENDING 状态超过 24 小时的运输需求自动取消。
    """
    try:
        from datetime import timedelta
        from django.utils import timezone
        from core.models import ShippingRequest, ShippingRequestStatus
        from core.utils.state_machine import Transition

        timeout_threshold = timezone.now() - timedelta(hours=24)
        timeout_requests = ShippingRequest.objects.filter(
            status=ShippingRequestStatus.PENDING,
            create_time__lt=timeout_threshold,
        )

        cancelled_count = 0
        for req in timeout_requests:
            try:
                Transition.transition(req, ShippingRequestStatus.CANCELLED)
                cancelled_count += 1
                logger.info('超时订单已自动取消: request_id=%s', req.request_id)
            except ValueError as e:
                logger.warning('超时订单取消失败: request_id=%s, error=%s', req.request_id, e)

        logger.info('超时订单清理完成: 已取消 %d 个订单', cancelled_count)
        return {'status': 'success', 'cancelled_count': cancelled_count}
    except Exception as e:
        logger.error('超时订单清理失败: error=%s', e)
        raise self.retry(exc=e)
