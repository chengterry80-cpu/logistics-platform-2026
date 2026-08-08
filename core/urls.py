from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.views import (
    AuthViewSet, UserViewSet,
    ShipperViewSet, CarrierViewSet, DriverViewSet, VehicleViewSet,
    ShippingRequestViewSet, QuoteViewSet, TransportTaskViewSet,
    StateLogViewSet, LoadingPlanViewSet,
)

router = DefaultRouter()

router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'users', UserViewSet, basename='user')
router.register(r'shippers', ShipperViewSet, basename='shipper')
router.register(r'carriers', CarrierViewSet, basename='carrier')
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'shipping-requests', ShippingRequestViewSet, basename='shipping-request')
router.register(r'quotes', QuoteViewSet, basename='quote')
router.register(r'transport-tasks', TransportTaskViewSet, basename='transport-task')
router.register(r'state-logs', StateLogViewSet, basename='state-log')
router.register(r'loading-plan', LoadingPlanViewSet, basename='loading-plan')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
