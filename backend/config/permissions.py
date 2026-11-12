"""Role-based permission classes shared by every app."""
from rest_framework.permissions import SAFE_METHODS, BasePermission


def _authenticated(request):
    return bool(request.user and request.user.is_authenticated)


class IsAdmin(BasePermission):
    message = 'Only administrators can perform this action.'

    def has_permission(self, request, view):
        return _authenticated(request) and request.user.is_admin


class IsLibraryStaff(BasePermission):
    """Admins and librarians."""

    message = 'Only library staff can perform this action.'

    def has_permission(self, request, view):
        return _authenticated(request) and request.user.is_library_staff


class IsStudent(BasePermission):
    message = 'Only students can perform this action.'

    def has_permission(self, request, view):
        return _authenticated(request) and request.user.is_student


class IsAdminOrReadOnly(BasePermission):
    """Any signed-in user may read; only admins may write."""

    message = 'Only administrators can change this.'

    def has_permission(self, request, view):
        if not _authenticated(request):
            return False
        return request.method in SAFE_METHODS or request.user.is_admin


class CanManageResourcesOrReadOnly(BasePermission):
    """
    Any signed-in user may read. Writing needs an admin, or a librarian the
    admin has granted the "manage seats and rooms" permission.
    """

    message = 'You are not permitted to manage seats and study rooms.'

    def has_permission(self, request, view):
        if not _authenticated(request):
            return False
        return request.method in SAFE_METHODS or request.user.can_manage_library_resources
