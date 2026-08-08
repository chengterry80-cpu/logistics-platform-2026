import logging

from django.http import Http404
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import exception_handler
from django_filters.rest_framework import DjangoFilterBackend

from core.models import (
    User, Role,
    Shipper, Carrier, Driver, Vehicle,
    ShippingRequest, Quote, TransportTask, StateLog,
    ShippingRequestStatus, QuoteStatus, TaskStatus, PaymentStatus,
)
from core.serializers import (
    RegisterSerializer, UserListSerializer, UserDetailSerializer,
    ShipperListSerializer, ShipperDetailSerializer,
    CarrierListSerializer, CarrierDetailSerializer,
    DriverListSerializer, DriverDetailSerializer,
    VehicleListSerializer, VehicleDetailSerializer,
    ShippingRequestListSerializer, ShippingRequestDetailSerializer,
    ShippingRequestCreateSerializer,
    QuoteListSerializer, QuoteDetailSerializer,
    TransportTaskListSerializer, TransportTaskDetailSerializer,
    StateLogListSerializer, StateLogDetailSerializer,
)
from core.permissions import IsAdmin, IsShipper, IsCarrier, IsDriver
from core.utils.cache_utils import (
    get_or_set_cache, delete_cache, delete_cache_pattern,
    cache_key, generate_list_cache_key,
)
from django.conf import settings

logger = logging.getLogger(__name__)


# ============================================================
# 统一响应
# ============================================================

def success_response(data=None, message='success', code=0, http_status=status.HTTP_200_OK):
    return Response({'code': code, 'data': data, 'message': message}, status=http_status)


def error_response(message='error', code=1001, http_status=status.HTTP_400_BAD_REQUEST, data=None):
    return Response({'code': code, 'data': data, 'message': message}, status=http_status)


def paginated_response(view, queryset, serializer_class):
    """统一分页响应"""
    page = view.paginate_queryset(queryset)
    serializer = serializer_class(page or queryset, many=True)
    if page:
        data = view.paginator.get_paginated_response(serializer.data).data
    else:
        data = serializer.data
    return success_response(data)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            'code': response.status_code,
            'data': None,
            'message': response.data.get('detail', str(exc))
            if isinstance(response.data, dict) and 'detail' in response.data
            else str(exc),
        }
    return response


# ============================================================
# 认证
# ============================================================

class AuthViewSet(viewsets.ViewSet):
    permission_classes = (AllowAny,)

    def get_permissions(self):
        action_method = getattr(self, self.action, None)
        if action_method:
            func = action_method.__func__ if hasattr(action_method, '__func__') else action_method
            if hasattr(func, 'permission_classes'):
                return [perm() for perm in func.permission_classes]
            kwargs = getattr(func, 'kwargs', {})
            if 'permission_classes' in kwargs:
                return [perm() for perm in kwargs['permission_classes']]
        return [AllowAny()]

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return success_response({
            'id': user.id,
            'username': user.username,
            'role': user.role.role_code,
        }, message='注册成功', http_status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = UserDetailSerializer(request.user)
        return success_response(serializer.data)


# ============================================================
# 用户管理 (管理员)
# ============================================================

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related('role').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['username', 'email']
    filterset_fields = ['role', 'status']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        return UserDetailSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if not request.user.role.role_code == 'admin':
            queryset = queryset.filter(id=request.user.id)
        return paginated_response(self, queryset, self.get_serializer_class())

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return success_response(serializer.data, message='创建成功', http_status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, message='更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message='删除成功', http_status=status.HTTP_204_NO_CONTENT)


# ============================================================
# 货主管理
# ============================================================

class ShipperViewSet(viewsets.ModelViewSet):
    queryset = Shipper.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['username', 'company_name', 'contact_person']
    filterset_fields = ['status']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get_serializer_class(self):
        if self.action == 'list':
            return ShipperListSerializer
        return ShipperDetailSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if not request.user.role.role_code == 'admin':
            queryset = queryset.filter(username=request.user.username)
        return paginated_response(self, queryset, self.get_serializer_class())

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, message='创建成功', http_status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, message='更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message='删除成功', http_status=status.HTTP_204_NO_CONTENT)


# ============================================================
# 承运商管理
# ============================================================

class CarrierViewSet(viewsets.ModelViewSet):
    queryset = Carrier.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['username', 'company_name']
    filterset_fields = ['status']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get_serializer_class(self):
        if self.action == 'list':
            return CarrierListSerializer
        return CarrierDetailSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if not request.user.role.role_code == 'admin':
            queryset = queryset.filter(username=request.user.username)
        return paginated_response(self, queryset, self.get_serializer_class())

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, message='创建成功', http_status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, message='更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message='删除成功', http_status=status.HTTP_204_NO_CONTENT)


# ============================================================
# 司机管理
# ============================================================

class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['username', 'name', 'phone']
    filterset_fields = ['status']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get_serializer_class(self):
        if self.action == 'list':
            return DriverListSerializer
        return DriverDetailSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if not request.user.role.role_code == 'admin':
            queryset = queryset.filter(username=request.user.username)
        return paginated_response(self, queryset, self.get_serializer_class())

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, message='创建成功', http_status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, message='更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message='删除成功', http_status=status.HTTP_204_NO_CONTENT)


# ============================================================
# 车辆管理
# ============================================================

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.select_related('driver').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['plate_number']
    filterset_fields = ['vehicle_type', 'status', 'is_online', 'driver']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get_serializer_class(self):
        if self.action == 'list':
            return VehicleListSerializer
        return VehicleDetailSerializer

    def list(self, request, *args, **kwargs):
        user_role = request.user.role.role_code

        # 管理员/承运商查看可用车辆列表时启用缓存
        if user_role in ('admin', 'carrier'):
            # 查询参数用于缓存键
            cache_params = {
                'role': user_role,
                'vehicle_type': request.query_params.get('vehicle_type'),
                'status': request.query_params.get('status', 'available'),
                'is_online': request.query_params.get('is_online'),
                'page': request.query_params.get('page', 1),
            }
            c_key = generate_list_cache_key('vehicle', request.user.id, cache_params)
            timeout = settings.CACHE_TIMEOUTS['VEHICLE_AVAILABLE']

            def _fetch():
                queryset = self.get_queryset().filter(
                    status='available'
                ).only(
                    'vehicle_id', 'plate_number', 'vehicle_type',
                    'load_capacity', 'status', 'is_online', 'driver_id',
                )
                if user_role != 'admin':
                    queryset = queryset.filter(driver__username=request.user.username)
                queryset = self.filter_queryset(queryset)
                serializer = self.get_serializer(queryset, many=True)
                return serializer.data

            data = get_or_set_cache(c_key, _fetch, timeout=timeout)
            return success_response(data)

        # 其他角色走普通查询（带 only 优化）
        queryset = self.filter_queryset(self.get_queryset().only(
            'vehicle_id', 'plate_number', 'vehicle_type',
            'load_capacity', 'status', 'is_online', 'driver_id',
        ))
        if not user_role == 'admin':
            queryset = queryset.filter(driver__username=request.user.username)
        return paginated_response(self, queryset, self.get_serializer_class())

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, message='创建成功', http_status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, message='更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message='删除成功', http_status=status.HTTP_204_NO_CONTENT)


# ============================================================
# 运输需求 (核心业务)
# ============================================================

class ShippingRequestViewSet(viewsets.ModelViewSet):
    queryset = ShippingRequest.objects.select_related('shipper').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['cargo_name', 'origin', 'destination']
    filterset_fields = ['status', 'cargo_type', 'shipper']
    ordering_fields = ['request_id', 'expected_time']
    owner_field = 'shipper'
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        action_method = getattr(self, self.action, None)
        if action_method:
            func = action_method.__func__ if hasattr(action_method, '__func__') else action_method
            if hasattr(func, 'permission_classes'):
                return [perm() for perm in func.permission_classes]
            kwargs = getattr(func, 'kwargs', {})
            if 'permission_classes' in kwargs:
                return [perm() for perm in kwargs['permission_classes']]
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsShipper()]

    def get_serializer_class(self):
        if self.action == 'list':
            return ShippingRequestListSerializer
        if self.action == 'create':
            return ShippingRequestCreateSerializer
        return ShippingRequestDetailSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        user_role = request.user.role.role_code
        if user_role == 'shipper':
            queryset = queryset.filter(shipper__username=request.user.username)
        elif user_role == 'carrier':
            # 承运商查看需求广场（待报价列表）—— 启用缓存
            queryset = queryset.filter(status=ShippingRequestStatus.PENDING)

            cache_params = {
                'role': 'carrier',
                'cargo_type': request.query_params.get('cargo_type'),
                'page': request.query_params.get('page', 1),
            }
            c_key = generate_list_cache_key('request', request.user.id, cache_params)
            timeout = settings.CACHE_TIMEOUTS['REQUEST_PENDING']

            def _fetch():
                qs = queryset.only(
                    'request_id', 'cargo_name', 'cargo_type', 'weight', 'volume',
                    'origin', 'destination', 'status', 'expected_time', 'shipper_id',
                )
                serializer = self.get_serializer(qs, many=True)
                return serializer.data

            data = get_or_set_cache(c_key, _fetch, timeout=timeout)
            return success_response(data)

        elif user_role == 'driver':
            queryset = queryset.filter(status__in=[
                ShippingRequestStatus.QUOTED, ShippingRequestStatus.ASSIGNED,
                ShippingRequestStatus.IN_TRANSIT,
            ])
        elif user_role != 'admin':
            queryset = queryset.none()

        # 所有角色列表查询应用 only() 优化
        queryset = queryset.only(
            'request_id', 'cargo_name', 'cargo_type', 'weight', 'volume',
            'origin', 'destination', 'status', 'expected_time', 'shipper_id',
        )
        return paginated_response(self, queryset, self.get_serializer_class())

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def create(self, request, *args, **kwargs):
        user = request.user
        try:
            shipper = Shipper.objects.get(username=user.username)
        except Shipper.DoesNotExist:
            return error_response('当前用户未关联货主账户', code=1002)
        data = request.data.copy()
        data['shipper'] = shipper.shipper_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, message='需求发布成功', http_status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if instance.status != ShippingRequestStatus.PENDING:
            return error_response('当前状态不可修改', code=1003)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, message='更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message='删除成功', http_status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        instance = self.get_object()
        try:
            instance.get_state_machine().transition(
                instance, ShippingRequestStatus.CANCELLED, user=request.user
            )
        except ValueError as e:
            return error_response(str(e), code=1003)
        return success_response(message='需求已取消')

    @action(detail=True, methods=['post'], url_path='confirm-quote')
    def confirm_quote(self, request, pk=None):
        """确认报价 - 将从 QUOTED 变为 ASSIGNED"""
        instance = self.get_object()
        try:
            instance.get_state_machine().transition(
                instance, ShippingRequestStatus.ASSIGNED, user=request.user
            )
        except ValueError as e:
            return error_response(str(e), code=1003)
        return success_response(message='报价已确认,需求已指派')


# ============================================================
# 报价单 (核心业务)
# ============================================================

class QuoteViewSet(viewsets.ModelViewSet):
    queryset = Quote.objects.select_related('request', 'carrier', 'driver').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['request__cargo_name', 'carrier__company_name']
    filterset_fields = ['status', 'quote_type', 'carrier', 'request']
    ordering_fields = ['quote_id', 'amount', 'create_time']
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        action_method = getattr(self, self.action, None)
        if action_method:
            func = action_method.__func__ if hasattr(action_method, '__func__') else action_method
            if hasattr(func, 'permission_classes'):
                return [perm() for perm in func.permission_classes]
            kwargs = getattr(func, 'kwargs', {})
            if 'permission_classes' in kwargs:
                return [perm() for perm in kwargs['permission_classes']]
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        if self.action in ('create', 'update', 'destroy'):
            return [IsCarrier()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'list':
            return QuoteListSerializer
        return QuoteDetailSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        user_role = request.user.role.role_code
        if user_role == 'shipper':
            queryset = queryset.filter(request__shipper__username=request.user.username)
        elif user_role == 'carrier':
            queryset = queryset.filter(carrier__username=request.user.username)
        elif user_role == 'driver':
            queryset = queryset.filter(driver__username=request.user.username)
        elif user_role != 'admin':
            queryset = queryset.none()

        # 按需求ID查询报价时启用缓存
        request_id = request.query_params.get('request')
        if request_id:
            c_key = cache_key('quote', 'request', request_id)
            timeout = settings.CACHE_TIMEOUTS['QUOTE_BY_REQUEST']

            def _fetch():
                qs = queryset.filter(request_id=request_id).only(
                    'quote_id', 'request_id', 'carrier_id', 'driver_id',
                    'amount', 'status', 'quote_type', 'create_time',
                )
                serializer = self.get_serializer(qs, many=True)
                return serializer.data

            data = get_or_set_cache(c_key, _fetch, timeout=timeout)
            return success_response(data)

        # 普通列表查询应用 only() 优化
        queryset = queryset.only(
            'quote_id', 'request_id', 'carrier_id', 'driver_id',
            'amount', 'status', 'quote_type', 'create_time',
        )
        return paginated_response(self, queryset, self.get_serializer_class())

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def create(self, request, *args, **kwargs):
        user = request.user
        try:
            carrier = Carrier.objects.get(username=user.username)
        except Carrier.DoesNotExist:
            return error_response('当前用户未关联承运商账户', code=1002)
        data = request.data.copy()
        data['carrier_id'] = carrier.carrier_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        quote = serializer.save()
        request_obj = quote.request
        try:
            request_obj.get_state_machine().transition(
                request_obj, ShippingRequestStatus.QUOTED, user=request.user
            )
        except ValueError:
            pass
        return success_response(serializer.data, message='报价提交成功', http_status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if instance.status != QuoteStatus.PENDING:
            return error_response('当前状态不可修改', code=1003)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, message='更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message='删除成功', http_status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='accept')
    def accept(self, request, pk=None):
        """货主接受报价"""
        instance = self.get_object()
        try:
            instance.get_state_machine().transition(
                instance, QuoteStatus.ACCEPTED, user=request.user
            )
        except ValueError as e:
            return error_response(str(e), code=1003)
        try:
            request_obj = instance.request
            request_obj.get_state_machine().transition(
                request_obj, ShippingRequestStatus.ASSIGNED, user=request.user
            )
        except ValueError:
            pass
        return success_response(message='报价已接受')

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """货主拒绝报价"""
        instance = self.get_object()
        try:
            instance.get_state_machine().transition(
                instance, QuoteStatus.REJECTED, user=request.user
            )
        except ValueError as e:
            return error_response(str(e), code=1003)
        return success_response(message='报价已拒绝')


# ============================================================
# 运输任务 (核心业务)
# ============================================================

class TransportTaskViewSet(viewsets.ModelViewSet):
    queryset = TransportTask.objects.select_related(
        'request', 'quote', 'carrier', 'driver', 'vehicle'
    ).all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['request__cargo_name', 'current_location']
    filterset_fields = ['task_status', 'payment_status', 'driver', 'carrier']
    ordering_fields = ['task_id']
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        action_method = getattr(self, self.action, None)
        if action_method:
            func = action_method.__func__ if hasattr(action_method, '__func__') else action_method
            # Check for @permission_classes decorator (sets directly)
            if hasattr(func, 'permission_classes'):
                return [perm() for perm in func.permission_classes]
            # Check for @action(permission_classes=...) (stored in kwargs)
            kwargs = getattr(func, 'kwargs', {})
            if 'permission_classes' in kwargs:
                return [perm() for perm in kwargs['permission_classes']]
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get_serializer_class(self):
        if self.action == 'list':
            return TransportTaskListSerializer
        return TransportTaskDetailSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        user_role = request.user.role.role_code
        if user_role == 'shipper':
            queryset = queryset.filter(request__shipper__username=request.user.username)
        elif user_role == 'carrier':
            queryset = queryset.filter(carrier__username=request.user.username)
        elif user_role == 'driver':
            queryset = queryset.filter(driver__username=request.user.username)
        elif user_role != 'admin':
            queryset = queryset.none()
        # 列表查询应用 only() 优化
        queryset = queryset.only(
            'task_id', 'request_id', 'quote_id', 'driver_id', 'carrier_id',
            'task_status', 'payment_status', 'current_location',
        )
        return paginated_response(self, queryset, self.get_serializer_class())

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, message='任务创建成功', http_status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, message='更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message='删除成功', http_status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='assign', permission_classes=[IsCarrier])
    def assign(self, request, pk=None):
        """承运商指派司机 - PENDING -> ASSIGNED"""
        instance = self.get_object()
        driver_id = request.data.get('driver_id')
        vehicle_id = request.data.get('vehicle_id')
        if driver_id:
            instance.driver_id = driver_id
        if vehicle_id:
            instance.vehicle_id = vehicle_id
        instance.save()
        try:
            instance.get_state_machine().transition(
                instance, TaskStatus.ASSIGNED, user=request.user
            )
        except ValueError as e:
            return error_response(str(e), code=1003)
        return success_response(message='任务已指派')

    @action(detail=True, methods=['post'], url_path='accept', permission_classes=[IsDriver])
    def accept(self, request, pk=None):
        """司机接单 - ASSIGNED -> IN_TRANSIT"""
        instance = self.get_object()
        try:
            instance.get_state_machine().transition(
                instance, TaskStatus.IN_TRANSIT, user=request.user
            )
        except ValueError as e:
            return error_response(str(e), code=1003)
        request_obj = instance.request
        try:
            request_obj.get_state_machine().transition(
                request_obj, ShippingRequestStatus.IN_TRANSIT, user=request.user
            )
        except ValueError:
            pass
        return success_response(message='任务已接单,运输中')

    @action(detail=True, methods=['post'], url_path='deliver', permission_classes=[IsDriver])
    def deliver(self, request, pk=None):
        """司机送达 - IN_TRANSIT -> DELIVERED"""
        instance = self.get_object()
        try:
            instance.get_state_machine().transition(
                instance, TaskStatus.DELIVERED, user=request.user
            )
        except ValueError as e:
            return error_response(str(e), code=1003)
        return success_response(message='已送达,等待确认')

    @action(detail=True, methods=['post'], url_path='complete', permission_classes=[IsShipper])
    def complete(self, request, pk=None):
        """货主确认完成 - DELIVERED -> COMPLETED"""
        instance = self.get_object()
        try:
            instance.get_state_machine().transition(
                instance, TaskStatus.COMPLETED, user=request.user
            )
        except ValueError as e:
            return error_response(str(e), code=1003)
        request_obj = instance.request
        try:
            request_obj.get_state_machine().transition(
                request_obj, ShippingRequestStatus.COMPLETED, user=request.user
            )
        except ValueError:
            pass
        quote = instance.quote
        try:
            quote.get_state_machine().transition(
                quote, QuoteStatus.EXPIRED, user=request.user
            )
        except ValueError:
            pass
        return success_response(message='任务已完成')

    @action(detail=True, methods=['post'], url_path='cancel', permission_classes=[IsCarrier])
    def cancel(self, request, pk=None):
        """取消任务"""
        instance = self.get_object()
        try:
            instance.get_state_machine().transition(
                instance, TaskStatus.CANCELLED, user=request.user
            )
        except ValueError as e:
            return error_response(str(e), code=1003)
        return success_response(message='任务已取消')

    @action(detail=True, methods=['put'], url_path='location', permission_classes=[IsDriver])
    def update_location(self, request, pk=None):
        """司机更新位置 — 使用异步任务"""
        instance = self.get_object()

        location = request.data.get('current_location')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')

        # 同步更新当前位置（保证前端立即看到最新数据）
        if location:
            instance.current_location = location
        if latitude:
            instance.latitude = latitude
        if longitude:
            instance.longitude = longitude
        instance.save(update_fields=['current_location', 'latitude', 'longitude'])

        # 异步上报（供后端日志/分析使用）
        try:
            from core.models import Driver
            driver = Driver.objects.filter(username=request.user.username).first()
            driver_id = driver.driver_id if driver else None
            from core.tasks import task_update_location
            task_update_location.delay(
                driver_id=driver_id or 0,
                lat=float(latitude) if latitude else 0,
                lng=float(longitude) if longitude else 0,
                task_id=instance.task_id,
            )
        except Exception as e:
            logger.warning('位置异步上报失败: %s', e)

        return success_response(message='位置已更新')

    @action(detail=True, methods=['post'], url_path='report-anomaly', permission_classes=[IsDriver])
    def report_anomaly(self, request, pk=None):
        """司机上报运输异常（事故、堵车等）"""
        instance = self.get_object()
        description = request.data.get('description', '')
        anomaly_type = request.data.get('type', 'accident')

        if not description:
            return error_response('异常描述不能为空', code=1004)

        # 异步处理异常上报
        try:
            from core.tasks import task_report_anomaly
            task_report_anomaly.delay(
                task_id=instance.task_id,
                description=description,
                type=anomaly_type,
            )
        except Exception as e:
            logger.warning('异常上报异步任务创建失败: %s', e)

        return success_response(message='异常已上报，正在处理')

    @action(detail=True, methods=['post'], url_path='confirm-payment', permission_classes=[IsShipper])
    def confirm_payment(self, request, pk=None):
        """货主确认付款"""
        instance = self.get_object()
        instance.payment_status = PaymentStatus.PAID
        instance.save()
        return success_response(message='付款已确认')


# ============================================================
# 状态日志
# ============================================================

class StateLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StateLog.objects.select_related('content_type').all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['content_type', 'changed_by']

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'list':
            return StateLogListSerializer
        return StateLogDetailSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return paginated_response(self, queryset, self.get_serializer_class())

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)


# ============================================================
# 装车推荐 API（二维装箱算法）
# ============================================================

class LoadingPlanViewSet(viewsets.ViewSet):
    """
    装车推荐 API

    POST /api/loading-plan/generate/ → 异步生成装车方案，返回 task_id
    GET  /api/loading-plan/result/{task_id}/ → 查询任务结果
    """
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=['post'], url_path='generate')
    def generate(self, request):
        """
        异步生成装车方案

        Request: {
            "cargo_ids": [1, 2, 3],
            "vehicle_id": 1
        }
        """
        cargo_ids = request.data.get('cargo_ids', [])
        vehicle_id = request.data.get('vehicle_id')

        if not cargo_ids:
            return error_response('货物ID列表不能为空', code=1004)
        if not vehicle_id:
            return error_response('车辆ID不能为空', code=1004)

        # 调用 Celery 异步任务
        from core.tasks import task_generate_loading_plan
        try:
            task_result = task_generate_loading_plan.delay(
                cargo_ids=cargo_ids,
                vehicle_id=vehicle_id,
            )
            return success_response({
                'task_id': str(task_result.id),
                'status': 'pending',
            }, message='装车方案生成中，请稍后查询结果')
        except Exception as e:
            logger.error('装车方案任务创建失败: %s', e)
            # 降级：同步调用
            try:
                from core.algorithms.loading_plan import generate_loading_plan
                from core.models import ShippingRequest, Vehicle

                vehicle = Vehicle.objects.filter(vehicle_id=vehicle_id).first()
                if not vehicle:
                    return error_response(f'车辆不存在: {vehicle_id}', code=1004)

                cargo_list = []
                for cid in cargo_ids:
                    req = ShippingRequest.objects.filter(request_id=cid).first()
                    if req:
                        cargo_list.append({
                            'cargo_id': cid,
                            'length': req.cargo_length or 0,
                            'width': req.cargo_width or 0,
                            'height': req.cargo_height or 0,
                            'weight': req.weight or 0,
                        })

                result = generate_loading_plan(cargo_list, {
                    'length': vehicle.length or 0,
                    'width': vehicle.width or 0,
                    'height': vehicle.height or 0,
                    'load_capacity': vehicle.load_capacity or 0,
                })
                return success_response(result, message='装车方案（同步降级）')
            except Exception as e2:
                return error_response(f'装车方案生成失败: {e2}', code=1003)

    @action(detail=True, methods=['get'], url_path='result')
    def result(self, request, pk=None):
        """查询异步任务结果"""
        from celery.result import AsyncResult
        task_id = pk
        try:
            async_result = AsyncResult(task_id)
            data = {
                'task_id': task_id,
                'status': async_result.status,
            }
            if async_result.ready():
                if async_result.successful():
                    data['result'] = async_result.result
                else:
                    data['error'] = str(async_result.result)
            return success_response(data)
        except Exception as e:
            return error_response(f'查询失败: {e}', code=1003)
