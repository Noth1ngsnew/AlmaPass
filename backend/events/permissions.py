from rest_framework import permissions

from accounts.models import User


def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.role == User.Role.ADMIN)


class IsOrganizerOwnerOrReadOnly(permissions.BasePermission):
    """Читать могут все; создавать — организаторы; менять — владелец события или админ."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        return user.is_authenticated and (is_admin(user) or hasattr(user, 'organizer'))

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return is_admin(request.user) or obj.organizer.user_id == request.user.id
