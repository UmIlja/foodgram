from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from .constants import (
    RECIPE_NAME_MAX_LENGTH,
    INGREDIENT_NAME_MAX_LENGTH,
    MEASUREMENT_UNIT_MAX_LENGTH,
    TAG_DATA_MAX_LENGTH,
    MIN_TIME_VALUE,
    MIN_AMOUNT_VALUE)


User = get_user_model()


class Ingredient(models.Model):
    """Модель Ингредиента."""

    name = models.CharField(
        'Название',
        max_length=INGREDIENT_NAME_MAX_LENGTH,
        unique=True)
    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=MEASUREMENT_UNIT_MAX_LENGTH)

    def save(self, *args, **kwargs):  # Уникальные независимо от регистра
        self.name = self.name.upper()
        return super(Ingredient, self).save(*args, **kwargs)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель Тега."""

    name = models.CharField(max_length=TAG_DATA_MAX_LENGTH, unique=True)
    slug = models.SlugField(
        max_length=TAG_DATA_MAX_LENGTH,
        unique=True,
        null=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""

    name = models.CharField('Название', max_length=RECIPE_NAME_MAX_LENGTH)
    text = models.TextField('Описание рецепта', default="")
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (в минутах)',
        validators=[MinValueValidator(MIN_TIME_VALUE)])
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',)
    image = models.ImageField(
        'Картинка готового блюда',
        upload_to='images/recipes/')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        related_name='recipes',
        verbose_name='Ингредиенты',)
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',)

    class Meta:
        ordering = ('name', 'author')
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    """Модель ингридиентов в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe_ingredients',
        on_delete=models.CASCADE)
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='recipe_ingredients',
        on_delete=models.CASCADE)
    # Дополнительные поля:
    amount = models.PositiveSmallIntegerField(
        'Количество ингридиента в рецепте',
        default=1,
        validators=[MinValueValidator(MIN_AMOUNT_VALUE)])

    class Meta:
        ordering = ('recipe', 'ingredient',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self):
        return f'{self.ingredient}'


class ShoppingCart(models.Model):
    """Модель корзины покупок для приготовления рецепта."""
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='shopping_cart')
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name='shopping_cart_items')

    class Meta:
        ordering = ('recipe', 'user')
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_shopping_cart_items')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"


class FavoriteRecipe(models.Model):
    """Модель избранных рецептов у пользователя."""
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='favorite_recipe')
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name='favorite_recipe_items')

    class Meta:
        ordering = ('recipe', 'user')
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_favorite_recipe_items')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"


class Subscription(models.Model):
    """Модель пользователей, на которых подписан текущий пользователь."""
    user = models.ForeignKey(User,
                             related_name='subscriptions',
                             on_delete=models.CASCADE)
    author = models.ForeignKey(User,
                               related_name='subscribers',
                               on_delete=models.CASCADE)

    class Meta:
        ordering = ('author', 'user')
        unique_together = ('user', 'author')
