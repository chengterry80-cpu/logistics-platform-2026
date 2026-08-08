"""
初始化测试账号数据命令
用法: python manage.py init_demo_accounts
"""
import sys
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.hashers import make_password

from core.models import (
    Role, User,
    Shipper, Carrier, Driver, Vehicle,
    ShipperStatus, CarrierStatus, DriverStatus, VehicleStatus, VehicleType,
    ShippingRequest, Quote, TransportTask,
    ShippingRequestStatus, QuoteStatus, TaskStatus, PaymentStatus, QuoteType, CargoType,
)


DEMO_PASSWORD = 'logistics123'


def get_or_create_roles():
    roles = [
        ('admin', '平台管理员', '平台超级管理员'),
        ('shipper', '货主', '发布运输需求的企业或个人'),
        ('carrier', '承运商', '提供运输服务的物流公司'),
        ('driver', '司机', '实际执行运输任务的司机'),
    ]
    created_any = False
    for code, name, desc in roles:
        obj, created = Role.objects.get_or_create(
            role_code=code,
            defaults={'role_name': name, 'description': desc}
        )
        if created:
            created_any = True
            print(f'  [+] 创建角色: {code} - {name}')
    return created_any


def create_user(username, role_code, email='', is_staff=False, is_superuser=False):
    role = Role.objects.get(role_code=role_code)
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'role': role,
            'password': make_password(DEMO_PASSWORD),
            'is_active': True,
            'is_staff': is_staff,
            'is_superuser': is_superuser,
        }
    )
    if created:
        print(f'  [+] 创建用户: {username} ({role_code})')
    else:
        # 重置密码，确保演示账号密码一致
        if not user.check_password(DEMO_PASSWORD):
            user.set_password(DEMO_PASSWORD)
            user.role = role
            user.save()
            print(f'  [!] 更新用户密码/角色: {username}')
    return user


class Command(BaseCommand):
    help = '初始化演示账号 (4 个角色 + 业务数据)'

    def handle(self, *args, **options):
        print('=' * 60)
        print('无车承运智能物流平台 - 演示账号初始化')
        print('=' * 60)

        # 1. 角色
        print('\n[1/5] 创建角色表数据...')
        get_or_create_roles()

        # 2. 管理员
        print('\n[2/5] 创建管理员账号...')
        admin = create_user('admin', 'admin', email='admin@demo.com', is_staff=True, is_superuser=True)

        # 3. 货主
        print('\n[3/5] 创建货主账号...')
        shipper_user = create_user('shipper01', 'shipper', email='shipper01@demo.com')
        shipper, _ = Shipper.objects.update_or_create(
            username=shipper_user.username,
            defaults={
                'password': make_password(DEMO_PASSWORD),
                'company_name': '宏达物流商贸有限公司',
                'contact_person': '张经理',
                'phone': '13800138001',
                'email': 'shipper01@demo.com',
                'status': ShipperStatus.APPROVED,
                'last_login_time': timezone.now(),
            }
        )
        print(f'  [+] 货主档案: {shipper.company_name}')

        # 4. 承运商
        print('\n[4/5] 创建承运商 / 司机 / 车辆...')
        carrier_user = create_user('carrier01', 'carrier', email='carrier01@demo.com')
        carrier, _ = Carrier.objects.update_or_create(
            username=carrier_user.username,
            defaults={
                'password': make_password(DEMO_PASSWORD),
                'company_name': '鸿运运输服务有限公司',
                'qualification': '道路运输经营许可证: 110101-000001',
                'credit_score': 98.5,
                'phone': '13900139001',
                'status': CarrierStatus.APPROVED,
                'total_orders': 188,
            }
        )
        print(f'  [+] 承运商档案: {carrier.company_name}')

        # 5. 司机 + 车辆
        drivers_data = [
            {'username': 'driver01', 'name': '王师傅', 'phone': '13700137001',
             'license_no': '110101198001010011', 'id_card': '110101198001010011'},
            {'username': 'driver02', 'name': '李师傅', 'phone': '13700137002',
             'license_no': '110101198502020022', 'id_card': '110101198502020022'},
        ]
        driver_instances = []
        for d in drivers_data:
            create_user(d['username'], 'driver', email=f'{d["username"]}@demo.com')
            driver, _ = Driver.objects.update_or_create(
                username=d['username'],
                defaults={
                    **d,
                    'password': make_password(DEMO_PASSWORD),
                    'status': DriverStatus.APPROVED,
                    'current_location': '北京市海淀区停车场',
                }
            )
            driver_instances.append(driver)
            print(f'  [+] 司机档案: {driver.name} ({driver.username})')

        vehicles_data = [
            {
                'plate_number': '京A88888', 'vehicle_type': VehicleType.VAN,
                'load_capacity': 5, 'vehicle_length': 6.8, 'vehicle_width': 2.4, 'vehicle_height': 2.6,
                'driver_idx': 0,
            },
            {
                'plate_number': '京B66666', 'vehicle_type': VehicleType.TRUCK,
                'load_capacity': 10, 'vehicle_length': 9.6, 'vehicle_width': 2.4, 'vehicle_height': 2.8,
                'driver_idx': 1,
            },
            {
                'plate_number': '京C99999', 'vehicle_type': VehicleType.REFRIGERATED,
                'load_capacity': 8, 'vehicle_length': 7.6, 'vehicle_width': 2.4, 'vehicle_height': 3.0,
                'driver_idx': 0,
            },
        ]
        for v in vehicles_data:
            driver_idx = v.pop('driver_idx')
            Vehicle.objects.update_or_create(
                plate_number=v['plate_number'],
                defaults={
                    **v,
                    'driver': driver_instances[driver_idx],
                    'status': VehicleStatus.AVAILABLE,
                    'is_online': True,
                }
            )
            print(f'  [+] 车辆档案: {v["plate_number"]} ({v["vehicle_type"]})')

        # 6. 创建演示运输需求 + 报价 + 任务
        print('\n[5/5] 创建示例运输需求...')
        requests_data = [
            ('电子产品（手机）', CargoType.GENERAL, 2.5, 12, 1.2, 1.0, 0.8,
             '北京市朝阳区中关村', '上海市浦东新区张江', 3),
            ('服装春装', CargoType.GENERAL, 1.8, 25, 0.8, 0.6, 0.4,
             '广州市白云区', '成都市武侯区', 4),
            ('生鲜水果', CargoType.PERISHABLE, 3.5, 18, 1.0, 0.8, 0.6,
             '深圳市南山区', '武汉市江汉区', 2),
        ]
        created_requests = []
        for name, ctype, weight, vol, cl, cw, ch, origin, dest, days in requests_data:
            sr, _ = ShippingRequest.objects.get_or_create(
                shipper=shipper,
                cargo_name=name,
                origin=origin,
                destination=dest,
                defaults={
                    'cargo_type': ctype,
                    'weight': weight,
                    'volume': vol,
                    'cargo_length': cl,
                    'cargo_width': cw,
                    'cargo_height': ch,
                    'expected_time': timezone.now() + timedelta(days=days),
                    'status': ShippingRequestStatus.PENDING,
                }
            )
            created_requests.append(sr)
            print(f'  [+] 需求: #{sr.request_id} {sr.cargo_name} {origin} → {dest}')

        # 7. 生成报价（第1个需求已报价、已接受、已生成任务）
        if created_requests:
            sr1 = created_requests[0]
            sr1.status = ShippingRequestStatus.ASSIGNED
            sr1.save()
            quote1, _ = Quote.objects.get_or_create(
                request=sr1, carrier=carrier,
                defaults={
                    'quote_type': QuoteType.FIXED,
                    'amount': 2800.00,
                    'currency': 'CNY',
                    'status': QuoteStatus.ACCEPTED,
                    'validity_period': timezone.now() + timedelta(days=30),
                }
            )
            driver1, vehicle1 = driver_instances[0], Vehicle.objects.filter(driver=driver_instances[0]).first()
            task1, _ = TransportTask.objects.get_or_create(
                request=sr1,
                defaults={
                    'quote': quote1,
                    'carrier': carrier,
                    'driver': driver1,
                    'vehicle': vehicle1,
                    'task_status': TaskStatus.IN_TRANSIT,
                    'payment_status': PaymentStatus.UNPAID,
                    'driver_payment_status': PaymentStatus.UNPAID,
                    'current_location': 'G4 高速石家庄段',
                }
            )
            print(f'  [+] 生成报价: #{quote1.quote_id}  ¥{quote1.amount}  [{quote1.get_status_display()}]')
            print(f'  [+] 生成运输任务: #{task1.task_id}  [{task1.get_task_status_display()}]')

            # 第 2 个需求：已报价，等待货主接受
            if len(created_requests) >= 2:
                sr2 = created_requests[1]
                sr2.status = ShippingRequestStatus.QUOTED
                sr2.save()
                Quote.objects.get_or_create(
                    request=sr2, carrier=carrier,
                    defaults={
                        'quote_type': QuoteType.FIXED,
                        'amount': 5600.00,
                        'currency': 'CNY',
                        'status': QuoteStatus.PENDING,
                        'validity_period': timezone.now() + timedelta(days=3),
                    }
                )
                print(f'  [+] 需求 #{sr2.request_id}: 已生成待确认报价')

            # 第 3 个需求：仅待报价（pending）
            if len(created_requests) >= 3:
                print(f'  [*] 需求 #{created_requests[2].request_id}: 待承运商报价')

        print('\n' + '=' * 60)
        print('初始化完成！所有账号统一密码:', DEMO_PASSWORD)
        print()
        print('演示账号列表:')
        print('  - 管理员:   admin        / logistics123')
        print('  - 货主:     shipper01    / logistics123')
        print('  - 承运商:   carrier01    / logistics123')
        print('  - 司机:     driver01     / logistics123')
        print('  - 司机:     driver02     / logistics123')
        print()
        print('Django Admin: /admin/')
        print('后端 API:     /api/')
        print('JWT Token:    /api/token/  |  /api/token/refresh/')
        print('=' * 60)
