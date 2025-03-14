from rest_framework.permissions import BasePermission
from django.contrib.auth.decorators import user_passes_test


# for views.py
def admin_required(view_func):
    return user_passes_test(
        lambda u: u.is_authenticated and u.is_superuser,
        login_url='/admin/login/'
    )(view_func)


# for api_views.py
class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser


class PostAdminOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ['POST']:
            return request.user.is_authenticated and request.user.is_superuser
        return True


class DeleteAdminOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ['DELETE']:
            return request.user.is_authenticated and request.user.is_superuser
        return True


class PutAdminOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ['PUT']:
            return request.user.is_authenticated and request.user.is_superuser
        return True
