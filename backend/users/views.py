from typing import Any
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Max
from rest_framework import permissions, status, viewsets, decorators
from rest_framework.response import Response
from .serializers import UserSerializer, UserWithRecipesSerializer
from .models import Subscription
from .pagination import StandardResultsSetPagination
from recipes.serializers import Base64ImageField

User = get_user_model()


class UserViewSet(viewsets.ViewSet):
	permission_classes = [permissions.AllowAny]
	pagination_class = StandardResultsSetPagination
	image_field = Base64ImageField()

	def retrieve(self, request, pk: int = None):
		user = get_object_or_404(User, id=pk)
		serializer = UserSerializer(user, context={'request': request})
		return Response(serializer.data)

	@decorators.action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
	def subscriptions(self, request):
		qs = User.objects.filter(id__in=Subscription.objects.filter(user=request.user).values('author_id'))
		qs = qs.annotate(last_pub=Max('recipes__created_at')).order_by('-last_pub', '-id')

		paginator = self.pagination_class()
		page = paginator.paginate_queryset(qs, request, view=self)

		recipes_limit = request.query_params.get('recipes_limit')
		ctx = {'request': request}
		if recipes_limit and recipes_limit.isdigit():
			ctx['recipes_limit'] = int(recipes_limit)

		serializer = UserWithRecipesSerializer(page, many=True, context=ctx)
		return paginator.get_paginated_response(serializer.data)

	@decorators.action(detail=True, methods=['post', 'delete'], permission_classes=[permissions.IsAuthenticated])
	def subscribe(self, request, pk: int = None):
		if request.method.lower() == 'post':
			if request.user.id == int(pk):
				return Response({'errors': 'Нельзя подписаться на себя'}, status=status.HTTP_400_BAD_REQUEST)
			author = get_object_or_404(User, id=pk)
			obj, created = Subscription.objects.get_or_create(user=request.user, author=author)
			if not created:
				return Response({'errors': 'Уже подписаны'}, status=status.HTTP_400_BAD_REQUEST)

			recipes_limit = request.query_params.get('recipes_limit')
			ctx = {'request': request}
			if recipes_limit and recipes_limit.isdigit():
				ctx['recipes_limit'] = int(recipes_limit)
			serializer = UserWithRecipesSerializer(author, context=ctx)
			return Response(serializer.data, status=status.HTTP_201_CREATED)

		deleted, _ = Subscription.objects.filter(user=request.user, author_id=pk).delete()
		if not deleted:
			return Response({'errors': 'Не были подписаны'}, status=status.HTTP_400_BAD_REQUEST)
		return Response(status=status.HTTP_204_NO_CONTENT)

	@decorators.action(detail=False, methods=['put', 'delete'], url_path='me/avatar', permission_classes=[permissions.IsAuthenticated])
	def avatar(self, request):
		if request.method.lower() == 'put':
			avatar_b64 = request.data.get('avatar')
			if not avatar_b64:
				return Response({'avatar': ['Обязательное поле.']}, status=status.HTTP_400_BAD_REQUEST)
			file = self.image_field.to_internal_value(avatar_b64)
			user = request.user
			user.avatar.save(file.name, file, save=True)
			url = request.build_absolute_uri(user.avatar.url)
			return Response({'avatar': url}, status=status.HTTP_200_OK)

		user = request.user
		if user.avatar:
			user.avatar.delete(save=True)
		return Response(status=status.HTTP_204_NO_CONTENT)
