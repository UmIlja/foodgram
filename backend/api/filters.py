from django_filters import rest_framework as filters

from .models import Recipe, Tag, User


class RecipesFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )
    author = filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        to_field_name='id'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_in_shopping_cart'
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorite'
    )

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_in_shopping_cart', 'is_favorited']

    def filter_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if value:
            return queryset.filter(shoppingcart_items__user=user)
        return queryset.exclude(shoppingcart_items__user=user)

    def filter_is_favorite(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if value:
            return queryset.filter(favoriterecipe_items__user=user)
        return queryset.exclude(favoriterecipe_items__user=user)
