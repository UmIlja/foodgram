from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from .models import (FavoriteRecipe, Ingredient, IngredientRecipe, Recipe,
                     ShoppingCart, Subscription, Tag, User)


class FullUserSerializer(serializers.ModelSerializer):
    """Serializer to manage user."""
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )
        read_only_fields = fields


class UserAvatarSerializer(FullUserSerializer):
    """Serializer of user avatar."""

    class Meta:
        model = User
        fields = ('avatar',)
        extra_kwargs = {'avatar': {'required': True}}


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class WriteIngredientsInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()  # Используем IntegerField для получения id

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')  # id ингредиента и его количество


class IngredientsInRecipeFullSerializer(IngredientSerializer):
    name = serializers.SlugRelatedField(
        'name', source='ingredient', queryset=Ingredient.objects.all())
    measurement_unit = serializers.SlugRelatedField(
        'measurement_unit',
        source='ingredient',
        queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FullRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = FullUserSerializer(many=False)
    ingredients = IngredientsInRecipeFullSerializer(
        source='recipe_ingredients', many=True)
    image = Base64ImageField(required=True, allow_null=False)
    is_favorited = serializers.SerializerMethodField(default=False)
    is_in_shopping_cart = serializers.SerializerMethodField(default=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = ('tags', 'author',)

    def get_is_favorited(self, obj):  # Добавлен ли рецепт в избранное?
        request = self.context.get('request')
        if request.user.is_authenticated:
            return FavoriteRecipe.objects.filter(
                user=request.user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):  # Добавлен ли рецепт в корзину?
        request = self.context.get('request')
        if request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user, recipe=obj).exists()
        return False


class WriteRecipeSerializer(serializers.ModelSerializer):
    ingredients = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(required=True),
            required=True
        ),
        required=True
    )
    tags = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )
    image = Base64ImageField(required=False, allow_null=True)
    name = serializers.CharField(max_length=256, required=True)
    text = serializers.CharField(required=True)
    cooking_time = serializers.IntegerField(min_value=1, required=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time'
        )
        read_only_fields = ('author',)

    def validate(self, data):
        # Убираем проверку на наличие изображения
        if 'image' in data and not data['image']:
            raise serializers.ValidationError('Поле image обязательно.')

        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Рецепт должен содержать хотя бы один тег.')

        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Рецепт должен содержать хотя бы один ингредиент.')

        # Проверка на дубликаты ингредиентов и минимальное количество
        ingredient_ids = []
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            amount = ingredient.get('amount', 0)
            if amount < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть больше 0.')

            if ingredient_id in ingredient_ids:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться.')
            ingredient_ids.append(ingredient_id)

        # Проверка существования тегов
        if not Tag.objects.filter(id__in=tags).exists():
            raise serializers.ValidationError(
                'Один или несколько тегов не существуют.')

        # Проверка на дубликаты тегов
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'Теги не должны повторяться.')

        # Проверка существования ингредиентов
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError(
                    f'Ингредиент с id {ingredient_id} не существует.')

        return data

    @staticmethod
    def create_or_update_ingredients(recipe, ingredients):
        unique_ingredients = []

        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            amount = ingredient['amount']

            unique_ingredients.append(IngredientRecipe(
                ingredient_id=ingredient_id,
                recipe=recipe,
                amount=amount
            ))

        IngredientRecipe.objects.bulk_create(unique_ingredients)

    def create(self, validated_data):
        """Метод создания модели рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(  # Создаем рецепт, устанавливаем автора
            author=self.context['request'].user, **validated_data)
        recipe.tags.set(tags)
        self.create_or_update_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Метод редактирования модели рецепта."""
        tags = validated_data.pop('tags', None)
        instance.tags.set(tags)
        ingredients = validated_data.pop('ingredients', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)  # Обновляем поля рецепта
        # Если изображение не передано, оставляем текущее значение
        if 'image' not in validated_data:
            validated_data['image'] = instance.image
        instance.save()
        # Обновляем ингредиенты
        if ingredients is None or len(ingredients) < 1:
            raise serializers.ValidationError(
                'Рецепт должен содержать хотя бы один ингредиент.')
        instance.ingredients.clear()  # Удаляем старые ингредиенты
        self.create_or_update_ingredients(instance, ingredients)
        return instance

    def to_representation(self, instance):
        """Метод для ответа"""
        return FullRecipeSerializer(
            instance, context={'request': self.context.get('request')}).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ['recipe']

    def validate_recipe(self, value):  # Проверка, существует ли рецепт
        if not Recipe.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Рецепт не найден.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        recipe = validated_data['recipe']
        shopping_cart_item, created = ShoppingCart.objects.get_or_create(
            user=user, recipe=recipe)
        if not created:  # Проверка, добавлен ли рецепт в корзину
            raise serializers.ValidationError("Рецепт уже в корзине.")
        return shopping_cart_item


class SubscribeSerializer(serializers.Serializer):
    author_id = serializers.IntegerField()

    def validate_author_id(self, value):
        request = self.context.get('request')
        user = request.user
        if user.id == value:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя.")
        if Subscription.objects.filter(user=user, author_id=value).exists():
            raise serializers.ValidationError(
                "Вы уже подписаны на этого пользователя.")
        return value


class SubscriptionWithRecipesSerializer(serializers.ModelSerializer):
    recipes = RecipeMinifiedSerializer(many=True, read_only=True)
    recipes_count = serializers.IntegerField(source='recipes.count',
                                             read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=obj).exists()
        return False

    def get_limited_recipes(self, recipes, recipes_limit):
        """Метод для ограничения количества рецептов."""
        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
                return recipes[:recipes_limit]
            except ValueError:
                raise serializers.ValidationError(
                    "Некорректное значение для recipes_limit.")
        return recipes

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        recipes = self.context.get('recipes', [])
        recipes_limit = self.context.get('recipes_limit', None)
        limited_recipes = self.get_limited_recipes(recipes, recipes_limit)
        representation['recipes'] = RecipeMinifiedSerializer(
            limited_recipes, many=True).data
        representation['recipes_count'] = len(limited_recipes)
        return representation
