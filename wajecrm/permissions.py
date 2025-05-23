from rest_framework import permissions


class BaseGiftCardPermission(permissions.BasePermission):
    allowed_methods = []
    role = None

    def has_permission(self, request, view):
        """Ensure user is authenticated and has the correct role"""
        return (
            request.user and
            request.user.is_authenticated and
            getattr(getattr(request.user, 'role', None), 'name', None) == self.role
        )
    def has_object_permission(self, request, view, obj):
        """Ensure account can only view the Voucher endpoint. """
        if getattr(request.user, 'role', None) == self.role and \
            request.method in self.allowed_methods :
            return True
        return False
            
class IsManager(BaseGiftCardPermission):
    allowed_methods = ['GET', 'POST', 'DELETE', 'PUT', 'PATCH']
    role = 'Manager'

class IsAccountant(BaseGiftCardPermission):
    allowed_methods = ['GET', 'PUT', 'PATCH', 'POST']
    role = 'Accountant'

class IsAuditor(BaseGiftCardPermission):
    allowed_methods = ['GET']
    role = 'Auditor'