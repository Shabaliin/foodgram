from __future__ import annotations
import base64
import uuid
from django.core.files.base import ContentFile
from typing import List
from rest_framework import serializers
from users.serializers import UserSerializer
from .models import Tag, Ingredient, Recipe, RecipeIngredient


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


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_ingredients(self, obj: Recipe):
        items = (
            RecipeIngredient.objects
            .filter(recipe=obj)
            .select_related('ingredient')
        )

        return [
            {
                'id': item.ingredient_id,
                'name': item.ingredient.name,
                'measurement_unit': item.ingredient.measurement_unit,
                'amount': item.amount,
            }
            for item in items
        ]

    def get_is_favorited(self, obj: Recipe) -> bool:
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.favorited_by.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj: Recipe) -> bool:
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.in_carts.filter(user=request.user).exists()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            header, b64data = data.split(';base64,')
            file_ext = header.split('/')[-1]
            decoded = base64.b64decode(b64data)
            file_name = f"{uuid.uuid4().hex}.{file_ext}"
            return ContentFile(decoded, name=file_name)
        return super().to_internal_value(data)


class RecipeWriteIngredientSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = RecipeWriteIngredientSerializer(many=True)
    tags = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients', 'tags', 
        'image', 'name', 'text', 'cooking_time')

    def validate_cooking_time(self, value: int):
        if value < 1:
            raise serializers.ValidationError(
                'Убедитесь, что это значение больше либо равно 1.'
                )
        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients', [])
        tag_ids: List[int] = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
            )
        recipe.tags.set(tag_ids)
        self._set_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance: Recipe, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tag_ids = validated_data.pop('tags', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self._set_ingredients(instance, ingredients_data)
        return instance

    def _set_ingredients(self, recipe: Recipe, ingredients_data: List[dict]):
        from .models import Ingredient, RecipeIngredient
        if not ingredients_data:
            raise serializers.ValidationError({'ingredients': ['Обязательное поле.']})
        seen = set()
        errors = []
        for idx, item in enumerate(ingredients_data):
            ingredient_id = item['id']
            amount = item['amount']
            if amount < 1:
                errors.append({})
                continue
            if ingredient_id in seen:
                errors.append({})
                continue
            seen.add(ingredient_id)
            errors.append({})
        if any(e for e in errors if e):
            raise serializers.ValidationError({'ingredients': errors})
        ingredient_ids = [d['id'] for d in ingredients_data]
        ingredient_map = {i.id: i for i in Ingredient.objects.filter(id__in=ingredient_ids)}
        for item in ingredients_data:
            ing = ingredient_map.get(item['id'])
            if not ing:
                raise serializers.ValidationError({
                    'ingredients': [
                        {'id': ['Выбран несуществующий объект.']}
                    ]
                })

            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ing,
                amount=item['amount'],
            )

