from rest_framework.filters import BaseFilterBackend
from django.db.models import QuerySet
from django.http import HttpRequest


class RecipesFilterBackend(BaseFilterBackend):
    def filter_queryset(
        self,
        request: HttpRequest,
        queryset: QuerySet,
        view,
    ) -> QuerySet:
        author = request.query_params.get('author')
        if author:
            queryset = queryset.filter(author_id=author)

        tags = request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        is_favorited = request.query_params.get('is_favorited')
        if is_favorited in {'0', '1'} and request.user.is_authenticated:
            if is_favorited == '1':
                queryset = queryset.filter(favorited_by__user=request.user)
            else:
                queryset = queryset.exclude(favorited_by__user=request.user)

        is_in_cart = request.query_params.get('is_in_shopping_cart')
        if is_in_cart in {'0', '1'} and request.user.is_authenticated:
            if is_in_cart == '1':
                queryset = queryset.filter(in_carts__user=request.user)
            else:
                queryset = queryset.exclude(in_carts__user=request.user)

        return queryset
