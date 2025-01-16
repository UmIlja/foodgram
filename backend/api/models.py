from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from .constants import (INGREDIENT_NAME_MAX_LENGTH,
                        MEASUREMENT_UNIT_MAX_LENGTH, MIN_AMOUNT_VALUE,
                        MIN_TIME_VALUE, RECIPE_NAME_MAX_LENGTH,
                        TAG_DATA_MAX_LENGTH)

User = get_user_model()


class Ingredient(models.Model):
    """Модель Ингредиента."""

    name = models.CharField(
        'Название',
        max_length=INGREDIENT_NAME_MAX_LENGTH,
        unique=True,)
    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=MEASUREMENT_UNIT_MAX_LENGTH)

    def save(self, *args, **kwargs):  # Уникальные независимо от регистра
        self.name = self.name.lower()
        return super(Ingredient, self).save(*args, **kwargs)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель Тега."""

    name = models.CharField(
        'Тег',
        max_length=TAG_DATA_MAX_LENGTH,
        unique=True)
    slug = models.SlugField(
        'Слаг тега',
        max_length=TAG_DATA_MAX_LENGTH,
        unique=True,
        null=False)

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
        upload_to='recipes/images/')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        related_name='recipes',
        verbose_name='Ингредиенты',)
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',)
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def favorite_count(self):
        """Возвращает кол-во пользователей, добавивших рецепт в избранное."""
        return self.favoriterecipe_items.count()

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    """Модель ингридиентов в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe_ingredients',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',)
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='recipe_ingredients',
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',)
    # Дополнительные поля:
    amount = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(MIN_AMOUNT_VALUE)],
        verbose_name='Количество ингредиента в рецепте',)

    class Meta:
        ordering = ('recipe', 'ingredient',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self):
        return f'{self.ingredient}'


class BaseUserAndRecipeRelation(models.Model):
    """Базовая модель для отношений между пользователем и рецептом."""

    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='%(class)s')
    recipe = models.ForeignKey('Recipe',
                               on_delete=models.CASCADE,
                               related_name='%(class)s_items')

    class Meta:
        abstract = True
        ordering = ('user', 'recipe')
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_%(class)s_items')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"


class ShoppingCart(BaseUserAndRecipeRelation):
    """Модель корзины покупок для приготовления рецепта."""

    class Meta(BaseUserAndRecipeRelation.Meta):
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'


class FavoriteRecipe(BaseUserAndRecipeRelation):
    """Модель избранных рецептов у пользователя."""

    class Meta(BaseUserAndRecipeRelation.Meta):
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


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
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_subscription'),
            models.CheckConstraint(check=~models.Q(user=models.F('author')),
                                   name='prevent_self_subscription')
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.author.username}"
