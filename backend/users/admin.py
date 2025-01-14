from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe
from rest_framework.authtoken.models import Token

from .models import UserProfile
from api.models import Ingredient, IngredientRecipe, Recipe, Tag


try:
    admin.site.unregister(Token)
except admin.sites.NotRegistered:
    pass  # Игнорируем, если токен не был зарегистрирован
admin.site.site_title = 'Администрирование Foodgram'
admin.site.site_header = 'Администрирование Foodgram'
admin.site.unregister(Group)
admin.site.register(Tag)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):

    list_display = ('username', 'email',)
    search_fields = ('username', 'email',)
    fields = ('email', 'username', 'first_name', 'last_name', 'password')


class IngredientInline(admin.StackedInline):
    model = IngredientRecipe
    extra = 1
    fields = ('ingredient', 'amount')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_image', 'author')
    list_select_related = ('author',)
    list_filter = ['tags']
    search_fields = ('name', 'author__username')
    fields = ('name', 'text', 'image', 'cooking_time', 'author', 'tags',)
    filter_horizontal = ('tags',)
    inlines = [IngredientInline]

    # Для визуальной ясности выводим также изображение блюда
    @admin.display(description='Изображение блюда')
    def get_image(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src={obj.image.url} width="50" height="60" />')

    def get_readonly_fields(self, request, obj=None):
        """Добавляем поле для отображения количества добавлений в избранное на странице редактирования."""
        if obj:  # Если это страница редактирования
            return super().get_readonly_fields(request, obj) + ('in_favourite_count',)
        return super().get_readonly_fields(request, obj)

    @admin.display(description='Число добавлений в избранное')
    def in_favourite_count(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return obj.favorite_items.count()

    def in_favourite_count_display(self, obj):
        """Метод для отображения количества добавлений в избранное."""
        return self.in_favourite_count(obj)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Добавляем контекст для отображения количества добавлений в избранное."""
        extra_context = extra_context or {}
        extra_context['in_favourite_count'] = self.in_favourite_count_display(self.get_object(request, object_id))
        return super().change_view(request, object_id, form_url, extra_context=extra_context)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):

    list_display = ('name', 'measurement_unit',)
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
