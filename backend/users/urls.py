from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path(
        '',
        include(router.urls)
    ),
    path(
        'users/<int:pk>/subscribe/',
        UserViewSet.as_view({'post': 'subscribe', 'delete': 'subscribe'}),
        name='user-subscribe'
    ),
	path(
        'users/subscriptions/',
        UserViewSet.as_view({'get': 'subscriptions'}),
        name='subscriptions-list'
    ),
	path(
        'users/me/avatar/',
        UserViewSet.as_view({'put': 'avatar', 'delete': 'avatar'}),
        name='user-avatar'
    ),
]
