from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from .constants import EMAIL_MAX_LENGTH, NAMES_FIELD_MAX_LENGTH


class UserProfile(AbstractUser):
    """
    Profile user model.
    Users within the project authentication system are represented by this
    model.
    """

    email = models.EmailField(
        'Эл.почта',
        max_length=EMAIL_MAX_LENGTH,
        unique=True, blank=False, null=False
    )
    username = models.CharField(
        'Логин',
        max_length=NAMES_FIELD_MAX_LENGTH,
        unique=True, blank=False, null=False,
        validators=[UnicodeUsernameValidator()]
    )
    first_name = models.CharField(
        'Имя', max_length=NAMES_FIELD_MAX_LENGTH, blank=False, null=False
    )
    last_name = models.CharField(
        'Фамилия', max_length=NAMES_FIELD_MAX_LENGTH, blank=False, null=False
    )
    avatar = models.ImageField(
        'Аватар', upload_to='users/', blank=True, null=True
    )
    is_subscribed = models.BooleanField('Подписан ли', default=False)

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')
