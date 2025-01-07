from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (AuthViewSet, IngredientViewSet, RecipeViewSet,
                    SubscriptionViewSet, TagViewSet, UsersViewSet)

app_name = 'api'

router = SimpleRouter()

router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')
router.register('auth/token', AuthViewSet, basename='token-auth')
router.register('users/subscriptions',
                SubscriptionViewSet,
                basename='subscriptions')
router.register('users', UsersViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
]
