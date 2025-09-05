from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RecipeViewSet, UserViewSet,
    list_tags, get_tag,
    list_ingredients, get_ingredient,
)

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.autoken')),
    path('tags/', list_tags),
    path('tags/<int:id>/', get_tag),
    path('ingredients/', list_ingredients),
    path('ingredients/<int:id>/', get_ingredient),
    path(
        'users/<int:pk>/subscribe/',
        UserViewSet.as_view({'post': 'subscribe', 'delete': 'subscribe'}),
        name='user-subscribe',
    )
    path(
        'users/subscriptions/',
        UserViewSet.as_view({'get': 'subscriptions'}),
        name='subscriptions-list',
    )

    path(
        'users/me/avatar/',
        UserViewSet.as_view({'put': 'avatar', 'delete': 'avatar'}),
        name='user-avatar',
    )
]
