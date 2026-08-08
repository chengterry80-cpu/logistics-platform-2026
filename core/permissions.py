from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role.role_code == 'admin'
        )


class IsShipper(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role.role_code == 'shipper'
        )


class IsCarrier(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role.role_code == 'carrier'
        )


class IsDriver(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role.role_code == 'driver'
        )


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return request.user and request.user.is_authenticated
        return IsAdmin().has_permission(request, view)


class IsOwnerOrAdmin(BasePermission):
    """对象级权限: 货主只能操作自己的需求, 承运商只能操作自己的报价等"""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.role.role_code == 'admin':
            return True
        owner_field = getattr(view, 'owner_field', None)
        if owner_field and hasattr(obj, owner_field):
            owner = getattr(obj, owner_field)
            if hasattr(owner, 'username'):
                return owner.username == request.user.username
            return owner == request.user
        return False
