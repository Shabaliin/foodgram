from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import Sum, Max
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, permissions, status, decorators
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .filters import RecipesFilterBackend
from .pagination import StandardResultsSetPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    RecipeReadSerializer,
    RecipeCreateUpdateSerializer,
    TagSerializer,
    IngredientSerializer,
    FavoriteActionSerializer,
    ShoppingCartActionSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)
from .fields import Base64ImageField
from recipes.models import (
    Recipe,
    Favorite,
    ShoppingCart,
    RecipeShortLink,
    Tag,
    Ingredient,
    RecipeIngredient,
)
from users.models import Subscription

User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = (
        Recipe.objects.all()
        .select_related('author')
        .prefetch_related('tags', 'recipe_ingredients__ingredient')
    )
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
        if self.action in [
            'favorite',
            'shopping_cart',
            'download_shopping_cart',
        ]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save()

    def _add_relation(self, request, recipe, serializer_class):
        serializer = serializer_class(
            data=request.data,
            context={'request': request, 'recipe': recipe},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_relation(self, model, request, recipe, not_found_error: str):
        deleted, _ = model.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if not deleted:
            return Response(
                {'errors': not_found_error},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if request.method.lower() == 'post':
            return self._add_relation(
                request,
                recipe,
                FavoriteActionSerializer,
            )
        return self._remove_relation(
            Favorite, request, recipe, 'Рецепта не было в избранном'
        )

    @decorators.action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        if request.method.lower() == 'post':
            return self._add_relation(
                request, recipe, ShoppingCartActionSerializer
            )
        return self._remove_relation(
            ShoppingCart, request, recipe, 'Рецепта не было в списке покупок'
        )

    @decorators.action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        agg = (
            RecipeIngredient.objects
            .filter(recipe__in_carts__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total=Sum('amount'))
            .order_by('ingredient__name')
        )
        lines = [
            "{name} ({unit}) — {total}".format(
                name=row['ingredient__name'],
                unit=row['ingredient__measurement_unit'],
                total=row['total'],
            )
            for row in agg
        ]
        content = "\n".join(lines) or "Список покупок пуст."
        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8',
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping-list.txt"'
        )
        return response

    @decorators.action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        link, _ = RecipeShortLink.objects.get_or_create(recipe=recipe)
        if not link.code:
            import secrets
            import string
            alphabet = string.ascii_letters + string.digits
            link.code = ''.join(
                secrets.choice(alphabet) for _ in range(4)
            )
            link.save(update_fields=['code'])
        absolute = request.build_absolute_uri(f"/s/{link.code}")
        return Response({"short-link": absolute})


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def list_tags(request):
    return Response(
        TagSerializer(
            Tag.objects.all(), many=True, context={'request': request}
        ).data
    )


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
    return Response(
        IngredientSerializer(qs, many=True, context={'request': request}).data
    )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_ingredient(request, id: int):
    ingredient = get_object_or_404(Ingredient, id=id)
    return Response(
        IngredientSerializer(ingredient, context={'request': request}).data
    )


class UserViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination
    image_field = Base64ImageField()

    def retrieve(self, request, pk: int = None):
        user = get_object_or_404(User, id=pk)
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)

    @decorators.action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscriptions(self, request):
        qs = User.objects.filter(
            id__in=Subscription
            .objects
            .filter(user=request.user)
            .values('author_id')
        )
        qs = qs.annotate(
            last_pub=Max('recipes__created_at')
        ).order_by('-last_pub', '-id')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)

        recipes_limit = request.query_params.get('recipes_limit')
        ctx = {'request': request}
        if recipes_limit and recipes_limit.isdigit():
            ctx['recipes_limit'] = int(recipes_limit)

        serializer = UserWithRecipesSerializer(page, many=True, context=ctx)
        return paginator.get_paginated_response(serializer.data)

    @decorators.action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscribe(self, request, pk: int = None):
        if request.method.lower() == 'post':
            if request.user.id == int(pk):
                return Response(
                    {'errors': 'Нельзя подписаться на себя'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            author = get_object_or_404(User, id=pk)
            obj, created = Subscription.objects.get_or_create(
                user=request.user,
                author=author,
            )
            if not created:
                return Response(
                    {'errors': 'Уже подписаны'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            recipes_limit = request.query_params.get('recipes_limit')
            ctx = {'request': request}
            if recipes_limit and recipes_limit.isdigit():
                ctx['recipes_limit'] = int(recipes_limit)
            serializer = UserWithRecipesSerializer(author, context=ctx)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = Subscription.objects.filter(
            user=request.user,
            author_id=pk,
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Не были подписаны'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[permissions.IsAuthenticated],
    )
    def avatar(self, request):
        if request.method.lower() == 'put':
            avatar_b64 = request.data.get('avatar')
            if not avatar_b64:
                return Response(
                    {'avatar': ['Обязательное поле.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            file = Base64ImageField().to_internal_value(avatar_b64)
            user = request.user
            user.avatar.save(file.name, file, save=True)
            url = request.build_absolute_uri(user.avatar.url)
            return Response({'avatar': url}, status=status.HTTP_200_OK)

        user = request.user
        if user.avatar:
            user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
