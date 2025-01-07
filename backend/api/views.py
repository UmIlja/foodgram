import csv

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import RecipesFilter
from .models import (FavoriteRecipe, Ingredient, Recipe, ShoppingCart,
                     Subscription, Tag)
from .permissions import IsAuthorOrAuthOrReadOnlyPermission
from .serializers import (FullRecipeSerializer, IngredientSerializer,
                          RecipeMinifiedSerializer, ShoppingCartSerializer,
                          SubscribeSerializer,
                          SubscriptionWithRecipesSerializer, TagSerializer,
                          TokenSerializer, UserAvatarSerializer,
                          UserChangePasswordSerializer, UserDetailSerializer,
                          UserRegistrationSerializer, UserSerializer,
                          WriteRecipeSerializer)

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
    filterset_fields = ('name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Получаем список всех ТЕГОВ.
    Получаем конкретный ТЕГ по его id.
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = (filters.SearchFilter,)


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

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self, action=None):
        if (action or self.action) in ('retrieve', 'list'):
            return FullRecipeSerializer
        return WriteRecipeSerializer

    def create(self, request, *args, **kwargs):
        """Создаем новый рецепт и возвращаем его полные данные."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Передаем контекст запроса в сериализатор
        return Response(FullRecipeSerializer(
            serializer.instance, context={'request': request}).data,
            status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        """Получаем короткую ссылку на РЕЦЕПТ по его id."""
        try:
            recipe = self.get_object()  # Получаем рецепт по id
            # Генерируем короткую ссылку
            short_link = f"https://foodgram.example.org/s/{recipe.id}"
            return Response({"short-link": short_link},
                            status=status.HTTP_200_OK)
        except Recipe.DoesNotExist:
            raise NotFound("Объект не найден")

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def manage_shopping_cart(self, request, pk=None):
        """Добавляем/Удаляем РЕЦЕПТ из списка покупок."""
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            serializer = ShoppingCartSerializer(
                data={'recipe': recipe.id}, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            # Используем сериализатор для формирования ответа
            response_serializer = RecipeMinifiedSerializer(
                recipe, context={'request': request})
            return Response(
                response_serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            try:
                # Пытаемся получить элемент корзины
                shopping_cart_item = ShoppingCart.objects.get(
                    user=request.user, recipe=recipe)
                shopping_cart_item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except ShoppingCart.DoesNotExist:
                return Response(
                    {'detail': 'Рецепт не найден в корзине покупок.'},
                    status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def manage_favorites(self, request, pk=None):
        """Добавляем/Удаляем РЕЦЕПТ из избранного."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        if request.method == 'POST':
            # Проверяем, существует ли уже запись в избранном
            if FavoriteRecipe.objects.filter(
                    user=user, recipe=recipe).exists():
                return Response(
                    {"detail": "Рецепт уже добавлен в избранное."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            FavoriteRecipe.objects.create(user=user, recipe=recipe)
            # Формируем ответ с использованием сериализатора
            response_data = RecipeMinifiedSerializer(recipe).data
            return Response(response_data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            try:  # Проверяем, существует ли запись в избранном
                favorite_recipe = FavoriteRecipe.objects.get(
                    user=user, recipe=recipe)
                favorite_recipe.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except FavoriteRecipe.DoesNotExist:
                return Response(
                    {"detail": "Рецепт не найден в избранном."},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        """Получаем файл со списком покупок."""
        shopping_cart = self.get_shopping_cart(request.user)
        response = HttpResponse(content_type='text/csv')  # Создание CSV файла
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_cart.csv"'
        writer = csv.writer(response)
        writer.writerow(['Название', 'Количество'])  # Заголовки столбцов
        for item in shopping_cart:
            writer.writerow([item['name'], item['quantity']])  # Запись данных
        return response

    def get_shopping_cart(self, user):
        """Формируем список покупок."""
        # Получаем все элементы списка покупок для текущего пользователя
        shopping_cart_items = ShoppingCart.objects.filter(user=user)
        # Словарь для хранения ингредиентов и их количеств
        ingredients = {}
        for item in shopping_cart_items:
            # Получаем все ингредиенты для текущего рецепта
            # Используем related_name из IngredientRecipe
            for ingredient in item.recipe.recipe_ingredients.all():
                if ingredient.ingredient.name in ingredients:
                    # Суммируем количество
                    ingredients[ingredient.ingredient.name] += (
                        ingredient.amount)
                else:
                    ingredients[ingredient.ingredient.name] = ingredient.amount
        # Формируем список покупок
        shopping_cart = [
            {'name': name, 'quantity': quantity}
            for name, quantity
            in ingredients.items()
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

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UsersViewSet(viewsets.ModelViewSet):
    """
    Получаем список всех/конкретного пользователя(-ей).
    Регистрируем своего пользователя | Заходим на свою страничку.
    Добавляем/Меняем/Удаляем свой аватар.
    Меняем свой пароль.
    Можем подписаться/отписаться от пользователя.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    pagination_class = LimitOffsetPagination

    def create(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(user=self.request.user)
            return Response(UserDetailSerializer(user).data,
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False,
            methods=['get'],
            url_path='me',
            permission_classes=(IsAuthenticated,))
    def me(self, request):  # Собственная страница пользователя
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

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
                return Response({'avatar': request.user.avatar.url},
                                status=status.HTTP_200_OK)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            request.user.avatar = None
            request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=['post'],
            url_path='set_password',
            permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        """Меняем свой ПАРОЛЬ авторизации."""
        serializer = UserChangePasswordSerializer(data=request.data,
                                                  context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            methods=['post', 'delete'],
            url_path='subscribe',
            permission_classes=(IsAuthenticated,))
    def manage_subscription(self, request, pk=None):
        """Подписка/Отписка от пользователя и получение данных о рецептах."""
        author = get_object_or_404(User, id=pk)
        recipes_limit = request.query_params.get('recipes_limit', None)
        if request.method == 'POST':
            serializer = SubscribeSerializer(
                data={'author_id': author.id}, context={'request': request})
            serializer.is_valid(raise_exception=True)
            Subscription.objects.get_or_create(
                user=request.user, author=author)
            recipes = author.recipes.all()
            if recipes_limit is not None:
                try:  # Ограничиваем количество рецептов, если указано
                    recipes_limit = int(recipes_limit)
                    recipes = recipes[:recipes_limit]
                except ValueError:
                    return Response(
                        {"error": "Некорректное значение для recipes_limit."},
                        status=status.HTTP_400_BAD_REQUEST)
            user_serializer = SubscriptionWithRecipesSerializer(
                author, context={'request': request, 'recipes': recipes})
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


class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet для аутентификации пользователей.
    POST: для получения токена  |  POST: для удаления токена.
    """
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        serializer = TokenSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    token, created = Token.objects.get_or_create(user=user)
                    return Response({"auth_token": token.key},
                                    status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Invalid email or password."},
                                    status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({"error": "Invalid email or password."},
                                status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='logout')
    def logout(self, request):
        token = request.auth
        if token:
            token.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "No active token found."},
                        status=status.HTTP_400_BAD_REQUEST)
