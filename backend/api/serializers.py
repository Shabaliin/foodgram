from __future__ import annotations
from typing import List

from rest_framework import serializers

from recipes.models import Tag, Ingredient, Recipe, RecipeIngredient
from users.models import User
from .fields import Base64ImageField


class TagSerializer(serializers.ModelSerializer):
	class Meta:
		model = Tag
		fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
	class Meta:
		model = Ingredient
		fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.Serializer):
	id = serializers.IntegerField(read_only=True)
	name = serializers.CharField(read_only=True)
	measurement_unit = serializers.CharField(read_only=True)
	amount = serializers.IntegerField()


class RecipeMinifiedSerializer(serializers.ModelSerializer):
	class Meta:
		model = Recipe
		fields = ('id', 'name', 'image', 'cooking_time')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
	id = serializers.IntegerField(source='ingredient_id', read_only=True)
	name = serializers.CharField(source='ingredient.name', read_only=True)
	measurement_unit = serializers.CharField(source='ingredient.measurement_unit', read_only=True)

	class Meta:
		model = RecipeIngredient
		fields = ('id', 'name', 'measurement_unit', 'amount')


class UserSerializer(serializers.ModelSerializer):
	is_subscribed = serializers.SerializerMethodField(read_only=True)
	avatar = serializers.SerializerMethodField(read_only=True)

	class Meta:
		model = User
		fields = (
			'id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed', 'avatar'
		)

	def get_is_subscribed(self, obj: User) -> bool:
		request = self.context.get('request')
		if not request or request.user.is_anonymous:
			return False
		return obj.subscribers.filter(user=request.user).exists()

	def get_avatar(self, obj: User) -> str | None:
		if not obj.avatar:
			return None
		request = self.context.get('request')
		url = obj.avatar.url
		if request:
			return request.build_absolute_uri(url)
		return url


class UserCreateSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = ('id', 'email', 'username', 'first_name', 'last_name', 'password')


class UserWithRecipesSerializer(UserSerializer):
	recipes = serializers.SerializerMethodField()
	recipes_count = serializers.SerializerMethodField()

	class Meta(UserSerializer.Meta):
		fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

	def get_recipes(self, obj: User):
		recipes_qs = obj.recipes.all().order_by('-created_at', '-id')
		limit = self.context.get('recipes_limit')
		if isinstance(limit, int):
			recipes_qs = recipes_qs[:limit]
		request = self.context.get('request')
		result = []
		for r in recipes_qs:
			image_url = r.image.url
			if request:
				image_url = request.build_absolute_uri(image_url)
			result.append({
				'id': r.id,
				'name': r.name,
				'image': image_url,
				'cooking_time': r.cooking_time,
			})
		return result

	def get_recipes_count(self, obj: User) -> int:
		return obj.recipes.count()


class RecipeReadSerializer(serializers.ModelSerializer):
	author = serializers.SerializerMethodField()
	tags = TagSerializer(many=True, read_only=True)
	ingredients = RecipeIngredientReadSerializer(source='recipe_ingredients', many=True, read_only=True)
	is_favorited = serializers.SerializerMethodField()
	is_in_shopping_cart = serializers.SerializerMethodField()

	class Meta:
		model = Recipe
		fields = (
			'id', 'tags', 'author', 'ingredients', 'is_favorited', 'is_in_shopping_cart',
			'name', 'image', 'text', 'cooking_time'
		)

	def get_author(self, obj: Recipe):
		return UserSerializer(obj.author, context=self.context).data

	def get_is_favorited(self, obj: Recipe) -> bool:
		request = self.context.get('request')
		return bool(request and not request.user.is_anonymous and obj.favorited_by.filter(user=request.user).exists())

	def get_is_in_shopping_cart(self, obj: Recipe) -> bool:
		request = self.context.get('request')
		return bool(request and not request.user.is_anonymous and obj.in_carts.filter(user=request.user).exists())


class RecipeWriteIngredientSerializer(serializers.Serializer):
	id = serializers.IntegerField()
	amount = serializers.IntegerField(min_value=1)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
	ingredients = RecipeWriteIngredientSerializer(many=True)
	tags = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
	image = Base64ImageField()

	class Meta:
		model = Recipe
		fields = ('id', 'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time')

	def validate(self, attrs):
		tags = attrs.get('tags')
		if not tags:
			raise serializers.ValidationError({'tags': ['Обязательное поле.']})
		if len(tags) != len(set(tags)):
			raise serializers.ValidationError({'tags': ['Теги должны быть уникальны.']})

		ingredients = attrs.get('ingredients')
		if not ingredients:
			raise serializers.ValidationError({'ingredients': ['Обязательное поле.']})
		seen_ids = set()
		for item in ingredients:
			ingredient_id = item.get('id')
			if ingredient_id in seen_ids:
				raise serializers.ValidationError({'ingredients': ['Ингредиенты должны быть уникальны.']})
			seen_ids.add(ingredient_id)
		return attrs

	def validate_cooking_time(self, value: int):
		if value < 1:
			raise serializers.ValidationError('Убедитесь, что это значение больше либо равно 1.')
		return value

	def create(self, validated_data):
		ingredients_data = validated_data.pop('ingredients', [])
		tag_ids: List[int] = validated_data.pop('tags', [])
		recipe = Recipe.objects.create(author=self.context['request'].user, **validated_data)
		recipe.tags.set(tag_ids)
		self._set_ingredients(recipe, ingredients_data)
		return recipe

	def update(self, instance: Recipe, validated_data):
		ingredients_data = validated_data.pop('ingredients', None)
		tag_ids = validated_data.pop('tags', None)
		instance = super().update(instance, validated_data)
		return instance

	def _set_ingredients(self, recipe: Recipe, ingredients_data: List[dict]):
		if not ingredients_data:
			raise serializers.ValidationError({'ingredients': ['Обязательное поле.']})
		ingredient_ids = [d['id'] for d in ingredients_data]
		ingredient_map = {
			i.id: i for i in Ingredient.objects.filter(id__in=ingredient_ids)
		}
		RecipeIngredient.objects.bulk_create([
			RecipeIngredient(
				recipe=recipe,
				ingredient=ingredient_map.get(item['id']),
				amount=item['amount'],
			)
			for item in ingredients_data
		])
