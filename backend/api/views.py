from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientSearchFilter, RecipesFilter
from .models import (FavoriteRecipe, Ingredient, Recipe, ShoppingCart,
                     Subscription, Tag)
from .permissions import IsAuthorOrAuthOrReadOnlyPermission
from .serializers import (FullRecipeSerializer, FullUserSerializer,
                          IngredientSerializer, RecipeMinifiedSerializer,
                          ShoppingCartSerializer, SubscribeSerializer,
                          SubscriptionWithRecipesSerializer, TagSerializer,
                          UserAvatarSerializer, WriteRecipeSerializer)

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Получаем список всех ИНГРЕДИЕНТОВ.
    Получаем конкретный ИНГРЕДИЕНТ по его id.
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientSearchFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Получаем список всех ТЕГОВ.
    Получаем конкретный ТЕГ по его id.
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Получаем список всех РЕЦЕПТОВ или создаём новый РЕЦЕПТ.
    Получаем, редактируем или удаляем конкретный РЕЦЕПТ по его id.
    Получаем короткую ссылку на РЕЦЕПТ по его id.
    Добавляем/Удаляем РЕЦЕПТ из списка покупок.
    Добавляем/Удаляем РЕЦЕПТ из избранного.
    Получаем файл со списком покупок для РЕЦЕПТА.
    """

    queryset = Recipe.objects.all()
    pagination_class = LimitOffsetPagination
    permission_classes = (IsAuthorOrAuthOrReadOnlyPermission,)
    http_method_names = ('get', 'post', 'patch', 'delete',)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter

    def get_serializer_class(self, action=None):
        if (action or self.action) in ('retrieve', 'list'):
            return FullRecipeSerializer
        return WriteRecipeSerializer

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        """Получаем короткую ссылку на РЕЦЕПТ по его id."""
        try:
            recipe = self.get_object()  # Получаем рецепт по id
            # Генерируем короткую ссылку
            short_link = f"{settings.BASE_URL}/api/recipes/{recipe.id}"
            return Response({"short-link": short_link},
                            status=status.HTTP_200_OK)
        except Recipe.DoesNotExist:
            raise NotFound("Объект не найден")

    def base_manage_user_and_recipe_method(
            self, request, pk=None, model=None, serializer_class=None):
        """Общая логика для добавления/удаления рецепта из списка."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        if request.method == 'POST':
            if model.objects.filter(user=user, recipe=recipe).exists():
                return Response(  # Проверяем, существует ли уже запись
                    {"detail": "Рецепт уже добавлен."},
                    status=status.HTTP_400_BAD_REQUEST)
            model.objects.create(user=user, recipe=recipe)
            response_data = RecipeMinifiedSerializer(recipe).data
            return Response(response_data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            try:
                item = model.objects.get(user=user, recipe=recipe)
                item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except model.DoesNotExist:
                return Response(
                    {"detail": "Рецепт не найден."},
                    status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def manage_shopping_cart(self, request, pk=None):
        """Добавляем/Удаляем РЕЦЕПТ из списка покупок."""
        return self.base_manage_user_and_recipe_method(
            request, pk, ShoppingCart, ShoppingCartSerializer)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def manage_favorites(self, request, pk=None):
        """Добавляем/Удаляем РЕЦЕПТ из избранного."""
        return self.base_manage_user_and_recipe_method(
            request, pk, FavoriteRecipe, None)

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        """Получаем файл со списком покупок в текстовом формате."""
        shopping_cart = self.get_shopping_cart(request.user)
        # Создание HTTP-ответа с типом контента текстового файла
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"')
        name_width = 35  # Ширина для названия
        quantity_width = 10  # Ширина для количества
        lines = [  # Запись данных в текстовый файл
            "          <<<СПИСОК ПОКУПОК>>>\n",
            "НАЗВАНИЕ".ljust(name_width) + "КОЛИЧЕСТВО\n"]
        for item in shopping_cart:
            # Форматируем строки с выравниванием
            lines.append(
                f"{item['name'].ljust(name_width)}"
                f"{str(item['quantity']).ljust(quantity_width)}\n"
            )
        response.writelines(lines)  # Запись всех строк в ответ
        return response

    def get_shopping_cart(self, user):
        """Формируем список покупок."""
        shopping_cart_items = (  # Получаем все ингредиенты и их количества
            ShoppingCart.objects
            .filter(user=user)
            .values('recipe__recipe_ingredients__ingredient__name')
            .annotate(total_quantity=Sum('recipe__recipe_ingredients__amount'))
        )
        shopping_cart = [  # Формируем список покупок
            {'name': item['recipe__recipe_ingredients__ingredient__name'],
             'quantity': item['total_quantity']}
            for item in shopping_cart_items
        ]
        return shopping_cart


class SubscriptionViewSet(viewsets.GenericViewSet):
    """
    Получаем пользователей, на которых подписан текущий пользователь
    (В выдачу добавляются рецепты)
    """
    serializer_class = SubscriptionWithRecipesSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter

    def get_queryset(self):
        return User.objects.filter(subscribers__user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)  # Применяем пагинацию
        # Получаем рецепты для всех пользователей
        recipes = Recipe.objects.filter(author__in=queryset)
        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
                context={'recipes': recipes,
                         'recipes_limit': request.query_params.get(
                             'recipes_limit')})
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(
            queryset,
            many=True,
            context={'recipes': recipes,
                     'recipes_limit': request.query_params.get(
                         'recipes_limit')})
        return Response(serializer.data)


class UsersViewSet(UserViewSet):
    """
    Получаем список всех/конкретного пользователя(-ей).
    Регистрируем своего пользователя | Заходим на свою страничку.
    Добавляем/Меняем/Удаляем свой аватар.
    Меняем свой пароль.
    Можем подписаться/отписаться от пользователя.
    """
    queryset = User.objects.all()
    serializer_class = FullUserSerializer
    pagination_class = LimitOffsetPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:  # Для методов list и retrieve
            return [AllowAny()]
        elif self.action == 'me':  # Для метода me
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=False,
            methods=['put', 'delete'],
            url_path='me/avatar',
            permission_classes=(IsAuthenticated,))
    def manage_avatar(self, request):
        """Добавляем/Меняем/Удаляем свой АВАТАР"""
        if request.method == 'PUT':
            serializer = UserAvatarSerializer(data=request.data)
            if serializer.is_valid():
                request.user.avatar = serializer.validated_data['avatar']
                request.user.save()
                # Возвращаем URL аватара
                return Response({'avatar': request.user.avatar.url},
                                status=status.HTTP_200_OK)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            request.user.avatar = None
            request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['post', 'delete'],
            url_path='subscribe',
            permission_classes=(IsAuthenticated,))
    def manage_subscription(self, request, id=None):
        """Подписка/Отписка от пользователя и получение данных о рецептах."""
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            serializer = SubscribeSerializer(
                data={'author_id': author.id}, context={'request': request})
            serializer.is_valid(raise_exception=True)
            Subscription.objects.get_or_create(
                user=request.user, author=author)
            recipes = author.recipes.all()  # Получаем рецепты
            recipes_limit = request.query_params.get('recipes_limit', None)
            user_serializer = SubscriptionWithRecipesSerializer(
                author, context={
                    'request': request,
                    'recipes': recipes,
                    'recipes_limit': recipes_limit  # Передаем лимит также
                })
            return Response(
                user_serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            try:
                subscription = Subscription.objects.get(
                    user=request.user, author=author)
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Subscription.DoesNotExist:
                return Response(
                    {"error": "Подписка не найдена."},
                    status=status.HTTP_400_BAD_REQUEST)
