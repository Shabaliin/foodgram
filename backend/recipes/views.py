from __future__ import annotations

from collections import defaultdict

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import (
    Ingredient,
    Favorite,
    Recipe,
    RecipeShortLink,
    ShoppingCart,
    Tag,
)
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeMinifiedSerializer,
    RecipeReadSerializer,
    TagSerializer,
)


class StandardResultsSetPagination(PageNumberPagination):
    page_query_param = 'page'
    page_size_query_param = 'limit'
    page_size = 6


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = (
        Recipe.objects.all()
        .select_related('author')
        .prefetch_related('tags', 'recipe_ingredients__ingredient')
    )

    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeReadSerializer
        return RecipeCreateUpdateSerializer

    def get_permissions(self):
        if self.action in ['create', 'partial_update', 'destroy']:
            return [IsAuthorOrReadOnly()]
        if self.action in [
            'favorite',
            'shopping_cart',
            'download_shopping_cart',
        ]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save()

    def get_queryset(self):
        qs = super().get_queryset()
        request = self.request

        author = request.query_params.get('author')
        if author:
            qs = qs.filter(author_id=author)

        tags = request.query_params.getlist('tags')
        if tags:
            qs = qs.filter(tags__slug__in=tags).distinct()

        is_favorited = request.query_params.get('is_favorited')
        if is_favorited in {'0', '1'} and request.user.is_authenticated:
            if is_favorited == '1':
                qs = qs.filter(favorited_by__user=request.user)
            else:
                qs = qs.exclude(favorited_by__user=request.user)

        is_in_cart = request.query_params.get('is_in_shopping_cart')
        if is_in_cart in {'0', '1'} and request.user.is_authenticated:
            if is_in_cart == '1':
                qs = qs.filter(in_carts__user=request.user)
            else:
                qs = qs.exclude(in_carts__user=request.user)

        return qs

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if request.method.lower() == 'post':
            obj, created = Favorite.objects.get_or_create(
                user=request.user,
                recipe=recipe,
            )
            if not created:
                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            data = RecipeMinifiedSerializer(
                recipe,
                context={'request': request},
            ).data
            return Response(data, status=status.HTTP_201_CREATED)

        deleted, _ = Favorite.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Рецепта не было в избранном'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        if request.method.lower() == 'post':
            obj, created = ShoppingCart.objects.get_or_create(
                user=request.user,
                recipe=recipe,
            )
            if not created:
                return Response(
                    {'errors': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            data = RecipeMinifiedSerializer(
                recipe,
                context={'request': request},
            ).data
            return Response(data, status=status.HTTP_201_CREATED)

        deleted, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Рецепта не было в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        items = ShoppingCart.objects.filter(user=request.user).select_related(
            'recipe'
        )
        ingredients_totals = defaultdict(int)

        for cart_item in items:
            qs = cart_item.recipe.recipe_ingredients.select_related(
                'ingredient'
            ).all()
            for ri in qs:
                key = (ri.ingredient.name, ri.ingredient.measurement_unit)
                ingredients_totals[key] += ri.amount

        lines = [
            f"{name} ({unit}) — {amount}"
            for (name, unit), amount in ingredients_totals.items()
        ]
        content = "\n".join(lines) or "Список покупок пуст."
        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8',
        )
        response[
            'Content-Disposition'
        ] = 'attachment; filename="shopping-list.txt"'
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


from rest_framework.routers import SimpleRouter

router = SimpleRouter()
router.register(r'recipes', RecipeViewSet, basename='recipes')


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def list_tags(request):
    data = TagSerializer(
        Tag.objects.all(),
        many=True,
        context={'request': request},
    ).data
    return Response(data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_tag(request, id: int):
    tag = get_object_or_404(Tag, id=id)
    data = TagSerializer(tag, context={'request': request}).data
    return Response(data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def list_ingredients(request):
    name = request.query_params.get('name', '')
    qs = Ingredient.objects.all()
    if name:
        qs = qs.filter(name__istartswith=name)
    data = IngredientSerializer(
        qs,
        many=True,
        context={'request': request},
    ).data
    return Response(data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_ingredient(request, id: int):
    ingredient = get_object_or_404(Ingredient, id=id)
    data = IngredientSerializer(
        ingredient,
        context={'request': request},
    ).data
    return Response(data)
