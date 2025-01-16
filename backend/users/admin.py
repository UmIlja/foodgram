from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
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


class IngredientRecipeInlineFormset(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        # Проверяем, есть ли хотя бы один ингредиент
        if not any(form.cleaned_data and form.cleaned_data[0].get(
            'ingredient') for form in self.forms if form.cleaned_data):
            raise ValidationError(
                "Рецепт должен содержать хотя бы один ингредиент.")


class IngredientInline(admin.StackedInline):
    model = IngredientRecipe
    extra = 1
    fields = ('ingredient', 'amount')
    formset = IngredientRecipeInlineFormset


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_image', 'author', 'in_favourite_count')
    list_select_related = ('author',)
    list_filter = ['tags']
    search_fields = ('name', 'author__username')
    fields = ('name', 'text', 'image', 'cooking_time', 'author', 'tags',)
    filter_horizontal = ('tags',)
    inlines = [IngredientInline]

    @admin.display(description='Изображение блюда')
    def get_image(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="50" height="60" />')
        return None

    @admin.display(description='Число добавлений в избранное')
    def in_favourite_count(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return obj.favorite_count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):

    list_display = ('name', 'measurement_unit',)
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
