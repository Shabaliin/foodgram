from django.contrib.auth.models import AbstractUser
from django.db import models

USERNAME_MAX_LENGTH = 150


def user_avatar_upload_to(instance: 'User', filename: str) -> str:
    return f'users/{instance.id}/avatar/{filename}'


class User(AbstractUser):
    username = models.CharField(
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        verbose_name='Логин'
    )
    email = models.EmailField(
        unique=True,
        verbose_name='Email'
    )
    avatar = models.ImageField(
        upload_to=user_avatar_upload_to,
        null=True,
        blank=True,
        verbose_name='Аватар'
    )

    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return self.email


class Subscription(models.Model):
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор'
    )

    class Meta:
        unique_together = ('user', 'author')
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
