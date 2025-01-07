from rest_framework import permissions


class IsAuthorOrAuthOrReadOnlyPermission(permissions.BasePermission):
    """
    Разрешение, которое позволяет автору редактировать и удалять свои рецепты,
    а также позволяет анонимным пользователям только просматривать рецепты.
    """
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)
