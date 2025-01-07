from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from rest_framework import serializers

from .constants import (EMAIL_MAX_LENGTH, NAME_MAX_LENGTH, USERNAME_REGEX)


class CustomUser(AbstractUser):
    """
    Custom user model.
    Users within the project authentication system are represented by this
    model.
    """

    email = models.EmailField(
        max_length=EMAIL_MAX_LENGTH, unique=True, blank=False, null=False
    )
    username = models.CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True, blank=False, null=False,
        validators=[RegexValidator(regex=USERNAME_REGEX)]
    )
    first_name = models.CharField(
        max_length=NAME_MAX_LENGTH, blank=False, null=False
    )
    last_name = models.CharField(
        max_length=150, blank=False, null=False
    )
    avatar = models.ImageField(
        upload_to='users/', blank=True, null=True
    )
    is_subscribed = models.BooleanField(default=False)

    def clean_username(self):
        if self.username.lower() == 'me':
            raise serializers.ValidationError(
                'Имя пользователя "me" недопустимо.'
            )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
