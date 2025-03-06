from rest_framework import permissions


class VoucherPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        """Ensure user is authenticated"""
        return request.user and  request.user.is_authenticated
        
    def has_object_permission(self, request, view, obj):
        """Ensure account can only view the Voucher endpoint. """
        if request.user.role == 'accountant' and \
        request.method not in permissions.SAFE_METHODS:
            return False
        return True
            


