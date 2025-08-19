from django.contrib.auth.models import AbstractUser
from django.db import models


def user_avatar_upload_to(instance: 'User', filename: str) -> str:
	return f'users/{instance.id}/avatar/{filename}'


class User(AbstractUser):
	username = models.CharField(max_length=150, unique=True)
	email = models.EmailField(unique=True)
	avatar = models.ImageField(upload_to=user_avatar_upload_to, null=True, blank=True)

	REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
	USERNAME_FIELD = 'email'

	def __str__(self) -> str:
		return self.email


class Subscription(models.Model):
	user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='subscriptions')
	author = models.ForeignKey('User', on_delete=models.CASCADE, related_name='subscribers')

	class Meta:
		unique_together = ('user', 'author')
