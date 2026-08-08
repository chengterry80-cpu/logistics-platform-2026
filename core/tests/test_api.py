from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from core.models import (
    User, Role,
    Shipper, Carrier, Driver, Vehicle,
    ShippingRequest, Quote, TransportTask,
    ShippingRequestStatus, QuoteStatus, TaskStatus,
)


class APITestBase(APITestCase):
    def setUp(self):
        self.admin_role = Role.objects.create(role_name='管理员', role_code='admin')
        self.shipper_role = Role.objects.create(role_name='货主', role_code='shipper')
        self.carrier_role = Role.objects.create(role_name='承运商', role_code='carrier')
        self.driver_role = Role.objects.create(role_name='司机', role_code='driver')

        self.admin_user = User.objects.create_user(
            username='admin', password='admin123',
            role=self.admin_role, email='admin@test.com'
        )
        self.shipper_user = User.objects.create_user(
            username='shipper1', password='shipper123',
            role=self.shipper_role, email='shipper@test.com'
        )
        self.carrier_user = User.objects.create_user(
            username='carrier1', password='carrier123',
            role=self.carrier_role, email='carrier@test.com'
        )
        self.driver_user = User.objects.create_user(
            username='driver1', password='driver123',
            role=self.driver_role, email='driver@test.com'
        )

        self.shipper = Shipper.objects.create(
            username='shipper1', password='sha123',
            company_name='测试货主公司', contact_person='张三',
            phone='13800138000', email='shipper@test.com'
        )
        self.carrier = Carrier.objects.create(
            username='carrier1', password='ca123',
            company_name='测试承运商', qualification='AAA级',
            phone='13900139000'
        )
        self.driver = Driver.objects.create(
            username='driver1', password='dr123',
            name='李四', license_no='DL2024001',
            phone='13700137000', id_card='110101199001011234'
        )
        self.vehicle = Vehicle.objects.create(
            driver=self.driver, plate_number='京A12345',
            vehicle_type='van', load_capacity=5.00,
            vehicle_length=6.00, vehicle_width=2.00, vehicle_height=2.50
        )

        self.client = APIClient()

    def _make_shipping_request(self, **kwargs):
        defaults = {
            'shipper': self.shipper,
            'cargo_type': 'general',
            'cargo_name': '测试货物',
            'weight': 10.00,
            'volume': 20.00,
            'origin': '北京',
            'destination': '上海',
            'expected_time': timezone.now() + timedelta(days=3),
            'status': ShippingRequestStatus.PENDING,
        }
        defaults.update(kwargs)
        return ShippingRequest.objects.create(**defaults)

    def _make_quote(self, shipping_request=None, **kwargs):
        defaults = {
            'request': shipping_request or self._make_shipping_request(),
            'carrier': self.carrier,
            'amount': 3000.00,
            'quote_type': 'fixed',
            'validity_period': timezone.now() + timedelta(days=1),
        }
        defaults.update(kwargs)
        return Quote.objects.create(**defaults)

    def _make_task(self, shipping_request=None, quote=None, **kwargs):
        sr = shipping_request or self._make_shipping_request(status=ShippingRequestStatus.ASSIGNED)
        q = quote or self._make_quote(shipping_request=sr, status=QuoteStatus.ACCEPTED)
        defaults = {
            'request': sr,
            'quote': q,
            'carrier': self.carrier,
            'driver': self.driver,
            'vehicle': self.vehicle,
            'task_status': TaskStatus.PENDING,
        }
        defaults.update(kwargs)
        return TransportTask.objects.create(**defaults)


class AuthAPITest(APITestBase):

    def test_register_success(self):
        data = {'username': 'newuser', 'password': 'newpass123', 'role_code': 'shipper', 'email': 'new@test.com'}
        resp = self.client.post('/api/auth/register/', data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['data']['role'], 'shipper')

    def test_register_invalid_role(self):
        data = {'username': 'newuser2', 'password': 'newpass123', 'role_code': 'invalid'}
        resp = self.client.post('/api/auth/register/', data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_obtain_token(self):
        resp = self.client.post('/api/token/', {'username': 'admin', 'password': 'admin123'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)

    def test_me_authenticated(self):
        self.client.force_authenticate(user=self.admin_user)
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['data']['username'], 'admin')


class ShippingRequestAPITest(APITestBase):

    def test_shipper_create_request(self):
        self.client.force_authenticate(user=self.shipper_user)
        resp = self.client.post('/api/shipping-requests/', {
            'cargo_type': 'general', 'cargo_name': '测试货物',
            'weight': 10.00, 'volume': 20.00,
            'origin': '北京', 'destination': '上海',
            'expected_time': (timezone.now() + timedelta(days=3)).isoformat(),
            'shipper': self.shipper.shipper_id,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_shipper_list_own_requests(self):
        self.client.force_authenticate(user=self.shipper_user)
        self._make_shipping_request(cargo_name='我的货物', status=ShippingRequestStatus.PENDING)
        resp = self.client.get('/api/shipping-requests/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['code'], 0)

    def test_carrier_list_available_requests(self):
        self.client.force_authenticate(user=self.carrier_user)
        self._make_shipping_request(cargo_name='待报价货物', status=ShippingRequestStatus.PENDING)
        resp = self.client.get('/api/shipping-requests/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['code'], 0)

    def test_shipper_cancel_request(self):
        self.client.force_authenticate(user=self.shipper_user)
        req = self._make_shipping_request(status=ShippingRequestStatus.PENDING)
        resp = self.client.post(f'/api/shipping-requests/{req.request_id}/cancel/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertEqual(req.status, ShippingRequestStatus.CANCELLED)

    def test_cancel_from_quoted(self):
        self.client.force_authenticate(user=self.shipper_user)
        req = self._make_shipping_request(status=ShippingRequestStatus.QUOTED)
        resp = self.client.post(f'/api/shipping-requests/{req.request_id}/cancel/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertEqual(req.status, ShippingRequestStatus.CANCELLED)

    def test_cancel_completed_fails(self):
        self.client.force_authenticate(user=self.shipper_user)
        req = self._make_shipping_request(status=ShippingRequestStatus.COMPLETED)
        resp = self.client.post(f'/api/shipping-requests/{req.request_id}/cancel/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class QuoteAPITest(APITestBase):

    def test_carrier_create_quote(self):
        sr = self._make_shipping_request(status=ShippingRequestStatus.PENDING)
        self.client.force_authenticate(user=self.carrier_user)
        resp = self.client.post('/api/quotes/', {
            'request_id': sr.request_id,
            'amount': 3000.00,
            'quote_type': 'fixed',
            'validity_period': (timezone.now() + timedelta(days=1)).isoformat(),
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        sr.refresh_from_db()
        self.assertEqual(sr.status, ShippingRequestStatus.QUOTED)

    def test_shipper_accept_quote(self):
        sr = self._make_shipping_request(status=ShippingRequestStatus.QUOTED)
        quote = self._make_quote(shipping_request=sr, status=QuoteStatus.PENDING)
        self.client.force_authenticate(user=self.shipper_user)
        resp = self.client.post(f'/api/quotes/{quote.quote_id}/accept/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        quote.refresh_from_db()
        self.assertEqual(quote.status, QuoteStatus.ACCEPTED)
        sr.refresh_from_db()
        self.assertEqual(sr.status, ShippingRequestStatus.ASSIGNED)

    def test_shipper_reject_quote(self):
        sr = self._make_shipping_request()
        quote = self._make_quote(shipping_request=sr)
        self.client.force_authenticate(user=self.shipper_user)
        resp = self.client.post(f'/api/quotes/{quote.quote_id}/reject/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        quote.refresh_from_db()
        self.assertEqual(quote.status, QuoteStatus.REJECTED)


class TransportTaskAPITest(APITestBase):

    def test_carrier_assign_task(self):
        task = self._make_task(task_status=TaskStatus.PENDING)
        self.client.force_authenticate(user=self.carrier_user)
        resp = self.client.post(f'/api/transport-tasks/{task.task_id}/assign/', {
            'driver_id': self.driver.driver_id,
            'vehicle_id': self.vehicle.vehicle_id,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.task_status, TaskStatus.ASSIGNED)

    def test_driver_accept_task(self):
        task = self._make_task(task_status=TaskStatus.ASSIGNED)
        self.client.force_authenticate(user=self.driver_user)
        resp = self.client.post(f'/api/transport-tasks/{task.task_id}/accept/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.task_status, TaskStatus.IN_TRANSIT)

    def test_driver_deliver_task(self):
        task = self._make_task(task_status=TaskStatus.IN_TRANSIT)
        self.client.force_authenticate(user=self.driver_user)
        resp = self.client.post(f'/api/transport-tasks/{task.task_id}/deliver/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.task_status, TaskStatus.DELIVERED)

    def test_shipper_complete_task(self):
        task = self._make_task(task_status=TaskStatus.DELIVERED)
        self.client.force_authenticate(user=self.shipper_user)
        resp = self.client.post(f'/api/transport-tasks/{task.task_id}/complete/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.task_status, TaskStatus.COMPLETED)

    def test_driver_update_location(self):
        task = self._make_task()
        self.client.force_authenticate(user=self.driver_user)
        resp = self.client.put(f'/api/transport-tasks/{task.task_id}/location/', {
            'current_location': '北京市朝阳区',
            'latitude': '39.9042',
            'longitude': '116.4074',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.current_location, '北京市朝阳区')

    def test_cancel_task(self):
        task = self._make_task(task_status=TaskStatus.PENDING)
        self.client.force_authenticate(user=self.carrier_user)
        resp = self.client.post(f'/api/transport-tasks/{task.task_id}/cancel/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.task_status, TaskStatus.CANCELLED)
