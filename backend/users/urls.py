from django.urls import path
from . import views

urlpatterns = [
    path('users/me/avatar/', views.UserAvatarView.as_view(), name='user-avatar'),
    path('users/subscriptions/', views.SubscriptionsListView.as_view(), name='subscriptions-list'),
    path('users/<int:id>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/<int:id>/subscribe/', views.SubscribeView.as_view(), name='user-subscribe'),
]
