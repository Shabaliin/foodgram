from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
from rest_framework import serializers
from .models import User


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


class UserCreateSerializer(DjoserUserCreateSerializer):
    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'password')


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj: User):
        from recipes.models import Recipe
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
