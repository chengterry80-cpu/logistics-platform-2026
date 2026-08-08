from rest_framework import serializers

from core.models import (
    User, Role,
    Shipper, Carrier, Driver, Vehicle,
    ShippingRequest, Quote, TransportTask, StateLog,
)


# ============================================================
# 工具函数 - 字段脱敏
# ============================================================

def mask_phone(phone):
    """手机号脱敏: 13800138001 -> 138****8001"""
    if not phone or len(phone) < 7:
        return phone
    return phone[:3] + '****' + phone[-4:]


def mask_id_card(id_card):
    """身份证脱敏: 110101198001010011 -> 110**********0011"""
    if not id_card or len(id_card) < 6:
        return id_card
    return id_card[:3] + '*' * (len(id_card) - 7) + id_card[-4:]


def mask_license(license_no):
    """驾照号脱敏"""
    if not license_no or len(license_no) < 4:
        return license_no
    return license_no[:2] + '****' + license_no[-2:]


# ============================================================
# 认证相关
# ============================================================

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    role_code = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'role_code', 'email')

    def validate_role_code(self, value):
        if not Role.objects.filter(role_code=value).exists():
            raise serializers.ValidationError(f'角色 {value} 不存在')
        return value

    def create(self, validated_data):
        role_code = validated_data.pop('role_code')
        role = Role.objects.get(role_code=role_code)
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
            role=role,
        )
        return user


class UserListSerializer(serializers.ModelSerializer):
    """用户列表 - 精简字段，不含敏感信息"""
    role_name = serializers.CharField(source='role.role_name', read_only=True)
    role_code = serializers.CharField(source='role.role_code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    full_name = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'role', 'role_name', 'role_code',
            'status', 'status_display', 'full_name', 'phone', 'last_login',
        )

    def get_full_name(self, user):
        """合并关联档案的名称"""
        if user.role.role_code == 'shipper':
            shipper = Shipper.objects.filter(username=user.username).first()
            return shipper.company_name if shipper else ''
        elif user.role.role_code == 'carrier':
            carrier = Carrier.objects.filter(username=user.username).first()
            return carrier.company_name if carrier else ''
        elif user.role.role_code == 'driver':
            driver = Driver.objects.filter(username=user.username).first()
            return driver.name if driver else ''
        return f'{user.first_name} {user.last_name}'.strip()

    def get_phone(self, user):
        """从关联档案获取手机号（脱敏）"""
        if user.role.role_code == 'shipper':
            s = Shipper.objects.filter(username=user.username).first()
            return mask_phone(s.phone) if s else ''
        elif user.role.role_code == 'carrier':
            c = Carrier.objects.filter(username=user.username).first()
            return mask_phone(c.phone) if c else ''
        elif user.role.role_code == 'driver':
            d = Driver.objects.filter(username=user.username).first()
            return mask_phone(d.phone) if d else ''
        return ''


class UserDetailSerializer(serializers.ModelSerializer):
    """用户详情 - 包含关联档案，密码 hash 不暴露"""
    role_name = serializers.CharField(source='role.role_name', read_only=True)
    role_code = serializers.CharField(source='role.role_code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    shipper = serializers.SerializerMethodField()
    carrier = serializers.SerializerMethodField()
    driver = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_name', 'role_code', 'status', 'status_display',
            'is_active', 'date_joined', 'last_login',
            'shipper', 'carrier', 'driver',
        )
        read_only_fields = ('date_joined', 'last_login')

    def get_shipper(self, user):
        if user.role.role_code != 'shipper':
            return None
        shipper = Shipper.objects.filter(username=user.username).first()
        return ShipperDetailSerializer(shipper).data if shipper else None

    def get_carrier(self, user):
        if user.role.role_code != 'carrier':
            return None
        carrier = Carrier.objects.filter(username=user.username).first()
        return CarrierDetailSerializer(carrier).data if carrier else None

    def get_driver(self, user):
        if user.role.role_code != 'driver':
            return None
        driver = Driver.objects.filter(username=user.username).first()
        return DriverDetailSerializer(driver).data if driver else None


# ============================================================
# 货主 / 承运商 / 司机 - 列表(脱敏) / 详情(完整) 分离
# ============================================================

class ShipperListSerializer(serializers.ModelSerializer):
    """货主列表 - 脱敏手机号，精简字段"""
    phone = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Shipper
        fields = ('shipper_id', 'username', 'company_name', 'contact_person', 'phone', 'status', 'status_display')

    def get_phone(self, obj):
        return mask_phone(obj.phone)


class ShipperDetailSerializer(serializers.ModelSerializer):
    """货主详情 - 完整信息（不含 password 字段）"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Shipper
        fields = (
            'shipper_id', 'username', 'company_name', 'contact_person',
            'phone', 'email', 'status', 'status_display', 'reg_time', 'last_login_time',
        )
        read_only_fields = ('reg_time', 'last_login_time')


class CarrierListSerializer(serializers.ModelSerializer):
    """承运商列表 - 精简字段"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Carrier
        fields = ('carrier_id', 'username', 'company_name', 'credit_score', 'status', 'status_display')


class CarrierDetailSerializer(serializers.ModelSerializer):
    """承运商详情 - 完整信息"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    phone = serializers.SerializerMethodField()

    class Meta:
        model = Carrier
        fields = (
            'carrier_id', 'username', 'company_name', 'qualification',
            'credit_score', 'phone', 'status', 'status_display', 'reg_time', 'total_orders',
        )
        read_only_fields = ('reg_time',)

    def get_phone(self, obj):
        return mask_phone(obj.phone)


class DriverListSerializer(serializers.ModelSerializer):
    """司机列表 - 脱敏手机号，不含身份证/驾照号"""
    phone = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Driver
        fields = ('driver_id', 'username', 'name', 'phone', 'status', 'status_display', 'current_location')

    def get_phone(self, obj):
        return mask_phone(obj.phone)


class DriverDetailSerializer(serializers.ModelSerializer):
    """司机详情 - 身份证/驾照号脱敏"""
    phone = serializers.SerializerMethodField()
    id_card = serializers.SerializerMethodField()
    license_no = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Driver
        fields = (
            'driver_id', 'username', 'name', 'license_no',
            'phone', 'id_card', 'status', 'status_display', 'reg_time', 'current_location',
        )
        read_only_fields = ('reg_time',)

    def get_phone(self, obj):
        return mask_phone(obj.phone)

    def get_id_card(self, obj):
        return mask_id_card(obj.id_card)

    def get_license_no(self, obj):
        return mask_license(obj.license_no)


# ============================================================
# 车辆
# ============================================================

class VehicleListSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.name', read_only=True)
    vehicle_type_display = serializers.CharField(source='get_vehicle_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Vehicle
        fields = (
            'vehicle_id', 'plate_number', 'vehicle_type', 'vehicle_type_display',
            'load_capacity', 'status', 'status_display', 'is_online', 'driver_name',
        )


class VehicleDetailSerializer(serializers.ModelSerializer):
    driver = DriverListSerializer(read_only=True)
    driver_id = serializers.PrimaryKeyRelatedField(
        queryset=Driver.objects.all(), source='driver', write_only=True
    )
    vehicle_type_display = serializers.CharField(source='get_vehicle_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    volume = serializers.ReadOnlyField()

    class Meta:
        model = Vehicle
        fields = (
            'vehicle_id', 'plate_number', 'vehicle_type', 'vehicle_type_display',
            'load_capacity', 'vehicle_length', 'vehicle_width', 'vehicle_height', 'volume',
            'status', 'status_display', 'is_online', 'driver', 'driver_id',
        )


# ============================================================
# 运输需求
# ============================================================

class ShippingRequestListSerializer(serializers.ModelSerializer):
    """需求列表 - 精简字段 + display 字段"""
    shipper_name = serializers.CharField(source='shipper.company_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    cargo_type_display = serializers.CharField(source='get_cargo_type_display', read_only=True)

    class Meta:
        model = ShippingRequest
        fields = (
            'request_id', 'cargo_name', 'cargo_type', 'cargo_type_display',
            'origin', 'destination', 'status', 'status_display',
            'shipper_name', 'weight', 'volume', 'expected_time',
        )


class ShippingRequestDetailSerializer(serializers.ModelSerializer):
    """需求详情 - 含完整尺寸信息和报价数"""
    shipper = ShipperListSerializer(read_only=True)
    shipper_id = serializers.PrimaryKeyRelatedField(
        queryset=Shipper.objects.all(), source='shipper', write_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    cargo_type_display = serializers.CharField(source='get_cargo_type_display', read_only=True)
    quotes_count = serializers.SerializerMethodField()

    class Meta:
        model = ShippingRequest
        fields = (
            'request_id', 'shipper', 'shipper_id',
            'cargo_type', 'cargo_type_display', 'cargo_name',
            'weight', 'volume',
            'cargo_length', 'cargo_width', 'cargo_height',
            'origin', 'destination', 'expected_time',
            'status', 'status_display', 'quotes_count',
        )

    def get_quotes_count(self, obj):
        return obj.quotes.count()


class ShippingRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingRequest
        fields = (
            'request_id', 'shipper', 'cargo_type', 'cargo_name',
            'weight', 'volume', 'cargo_length', 'cargo_width', 'cargo_height',
            'origin', 'destination', 'expected_time',
        )

    def validate(self, attrs):
        if attrs.get('weight', 0) <= 0:
            raise serializers.ValidationError({'weight': '重量必须大于0'})
        return attrs


# ============================================================
# 报价单
# ============================================================

class QuoteListSerializer(serializers.ModelSerializer):
    """报价列表 - 精简 + display"""
    carrier_name = serializers.CharField(source='carrier.company_name', read_only=True)
    request_cargo = serializers.CharField(source='request.cargo_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    quote_type_display = serializers.CharField(source='get_quote_type_display', read_only=True)

    class Meta:
        model = Quote
        fields = (
            'quote_id', 'request', 'request_cargo', 'carrier', 'carrier_name',
            'amount', 'status', 'status_display', 'quote_type', 'quote_type_display',
            'validity_period', 'create_time',
        )


class QuoteDetailSerializer(serializers.ModelSerializer):
    """报价详情 - 含关联对象"""
    request = ShippingRequestListSerializer(read_only=True)
    carrier = CarrierListSerializer(read_only=True)
    driver = DriverListSerializer(read_only=True)
    request_id = serializers.PrimaryKeyRelatedField(
        queryset=ShippingRequest.objects.all(), source='request', write_only=True
    )
    carrier_id = serializers.PrimaryKeyRelatedField(
        queryset=Carrier.objects.all(), source='carrier', write_only=True
    )
    driver_id = serializers.PrimaryKeyRelatedField(
        queryset=Driver.objects.all(), source='driver', write_only=True,
        required=False, allow_null=True,
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    quote_type_display = serializers.CharField(source='get_quote_type_display', read_only=True)

    class Meta:
        model = Quote
        fields = (
            'quote_id', 'request', 'request_id',
            'carrier', 'carrier_id', 'driver', 'driver_id',
            'quote_type', 'quote_type_display', 'amount', 'currency',
            'status', 'status_display',
            'validity_period', 'create_time',
        )
        read_only_fields = ('create_time',)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('报价金额必须大于0')
        return value


# ============================================================
# 运输任务
# ============================================================

class TransportTaskListSerializer(serializers.ModelSerializer):
    """任务列表 - 精简 + display"""
    driver_name = serializers.CharField(source='driver.name', read_only=True)
    carrier_name = serializers.CharField(source='carrier.company_name', read_only=True)
    vehicle_plate = serializers.CharField(source='vehicle.plate_number', read_only=True)
    task_status_display = serializers.CharField(source='get_task_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    cargo_name = serializers.CharField(source='request.cargo_name', read_only=True)
    origin = serializers.CharField(source='request.origin', read_only=True)
    destination = serializers.CharField(source='request.destination', read_only=True)

    class Meta:
        model = TransportTask
        fields = (
            'task_id', 'request', 'quote',
            'driver', 'driver_name', 'carrier', 'carrier_name', 'vehicle_plate',
            'task_status', 'task_status_display',
            'payment_status', 'payment_status_display',
            'current_location', 'cargo_name', 'origin', 'destination',
        )


class TransportTaskDetailSerializer(serializers.ModelSerializer):
    """任务详情 - 含关联对象完整信息"""
    request = ShippingRequestListSerializer(read_only=True)
    quote = QuoteListSerializer(read_only=True)
    carrier = CarrierListSerializer(read_only=True)
    driver = DriverListSerializer(read_only=True)
    vehicle = VehicleListSerializer(read_only=True)
    request_id = serializers.PrimaryKeyRelatedField(
        queryset=ShippingRequest.objects.all(), source='request', write_only=True
    )
    quote_id = serializers.PrimaryKeyRelatedField(
        queryset=Quote.objects.all(), source='quote', write_only=True
    )
    carrier_id = serializers.PrimaryKeyRelatedField(
        queryset=Carrier.objects.all(), source='carrier', write_only=True
    )
    driver_id = serializers.PrimaryKeyRelatedField(
        queryset=Driver.objects.all(), source='driver', write_only=True
    )
    vehicle_id = serializers.PrimaryKeyRelatedField(
        queryset=Vehicle.objects.all(), source='vehicle', write_only=True
    )
    task_status_display = serializers.CharField(source='get_task_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    driver_payment_status_display = serializers.CharField(
        source='get_driver_payment_status_display', read_only=True
    )

    class Meta:
        model = TransportTask
        fields = (
            'task_id', 'request', 'request_id', 'quote', 'quote_id',
            'carrier', 'carrier_id', 'driver', 'driver_id',
            'vehicle', 'vehicle_id',
            'task_status', 'task_status_display',
            'payment_status', 'payment_status_display',
            'driver_payment_status', 'driver_payment_status_display',
            'current_location', 'latitude', 'longitude',
        )


# ============================================================
# 状态日志
# ============================================================

class StateLogListSerializer(serializers.ModelSerializer):
    """状态日志列表 - 友好字段名"""
    object_type = serializers.CharField(source='content_object.__class__.__name__', read_only=True)
    model_name = serializers.SerializerMethodField()

    class Meta:
        model = StateLog
        fields = (
            'log_id', 'content_type', 'object_id', 'object_type', 'model_name',
            'old_status', 'new_status', 'changed_by', 'changed_at', 'remark',
        )

    def get_model_name(self, obj):
        try:
            return obj.content_object.__class__.__name__ if obj.content_object else ''
        except Exception:
            return ''


class StateLogDetailSerializer(serializers.ModelSerializer):
    """状态日志详情 - 显式字段（不使用 __all__）"""
    object_type = serializers.CharField(source='content_object.__class__.__name__', read_only=True)

    class Meta:
        model = StateLog
        fields = (
            'log_id', 'content_type', 'object_id', 'object_type',
            'old_status', 'new_status', 'changed_by', 'changed_at', 'remark',
        )
