from typing import Any
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Max
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from .serializers import UserSerializer, UserWithRecipesSerializer
from .models import Subscription
from recipes.serializers import Base64ImageField

User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    page_query_param = 'page'
    page_size_query_param = 'limit'
    page_size = 6


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'id'
    permission_classes = [permissions.AllowAny]


class UserAvatarView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    image_field = Base64ImageField()

    def put(self, request, *args: Any, **kwargs: Any):
        avatar_b64 = request.data.get('avatar')
        if not avatar_b64:
            return Response({'avatar': ['Обязательное поле.']}, status=status.HTTP_400_BAD_REQUEST)
        file = self.image_field.to_internal_value(avatar_b64)
        user = request.user
        user.avatar.save(file.name, file, save=True)
        url = request.build_absolute_uri(user.avatar.url)
        return Response({'avatar': url}, status=status.HTTP_200_OK)

    def delete(self, request, *args: Any, **kwargs: Any):
        user = request.user
        if user.avatar:
            user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsListView(generics.ListAPIView):
    serializer_class = UserWithRecipesSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # authors current user is subscribed to, ordered by latest recipe publication (new to old)
        qs = User.objects.filter(id__in=Subscription.objects.filter(user=self.request.user).values('author_id'))
        qs = qs.annotate(last_pub=Max('recipes__created_at')).order_by('-last_pub', '-id')
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        recipes_limit = self.request.query_params.get('recipes_limit')
        if recipes_limit and recipes_limit.isdigit():
            ctx['recipes_limit'] = int(recipes_limit)
        return ctx


class SubscribeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id: int):
        if request.user.id == id:
            return Response({'errors': 'Нельзя подписаться на себя'}, status=status.HTTP_400_BAD_REQUEST)
        author = get_object_or_404(User, id=id)
        obj, created = Subscription.objects.get_or_create(user=request.user, author=author)
        if not created:
            return Response({'errors': 'Уже подписаны'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = UserWithRecipesSerializer(author, context={**self.get_serializer_context(request), 'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id: int):
        deleted, _ = Subscription.objects.filter(user=request.user, author_id=id).delete()
        if not deleted:
            return Response({'errors': 'Не были подписаны'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_context(self, request):
        recipes_limit = request.query_params.get('recipes_limit')
        ctx = {}
        if recipes_limit and recipes_limit.isdigit():
            ctx['recipes_limit'] = int(recipes_limit)
        return ctx
