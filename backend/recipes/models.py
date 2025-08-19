from __future__ import annotations
from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Tag(models.Model):
	name = models.CharField(max_length=32, unique=True)
	slug = models.SlugField(max_length=32, unique=True)

	def __str__(self) -> str:
		return self.name


class Ingredient(models.Model):
	name = models.CharField(max_length=128, db_index=True)
	measurement_unit = models.CharField(max_length=64)

	class Meta:
		unique_together = ('name', 'measurement_unit')

	def __str__(self) -> str:
		return f"{self.name} ({self.measurement_unit})"


def recipe_image_upload_to(instance: 'Recipe', filename: str) -> str:
	return f'recipes/{instance.author_id}/{instance.id}/{filename}'


class Recipe(models.Model):
	author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recipes')
	name = models.CharField(max_length=256)
	image = models.ImageField(upload_to=recipe_image_upload_to)
	text = models.TextField()
	cooking_time = models.PositiveIntegerField()
	tags = models.ManyToManyField(Tag, related_name='recipes', blank=False)
	ingredients = models.ManyToManyField('Ingredient', through='RecipeIngredient', related_name='recipes')
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return self.name


class RecipeIngredient(models.Model):
	recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipe_ingredients')
	ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='ingredient_recipes')
	amount = models.PositiveIntegerField()

	class Meta:
		unique_together = ('recipe', 'ingredient')


class Favorite(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
	recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='favorited_by')

	class Meta:
		unique_together = ('user', 'recipe')


class ShoppingCart(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shopping_cart')
	recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='in_carts')

	class Meta:
		unique_together = ('user', 'recipe')


class RecipeShortLink(models.Model):
	recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE, related_name='shortlink')
	code = models.SlugField(max_length=8, unique=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return self.code

