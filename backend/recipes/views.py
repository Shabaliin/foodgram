from __future__ import annotations
from collections import defaultdict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from users.pagination import StandardResultsSetPagination
from rest_framework.routers import SimpleRouter
from .models import Recipe, Favorite, ShoppingCart, RecipeShortLink, Tag, Ingredient
from .serializers import (
	RecipeReadSerializer,
	RecipeCreateUpdateSerializer,
	RecipeMinifiedSerializer,
	TagSerializer,
	IngredientSerializer,
)
from .permissions import IsAuthorOrReadOnly
from .filters import RecipesFilterBackend


class RecipeViewSet(viewsets.ModelViewSet):
	queryset = Recipe.objects.all().select_related('author').prefetch_related('tags', 'recipe_ingredients__ingredient')
	permission_classes = [IsAuthorOrReadOnly]
	pagination_class = StandardResultsSetPagination
	filter_backends = [RecipesFilterBackend]

	def get_serializer_class(self):
		if self.action in ['list', 'retrieve']:
			return RecipeReadSerializer
		return RecipeCreateUpdateSerializer

	def get_permissions(self):
		if self.action in ['create', 'partial_update', 'destroy']:
			return [IsAuthorOrReadOnly()]
		if self.action in ['favorite', 'shopping_cart', 'download_shopping_cart']:
			return [permissions.IsAuthenticated()]
		return [permissions.AllowAny()]

	def perform_create(self, serializer):
		serializer.save()

	@action(detail=True, methods=['post', 'delete'])
	def favorite(self, request, pk=None):
		recipe = self.get_object()
		if request.method.lower() == 'post':
			obj, created = Favorite.objects.get_or_create(user=request.user, recipe=recipe)
			if not created:
				return Response({'errors': 'Рецепт уже в избранном'}, status=status.HTTP_400_BAD_REQUEST)
			return Response(RecipeMinifiedSerializer(recipe, context={'request': request}).data, status=status.HTTP_201_CREATED)
		else:
			deleted, _ = Favorite.objects.filter(user=request.user, recipe=recipe).delete()
			if not deleted:
				return Response({'errors': 'Рецепта не было в избранном'}, status=status.HTTP_400_BAD_REQUEST)
			return Response(status=status.HTTP_204_NO_CONTENT)

	@action(detail=True, methods=['post', 'delete'])
	def shopping_cart(self, request, pk=None):
		recipe = self.get_object()
		if request.method.lower() == 'post':
			obj, created = ShoppingCart.objects.get_or_create(user=request.user, recipe=recipe)
			if not created:
				return Response({'errors': 'Рецепт уже в списке покупок'}, status=status.HTTP_400_BAD_REQUEST)
			return Response(RecipeMinifiedSerializer(recipe, context={'request': request}).data, status=status.HTTP_201_CREATED)
		else:
			deleted, _ = ShoppingCart.objects.filter(user=request.user, recipe=recipe).delete()
			if not deleted:
				return Response({'errors': 'Рецепта не было в списке покупок'}, status=status.HTTP_400_BAD_REQUEST)
			return Response(status=status.HTTP_204_NO_CONTENT)

	@action(detail=False, methods=['get'])
	def download_shopping_cart(self, request):
		items = ShoppingCart.objects.filter(user=request.user).select_related('recipe')
		ingredients_totals = defaultdict(int)
		for cart_item in items:
			for ri in cart_item.recipe.recipe_ingredients.select_related('ingredient').all():
				ingredients_totals[(ri.ingredient.name, ri.ingredient.measurement_unit)] += ri.amount
		lines = [f"{name} ({unit}) — {amount}" for (name, unit), amount in ingredients_totals.items()]
		content = "\n".join(lines) or "Список покупок пуст."
		response = HttpResponse(content, content_type='text/plain; charset=utf-8')
		response['Content-Disposition'] = 'attachment; filename="shopping-list.txt"'
		return response

	@action(detail=True, methods=['get'], url_path='get-link')
	def get_link(self, request, pk=None):
		recipe = self.get_object()
		link, _ = RecipeShortLink.objects.get_or_create(recipe=recipe)
		if not link.code:
			import secrets
			import string
			alphabet = string.ascii_letters + string.digits
			link.code = ''.join(secrets.choice(alphabet) for _ in range(4))
			link.save(update_fields=['code'])
		absolute = request.build_absolute_uri(f"/s/{link.code}")
		return Response({"short-link": absolute})


router = SimpleRouter()
router.register(r'recipes', RecipeViewSet, basename='recipes')


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def list_tags(request):
	return Response(TagSerializer(Tag.objects.all(), many=True, context={'request': request}).data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_tag(request, id: int):
	tag = get_object_or_404(Tag, id=id)
	return Response(TagSerializer(tag, context={'request': request}).data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def list_ingredients(request):
	name = request.query_params.get('name', '')
	qs = Ingredient.objects.all()
	if name:
		qs = qs.filter(name__istartswith=name)
	return Response(IngredientSerializer(qs, many=True, context={'request': request}).data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_ingredient(request, id: int):
	ingredient = get_object_or_404(Ingredient, id=id)
	return Response(IngredientSerializer(ingredient, context={'request': request}).data)
