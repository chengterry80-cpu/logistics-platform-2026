from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from core.utils.state_machine import Transition


# ============================================================
# 枚举类 - 状态/类型常量
# ============================================================

class UserStatus(models.TextChoices):
    ACTIVE = 'active', '正常'
    DISABLED = 'disabled', '已禁用'


class ShipperStatus(models.TextChoices):
    PENDING = 'pending', '待审核'
    APPROVED = 'approved', '已审核'
    REJECTED = 'rejected', '已拒绝'
    DISABLED = 'disabled', '已禁用'


class CarrierStatus(models.TextChoices):
    PENDING = 'pending', '待审核'
    APPROVED = 'approved', '已审核'
    REJECTED = 'rejected', '已拒绝'
    DISABLED = 'disabled', '已禁用'


class DriverStatus(models.TextChoices):
    PENDING = 'pending', '待审核'
    APPROVED = 'approved', '已审核'
    REJECTED = 'rejected', '已拒绝'
    DISABLED = 'disabled', '已禁用'


class VehicleStatus(models.TextChoices):
    AVAILABLE = 'available', '可接单'
    IN_USE = 'in_use', '运输中'
    MAINTENANCE = 'maintenance', '维护中'
    SCRAPPED = 'scrapped', '已报废'


class VehicleType(models.TextChoices):
    VAN = 'van', '厢式货车'
    TRUCK = 'truck', '平板车'
    REFRIGERATED = 'refrigerated', '冷藏车'
    LORRY = 'lorry', '重型卡车'
    PICKUP = 'pickup', '皮卡'
    OTHER = 'other', '其他'


class ShippingRequestStatus(models.TextChoices):
    PENDING = 'pending', '待报价'
    QUOTED = 'quoted', '已报价'
    ASSIGNED = 'assigned', '已指派'
    IN_TRANSIT = 'in_transit', '运输中'
    COMPLETED = 'completed', '已完成'
    CANCELLED = 'cancelled', '已取消'


class CargoType(models.TextChoices):
    GENERAL = 'general', '普通货物'
    FRAGILE = 'fragile', '易碎品'
    PERISHABLE = 'perishable', '生鲜食品'
    DANGEROUS = 'dangerous', '危险品'
    VALUABLE = 'valuable', '贵重物品'
    LARGE = 'large', '大件货物'
    OTHER = 'other', '其他'


class QuoteStatus(models.TextChoices):
    PENDING = 'pending', '待确认'
    ACCEPTED = 'accepted', '已接受'
    REJECTED = 'rejected', '已拒绝'
    EXPIRED = 'expired', '已过期'


class QuoteType(models.TextChoices):
    FIXED = 'fixed', '固定报价'
    NEGOTIABLE = 'negotiable', '议价报价'
    AUCTION = 'auction', '竞拍报价'


class TaskStatus(models.TextChoices):
    PENDING = 'pending', '待接单'
    ASSIGNED = 'assigned', '已指派'
    IN_TRANSIT = 'in_transit', '运输中'
    DELIVERED = 'delivered', '已送达'
    COMPLETED = 'completed', '已完成'
    CANCELLED = 'cancelled', '已取消'


class PaymentStatus(models.TextChoices):
    UNPAID = 'unpaid', '未支付'
    PAID = 'paid', '已支付'
    REFUNDED = 'refunded', '已退款'


# ============================================================
# 表1: Role 角色表
# ============================================================

class Role(models.Model):
    role_id = models.BigAutoField(primary_key=True)
    role_name = models.CharField(max_length=50, verbose_name='角色名称')
    role_code = models.CharField(max_length=30, unique=True, verbose_name='角色编码')
    description = models.CharField(max_length=200, blank=True, verbose_name='角色描述')

    class Meta:
        db_table = 'role'
        verbose_name = '角色'
        verbose_name_plural = '角色管理'

    def __str__(self):
        return f'{self.role_name}({self.role_code})'


# ============================================================
# 系统用户模型 (用于Django Admin认证)
# 注意：此表为系统基础设施，论文核心业务表为下方8张表
# ============================================================

class User(AbstractUser):
    role = models.ForeignKey(
        Role, on_delete=models.PROTECT,
        related_name='users',
        verbose_name='所属角色'
    )
    status = models.CharField(
        max_length=20, choices=UserStatus.choices,
        default=UserStatus.ACTIVE, verbose_name='账户状态'
    )

    class Meta:
        db_table = 'user'
        verbose_name = '用户'
        verbose_name_plural = '用户管理'

    def __str__(self):
        return f'{self.username} ({self.role.role_name if self.role else "无角色"})'


# ============================================================
# 表2: Shipper 货主表 (论文定义)
# ============================================================

class Shipper(models.Model):
    shipper_id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True, verbose_name='用户名')
    password = models.CharField(max_length=100, verbose_name='密码')
    company_name = models.CharField(max_length=200, verbose_name='公司名称')
    contact_person = models.CharField(max_length=50, verbose_name='联系人')
    phone = models.CharField(max_length=20, verbose_name='联系电话')
    email = models.EmailField(max_length=254, blank=True, verbose_name='电子邮箱')
    status = models.CharField(
        max_length=20, choices=ShipperStatus.choices,
        default=ShipperStatus.PENDING, verbose_name='审核状态'
    )
    reg_time = models.DateTimeField(auto_now_add=True, verbose_name='注册时间')
    last_login_time = models.DateTimeField(null=True, blank=True, verbose_name='最后登录时间')

    class Meta:
        db_table = 'shipper'
        verbose_name = '货主'
        verbose_name_plural = '货主管理'
        ordering = ['-reg_time']

    def __str__(self):
        return f'{self.company_name}(ID:{self.shipper_id})'


# ============================================================
# 表3: Carrier 承运商表 (论文定义)
# ============================================================

class Carrier(models.Model):
    carrier_id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True, verbose_name='用户名')
    password = models.CharField(max_length=100, verbose_name='密码')
    company_name = models.CharField(max_length=200, verbose_name='公司名称')
    qualification = models.CharField(max_length=500, verbose_name='资质信息')
    credit_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=100.00,
        verbose_name='信用评分'
    )
    phone = models.CharField(max_length=20, verbose_name='联系电话')
    status = models.CharField(
        max_length=20, choices=CarrierStatus.choices,
        default=CarrierStatus.PENDING, verbose_name='审核状态'
    )
    reg_time = models.DateTimeField(auto_now_add=True, verbose_name='注册时间')
    total_orders = models.IntegerField(default=0, verbose_name='累计订单数')

    class Meta:
        db_table = 'carrier'
        verbose_name = '承运商'
        verbose_name_plural = '承运商管理'
        ordering = ['-reg_time']

    def __str__(self):
        return f'{self.company_name}(ID:{self.carrier_id})'


# ============================================================
# 表4: Driver 司机表 (论文定义)
# ============================================================

class Driver(models.Model):
    driver_id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True, verbose_name='用户名')
    password = models.CharField(max_length=100, verbose_name='密码')
    name = models.CharField(max_length=50, verbose_name='真实姓名')
    license_no = models.CharField(max_length=50, verbose_name='驾照编号')
    phone = models.CharField(max_length=20, verbose_name='联系电话')
    id_card = models.CharField(max_length=18, verbose_name='身份证号')
    status = models.CharField(
        max_length=20, choices=DriverStatus.choices,
        default=DriverStatus.PENDING, verbose_name='审核状态'
    )
    reg_time = models.DateTimeField(auto_now_add=True, verbose_name='注册时间')
    current_location = models.CharField(max_length=200, blank=True, default='', verbose_name='当前位置')

    class Meta:
        db_table = 'driver'
        verbose_name = '司机'
        verbose_name_plural = '司机管理'
        ordering = ['-reg_time']

    def __str__(self):
        return f'{self.name}(ID:{self.driver_id})'


# ============================================================
# 表5: Vehicle 运力档案表 (论文定义)
# ============================================================

class Vehicle(models.Model):
    vehicle_id = models.BigAutoField(primary_key=True)
    driver = models.ForeignKey(
        Driver, on_delete=models.PROTECT,
        related_name='vehicles',
        verbose_name='所属司机'
    )
    plate_number = models.CharField(max_length=20, unique=True, verbose_name='车牌号')
    vehicle_type = models.CharField(
        max_length=30, choices=VehicleType.choices,
        default=VehicleType.VAN, verbose_name='车型'
    )
    load_capacity = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='载重(吨)'
    )
    vehicle_length = models.DecimalField(
        max_digits=8, decimal_places=2,
        verbose_name='车长(米)'
    )
    vehicle_width = models.DecimalField(
        max_digits=8, decimal_places=2,
        verbose_name='车宽(米)'
    )
    vehicle_height = models.DecimalField(
        max_digits=8, decimal_places=2,
        verbose_name='车高(米)'
    )
    status = models.CharField(
        max_length=20, choices=VehicleStatus.choices,
        default=VehicleStatus.AVAILABLE, verbose_name='车辆状态'
    )
    is_online = models.BooleanField(default=True, verbose_name='是否在线')

    class Meta:
        db_table = 'vehicle'
        verbose_name = '车辆'
        verbose_name_plural = '车辆管理'

    def __str__(self):
        return f'{self.plate_number}({self.get_vehicle_type_display()})'

    @property
    def volume(self):
        return (self.vehicle_length * self.vehicle_width * self.vehicle_height)


# ============================================================
# 表6: ShippingRequest 运输需求表 (论文定义)
# ============================================================

class ShippingRequest(models.Model):
    request_id = models.BigAutoField(primary_key=True)
    shipper = models.ForeignKey(
        Shipper, on_delete=models.CASCADE,
        related_name='shipping_requests',
        verbose_name='货主'
    )
    cargo_type = models.CharField(
        max_length=30, choices=CargoType.choices,
        default=CargoType.GENERAL, verbose_name='货物类型'
    )
    cargo_name = models.CharField(max_length=200, verbose_name='货物名称')
    weight = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='重量(吨)'
    )
    volume = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='体积(立方米)'
    )
    cargo_length = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        verbose_name='货长(米)'
    )
    cargo_width = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        verbose_name='货宽(米)'
    )
    cargo_height = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        verbose_name='货高(米)'
    )
    origin = models.CharField(max_length=200, verbose_name='始发地')
    destination = models.CharField(max_length=200, verbose_name='目的地')
    expected_time = models.DateTimeField(verbose_name='期望送达时间')
    status = models.CharField(
        max_length=20, choices=ShippingRequestStatus.choices,
        default=ShippingRequestStatus.PENDING, verbose_name='需求状态'
    )

    class Meta:
        db_table = 'shipping_request'
        verbose_name = '运输需求'
        verbose_name_plural = '运输需求管理'
        ordering = ['-request_id']

    def __str__(self):
        return f'#{self.request_id} {self.cargo_name} ({self.origin} → {self.destination})'

    def get_state_field(self):
        return 'status'

    def get_state_machine(self):
        return Transition({
            ShippingRequestStatus.PENDING: [
                ShippingRequestStatus.QUOTED,
                ShippingRequestStatus.CANCELLED,
            ],
            ShippingRequestStatus.QUOTED: [
                ShippingRequestStatus.ASSIGNED,
                ShippingRequestStatus.CANCELLED,
            ],
            ShippingRequestStatus.ASSIGNED: [
                ShippingRequestStatus.IN_TRANSIT,
                ShippingRequestStatus.CANCELLED,
            ],
            ShippingRequestStatus.IN_TRANSIT: [
                ShippingRequestStatus.COMPLETED,
            ],
        })


# ============================================================
# 表7: Quote 报价单表 (论文定义)
# ============================================================

class Quote(models.Model):
    quote_id = models.BigAutoField(primary_key=True)
    request = models.ForeignKey(
        ShippingRequest, on_delete=models.CASCADE,
        related_name='quotes',
        verbose_name='运输需求'
    )
    carrier = models.ForeignKey(
        Carrier, on_delete=models.CASCADE,
        related_name='quotes',
        verbose_name='承运商'
    )
    driver = models.ForeignKey(
        Driver, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='quotes',
        verbose_name='指定司机'
    )
    quote_type = models.CharField(
        max_length=20, choices=QuoteType.choices,
        default=QuoteType.FIXED, verbose_name='报价类型'
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='报价金额'
    )
    currency = models.CharField(max_length=10, default='CNY', verbose_name='货币')
    status = models.CharField(
        max_length=20, choices=QuoteStatus.choices,
        default=QuoteStatus.PENDING, verbose_name='报价状态'
    )
    validity_period = models.DateTimeField(verbose_name='有效期截止时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'quote'
        verbose_name = '报价单'
        verbose_name_plural = '报价单管理'
        ordering = ['-create_time']

    def __str__(self):
        return f'#{self.quote_id} ¥{self.amount} ({self.carrier})'

    def get_state_field(self):
        return 'status'

    def get_state_machine(self):
        return Transition({
            QuoteStatus.PENDING: [
                QuoteStatus.ACCEPTED,
                QuoteStatus.REJECTED,
                QuoteStatus.EXPIRED,
            ],
        })

    @property
    def is_valid(self):
        return timezone.now() < self.validity_period and self.status == QuoteStatus.PENDING


# ============================================================
# 表8: TransportTask 运输任务表 (论文定义)
# ============================================================

class TransportTask(models.Model):
    task_id = models.BigAutoField(primary_key=True)
    request = models.OneToOneField(
        ShippingRequest, on_delete=models.CASCADE,
        related_name='transport_task',
        verbose_name='运输需求'
    )
    quote = models.OneToOneField(
        Quote, on_delete=models.CASCADE,
        related_name='transport_task',
        verbose_name='关联报价单'
    )
    carrier = models.ForeignKey(
        Carrier, on_delete=models.CASCADE,
        related_name='transport_tasks',
        verbose_name='承运商'
    )
    driver = models.ForeignKey(
        Driver, on_delete=models.CASCADE,
        related_name='transport_tasks',
        verbose_name='司机'
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE,
        related_name='transport_tasks',
        verbose_name='运输车辆'
    )
    task_status = models.CharField(
        max_length=20, choices=TaskStatus.choices,
        default=TaskStatus.PENDING, verbose_name='任务状态'
    )
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID, verbose_name='货主付款状态'
    )
    driver_payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID, verbose_name='司机结算状态'
    )
    current_location = models.CharField(max_length=200, blank=True, default='', verbose_name='当前位置')
    latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True, verbose_name='纬度')
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True, verbose_name='经度')

    class Meta:
        db_table = 'transport_task'
        verbose_name = '运输任务'
        verbose_name_plural = '运输任务管理'
        ordering = ['-task_id']

    def __str__(self):
        return f'#{self.task_id} [{self.get_task_status_display()}] ({self.driver})'

    def get_state_field(self):
        return 'task_status'

    def get_state_machine(self):
        return Transition({
            TaskStatus.PENDING: [
                TaskStatus.ASSIGNED,
                TaskStatus.CANCELLED,
            ],
            TaskStatus.ASSIGNED: [
                TaskStatus.IN_TRANSIT,
                TaskStatus.CANCELLED,
            ],
            TaskStatus.IN_TRANSIT: [
                TaskStatus.DELIVERED,
            ],
            TaskStatus.DELIVERED: [
                TaskStatus.COMPLETED,
            ],
        })


# ============================================================
# 表9: StateLog 状态变更日志表 (通用外键)
# ============================================================

class StateLog(models.Model):
    log_id = models.BigAutoField(primary_key=True)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        verbose_name='关联模型类型'
    )
    object_id = models.PositiveIntegerField(verbose_name='关联对象ID')
    content_object = GenericForeignKey('content_type', 'object_id')
    old_status = models.CharField(max_length=50, verbose_name='变更前状态')
    new_status = models.CharField(max_length=50, verbose_name='变更后状态')
    changed_by = models.CharField(max_length=100, blank=True, default='', verbose_name='操作人')
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name='变更时间')
    remark = models.CharField(max_length=500, blank=True, default='', verbose_name='备注')

    class Meta:
        db_table = 'state_log'
        verbose_name = '状态变更日志'
        verbose_name_plural = '状态变更日志管理'
        ordering = ['-changed_at']

    def __str__(self):
        return f'#{self.log_id} {self.content_type} #{self.object_id}: {self.old_status} → {self.new_status}'
