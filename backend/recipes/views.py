from __future__ import annotations
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from users.pagination import StandardResultsSetPagination
from rest_framework.routers import SimpleRouter
from .models import Recipe, Favorite, ShoppingCart, RecipeShortLink, Tag, Ingredient, RecipeIngredient
from .serializers import (
	RecipeReadSerializer,
	RecipeCreateUpdateSerializer,
	RecipeMinifiedSerializer,
	TagSerializer,
	IngredientSerializer,
	FavoriteActionSerializer,
	ShoppingCartActionSerializer,
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

	def _add_relation(self, request, recipe, serializer_class):
		serializer = serializer_class(data=request.data, context={'request': request, 'recipe': recipe})
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data, status=status.HTTP_201_CREATED)

	def _remove_relation(self, model, request, recipe, not_found_error: str):
		deleted, _ = model.objects.filter(user=request.user, recipe=recipe).delete()
		if not deleted:
			return Response({'errors': not_found_error}, status=status.HTTP_400_BAD_REQUEST)
		return Response(status=status.HTTP_204_NO_CONTENT)

	@action(detail=True, methods=['post', 'delete'])
	def favorite(self, request, pk=None):
		recipe = self.get_object()
		if request.method.lower() == 'post':
			return self._add_relation(request, recipe, FavoriteActionSerializer)
		return self._remove_relation(Favorite, request, recipe, 'Рецепта не было в избранном')

	@action(detail=True, methods=['post', 'delete'])
	def shopping_cart(self, request, pk=None):
		recipe = self.get_object()
		if request.method.lower() == 'post':
			return self._add_relation(request, recipe, ShoppingCartActionSerializer)
		return self._remove_relation(ShoppingCart, request, recipe, 'Рецепта не было в списке покупок')

	@action(detail=False, methods=['get'])
	def download_shopping_cart(self, request):
		agg = (
			RecipeIngredient.objects
			.filter(recipe__in_carts__user=request.user)
			.values('ingredient__name', 'ingredient__measurement_unit')
			.annotate(total=Sum('amount'))
			.order_by('ingredient__name')
		)
		lines = [
			f"{row['ingredient__name']} ({row['ingredient__measurement_unit']}) — {row['total']}"
			for row in agg
		]
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
