from __future__ import annotations
from django.conf import settings
from django.db import models


TAG_NAME_MAX_LENGTH = 32
TAG_SLUG_MAX_LENGTH = 32
INGREDIENT_NAME_MAX_LENGTH = 128
INGREDIENT_UNIT_MAX_LENGTH = 64
RECIPE_NAME_MAX_LENGTH = 256
SHORTLINK_CODE_MAX_LENGTH = 8


class Tag(models.Model):
	name = models.CharField(max_length=TAG_NAME_MAX_LENGTH, unique=True, verbose_name='Название')
	slug = models.SlugField(max_length=TAG_SLUG_MAX_LENGTH, unique=True, verbose_name='Слаг')

	class Meta:
		verbose_name = 'Тег'
		verbose_name_plural = 'Теги'

	def __str__(self) -> str:
		return self.name


class Ingredient(models.Model):
	name = models.CharField(max_length=INGREDIENT_NAME_MAX_LENGTH, db_index=True, verbose_name='Название')
	measurement_unit = models.CharField(max_length=INGREDIENT_UNIT_MAX_LENGTH, verbose_name='Единица измерения')

	class Meta:
		unique_together = ('name', 'measurement_unit')
		verbose_name = 'Ингредиент'
		verbose_name_plural = 'Ингредиенты'

	def __str__(self) -> str:
		return f"{self.name} ({self.measurement_unit})"


def recipe_image_upload_to(instance: 'Recipe', filename: str) -> str:
	return f'recipes/{instance.author_id}/{instance.id}/{filename}'


class Recipe(models.Model):
	author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Автор')
	name = models.CharField(max_length=RECIPE_NAME_MAX_LENGTH, verbose_name='Название')
	image = models.ImageField(upload_to=recipe_image_upload_to, verbose_name='Изображение')
	text = models.TextField(verbose_name='Описание')
	cooking_time = models.PositiveIntegerField(verbose_name='Время приготовления')
	tags = models.ManyToManyField(Tag, blank=False, verbose_name='Теги')
	ingredients = models.ManyToManyField('Ingredient', through='RecipeIngredient', verbose_name='Ингредиенты')
	created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')

	class Meta:
		verbose_name = 'Рецепт'
		verbose_name_plural = 'Рецепты'
		default_related_name = 'recipes'

	def __str__(self) -> str:
		return self.name


class RecipeIngredient(models.Model):
	recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipe_ingredients', verbose_name='Рецепт')
	ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='ingredient_recipes', verbose_name='Ингредиент')
	amount = models.PositiveIntegerField(verbose_name='Количество')

	class Meta:
		unique_together = ('recipe', 'ingredient')
		verbose_name = 'Ингредиент в рецепте'
		verbose_name_plural = 'Ингредиенты в рецепте'


class UserRecipeRelation(models.Model):
	class Meta:
		abstract = True

	def __str__(self) -> str:
		return f"{self.user} — {self.recipe}"


class Favorite(UserRecipeRelation):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites', verbose_name='Пользователь')
	recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='favorited_by', verbose_name='Рецепт')

	class Meta:
		unique_together = ('user', 'recipe')
		verbose_name = 'Избранное'
		verbose_name_plural = 'Избранное'


class ShoppingCart(UserRecipeRelation):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shopping_cart', verbose_name='Пользователь')
	recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='in_carts', verbose_name='Рецепт')

	class Meta:
		unique_together = ('user', 'recipe')
		verbose_name = 'Покупка'
		verbose_name_plural = 'Покупки'


class RecipeShortLink(models.Model):
	recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE, related_name='shortlink', verbose_name='Рецепт')
	code = models.SlugField(max_length=SHORTLINK_CODE_MAX_LENGTH, unique=True, verbose_name='Код')
	created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')

	class Meta:
		verbose_name = 'Короткая ссылка'
		verbose_name_plural = 'Короткие ссылки'

	def __str__(self) -> str:
		return self.code
