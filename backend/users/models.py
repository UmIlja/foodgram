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
        max_length=EMAIL_MAX_LENGTH, unique=True, blank=False, null=False
    )
    username = models.CharField(
        max_length=NAMES_FIELD_MAX_LENGTH,
        unique=True, blank=False, null=False,
        validators=[UnicodeUsernameValidator()]
    )
    first_name = models.CharField(
        max_length=NAMES_FIELD_MAX_LENGTH, blank=False, null=False
    )
    last_name = models.CharField(
        max_length=NAMES_FIELD_MAX_LENGTH, blank=False, null=False
    )
    avatar = models.ImageField(
        upload_to='users/', blank=True, null=True
    )
    is_subscribed = models.BooleanField(default=False)

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
